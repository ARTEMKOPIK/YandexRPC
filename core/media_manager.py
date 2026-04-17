"""
Media information retrieval module.
Handles getting media info from Windows MediaManager.
"""

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)

from .app_state import get_app_state, PlaybackStatus, LogType
from .exceptions import MediaInfoError
from ..utils.logger import log


class MediaInfoProvider:
    """
    Provides media information from Windows MediaManager.
    Encapsulates all media session handling.
    """
    
    def __init__(self):
        self._app_state = get_app_state()
        self._media_sessions = None
    
    async def _get_media_sessions(self):
        """Get or cache media sessions."""
        if self._media_sessions is None:
            try:
                log("Making the first request to windows MediaManager...", LogType.Default)
                self._media_sessions = await MediaManager.request_async()
            except Exception as e:
                log(f"Failed to get MediaManager sessions: {e}", LogType.Error)
                raise MediaInfoError(f"Failed to get MediaManager sessions: {e}")
        return self._media_sessions
    
    async def get_media_info(self):
        """
        Get current media information.
        
        Returns:
            dict with keys: artist, title, playback_status, position, 
                           session_title, app_name
        
        Raises:
            MediaInfoError: If media info cannot be retrieved
        """
        media_sessions = await self._get_media_sessions()
        
        config_manager = self._app_state.config_manager
        selected_session_id = config_manager.get_selected_session() if config_manager else "Automatic"
        
        all_sessions = media_sessions.get_sessions()
        target_session = None
        
        if selected_session_id and selected_session_id != "Automatic":
            # Find session by source_app_user_model_id
            for session in all_sessions:
                if session.source_app_user_model_id == selected_session_id:
                    target_session = session
                    break
            
            if not target_session:
                raise MediaInfoError(
                    f"Selected session '{selected_session_id}' not found."
                )
        else:
            target_session = media_sessions.get_current_session()
        
        if not target_session:
            raise MediaInfoError("No active media session found.")
        
        info = await target_session.try_get_media_properties_async()
        playback_info = target_session.get_playback_info()
        timeline_props = target_session.get_timeline_properties()
        
        return {
            'artist': info.artist,
            'title': info.title,
            'playback_status': PlaybackStatus(
                playback_info.playback_status
            ).name,
            'position': timeline_props.position,
            'session_title': info.title or "Unknown Title",
            'app_name': target_session.source_app_user_model_id or "Unknown App"
        }
    
    async def get_session_ids(self):
        """
        Get list of available session IDs.
        
        Returns:
            list of session ID strings
        """
        media_sessions = await self._get_media_sessions()
        return [
            session.source_app_user_model_id or "UnknownApp"
            for session in media_sessions.get_sessions()
        ]
    
    def invalidate_cache(self):
        """Invalidate the media sessions cache."""
        self._media_sessions = None
