# Void Suite

Void Suite is an Android toolkit with CLI and optional GUI modes for device management,
backups, reporting, and recovery workflows.

## Quick Start

```bash
# Install (from repo root)
pip install .

# Launch the interactive CLI
void
```

If you prefer the GUI:

```bash
void --gui
```

## Installation

### 1) Install the package

```bash
pip install .
```

### 2) Optional GUI extras

```bash
pip install .[gui]
```

### 3) Ensure platform dependencies

Void relies on Android platform tools and device drivers.

- **ADB & fastboot**: Install Android Platform Tools and make sure `adb`/`fastboot` are in your PATH.
- **Device drivers**:
  - **Windows**: OEM USB drivers (Samsung, Google, Xiaomi, etc.).
  - **macOS**: Usually no extra drivers required, but Android Platform Tools are still required.
  - **Linux**: Add appropriate `udev` rules for your vendor (or run as root for testing).

### 4) Tkinter (GUI)

The GUI uses Tkinter, which is provided by your Python distribution or OS packages, not by `pip`:

- **Linux**: install the system package (e.g., `python3-tk` on Debian/Ubuntu, `tk` on Arch).
- **macOS**: ensure a Python build with Tk support (python.org installers include it).
- **Windows**: the official Python installer typically bundles Tkinter.

## Environment Requirements

- Python 3.9+ (recommended)
- Android Platform Tools (`adb`, `fastboot`)
- USB drivers or `udev` rules for your device vendor
- Optional: Tkinter for GUI mode

## Terms & Authorization Warning

Void requires you to confirm that you have authorization to access any connected device.
On first run, the CLI/GUI will prompt for acceptance and store it locally.
If you do not have explicit permission to access a device, **do not use this tool**.

## CLI Usage

Run the interactive CLI:

```bash
void
```

### CLI Examples

```text
void> devices
void> info emulator-5554
void> backup emulator-5554
void> screenshot emulator-5554
void> analyze emulator-5554
void> report emulator-5554
void> logcat emulator-5554
void> execute adb_shell_reset emulator-5554
```

## GUI Usage

```bash
void --gui
```

## Common Commands (from `void/cli.py`)

- **Device management**
  - `devices`
  - `info <device_id>`
  - `summary`

- **Backups & data**
  - `backup <device_id>`
  - `recover <device_id> <type>` (contacts/sms)
  - `screenshot <device_id>`

- **App & file operations**
  - `apps <device_id> [filter]` (system/user/all)
  - `files <device_id> list [path]`
  - `files <device_id> pull <path> [local]`
  - `files <device_id> push <local> <remote>`
  - `files <device_id> delete <path>`

- **Analysis & reports**
  - `analyze <device_id>`
  - `report <device_id>`
  - `logcat <device_id> [tag]`

- **System & utilities**
  - `menu`
  - `version`
  - `paths`
  - `netcheck`
  - `adb`
  - `doctor`
  - `logs` / `backups` / `reports` / `exports`
  - `help`
  - `exit`

## Troubleshooting

- **No devices detected**
  - Confirm `adb devices` shows your device.
  - Check the USB cable and enable USB debugging on the device.
  - Ensure drivers or `udev` rules are installed.

- **ADB/fastboot not found**
  - Install Android Platform Tools and confirm `adb`/`fastboot` are in your PATH.
  - Restart your terminal after installation.

- **GUI won’t launch**
  - Install Tkinter for your OS.
  - On Linux, check the `python3-tk` package.

- **Permission or authorization errors**
  - Make sure you accepted the Terms & Conditions prompt.
  - Ensure you have explicit authorization for the device.
