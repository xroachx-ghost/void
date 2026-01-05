"""
Embedded Tools Manager - Manages all standalone embedded binaries and utilities.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import platform
import stat
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, Optional
import urllib.request


class EmbeddedToolsManager:
    """Manages embedded Android tools and utilities"""

    # Tool download URLs (official sources)
    PLATFORM_TOOLS_URLS = {
        "Windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
        "Darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
        "Linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
    }

    def __init__(self):
        self.system = platform.system()
        self.arch = platform.machine().lower()
        self.tools_dir = Path(__file__).parent / "binaries"
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        # Platform-specific executable extensions
        self.exe_ext = ".exe" if self.system == "Windows" else ""

    def ensure_all_tools(self) -> bool:
        """Ensure all required tools are available"""
        print("🔧 Checking embedded tools...")

        tools_needed = ["adb", "fastboot"]
        missing = []

        for tool in tools_needed:
            if not self.get_tool_path(tool):
                missing.append(tool)

        if missing:
            print(f"📥 Missing tools: {', '.join(missing)}")
            return self.download_platform_tools()

        print("✅ All tools available")
        return True

    def get_tool_path(self, tool_name: str) -> Optional[Path]:
        """Get the path to an embedded tool"""
        tool_file = tool_name + self.exe_ext

        # Check in tools directory
        tool_path = self.tools_dir / "platform-tools" / tool_file
        if tool_path.exists():
            return tool_path

        # Alternative locations
        alt_path = self.tools_dir / tool_file
        if alt_path.exists():
            return alt_path

        return None

    def download_platform_tools(self) -> bool:
        """Download and extract Android platform tools"""
        print(f"📥 Downloading platform tools for {self.system}...")

        url = self.PLATFORM_TOOLS_URLS.get(self.system)
        if not url:
            print(f"❌ Unsupported platform: {self.system}")
            return False

        try:
            # Download
            zip_path = self.tools_dir / "platform-tools.zip"
            print("   Downloading from Google...")
            urllib.request.urlretrieve(url, zip_path)

            # Extract
            print("   Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.tools_dir)

            # Make executable (Unix-like systems)
            if self.system in ["Linux", "Darwin"]:
                for tool in ["adb", "fastboot"]:
                    tool_path = self.tools_dir / "platform-tools" / tool
                    if tool_path.exists():
                        tool_path.chmod(tool_path.stat().st_mode | stat.S_IEXEC)

            # Cleanup
            zip_path.unlink()

            print("✅ Platform tools installed successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to download platform tools: {e}")
            return False

    def get_adb_command(self) -> str:
        """Get the full path to ADB command"""
        adb_path = self.get_tool_path("adb")
        if adb_path:
            return str(adb_path)

        # Fallback to system PATH
        return "adb"

    def get_fastboot_command(self) -> str:
        """Get the full path to fastboot command"""
        fastboot_path = self.get_tool_path("fastboot")
        if fastboot_path:
            return str(fastboot_path)

        # Fallback to system PATH
        return "fastboot"

    def test_tools(self) -> Dict[str, bool]:
        """Test if tools are working"""
        results = {}

        # Test ADB
        try:
            result = subprocess.run(
                [self.get_adb_command(), "version"], capture_output=True, timeout=5
            )
            results["adb"] = result.returncode == 0
        except Exception:
            results["adb"] = False

        # Test Fastboot
        try:
            result = subprocess.run(
                [self.get_fastboot_command(), "--version"], capture_output=True, timeout=5
            )
            results["fastboot"] = result.returncode == 0
        except Exception:
            results["fastboot"] = False

        return results

    def create_edl_tools(self):
        """Create embedded EDL tools and utilities"""
        # EDL Python library (embedded)
        edl_dir = self.tools_dir / "edl"
        edl_dir.mkdir(exist_ok=True)

        # Create a basic EDL interface script
        edl_script = edl_dir / "edl_interface.py"
        edl_script.write_text(
            '''#!/usr/bin/env python3
"""
Embedded EDL Interface
Minimal EDL mode interface for Qualcomm devices
"""
import usb.core
import usb.util
import struct

class EDLInterface:
    """Basic EDL interface for Qualcomm devices"""
    
    QUALCOMM_VID = 0x05c6
    EDL_PID = 0x9008
    
    def __init__(self):
        self.device = None
    
    def find_device(self):
        """Find Qualcomm device in EDL mode"""
        self.device = usb.core.find(idVendor=self.QUALCOMM_VID, idProduct=self.EDL_PID)
        return self.device is not None
    
    def read_info(self):
        """Read basic device info"""
        if not self.device:
            return None
        
        try:
            # Basic device info
            return {
                'vendor_id': f'{self.device.idVendor:04x}',
                'product_id': f'{self.device.idProduct:04x}',
                'manufacturer': usb.util.get_string(self.device, self.device.iManufacturer),
                'product': usb.util.get_string(self.device, self.device.iProduct),
            }
        except Exception as e:
            return {'error': str(e)}

if __name__ == '__main__':
    edl = EDLInterface()
    if edl.find_device():
        print("EDL device found!")
        print(edl.read_info())
    else:
        print("No EDL device found")
'''
        )

        print(f"✅ Created EDL tools in {edl_dir}")

    def create_recovery_tools(self):
        """Create embedded recovery and repair tools"""
        recovery_dir = self.tools_dir / "recovery"
        recovery_dir.mkdir(exist_ok=True)

        # Create bootloop fixer
        bootloop_fixer = recovery_dir / "bootloop_fixer.py"
        bootloop_fixer.write_text(
            '''#!/usr/bin/env python3
"""
Bootloop Fixer - Automated bootloop repair
"""
import subprocess
import time

def fix_bootloop(device_id):
    """Attempt to fix bootloop"""
    fixes = [
        # Clear cache partition
        lambda: subprocess.run(['adb', '-s', device_id, 'shell', 'recovery', '--wipe_cache']),
        
        # Clear dalvik cache
        lambda: subprocess.run(['adb', '-s', device_id, 'shell', 'rm', '-rf', '/data/dalvik-cache/*']),
        
        # Fix permissions
        lambda: subprocess.run(['adb', '-s', device_id, 'shell', 'chmod', '755', '/system']),
        
        # Remove problematic apps
        lambda: subprocess.run(['adb', '-s', device_id, 'shell', 'pm', 'disable-user', '--user', '0', 'com.android.vending']),
    ]
    
    print("🔧 Attempting bootloop fixes...")
    for i, fix in enumerate(fixes, 1):
        try:
            print(f"   Attempt {i}...")
            fix()
            time.sleep(2)
        except Exception as e:
            print(f"   Failed: {e}")
    
    print("✅ Bootloop fixes applied. Reboot device.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: bootloop_fixer.py <device_id>")
    else:
        fix_bootloop(sys.argv[1])
'''
        )

        print(f"✅ Created recovery tools in {recovery_dir}")

    def create_frp_tools(self):
        """Create embedded FRP bypass tools"""
        frp_dir = self.tools_dir / "frp"
        frp_dir.mkdir(exist_ok=True)

        # Create FRP bypass automation
        frp_tool = frp_dir / "frp_bypass.py"
        frp_tool.write_text(
            '''#!/usr/bin/env python3
"""
FRP Bypass Automation
Automated FRP removal methods
"""
import subprocess

def bypass_frp_adb(device_id):
    """FRP bypass via ADB"""
    commands = [
        # Method 1: Remove FRP lock
        ['adb', '-s', device_id, 'shell', 'rm', '-rf', '/data/system/users/0/accounts.db'],
        
        # Method 2: Disable Google services
        ['adb', '-s', device_id, 'shell', 'pm', 'disable-user', '--user', '0', 'com.google.android.gsf'],
        
        # Method 3: Clear setup wizard
        ['adb', '-s', device_id, 'shell', 'pm', 'clear', 'com.google.android.setupwizard'],
        
        # Method 4: Remove FRP partition file
        ['adb', '-s', device_id, 'shell', 'dd', 'if=/dev/zero', 'of=/dev/block/platform/*/by-name/frp', 'bs=1', 'count=1'],
    ]
    
    print("🔓 Attempting FRP bypass...")
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ {' '.join(cmd[4:6])}")
        except Exception:
            pass
    
    print("✅ FRP bypass attempts completed")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: frp_bypass.py <device_id>")
    else:
        bypass_frp_adb(sys.argv[1])
'''
        )

        print(f"✅ Created FRP tools in {frp_dir}")

    def create_root_tools(self):
        """Create embedded rooting and Magisk tools"""
        root_dir = self.tools_dir / "root"
        root_dir.mkdir(exist_ok=True)

        # Create root checker
        root_checker = root_dir / "root_checker.py"
        root_checker.write_text(
            '''#!/usr/bin/env python3
"""
Root Checker - Comprehensive root detection
"""
import subprocess

def check_root(device_id):
    """Check if device is rooted"""
    checks = {
        'su_binary': ['adb', '-s', device_id, 'shell', 'which', 'su'],
        'su_execute': ['adb', '-s', device_id, 'shell', 'su', '-c', 'id'],
        'magisk': ['adb', '-s', device_id, 'shell', 'which', 'magisk'],
        'supersu': ['adb', '-s', device_id, 'shell', 'pm', 'list', 'packages', 'eu.chainfire.supersu'],
        'root_files': ['adb', '-s', device_id, 'shell', 'ls', '/system/xbin/su'],
    }
    
    results = {}
    for check_name, cmd in checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            results[check_name] = result.returncode == 0 and len(result.stdout) > 0
        except Exception:
            results[check_name] = False
    
    is_rooted = any(results.values())
    
    print(f"📱 Root Status: {'✅ ROOTED' if is_rooted else '❌ NOT ROOTED'}")
    for check, status in results.items():
        print(f"   {check}: {'✅' if status else '❌'}")
    
    return is_rooted

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: root_checker.py <device_id>")
    else:
        check_root(sys.argv[1])
'''
        )

        print(f"✅ Created root tools in {root_dir}")

    def create_all_embedded_tools(self):
        """Create all embedded tools"""
        print("\n🛠️  Creating all embedded tools...")
        self.create_edl_tools()
        self.create_recovery_tools()
        self.create_frp_tools()
        self.create_root_tools()
        print("✅ All embedded tools created")


# Global instance
_embedded_tools = None


def get_embedded_tools() -> EmbeddedToolsManager:
    """Get the global embedded tools manager instance"""
    global _embedded_tools
    if _embedded_tools is None:
        _embedded_tools = EmbeddedToolsManager()
    return _embedded_tools


def setup_embedded_tools():
    """Setup all embedded tools on first run"""
    manager = get_embedded_tools()
    manager.ensure_all_tools()
    manager.create_all_embedded_tools()
    return manager


if __name__ == "__main__":
    # Test the embedded tools
    manager = setup_embedded_tools()
    print("\n🧪 Testing tools...")
    results = manager.test_tools()
    for tool, status in results.items():
        print(f"   {tool}: {'✅' if status else '❌'}")
