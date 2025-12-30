# Screenshots Guide

**Void Suite - Visual Documentation & Marketing Materials**

**Copyright (c) 2024 Roach Labs. All rights reserved.**

---

## Overview

This document provides guidelines for capturing, creating, and maintaining screenshots for Void Suite. Professional screenshots are essential for:

- Marketing materials
- Documentation
- User guides
- Website and GitHub
- Sales presentations

---

## Required Screenshots

### 1. Main Interface Screenshots

#### CLI Interface
- [ ] **Main Menu** - Show the main CLI menu with all categories
- [ ] **Help System** - Display help command output
- [ ] **Device Detection** - Show successful device connection
- [ ] **Command Execution** - Example of running a command
- [ ] **Error Handling** - Show user-friendly error message
- [ ] **Progress Indicators** - Show progress bars/spinners

**File naming**: `cli-main-menu.png`, `cli-help.png`, etc.

#### GUI Interface
- [ ] **Dashboard/Home** - Main window on startup
- [ ] **Device Manager** - Device list and information panel
- [ ] **FRP Wizard** - FRP bypass wizard interface
- [ ] **EDL Operations** - EDL toolkit interface
- [ ] **Backup Manager** - Backup/restore interface
- [ ] **Settings** - Configuration panel
- [ ] **License Manager** - License activation dialog
- [ ] **About Dialog** - About window with license info

**File naming**: `gui-dashboard.png`, `gui-device-manager.png`, etc.

### 2. Feature Showcase Screenshots

#### Device Management
- [ ] Device information display
- [ ] Multi-device handling
- [ ] Battery and system stats
- [ ] Property viewer

#### Backup & Recovery
- [ ] Creating a backup (in progress)
- [ ] Backup completed with summary
- [ ] Restore interface
- [ ] Backup history/list

#### FRP Bypass
- [ ] FRP wizard - method selection
- [ ] FRP wizard - in progress
- [ ] FRP wizard - success message
- [ ] Multiple FRP methods available

#### EDL Operations
- [ ] EDL device detection
- [ ] Partition list
- [ ] Flashing progress
- [ ] EDL toolkit menu

#### Diagnostics
- [ ] Performance analyzer output
- [ ] Network analysis
- [ ] Display diagnostics
- [ ] Logcat viewer

#### Reports
- [ ] HTML report preview
- [ ] Report generation progress
- [ ] Report contents sample

### 3. Licensing Screenshots

- [ ] **Trial Mode** - Trial period countdown/notice
- [ ] **License Activation** - Activation dialog
- [ ] **License Status** - Valid license display
- [ ] **License Expired** - Expiration notice
- [ ] **Upgrade Prompt** - Prompt to upgrade tier

### 4. Installation Screenshots

- [ ] Installer welcome screen
- [ ] License acceptance (EULA)
- [ ] Installation progress
- [ ] Installation complete
- [ ] First-run wizard

### 5. Platform-Specific Screenshots

#### Windows
- [ ] Start Menu shortcuts
- [ ] Desktop icon
- [ ] Windows GUI theme
- [ ] System tray integration (if applicable)

#### macOS
- [ ] Applications folder
- [ ] macOS GUI theme
- [ ] Menu bar integration (if applicable)
- [ ] Touch Bar support (if applicable)

#### Linux
- [ ] Application menu
- [ ] Linux GUI theme
- [ ] Terminal integration

---

## Screenshot Standards

### Technical Requirements

**Resolution:**
- Minimum: 1920x1080 (Full HD)
- Recommended: 2560x1440 (2K) or 3840x2160 (4K)
- High DPI displays: Use native resolution

**Format:**
- Primary: PNG (lossless, transparency support)
- Alternative: WebP (smaller size, good quality)
- Avoid: JPEG (lossy compression, no transparency)

**File Size:**
- Target: Under 500 KB per screenshot
- Use PNG compression tools (e.g., pngquant, TinyPNG)
- Balance quality and file size

**Naming Convention:**
```
<interface>-<feature>-<variant>.png

Examples:
gui-dashboard-light.png
gui-dashboard-dark.png
cli-main-menu.png
cli-frp-wizard-progress.png
installer-windows-welcome.png
```

### Visual Standards

