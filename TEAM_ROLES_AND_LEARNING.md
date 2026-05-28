# Corpus Forge - Team Roles, Implementation & Learning Guide

**Project**: Corpus Forge - AI Document Exploration Platform  
**Duration**: 11 days (May 18 - May 29, 2026)  
**Team Size**: 3 First-Year CS Students  

---

## 🎯 Project Overview

Corpus Forge is a **web application** that lets users upload documents (PDFs, text files, code) and then **ask AI questions** about them. The AI uses embeddings (vector search) to find relevant parts of documents and generates smart responses.

**The Loop**:
1. User uploads a document
2. App extracts text and creates embeddings (vector representations)
3. User asks a question
4. App finds relevant document chunks using vector search
5. AI reads those chunks and answers the question
6. App tracks token usage and remembers chat history

---

# 👤 PERSON A: Frontend Developer

## Role Summary
**Person A builds the user interface** — the HTML pages users see, the styling (CSS), and the interactivity (JavaScript). This person makes the app look good and respond to user clicks/inputs.

---

## What Person A Did (Simple Steps)

### Step 1: Created the Main Dashboard Template (`templates/base.html` + `dashboard.html`)
**Simple explanation**: Built the main page layout with:
- A sidebar on the left showing all uploaded documents
- A chat area in the middle for conversations
- A settings panel on the right to adjust AI behavior
- A header with the app title

**Key code areas**:
- `templates/base.html` - The master template with header and nav
- `templates/dashboard.html` - The main page layout combining all parts
- `templates/partials/documents_sidebar.html` - Shows list of documents (clickable)
- `templates/partials/chat_box.html` - Where messages appear
- `templates/partials/settings_panel.html` - Sliders and dropdowns
- `templates/partials/usage_stats.html` - Shows token usage stats

### Step 2: Styled Everything (`static/css/main.css`)
**Simple explanation**: Made the app look professional with colors, spacing, fonts, and responsive layout. Ensured it works on phones and desktops.

**What was styled**:
- Buttons (upload, send, delete)
- Form inputs (text areas, sliders)
- Chat messages (different colors for user vs AI)
- Sidebar (document list highlighting)
- Modal dialogs (upload form, delete confirmation)

### Step 3: Made the UI Interactive (`static/js/chat-stream.js`)
**Simple explanation**: Added JavaScript code to:
- Handle button clicks (upload, send, delete)
- Send data to the backend (HTTP requests)
- Display real-time chat streaming
- Show loading spinners while waiting
- Handle errors and show messages to users

**Key interactions**:
- Upload button → opens modal form
- Document click → selects that document
- Send button → submits question to AI
- Delete button → confirms and deletes document

---

## Libraries Person A Used

### 1. **HTML (HyperText Markup Language)**
   - **What it is**: The language for building web pages
   - **What it does**: Creates the structure of the page (headings, forms, buttons, lists)
   - **Example**: `<button id="send-btn">Send</button>` creates a clickable button
   - **Person A's use**: Built all the templates with proper semantic HTML (labels, forms, nav, main, etc.)

### 2. **CSS (Cascading Style Sheets)**
   - **What it is**: The language for styling web pages
   - **What it does**: Controls colors, fonts, spacing, layout, and responsiveness
   - **Example**: `button { background-color: blue; padding: 10px; }` makes buttons blue with padding
   - **Person A's use**: Created `main.css` with classes for buttons, forms, chat messages, sidebar, modals

### 3. **JavaScript (JS)**
   - **What it is**: The language that runs in web browsers
   - **What it does**: Makes pages interactive - responds to clicks, submits forms, updates content without page refresh
   - **Example**: `document.getElementById('btn').addEventListener('click', function() { alert('Clicked!'); })`
   - **Person A's use**: Implemented `chat-stream.js` to handle form submissions, streaming responses, and error display

### 4. **Fetch API (Browser API)**
   - **What it is**: A built-in browser feature for sending HTTP requests from JavaScript
   - **What it does**: Lets the frontend send data to the backend and receive responses asynchronously
   - **Example**: `fetch('/chat', { method: 'POST', body: JSON.stringify({query: 'hello'}) })`
   - **Person A's use**: Used to POST questions to the backend `/chat` route and receive AI responses

