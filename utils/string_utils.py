"""
String utilities module.
Provides string manipulation helpers.
"""


def trim_string(string, max_chars):
    """
    Trim a string to maximum length, adding ellipsis if needed.
    
    Args:
        string: The string to trim
        max_chars: Maximum number of characters
    
    Returns:
        Trimmed string with ellipsis if it exceeded max_chars
    """
    if len(string) > max_chars:
        return string[:max_chars] + "..."
    return string


def single_char(s):
    """
    Wrap single character strings in quotes.
    
    Args:
        s: The string to process
    
    Returns:
        String wrapped in quotes if it's a single character
    """
    if len(s) == 1:
        return f'"{s}"'
    return s


def blur_string(s):
    """
    Blur a sensitive string (e.g., tokens) for display.
    
    Args:
        s: The string to blur
    
    Returns:
        Blurred string showing only first 4 and last 4 characters
    """
    if s is None:
        return ''
    if len(s) <= 8:
        return s
    return s[:4] + '*' * (len(s) - 8) + s[-4:]


def format_duration(duration_ms):
    """
    Format duration in milliseconds to MM:SS format.
    
    Args:
        duration_ms: Duration in milliseconds
    
    Returns:
        Formatted string in MM:SS format
    """
    total_seconds = duration_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02}"
