"""
Document processing service module.

Handles extraction of text from various file formats (PDF, TXT, code files).

TODO: Add support for more file types (DOCX, MD, etc.)
TODO: Add OCR for scanned PDFs
TODO: Add error handling and logging for parsing failures
"""

import pdfplumber
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from all pages
        
    Raises:
        Exception: If PDF cannot be parsed
        
    TODO: Handle corrupted PDFs gracefully
    TODO: Add page-by-page extraction for large files
    TODO: Preserve formatting information (headings, lists, etc.)
    """
    try:
        text = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text.append(f"--- Page {page_num} ---\n{page_text}")
        
        extracted = "\n\n".join(text)
        logger.info(f"Extracted {len(extracted)} characters from PDF: {file_path}")
        return extracted
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        raise


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.
    
    Args:
        file_path (str): Path to the TXT file
        
    Returns:
        str: File contents
        
    Raises:
        Exception: If file cannot be read
        
    TODO: Handle different encodings (UTF-8, Latin-1, etc.)
    TODO: Add file size limits
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        logger.info(f"Extracted {len(text)} characters from TXT: {file_path}")
        return text
    
    except Exception as e:
        logger.error(f"Error reading TXT file {file_path}: {str(e)}")
        raise


def extract_text_from_code(file_path: str) -> str:
    """
    Extract text from a code file (Python, JavaScript, Java, etc.).
    
    Code files are treated as plain text with syntax preservation.
    
    Args:
        file_path (str): Path to the code file
        
    Returns:
        str: File contents (code)
        
    Raises:
        Exception: If file cannot be read
        
    TODO: Add syntax highlighting metadata
    TODO: Add code structure analysis (classes, functions, etc.)
    TODO: Add language detection
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
        logger.info(f"Extracted {len(code)} characters from code file: {file_path}")
        return code
    
    except Exception as e:
        logger.error(f"Error reading code file {file_path}: {str(e)}")
        raise


def extract_text_by_file_type(file_path: str, file_type: str) -> str:
    """
    Route text extraction to the appropriate handler based on file type.
    
    Args:
        file_path (str): Path to the file
        file_type (str): Type of file (pdf, txt, py, js, etc.)
        
    Returns:
        str: Extracted text
        
    Raises:
        ValueError: If file type is not supported
        Exception: If extraction fails
        
    TODO: Add more file type support
    """
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'txt':
        return extract_text_from_txt(file_path)
    elif file_type in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'go', 'rs', 'rb', 'php']:
        return extract_text_from_code(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def get_preview_text(text: str, max_chars: int = 500) -> str:
    """
    Generate a preview/preview of the extracted text.
    
    Args:
        text (str): Full extracted text
        max_chars (int): Maximum characters for preview
        
    Returns:
        str: Truncated text preview
        
    TODO: Make preview more intelligent (complete sentences, key excerpts)
    """
    if len(text) <= max_chars:
        return text
    
    # Truncate to max_chars and try to end at a sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    
    if last_period > max_chars * 0.8:  # If period is reasonably close to the end
        return truncated[:last_period + 1]
    
    return truncated + "..."