### 5. **Jinja2 Templating (Flask's Template Engine)**
   - **What it is**: A way to generate HTML dynamically with Python variables
   - **What it does**: Allows mixing Python logic with HTML so pages can show different content based on data from the backend
   - **Example**: `{% for doc in documents %}<li>{{ doc.title }}</li>{% endfor %}` loops through documents and displays them
   - **Person A's use**: Used in all HTML templates to display document lists, chat history, and settings from the database

### 6. **Bootstrap or CSS Framework** (Optional, may be used for styling)
   - **What it is**: Pre-made CSS classes for common UI patterns
   - **What it does**: Provides ready-to-use styles for buttons, forms, grids, modals, etc.
   - **Person A's use**: May have used for responsive grid layout and modal dialogs

---

## Key Frontend Concepts Person A Should Understand

### DOM (Document Object Model)
The DOM is a tree of all HTML elements on the page. JavaScript can read and modify it.
```javascript
// Get element from the page
const button = document.getElementById('send-btn');

// Listen for clicks
button.addEventListener('click', () => {
  console.log('Button clicked!');
});

// Modify the page
document.getElementById('chat-box').innerHTML += '<p>New message</p>';
```

### Events
When a user interacts with the page (click, type, submit), the browser fires an "event". JavaScript can "listen" for events and run code when they happen.
```javascript
// Listen for form submission
document.getElementById('chat-form').addEventListener('submit', (e) => {
  e.preventDefault();  // Stop default form behavior
  // Send data to backend instead
});
```

### Async/Await (Handling Delayed Responses)
When JavaScript sends a request to the backend, it takes time to get a response. We use `async/await` to wait for it without freezing the page.
```javascript
async function sendQuestion() {
  const response = await fetch('/chat', {
    method: 'POST',
    body: JSON.stringify({query: 'What is AI?'})
  });
  const data = await response.json();
  console.log(data);  // This runs AFTER the response arrives
}
```

### Server-Sent Events (Streaming)
Instead of waiting for one big response, the server can send many small chunks over time. The frontend listens and displays each chunk as it arrives.
```javascript
const response = await fetch('/chat', {...});
const reader = response.body.getReader();
while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  console.log(new TextDecoder().decode(value));  // Process each chunk
}
```

---

## 🧠 Learning Check: Questions for Person A

**Basic Understanding**
1. What is the difference between HTML, CSS, and JavaScript? What does each one do?
2. Why do we use templates (Jinja2) instead of just writing HTML directly?
3. What is the DOM, and why would we need to modify it after a page loads?

**Practical Implementation**
4. How would you make a button that changes color when you hover over it? (Answer: CSS `:hover` selector)
5. How would you listen for a button click and run some code? (Answer: `addEventListener('click', ...)`)
6. What is the Fetch API, and why can't you just use regular function calls to talk to the backend?

**Debugging & Testing**
7. If a button click doesn't work, what tools would you use to debug it? (Hint: Browser DevTools - F12)
8. If data isn't showing in the chat box, how would you check if it was received from the backend?
9. How would you test that the upload form actually sends the file to the backend?

**Design Thinking**
10. Why is it important to show a loading spinner while the AI is generating a response?
11. What happens if the network connection fails while streaming a response? Should we handle it?
12. If a user uploads a very large file, should the frontend do any validation before sending it?

---

---

# 🧠 PERSON B: AI & Embeddings Specialist

## Role Summary
**Person B builds the AI brains of the app** — the services that handle text extraction, vectorization, and semantic search. This person also handles the core AI response generation using Google's Gemini API.

---

## What Person B Did (Simple Steps)

### Step 1: Implemented Document Text Extraction (`services/document_processor.py`)
**Simple explanation**: Created functions to read text from different file types:
- **PDF files**: Used `pdfplumber` to extract text page-by-page
- **Text files (.txt, .md)**: Read raw text, handle encoding issues
- **Code files (.py, .js, etc.)**: Extract code and detect language
- **DOCX files**: Extract paragraphs from Word documents

**Key functions**:
- `extract_text_from_pdf()` - Reads PDFs, tries OCR as fallback
- `extract_text_from_txt()` - Reads text files, handles encoding
- `extract_text_from_code()` - Reads code and extracts function/class names
- `extract_text_from_docx()` - Reads Word documents
- `get_preview_text()` - Creates a short preview (first 500 chars)

