#!/usr/bin/env python3
"""
Void Suite Installer

Creates Start Menu shortcuts and desktop entries for easy access.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

import os
import platform
import shutil
import subprocess
import sys
import json
from pathlib import Path


class VoidInstaller:
    """Installer for Void Suite"""

    def __init__(self):
        self.system = platform.system()
        self.void_dir = Path(__file__).parent.absolute()
        self.python_exe = sys.executable

    def install(self):
        """Run the installation"""
        print("=" * 60)
        print("Void Suite Installer")
        print("Copyright (c) 2024 Roach Labs. All rights reserved.")
        print("Made by James Michael Roach Jr.")
        print("=" * 60)
        print()
        
        print(f"Detected OS: {self.system}")
        print(f"Python: {self.python_exe}")
        print(f"Void Directory: {self.void_dir}")
        print()

        # Install dependencies
        print("Installing dependencies...")
        self._install_dependencies()
        
        # Handle licensing
        print()
        self._handle_licensing()
        
        # Create shortcuts based on OS
        if self.system == "Windows":
            self._install_windows()
        elif self.system == "Darwin":
            self._install_macos()
        elif self.system == "Linux":
            self._install_linux()
        else:
            print(f"Unsupported operating system: {self.system}")
            return False

        print()
        print("=" * 60)
        print("Installation completed successfully!")
        print()
        print("You can now launch Void Suite from:")
        if self.system == "Windows":
            print("  - Start Menu > Void Suite (GUI)")
            print("  - Start Menu > Void Suite (CLI)")
        elif self.system == "Darwin":
            print("  - Applications > Void Suite (GUI)")
            print("  - Applications > Void Suite (CLI)")
        elif self.system == "Linux":
            print("  - Application Menu > Void Suite (GUI)")
            print("  - Application Menu > Void Suite (CLI)")
        print("=" * 60)
        return True
    
    def _handle_licensing(self):
        """Handle license activation during installation"""
        try:
            from void.licensing import LicenseManager
            
            print("=" * 60)
            print("License Activation")
            print("=" * 60)
            print()
            print("Void Suite requires a license to use.")
            print("You can:")
            print("  1. Activate a license key (if you have one)")
            print("  2. Start a 14-day free trial")
            print("  3. Skip for now (activate later)")
            print()
            
            choice = input("Enter choice (1/2/3): ").strip()
            
            manager = LicenseManager()
            
            if choice == "1":
                # Activate license key
                license_file = input("Enter path to license key file: ").strip()
                if Path(license_file).exists():
                    try:
                        import json
                        with open(license_file, 'r') as f:
                            license_data = json.load(f)
                        
                        if manager.activate_license(license_data):
                            print("✓ License activated successfully!")
                        else:
                            print("✗ License activation failed.")
                    except Exception as e:
                        print(f"✗ Error activating license: {e}")
                else:
                    print("✗ License file not found.")
            
            elif choice == "2":
                # Start trial
                if manager.start_trial():
                    print("✓ 14-day trial started successfully!")
                    print("  You can purchase a license anytime from our website.")
                else:
                    print("✗ Failed to start trial.")
            
            else:
                # Skip
                print("⚠ Skipping license activation.")
                print("  You can activate a license later using: void license activate")
            
            print()
        
        except ImportError:
            print("⚠ Licensing module not available. Skipping license activation.")
        except Exception as e:
            print(f"⚠ Error during licensing: {e}")
            print("  You can activate a license later using: void license activate")

    def _install_dependencies(self):
        """Install Python dependencies"""
        try:
            subprocess.check_call(
                [self.python_exe, "-m", "pip", "install", "-e", str(self.void_dir)],
                stdout=subprocess.DEVNULL
            )
            print("✓ Dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            sys.exit(1)

    def _install_windows(self):
        """Install on Windows"""
        import winshell
        from win32com.client import Dispatch
        
        # Get Start Menu Programs folder
        start_menu = Path(winshell.start_menu()) / "Programs" / "Void Suite"
        start_menu.mkdir(parents=True, exist_ok=True)
        
        # Get Desktop
        desktop = Path(winshell.desktop())
        
        # Create GUI shortcut in Start Menu
        gui_shortcut_path = start_menu / "Void Suite (GUI).lnk"
        self._create_windows_shortcut(
            gui_shortcut_path,
            self.python_exe,
            f'"{self.void_dir / "void.py"}"',
            str(self.void_dir),
            "Void Suite - Graphical User Interface"
        )
        print(f"✓ Created: {gui_shortcut_path}")
        
        # Create CLI shortcut in Start Menu
        cli_shortcut_path = start_menu / "Void Suite (CLI).lnk"
        self._create_windows_shortcut(
            cli_shortcut_path,
            self.python_exe,
            f'"{self.void_dir / "void.py"}" --cli',
            str(self.void_dir),
            "Void Suite - Command Line Interface"
        )
        print(f"✓ Created: {cli_shortcut_path}")
        
        # Create desktop shortcut for GUI
        desktop_shortcut = desktop / "Void Suite.lnk"
        self._create_windows_shortcut(
            desktop_shortcut,
            self.python_exe,
            f'"{self.void_dir / "void.py"}"',
            str(self.void_dir),
            "Void Suite - Android Toolkit"
        )
        print(f"✓ Created: {desktop_shortcut}")

    def _create_windows_shortcut(self, shortcut_path, target, arguments, working_dir, description):
        """Create a Windows shortcut"""
        try:
            from win32com.client import Dispatch
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = target
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = working_dir
            shortcut.Description = description
            shortcut.save()
        except ImportError:
            print("✗ Warning: pywin32 not installed. Installing...")
            subprocess.check_call([self.python_exe, "-m", "pip", "install", "pywin32"])
            # Retry
            self._create_windows_shortcut(shortcut_path, target, arguments, working_dir, description)

    def _install_macos(self):
        """Install on macOS"""
        # Create Applications folder scripts
        apps_dir = Path.home() / "Applications" / "Void Suite"
        apps_dir.mkdir(parents=True, exist_ok=True)
        
        # Create GUI launcher script
        gui_script = apps_dir / "Void Suite (GUI).command"
        gui_script.write_text(f"""#!/bin/bash
