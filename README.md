# Corpus Forge - AI Document Explorer

**An educational project inspired by NotebookLM that enables users to explore documents through AI-powered chat, generate flashcards & quizzes, and analyze code.**

**Team**: 3 First-Year Computer Science Students  
**Timeline**: 11 Days (May 18-29, 2026)  
**Status**: Skeleton complete, ready for implementation  

---

## 🎯 What is Corpus Forge?

Corpus Forge is a Flask-based web application that lets you:
- 📄 **Upload documents** (PDFs, TXT, code files)
- 💬 **Chat with your documents** using AI (powered by Google Gemini)
- 🎓 **Generate flashcards** for study
- ❓ **Create quizzes** with auto-grading
- 🔍 **Analyze code** (reviews, architecture, control flow)
- 📊 **Track AI usage** (token counts, request logs)
- ⚙️ **Customize AI behavior** (temperature, tone, audience level)

---

## 📋 Prerequisites

Before you start, make sure you have:

- **Python 3.8 or higher** installed
  - Check: `python --version` (Windows) or `python3 --version` (macOS/Linux)
  - Download: https://www.python.org/downloads/
  
- **Git** installed
  - Check: `git --version`
  - Download: https://git-scm.com/

- **Google GenAI API Key** (free)
  - Get one: https://aistudio.google.com/apikey
  - No credit card required for free tier

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd capstone-corpus-forge
```

### Step 2: Create Virtual Environment

A **virtual environment** isolates your project's Python packages from your system Python.

#### **Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal line.

#### **macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal line.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages:
- **Flask 2.3.3** - Web framework
- **SQLAlchemy 2.0.21** - Database ORM
- **google-generativeai 0.3.0** - Google Gemini API
- **chromadb 0.3.21** - Vector database for embeddings
- **pdfplumber** - PDF text extraction
- **python-dotenv** - Environment variable management
- And more...

### Step 4: Configure Environment Variables

Copy the template and add your API key:

```bash
# Copy template to .env
cp .env.template .env
```

On Windows:
```bash
copy .env.template .env
```

Now open `.env` in your text editor and add your Google API key:

```
GOOGLE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FLASK_ENV=development
```

**⚠️ Important**: Never commit `.env` to Git. It's already in `.gitignore`.

### Step 5: Initialize Database

```bash
python database/init_db.py
```

You should see:
```
✓ Database tables created
✓ Default settings created
✓ Uploads directory ready: static/uploads
✓ ChromaDB directory ready: ./.chromadb
✓ Database initialization complete!
```

### Step 6: Run the Application

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open http://localhost:5000 in your browser. You should see the dashboard with an empty document list.

✅ **Setup complete!**

---

## 📚 Understanding Virtual Environments

A **virtual environment** is a isolated Python workspace for your project.

### Why use a virtual environment?

- 🔒 **Isolation**: Your project's packages don't interfere with system Python
- 📦 **Reproducibility**: `requirements.txt` ensures everyone has the same versions
- 🧹 **Cleanliness**: Easy to delete and start fresh
- 🚫 **No permission issues**: Install packages without sudo

### Common Virtual Environment Commands

```bash
# Activate venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# Deactivate venv (return to system Python)
deactivate

# See installed packages
pip list

# See package details
pip show <package-name>

# Install a new package
pip install <package-name>

# Update a package
pip install --upgrade <package-name>

# Generate requirements from current environment
pip freeze > requirements.txt