### Step 2: Implemented Embeddings Service (`services/embeddings.py`)
**Simple explanation**: Created a service that:
1. **Chunks text** - Splits long documents into smaller pieces (vectors must be small)
2. **Generates embeddings** - Converts each chunk into a vector (array of numbers) using Google's API
3. **Stores vectors** - Saves them in ChromaDB (a vector database)
4. **Retrieves relevant chunks** - When user asks a question, finds the most similar chunks using vector similarity

**Key functions**:
- `__init__()` - Initializes Google GenAI and ChromaDB clients
- `_chunk_text()` - Splits document into overlapping chunks (~1000 chars each)
- `embed_document()` - Converts each chunk to a vector and stores it
- `retrieve_context()` - Finds chunks most similar to a query
- `delete_document_embeddings()` - Cleans up ChromaDB when document is deleted

### Step 3: Implemented AI Agent Service (`services/ai_agent.py`)
**Simple explanation**: Created a service that:
1. **Generates chat responses** - Sends context + question to Google Gemini API and streams response
2. **Counts tokens** - Tracks how many tokens (words) the AI used
3. **Generates flashcards** - Creates QA pairs from document text
4. **Generates quizzes** - Creates multiple-choice questions
5. **Analyzes code** - Provides code review and architecture analysis

**Key functions**:
- `__init__()` - Initializes Google Gemini model
- `generate_response()` - Streams AI response given context + question
- `_build_system_prompt()` - Creates system instruction based on audience + tone
- `_count_tokens()` - Estimates or counts tokens used
- `generate_flashcards()` - Creates study flashcards from text
- `generate_quiz()` - Creates quiz questions from text
- `analyze_architecture()` - Analyzes code structure
- `review_code()` - Provides code review

---

## Libraries Person B Used

### 1. **Google GenAI Library** (`google.genai`)
   - **What it is**: Official Python client for Google's Gemini AI models
   - **What it does**: Lets you send text to Google's AI and get responses. Can generate embeddings too.
   - **Example**:
     ```python
     client = genai.Client(api_key="sk-...")
     response = client.models.generate_content(
       model="gemini-2.5-flash",
       contents="What is Python?"
     )
     ```
   - **Person B's use**: Used to generate chat responses, count tokens, and create embeddings

### 2. **pdfplumber**
   - **What it is**: A Python library for reading PDF files
   - **What it does**: Opens PDFs and extracts text from each page
   - **Example**:
     ```python
     import pdfplumber
     with pdfplumber.open("document.pdf") as pdf:
       for page in pdf.pages:
         text = page.extract_text()
     ```
   - **Person B's use**: In `extract_text_from_pdf()` to pull text from uploaded PDFs

### 3. **pytesseract** (Optional for OCR)
   - **What it is**: Python wrapper for Tesseract OCR (Optical Character Recognition)
   - **What it does**: Converts images (like scanned PDFs) into text using machine learning
   - **Example**:
     ```python
     from PIL import Image
     import pytesseract
     img = Image.open("scanned_page.png")
     text = pytesseract.image_to_string(img)
     ```
   - **Person B's use**: Fallback in `extract_text_from_pdf()` for scanned PDFs with no extractable text

### 4. **Pillow** (`PIL`)
   - **What it is**: A Python image processing library
   - **What it does**: Load, manipulate, and analyze images
   - **Example**:
     ```python
     from PIL import Image
     img = Image.open("photo.jpg")
     img.save("resized.jpg", size=(100, 100))
     ```
   - **Person B's use**: Convert PDF pages to images for OCR processing

### 5. **python-docx**
   - **What it is**: A Python library for reading and writing Word (.docx) files
   - **What it does**: Extract text from Word documents while preserving structure
   - **Example**:
     ```python
     from docx import Document
     doc = Document("file.docx")
     for para in doc.paragraphs:
       print(para.text)
     ```
   - **Person B's use**: In `extract_text_from_docx()` to extract text from Word files

