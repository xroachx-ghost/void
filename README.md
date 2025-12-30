# Void Suite

**Copyright (c) 2024 Roach Labs. All rights reserved.**  
**Made by James Michael Roach Jr.**  
**Proprietary and confidential. Unauthorized use or distribution is prohibited.**

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

---

## About Void Suite

Void Suite is a Python-based Android maintenance and recovery toolkit. It wraps `adb` and
`fastboot` with a guided CLI and optional GUI, and adds diagnostics, reporting, and recovery
workflows for common device-service tasks. A built-in Gemini-powered AI agent is a core
feature, helping you automate web-based research and retrieval steps when you need device
assets (for example: app packages, firehose loaders, or vendor-specific files).

What it can help with:

- Device discovery, summaries, and quick health checks
- Backups, file management, screenshots, and reports
- App inventory tools and logcat collection
- Performance, network, and display diagnostics
- FRP guidance, data recovery helpers, and system tweaks
- Qualcomm EDL utilities (flash/backup/partition tools) and chipset helpers
- Plugin support for extending commands
- Gemini-powered AI agent mode with automated browser workflows for:
  - Finding vendor assets and downloads (app packages, firehose loaders, firmware links)
  - Cross-referencing device identifiers with public resources
  - Saving useful links or results for follow-up tooling steps

### Gemini AI agent mode (built-in)

Void Suite includes a Gemini-powered agent that can spin up an automated browser, navigate
websites, and simulate clicks to locate files or references you need during device service.
This is designed to reduce manual searching and keep the workflow inside the tool.

Typical uses include:

- Locating OEM downloads (firmware packages, firehose programmers, and recovery images)
- Searching for device-specific app bundles and dependencies
- Gathering reference links for repair or recovery steps before you run commands locally

## What You Need (before installing)

Keep this list handy so nothing breaks:

- **Python 3.9+**
- **Android Platform Tools** (gives you `adb` and `fastboot`)
- **USB drivers or udev rules** for your device
- **Optional GUI support**: Tkinter

### Check your Python first

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

- **Windows**: Install Android Platform Tools and make sure `adb` and `fastboot` are in your PATH.
- **macOS**: Install Android Platform Tools (Homebrew or manual) and make sure `adb` is in your PATH.
- **Linux**: Install Android Platform Tools from your package manager, then confirm `adb` is in your PATH.

Quick check (run these and make sure they print a version):

```bash
adb version
fastboot version
```

### Device Drivers / Permissions

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

Tkinter is not installed by `pip`. It comes from your OS or Python build.

- **Windows**: Usually included with the Python installer.
- **macOS**: python.org installers include Tkinter.
- **Linux**: install `python3-tk` (Debian/Ubuntu) or `tk` (Arch).

## Installation (copy & paste)

> Please use a virtual environment (venv). It keeps your system clean and avoids broken installs.

### macOS / Linux

```bash
cd /path/to/void
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

If you need to clone the repo first:

```bash
git clone <REPO_URL>
cd /path/to/void
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

### Windows (PowerShell)

```powershell
cd C:\path\to\void
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install .
```

If you need to clone the repo first:

```powershell
git clone <REPO_URL>
cd C:\path\to\void
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install .
```

### Optional: Install GUI extras

```bash
pip install .[gui]
```

### Updating later

If you pull new changes, reinstall inside the same venv:

```bash
pip install --upgrade .
```

## Run It

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

If the GUI fails to open, double-check Tkinter and rerun the command.

#### GUI Modes

The GUI offers two modes accessible via the toggle button in the top-right corner:

- **Simple Mode** 🎯 - A streamlined dashboard with quick actions for common tasks
- **Advanced Mode** ⚙️ - Full feature access with organized tabs

#### Advanced Mode Tab Organization

The Advanced GUI is organized into 8 main categories with logical sub-tabs:

1. **📊 Dashboard** - Device overview, details, and quick actions
2. **🔧 Device Tools** - Apps | Files | System | Network
3. **🔄 Recovery** - Data Recovery | EDL Mode | Flash/Dump
4. **🔍 Diagnostics** - Logcat | Monitor | Troubleshoot
5. **💾 Data** - Exports | Database
6. **🤖 Automation** - Commands | Plugins | Browser | AI Assistant
7. **📝 Logs** - Operations log viewer
8. **⚙️ Settings** - Configuration | Help

Each main tab contains related functionality in sub-tabs, making it easy to find what you need without overwhelming the interface.

## Where files go

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

## Common Commands (simple examples)

```text
void> devices
void> info emulator-5554
void> backup emulator-5554
void> screenshot emulator-5554
void> report emulator-5554
void> logcat emulator-5554
```

## Troubleshooting (detailed)

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

- Make sure Tkinter is installed (see the Tkinter section above).
- On Linux, install `python3-tk` and try again.

### Permission or authorization errors

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

## Uninstall (if you need to)

```bash
pip uninstall void-suite
```

## Turn off the venv when done

```bash
deactivate
```
