"""
Logging utility module.
Provides centralized logging with color support.
"""

from colorama import init, Fore, Style
from .app_state import LogType


# Initialize colorama once at module load
init()


def log(text, log_type=LogType.Default):
    """
    Log a message with appropriate coloring based on type.
    
    Args:
        text: The message to log
        log_type: Type of log message (Default, Notification, Error, Update_Status)
    """
    # Color mappings
    color_map = {
        LogType.Notification: Fore.YELLOW,
        LogType.Error: Fore.RED,
        LogType.Update_Status: Fore.CYAN,
        LogType.Default: Style.RESET_ALL
    }
    
    message_color = color_map.get(log_type, Style.RESET_ALL)
    print(f"{Fore.RED}[WinYandexMusicRPC] -> {message_color}{text}{Style.RESET_ALL}")
