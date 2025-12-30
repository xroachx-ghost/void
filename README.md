# Void Suite

<div align="center">

![Version](https://img.shields.io/badge/version-6.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**Professional Android Device Management & Recovery Toolkit**

*Comprehensive CLI and GUI suite with 250+ automated features, EDL operations, and AI-powered assistance*

**Copyright (c) 2024 Roach Labs. All rights reserved.**  
**Made by James Michael Roach Jr.**  
**Proprietary and confidential. Unauthorized use or distribution is prohibited.**

</div>

---

```
__     ___     _     _      _       _ _
\ \   / (_) __| | __| |_   _(_)___  (_) |_ ___
 \ \ / /| |/ _` |/ _` | | | | / __| | | __/ _ \
  \ V / | | (_| | (_| | |_| | \__ \ | | ||  __/
   \_/  |_|\__,_|\__,_|\__,_|_|___/_|_|\__\___|

                .-._   _ _ _ _ _ _ _ _ _ _ _ _.
              .'   `-.'                         `-.
             /   .-"""-.        .-"""-.           \
            /   /  _ _  \      /  _ _  \           \
           |   |  (o o)  |    |  (o o)  |           |
           |   |   \_/   |    |   \_/   |           |
           |   | .-==='-.|    |.-==='-. |           |
           |   |/  .-.  \|    |/  .-.  \|           |
           |   /  /   \  \    /  /   \  \           |
           |  /  /  _  \  \  /  /  _  \  \          |
           | |  |  ( )  |  ||  |  ( )  |  |         |
           | |  |   ^   |  ||  |   ^   |  |         |
           | |  |  '-'  |  ||  |  '-'  |  |         |
           |  \  \     /  /  \  \     /  /          |
           |   \  `---'  /    \  `---'  /           |
            \   `-.___.-'      `-.___.-'           /
             \          .-""""-.                  /
              `-._     /  ____  \              _.-'
                  `---/__/    \__\------------'

              "We are Anonymous. We are Legion.
                We do not forgive. We do not forget."
```

## Ownership & Legal Notice

This software is the proprietary property of **Roach Labs**.

- **Owner**: Roach Labs
- **Author**: James Michael Roach Jr.
- **License**: Proprietary (see LICENSE file)

All rights reserved. This is proprietary and confidential software. Unauthorized copying, modification, distribution, or disclosure is strictly prohibited without express written agreement from Roach Labs.

## 📑 Table of Contents

- [About](#-about-void-suite)
- [Key Features](#-key-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [GUI Overview](#-gui-overview)
- [Common Commands](#-common-commands)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)
- [Uninstall](#-uninstall)
- [Legal & License](#-legal--license)

---

## 📖 About Void Suite

Void Suite is a **professional-grade Android maintenance and recovery toolkit** built with Python. It provides a unified interface (CLI and GUI) for comprehensive device management, diagnostics, backup, recovery, and advanced operations including EDL (Emergency Download Mode) support.

### 🎯 Core Capabilities

- 📱 **Device Management**: Multi-mode detection (ADB, Fastboot, EDL), comprehensive device info, health monitoring
- 💾 **Backup & Recovery**: Full device backups, selective data recovery (contacts, SMS), file management
- 📦 **App Management**: Complete app inventory, installation, uninstallation, package analysis
- 🔍 **Diagnostics**: Performance analysis (CPU, memory, battery), display diagnostics, network testing
- ⚙️ **System Tweaks**: DPI adjustment, animation control, developer options, USB debugging
- 🔓 **FRP Bypass**: Multiple methods for Factory Reset Protection bypass (authorized use only)
- 💿 **Partition Management**: List, backup, and manage device partitions
- 🔥 **EDL Operations**: 24+ specialized commands for Emergency Download Mode (Qualcomm, MediaTek)
- 🛠️ **Recovery & Root**: Boot image extraction, Magisk workflow, TWRP support, root verification
- 🤖 **AI Assistant**: Gemini-powered agent for automated web research and asset retrieval
- 🔌 **Plugin System**: Extensible architecture for custom commands and workflows
- 📊 **Reporting**: Comprehensive HTML/JSON reports with detailed device analytics

### 🤖 AI-Powered Assistance

Void Suite includes a **Gemini-powered AI agent** (GUI mode) that automates web research and asset retrieval:

- 🔍 **Automated Web Search**: Navigate websites and locate device-specific resources
- 📥 **Asset Discovery**: Find firmware packages, firehose loaders, recovery images
- 🔗 **Reference Gathering**: Collect repair guides, documentation, and useful links
- 💡 **Smart Recommendations**: Context-aware suggestions for repair workflows

---

## 🎯 Key Features

<div align="center">

| Feature Category | Highlights |
|-----------------|------------|
| **250+ Features** | Comprehensive toolkit covering every aspect of Android device management |
| **Zero Configuration** | Works out-of-the-box with automatic setup and intelligent defaults |
| **Multi-Platform** | Windows, macOS, and Linux support with unified interface |
| **Smart Automation** | Intelligent device selection, auto-diagnostics, context-aware suggestions |
| **Professional GUI** | Modern dark-themed interface with Simple and Advanced modes |
| **EDL Mastery** | Complete EDL toolkit with 24+ specialized operations |
| **Security First** | Authorization checks, audit logging, smart safeguards |
| **Extensible** | Plugin system for custom commands and workflows |

</div>

---

## ⚙️ Prerequisites

### 📋 System Requirements

Before installing Void Suite, ensure you have the following:

| Requirement | Details |
|-------------|---------|
| **Python** | 3.9 or newer |
| **Android Platform Tools** | `adb` and `fastboot` |
| **USB Drivers** | Device-specific drivers (Windows) or udev rules (Linux) |
| **GUI Support (Optional)** | Tkinter for graphical interface |

### ✅ Pre-Installation Checks

Make sure Python and pip are available:

```bash
python --version
pip --version
```

If you see Python 3.9 or newer, you are good.

### Check Git (for cloning)

If you plan to clone the repo, make sure Git is installed:

```bash
git --version
```

### Make sure your PATH is working

Your terminal must be able to find these commands:

- `python`
- `pip`
- `adb`
- `fastboot`

If any command says “not found,” add it to your PATH and reopen the terminal.

### Get Android Platform Tools

**Download and install Android Platform Tools for your operating system:**

| Platform | Installation Method |
|----------|-------------------|
| **Windows** | Download from [developer.android.com](https://developer.android.com/studio/releases/platform-tools), extract, and add to PATH |
| **macOS** | `brew install android-platform-tools` or download manually |
| **Linux** | `sudo apt install android-tools-adb android-tools-fastboot` (Debian/Ubuntu)<br>`sudo pacman -S android-tools` (Arch) |

**Verify installation:**

```bash
adb version
fastboot --version
```

### 🔌 Device Setup

- **Windows**: Install your phone’s USB driver (Samsung, Google, Xiaomi, etc.).
- **macOS**: Usually no extra drivers.
- **Linux**: Add udev rules for your vendor (or use root for testing only).

### Turn on USB Debugging (for adb)

1. On your phone, enable **Developer options**.
2. Turn on **USB debugging**.
3. Plug in your phone and accept the USB debugging prompt.

### Optional: Allow file access on the device

Some phones show a USB mode prompt. If you see it, choose **File Transfer (MTP)** so tools can talk to the device.

### Tkinter (only for GUI)

Tkinter is not installed by `pip`. It comes with your OS or Python installation.

| Platform | Installation |
|----------|-------------|
| **Windows** | Usually included with Python installer |
| **macOS** | Included with python.org installers |
| **Linux** | `sudo apt install python3-tk` (Debian/Ubuntu) or `sudo pacman -S tk` (Arch) |

---

## 📦 Installation

> **💡 Tip:** Always use a virtual environment (venv) to keep your system clean and avoid dependency conflicts.

### Option 1: Install from Source (Recommended)

#### macOS / Linux

```bash
# Clone the repository
git clone https://github.com/xroachx-ghost/void.git
cd void

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install
pip install --upgrade pip
pip install .

# Optional: Install with GUI support
pip install .[gui]
```

#### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/xroachx-ghost/void.git
cd void

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install
pip install --upgrade pip
pip install .

# Optional: Install with GUI support
pip install .[gui]
```

### Option 2: Install from Local Directory

If you already have the source code:

**macOS / Linux:**
```bash
cd /path/to/void
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

**Windows:**
```powershell
cd C:\path\to\void
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install .
```

### 🔄 Updating Void Suite

To update to the latest version:

```bash
# Make sure venv is activated
source .venv/bin/activate  # macOS/Linux
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Pull latest changes (if from git)
git pull

# Reinstall
pip install --upgrade .
```

---

## 🚀 Quick Start

### Command line mode

```bash
void
```

If that doesn’t work, try:

```bash
python -m void
```

### GUI mode

```bash
void --gui
```

### Interface Modes

The GUI offers **two modes** accessible via the toggle button in the top-right corner:

| Mode | Icon | Description |
|------|------|-------------|
| **Simple Mode** | 🎯 | Streamlined dashboard with quick actions for common tasks |
| **Advanced Mode** | ⚙️ | Full feature access with organized tabs and advanced operations |

### Advanced Mode Tab Organization

The Advanced GUI is organized into **8 main categories:**

| Tab | Features |
|-----|----------|
| **📊 Dashboard** | Device overview, details, and quick actions |
| **🔧 Device Tools** | Apps \| Files \| System \| Network |
| **🔄 Recovery** | Data Recovery \| EDL Mode \| Flash/Dump |
| **🔍 Diagnostics** | Logcat \| Monitor \| Troubleshoot |
| **💾 Data** | Exports \| Database |
| **🤖 Automation** | Commands \| Plugins \| Browser \| AI Assistant |
| **📝 Logs** | Operations log viewer |
| **⚙️ Settings** | Configuration \| Help |

Each main tab contains related functionality in sub-tabs for easy navigation.

---

## 📂 File Structure

The CLI creates folders for logs, backups, reports, and exports. Use the `paths` command to see them:

```text
void> paths
```

## First-Run Safety Check

You must confirm that you have permission to access any connected device. The first run will prompt you.
If you do not have explicit authorization to access a device, **do not use this tool**.

## Connect a Device (quick checklist)

1. Plug the phone in with a data-capable USB cable.
2. Approve the USB debugging prompt on the device.
3. Run:

```bash
adb devices
```

You should see your device listed as `device`.

## Verify It’s Working

Run the CLI and list devices:

```bash
void
```

Then type:

```text
void> devices
```

If your device shows up, setup is complete.

### 📱 Device Management
```bash
void> devices                    # List all connected devices
void> info smart                 # Get device information
void> summary                    # Device summary dashboard
void> analyze smart              # Performance analysis
```

### 💾 Backup & Recovery
```bash
void> backup smart               # Create full device backup
void> recover smart contacts     # Recover contacts
void> recover smart sms          # Recover SMS messages
void> screenshot smart           # Take screenshot
```

### 📦 App Management
```bash
void> apps smart all             # List all apps
void> apps smart user            # List user apps only
void> apps smart system          # List system apps only
```

### 📂 File Operations
```bash
void> files smart list /sdcard   # List files
void> files smart pull /sdcard/DCIM /tmp/  # Download files
void> files smart push myfile.txt /sdcard/ # Upload files
```

### 🔍 Diagnostics
```bash
void> display-diagnostics smart  # Display analysis
void> logcat smart               # View device logs
void> repair-flow smart          # Guided repair workflow
void> report smart               # Generate full report
```

### ⚙️ System & Utilities
```bash
void> doctor                     # System diagnostics
void> stats                      # Usage statistics
void> menu                       # Interactive menu
void> help <command>             # Get help for any command
```

---

## 🔧 Troubleshooting

### No devices found

1. Check the cable and try a different USB port.
2. Make sure USB debugging is enabled on the phone.
3. Run this command and look for your device:

```bash
adb devices
```

### ADB or fastboot not found

- Reinstall Android Platform Tools.
- Reopen your terminal after installing.
- Make sure the Platform Tools folder is in your PATH.

### GUI won’t open

1. Verify Tkinter is installed:
   - **Linux**: `sudo apt install python3-tk` or `sudo pacman -S tk`
   - **macOS/Windows**: Usually pre-installed with Python
2. Try reinstalling with GUI support: `pip install .[gui]`
3. Check for error messages in terminal
4. Use CLI mode instead: `void` (without `--gui`)

### 🔐 Device Shows "Unauthorized"

**Symptoms:** Device appears as "unauthorized" in `adb devices`

**Solutions:**
1. Unplug and replug the USB cable
2. Look for the authorization prompt on your device screen
3. Accept the "Allow USB debugging" prompt
4. Check "Always allow from this computer" (optional)
5. If prompt doesn't appear, revoke authorizations: Settings → Developer Options → Revoke USB debugging authorizations

### 🚫 "void: command not found"

**Symptoms:** `void` command doesn't work after installation

**Solutions:**
1. Ensure virtual environment is activated:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.\.venv\Scripts\Activate.ps1`
2. Use alternative: `python -m void`
3. Reinstall: `pip install --upgrade .`

### 🔒 Permission or Authorization Errors

**Symptoms:** "Permission denied" or authorization failures

**Solutions:**

- Accept the authorization prompt on first run.
- Only use devices you are allowed to access.

### Venv not activating (Windows)

If PowerShell blocks the activate script, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### pip install fails

Try updating pip inside the venv and install again:

```bash
pip install --upgrade pip
pip install .
```

### “void: command not found”

Make sure your venv is active. If it still fails, use:

```bash
python -m void
```

### Device shows “unauthorized”

1. Unplug and replug the USB cable.
2. On the device, accept the debugging prompt.
3. Run again:

```bash
adb devices
```

### Uninstall Void Suite

```bash
# Make sure venv is activated
pip uninstall void-suite
```

### Remove Data Files (Optional)

To completely remove all data:

```bash
# Remove the .void directory (contains logs, backups, reports, database)
rm -rf ~/.void  # macOS/Linux
# or
rmdir /s ~/.void  # Windows
```

⚠️ **Warning:** This will delete all backups, reports, and logs!

### Deactivate Virtual Environment

When done using Void Suite:

```bash
deactivate
```

---

## ⚖️ Legal & License

### Ownership

**Void Suite** is proprietary software:

- **Owner:** Roach Labs
- **Author:** James Michael Roach Jr.
- **Copyright:** © 2024 Roach Labs. All rights reserved.
- **License:** Proprietary (see [LICENSE](LICENSE) file)

### Usage Terms

- ✅ **Authorized use only** - You must have explicit permission to access any connected device
- ❌ **No unauthorized copying, modification, or distribution**
- ❌ **No commercial use without express written permission**
- ℹ️ **Use at your own risk** - See LICENSE for warranty disclaimer

### Legal Compliance

Users must:
- Have explicit authorization to access any connected devices
- Comply with all applicable laws and regulations
- Use the tool only on devices they own or are authorized to service
- Not use this tool for any illegal activities

### Security & Privacy

- See [SECURITY.md](SECURITY.md) for security policy
- Report vulnerabilities responsibly through private channels
- Do not disclose security issues publicly

---

## 🙏 Acknowledgments

Void Suite leverages these excellent open-source projects:

- **Python** - Core programming language
- **ADB/Fastboot** - Android Debug Bridge and fastboot
- **Rich** - Terminal formatting and output
- **psutil** - System monitoring
- **Playwright** - Browser automation (GUI mode)
- **Tkinter** - GUI framework
- **SQLite** - Embedded database

---

## 📞 Support & Community

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/xroachx-ghost/void/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/xroachx-ghost/void/discussions)
- 📖 **Documentation:** [Documentation Index](DOCUMENTATION_INDEX.md)
- 🔒 **Security:** [Security Policy](SECURITY.md)

---

<div align="center">

**Made with ❤️ by James Michael Roach Jr. for Roach Labs**

**Void Suite v6.0.1 (AUTOMATION) - Codename: Veilstorm Protocol**

*The ultimate Android device management and recovery toolkit*

---

[![GitHub](https://img.shields.io/badge/GitHub-xroachx--ghost%2Fvoid-blue?logo=github)](https://github.com/xroachx-ghost/void)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](https://www.python.org/)

**© 2024 Roach Labs. All rights reserved.**

</div>
