#!/usr/bin/env python
"""
Comprehensive test of all app features
"""
from app import create_app
import json

app = create_app()

print("=== COMPREHENSIVE FEATURE TEST ===\n")

with app.test_client() as client:
    with app.app_context():
        from models import Document, db
        
        # Cleanup
        Document.query.delete()
        db.session.commit()
        
        # Create test document
        doc = Document(
            filename='test.pdf',
            title='Test Document',
            content_preview='Python is a programming language used for web dev, data science, and automation.',
            file_path='test.pdf',
            file_type='pdf'
        )
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id
        print(f"Setup: Created test document (ID: {doc_id})\n")
    
    tests = [
        ("Dashboard", "GET", "/", None),
        ("Chat - Question", "POST", "/chat", {"query": "What is this about?", "document_id": doc_id}),
        ("Settings - Update", "POST", "/update-settings", {"temperature": 0.8, "top_p": 0.95}),
        ("Flashcards - Generate", "POST", "/generate-flashcards", {"document_id": doc_id}),
        ("Quiz - Generate", "POST", "/generate-quiz", {"document_id": doc_id}),
        ("Code - Analyze", "POST", f"/analyze-code/{doc_id}", {"code": "def test(): pass"}),
    ]
    
    for name, method, endpoint, body in tests:
        try:
            if method == "GET":
                r = client.get(endpoint)
            else:
                r = client.post(endpoint, json=body)
            
            status_ok = r.status_code == 200
            status_mark = "[OK]" if status_ok else "[FAIL]"
            
            print(f"{status_mark} {name}: {r.status_code}")
            
            if not status_ok:
                print(f"     Error: {r.data.decode()[:100]}")
        except Exception as e:
            print(f"[ERROR] {name}: {str(e)[:80]}")

print("\n=== ALL TESTS COMPLETE ===")
