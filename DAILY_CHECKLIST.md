# Daily Implementation Checklist - Corpus Forge

**Project**: Corpus Forge - AI Document Exploration  
**Timeline**: 11 days (May 18 - May 29, 2026)  
**Team**: 3 First-Year CS Students  

---

## PHASE 1: MVP (Days 1-5)

### ✅ DAY 1: Project Setup (2 hours)

**Morning - Environment Setup**
- [ ] Clone repository
- [ ] Create Python virtual environment (`python -m venv venv`)
- [ ] Activate venv
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Copy `.env.template` to `.env`
- [ ] Get Google GenAI API key from aistudio.google.com
- [ ] Add API key to `.env`

**Afternoon - Verification**
- [ ] Run `python database/init_db.py` (initializes SQLite + ChromaDB)
- [ ] Run `python app.py` (starts Flask server)
- [ ] Open http://localhost:5000 in browser
- [ ] Dashboard loads with empty document list
- [ ] No console errors
- [ ] All team members have working setup

**Deliverable**: Everyone can run the app locally with empty dashboard visible

---

### ✅ DAY 2: Document Upload & Management (6 hours)

**Person A (Frontend Main)**
- [X] Implement upload modal in `dashboard.html` (show/hide)
- [X] Implement file input form with proper file type validation feedback
- [X] Style upload button and modal (CSS in `static/css/main.css`)
- [X] Make document items clickable (add visual selection state)
- [X] Implement delete button with confirmation dialog
- [X] Add event listeners for:
  - [X] Upload button → show modal
  - [X] Document click → select document
  - [X] Delete button → confirm delete + send to backend
- [ ] **Side Task (AI/Embeddings)**: Understand how extracted text will be chunked and embedded on Day 3. Review `document_processor.py` to see what text extraction returns.

**Person B (AI/Embeddings Main)**
- [ ] Test `document_processor.extract_text()` with sample PDFs and text files:
  - [ ] Verify text extraction works for `.pdf` files
  - [ ] Verify text extraction works for `.txt` files
  - [ ] Check that returned text is clean (no formatting artifacts)
  - [ ] Add debug logs to confirm output
- [ ] Add TODO comments in `app.py` upload_document() for Day 3:
  - [ ] Mark where embeddings will be called
  - [ ] Document the expected flow: upload → extract text → embed text
- [ ] **Side Task (Backend)**: Understand the upload route structure. Review what data needs to flow from frontend form to backend route (file, user inputs, etc.).

**Person C (Backend Main)**
- [ ] Implement `upload_document()` in `app.py`:
  - [ ] Get file from request
  - [ ] Validate file exists and has allowed extension (.pdf, .txt)
  - [ ] Save file to `static/uploads/` with secure filename (use `werkzeug.utils.secure_filename`)
  - [ ] Extract text using `document_processor.extract_text(file_path)`
  - [ ] Generate preview text (first 150 characters)
  - [ ] Create Document DB entry with filename, text, preview
  - [ ] Return redirect to dashboard
- [ ] Implement `delete_document()` in `app.py`:
  - [ ] Query Document by ID
  - [ ] Delete file from `static/uploads/`
  - [ ] Delete Document from database
  - [ ] Return redirect to dashboard
- [ ] Test both routes with actual file submissions
- [ ] **Side Task (Frontend)**: Verify upload form works end-to-end. Test that files are properly received and stored. Ensure error responses display correctly to Person A's frontend.

**Testing Checklist** (All three collaborate)
- [ ] Manual: Upload PDF → appears in sidebar
- [ ] Manual: Upload TXT → appears in sidebar
- [ ] Manual: Invalid file type (.docx, .zip) → rejected with message
- [ ] Manual: Delete document → gone from sidebar and disk
- [ ] Manual: Upload same file twice → second gets unique filename, both appear
- [ ] Manual: File with spaces/special chars in name → stored securely

**Deliverable**: Upload/delete documents working. Files saved to disk with secure names. DB entries created/deleted. Text extraction verified to work for embedding on Day 3.

---

### ✅ DAY 3: Embeddings & Vector Search (6 hours)

**Person B (AI/Embeddings Main)**
- [ ] Implement `EmbeddingsService.__init__()`:
  - [ ] Initialize GenAI API
  - [ ] Initialize ChromaDB client
- [ ] Implement `_chunk_text()`:
  - [ ] Convert tokens to characters (4 chars ≈ 1 token)
  - [ ] Split text with overlap
  - [ ] Handle edge cases (short text, end of document)
