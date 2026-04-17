"""
Application state management module.
Encapsulates all global state in a single class.
"""

from enum import Enum


class ActivityTypeConfig(Enum):
    """Enum for activity type configuration."""
    PLAYING = 0
    LISTENING = 2


class ButtonConfig(Enum):
    """Enum for button configuration."""
    YANDEX_MUSIC_WEB = 1
    YANDEX_MUSIC_APP = 2
    BOTH = 3
    NEITHER = 4


class LanguageConfig(Enum):
    """Enum for language configuration."""
    ENGLISH = 0
    RUSSIAN = 1


class PlaybackStatus(Enum):
    """Enum for media playback status."""
    Unknown = 0
    Closed = 1
    Opened = 2
    Paused = 3
    Playing = 4
    Stopped = 5


class LogType(Enum):
    """Enum for log message types."""
    Default = 0
    Notification = 1
    Error = 2
    Update_Status = 3


class AppState:
    """
    Centralized application state management.
    Replaces scattered global variables with a single encapsulated class.
    """
    
    # Discord Client IDs
    CLIENT_ID_EN = '1269807014393942046'
    CLIENT_ID_RU = '1217562797999784007'
    CLIENT_ID_RU_DECLINED = '1269826362399522849'
    
    # Application version
    CURRENT_VERSION = "v2.5.1"
    
    # Repository URL
    REPO_URL = "https://github.com/FozerG/WinYandexMusicRPC"
    
    def __init__(self):
        # Authentication
        self.ya_token = None
        
        # Search settings
        self.strong_find = True
        
        # Auto-start setting
        self.auto_start_windows = False
        
        # Track state
        self.name_prev = None
        self.current_track = None
        
        # Restart flag
        self.need_restart = False
        
        # Tray icon visibility
        self.icon_tray = True
        
        # Media sessions cache
        self.media_sessions = None
        
        # Configuration manager (injected)
        self.config_manager = None
        
        # RPC settings (loaded from config)
        self.activity_type_config = ActivityTypeConfig.LISTENING
        self.button_config = ButtonConfig.BOTH
        self.language_config = LanguageConfig.RUSSIAN
        
        # Window handle
        self.window = None
    
    def set_config_manager(self, config_manager):
        """Set the configuration manager instance."""
        self.config_manager = config_manager
    
    def load_settings(self, from_start=False):
        """Load settings from configuration."""
        if self.config_manager is None:
            raise RuntimeError("ConfigManager not initialized")
        
        self.auto_start_windows = self._is_in_autostart()
        self.activity_type_config = self.config_manager.get_enum_setting(
            'UserSettings', 'activity_type', ActivityTypeConfig, 
            fallback=ActivityTypeConfig.LISTENING
        )
        self.button_config = self.config_manager.get_enum_setting(
            'UserSettings', 'buttons_settings', ButtonConfig, 
            fallback=ButtonConfig.BOTH
        )
        self.language_config = self.config_manager.get_enum_setting(
            'UserSettings', 'language', LanguageConfig, 
            fallback=LanguageConfig.RUSSIAN
        )
        
        strong_find_str = self.config_manager.get_setting(
            'UserSettings', 'strong_find', fallback='True'
        )
        self.strong_find = strong_find_str.lower() == 'true'
        
        if from_start:
            from colorama import Style
            from .logger import log
            log(
                f"Loaded settings: {Style.RESET_ALL}"
                f"activity_type_config = {self.activity_type_config.name}, "
                f"button_config = {self.button_config.name}, "
                f"language_config = {self.language_config.name}, "
                f"strong_find = {self.strong_find}, "
                f"selected_session = {self.config_manager.get_selected_session()}",
                LogType.Update_Status
            )
    
    def _is_in_autostart(self):
        """Check if application is in autostart."""
        import os
        import winreg
        
        def is_in_startup():
            shortcut_path = os.path.join(
                os.getenv('APPDATA'), 
                'Microsoft', 'Windows', 'Start Menu', 
                'Programs', 'Startup', 'YaMusicRPC.lnk'
            )
            return os.path.exists(shortcut_path)
        
        def is_in_registry():
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, 
                    r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                    0, winreg.KEY_READ
                )
                winreg.QueryValueEx(key, 'YaMusicRPC')
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                return False
        
        return is_in_startup() or is_in_registry()
    
    def get_client_id(self):
        """Get appropriate Discord client ID based on settings."""
        if self.language_config == LanguageConfig.ENGLISH:
            return self.CLIENT_ID_EN
        elif self.activity_type_config == ActivityTypeConfig.LISTENING:
            return self.CLIENT_ID_RU_DECLINED
        else:
            return self.CLIENT_ID_RU
    
    def reset_track_state(self):
        """Reset track-related state."""
        self.current_track = None
        self.name_prev = None


# Singleton instance
_app_state = None


def get_app_state():
    """Get the global application state instance."""
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state


def initialize_app_state(config_manager=None):
    """Initialize the application state with optional config manager."""
    global _app_state
    _app_state = AppState()
    if config_manager:
        _app_state.set_config_manager(config_manager)
    return _app_state
