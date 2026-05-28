#!/usr/bin/env python
"""Quick verification of database schema and document processing."""

import sys
sys.path.insert(0, '.')

from app import create_app, db
from models import Document
from services.document_processor import extract_text_from_txt, extract_text_by_file_type
from pathlib import Path

print("=== VERIFICATION 1: Database Schema ===")
app = create_app()
with app.app_context():
    # Check if Document model has full_content column
    inspector = db.inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('documents')]
    
    print(f"Document table columns: {columns}")
    if 'full_content' in columns:
        print("✓ full_content column exists in database")
    else:
        print("✗ full_content column MISSING from database")
    
    if 'file_path' in columns:
        print("✓ file_path column exists")
    else:
        print("✗ file_path column MISSING")

print("\n=== VERIFICATION 2: Text Extraction ===")

# Test TXT extraction
test_txt = Path('temp_test.txt')
test_txt.write_text("Hello World\nThis is a test file\nWith multiple lines")

try:
    extracted = extract_text_from_txt(str(test_txt))
    if "Hello World" in extracted and "multiple lines" in extracted:
        print("✓ TXT extraction working")
    else:
        print(f"✗ TXT extraction incomplete: {extracted[:50]}")
except Exception as e:
    print(f"✗ TXT extraction failed: {str(e)}")
finally:
    test_txt.unlink()

# Test extraction by file type
test_txt2 = Path('temp_test2.txt')
test_txt2.write_text("Python is great")

try:
    extracted = extract_text_by_file_type(str(test_txt2), 'txt')
    if "Python" in extracted:
        print("✓ extract_text_by_file_type working")
    else:
        print(f"✗ File type extraction issue: {extracted}")
except Exception as e:
    print(f"✗ File type extraction failed: {str(e)}")
finally:
    test_txt2.unlink()

print("\n=== VERIFICATION 3: Document Model ===")
with app.app_context():
    # Create a test document
    test_doc = Document(
        filename='test.txt',
        title='Test',
        file_path='/tmp/test.txt',
        file_type='txt',
        content_preview='Test preview',
        full_content='This is the full content of the test document'
    )
    db.session.add(test_doc)
    db.session.commit()
    
    # Retrieve and check
    retrieved = Document.query.filter_by(title='Test').first()
    if retrieved:
        print(f"✓ Document saved: id={retrieved.id}")
        if hasattr(retrieved, 'full_content') and retrieved.full_content:
            print(f"✓ full_content saved: {retrieved.full_content[:50]}...")
        else:
            print("✗ full_content not saved or missing")
    else:
        print("✗ Document not retrieved")
    
    # Cleanup
    db.session.delete(retrieved)
    db.session.commit()

print("\n=== All verifications complete ===")
