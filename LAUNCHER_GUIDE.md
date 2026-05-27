# 🚀 Corpus Forge - Quick Start

## Easy Launch Methods

### For Windows Users - Double Click!
**Double-click** `run.bat` in the project folder.

That's it! The app will:
- ✅ Install any missing dependencies
- ✅ Start the Flask server  
- ✅ Open your browser to http://localhost:5000
- ✅ Display all access URLs

### For Mac/Linux Users
Run in terminal:
```bash
./run.sh
```

Or use Python directly:
```bash
python run.py
```

### What You'll See
```
============================================================
                Corpus Forge Setup & Launch                 
============================================================

ℹ Python 3.13.13 on Windows

✓ Virtual environment already exists
✓ pip upgraded
✓ All dependencies installed

============================================================
                Corpus Forge is Running!
============================================================

The app is now running locally.

Access the application at:
  • http://localhost:5000
  • http://127.0.0.1:5000
  • http://192.168.x.x:5000

Press Ctrl+C to stop the server
```

---

## First Time Setup

On first run, the launcher will:

1. **Create Virtual Environment** (if needed)
   - Creates a `.venv` folder with isolated Python packages

2. **Upgrade pip** (optional)
   - Updates pip package manager (non-critical if fails)

3. **Install Dependencies**
   - Installs all required packages from `requirements.txt`
   - Uses previously downloaded packages on subsequent runs

4. **Start Flask Server**
   - Launches the development server on port 5000
   - Automatically opens your default browser

---

## System Requirements

- **Python 3.8 or higher** (download from https://www.python.org/)
- **Internet connection** (first-time setup only)
- **Modern web browser** (Chrome, Firefox, Safari, Edge, etc.)

### Windows-Specific
When installing Python on Windows:
- ☑️ Check **"Add Python to PATH"** during installation
- This allows `run.bat` to find Python automatically

---

## Troubleshooting

### ❌ "Python is not installed"
**Solution:** Download from https://www.python.org/ (3.8+)
- Make sure to check "Add Python to PATH" during installation

### ❌ "Port 5000 already in use"
**Solution:** One of these:
1. Stop any other app using port 5000
2. Edit `app.py` line 601: change `port=5000` to `port=5001` or another number

### ❌ Launcher won't start on Mac/Linux
**Solution:** Make it executable first:
```bash
chmod +x run.sh
./run.sh
```

### ❌ Dependencies fail to install
**Solution:** Try manually in terminal:
```bash
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows

pip install -r requirements.txt
python app.py
```

---

## Features

📄 **Upload Documents** - PDF, TXT, code files  
💬 **AI Chat** - Ask questions about documents  
⚙️ **Settings** - Customize AI responses  
📊 **Usage Stats** - Track API usage  
🗑️ **Delete** - Remove documents and history  

---

## Next Steps

1. Run `run.py` (or `run.bat` on Windows)
2. Wait for browser to open (localhost:5000)
3. Upload a document
4. Ask the AI questions about it!

---

**Enjoy learning with Corpus Forge!** 🎓
