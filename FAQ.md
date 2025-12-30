# Void Suite - Frequently Asked Questions (FAQ)

<div align="center">

![Version](https://img.shields.io/badge/version-6.0.1-blue.svg)
![FAQ](https://img.shields.io/badge/FAQ-Answers-green.svg)

**Quick answers to common questions**

</div>

---

## 📑 Table of Contents

- [General Questions](#-general-questions)
- [Installation & Setup](#-installation--setup)
- [Usage & Features](#-usage--features)
- [Troubleshooting](#-troubleshooting)
- [Device Management](#-device-management)
- [EDL & Advanced Operations](#-edl--advanced-operations)
- [Security & Legal](#-security--legal)
- [GUI & Interface](#-gui--interface)
- [Development & Customization](#-development--customization)

---

## 🤔 General Questions

### What is Void Suite?

Void Suite is a professional-grade Android device management and recovery toolkit with 250+ automated features. It provides comprehensive CLI and GUI interfaces for device diagnostics, backup, recovery, EDL operations, and advanced maintenance tasks.

### Who is Void Suite for?

- **Device Technicians** - Complete diagnostics and repair workflows
- **Android Developers** - ADB automation and app testing
- **Power Users** - Advanced rooting and custom ROM flashing
- **Support Teams** - Automated device checks and reporting
- **Forensics** - Data extraction and partition imaging

### Is Void Suite free?

Void Suite is proprietary software owned by Roach Labs. Please see the [LICENSE](LICENSE) file for usage terms.

### What platforms does it support?

Void Suite runs on:
- **Windows** (10, 11)
- **macOS** (Intel and Apple Silicon)
- **Linux** (Debian, Ubuntu, Arch, Fedora, etc.)

### What Android devices does it support?

Void Suite works with **any Android device** that supports ADB/Fastboot, including:
- Smartphones and tablets (all manufacturers)
- Android TV boxes
- Android-based embedded devices

Chipsets with enhanced support:
- Qualcomm Snapdragon
- MediaTek
- Samsung Exynos
- HiSilicon Kirin

---

## 🔧 Installation & Setup

### What are the system requirements?

**Minimum:**
- Python 3.9 or newer
- 2 GB RAM
- 500 MB free disk space
- USB port for device connection

**Recommended:**
- Python 3.10+
- 4 GB RAM
- 1 GB free disk space
- USB 3.0 port

### Do I need Android Studio?

**No.** You only need **Android Platform Tools** (ADB and Fastboot), which can be installed separately without Android Studio.

### Can I use Void Suite without installing it?

Not recommended. While you could run from source, installation via `pip install .` sets up the proper environment and dependencies.

### How do I update Void Suite?

```bash
# Activate your virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Pull latest changes (if from git)
git pull

# Reinstall
pip install --upgrade .
```

### Why should I use a virtual environment?

Virtual environments:
- ✅ Isolate dependencies from your system Python
- ✅ Prevent conflicts with other Python packages
- ✅ Make uninstallation clean and simple
- ✅ Allow multiple Python project environments

---

## 💻 Usage & Features

### How do I start Void Suite?

**CLI Mode:**
```bash
void
```

**GUI Mode:**
```bash
void --gui
```

If `void` command doesn't work, use:
```bash
python -m void
```

### What is "smart" device selection?

The `smart` keyword automatically selects the appropriate device:
- If only one device is connected, it's automatically selected
- If multiple devices are present, it uses the last device you worked with
- You can use `smart` in place of any device ID

Example:
```bash
void> backup smart
void> info smart
void> report smart
```

### Can I run commands without the interactive CLI?

Not directly, but you can:
1. Use the GUI for one-click operations
2. Call Python functions directly (see Python API in FEATURES.md)
3. Use the upcoming REST API (planned feature)

### Where are my backups/reports stored?

By default, files are stored in `~/.void/`:
- Backups: `~/.void/backups/`
- Reports: `~/.void/reports/`
- Exports: `~/.void/exports/`
- Logs: `~/.void/logs/`

View all paths with:
```bash
void> paths
```

### How do I generate a device report?

```bash
void> report smart
```

Or in GUI: Click the "Generate Report" button in the Operations panel.

Reports are saved as HTML and JSON in the reports directory.

### Can I backup multiple devices at once?

Currently, backups are performed one device at a time. Batch operations are a planned feature for future releases.

---

## 🔍 Troubleshooting

### Why doesn't Void Suite detect my device?

**Checklist:**
1. ✅ USB debugging enabled on device
2. ✅ USB cable is data-capable (not charge-only)
3. ✅ USB debugging authorization prompt accepted
4. ✅ ADB drivers installed (Windows) or udev rules configured (Linux)
5. ✅ Device shows "device" status in `adb devices` output

### Device shows "unauthorized"

1. Unplug and replug the USB cable
2. Look for the authorization prompt on your device
3. Accept "Allow USB debugging"
4. Check "Always allow from this computer" (optional)

If prompt doesn't appear:
- Go to Settings → Developer Options → Revoke USB debugging authorizations
- Unplug and replug the device

### "void: command not found"

**Solution 1:** Activate your virtual environment
```bash
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows
```

**Solution 2:** Use alternative syntax
```bash
python -m void
```

**Solution 3:** Reinstall
```bash
pip install --upgrade .
```

### GUI won't open

1. **Check Tkinter:**
   - Linux: `sudo apt install python3-tk` or `sudo pacman -S tk`
   - macOS/Windows: Usually pre-installed

2. **Reinstall with GUI support:**
   ```bash
   pip install .[gui]
   ```

3. **Use CLI instead:**
   ```bash
   void
   ```

### Commands are slow or hang

**Possible causes:**
- Device is not responding (reboot it)
- ADB server issues (run `adb kill-server` then restart)
- USB connection problems (try different port/cable)
- Device in wrong mode (not in ADB mode)

### How do I see error messages?

Check the logs:
```bash
void> logs
void> logtail 50
```

Or view the log file directly:
```bash
tail -f ~/.void/logs/void_YYYY-MM-DD.log
```

---

## 📱 Device Management

### Can I manage multiple devices simultaneously?

Yes! Void Suite detects and lists all connected devices. You can switch between devices by specifying the device ID in commands.

### What information does Void Suite collect from my device?

**Collected (with your permission):**
- Device model, manufacturer, Android version
- Battery status, storage info
- Installed apps list
- System properties

**Privacy controls available:**
- Toggle IMEI collection
- Toggle serial number collection
- Configure what's stored in the database

See [SECURITY.md](SECURITY.md) for details.

### Can I use Void Suite over WiFi?

Yes! Enable ADB over WiFi:
```bash
void> # In CLI (feature depends on implementation)
```

Or manually:
```bash
adb tcpip 5555
adb connect <device-ip>:5555
```

### Does Void Suite work with emulators?

**Yes!** Void Suite works with:
- Android Studio Emulator
- Genymotion
- BlueStacks (if ADB is enabled)
- Other ADB-compatible emulators

---

## 🔥 EDL & Advanced Operations

### What is EDL mode?

**EDL (Emergency Download Mode)** is a low-level diagnostic mode on Qualcomm and MediaTek devices. It allows:
- Flashing firmware when device is bricked
- Direct partition access
- Unbrick devices that won't boot
- Deep-level recovery operations

### Is EDL safe to use?

EDL operations are **powerful and potentially dangerous**:
- ⚠️ Can brick your device if used incorrectly
- ⚠️ Requires correct firehose programmer for your chipset
- ⚠️ Should only be used by experienced users
- ✅ Void Suite includes safety checks and confirmations

**Always backup critical partitions before EDL operations.**

### Where do I find firehose programmers?

Void Suite includes a built-in firehose programmer database:
```bash
void> edl-programmers
```

The AI assistant can also help locate programmers:
- Run GUI mode
- Ask the AI: "Find firehose loader for [your device model]"

### Can I unbrick any device with Void Suite?

**It depends:**
- ✅ Qualcomm devices with EDL access
- ✅ MediaTek devices with BootROM mode
- ⚠️ Samsung devices (limited - Odin is better)
- ❌ Devices with eFuse blown or hardware damage

Always check device-specific unbrick procedures first.

### What is FRP bypass?

**FRP (Factory Reset Protection)** locks your device to a Google account after a factory reset. Void Suite includes tools to bypass FRP on devices you own or have authorization to access.

**⚠️ Legal Notice:** Only use FRP bypass on devices you own or are authorized to service.

---

## 🔒 Security & Legal

### Is Void Suite safe to use?

Yes, when used responsibly:
- ✅ Open codebase for review
- ✅ No telemetry or data collection sent externally
- ✅ All operations are local
- ✅ Authorization checks for sensitive operations

### Can Void Suite harm my device?

**Most operations are safe**, but:
- ⚠️ EDL flashing can brick devices if done incorrectly
- ⚠️ Partition wiping is destructive
- ⚠️ System tweaks may cause instability

**Safety measures:**
- Smart safeguards with confirmation prompts
- Automatic backups before critical operations
- Rollback capability for some operations
- Detailed logging of all actions

### Is it legal to use Void Suite?

**Yes**, when used on:
- ✅ Your own devices
- ✅ Devices you're authorized to service
- ✅ Devices with explicit owner permission

**Illegal use:**
- ❌ Unauthorized device access
- ❌ Bypassing security without permission
- ❌ Theft or fraud purposes

See the [LICENSE](LICENSE) and first-run terms.

### Does Void Suite require root?

**No**, Void Suite does not require root on your computer or device for most operations. Some advanced features may benefit from root access on the device, but it's not mandatory.

### Can I use Void Suite for data recovery on a locked device?

**Limited capability:**
- ✅ If USB debugging is enabled and authorized
- ⚠️ Some data accessible via EDL (depends on encryption)
- ❌ Cannot bypass encryption or screen lock

**Forensics users:** Check legal requirements in your jurisdiction.

---

## 🎨 GUI & Interface

### What's the difference between Simple and Advanced mode?

| Feature | Simple Mode | Advanced Mode |
|---------|-------------|---------------|
| **Interface** | Streamlined dashboard | 8 organized tabs |
| **Operations** | Common tasks only | All features |
| **Best For** | Beginners | Power users |
| **Quick Actions** | ✅ Yes | ✅ Yes |
| **Advanced Tools** | ❌ No | ✅ Yes |

Toggle between modes using the button in the top-right corner.

### What is the AI Assistant?

The AI Assistant (GUI mode only) is powered by Google Gemini and can:
- 🔍 Search for device-specific resources
- 📥 Find firmware downloads and firehose loaders
- 🔗 Gather repair guides and documentation
- 💬 Answer questions about device operations

### Can I customize the GUI theme?

Theme customization is a planned feature. Currently, the GUI uses a fixed dark theme with cyan/purple accents.

### Does the GUI have all CLI features?

**Most features**, but not all. Some advanced operations are CLI-only. For full control, use the CLI.

---

## 🔌 Development & Customization

### Can I create my own commands?

**Yes!** Use the plugin system:

1. Create a plugin file in `~/.void/plugins/my_plugin.py`
2. Follow the plugin template (see `void/plugins/example.py`)
3. Reload Void Suite

See [FEATURES.md](FEATURES.md#plugin-system) for details.

### Is there a Python API?

Yes! You can import and use Void Suite modules directly:

```python
from void.core.device import DeviceDetector
from void.core.backup import AutoBackup

# Detect devices
devices, _ = DeviceDetector.detect_all()

# Create backup
result = AutoBackup.create_backup(devices[0]['id'])
```

See [FEATURES.md](FEATURES.md) for API documentation.

### Can I contribute to Void Suite?

Void Suite is proprietary software. Direct contributions are not accepted, but you can:
- 🐛 Report bugs via [GitHub Issues](https://github.com/xroachx-ghost/void/issues)
- 💡 Suggest features
- 📚 Improve documentation
- 🔌 Create and share plugins

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### How do I report a bug?

1. Check [existing issues](https://github.com/xroachx-ghost/void/issues)
2. Run system diagnostics: `void> doctor`
3. Collect logs: `void> logs`
4. Open a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System info and logs

### How do I request a feature?

Open a [GitHub Issue](https://github.com/xroachx-ghost/void/issues) with:
- Feature description
- Use case and benefits
- Why it would help users

---

## 📚 Additional Resources

### Where can I find more documentation?

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Quick start & installation |
| [FEATURES.md](FEATURES.md) | Complete feature documentation |
| [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md) | Quick overview |
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | Navigation guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

### How do I get help?

1. **Check this FAQ**
2. **Run system doctor:** `void> doctor`
3. **Search documentation:** Use Ctrl+F in docs
4. **Check issues:** [GitHub Issues](https://github.com/xroachx-ghost/void/issues)
5. **Ask the community:** [GitHub Discussions](https://github.com/xroachx-ghost/void/discussions)

### Where can I learn more about ADB?

- [Android Developers - ADB Documentation](https://developer.android.com/studio/command-line/adb)
- [XDA Developers ADB Tutorial](https://www.xda-developers.com/adb-guide/)

### Is there a video tutorial?

Currently, there are no official video tutorials. This is a planned addition for future releases.

---

## 🆘 Still Need Help?

If your question isn't answered here:

1. **Search the documentation** - Use Ctrl+F to search all docs
2. **Run diagnostics** - `void> doctor` can identify issues
3. **Check logs** - `void> logs` or `void> logtail 50`
4. **GitHub Issues** - [Report bugs or ask questions](https://github.com/xroachx-ghost/void/issues)
5. **GitHub Discussions** - [Community help](https://github.com/xroachx-ghost/void/discussions)

---

<div align="center">

**Still stuck? Open an issue and we'll help you out!**

[![GitHub Issues](https://img.shields.io/github/issues/xroachx-ghost/void.svg)](https://github.com/xroachx-ghost/void/issues)
[![GitHub Discussions](https://img.shields.io/github/discussions/xroachx-ghost/void.svg)](https://github.com/xroachx-ghost/void/discussions)

---

**© 2024 Roach Labs. All rights reserved.**

</div>