### 6. **ChromaDB**
   - **What it is**: A vector database designed for AI applications
   - **What it does**: Stores and searches embeddings (vectors) using similarity search
   - **Example**:
     ```python
     import chromadb
     client = chromadb.PersistentClient(path="./.chromadb")
     collection = client.get_or_create_collection("docs")
     collection.add(ids=["1"], documents=["Hello world"], embeddings=[[0.1, 0.2, ...]])
     results = collection.query(query_texts=["greeting"], n_results=3)
     ```
   - **Person B's use**: Stores embeddings in `embed_document()` and retrieves them in `retrieve_context()`

### 7. **Pathlib** (`from pathlib import Path`)
   - **What it is**: Python's modern way to handle file paths
   - **What it does**: Create, check, and manipulate file paths in a cross-platform way
   - **Example**:
     ```python
     from pathlib import Path
     p = Path(".chromadb")
     p.mkdir(parents=True, exist_ok=True)  # Create directory if not exists
     if p.exists():
       print("Directory exists")
     ```
   - **Person B's use**: Ensured ChromaDB path exists before initializing

### 8. **Logging**
   - **What it is**: Python's built-in logging module
   - **What it does**: Records important events (info, warnings, errors) to help debug
   - **Example**:
     ```python
     import logging
     logger = logging.getLogger(__name__)
     logger.info(f"Extracted {len(text)} characters")
     logger.error(f"Failed to embed: {e}")
     ```
   - **Person B's use**: Added debug logs throughout services to track what's happening

---

## Key AI & Embeddings Concepts Person B Should Understand

### Embeddings (Vector Representations)
An embedding is a list of numbers that represents the *meaning* of text. Similar text has similar embeddings.
```
Text: "The cat sat on the mat"
Embedding: [0.1, -0.5, 0.8, 0.2, -0.3, ...]  (list of ~768 numbers)

Text: "A cat is sitting on a mat"
Embedding: [0.11, -0.48, 0.79, 0.21, -0.32, ...]  (very similar!)

Distance between them: 0.02 (very close = very similar)
```

### Semantic Search
Using embeddings to find *similar* content, not just keyword matches.
```
User asks: "How do cats climb?"
Vector search finds: "Cats use their claws to scale trees"
(Even though there's no keyword overlap!)
```

### Chunking
Large documents must be split into chunks because:
1. Embeddings API has token limits
2. We want fine-grained search results
3. Smaller pieces are faster to embed

```
Full document: "Python is a programming language. It was created in 1989..."
Chunk 1: "Python is a programming language. It was created in 1989..."
Chunk 2: "...and is used for web development, data science, and AI..."
Chunk 3: "...with a focus on readability and simplicity."
```

### Token Counting
Tokens are roughly 4 characters each (varies by language/model).
```
Text: "Hello World"
Tokens: approximately 3
Cost: more tokens = more expensive and slower
```

---

## 🧠 Learning Check: Questions for Person B

**Basic Understanding**
1. What is an embedding? Why do we need to convert text into vectors?
2. What does ChromaDB do? How is it different from a regular database?
3. Why do we need to chunk documents before embedding them?
4. What is the difference between extracting text from a PDF vs. OCR?

**Practical Implementation**
5. How would you extract text from a PDF that has been scanned (is an image)?
6. If a document is 100,000 words long, how would you decide chunk size?
7. How would you know if an embedding was successful? What would you log/check?
8. What happens if the embedding API call fails? Should you retry?

**Semantic Search & Retrieval**
9. A user asks "How to learn Python?" and you have a document about "Python programming tutorial". Would semantic search find it? Why?
10. If `retrieve_context()` returns 3 chunks, could they be duplicates? How would you prevent that?
11. How would you improve search results if they're not relevant enough?

**Performance & Optimization**
12. If a user uploads a 50 MB PDF, what could go wrong? How would you handle it?
13. How would you make embeddings faster for large documents?
14. Should you cache embeddings? If yes, how?

**Debugging & Testing**
15. If a question about a document returns "no context found", how would you debug?
16. How would you test that your chunking strategy works well?

---

---

# 🔧 PERSON C: Backend Developer

## Role Summary
**Person C builds the backend** — the Flask routes (endpoints) that handle HTTP requests from the frontend. This person connects the frontend to the database and AI services.

---

## What Person C Did (Simple Steps)

### Step 1: Implemented the Upload Route (`app.py` - `/upload`)
**Simple explanation**: Created a route that:
1. Receives a file from the frontend
2. Validates it (is it a PDF, text file, or code?)
3. Saves it to disk with a secure name
4. Extracts text from it
5. Creates a database entry
6. Starts the embedding process
7. Returns success/error to frontend

