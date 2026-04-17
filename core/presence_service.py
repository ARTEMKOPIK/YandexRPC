"""
Main presence service module.
Orchestrates all components for Discord Rich Presence.
"""

import time
import re
from datetime import timedelta

import pypresence
from yandex_music import Client, exceptions as yandex_exceptions

from .app_state import get_app_state, ActivityTypeConfig, LanguageConfig, LogType, PlaybackStatus
from .rpc_manager import DiscordRPCManager
from .media_manager import MediaInfoProvider
from .track_finder import TrackFinder
from .exceptions import TokenError, NetworkError
from ..utils.logger import log
from ..utils.async_utils import run_async, AsyncTimeoutError
from ..utils.string_utils import blur_string


class PresenceService:
    """
    Main service class that orchestrates Discord Rich Presence.
    Replaces the monolithic Presence class with better separation of concerns.
    """
    
    def __init__(self):
        self._app_state = get_app_state()
        self.rpc_manager = DiscordRPCManager()
        self.media_provider = MediaInfoProvider()
        self.client = None
        self.track_finder = None
        self.running = False
        self.paused = False
        self.paused_time = 0
        self.track_time = 0
    
    def initialize_client(self, token=None):
        """
        Initialize Yandex Music client.
        
        Args:
            token: Optional Yandex authentication token
        """
        try:
            if token:
                log("Initialize client with token...", LogType.Default)
                self.client = Client(token=token).init()
            else:
                self.client = Client().init()
            
            self.track_finder = TrackFinder(self.client)
        except Exception as e:
            self._handle_yandex_exception(e)
            raise
    
    def start(self):
        """Start the presence service main loop."""
        self.rpc_manager.wait_for_discord()
        
        if not self.client:
            self.initialize_client(self._app_state.ya_token)
        
        self.rpc_manager.running = True
        self._app_state.current_track = None
        
        while self.rpc_manager.running:
            current_time = time.time()
            
            # Check Discord status
            if not self.rpc_manager.is_discord_running():
                self.rpc_manager.handle_disconnect()
            
            # Check for restart request
            if self._app_state.need_restart:
                self._app_state.need_restart = False
                self.rpc_manager.restart()
            
            try:
                ongoing_track = self._get_track()
                
                if self._app_state.current_track != ongoing_track:
                    # New track detected
                    self._handle_new_track(ongoing_track, current_time)
                else:
                    # Same track, check pause status
                    self._handle_pause_status(ongoing_track, current_time)
                
                time.sleep(3)
                
            except pypresence.exceptions.PipeClosed:
                self.rpc_manager.handle_disconnect()
            except AsyncTimeoutError:
                log("Timeout: get_media_info() took more than 10 seconds", LogType.Error)
            except Exception as e:
                log(f"Presence service stopped for a reason: {e}", LogType.Error)
    
    def _handle_new_track(self, track: dict, current_time: float):
        """Handle new track detection and update presence."""
        if track['success']:
            # Log track change
            if (self._app_state.current_track is not None and 
                'label' in self._app_state.current_track and 
                self._app_state.current_track['label'] is not None):
                
                if track['label'] != self._app_state.current_track['label']:
                    log(f"Changed track to {track['label']}", LogType.Update_Status)
            else:
                log(f"Changed track to {track['label']}", LogType.Update_Status)
            
            self.paused_time = 0
            self.track_time = current_time
            
            start_time = current_time - int(track['start-time'].total_seconds())
            end_time = start_time + track['durationSec']
            
            presence_args = {
                'activity_type': self._app_state.activity_type_config.value,
                'details': track['title'],
                'state': track['artist'],
                'start': start_time,
                'end': end_time,
                'large_image': track['og-image'],
            }
            
            if track['album'] != track['title']:
                presence_args['large_text'] = track['album']
            
            if self._app_state.button_config != ButtonConfig.NEITHER:
                presence_args['buttons'] = build_buttons(track['link'])
            
            if self._app_state.activity_type_config == ActivityTypeConfig.LISTENING:
                presence_args['small_image'] = (
                    "https://raw.githubusercontent.com/FozerG/WinYandexMusicRPC/"
                    "main/assets/Playing.png"
                )
                presence_args['small_text'] = (
                    "Playing" if self._app_state.language_config == LanguageConfig.ENGLISH 
                    else "Проигрывается"
                )
            
            self.rpc_manager.update_presence(**presence_args)
        else:
            self.rpc_manager.clear_presence()
        
        self._app_state.current_track = ongoing_track
        self.paused = False
    
    def _handle_pause_status(self, track: dict, current_time: float):
        """Handle pause/play status for current track."""
        if not track['success']:
            return
        
        playback = track.get("playback")
        
        # Track paused
        if playback != PlaybackStatus.Playing.name and not self.paused:
            self.paused = True
            log(f"Track {track['label']} on pause", LogType.Update_Status)
            
            presence_args = {
                'activity_type': self._app_state.activity_type_config.value,
                'details': track['title'],
                'state': track['artist'],
                'large_image': track['og-image'],
                'large_text': track['album'],
                'small_image': (
                    "https://raw.githubusercontent.com/FozerG/WinYandexMusicRPC/"
                    "main/assets/Paused.png"
                ),
                'small_text': (
                    "On pause" if self._app_state.language_config == LanguageConfig.ENGLISH 
                    else "На паузе"
                )
            }
            
            if self._app_state.button_config != ButtonConfig.NEITHER:
                presence_args['buttons'] = build_buttons(track['link'])
            
            position_seconds = int(track['start-time'].total_seconds())
            if (self._app_state.activity_type_config == ActivityTypeConfig.LISTENING 
                and position_seconds != 0):
                presence_args['large_text'] = (
                    f"{'On pause' if self._app_state.language_config == LanguageConfig.ENGLISH else 'На паузе'} "
                    f"{format_duration(position_seconds * 1000)} / {track['formatted_duration']}"
                )
            
            if position_seconds != 0:
                presence_args['small_text'] = (
                    f"{'On pause' if self._app_state.language_config == LanguageConfig.ENGLISH else 'На паузе'} "
                    f"{format_duration(position_seconds * 1000)} / {track['formatted_duration']}"
                )
            
            self.rpc_manager.update_presence(**presence_args)
        
        # Track resumed
        elif playback == PlaybackStatus.Playing.name and self.paused:
            log(f"Track {track['label']} off pause.", LogType.Update_Status)
            self.paused = False
        
        # Long pause (>5 minutes)
        elif playback != PlaybackStatus.Playing.name and self.paused and self.track_time != 0:
            self.paused_time = current_time - self.track_time
            if self.paused_time > 5 * 60:
                self.track_time = 0
                self.rpc_manager.clear_presence()
                log("Clear RPC due to paused for more than 5 minutes", LogType.Update_Status)
        else:
            self.paused_time = 0
    
    def _get_track(self) -> dict:
        """Get current track information."""
        try:
            current_media_info = run_async(
                self.media_provider.get_media_info(), 
                timeout=10
            )
            
            if not current_media_info:
                log("No media information returned from get_media_info", LogType.Error)
                return {'success': False}
            
            artist = current_media_info.get("artist", "").strip()
            title = current_media_info.get("title", "").strip()
            position = current_media_info['position']
            
            if not artist or not title:
                log(
                    f"MediaManager returned empty string for artist or title. "
                    f"Active app - {current_media_info['app_name']}. "
                    f"Title - {current_media_info['session_title']}",
                    LogType.Error
                )
                return {'success': False}
            
            if not self.track_finder:
                return {'success': False}
            
            track_data = self.track_finder.find_track(artist, title, position)
            if track_data:
                track_data['playback'] = current_media_info['playback_status']
            
            return track_data
            
        except Exception as e:
            self._handle_yandex_exception(e)
            return {'success': False}
    
    def _handle_yandex_exception(self, exception):
        """Handle Yandex Music API exceptions."""
        json_str = str(exception).replace("'", '"')
        match = re.search(r'({.*?})', json_str)
        
        if match:
            json_str = match.group(1)
        
        try:
            import json
            data = json.loads(json_str)
            error_name = data.get('name')
            
            if error_name == 'Unavailable For Legal Reasons':
                log(
                    "You are using Yandex music in a country where it is not available "
                    "without authorization! Turn off VPN or login using a Yandex token.",
                    LogType.Error
                )
            elif error_name == 'session-expired':
                log("Your Yandex token is out of date or incorrect, login again.", LogType.Error)
            else:
                log(f"Something happened: {exception}", LogType.Error)
        except Exception:
            log(f"Something happened: {exception}", LogType.Error)
    
    def stop(self):
        """Stop the presence service."""
        self.rpc_manager.stop()


