from datetime import datetime
from typing import Optional


def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Format datetime to string"""
    return dt.strftime(format_str) if dt else ""


def format_date(dt: datetime, format_str: str = "%d.%m.%Y") -> str:
    """Format date to string"""
    return dt.strftime(format_str) if dt else ""


def format_time(dt: datetime, format_str: str = "%H:%M") -> str:
    """Format time to string"""
    return dt.strftime(format_str) if dt else ""


def format_phone(phone: str) -> str:
    """Format phone number for display"""
    if not phone:
        return ""
    
    # Remove + and format as +7 (XXX) XXX-XX-XX
    digits = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    
    if len(digits) == 11 and digits.startswith("7"):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return phone


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_list(items: list, separator: str = ", ", max_items: int = None) -> str:
    """Format list as string"""
    if not items:
        return ""
    
    if max_items and len(items) > max_items:
        displayed_items = items[:max_items]
        remaining = len(items) - max_items
        return f"{separator.join(map(str, displayed_items))} и еще {remaining}"
    
    return separator.join(map(str, items))


def format_status_emoji(status: str) -> str:
    """Get emoji for status"""
    status_emojis = {
        "pending": "⏳",
        "accepted": "✅",
        "transferred": "📤", 
        "completed": "🎉",
        "cancelled": "❌",
        "rejected": "🚫",
        "active": "✅",
        "inactive": "❌",
        "blocked": "🚫"
    }
    
    return status_emojis.get(status.lower(), "❓")