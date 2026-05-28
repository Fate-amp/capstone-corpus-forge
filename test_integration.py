#!/usr/bin/env python
"""Integration test for document upload, chat, and quiz generation."""

import requests
import json
from pathlib import Path
import time

BASE_URL = 'http://localhost:5000'

print('=== TEST 1: Upload TXT Document ===')
test_file = Path('test_ww2.txt')
test_content = '''World War 2 (1939-1945)

World War 2 was a global military conflict that lasted from 1939 to 1945. It involved most of the world's nations divided into two opposing military alliances: the Allies and the Axis.

Key Facts:
- Started on September 1, 1939, with Germany's invasion of Poland
- Ended on September 2, 1945, with Japan's surrender
- Approximately 70-85 million deaths
- Major participants: Germany, Japan, Italy, United States, Soviet Union, United Kingdom, China

Major Events:
1. Pearl Harbor Attack (December 7, 1941) - Japan attacks US naval base
2. D-Day (June 6, 1944) - Allied invasion of Normandy
3. Hiroshima and Nagasaki bombings (August 1945)
4. Holocaust - Genocide of approximately 6 million Jews

Outcome:
- Axis powers defeated
- United Nations formed
- Cold War began
- European and Asian territories reorganized
'''
test_file.write_text(test_content)

try:
    with open(test_file, 'rb') as f:
        files = {'file': f}
        response = requests.post(f'{BASE_URL}/upload', files=files)
    
    print(f'Upload status: {response.status_code}')
    result = response.json()
    if response.ok:
        doc_id = result['document_id']
        print(f'✓ Document uploaded: ID={doc_id}')
    else:
        print(f'✗ Error: {result}')
        exit(1)
except Exception as e:
    print(f'✗ Upload failed: {str(e)}')
    test_file.unlink()
    exit(1)

time.sleep(1)

print(f'\n=== TEST 2: Chat with Document ===')
try:
    response = requests.post(f'{BASE_URL}/chat',
        json={
            'query': 'When did World War 2 start and end?',
            'document_id': doc_id
        },
        stream=True
    )
    
    print(f'Chat status: {response.status_code}')
    if response.ok:
        full_response = ''
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                chunk = line[6:].decode('utf-8', errors='ignore')
                full_response += chunk
        
        has_content = any(term in full_response for term in ['1939', '1945', 'started', 'September', 'World War 2'])
        if has_content:
            print(f'✓ Response contains document content')
            print(f'  Response preview: {full_response[:120]}...')
        else:
            print(f'⚠ Response may not contain expected content')
            print(f'  Response: {full_response[:200]}')
    else:
        print(f'✗ Chat error: {response.status_code}')
except Exception as e:
    print(f'✗ Chat failed: {str(e)}')

print(f'\n=== TEST 3: Generate Quiz ===')
try:
    response = requests.post(f'{BASE_URL}/generate-quiz',
        json={
            'document_id': doc_id,
            'num_questions': 2
        }
    )
    
    print(f'Quiz generation status: {response.status_code}')
    if response.ok:
        quiz_result = response.json()
        if 'quiz_id' in quiz_result:
            print(f'✓ Quiz generated: ID={quiz_result["quiz_id"]}')
            print(f'  Title: {quiz_result.get("title", "N/A")}')
            print(f'  Questions: {len(quiz_result.get("questions", []))}')
            if quiz_result.get('questions'):
                first_q = quiz_result['questions'][0]
                print(f'  Sample Q: {first_q["question"][:80]}...')
        else:
            print(f'✗ Quiz response missing quiz_id: {quiz_result}')
    else:
        error_text = response.text if response.status_code >= 400 else response.json()
        print(f'✗ Quiz error {response.status_code}: {str(error_text)[:200]}')
except Exception as e:
    print(f'✗ Quiz failed: {str(e)}')

print(f'\n=== TEST 4: Generate Flashcards ===')
try:
    response = requests.post(f'{BASE_URL}/generate-flashcards',
        json={
            'document_id': doc_id,
            'num_cards': 2
        }
    )
    
    print(f'Flashcard generation status: {response.status_code}')
    if response.ok:
        result = response.json()
        if 'flashcards' in result:
            print(f'✓ Flashcards generated: {len(result["flashcards"])} cards')
            if result.get('flashcards'):
                card = result['flashcards'][0]
                print(f'  Sample card: Q: {card["question"][:60]}...')
        else:
            print(f'⚠ Flashcard response: {result}')
    else:
        print(f'✗ Flashcard error {response.status_code}')
except Exception as e:
    print(f'✗ Flashcards failed: {str(e)}')

test_file.unlink()
print('\n=== All tests completed ===')
