"""
Custom exceptions module.
Provides specific exception classes for better error handling.
"""


class WinYandexMusicRPCError(Exception):
    """Base exception for WinYandexMusicRPC."""
    pass


class TokenError(WinYandexMusicRPCError):
    """Exception raised for token-related errors."""
    
    def __init__(self, message="Invalid or expired Yandex token"):
        self.message = message
        super().__init__(self.message)


class MediaInfoError(WinYandexMusicRPCError):
    """Exception raised when media information cannot be retrieved."""
    
    def __init__(self, message="Failed to get media information"):
        self.message = message
        super().__init__(self.message)


class TrackNotFoundError(WinYandexMusicRPCError):
    """Exception raised when a track cannot be found."""
    
    def __init__(self, track_name="Unknown track"):
        self.track_name = track_name
        super().__init__(f"Track not found: {track_name}")


class DiscordRPCError(WinYandexMusicRPCError):
    """Exception raised for Discord RPC-related errors."""
    
    def __init__(self, message="Discord RPC error"):
        self.message = message
        super().__init__(self.message)


class ConfigError(WinYandexMusicRPCError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message="Configuration error"):
        self.message = message
        super().__init__(self.message)


class NetworkError(WinYandexMusicRPCError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message="Network error"):
        self.message = message
        super().__init__(self.message)
