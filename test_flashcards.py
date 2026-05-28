#!/usr/bin/env python
"""Debug test for flashcards generation"""
from app import create_app
import json

app = create_app()

with app.test_client() as client:
    with app.app_context():
        from models import Document, db
        
        Document.query.delete()
        db.session.commit()
        
        doc = Document(
            filename='test.pdf',
            title='Test',
            content_preview='Python is used for web development and data science.',
            file_path='test.pdf',
            file_type='pdf'
        )
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id
    
    print("Testing Flashcards...")
    r = client.post('/generate-flashcards', json={'document_id': doc_id})
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.content_type}")
    print(f"Raw response: {r.data.decode()[:500]}")
    
    try:
        data = r.get_json()
        print(f"JSON parsed successfully")
        print(f"Keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")
        if 'success' in data:
            print(f"Success: {data['success']}")
        if 'error' in data:
            print(f"Error: {data['error']}")
    except Exception as e:
        print(f"JSON parse error: {e}")