- [ ] Implement `embed_document()`:
  - [ ] Chunk document text
  - [ ] Get/create ChromaDB collection
  - [ ] For each chunk, call `genai.embed_content()`
  - [ ] Store embeddings in ChromaDB
  - [ ] Log success
- [ ] Implement `retrieve_context()`:
  - [ ] Query ChromaDB collection with user query
  - [ ] Return top-3 most relevant chunks
  - [ ] Concatenate chunks with newlines
- [ ] Implement `delete_document_embeddings()`:
  - [ ] Delete ChromaDB collection for document

**Person C (Backend Main)**
- [ ] Uncomment/enable embeddings call in `upload_document()`:
  ```python
  app.embeddings_service.embed_document(doc.id, text)
  ```
- [ ] Add embeddings deletion in `delete_document()`:
  ```python
  app.embeddings_service.delete_document_embeddings(doc_id)
  ```
- [ ] Test end-to-end: Upload document → embeddings created → ChromaDB updated
- [ ] **Side Task (Frontend)**: Add debug log output to frontend console to show embedding status when documents are uploaded.

**Person A (Frontend Main)**
- [ ] Add visual feedback when document is being embedded (loading spinner)
- [ ] Display success/error message after embedding completes
- [ ] **Side Task (AI/Embeddings)**: Understand chunk retrieval logic. Help test semantic search with various queries to ensure chunking/retrieval works as expected.

**Testing**
- [ ] Upload document
- [ ] Verify `.chromadb/` folder has new collection files
- [ ] Test semantic search (manual):
  - [ ] Upload document about Python
  - [ ] Query "Python code" should retrieve document chunks
  - [ ] Add debug logs to verify retrieval
- [ ] Test chunk retrieval quality (does top-3 make sense?)

**Deliverable**: Documents are embedded and searchable. ChromaDB collections created per document. Embedding status visible to user.

---

### ✅ DAY 4: AI Chat & Streaming (8 hours)

**Person B (AI/Embeddings Main)**
- [ ] Implement `AIAgent.__init__()`:
  - [ ] Configure genai API
  - [ ] Create GenerativeModel
- [ ] Implement `_build_system_prompt()`:
  - [ ] Use audience_level and tone to create system instruction
  - [ ] Return formatted prompt string
- [ ] Implement `_count_tokens()`:
  - [ ] Call `genai.count_tokens()`
  - [ ] Handle errors (fallback to approximation)
- [ ] Implement `generate_response()`:
  - [ ] Build full message (system + context + query)
  - [ ] Count input tokens
  - [ ] Call `model.generate_content(..., stream=True)`
  - [ ] Yield chunks as they arrive
  - [ ] Count output tokens
  - [ ] Return token counts

**Person C (Backend Main)**
- [ ] Implement `chat()` route in `app.py`:
  - [ ] Get query, document_id from request
  - [ ] Get Settings from database
  - [ ] Retrieve context from ChromaDB using EmbeddingsService
  - [ ] Call AI agent's `generate_response()`
  - [ ] Collect full response text
  - [ ] Create ChatMessage DB entry
  - [ ] Log usage with UsageTracker
  - [ ] Return response as JSON
- [ ] Ensure error handling for missing documents or failed embeddings lookups
- [ ] **Side Task (Frontend)**: Test chat route with curl/Postman before Person A integrates frontend.

**Person A (Frontend Main)**
- [ ] Update `chat_box.html` template:
  - [ ] Add chat history display area
  - [ ] Add user input textarea
  - [ ] Add send button
- [ ] Implement JavaScript event handler in `chat_box.html`:
  - [ ] Form submit → POST to `/chat` with query and selected document_id
  - [ ] Display user message in chat
  - [ ] Display AI response in chat as it streams in
  - [ ] Clear input after sending
  - [ ] Auto-scroll to latest message
- [ ] Style chat messages:
  - [ ] User messages: right-aligned, blue
  - [ ] AI messages: left-aligned, gray
- [ ] **Side Task (AI/Embeddings)**: Understand streaming response format. Help debug any token counting or context retrieval issues.

**Testing**
- [ ] Upload document
- [ ] Select document from sidebar
- [ ] Type question
- [ ] Click Send
- [ ] Response appears in chat box with streaming effect
- [ ] Token count is accurate
- [ ] Multiple messages show in conversation
- [ ] Settings (temperature, tone) affect response quality

