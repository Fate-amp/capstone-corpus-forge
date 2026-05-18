# Quick Start - Get Running in 5 Minutes

## For Team Leads & First Time Setup

### 1. Clone & Install (3 min)

```bash
# Clone repo
git clone <repo-url>
cd capstone-corpus-forge

# Setup Python environment
python -m venv venv

# Activate (choose based on OS)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install all packages
pip install -r requirements.txt
```

### 2. Configure API Key (1 min)

```bash
# Copy template
cp .env.template .env

# Edit .env and add your Google GenAI API key:
# GOOGLE_API_KEY=sk-xxxxxxxxxxxxx
```

Get your free key from: https://aistudio.google.com/apikey

### 3. Initialize Database (1 min)

```bash
python database/init_db.py
```

You should see:
```
✓ Database tables created
✓ Default settings created
✓ Uploads directory ready
✓ ChromaDB directory ready
✓ Database initialization complete!
```

### 4. Run & Verify (0 min)

```bash
python app.py
```

Open: http://localhost:5000

You should see a dashboard with an empty document list. ✅

---

## That's it! You're ready to start implementing.

### Next: Read Documentation

1. **Team assignments**? Start with [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) (read your person section)
2. **Daily tracking**? Use [DAILY_CHECKLIST.md](DAILY_CHECKLIST.md) (print it out!)
3. **Architecture overview**? See [README.md](README.md)

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: google` | `pip install google-generativeai` |
| `no such table: documents` | `python database/init_db.py` |
| `GOOGLE_API_KEY not found` | Check `.env` file has your API key |
| Port 5000 already in use | `python app.py --port 5001` |

### First Day Plan

**9:00 AM - Setup** (30 min)
- All team members run steps 1-4 above
- Verify everyone can load localhost:5000
- Celebrate! 🎉

**10:00 AM - Architecture Review** (30 min)
- Review project structure together
- Assign responsibilities (Person A/B/C)
- Read through relevant code sections

**11:00 AM - Start Day 1 Implementation** (2 hours)
- Follow Day 1 in IMPLEMENTATION_GUIDE.md
- Goal: Verify database + services are initialized

**1:00 PM - Lunch Break**

**2:00 PM - Day 2 Begins**
- Person A: Document upload/delete
- Person B: UI/modals
- Person C: Verify document_processor works

---

## File Structure at a Glance

```
├── app.py                    ← Flask routes (Person A starts here)
├── config.py                 ← Configuration loaded from .env
├── requirements.txt          ← Dependencies (already set up)
├── .env                      ← API keys (YOUR GOOGLE KEY GOES HERE)
│
├── models/                   ← Database models (already designed)
├── services/                 ← Business logic
│   ├── document_processor.py  ← Fully implemented ✅
│   ├── ai_agent.py          ← Person C implements streaming
│   ├── embeddings.py         ← Person C implements ChromaDB
│   └── usage_tracker.py      ← Already ready
├── utils/                    ← Helpers (already set up)
│
├── templates/                ← HTML (Person B starts here)
│   ├── base.html
│   ├── dashboard.html
│   └── partials/
├── static/
│   ├── css/main.css          ← Styling complete ✅
│   ├── js/chat-stream.js     ← Person B implements
│   └── uploads/              ← Where files get saved
│
├── database/init_db.py       ← Run once on Day 1
├── tests/test_suite.py       ← Test stubs for all features
│
├── README.md                 ← Full documentation
├── IMPLEMENTATION_GUIDE.md   ← Day-by-day implementation
├── DAILY_CHECKLIST.md        ← 11-day sprint checklist
└── JOURNAL.md               ← Session log
```

---

## Person Assignments (Recommended)

### Person A - Backend Routes
- `app.py`: Implement routes for upload, delete, chat, settings
- Owns: Document lifecycle, request handling, database operations
- **Start**: Read IMPLEMENTATION_GUIDE.md section "DAY 2: Document Upload"

### Person B - Frontend & UI  
- `templates/`: HTML + styling
- `static/css/main.css`: Layout (already 90% done)
- `static/js/`: Event handlers and form submission
- **Start**: Read IMPLEMENTATION_GUIDE.md section "DAY 4: Chat UI"

### Person C - AI & Embeddings
- `services/ai_agent.py`: Google GenAI integration
- `services/embeddings.py`: ChromaDB + semantic search
- `services/usage_tracker.py`: Token logging
- **Start**: Read IMPLEMENTATION_GUIDE.md section "DAY 3: Embeddings"

---

## Testing Your Setup

```bash
# Test Python imports
python -c "import flask; import google.generativeai; import chromadb; print('✓ All imports OK')"

# Test Flask app
python app.py &
sleep 2
curl http://localhost:5000
# Should return HTML dashboard

# Test database
python -c "from models import db, Document; print(f'✓ Database OK: {Document.__tablename__}')"

# Test ChromaDB
python -c "import chromadb; print(f'✓ ChromaDB OK')"
```

---

## Success Criteria - Day 1

✅ All team members can:
1. Run `python app.py` without errors
2. Load http://localhost:5000 in browser
3. See dashboard with empty document list
4. Access `.env` with API key set

If all 4 pass: **Day 1 Complete!** 🚀

---

## Troubleshooting

### Flask won't start?
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt --upgrade

# Check API key
grep GOOGLE_API_KEY .env
```

### Database issues?
```bash
# Reinitialize from scratch
rm corpus_forge.db
python database/init_db.py
```

### Still stuck?
1. Check the error message carefully
2. Search GitHub Issues
3. Ask in team chat/Slack
4. Refer to relevant docs links in README.md

---

## Important Notes

- ⚠️ **Never commit `.env`** file (it contains your API key!)
- ✅ Git already ignores it (check `.gitignore`)
- 💾 Save your work frequently (`git add . && git commit -m "message"`)
- 📞 Communicate in team standups (see DAILY_CHECKLIST.md)
- 🎯 Follow day-by-day plan - don't skip ahead!

---

## Key Dates

| Date | Milestone |
|------|-----------|
| May 18 | Day 1 - Setup (TODAY!) |
| May 19 | Day 2 - Upload/Delete |
| May 20 | Day 3 - Embeddings |
| May 21 | Day 4 - Chat |
| May 22 | Day 5 - Settings (MVP Complete!) |
| May 23-29 | Days 6-11 - Flashcards, Quizzes, Code Analysis |

---

**You're all set! Start with DAY 1 in IMPLEMENTATION_GUIDE.md 🚀**

Questions? Check README.md or ask in team chat.

Good luck! 💪
