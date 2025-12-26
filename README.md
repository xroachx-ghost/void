# Void Suite

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

Void Suite helps you work with Android devices using a simple command line (and an optional GUI).

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
