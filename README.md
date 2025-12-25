# Void Suite

Void Suite is an Android toolkit with CLI and optional GUI modes.

## Installation

```bash
pip install .
```

### Optional features

The project defines extras for feature grouping:

- `gui`: GUI mode (requires Tkinter to be available on your OS).
- `advanced`: placeholder for advanced feature grouping.

```bash
pip install .[gui]
```

## Non-pip requirements

### Tkinter (GUI)

The GUI uses Tkinter, which is provided by your Python distribution or OS packages, not by `pip`:

- **Linux**: install the system package (e.g., `python3-tk` on Debian/Ubuntu, `tk` on Arch).
- **macOS**: ensure a Python build with Tk support (python.org installers include it).
- **Windows**: the official Python installer typically bundles Tkinter.