cd "{self.void_dir}"
"{self.python_exe}" void.py
""")
        gui_script.chmod(0o755)
        print(f"✓ Created: {gui_script}")
        
        # Create CLI launcher script
        cli_script = apps_dir / "Void Suite (CLI).command"
        cli_script.write_text(f"""#!/bin/bash
cd "{self.void_dir}"
"{self.python_exe}" void.py --cli
""")
        cli_script.chmod(0o755)
        print(f"✓ Created: {cli_script}")
        
        # Create desktop shortcut for GUI
        desktop = Path.home() / "Desktop"
        desktop_script = desktop / "Void Suite.command"
        desktop_script.write_text(f"""#!/bin/bash
cd "{self.void_dir}"
"{self.python_exe}" void.py
""")
        desktop_script.chmod(0o755)
        print(f"✓ Created: {desktop_script}")

    def _install_linux(self):
        """Install on Linux"""
        # Create .desktop files
        apps_dir = Path.home() / ".local" / "share" / "applications"
        apps_dir.mkdir(parents=True, exist_ok=True)
        
        # Create GUI desktop entry
        gui_desktop = apps_dir / "void-suite-gui.desktop"
        gui_desktop.write_text(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Void Suite (GUI)
Comment=Android Device Management Toolkit - GUI Mode
Exec={self.python_exe} {self.void_dir / "void.py"}
Path={self.void_dir}
Terminal=false
Categories=Development;System;Utility;
""")
        gui_desktop.chmod(0o755)
        print(f"✓ Created: {gui_desktop}")
        
        # Create CLI desktop entry
        cli_desktop = apps_dir / "void-suite-cli.desktop"
        cli_desktop.write_text(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Void Suite (CLI)
Comment=Android Device Management Toolkit - CLI Mode
Exec={self.python_exe} {self.void_dir / "void.py"} --cli
Path={self.void_dir}
Terminal=true
Categories=Development;System;Utility;
""")
        cli_desktop.chmod(0o755)
        print(f"✓ Created: {cli_desktop}")
        
        # Create desktop shortcut for GUI
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            desktop_file = desktop / "void-suite.desktop"
            desktop_file.write_text(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Void Suite
Comment=Android Device Management Toolkit
Exec={self.python_exe} {self.void_dir / "void.py"}
Path={self.void_dir}
Terminal=false
Categories=Development;System;Utility;
""")
            desktop_file.chmod(0o755)
            print(f"✓ Created: {desktop_file}")
        
        # Update desktop database
        try:
            subprocess.run(["update-desktop-database", str(apps_dir)], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass  # update-desktop-database not available

    def uninstall(self):
        """Uninstall Void Suite shortcuts"""
        print("=" * 60)
        print("Void Suite Uninstaller")
        print("=" * 60)
        print()
        
        if self.system == "Windows":
            self._uninstall_windows()
        elif self.system == "Darwin":
            self._uninstall_macos()
        elif self.system == "Linux":
            self._uninstall_linux()
        
        print()
        print("Uninstallation completed!")
        print("Note: Python package 'void-suite' is still installed.")
        print("To remove it completely, run: pip uninstall void-suite")
        print("=" * 60)

    def _uninstall_windows(self):
        """Uninstall from Windows"""
        try:
            import winshell
            start_menu = Path(winshell.start_menu()) / "Programs" / "Void Suite"
            desktop = Path(winshell.desktop())
            
            if start_menu.exists():
                shutil.rmtree(start_menu)
                print(f"✓ Removed: {start_menu}")
            
            desktop_shortcut = desktop / "Void Suite.lnk"
            if desktop_shortcut.exists():
                desktop_shortcut.unlink()
                print(f"✓ Removed: {desktop_shortcut}")
        except ImportError:
            print("✗ winshell not available")

    def _uninstall_macos(self):
        """Uninstall from macOS"""
        apps_dir = Path.home() / "Applications" / "Void Suite"
        if apps_dir.exists():
            shutil.rmtree(apps_dir)
            print(f"✓ Removed: {apps_dir}")
        
        desktop_script = Path.home() / "Desktop" / "Void Suite.command"
        if desktop_script.exists():
            desktop_script.unlink()
            print(f"✓ Removed: {desktop_script}")

    def _uninstall_linux(self):
        """Uninstall from Linux"""
        apps_dir = Path.home() / ".local" / "share" / "applications"
        
        gui_desktop = apps_dir / "void-suite-gui.desktop"
        if gui_desktop.exists():
            gui_desktop.unlink()
            print(f"✓ Removed: {gui_desktop}")
        
        cli_desktop = apps_dir / "void-suite-cli.desktop"
        if cli_desktop.exists():
            cli_desktop.unlink()
            print(f"✓ Removed: {cli_desktop}")
        
        desktop_file = Path.home() / "Desktop" / "void-suite.desktop"
        if desktop_file.exists():
            desktop_file.unlink()
            print(f"✓ Removed: {desktop_file}")


def main():
    """Main installer function"""
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        installer = VoidInstaller()
        installer.uninstall()
    else:
        installer = VoidInstaller()
        installer.install()


if __name__ == "__main__":
    main()