**Key code**:
```python
@app.route('/upload', methods=['POST'])
def upload_document():
    # Get file from request
    # Validate file type
    # Save file securely
    # Extract text
    # Save to database
    # Embed document
    # Return result
```

### Step 2: Implemented the Delete Route (`app.py` - `/delete/<doc_id>`)
**Simple explanation**: Created a route that:
1. Finds the document by ID
2. Deletes the file from disk
3. Deletes embeddings from ChromaDB
4. Deletes the database entry
5. Returns redirect to dashboard

### Step 3: Implemented the Chat Route (`app.py` - `/chat`)
**Simple explanation**: Created the core AI conversation route that:
1. Receives a question and document ID
2. Retrieves the relevant document chunks (embeddings search)
3. Sends chunks + question to AI
4. Streams AI response back to frontend
5. Saves the conversation to database
6. Logs token usage

**Key code**:
```python
@app.route('/chat', methods=['POST'])
def chat():
    # Get query and document_id from request
    # Retrieve context from ChromaDB
    # Call AI agent to generate response
    # Stream response chunks to frontend
    # Save chat message to database
    # Log usage
```

### Step 4: Implemented the Settings Route (`app.py` - `/update-settings`)
**Simple explanation**: Created a route that:
1. Receives updated settings (temperature, tone, etc.)
2. Validates values are in correct range
3. Saves to database
4. Returns success

### Step 5: Implemented Phase 2 Routes (`app.py`)
**Simple explanation**: Created additional routes for:
- `/generate-flashcards` - Generate study flashcards from a document
- `/generate-quiz` - Generate quiz questions from a document
- `/analyze-code/<doc_id>` - Analyze code structure and quality

---

## Libraries Person C Used

### 1. **Flask**
   - **What it is**: A Python web framework for building web applications
   - **What it does**: Handles HTTP requests (GET, POST, etc.) and routes them to the right function
   - **Example**:
     ```python
     from flask import Flask, request, jsonify
     app = Flask(__name__)
     
     @app.route('/hello', methods=['GET'])
     def hello():
       return jsonify({'message': 'Hello!'})
     ```
   - **Person C's use**: Built all the routes (/upload, /chat, /delete, /update-settings, etc.)

### 2. **SQLAlchemy** (via Flask-SQLAlchemy)
   - **What it is**: An Object-Relational Mapping (ORM) library for databases
   - **What it does**: Lets you work with databases using Python objects instead of writing SQL
   - **Example**:
     ```python
     doc = Document(filename="paper.pdf", title="Research Paper")
     db.session.add(doc)
     db.session.commit()  # Save to database
     
     # Query
     all_docs = Document.query.all()
     doc_by_id = Document.query.get(1)
     ```
   - **Person C's use**: Saved and retrieved documents, chat messages, flashcards, etc.

### 3. **Werkzeug** (via Flask)
   - **What it is**: A utility library that Flask uses under the hood
   - **What it does**: Provides file handling, security utilities, and HTTP helpers
   - **Example**:
     ```python
     from werkzeug.utils import secure_filename
     safe_name = secure_filename("my file (2).pdf")  # Returns "my_file_2.pdf"
     ```
   - **Person C's use**: Secured filenames before saving uploaded files

### 4. **Python-dotenv**
   - **What it is**: A library for loading environment variables from `.env` files
   - **What it does**: Reads secrets (like API keys) from `.env` so they're not hardcoded
   - **Example**:
     ```python
     from dotenv import load_dotenv
     import os
     load_dotenv()
     api_key = os.getenv('GOOGLE_API_KEY')
     ```
   - **Person C's use**: Loaded the Google API key from `.env` file

### 5. **Logging**
   - **What it is**: Python's built-in logging module
   - **What it does**: Records events for debugging and monitoring
   - **Example**:
     ```python
     import logging
     logger = logging.getLogger(__name__)
     logger.info(f"Uploaded document: {filename}")
     logger.error(f"Upload failed: {error}")
     ```
   - **Person C's use**: Logged all route activities for debugging

