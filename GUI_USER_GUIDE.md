# GUI User Guide

## Accessing the GUI

Launch the Void Suite GUI with:
```bash
void --gui
```

## GUI Modes

The GUI has two modes, switchable via the button in the top-right corner:

### 🎯 Simple Mode (Default)
A streamlined dashboard perfect for common tasks:
- Device overview card showing connected device info
- Quick action buttons for Backup, Reports, Screenshots, etc.
- Clear status indicators
- One-click refresh for device detection

**Best for:** Quick device maintenance, backups, and common operations

### ⚙️ Advanced Mode
Full-featured interface with complete control:
- All 8 categorized tabs with nested sub-tabs
- Complete access to every feature
- Device list panel on the left
- Tab navigation with scroll controls
- **Scrollable panels** - All sub-tabs support vertical scrolling, allowing you to access all options even in small windows or when panels have many options

**Best for:** Power users, development, advanced troubleshooting

## Advanced Mode Navigation

### Main Tabs

#### 📊 Dashboard
Your central hub for device information:
- **Selected Device** - Currently active device
- **Device Summary** - Key device information
  - Device details (manufacturer, model, serial)
  - Build information (Android version, build ID)
  - Connectivity status (USB, ADB, network)
  - Chipset information (detected chipset type)
  - Problem categories (targeted diagnostics)
- **Quick Actions** - Backup, Report, Analyze buttons

**Tip:** Use "Copy Device ID" or "Copy Device Summary" buttons to share info

---

#### 🔧 Device Tools
Everything you need for device management:

**Apps Sub-tab:**
- List installed apps (system/user/all)
- Install/uninstall packages
- Launch, stop, or force-stop apps
- Backup individual APKs
- Filter: system, user, or all apps

**Files Sub-tab:**
- Browse device filesystem
- Pull files from device to computer
- Push files from computer to device
- Delete remote files
- Navigate /sdcard and other directories

**System Sub-tab:**
- Adjust DPI (screen density)
- Set animation scales (performance tuning)
- Configure screen timeout
- Enable USB debugging (standard or forced)
- System-level tweaks

**Network Sub-tab:**
- Check internet connectivity
- Network diagnostics
- Connection analysis

---

#### 🔄 Recovery
Advanced recovery and repair workflows:

**Data Recovery Sub-tab:**
- Recover contacts from device
- Extract SMS messages
- FRP (Factory Reset Protection) bypass methods
- Data extraction tools

**EDL Mode Sub-tab:**
- Chipset detection (Qualcomm, MediaTek, Samsung)
- EDL mode entry workflows
- Recovery mode access
- Bootloader/fastboot mode entry
- Chipset-specific recovery procedures

**Flash/Dump Sub-tab:**
- EDL flash operations (requires loaders)
- Partition dump/backup
- Low-level device operations
- Firehose protocol support

---

#### 🔍 Diagnostics
Troubleshooting and monitoring tools:

**Logcat Sub-tab:**
- Real-time device log streaming
- Filter by tag/priority
- Start/stop logcat capture
- Live log analysis

**Monitor Sub-tab:**
- Start/stop system monitoring
- View real-time device metrics
- CPU, memory, disk usage
- Performance snapshots

**Troubleshoot Sub-tab:**
- Platform tools diagnostics (ADB, fastboot)
- USB debugging status checks
- Driver guidance for your OS
- Display state/framebuffer analysis
- Download required assets
- Setup wizard diagnostics

---

#### 💾 Data
Export and database management:

**Exports Sub-tab:**
- Export device list (JSON)
- Export statistics (JSON)
- Export operation logs (JSON/CSV)
- Export reports and backups
- Open exports directory
- List recent exports, reports, backups

**Database Sub-tab:**
- Database health check
- View recent logs
- View recent backups
- View recent reports
- View recent devices
- Top methods statistics
- Filtered log exports

---

