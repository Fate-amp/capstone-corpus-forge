"""
Helper utilities module.

Contains common helper functions for validation, formatting, etc.

TODO: Add logging helper
TODO: Add error formatting helper
"""

import os
from werkzeug.utils import secure_filename


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a file has an allowed extension.
    
    Args:
        filename (str): Original filename
        allowed_extensions (set): Set of allowed extensions (e.g., {'pdf', 'txt', 'py'})
        
    Returns:
        bool: True if filename has an allowed extension
        
    TODO: Add case-insensitive check
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_type(filename: str) -> str:
    """
    Extract file type/extension from filename.
    
    Args:
        filename (str): Filename
        
    Returns:
        str: File extension (lowercase)
        
    Example:
        get_file_type("document.pdf") → "pdf"
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ""


def get_secure_filename(filename: str) -> str:
    """
    Get a secure filename for storage.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Secure filename
        
    TODO: Add timestamp/hash to prevent collisions
    """
    return secure_filename(filename)


def format_bytes(bytes_value: int) -> str:
    """
    Format byte size as human-readable string.
    
    Args:
        bytes_value (int): Number of bytes
        
    Returns:
        str: Formatted size (e.g., "1.5 MB")
        
    Example:
        format_bytes(1048576) → "1.0 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f} TB"


def format_tokens(tokens: int) -> str:
    """
    Format token count with thousand separators.
    
    Args:
        tokens (int): Number of tokens
        
    Returns:
        str: Formatted token count (e.g., "1,234")
    """
    return f"{tokens:,}"
