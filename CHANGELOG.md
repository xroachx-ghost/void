# Changelog

All notable changes to Void Suite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.1] - 2025-12-30

### Added

#### Core Features
- **Device Discovery & Management**: Automatic device detection with comprehensive summaries and health checks
- **ADB/Fastboot Integration**: Full wrapper for Android Debug Bridge and fastboot commands with guided CLI
- **Backup & File Management**: Device backups, file transfers, screenshots, and organized exports
- **App Inventory Tools**: Application listing, management, and package analysis
- **Logcat Collection**: Real-time log capture and analysis utilities

#### Diagnostics
- **Performance Diagnostics**: CPU, memory, and storage analysis
- **Network Diagnostics**: Connectivity testing and network configuration checks
- **Display Diagnostics**: Screen and display property analysis

#### Recovery & Advanced Tools
- **FRP Guidance**: Step-by-step Factory Reset Protection assistance
- **Data Recovery Helpers**: Tools for recovering accessible data from devices
- **System Tweaks**: Safe system configuration adjustments
- **Qualcomm EDL Utilities**: Emergency Download Mode tools for flash, backup, and partition operations
- **Chipset Helpers**: Device-specific tooling support

#### AI Integration
- **Gemini-Powered AI Agent**: Automated browser workflows for:
  - Locating OEM downloads (firmware, firehose programmers, recovery images)
  - Searching for device-specific app bundles and dependencies
  - Gathering reference links for repair or recovery steps

#### User Interface
- **CLI Mode**: Interactive command-line interface with rich formatting
- **GUI Mode**: Tkinter-based graphical interface with:
  - **Simple Mode**: Streamlined dashboard for quick actions
  - **Advanced Mode**: Full feature access with organized tabs
  - 8 main categories: Dashboard, Device Tools, Recovery, Diagnostics, Data, Automation, Logs, Settings

#### Extensibility
- **Plugin Support**: Extensible command system for custom workflows
- **Report Generation**: Automated device reports and documentation

### Technical
- Python 3.9+ support
- Cross-platform compatibility (Windows, macOS, Linux)
- Virtual environment recommended installation
- Optional GUI dependencies via `pip install .[gui]`

---

## [Unreleased]

### Pending Pull Requests
- Device security, partition, ROM validation and recovery tooling (#22)
- Destructive-action confirmations and audit logging (#23)

[6.0.1]: https://github.com/xroachx-ghost/void/releases/tag/v6.0.1
[Unreleased]: https://github.com/xroachx-ghost/void/compare/v6.0.1...HEAD