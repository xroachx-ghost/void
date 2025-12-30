# Deployment Guide

**Void Suite - Enterprise Deployment & Installation Best Practices**

**Copyright (c) 2024 Roach Labs. All rights reserved.**

---

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Silent Installation](#silent-installation)
5. [Corporate Deployment](#corporate-deployment)
6. [Configuration Management](#configuration-management)
7. [License Deployment](#license-deployment)
8. [Network Requirements](#network-requirements)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides best practices for deploying Void Suite across multiple devices, particularly in enterprise and corporate environments. It covers installation methods, configuration management, and deployment automation.

### Audience

- IT Administrators
- System Engineers
- DevOps Teams
- MSP Providers

---

## System Requirements

### Minimum Requirements

**Operating System:**
- Windows 10/11 (64-bit)
- macOS 11.0 (Big Sur) or later
- Linux (Ubuntu 20.04+, Fedora 35+, Debian 11+)

**Hardware:**
- CPU: Dual-core 2.0 GHz or better
- RAM: 4 GB (8 GB recommended)
- Storage: 500 MB free space
- USB ports for device connection

**Software:**
- Python 3.9 or later
- ADB/Fastboot tools (included in package)

### Recommended Requirements

**For Professional/Enterprise Use:**
- CPU: Quad-core 2.5 GHz or better
- RAM: 16 GB
- Storage: 2 GB (for logs, backups, etc.)
- SSD for better performance
- Multiple USB ports or hub

---

## Installation Methods

### Method 1: Standard Interactive Installation

**Best for**: Individual workstations, manual deployments

```bash
# Download installer
wget https://github.com/xroachx-ghost/void/releases/latest/void-installer.sh

# Run installer
chmod +x void-installer.sh
./void-installer.sh
```

**Windows:**
```powershell
# Download void-installer.exe
# Double-click to run installer
# Follow prompts
```

**Features:**
- GUI-guided installation
- Options to customize installation path
- Desktop shortcuts and Start Menu entries
- Dependency installation
- License activation prompt

### Method 2: Package Managers

**Linux (Debian/Ubuntu):**
```bash
# Download .deb package
wget https://github.com/xroachx-ghost/void/releases/latest/void-suite.deb

# Install
sudo dpkg -i void-suite.deb
sudo apt-get install -f  # Resolve dependencies
```

**Linux (RPM-based):**
```bash
# Fedora/RHEL/CentOS
sudo dnf install void-suite.rpm

# Or using rpm directly
sudo rpm -ivh void-suite.rpm
```

**macOS (Homebrew):**
```bash
brew tap roach-labs/void
brew install void-suite
```

**macOS (DMG):**
```bash
# Download .dmg file
# Open and drag to Applications folder
```

### Method 3: Python Package (pip)

**Best for**: Python developers, virtual environments

```bash
# Install from PyPI
pip install void-suite

# Install with GUI support
pip install void-suite[gui]

# Install full development version
pip install void-suite[dev,gui,api]
```

**Virtual Environment (Recommended):**
```bash
# Create virtual environment
python3 -m venv void-env
source void-env/bin/activate  # Linux/Mac
void-env\Scripts\activate  # Windows

# Install
pip install void-suite
```

---

## Silent Installation

### Overview

Silent installation allows automated deployment without user interaction. Essential for:
- Corporate rollouts
- Imaging systems
- Configuration management tools (Ansible, Puppet, etc.)

### Windows Silent Install

```powershell
# Run installer with silent flags
void-installer.exe /S /D=C:\Program Files\Void Suite

# With license pre-activation
void-installer.exe /S /LICENSE="C:\deploy\license.key"

# With configuration
void-installer.exe /S /CONFIG="C:\deploy\config.ini"
```

**Installer Flags:**
- `/S` - Silent mode (no UI)
- `/D=PATH` - Custom installation directory
- `/LICENSE=PATH` - Pre-install license
- `/CONFIG=PATH` - Pre-install configuration
- `/NOSTART` - Don't launch after install
- `/NODESKTOP` - Don't create desktop shortcut

### Linux Silent Install

```bash
# Debian/Ubuntu silent install
sudo DEBIAN_FRONTEND=noninteractive dpkg -i void-suite.deb

# With pre-seeded configuration
sudo debconf-set-selections <<EOF
void-suite void-suite/license-path string /opt/deploy/license.key
void-suite void-suite/create-shortcuts boolean true
EOF
sudo dpkg -i void-suite.deb
```

**Environment Variables:**
- `VOID_INSTALL_PATH` - Installation directory
- `VOID_LICENSE_FILE` - License file path
- `VOID_CONFIG_FILE` - Configuration file path
- `VOID_SILENT_INSTALL` - Enable silent mode

### macOS Silent Install

```bash
# Install .pkg silently
sudo installer -pkg void-suite.pkg -target /

# With license pre-activation
VOID_LICENSE_FILE=/opt/deploy/license.key sudo installer -pkg void-suite.pkg -target /
```

---

## Corporate Deployment

### Using SCCM (Microsoft Endpoint Configuration Manager)

**1. Create Application:**
```xml
<!-- Application definition -->
<Application>
    <Name>Void Suite</Name>
    <Version>6.0.1</Version>
    <InstallCommand>void-installer.exe /S /D="%ProgramFiles%\Void Suite"</InstallCommand>
    <UninstallCommand>"%ProgramFiles%\Void Suite\uninstall.exe" /S</UninstallCommand>
    <DetectionMethod>Registry</DetectionMethod>
    <DetectionPath>HKLM\SOFTWARE\RoachLabs\VoidSuite</DetectionPath>
</Application>
```

**2. Create Package:**
- Add installer files
- Add license.key
- Add configuration files
- Set install command line

**3. Deploy:**
- Target device collection
- Schedule deployment
- Monitor installation status

### Using Group Policy (GPO)

**Software Installation Policy:**

1. Create network share for installer
2. Open Group Policy Management
3. Edit GPO → Computer Configuration → Software Installation
4. New Package → Select void-suite.msi
5. Deployment type: Assigned
6. Configure: Advanced → Add license file to package

**Startup Script (Alternative):**

```powershell
# GPO Startup Script: deploy-void.ps1
$installerPath = "\\server\deploy\void-installer.exe"
$licensePath = "\\server\deploy\license.key"

# Check if already installed
if (!(Test-Path "C:\Program Files\Void Suite")) {
    # Run installer
    Start-Process $installerPath -ArgumentList "/S", "/LICENSE=$licensePath" -Wait
}
```

### Using Ansible

```yaml
# void-deploy.yml
---
- name: Deploy Void Suite
  hosts: workstations
  become: yes
  
  vars:
    void_version: "6.0.1"
    license_path: "/opt/deploy/license.key"
  
  tasks:
    - name: Download installer
      get_url:
        url: "https://github.com/xroachx-ghost/void/releases/download/v{{ void_version }}/void-suite.deb"
        dest: "/tmp/void-suite.deb"
      when: ansible_os_family == "Debian"
    
    - name: Install Void Suite
      apt:
        deb: "/tmp/void-suite.deb"
      when: ansible_os_family == "Debian"
    
    - name: Copy license file
      copy:
        src: "{{ license_path }}"
        dest: "/etc/void/license.key"
        mode: '0644'
    
    - name: Configure Void Suite
      template:
        src: "config.ini.j2"
        dest: "/etc/void/config.ini"
```

### Using Docker (Experimental)

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    android-tools-adb \
    android-tools-fastboot \
    && rm -rf /var/lib/apt/lists/*

# Install Void Suite
RUN pip install void-suite[api]

# Copy license
COPY license.key /root/.void/license.key

# Expose API port
EXPOSE 8000

# Run API server
CMD ["void", "api", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  void-suite:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./license.key:/root/.void/license.key:ro
      - void-data:/root/.void
    privileged: true  # For USB device access
    devices:
      - /dev/bus/usb:/dev/bus/usb

volumes:
  void-data:
```

---

## Configuration Management

### Configuration File Format

**Location:**
- Linux/Mac: `~/.void/config.ini`
- Windows: `%USERPROFILE%\.void\config.ini`
- System-wide: `/etc/void/config.ini` (Linux)

**Sample Configuration:**

```ini
[general]
log_level = INFO
log_retention_days = 30
auto_update = false

[licensing]
license_file = /etc/void/license.key
check_license_on_startup = true

[backups]
backup_path = /var/void/backups
max_backup_size_gb = 100
auto_backup = true

[security]
require_authorization = true
audit_logging = true
log_device_access = true

[ui]
theme = dark
show_advanced_options = false
confirmation_prompts = true

[network]
proxy_server = http://proxy.company.com:8080
proxy_auth = false
timeout_seconds = 30
```

### Pre-configuring Deployments

**Option 1: Include config in installer**

```bash
# Create custom installer with config
void-package-tool \
    --config /path/to/config.ini \
    --license /path/to/license.key \
    --output void-company-installer.exe
```

**Option 2: Deploy config separately**

```bash
# Deploy config via configuration management
ansible all -m copy \
    -a "src=config.ini dest=/etc/void/config.ini mode=0644"
```

**Option 3: Generate from template**

```bash
# Use environment variables
cat > /etc/void/config.ini <<EOF
[general]
log_level = ${VOID_LOG_LEVEL:-INFO}

[licensing]
license_file = ${VOID_LICENSE_FILE}

[backups]
backup_path = ${VOID_BACKUP_PATH:-/var/void/backups}
EOF
```

---

## License Deployment

### Enterprise License Distribution

**Option 1: System-wide License**

```bash
# Install license for all users
sudo mkdir -p /etc/void
sudo cp license.key /etc/void/license.key
sudo chmod 644 /etc/void/license.key
```

Void Suite checks these locations in order:
1. `~/.void/license.key` (user-specific)
2. `/etc/void/license.key` (system-wide, Linux)
3. `C:\ProgramData\Void\license.key` (system-wide, Windows)

**Option 2: User-specific Licenses**

```bash
# Deploy via logon script
if [ ! -f "$HOME/.void/license.key" ]; then
    cp /opt/deploy/license.key "$HOME/.void/license.key"
fi
```

**Option 3: Network License (Enterprise Only)**

```ini
# config.ini
[licensing]
license_server = https://license.company.com
license_type = network
check_interval = 3600
```

### License Activation Scripts

**Automated Activation:**

```python
#!/usr/bin/env python3
# activate-license.py
from void.licensing import LicenseManager
import json
import sys

def activate_from_file(license_path):
    """Activate license from file"""
    try:
        with open(license_path, 'r') as f:
            license_data = json.load(f)
        
        manager = LicenseManager()
        if manager.activate_license(license_data):
            print("License activated successfully")
            return 0
        else:
            print("License activation failed")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: activate-license.py <license_file>")
        sys.exit(1)
    
    sys.exit(activate_from_file(sys.argv[1]))
```

---

## Network Requirements

### Firewall Rules

**Outbound (Optional, for updates/telemetry):**
- HTTPS (443): github.com, api.roach-labs.com
- DNS (53): For resolving hostnames

**Inbound (For API server):**
- TCP 8000: Default API port (configurable)

**No inbound connections required for client use.**

### Proxy Configuration

```ini
# config.ini
[network]
proxy_server = http://proxy.company.com:8080
proxy_auth = true
proxy_username = username
proxy_password = encrypted:XXXXXX

# Or via environment variables
http_proxy = http://proxy.company.com:8080
https_proxy = http://proxy.company.com:8080
no_proxy = localhost,127.0.0.1,.company.local
```

### Air-Gapped Environments

For networks without internet access:

1. **Download packages on internet-connected system**
2. **Transfer to air-gapped network**
3. **Install from local files**
4. **Activate license offline** (supported by default)

**Offline Update Process:**

```bash
# On internet-connected system
wget https://github.com/xroachx-ghost/void/releases/latest/void-suite.deb

# Transfer to air-gapped network
scp void-suite.deb user@airgap:/tmp/

# On air-gapped system
sudo dpkg -i /tmp/void-suite.deb
```

---

## Security Considerations

### Least Privilege

- Install to system directories (requires admin)
- Run as standard user (not admin/root)
- Use dedicated service account for API server
- Restrict USB device access to authorized users

### License Security

```bash
# Secure license file permissions
chmod 600 ~/.void/license.key
chown $USER:$USER ~/.void/license.key

# System-wide license
sudo chmod 644 /etc/void/license.key
sudo chown root:root /etc/void/license.key
```

### Audit Logging

Enable audit logging for compliance:

```ini
[security]
audit_logging = true
audit_log_path = /var/log/void/audit.log
log_device_access = true
log_frp_bypass = true
require_authorization_docs = true
```

### Network Segmentation

- Place workstations in separate VLAN
- Restrict access to sensitive networks
- Use network monitoring for anomaly detection

---

## Troubleshooting

### Installation Fails

**Check:**
- Sufficient disk space
- Administrator/root privileges
- No conflicting software
- Antivirus not blocking installer

**Logs:**
- Windows: `%TEMP%\void-install.log`
- Linux/Mac: `/tmp/void-install.log`

### License Not Detected

**Check:**
- License file exists in correct location
- File permissions allow reading
- File is valid JSON
- System-wide vs user-specific license

### USB Device Not Detected

**Check:**
- USB drivers installed
- Device in correct mode (ADB/Fastboot)
- USB debugging enabled on device
- User has permissions to access USB

### Performance Issues

**Optimize:**
- Close unnecessary applications
- Use SSD for better I/O
- Increase RAM if possible
- Check antivirus isn't scanning actively

---

## Best Practices Summary

✅ **DO:**
- Use silent installation for mass deployment
- Pre-configure settings via config files
- Implement audit logging for compliance
- Test deployment in staging environment first
- Document your deployment process
- Train users on proper usage
- Keep licenses secure

❌ **DON'T:**
- Hard-code credentials in scripts
- Store licenses in public locations
- Grant unnecessary administrative privileges
- Skip testing updates before deployment
- Ignore security best practices

---

## Contact

**Enterprise Support:**
Email: enterprise@roach-labs.com

**Deployment Assistance:**
Email: support@roach-labs.com

**Documentation:**
https://github.com/xroachx-ghost/void/tree/main/docs

---

**Last Updated**: December 30, 2024  
**Version**: 1.0

**Copyright (c) 2024 Roach Labs. All rights reserved.**
