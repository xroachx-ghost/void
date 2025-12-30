# Void Suite v6.0.1 - Initial Release 🚀

**Copyright (c) 2024 Roach Labs. All rights reserved.**
**Made by James Michael Roach Jr.**

---

## What is Void Suite?

Void Suite is a Python-based Android maintenance and recovery toolkit. It wraps `adb` and `fastboot` with a guided CLI and optional GUI, adding diagnostics, reporting, and recovery workflows for common device-service tasks. A built-in Gemini-powered AI agent helps automate web-based research and retrieval steps.

---

## ✨ Highlights

### 🔧 Core Device Tools
- **Device Discovery** - Automatic detection with health checks and summaries
- **ADB/Fastboot Integration** - Full command wrapper with guided interface
- **Backup & File Management** - Device backups, file transfers, screenshots
- **App Inventory** - Application listing, management, and analysis
- **Logcat Collection** - Real-time log capture and analysis

### 🔍 Diagnostics
- Performance monitoring (CPU, memory, storage)
- Network connectivity testing
- Display property analysis

### 🔄 Recovery & Advanced Tools
- FRP (Factory Reset Protection) guidance
- Data recovery helpers
- System configuration tweaks
- **Qualcomm EDL Utilities** - Emergency Download Mode tools
- Partition flash, backup, and management

### 🤖 AI-Powered Automation
- **Gemini AI Agent** with automated browser workflows
- Locate OEM downloads (firmware, firehose programmers)
- Search for device-specific packages and dependencies
- Gather reference links for repair workflows

### 🖥️ User Interfaces
- **CLI Mode** - Interactive command-line with rich formatting
- **GUI Mode** - Tkinter-based graphical interface
  - Simple Mode: Quick actions dashboard
  - Advanced Mode: Full features in organized tabs

### 🔌 Extensibility
- Plugin support for custom commands
- Automated report generation

---

## 📦 Installation

```bash
# Clone and install
git clone https://github.com/xroachx-ghost/void.git
cd void
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install .

# Optional GUI support
pip install .[gui]
```

---

## 🚀 Quick Start

```bash
# CLI mode
void

# GUI mode
void --gui
```

---

## 📋 Requirements

- Python 3.9+
- Android Platform Tools (adb, fastboot)
- USB drivers for your device
- Optional: Tkinter for GUI

---

## 📖 Documentation

- [README](https://github.com/xroachx-ghost/void/blob/main/README.md) - Full setup and usage guide
- [FEATURES](https://github.com/xroachx-ghost/void/blob/main/FEATURES.md) - Complete feature documentation
- [GUI User Guide](https://github.com/xroachx-ghost/void/blob/main/GUI_USER_GUIDE.md) - GUI-specific instructions

---

## ⚠️ Important Notice

This software requires **explicit authorization** to access any connected device. Only use on devices you own or are authorized to service.

---

**Full Changelog**: https://github.com/xroachx-ghost/void/blob/main/CHANGELOG.md