**Window Size:**
- CLI: 120x30 characters minimum
- GUI: Standard window size (not full screen)
- Show application focused (active window)
- Avoid maximized windows unless necessary

**Content:**
- Use realistic but non-sensitive data
- Avoid personal information, real device IDs
- Use placeholder data when needed
- Show successful operations (green checkmarks, "Success" messages)

**Clarity:**
- Sharp, in-focus images
- No blur or artifacts
- High contrast for readability
- Avoid glare on physical photos

**Context:**
- Include relevant UI elements (menus, toolbars)
- Show application title bar
- Include cursor for interactive screenshots
- Capture modal dialogs with parent window

**Consistency:**
- Same theme/color scheme across related shots
- Same resolution within a category
- Same mock data across related screenshots

---

## Capturing Screenshots

### Tools

**Windows:**
- Built-in: Snipping Tool or Snip & Sketch (Win+Shift+S)
- Professional: ShareX, Greenshot
- Screen recording: OBS Studio

**macOS:**
- Built-in: Screenshot app (Cmd+Shift+3/4/5)
- Professional: CleanShot X, Skitch
- Screen recording: QuickTime, OBS Studio

**Linux:**
- Built-in: Screenshot utility (varies by DE)
- Professional: Flameshot, Shutter, Spectacle
- Screen recording: SimpleScreenRecorder, OBS Studio

### Preparation

**Before capturing:**

1. **Clean Environment**
   - Close unnecessary applications
   - Hide desktop clutter
   - Clear notification tray
   - Use clean wallpaper (solid color or minimal)

2. **Application Setup**
   - Launch application fresh
   - Set appropriate theme (light/dark)
   - Navigate to desired view
   - Load sample data if needed

3. **Window Positioning**
   - Center window on screen
   - Appropriate size (not too small/large)
   - All important UI visible
   - No overlapping windows

4. **Mock Data**
   - Use consistent device names (e.g., "Samsung Galaxy S21")
   - Use realistic but fake IMEI/serial numbers
   - Use generic customer names if needed
   - Don't use real personal data

### Capture Process

1. **Set Up Scene**
   - Arrange UI as desired
   - Position mouse cursor (if showing interaction)
   - Ensure all text is readable

2. **Capture**
   - Use appropriate tool
   - Capture window only (not full screen) when possible
   - Include window shadow for depth

3. **Review**
   - Check for clarity
   - Verify no sensitive data visible
   - Confirm all important elements captured

4. **Edit** (if needed)
   - Crop to remove unnecessary space
   - Add arrows/callouts for emphasis (optional)
   - Blur any sensitive information
   - Optimize file size

### Post-Processing

**Basic Editing:**
- Crop to relevant area
- Add subtle shadow (for standalone windows)
- Adjust brightness/contrast if needed
- Remove any artifacts

**Annotations (Optional):**
- Red arrows to highlight features
- Number labels for step-by-step guides
- Text callouts for explanations
- Blur/redact sensitive information

**Tools:**
- GIMP (free, cross-platform)
- Photoshop (professional)
- Figma (design tool, free tier)
- Canva (online, easy to use)

---

## Marketing Screenshots

### Hero Images

**Main Marketing Image:**
- Show GUI dashboard with device connected
- Bright, professional look
- All features visible but not cluttered
- Annotate key features with labels

**Recommended Size**: 1920x1080 or wider
**Format**: PNG or high-quality WebP

### Feature Highlights

Create focused screenshots for each major feature:

1. **Device Management** - Show device list with details
2. **FRP Bypass** - Show wizard with success message
3. **EDL Operations** - Show partition management
4. **Backup & Restore** - Show backup in progress
5. **Diagnostics** - Show performance graphs

**Style**: Clean, focused, one feature per image
**Size**: 1280x720 or 1920x1080

### Comparison Images

**Before/After:**
- Device locked (before) vs unlocked (after)
- Slow performance vs optimized
- Missing features vs full features

**Split-Screen:**
- CLI vs GUI comparison
- Trial vs Professional tier comparison
- Windows vs Mac vs Linux

### Social Media Images

**Twitter/X** (1200x675):
- Landscape oriented
- Key feature prominently displayed
- Minimal text overlay

**Instagram** (1080x1080):
- Square format
- Mobile-friendly view
- Bold, eye-catching

