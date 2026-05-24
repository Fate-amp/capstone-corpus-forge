# 🚀 Quick Start Guide - Corpus Forge

## One-Click Startup

### **Windows Users**
Double-click `run.bat` to start the app!

```
Double-click: run.bat
```

### **macOS/Linux Users**
Run the shell script:

```bash
chmod +x run.sh
./run.sh
```

### **All Platforms (Python)**
Or use Python directly:

```bash
python run.py
```

---

## What Happens When You Run

The launcher automatically:

1. ✅ **Checks Python** - Verifies Python 3.8+ is installed
2. ✅ **Creates Virtual Environment** - Sets up `.venv` if needed
3. ✅ **Installs Dependencies** - Installs all required packages from `requirements.txt`
4. ✅ **Starts Flask Server** - Launches the application
5. ✅ **Opens Browser** - Automatically opens `http://localhost:5000`
6. ✅ **Shows Links** - Displays all access URLs

---

## Access the App

Once running, you can access Corpus Forge at:

| Link | Usage |
|------|-------|
| `http://localhost:5000` | Local machine only |
| `http://127.0.0.1:5000` | Local machine only |
| `http://<your-ip>:5000` | From other devices on same network |

---

## Stop the Server

Press **Ctrl+C** in the terminal to stop the server.

---

## Troubleshooting

### ❌ Python Not Found

**Error:** `python: command not found`

**Solution:** Install Python from https://www.python.org/ (3.8 or higher)

On Windows, make sure to check "Add Python to PATH" during installation.

### ❌ Permission Denied (macOS/Linux)

**Error:** `Permission denied: ./run.sh`

**Solution:** Make the script executable:
```bash
chmod +x run.sh
./run.sh
```

### ❌ Port 5000 Already in Use

**Error:** `Address already in use`

**Solution:** Either:
1. Stop any other app using port 5000
2. Edit `app.py` line 601 and change `port=5000` to another number (e.g., `port=5001`)

### ❌ Dependencies Installation Fails

**Solution:** Try manually installing dependencies:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
python app.py
```

---

## Manual Setup (if launcher fails)

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py

# 5. Open browser to http://localhost:5000
```

---

## Files in This Project

- `run.py` - Universal Python launcher (Windows/Mac/Linux)
- `run.bat` - Windows batch file launcher (double-click friendly)
- `run.sh` - macOS/Linux shell script launcher
- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `.venv/` - Virtual environment (created automatically)

---

## Features

📄 **Upload Documents** - PDF, TXT, code files

💬 **AI Chat** - Ask questions about your documents

⚙️ **Settings** - Customize AI responses (temperature, tone, audience)

📊 **Usage Stats** - Track your API usage

🗑️ **Delete Documents** - Remove documents and clear history

---

## Need Help?

Check the project documentation in:
- `README.md` - Project overview
- `QUICKSTART.md` - Detailed setup instructions
- `HowToSetupYourTeamRepo.md` - Team collaboration guide

---

**Happy learning! 🎓**