**Deliverable**: Ask questions about document. Get AI responses with streaming. Tokens tracked accurately.

---

### ✅ DAY 5: Settings & Usage Dashboard (4 hours)

**Person A (Frontend Main)**
- [ ] Review `settings_panel.html` template:
  - [ ] Verify all form fields are present
  - [ ] Implement real-time slider value display
  - [ ] Test form submission to backend
- [ ] Wire up sliders JavaScript:
  - [ ] Temperature slider updates temperature-display
  - [ ] Top-p slider updates top_p-display
  - [ ] POST updated settings to `/update-settings`
- [ ] Review `usage_stats.html` template
- [ ] Verify stats display (auto-update from backend)
- [ ] Test that numbers format correctly
- [ ] **Side Task (AI/Embeddings)**: Ensure temperature/top-p changes actually affect AI response creativity. Help test the settings impact.

**Person C (Backend Main)**
- [ ] Implement `update_settings()` route in `app.py`:
  - [ ] Get or create Settings entry
  - [ ] Extract form data (temperature, top_p, audience_level, tone)
  - [ ] Validate ranges (temp 0-2, top_p 0-1)
  - [ ] Save to database
  - [ ] Return JSON success response or redirect
- [ ] Ensure Settings are loaded when app starts
- [ ] Add `/get-usage-stats` route to return usage data as JSON:
  - [ ] Call `UsageTracker.get_total_usage()`
  - [ ] Return formatted stats (total tokens, request count, last updated)
- [ ] Test both routes end-to-end
- [ ] **Side Task (Frontend)**: Verify that the HTML forms POST data correctly. Help debug any validation issues.

**Person B (AI/Embeddings Main)**
- [ ] Verify `UsageTracker.log_usage()` is called correctly from chat endpoint
- [ ] Verify `UsageTracker.get_total_usage()` returns correct aggregates
- [ ] Test that settings (temperature, top_p, audience_level, tone) are passed to AI agent
- [ ] Verify that changing settings actually changes AI response behavior
- [ ] **Side Task (Backend)**: Help ensure settings are properly threaded through the chat flow.

**Testing** (All three collaborate)
- [ ] Ask 5 questions to generate usage data
- [ ] Dashboard shows total tokens, requests
- [ ] Adjust temperature slider to 1.0 (more creative)
- [ ] Ask question: "Be creative: what could this concept apply to?"
- [ ] Response is more exploratory/creative
- [ ] Adjust temperature slider to 0.1 (very consistent)
- [ ] Ask same question again
- [ ] Response is more mechanical/predictable
- [ ] Refresh page
- [ ] Settings persist
- [ ] Usage stats remain (not reset)
- [ ] Change tone to "Academic" and ask a question
- [ ] Response uses more formal language

**Deliverable**: Settings panel works. Usage dashboard displays accurate stats. Temperature/tone changes affect AI responses. Everything persists across page refresh.

---

## END OF PHASE 1 VERIFICATION

**All 3 team members together, test complete flow**:

1. ✅ Upload PDF from your computer
2. ✅ Select document in sidebar (it highlights)
3. ✅ Type question: "What is the main topic of this document?"
4. ✅ Click Send
5. ✅ See AI response in chat within 10 seconds
6. ✅ Check usage dashboard - tokens incremented
7. ✅ Adjust temperature slider to 0.1 (very consistent)
8. ✅ Ask: "Explain the key concepts"
9. ✅ Response is more mechanical/predictable
10. ✅ Refresh page - chat history and settings persist
11. ✅ Delete document - removed from sidebar and disk
12. ✅ No error messages in browser or Flask console

**If all 12 checks pass**: Phase 1 is COMPLETE ✅

---

## PHASE 2: Extended Features (Days 6-11)

### DAY 6-7: Flashcard Generator

**Day 6 Implementation**:
- [ ] `services/ai_agent.py`: Implement `generate_flashcards()` method
- [ ] `models/__init__.py`: Flashcard model already defined, just verify it
- [ ] `app.py`: Add `/generate-flashcards` route
- [ ] `templates/`: Create `flashcards.html` template
  - [ ] Display current flashcard
  - [ ] Show/hide answer button
  - [ ] Navigation (prev/next)
  - [ ] Progress indicator

**Day 7 Implementation**:
- [ ] `templates/`: Update dashboard sidebar to link to flashcards
- [ ] `app.py`: Add `/generate-flashcards` button/link
- [ ] Frontend: Handle flashcard navigation and study UX
- [ ] Test: Generate 5 flashcards from document