**LinkedIn** (1200x627):
- Professional appearance
- Business value highlighted
- Clean design

---

## Screenshot Library Organization

### Directory Structure

```
docs/
└── screenshots/
    ├── README.md (this file)
    ├── cli/
    │   ├── main-menu.png
    │   ├── help-system.png
    │   └── device-detection.png
    ├── gui/
    │   ├── dashboard-light.png
    │   ├── dashboard-dark.png
    │   ├── device-manager.png
    │   └── frp-wizard.png
    ├── features/
    │   ├── backup-in-progress.png
    │   ├── edl-operations.png
    │   └── diagnostics.png
    ├── licensing/
    │   ├── trial-mode.png
    │   ├── activation.png
    │   └── license-status.png
    ├── installation/
    │   ├── installer-windows.png
    │   ├── installer-mac.png
    │   └── installer-linux.png
    ├── marketing/
    │   ├── hero-image.png
    │   ├── feature-highlights.png
    │   └── social-media/
    │       ├── twitter-card.png
    │       └── instagram-post.png
    └── platform-specific/
        ├── windows/
        ├── macos/
        └── linux/
```

### Metadata

Create a `manifest.json` for each directory:

```json
{
  "screenshots": [
    {
      "filename": "gui-dashboard-light.png",
      "title": "Void Suite Dashboard (Light Theme)",
      "description": "Main dashboard showing device management interface",
      "resolution": "1920x1080",
      "theme": "light",
      "platform": "all",
      "date_captured": "2024-12-30",
      "version": "6.0.1",
      "tags": ["gui", "dashboard", "main-window"]
    }
  ]
}
```

---

## Usage in Documentation

### Markdown

```markdown
![Dashboard](docs/screenshots/gui/dashboard-light.png)
*Void Suite Dashboard - Device Management Interface*
```

### HTML

```html
<img src="docs/screenshots/gui/dashboard-light.png" 
     alt="Void Suite Dashboard" 
     width="800" 
     style="border: 1px solid #ddd; border-radius: 4px;" />
<p><em>Void Suite Dashboard - Device Management Interface</em></p>
```

### Website Integration

```jsx
// React component
import dashboardImg from './assets/screenshots/dashboard.png';

<div className="screenshot-container">
  <img 
    src={dashboardImg} 
    alt="Void Suite Dashboard" 
    loading="lazy"
    className="shadow-lg rounded-lg"
  />
  <p className="caption">Device Management Interface</p>
</div>
```

---

## Maintenance

### Regular Updates

- [ ] Update screenshots with each major release
- [ ] Verify all screenshots match current UI
- [ ] Remove outdated screenshots
- [ ] Add screenshots for new features
- [ ] Update marketing materials

### Version Control

- Track screenshot versions
- Tag screenshots with software version
- Keep previous versions for historical reference
- Update documentation references

### Review Schedule

- **Minor Updates** (bug fixes): Update only affected screenshots
- **Major Updates** (new features): Full screenshot audit and update
- **Quarterly Review**: Check for outdated or low-quality images

---

## Legal Considerations

### Copyright

All screenshots are copyright Roach Labs and follow the same license as the software.

### Privacy

- Never include real customer data
- Use mock/placeholder data
- Blur any inadvertent PII
- Don't capture sensitive information

### Usage Rights

Screenshots in docs/ directory:
- May be used in documentation
- May be used in marketing materials
- May be shared with proper attribution
- Not for use in competing products

---

## Checklist for New Screenshots

Before adding a screenshot to the repository:

- [ ] High resolution (1920x1080 minimum)
- [ ] PNG format
- [ ] Optimized file size (< 500 KB)
- [ ] Consistent with existing screenshots
- [ ] No sensitive data visible
- [ ] Proper filename (follows convention)
- [ ] Saved in correct directory
- [ ] Added to manifest.json
- [ ] Referenced in documentation
- [ ] Reviewed for quality

---

## Need Help?

For questions about screenshots or visual materials:

**Documentation Team**: docs@roach-labs.com  
**Marketing Team**: marketing@roach-labs.com  
**General Support**: support@roach-labs.com

---

**Last Updated**: December 30, 2024  
**Version**: 1.0

**Copyright (c) 2024 Roach Labs. All rights reserved.**