### 6. **JSON** (Python built-in)
   - **What it is**: A library for working with JSON (JavaScript Object Notation)
   - **What it does**: Convert Python objects to/from JSON for API responses
   - **Example**:
     ```python
     import json
     data = {'message': 'success', 'id': 123}
     json_string = json.dumps(data)  # Convert to JSON string
     ```
   - **Person C's use**: Returned JSON responses from routes

### 7. **Pathlib** (`from pathlib import Path`)
   - **What it is**: Modern Python module for file path operations
   - **What it does**: Create, check, and manipulate file paths
   - **Example**:
     ```python
     from pathlib import Path
     uploads = Path("static/uploads")
     uploads.mkdir(parents=True, exist_ok=True)
     ```
   - **Person C's use**: Managed upload folder creation and file paths

---

## Key Backend Concepts Person C Should Understand

### HTTP Methods
Different operations use different HTTP methods:
- **GET**: Retrieve data (no side effects)
- **POST**: Create/submit data (causes changes)
- **PUT**: Update existing data
- **DELETE**: Remove data

```python
@app.route('/documents', methods=['GET'])
def list_documents():
    return jsonify(all_documents)

@app.route('/upload', methods=['POST'])
def upload():
    # Create new document
    pass
```

### Request/Response Flow
1. Frontend sends HTTP request with data (JSON or form)
2. Backend route receives it
3. Route processes it (talks to database, AI, etc.)
4. Route sends back HTTP response with data/status code
5. Frontend receives response and updates UI

```python
@app.route('/chat', methods=['POST'])
def chat():
    # 1. Receive request
    data = request.get_json()
    query = data['query']
    
    # 2. Process
    response = ai_agent.generate_response(query)
    
    # 3. Send back
    return jsonify({'response': response})
```

### Status Codes
HTTP responses include status codes that tell the frontend if things worked:
- **200**: OK - Request succeeded
- **201**: Created - Resource was created successfully
- **400**: Bad Request - Frontend sent invalid data
- **404**: Not Found - Resource doesn't exist
- **500**: Server Error - Something went wrong on backend

```python
if not file:
    return jsonify({'error': 'No file'}), 400  # Bad request

if not document:
    return jsonify({'error': 'Not found'}), 404  # Not found

return jsonify({'success': True}), 200  # Success
```

### Database Transactions
When multiple operations must succeed together, use transactions:
```python
try:
    doc = Document(filename="test.pdf")
    db.session.add(doc)
    db.session.commit()  # Save to DB
except Exception as e:
    db.session.rollback()  # Undo if something fails
    logger.error(f"Error: {e}")
```

### Streaming Responses
For large/long-running operations, stream data instead of waiting:
```python
def generate_stream():
    for chunk in ai_response:
        yield f"data: {chunk}\n\n"  # Send one chunk at a time

return generate_stream(), 200, {
    'Content-Type': 'text/event-stream'
}
```

---

## 🧠 Learning Check: Questions for Person C

**Basic Understanding**
1. What is a route? How does it connect to a URL?
2. Why is Flask needed? What would happen if we just tried to handle HTTP ourselves?
3. What is an ORM like SQLAlchemy? How is it better than writing SQL directly?
4. What are HTTP status codes? Name 5 and explain when you'd use them.

**Practical Implementation**
5. A user uploads a file. Walk me through all the steps from upload button click to database save.
6. A user asks "What is Python?" How does the `/chat` route get the question to the AI and back to the user?
7. How would you validate that a file extension is allowed before saving it?
8. If embedding fails but upload succeeds, what should you do?

**Database Operations**
9. How would you query the database to find all documents uploaded by a specific user?
10. If you need to save both a Document and a ChatMessage at the same time, how would you ensure both succeed or both fail?
11. What's the difference between `db.session.add()` and `db.session.commit()`?
12. If you accidentally deleted the wrong document from the database, how would you recover it?

**Error Handling & Security**
13. What happens if a user uploads a file named `../../evil.txt`? How would you prevent path traversal attacks?
14. Should you trust file extensions? How would you validate file types safely?
15. If the AI API is down, what should your `/chat` route return to the user?

**Debugging & Testing**
16. How would you test the `/upload` route without using the frontend?
17. If the `/chat` response is slow, where would you start debugging?
18. How would you log useful information to help debug production issues?

---

---

# 🌉 How All Three Work Together

## The Complete Flow