#### 🤖 Automation
Powerful automation features:

**Commands Sub-tab:**
- Browse all CLI commands
- Execute commands from GUI
- Search command catalog
- View command details
- Command line builder

**Plugins Sub-tab:**
- Discover and load plugins
- Execute plugin operations
- View plugin metadata
- Extend Void Suite functionality

**Browser Sub-tab:**
- Launch automated browser
- Navigate to URLs
- Click coordinates
- Type text
- Take screenshots
- Automation for web-based tasks

**AI Assistant Sub-tab:**
- Gemini-powered AI assistant
- Task management
- Conversation history
- Model configuration
- Browser automation integration
- Asset discovery and download assistance

---

#### 📝 Logs
Operations log viewer:
- All operations logged in real-time
- Color-coded by level (INFO, WARN, ERROR, DATA)
- Scrollable history
- Export functionality
- Searchable (Ctrl+F in text area)

---

#### ⚙️ Settings
Configuration and help:

**Configuration Sub-tab:**
- Enable/disable auto-backups
- Enable/disable reports
- Enable/disable analytics
- Set exports directory
- Set reports directory
- Save settings

**Help Sub-tab:**
- "What Does This Do?" explanations
- Action descriptions
- Feature help text
- Quick reference

---

## Navigation Tips

### Keyboard Shortcuts
- **Mouse Wheel** - Scroll through tabs OR scroll within panel content (when mouse is over a tab)
- **Ctrl+C** - Copy selected text
- **Ctrl+A** - Select all text (in log areas)

### Scrolling in Panels
- All Advanced mode sub-tabs support vertical scrolling
- Scroll with mouse wheel when hovering over the panel
- Scroll bar appears on the right side of each panel when content exceeds visible area
- Works in both fullscreen and windowed modes
- No horizontal scrolling - content adapts to window width

### Tab Controls
- **◀ ▶ Buttons** - Navigate tabs (when too many to display)
- **Click Tab** - Switch to that tab
- **Click Sub-tab** - Switch to sub-feature

### Device Selection
1. **Advanced Mode**: Click device in left panel list
2. **Simple Mode**: Device auto-selected if only one connected
3. Use **Refresh Devices** to re-scan

### Status Bar
Bottom of window shows:
- Current operation status
- Selected device
- Progress indicators
- Error/warning messages

## Common Workflows

### Quick Backup
1. Connect device
2. Click **Refresh Devices**
3. Select device (Advanced) or use auto-selected (Simple)
4. Click **Backup** button
5. Wait for completion
6. Check exports directory

### Troubleshooting Connection
1. Go to 🔍 **Diagnostics** → **Troubleshoot**
2. Review diagnostic checks
3. Follow remediation links if issues found
4. Click **Recheck** after fixes
5. Verify all checks pass

### EDL Recovery
1. Go to 🔄 **Recovery** → **EDL Mode**
2. Run chipset detection
3. Review preflight checks in **Troubleshoot** tab
4. Follow manual steps if required
5. Execute recovery workflow
6. Monitor progress in **Logs**

### Export Device Report
1. Select device in **Dashboard**
2. Click **Generate Report**
3. Go to 💾 **Data** → **Exports**
4. Click **Open Exports Directory**
5. Find the report file

## Best Practices

1. **Always check device selection** before operations
2. **Monitor the Logs tab** during long operations
3. **Use Simple Mode** for routine tasks
4. **Use Advanced Mode** for diagnostics and troubleshooting
5. **Back up before** attempting recovery operations
6. **Read error messages** carefully - they contain guidance
7. **Keep platform-tools updated** for best compatibility

## Getting Help

- Hover over buttons for tooltips
- Check the **Help** sub-tab in Settings
- Review error messages in Logs for next steps
- Consult documentation in the repository

## Mode Persistence

Your selected mode (Simple/Advanced) is remembered between sessions, so the GUI will open in your preferred mode next time.
