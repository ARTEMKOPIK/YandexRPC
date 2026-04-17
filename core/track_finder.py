"""
Track finding module.
Handles searching and matching tracks on Yandex Music.
"""

from itertools import permutations

from yandex_music import Client

from .app_state import get_app_state, LogType
from .exceptions import TrackNotFoundError
from ..utils.logger import log
from ..utils.string_utils import trim_string, single_char, format_duration


class TrackFinder:
    """
    Finds and matches tracks on Yandex Music.
    Encapsulates all track search logic.
    """
    
    def __init__(self, client: Client):
        self.client = client
        self._app_state = get_app_state()
    
    def find_track(self, artist: str, title: str, position) -> dict:
        """
        Find a track on Yandex Music by artist and title.
        
        Args:
            artist: Track artist name
            title: Track title
            position: Current playback position
        
        Returns:
            dict with track information or {'success': False} if not found
        
        Raises:
            Exception: If search fails unexpectedly
        """
        name_current = f"{artist} - {title}"
        
        # Check if this is the same track as before
        if name_current == self._app_state.name_prev:
            # Return cached track with updated position
            if self._app_state.current_track:
                current_track_copy = self._app_state.current_track.copy()
                current_track_copy["start-time"] = position
                return current_track_copy
            return {'success': False}
        
        self._app_state.name_prev = name_current
        log(f"Now listening to {name_current}")
        
        # Search attempts: first without apostrophe, then with original
        search = self._search_track(name_current.replace("'", " "))
        if search.tracks is None:
            search = self._search_track(name_current)
        
        if search.tracks is None:
            log(f"Can't find the song: {name_current}", LogType.Error)
            return {'success': False}
        
        # Try to match from first 5 results
        final_track = self._match_track(search.tracks.results[:5], name_current)
        
        if final_track is None:
            return {'success': False}
        
        return self._build_track_response(final_track, position)
    
    def _search_track(self, query: str):
        """Execute a search query."""
        return self.client.search(query, True, "all", 0, False)
    
    def _match_track(self, results, target_name: str):
        """
        Match a track from search results.
        
        Args:
            results: List of track results
            target_name: Target track name to match
        
        Returns:
            Matched track or None
        """
        debug_str = []
        
        for index, track in enumerate(results, start=1):
            if track.type not in ['music', 'track', 'podcast_episode']:
                debug_str.append(
                    f"[WinYandexMusicRPC] -> The result #{index} has the wrong type."
                )
                continue
            
            # Generate all possible artist name permutations
            artists = track.artists_name()
            track_names = self._generate_track_names(artists, track.title)
            
            # Case-insensitive match
            is_match = any(
                target_name.lower() == name.lower() 
                for name in track_names
            )
            
            if self._app_state.strong_find and not is_match:
                find_track_name = ', '.join(artists) + f" - {track.title}"
                debug_str.append(
                    f"[WinYandexMusicRPC] -> The result #{index} has the wrong title. "
                    f"Now play: {target_name}. But we find: {find_track_name}"
                )
                continue
            
            return track
        
        # Log debug info if no match found
        if debug_str:
            print('\n'.join(debug_str))
            log(f"Can't find the song (strong_find): {target_name}", LogType.Error)
        
        return None
    
    def _generate_track_names(self, artists: list, title: str) -> list:
        """Generate all possible track name variations with artist permutations."""
        if len(artists) <= 4:
            all_variants = [list(v) for v in permutations(artists)]
            return [', '.join(variant) + f" - {title}" for variant in all_variants]
        else:
            return [', '.join(artists) + f" - {title}"]
    
    def _build_track_response(self, track, position) -> dict:
        """Build the track response dictionary."""
        track_id = track.trackId.split(":")
        
        return {
            'success': True,
            'title': single_char(trim_string(track.title, 40)),
            'artist': single_char(
                trim_string(f"{', '.join(track.artists_name())}", 40)
            ),
            'album': single_char(trim_string(track.albums[0].title, 25)),
            'label': trim_string(
                f"{', '.join(track.artists_name())} - {track.title}", 50
            ),
            'link': f"https://music.yandex.ru/album/{track_id[1]}/track/{track_id[0]}/",
            'durationSec': track.duration_ms // 1000,
            'formatted_duration': format_duration(track.duration_ms),
            'start-time': position,
            'playback': None,  # Will be set by caller
            'og-image': "https://" + track.og_image[:-2] + "400x400"
        }