# Delete venv (if needed to start fresh)
rm -r venv  # macOS/Linux
rmdir /s venv  # Windows
```

---

## 🏗️ Project Structure

```
capstone-corpus-forge/
├── app.py                      ← Flask main app (all routes)
├── config.py                   ← Configuration management
├── requirements.txt            ← Python dependencies
├── .env.template               ← Environment variables template
├── .gitignore                  ← Git ignore rules
│
├── models/
│   └── __init__.py            ← Database models (Document, ChatMessage, etc.)
│
├── services/
│   ├── ai_agent.py            ← Google Gemini integration
│   ├── embeddings.py          ← ChromaDB vector search
│   ├── document_processor.py   ← PDF/TXT/code extraction
│   └── usage_tracker.py        ← Token logging
│
├── utils/
│   ├── db.py                  ← Database utilities
│   └── helpers.py             ← Common helpers
│
├── database/
│   └── init_db.py             ← Database initialization
│
├── templates/
│   ├── base.html              ← Base layout
│   ├── dashboard.html         ← Main dashboard
│   ├── error.html             ← Error page
│   └── partials/
│       ├── documents_sidebar.html   ← Document list
│       ├── chat_box.html           ← Chat interface
│       ├── settings_panel.html     ← Settings form
│       └── usage_stats.html        ← Usage dashboard
│
├── static/
│   ├── css/
│   │   └── main.css           ← Styling
│   ├── js/
│   │   └── chat-stream.js     ← Chat streaming logic
│   └── uploads/               ← Uploaded files (created at runtime)
│
├── tests/
│   └── test_suite.py          ← Pytest test stubs
│
├── .chromadb/                 ← ChromaDB data (created at runtime)
├── corpus_forge.db            ← SQLite database (created at init_db.py)
│
├── README.md                  ← This file
├── QUICKSTART.md              ← 5-minute quick start guide
├── IMPLEMENTATION_GUIDE.md    ← Day-by-day implementation instructions
├── DAILY_CHECKLIST.md         ← 11-day sprint checklist
└── JOURNAL.md                 ← Development journal
```

---

## 🔧 Troubleshooting Setup

### Issue: "python: command not found" or "python is not recognized"

**Solution**: Python is not installed or not in your PATH.
- Download Python: https://www.python.org/downloads/
- On Windows, during installation, check "Add Python to PATH"
- Verify: `python --version`

### Issue: "venv is not activated" (no `(venv)` in terminal)

**Solution**: Re-run the activation command:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution**: Virtual environment not activated or requirements not installed.
```bash
# Verify venv is active (should see (venv) prefix)
# If not, activate it

# Then install requirements
pip install -r requirements.txt
```

### Issue: "GOOGLE_API_KEY not found" error when running app

**Solution**: `.env` file missing or incomplete.
```bash
# Verify .env exists
ls .env      # macOS/Linux
dir .env     # Windows

# Add your API key
# Open .env in text editor and add:
# GOOGLE_API_KEY=sk-xxxxx

# Verify it's there
cat .env     # macOS/Linux
type .env    # Windows
```

### Issue: Port 5000 already in use

**Solution**: Another app is using port 5000.
```bash
# Run on a different port
python app.py --port 5001

# Or kill the process using port 5000
# (varies by OS, ask your team lead if stuck)
```

### Issue: Database error "no such table: documents"

**Solution**: Database not initialized.
```bash
python database/init_db.py
```

### Issue: "pip: command not found"

**Solution**: pip comes with Python, but might be named `pip3` on macOS/Linux.
```bash
pip3 install -r requirements.txt
```

---

## 📖 Documentation

- **QUICKSTART.md** - Get up and running in 5 minutes (start here!)
- **IMPLEMENTATION_GUIDE.md** - Detailed day-by-day implementation with code snippets
- **DAILY_CHECKLIST.md** - Printable 11-day sprint tracking checklist
- **JOURNAL.md** - Development decisions and session logs

---

## 👥 Team Roles & Responsibilities

### Person A - Backend Routes
- Implement routes in `app.py`
- Handle request/response logic
- Database operations
- Start: Read IMPLEMENTATION_GUIDE.md "DAY 2: Document Upload"

### Person B - Frontend & UI
- Implement templates in `templates/`
- HTML forms and styling
- JavaScript event handlers
- Start: Read IMPLEMENTATION_GUIDE.md "DAY 4: Chat UI"

### Person C - AI & Embeddings
- Implement `services/ai_agent.py` (Google Gemini)
- Implement `services/embeddings.py` (ChromaDB)
- Token tracking and analytics
- Start: Read IMPLEMENTATION_GUIDE.md "DAY 3: Embeddings"

---

## 📅 Development Timeline

| Phase | Days | Focus |
|-------|------|-------|
| **Phase 1 MVP** | Days 1-5 | Upload → Chat → Settings |
| **Phase 2** | Days 6-11 | Flashcards, Quizzes, Code Analysis |

**Day 1**: Setup environment (you are here!)  
**Days 2-5**: Implement core features (upload, embeddings, chat, settings)  
**Days 6-11**: Implement advanced features (flashcards, quizzes, code analysis)

---

## 🧪 Testing Your Setup

After completing all 6 steps above, run these commands to verify everything works:

```bash
# Test Python imports
python -c "import flask; import google.generativeai; import chromadb; print('✓ All imports OK')"

