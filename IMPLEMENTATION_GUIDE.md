# Implementation Guide - Corpus Forge

**Last Updated**: May 18, 2026  
**Status**: Skeleton complete, ready for Day 1 implementation

---

## Overview

This guide provides step-by-step implementation instructions for each day of the project.

All skeleton files are in place with:
- ✅ Clear TODO comments marking what needs implementation
- ✅ Docstrings explaining the purpose of each function
- ✅ Placeholder code showing the expected flow
- ✅ Comments with implementation checklists

---

## PHASE 1: Core Chat Loop (Days 1-5)

### DAY 1: Project Setup & Environment

**Goal**: Get everyone running the Flask app locally  
**Time**: 2 hours  
**Assigned to**: Everyone (pair session)

#### Tasks

1. **Environment Setup** (all together)
   ```bash
   # Clone repo
   git clone <repo-url>
   cd capstone-corpus-forge
   
   # Create venv
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Google API Key**
   - Go to [Google AI Studio](https://aistudio.google.com/apikey)
   - Create a new API key
   - Copy `.env.template` to `.env`
   - Add your key: `GOOGLE_API_KEY=sk-...`

3. **Initialize Database**
   ```bash
   python database/init_db.py
   ```
   Expected output:
   ```
   Initializing database...
   ✓ Database tables created
   ✓ Default settings created
   ✓ Uploads directory ready: static/uploads
   ✓ ChromaDB directory ready: ./.chromadb
   ✓ Database initialization complete!
   ```

4. **Verify Flask Starts**
   ```bash
   python app.py
   ```
   Should see:
   ```
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```
   - Open http://localhost:5000 in browser
   - Should see dashboard with empty documents list

5. **Quick Check**
   - [ ] All 3 team members can run `python app.py`
   - [ ] Dashboard loads at localhost:5000
   - [ ] No Python errors in console
   - [ ] upload-btn exists in HTML (you can inspect it)

**Deliverable**: All team members have working Flask server + empty dashboard

---

### DAY 2: Document Upload & Management

**Goal**: Upload PDF/TXT files → saved to disk → displayed in sidebar  
**Time**: 6 hours  
**Assigned to**: Person A (backend) + Person B (frontend)

#### Implementation Checklist

**Backend** (`app.py` - `upload_document()` route):

1. Extract the uploaded file from request
   ```python
   if 'file' not in request.files:
       return redirect(url_for('dashboard'))
   file = request.files['file']
   ```

2. Validate file
   ```python
   if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
       # Reject file, log warning
   ```

3. Save file to disk
   ```python
   filename = get_secure_filename(file.filename)
   file_type = get_file_type(filename)
   file_path = f"{app.config['UPLOAD_FOLDER']}/{filename}"
   file.save(file_path)
   ```

4. Extract text (this is already implemented!)
   ```python
   from services.document_processor import extract_text_by_file_type
   text = extract_text_by_file_type(file_path, file_type)
   ```

5. Generate preview
   ```python
   from services.document_processor import get_preview_text
   preview = get_preview_text(text)
   ```

6. Create Document in database
   ```python
   doc = Document(
       filename=filename,
       title=filename,  # or parse title from filename
       content_preview=preview,
       file_path=file_path,
       file_type=file_type
   )
   db.session.add(doc)
   db.session.commit()
   ```

7. Trigger embeddings (DAY 3 WILL IMPLEMENT THIS)
   ```python
   # For now, just add a TODO comment
   # TODO: app.embeddings_service.embed_document(doc.id, text)
   ```

8. Redirect to dashboard
   ```python
   return redirect(url_for('dashboard'))
   ```

**Delete** (`app.py` - `delete_document()` route):

1. Query document
   ```python
   doc = Document.query.get(doc_id)
   if not doc:
       return redirect(url_for('dashboard'))
   ```

2. Delete file
   ```python
   from pathlib import Path
   Path(doc.file_path).unlink(missing_ok=True)
   ```

3. Delete from ChromaDB (TODO for Day 3)
   ```python
   # TODO: app.embeddings_service.delete_document_embeddings(doc_id)
   ```

4. Delete from database
   ```python
   db.session.delete(doc)
   db.session.commit()
   ```

5. Redirect
   ```python
   return redirect(url_for('dashboard'))
   ```

**Frontend** (templates):

1. Make document items selectable
   - Add click handler in `documents_sidebar.html`
   - Update `selected-doc-title` in dashboard

2. Implement delete button
   - Add POST request to `/delete/<doc_id>`
   - Add confirmation dialog

3. Add upload form
   - Uncomment/implement upload modal in `dashboard.html`
   - Handle form submission

**Testing**:
```python
# Manual test in browser:
# 1. Click "+ Upload" button
# 2. Select a PDF or TXT file from your computer
# 3. File should appear in sidebar
# 4. Click delete → file should disappear
```

**Deliverable**: Upload document → appears in sidebar. Delete → removed.

---

### DAY 3: Vector Embeddings & ChromaDB

**Goal**: Uploaded documents are chunked, embedded, and searchable  
**Time**: 6 hours  
**Assigned to**: Person C (AI/embeddings)

#### Implementation Checklist

**Embeddings Service** (`services/embeddings.py`):

1. **`_chunk_text()` method** (helper):
   - Takes full text + chunk_size + overlap parameters
   - Splits into overlapping chunks
   - Returns list of text chunks
   - Pseudo-code:
     ```python
     chunks = []
     char_size = chunk_size * 4  # rough token to char conversion
     char_overlap = overlap * 4
     
     pos = 0
     while pos < len(text):
         chunk = text[pos:pos + char_size]
         # Try to end at sentence boundary
         last_period = chunk.rfind('.')
         if last_period > len(chunk) * 0.8:
             chunk = chunk[:last_period + 1]
         chunks.append(chunk)
         pos += len(chunk) - char_overlap
     
     return [c for c in chunks if c.strip()]
     ```

2. **`embed_document()` method** (main):
   - Chunk the document text: `chunks = self._chunk_text(document_text)`
   - Get/create ChromaDB collection: `self.client.get_or_create_collection(f"doc_{doc_id}")`
   - For each chunk:
     - Embed using `genai.embed_content()` (already shown in docstring)
     - Store in ChromaDB using `collection.add()`
   - Return collection name

3. **`retrieve_context()` method**:
   - Get collection for document: `self.client.get_collection(f"doc_{doc_id}")`
   - Query with: `collection.query(query_texts=[query], n_results=top_k)`
   - Concatenate returned chunks with newlines
   - Return as string

4. **`delete_document_embeddings()` method**:
   - Get collection for document
   - Delete with: `self.client.delete_collection(name=collection_name)`
   - Return True on success

**Integration with Upload** (Day 2 follow-up in `app.py`):

After creating Document entry (in `upload_document()`):
```python
# Trigger embeddings
app.embeddings_service.embed_document(doc.id, text)
```

After deleting Document (in `delete_document()`):
```python
# Delete embeddings
app.embeddings_service.delete_document_embeddings(doc_id)
```

**Testing**:
```bash
# After uploading a document, verify ChromaDB collection exists:
# 1. Open .chromadb folder and check for created files
# 2. Or add debug print in retrieve_context() and query in /chat