**Deliverable**: Generate QA flashcards from documents. Study interface works.

---

### DAY 8-9: Quiz Generator

**Day 8 Implementation**:
- [ ] `services/ai_agent.py`: Implement `generate_quiz()` method
- [ ] Models: `Quiz`, `QuizQuestion`, `QuizResult` already defined
- [ ] `app.py`: Add `/generate-quiz` route
- [ ] `app.py`: Add `/submit-answer` route
- [ ] `templates/`: Create `quiz.html` template

**Day 9 Implementation**:
- [ ] `app.py`: Add `/quiz-results/<quiz_id>` route
- [ ] `templates/`: Create `quiz_results.html`
- [ ] Frontend: Quiz submission logic
- [ ] Test: Generate quiz, take quiz, see results

**Deliverable**: Generate quizzes. Take quizzes. See scoring and results.

---

### DAY 10: Code Analysis

**Implementation**:
- [ ] Detect code files in document upload
- [ ] `services/ai_agent.py`: Implement `review_code()`, `analyze_architecture()`, `analyze_control_flow()`
- [ ] `app.py`: Add `/analyze-code/<doc_id>` route(s)
- [ ] `templates/`: Create `code_analysis.html` with tabs
- [ ] Frontend: Display analysis reports

**Deliverable**: Upload code file. Generate review, architecture, control flow reports.

---

### DAY 11: Testing, Documentation, Optimization

**Testing**:
- [ ] Run `pytest` - all tests pass
- [ ] Test error cases (bad input, invalid files, API errors)
- [ ] Load testing (upload large files, generate many items)

**Documentation**:
- [ ] README complete
- [ ] Code commented
- [ ] Docstrings for all functions

**Optimization**:
- [ ] Log all AI responses for quality analysis
- [ ] Identify and fix hallucination patterns
- [ ] Optimize prompts based on logs
- [ ] Performance improvements

**Deliverable**: All features working. Tests passing. Code documented. Ready for presentation.

---

## Daily Standup Template

**Every day at start/end, answer**:

1. ✅ **What did you complete yesterday?**
2. ⏳ **What will you work on today?**
3. 🚧 **Any blockers or issues?**
4. 📊 **Confidence level** (1-5)

**Example**:
- A: "Day 2 upload. Today: delete & embeddings. No blockers. 4/5"
- B: "Day 2 UI + styling. Today: chat interface. Waiting on A's upload impl. 3/5"
- C: "Day 3 embeddings. Today: AI agent. Need to test GenAI API. 4/5"

---

## Git Workflow (Recommended)

```bash
# Day 1: Create branches
git checkout -b feature/document-management  # Person A
git checkout -b feature/frontend-ui          # Person B
git checkout -b feature/embeddings           # Person C

# Each day: commit progress
git add .
git commit -m "Day 2: Document upload & delete endpoints"
git push origin feature/document-management

# End of each phase: merge to main
git checkout main
git merge feature/document-management
```

---

## Success Checklist - Print This!

### By End of Day 5 (Phase 1 MVP):
- [ ] Upload documents (PDF, TXT, code files)
- [ ] Select documents → chat interface activates
- [ ] Ask questions → get AI responses (10 sec response time)
- [ ] See token counts on dashboard
- [ ] Adjust settings → affects responses
- [ ] Data persists across page refreshes
- [ ] No console errors or crashes

### By End of Day 11 (Phase 2 Complete):
- [ ] Everything above, PLUS:
- [ ] Generate flashcards from documents
- [ ] Study flashcards with flip interface
- [ ] Generate quizzes (MC + short answer)
- [ ] Take quizzes with scoring
- [ ] Code analysis (review, architecture, control flow)
- [ ] Prompts optimized for low hallucination
- [ ] All features tested with pytest
- [ ] Complete documentation

---

## Key Contacts & Resources

**Google GenAI API**:
- Docs: https://ai.google.dev/
- API Keys: https://aistudio.google.com/apikey
- Limits: 60 requests per minute (free tier)

**Flask Documentation**:
- Official: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/

**ChromaDB**:
- Docs: https://docs.trychroma.com/
- Quick Start: https://docs.trychroma.com/getting-started

**Help Resources**:
- Python: Stack Overflow
- JavaScript: MDN Web Docs
- SQL: W3Schools SQL

---

**Good luck! Remember: Commit often, communicate daily, ask for help early! 🚀**

*Last updated: May 18, 2026*
