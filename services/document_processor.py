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
import os
import re

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from docx import Document as DocxDocument
except Exception:
    DocxDocument = None

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None


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

                # If no text and OCR is available, try OCR on the rendered page
                if (not page_text or not page_text.strip()) and pytesseract and hasattr(page, "to_image"):
                    try:
                        img = page.to_image(resolution=150).original
                        if img and Image:
                            ocr_text = pytesseract.image_to_string(img)
                            page_text = ocr_text
                    except Exception:
                        # OCR fallback failed; continue gracefully
                        page_text = page_text

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
    # Enforce a conservative file size limit (20 MB) to avoid memory spikes
    try:
        size = Path(file_path).stat().st_size
        if size > 20 * 1024 * 1024:
            raise ValueError("File too large")
    except Exception:
        # If we cannot stat, proceed and let read fail later
        pass

    # Try UTF-8 first, then fallback to Latin-1
    for enc in ("utf-8", "latin-1"):
        try:
            with open(file_path, 'r', encoding=enc, errors='replace') as f:
                text = f.read()
            logger.info(f"Extracted {len(text)} characters from TXT: {file_path} (encoding={enc})")
            return text
        except Exception:
            continue

    logger.error(f"Error reading TXT file {file_path}: could not decode with utf-8 or latin-1")
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

        # Minimal language detection by extension
        ext = Path(file_path).suffix.lower().lstrip('.')
        header = f"--- {Path(file_path).name} (lang={ext}) ---\n"

        # For Python, provide a tiny structure summary (top-level defs/classes)
        structure = []
        if ext == 'py':
            for line in code.splitlines():
                m = re.match(r'^\s*(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)', line)
                if m:
                    structure.append(f"{m.group(1)} {m.group(2)}")
        if structure:
            header += "\n" + "\n".join(structure) + "\n\n"

        logger.info(f"Extracted {len(code)} characters from code file: {file_path}")
        return header + code

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
    # If caller didn't provide file_type, infer from extension
    if not file_type:
        suffix = Path(file_path).suffix.lower().lstrip('.')
        file_type = suffix

    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type in ('txt', 'md'):
        return extract_text_from_txt(file_path)
    elif file_type == 'docx':
        if DocxDocument is None:
            raise RuntimeError('python-docx is required to parse DOCX files')
        return extract_text_from_docx(file_path)
    elif file_type in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'go', 'rs', 'rb', 'php']:
        return extract_text_from_code(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file using python-docx. Falls back with clear error if
    dependency is missing.
    """
    if DocxDocument is None:
        raise RuntimeError('python-docx is not installed')

    try:
        doc = DocxDocument(file_path)
        parts = []
        for para in doc.paragraphs:
            text = para.text
            if text and text.strip():
                parts.append(text)

        extracted = "\n\n".join(parts)
        logger.info(f"Extracted {len(extracted)} characters from DOCX: {file_path}")
        return extracted
    except Exception as e:
        logger.error(f"Error extracting DOCX {file_path}: {str(e)}")
        raise


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

    truncated = text[:max_chars]

    # Prefer ending at a sentence boundary or newline
    # Search for last sentence-ending punctuation
    m = re.search(r'([\.!?])(?=[^\.!?]*$)', truncated)
    if m:
        idx = truncated.rfind(m.group(1))
        if idx and idx > max_chars * 0.6:
            return truncated[:idx + 1]

    # Otherwise, end at last newline if present
    last_nl = truncated.rfind('\n')
    if last_nl > max_chars * 0.5:
        return truncated[:last_nl].strip() + "..."

    return truncated + "..."