# Manual verification:
# 1. Upload document
# 2. Check .chromadb/ folder has new collection
# 3. Query should work (test in Day 4)
```

**Deliverable**: Upload document → ChromaDB collection created with embeddings. Semantic search works.

---

### DAY 4: AI Chat & Streaming Responses

**Goal**: Ask questions → get AI responses in real-time  
**Time**: 8 hours  
**Assigned to**: Person A (backend `/chat` route) + Person B (frontend streaming) + Person C (AI agent)

#### Implementation Checklist

**AI Agent** (`services/ai_agent.py`):

1. **Constructor** (`__init__`):
   - Initialize GenAI: `genai.configure(api_key=api_key)`
   - Create model: `self.model = genai.GenerativeModel(model_name)`
   - Store as instance variables

2. **`generate_response()` method**:
   - Build system prompt using `_build_system_prompt()`
   - Build full message (system + context + query)
   - Count input tokens: `genai.count_tokens(full_message)`
   - Call `self.model.generate_content(..., stream=True)`
   - Yield chunks as they come in
   - Count output tokens of full response
   - Return (tokens_input, tokens_output) tuple

**Backend Route** (`app.py` - `chat()` function):

1. Parse request
   ```python
   data = request.get_json() or request.form
   query = data.get('query', '')
   doc_id = data.get('document_id')
   ```

2. Get settings
   ```python
   settings = Settings.query.first() or Settings()
   ```

3. Retrieve context from ChromaDB
   ```python
   context = app.embeddings_service.retrieve_context(query, doc_id)
   ```

4. Generate response (streaming generator)
   ```python
   gen = app.ai_agent.generate_response(
       query=query,
       context=context,
       temperature=settings.temperature,
       # ... other params
   )
   ```

5. Create streaming response back to client
   ```python
   # Option 1: Simple (non-streaming for now, stream in Day 4 polish)
   response_text = ""
   for chunk in gen:
       response_text += chunk
   
   # tokens_input, tokens_output = next(gen)  # Get token counts from generator
   ```

6. Save to database
   ```python
   msg = ChatMessage(
       document_id=doc_id,
       query=query,
       response=response_text,
       tokens_input=tokens_input,
       tokens_output=tokens_output,
       tokens_used=tokens_input + tokens_output
   )
   db.session.add(msg)
   ```

7. Log usage
   ```python
   from services.usage_tracker import UsageTracker
   UsageTracker.log_usage(
       model_name=settings.model_choice,
       tokens_input=tokens_input,
       tokens_output=tokens_output,
       request_type='chat'
   )
   ```

8. Return response to frontend
   ```python
   return jsonify({
       'response': response_text,
       'tokens': tokens_input + tokens_output
   })
   ```

**Frontend** (`templates/chat_box.html` + `static/js/chat-stream.js`):

1. **Form Submission**:
   ```javascript
   chatForm.addEventListener('submit', async (e) => {
       e.preventDefault();
       const query = chatInput.value.trim();
       const docId = selectedDocIdInput.value;
       
       if (!query || !docId) return;
       
       // Send to /chat
       const response = await fetch('/chat', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({query, document_id: docId})
       });
       
       const data = await response.json();
       
       // Add to chat display
       appendMessageToChat(query, true);  // user message
       appendMessageToChat(data.response, false);  // AI response
       
       chatInput.value = '';  // clear input
   });
   ```

2. **Append Message to Chat**:
   ```javascript
   function appendMessageToChat(message, isUserMessage) {
       const div = document.createElement('div');
       div.className = `chat-message ${isUserMessage ? 'user' : 'ai'}`;
       
       const content = document.createElement('div');
       content.className = 'chat-message-content';
       content.textContent = message;
       
       div.appendChild(content);
       chatHistory.appendChild(div);
       
       // Auto-scroll
       chatHistory.scrollTop = chatHistory.scrollHeight;
   }
   ```

3. **Select Document**:
   ```javascript
   // In documents_sidebar.html
   document.querySelectorAll('.document-item').forEach(item => {
       item.addEventListener('click', function() {
           // Remove previous selection
           document.querySelectorAll('.document-item').forEach(i => 
               i.classList.remove('selected')
           );
           this.classList.add('selected');
           
           // Update form
           selectedDocIdInput.value = this.dataset.docId;
           chatInput.disabled = false;
           sendBtn.disabled = false;
           
           // Clear chat history for new document
           chatHistory.innerHTML = '';
       });
   });
   ```

**Testing**:
```
Manual test flow:
1. Upload a document (PDF or TXT)
2. Click on document in sidebar
3. Type a question in chat box
4. Click Send
5. Response should appear in chat
6. Check token count displayed
```

**Deliverable**: Ask question about document → get AI response displayed in chat with token count

---

### DAY 5: Settings & Usage Dashboard

**Goal**: Users can tweak parameters; see usage stats  
**Time**: 4 hours  
**Assigned to**: Person B (frontend forms) + Person A (backend settings endpoint)

#### Implementation Checklist

**Backend** (`app.py` - `update_settings()` route):

1. Get form data
   ```python
   data = request.form or request.get_json()
   ```

2. Get or create Settings entry
   ```python
   settings = Settings.query.first() or Settings()
   ```

3. Update fields
   ```python
   settings.temperature = float(data.get('temperature', 0.7))
   settings.top_p = float(data.get('top_p', 0.9))
   settings.audience_level = data.get('audience_level', 'intermediate')
   settings.tone = data.get('tone', 'friendly')
   settings.max_tokens_per_response = int(data.get('max_tokens_per_response', 1000))
   ```

4. Validate ranges
   ```python
   settings.temperature = max(0, min(2.0, settings.temperature))
   settings.top_p = max(0, min(1.0, settings.top_p))
   ```

5. Save
   ```python
   db.session.add(settings)
   db.session.commit()
   ```

6. Redirect
   ```python
   return redirect(url_for('dashboard'))
   ```

**Frontend** (`templates/partials/settings_panel.html`):

1. Form is already structured, just ensure:
   - All input names match backend expectations
   - Sliders update display values in real-time
   - Submit button sends to `/update-settings`

2. JavaScript (already in template):
   ```javascript
   // Update displayed slider value on change
   temperatureSlider.addEventListener('input', function() {
       temperatureDisplay.textContent = this.value;
   });
   ```

**Usage Dashboard** (`templates/partials/usage_stats.html`):

1. Already displays stats from `usage_stats` dict passed from backend
2. Make sure dashboard.html passes it:
   ```python
   # In app.py GET / route (already done)
   usage_stats = UsageTracker.get_total_usage()
   recent_usage = UsageTracker.get_recent_usage(limit=5)
   
   return render_template('dashboard.html', 
       usage_stats=usage_stats,
       recent_usage=recent_usage,
       # ...
   )
   ```

**Testing**:
```
Manual test flow:
1. Ask a few questions to generate usage
2. Check that token counts appear on dashboard
3. Adjust temperature slider
4. Ask another question
5. Verify new temperature was used (should see different response style)
6. Refresh page
7. Settings should persist
```

**Deliverable**: Adjust model parameters → takes effect. See usage stats update in real-time.

---

## PHASE 2: Extended Features (Days 6-11)

### Days 6-7: Flashcard Generator

**What to Build**:
- Generate QA pairs from documents
- Study interface with card flip
- Track review count

**Key Files**:
- `app.py`: Add `/generate-flashcards` route
- `services/ai_agent.py`: Implement `generate_flashcards()` method
- Models already defined: `Flashcard` model

---

### Days 8-9: Quiz Generator

**What to Build**:
- Generate MC + short-answer questions
- Quiz taking interface
- Score calculation

**Key Files**:
- `app.py`: Add `/generate-quiz`, `/submit-answer` routes
- Models: `Quiz`, `QuizQuestion`, `QuizResult` (already defined)

---

### Day 10: Code Analysis

**What to Build**:
- Code review reports
- Architecture analysis
- Control flow analysis

**Key Files**:
- `app.py`: Add `/analyze-code/<doc_id>` route
- `services/ai_agent.py`: Add `review_code()`, `analyze_architecture()`, `analyze_control_flow()` methods
- Model: `CodeAnalysis` (already defined)

---

### Day 11: Testing & Optimization

**What to Do**:
- Write pytest tests for all features
- Optimize prompts to reduce hallucinations
- Performance improvements
- Error handling polish

---

## Common Patterns to Remember

### Form Submission Pattern
```html
<!-- Template -->
<form method="POST" action="{{ url_for('route_name') }}">
    <input type="hidden" name="doc_id" value="{{ doc.id }}">
    <input type="text" name="query">
    <button type="submit">Submit</button>
