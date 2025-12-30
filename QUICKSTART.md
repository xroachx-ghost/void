# Void Suite - Quick Start Guide

<div align="center">

![Version](https://img.shields.io/badge/version-6.0.1-blue.svg)
![Quick Start](https://img.shields.io/badge/guide-quickstart-brightgreen.svg)

**Get up and running in 5 minutes**

</div>

---

## ⚡ 5-Minute Setup

### Step 1: Prerequisites Check (1 minute)

Before installing, make sure you have:

```bash
# Check Python version (need 3.9+)
python --version

# Check if ADB is installed
adb version

# Check if Git is installed (for cloning)
git --version
```

**All good?** ✅ Proceed to Step 2  
**Missing something?** ⚠️ See [Prerequisites](#-prerequisites-installation) below

---

### Step 2: Install Void Suite (2 minutes)

**Option A: From Source (Recommended)**

```bash
# Clone the repository
git clone <REPO_URL>
cd void

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate          # macOS/Linux
# OR
.\.venv\Scripts\Activate.ps1        # Windows PowerShell

# Install
pip install --upgrade pip
pip install .

# Optional: Install with GUI support
pip install .[gui]
```

**Done!** ✅ Void Suite is installed

---

### Step 3: Connect Your Device (1 minute)

1. **Enable USB Debugging** on your Android device:
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → Developer Options → Enable "USB debugging"

2. **Connect via USB cable** (must be data-capable, not charge-only)

3. **Accept the authorization prompt** on your device

4. **Verify connection:**
   ```bash
   adb devices
   ```
   
   Should show:
   ```
   List of devices attached
   <device-id>     device
   ```

**Device connected?** ✅ You're ready!

---

### Step 4: Run Your First Commands (1 minute)

**Launch Void Suite:**
```bash
void
```

**Try these commands:**
```bash
# List connected devices
void> devices

# Get device information
void> info smart

# Take a screenshot
void> screenshot smart

# See available commands
void> help

# Exit
void> exit
```

**🎉 Congratulations! You're now using Void Suite!**

---

## 🎯 Common Tasks

### 📸 Take a Screenshot

```bash
void> screenshot smart
```

Screenshot saved to `~/.void/exports/`

---

### 💾 Create a Backup

```bash
void> backup smart
```

Backup saved to `~/.void/backups/`

---

### 📊 Generate Device Report

```bash
void> report smart
```

Report saved to `~/.void/reports/` (HTML + JSON)

---

### 📱 List All Apps

```bash
void> apps smart all
```

Or filter by type:
```bash
void> apps smart user      # User-installed apps
void> apps smart system    # System apps
```

---

### 📁 Browse Device Files

```bash
void> files smart list /sdcard
```

Download files:
```bash
void> files smart pull /sdcard/DCIM/photo.jpg /tmp/
```

Upload files:
```bash
void> files smart push myfile.txt /sdcard/
```

---

### 🔍 Check Device Health

```bash
void> analyze smart
```

Shows:
- CPU and memory usage
- Battery status and temperature
- Storage space
- Network connectivity

---

### 🩺 Run System Diagnostics

```bash
void> doctor
```

Checks:
- Python and dependencies
- ADB/Fastboot availability
- Device connectivity
- System health

---

### 📝 View Device Logs

```bash
void> logcat smart
```

Press `Ctrl+C` to stop.

---

### 🔄 Recover Data

Recover contacts:
```bash
void> recover smart contacts
```

Recover SMS messages:
```bash
void> recover smart sms
```

---

## 🎨 Using the GUI

### Launch GUI Mode

```bash
void --gui
```

### GUI Modes

The GUI has two modes:

| Mode | Toggle Button | Best For |
|------|--------------|----------|
| **Simple Mode** | 🎯 | Beginners, quick tasks |
| **Advanced Mode** | ⚙️ | Power users, all features |

Click the toggle button in the top-right corner to switch.

### Quick Actions (Simple Mode)

1. **Select device** from the device panel
2. **Click action buttons:**
   - Backup Device
   - Take Screenshot
   - Generate Report
   - Analyze Performance
   - List Apps

### Advanced Features (Advanced Mode)

**8 Main Tabs:**

| Tab | Features |
|-----|----------|
| 📊 **Dashboard** | Device overview and quick actions |
| 🔧 **Device Tools** | Apps, Files, System, Network |
| 🔄 **Recovery** | Data recovery, EDL, Flash/Dump |
| 🔍 **Diagnostics** | Logcat, Monitor, Troubleshoot |
| 💾 **Data** | Exports, Database |
| 🤖 **Automation** | Commands, Plugins, AI Assistant |
| 📝 **Logs** | Operation logs viewer |
| ⚙️ **Settings** | Configuration, Help |

### Using the AI Assistant (GUI Only)

1. Go to **Automation** tab
2. Click **AI Assistant** sub-tab
3. Type your question, e.g.:
   - "Find firehose loader for Snapdragon 845"
   - "Where can I download firmware for Pixel 6?"
   - "How do I enter EDL mode on OnePlus 9?"

---

## 🗂️ Where Are My Files?

All files are stored in `~/.void/`:

```
~/.void/
├── backups/      # Device backups
├── reports/      # HTML/JSON device reports
├── exports/      # Screenshots, data exports
├── logs/         # Application logs
├── cache/        # Temporary files
├── tools/        # Downloaded tools
└── void.db       # SQLite database
```

View all paths:
```bash
void> paths
```

---

## 🔑 Essential Commands

### Device Management
```bash
void> devices               # List all connected devices
void> info smart            # Device information
void> summary               # Device summary dashboard
void> analyze smart         # Performance analysis
```

### Backup & Recovery
```bash
void> backup smart          # Full device backup
void> recover smart contacts # Recover contacts
void> recover smart sms     # Recover SMS
void> screenshot smart      # Take screenshot
```

### Apps & Files
```bash
void> apps smart all        # List all apps
void> files smart list /sdcard  # Browse files
void> files smart pull <src> <dst>  # Download files
void> files smart push <src> <dst>  # Upload files
```

### Diagnostics
```bash
void> logcat smart          # View device logs
void> display-diagnostics smart  # Display analysis
void> repair-flow smart     # Guided repair
void> report smart          # Generate full report
```

### System & Help
```bash
void> doctor                # System diagnostics
void> stats                 # Usage statistics
void> version               # Version information
void> help                  # Show all commands
void> help <command>        # Help for specific command
void> search <keyword>      # Search commands
void> menu                  # Interactive menu
void> exit                  # Exit Void Suite
```

---

## 💡 Pro Tips

### 1. Use "smart" Instead of Device IDs

Instead of:
```bash
void> backup 05157df41f03d015
```

Use:
```bash
void> backup smart
```

Void Suite automatically selects the right device!

### 2. Explore the Interactive Menu

```bash
void> menu
```

Navigate categories with arrow keys and Enter.

### 3. Search for Commands

Don't remember a command? Search!
```bash
void> search backup
void> search partition
void> search edl
```

### 4. Get Command Help

```bash
void> help backup
void> help edl-flash
void> help recover
```

### 5. Check System Health First

Before reporting issues:
```bash
void> doctor
```

### 6. View Recent Operations

```bash
void> recent-logs 25
void> recent-backups 10
void> recent-reports 10
```

### 7. Use Tab Organization (GUI)

In Advanced Mode, features are logically grouped:
- **Device Tools** → Everything about apps, files, system
- **Recovery** → Data recovery and EDL operations
- **Diagnostics** → Troubleshooting and monitoring

---

## 🚨 Common Issues & Quick Fixes

### ❌ "void: command not found"

**Fix:**
```bash
# Make sure venv is activated
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Or use alternative
python -m void
```

---

### ❌ No Devices Found

**Fix:**
1. Check USB cable (must be data-capable)
2. Enable USB debugging on device
3. Accept authorization prompt on device
4. Verify: `adb devices`

---

### ❌ Device Shows "Unauthorized"

**Fix:**
1. Unplug and replug USB cable
2. Accept authorization prompt on device
3. Check "Always allow from this computer"

---

### ❌ GUI Won't Open

**Fix:**
```bash
# Linux: Install Tkinter
sudo apt install python3-tk

# Or install GUI dependencies
pip install .[gui]

# Or use CLI instead
void
```

---

### ❌ Permission Denied Errors

**Fix:**
- **Linux:** Add user to plugdev group
  ```bash
  sudo usermod -a -G plugdev $USER
  ```
  Then log out and log back in.

---

## 📚 Next Steps

### Learn More Features

- **Read the full feature list:** [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md)
- **Detailed documentation:** [FEATURES.md](FEATURES.md)
- **Navigate docs:** [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)

### Advanced Topics

- **EDL Operations:** [FEATURES.md#edl-operations](FEATURES.md#edl-emergency-download-mode-operations)
- **Plugin System:** [FEATURES.md#plugin-system](FEATURES.md#plugin-system)
- **Smart Features:** [FEATURES.md#smart-features](FEATURES.md#smart-features--ai-assistant)

### Get Help

- **FAQ:** [FAQ.md](FAQ.md)
- **Troubleshooting:** [README.md#troubleshooting](README.md#-troubleshooting)
- **GitHub Issues:** [Report bugs](https://github.com/xroachx-ghost/void/issues)
- **GitHub Discussions:** [Ask questions](https://github.com/xroachx-ghost/void/discussions)

---

## 🎓 Tutorial: Complete Workflow Example

Here's a complete workflow for backing up and reporting on a device:

```bash
# 1. Start Void Suite
void

# 2. Check what devices are connected
void> devices

# 3. Get detailed device information
void> info smart

# 4. Check device health
void> analyze smart

# 5. Create a full backup
void> backup smart

# 6. Take a screenshot
void> screenshot smart

# 7. Generate a comprehensive report
void> report smart

# 8. View backup and report locations
void> paths

# 9. List recent backups
void> backups

# 10. List recent reports
void> reports

# 11. Exit
void> exit
```

**Result:**
- ✅ Full device backup saved
- ✅ Screenshot captured
- ✅ HTML/JSON report generated
- ✅ All operations logged to database

---

## 🎉 You're All Set!

You now know how to:
- ✅ Install and run Void Suite
- ✅ Connect and manage devices
- ✅ Perform common operations
- ✅ Use both CLI and GUI
- ✅ Find help when needed

### What's Next?

- 🔍 **Explore advanced features** in [FEATURES.md](FEATURES.md)
- 🤖 **Try the AI Assistant** in GUI mode
- 🔌 **Create custom plugins** for your workflows
- 📊 **Generate detailed reports** for analysis

---

<div align="center">

**Happy Voiding! 🚀**

---

[![Documentation](https://img.shields.io/badge/docs-complete-brightgreen.svg)](DOCUMENTATION_INDEX.md)
[![FAQ](https://img.shields.io/badge/FAQ-available-blue.svg)](FAQ.md)
[![Support](https://img.shields.io/badge/support-GitHub-orange.svg)](https://github.com/xroachx-ghost/void/issues)

**© 2024 Roach Labs. All rights reserved.**

</div>
