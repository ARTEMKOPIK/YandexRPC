"""
Tests for string utilities module.
"""

import pytest
from utils.string_utils import trim_string, single_char, blur_string, format_duration


class TestTrimString:
    """Tests for trim_string function."""
    
    def test_trim_shorter_string(self):
        """Test that shorter strings are not trimmed."""
        assert trim_string("Hello", 10) == "Hello"
    
    def test_trim_exact_length(self):
        """Test that exact length strings are not trimmed."""
        assert trim_string("Hello", 5) == "Hello"
    
    def test_trim_longer_string(self):
        """Test that longer strings are trimmed with ellipsis."""
        assert trim_string("Hello World", 5) == "Hello..."
    
    def test_trim_empty_string(self):
        """Test empty string handling."""
        assert trim_string("", 5) == ""
    
    def test_trim_zero_max_chars(self):
        """Test zero max_chars handling."""
        assert trim_string("Hello", 0) == "..."


class TestSingleChar:
    """Tests for single_char function."""
    
    def test_single_character(self):
        """Test single character wrapping."""
        assert single_char("a") == '"a"'
    
    def test_multiple_characters(self):
        """Test multiple characters are not wrapped."""
        assert single_char("ab") == "ab"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert single_char("") == ""


class TestBlurString:
    """Tests for blur_string function."""
    
    def test_blur_long_string(self):
        """Test blurring of long strings."""
        result = blur_string("secret_token_12345")
        assert result.startswith("secr")
        assert result.endswith("1234")
        assert "*" in result
    
    def test_blur_short_string(self):
        """Test short strings are not blurred."""
        assert blur_string("short") == "short"
    
    def test_blur_none(self):
        """Test None handling."""
        assert blur_string(None) == ""
    
    def test_blur_exactly_8_chars(self):
        """Test exactly 8 character string."""
        assert blur_string("12345678") == "12345678"


class TestFormatDuration:
    """Tests for format_duration function."""
    
    def test_format_zero(self):
        """Test zero duration."""
        assert format_duration(0) == "0:00"
    
    def test_format_seconds_only(self):
        """Test seconds only formatting."""
        assert format_duration(30000) == "0:30"
    
    def test_format_minutes_and_seconds(self):
        """Test minutes and seconds formatting."""
        assert format_duration(150000) == "2:30"
    
    def test_format_hours_converted(self):
        """Test hours are converted to minutes."""
        assert format_duration(3661000) == "61:01"