</form>
```

```python
# Backend
@app.route('/route_name', methods=['POST'])
def route_name():
    doc_id = request.form.get('doc_id')
    query = request.form.get('query')
    # ...
    return redirect(url_for('dashboard'))
```

### AJAX Pattern (for real-time updates)
```javascript
// Frontend
fetch('/api/endpoint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({key: 'value'})
})
.then(r => r.json())
.then(data => {
    // Handle response
});
```

```python
# Backend
@app.route('/api/endpoint', methods=['POST'])
def endpoint():
    data = request.get_json()
    # ... process ...
    return jsonify({'status': 'success'})
```

### Database Query Pattern
```python
# Get all
items = Model.query.all()

# Get one
item = Model.query.get(id)
item = Model.query.filter_by(name='value').first()

# Create
item = Model(field1=value1, field2=value2)
db.session.add(item)
db.session.commit()

# Update
item.field = new_value
db.session.commit()

# Delete
db.session.delete(item)
db.session.commit()
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'google'"
**Solution**: 
```bash
pip install google-generativeai
```

### Issue: "SQLAlchemy: no such table"
**Solution**:
```bash
python database/init_db.py
```

### Issue: API Key invalid
**Solution**:
- Verify API key in `.env`
- Test key: `python -c "import google.generativeai as genai; genai.configure(api_key='KEY'); print('OK')"`

### Issue: Chat endpoint returns 500 error
**Solution**:
- Check Flask console for error message
- Verify all services are initialized
- Check ChromaDB collection exists for document

---

## Success Metrics (End of Day 5)

✅ You've successfully completed Phase 1 MVP if:

1. **Upload works**
   - [ ] Can upload PDF/TXT files
   - [ ] Files appear in sidebar
   - [ ] Files can be deleted

2. **Search works**
   - [ ] Documents are embedded
   - [ ] ChromaDB collections are created

3. **Chat works**
   - [ ] Can ask questions about documents
   - [ ] Get coherent AI responses
   - [ ] Responses appear in chat box

4. **Settings work**
   - [ ] Can adjust temperature/tone
   - [ ] Settings persist after refresh
   - [ ] Changes affect responses

5. **Usage tracking works**
   - [ ] Token counts are accurate
   - [ ] Statistics display on dashboard
   - [ ] Usage persists in database

---

Good luck with the implementation! 🚀

If you get stuck on any specific function, refer to the docstrings in the skeleton files - they have detailed explanations and pseudo-code.