# Import needed for type checking
from .app_state import ButtonConfig
from ..utils.string_utils import format_duration


def build_buttons(url):
    """Build RPC buttons based on configuration."""
    from .app_state import get_app_state, ButtonConfig, LanguageConfig
    
    app_state = get_app_state()
    buttons = []
    
    if app_state.button_config == ButtonConfig.YANDEX_MUSIC_WEB:
        buttons.append({
            'label': (
                'Listen on Yandex Music' 
                if app_state.language_config == LanguageConfig.ENGLISH 
                else 'Откр. в браузере'
            ), 
            'url': url
        })
    elif app_state.button_config == ButtonConfig.YANDEX_MUSIC_APP:
        deep_link = extract_deep_link(url)
        buttons.append({
            'label': (
                'Listen on Yandex Music (in App)' 
                if app_state.language_config == LanguageConfig.ENGLISH 
                else 'Откр. в прилож.'
            ), 
            'url': deep_link
        })
    elif app_state.button_config == ButtonConfig.BOTH:
        buttons.append({
            'label': (
                'Listen on Yandex Music (Web)' 
                if app_state.language_config == LanguageConfig.ENGLISH 
                else 'Откр. в браузере'
            ), 
            'url': url
        })
        deep_link = extract_deep_link(url)
        buttons.append({
            'label': (
                'Listen on Yandex Music (App)' 
                if app_state.language_config == LanguageConfig.ENGLISH 
                else 'Откр. в прилож.'
            ), 
            'url': deep_link
        })
    
    # Validate button label lengths
    for button in buttons:
        label = button['label']
        if len(label.encode('utf-8')) > 32:
            raise ValueError(f"Label '{label}' exceeds 32 bytes")
    
    return buttons


def extract_deep_link(url):
    """Extract deep link from Yandex Music URL."""
    pattern = r"https://music.yandex.ru/album/(\d+)/track/(\d+)"
    match = re.match(pattern, url)
    
    if match:
        album_id, track_id = match.groups()
        return f"yandexmusic://album/{album_id}/track/{track_id}"
    return None