# Test Flask app (should return HTML dashboard)
python app.py &
sleep 2
curl http://localhost:5000
# Press Ctrl+C to stop the app

# Test database
python -c "from models import db, Document; print(f'✓ Database OK')"

# Test ChromaDB
python -c "import chromadb; print('✓ ChromaDB OK')"
```

If all 4 print "✓ OK", your setup is complete! 🎉

---

## 💡 Tips for Success

1. **Keep your venv activated** while working on the project
   - You'll see `(venv)` at the start of your terminal
   - If you see plain `$` or `>`, activate it again

2. **Commit often** 
   - After each feature/day: `git add . && git commit -m "Day X: Feature description"`
   - Never commit `.env` or `venv/` folder

3. **Install new packages carefully**
   - Always use `pip install <package>` (not system package manager)
   - Then update `requirements.txt`: `pip freeze > requirements.txt`

4. **Ask for help early**
   - If something breaks, ask in team chat immediately
   - Check the Troubleshooting section first

5. **Read the documentation**
   - IMPLEMENTATION_GUIDE.md has everything you need to implement features
   - DAILY_CHECKLIST.md helps track progress

---

## 🤝 Getting Help

**Setup issues?**
- Check Troubleshooting section above
- Verify each step completed (especially .env file)

**Implementation stuck?**
- Read IMPLEMENTATION_GUIDE.md for your assigned day
- Check docstrings in code files
- Ask in team chat with error message and traceback

**API issues?**
- Verify API key in `.env`: `cat .env` (macOS/Linux) or `type .env` (Windows)
- Test API key: `python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"`
- Get new key: https://aistudio.google.com/apikey

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `python -m venv venv` | Create virtual environment |
| `venv\Scripts\activate` | Activate venv (Windows) |
| `source venv/bin/activate` | Activate venv (macOS/Linux) |
| `deactivate` | Exit venv |
| `pip install -r requirements.txt` | Install all dependencies |
| `python database/init_db.py` | Initialize database |
| `python app.py` | Run Flask app |
| `pip list` | Show installed packages |
| `pip install <package>` | Install new package |

---

## ✅ Success Checklist - Day 1

- [ ] Python 3.8+ installed
- [ ] Virtual environment created (`venv/` folder exists)
- [ ] Virtual environment activated (see `(venv)` in terminal)
- [ ] Dependencies installed (`pip install -r requirements.txt` ran successfully)
- [ ] `.env` file created with GOOGLE_API_KEY added
- [ ] Database initialized (`python database/init_db.py` ran successfully)
- [ ] Flask app runs (`python app.py` starts without errors)
- [ ] Dashboard loads at http://localhost:5000
- [ ] All team members completed steps 1-8

**If all checkboxes are ✓, you're ready to start Day 2 implementation!** 🚀

---

## 📝 License & Notes

This is an educational capstone project for first-year CS students.

**Important**: 
- Keep `.env` file private (never share API key)
- Don't commit `venv/` folder (it's in `.gitignore`)
- Update JOURNAL.md with significant changes
- Reference IMPLEMENTATION_GUIDE.md frequently

---

**Let's build something awesome! 🚀**

For questions, check QUICKSTART.md or IMPLEMENTATION_GUIDE.md.

Last updated: May 18, 2026
