import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Russian phone number
    # Should be 10 or 11 digits (with or without country code)
    if len(digits_only) == 10:
        # Mobile numbers starting with 9
        return digits_only.startswith('9')
    elif len(digits_only) == 11:
        # With country code +7
        return digits_only.startswith('7') and digits_only[1] == '9'
    
    return False


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number to standard format"""
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Normalize to +7XXXXXXXXXX format
    if len(digits_only) == 10 and digits_only.startswith('9'):
        return f"+7{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('7'):
        return f"+{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('8'):
        return f"+7{digits_only[1:]}"
    
    return None


def validate_telegram_id(telegram_id: int) -> bool:
    """Validate Telegram user ID"""
    return isinstance(telegram_id, int) and telegram_id > 0


def validate_non_empty_string(value: str, min_length: int = 1) -> bool:
    """Validate that string is not empty and meets minimum length"""
    return isinstance(value, str) and len(value.strip()) >= min_length