```
1. PERSON A (Frontend): User clicks "Upload"
        ↓
2. Frontend sends file to backend
        ↓
3. PERSON C (Backend): /upload route receives file
        ↓
4. PERSON B: document_processor extracts text
        ↓
5. PERSON C: Saves document to database
        ↓
6. PERSON B: embeddings_service chunks and embeds text
        ↓
7. ChromaDB stores vectors
        ↓
   [User selects document and asks question]
        ↓
8. PERSON A: Sends question to backend
        ↓
9. PERSON C: /chat route receives question
        ↓
10. PERSON B: retrieve_context searches embeddings
        ↓
11. PERSON B: generate_response calls Google Gemini
        ↓
12. PERSON C: Streams response back to frontend
        ↓
13. PERSON A: Displays response in chat
        ↓
14. PERSON C: Saves chat message to database
```

## What Each Person Needs to Know About the Others

### Person A Needs to Know (Frontend):
- **From Person C**: What routes exist? What data do they return? What status codes mean what?
- **From Person B**: How long do embedding operations take? Should I show a loading spinner?

### Person B Needs to Know (AI/Embeddings):
- **From Person C**: Which routes call my services? What happens if they fail?
- **From Person A**: How much text should I chunk at a time? What's the max response size?

### Person C Needs to Know (Backend):
- **From Person A**: What format is the data sent from forms? What should error messages look like?
- **From Person B**: How long do services take? What exceptions should I handle?

---

# 📋 Common Issues & Solutions

## Person A Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Button clicks don't work | JavaScript not loaded or selector wrong | Check browser console, verify class names |
| Forms don't submit data | Missing `type="submit"` on button | Add submit button or call `form.submit()` |
| Chat doesn't stream | Streaming handler incomplete | Implement fetch stream reading loop |
| Styling looks broken | CSS file not loaded | Check `<link>` tag, verify file path |

## Person B Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Embeddings fail | API token limit hit | Reduce chunk size |
| ChromaDB not found | Collection doesn't exist | Handle exception, create collection |
| PDF extraction empty | Scanned image PDF | Use OCR fallback |
| Memory issues | Document too large | Chunk more aggressively |

## Person C Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Route not defined | Check `@app.route()` decorator |
| File won't save | Permission denied | Ensure `static/uploads/` exists and writable |
| Database error | Schema mismatch | Run `database/init_db.py` |
| CORS error | Frontend from different origin | Configure Flask CORS if needed |

---

# ✅ Verification Checklist

Verify each person's work:

**Person A (Frontend)**
- [ ] All HTML templates render without errors
- [ ] CSS styling looks professional
- [ ] All buttons and forms are interactive
- [ ] Chat displays messages from both user and AI
- [ ] Settings sliders work and affect AI responses
- [ ] Usage dashboard updates after chat

**Person B (AI/Embeddings)**
- [ ] Document processor extracts text from PDF, TXT, and code files
- [ ] Embeddings service creates ChromaDB collections
- [ ] Semantic search finds relevant document chunks
- [ ] AI agent generates responses with correct temperature/tone
- [ ] Flashcard and quiz generation work
- [ ] Code analysis provides useful feedback

**Person C (Backend)**
- [ ] /upload route saves files and creates DB entries
- [ ] /delete route removes files and DB entries
- [ ] /chat route retrieves context and streams responses
- [ ] /update-settings validates and saves settings
- [ ] All routes return appropriate status codes
- [ ] Error messages are clear and helpful
- [ ] Database transactions succeed/fail together

---

# 🚀 Next Steps for Each Person

**Person A (Frontend)**
- [ ] Implement mobile-responsive design
- [ ] Add loading indicators for async operations
- [ ] Implement markdown rendering for code blocks in chat
- [ ] Add dark mode toggle

**Person B (AI/Embeddings)**
- [ ] Implement token-based chunking (use `tiktoken`)
- [ ] Add caching for embeddings
- [ ] Implement re-ranking for better search results
- [ ] Add support for more file types (EPUB, Word, Excel)

**Person C (Backend)**
- [ ] Add user authentication and multi-user support
- [ ] Implement rate limiting to prevent API abuse
- [ ] Add background job processing for large documents
- [ ] Create admin dashboard for monitoring

---

**End of Guide**  
Last Updated: May 27, 2026
