"""
VOID Auto-Update System

Checks for and downloads software updates.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class UpdateManager:
    """
    Manages software updates for Void Suite.
    
    Features:
    - Check for updates on startup
    - Download and verify updates
    - Display changelog
    - Rollback capability
    - Version comparison
    """
    
    CONFIG_FILE = Path.home() / ".void" / "update.json"
    UPDATE_CHECK_URL = "https://api.roach-labs.com/void/updates/check"
    GITHUB_RELEASES_URL = "https://api.github.com/repos/xroachx-ghost/void/releases/latest"
    
    def __init__(self):
        """Initialize update manager"""
        self.config_file = self.CONFIG_FILE
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.current_version = self._get_current_version()
    
    def _load_config(self) -> Dict:
        """Load update configuration"""
        if not self.config_file.exists():
            default_config = {
                "auto_check": True,
                "last_check": None,
                "check_interval_days": 1,
                "skip_version": None,
                "update_channel": "stable",  # stable, beta, dev
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"auto_check": True}
    
    def _save_config(self, config: Dict):
        """Save update configuration"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save update config: {e}")
    
    def _get_current_version(self) -> str:
        """Get current Void Suite version"""
        try:
            # Try to import version from package
            from . import __version__
            return __version__
        except Exception:
            # Fallback: try to read from pyproject.toml
            try:
                import toml
                pyproject = Path(__file__).parent.parent / "pyproject.toml"
                if pyproject.exists():
                    data = toml.load(pyproject)
                    return data["project"]["version"]
            except Exception:
                pass
            
            return "unknown"
    
    def should_check_for_updates(self) -> bool:
        """Check if we should check for updates"""
        if not self.config.get("auto_check", True):
            return False
        
        last_check = self.config.get("last_check")
        if not last_check:
            return True
        
        # Check interval
        interval_days = self.config.get("check_interval_days", 1)
        last_check_date = datetime.fromisoformat(last_check)
        
        return datetime.now() - last_check_date > timedelta(days=interval_days)
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        Check if updates are available.
        
        Returns:
            Dict with update info if available, None otherwise
        """
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            # Update last check time
            self.config["last_check"] = datetime.now().isoformat()
            self._save_config(self.config)
            
            # Check for updates
            response = requests.get(
                self.GITHUB_RELEASES_URL,
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            response.raise_for_status()
            
            release_data = response.json()
            
            # Extract version info
            latest_version = release_data["tag_name"].lstrip("v")
            
            # Compare versions
            if self._is_newer_version(latest_version, self.current_version):
                # Check if user skipped this version
                if latest_version == self.config.get("skip_version"):
                    return None
                
                return {
                    "version": latest_version,
                    "current_version": self.current_version,
                    "release_date": release_data["published_at"],
                    "changelog": release_data["body"],
                    "download_url": self._get_download_url(release_data),
                    "release_url": release_data["html_url"],
                }
            
            return None
        
        except Exception as e:
            print(f"Failed to check for updates: {e}")
            return None
    
    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """
        Compare version strings.
        
        Args:
            new_version: New version string (e.g., "6.1.0")
            current_version: Current version string
            
        Returns:
            True if new_version is newer
        """
        try:
            # Parse versions
            new_parts = [int(x) for x in new_version.split(".")]
            current_parts = [int(x) for x in current_version.split(".")]
            
            # Pad to same length
            max_len = max(len(new_parts), len(current_parts))
            new_parts += [0] * (max_len - len(new_parts))
            current_parts += [0] * (max_len - len(current_parts))
            
            # Compare
            return new_parts > current_parts
        
        except Exception:
            # If parsing fails, assume not newer
            return False
    
    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Get appropriate download URL for current platform"""
        import platform
        
        system = platform.system().lower()
        assets = release_data.get("assets", [])
        
        # Platform-specific package names
        patterns = {
            "linux": ["linux", ".deb", ".rpm", ".tar.gz"],
            "darwin": ["macos", "darwin", ".dmg", ".pkg"],
            "windows": ["windows", "win", ".exe", ".msi"],
        }
        
        # Find matching asset
        for asset in assets:
            name = asset["name"].lower()
            if system in patterns:
                if any(pattern in name for pattern in patterns[system]):
                    return asset["browser_download_url"]
        
        # Fallback to source tarball
        return release_data.get("tarball_url")
    
    def download_update(self, update_info: Dict, destination: Path = None) -> Optional[Path]:
        """
        Download update package.
        
        Args:
            update_info: Update information from check_for_updates()
            destination: Where to save download
            
        Returns:
            Path to downloaded file, or None on failure
        """
        if not REQUESTS_AVAILABLE:
            print("Error: requests library required for downloads")
            return None
        
        download_url = update_info.get("download_url")
        if not download_url:
            print("Error: No download URL available")
            return None
        
        try:
            # Determine destination
            if destination is None:
                temp_dir = Path(tempfile.mkdtemp(prefix="void_update_"))
                filename = download_url.split("/")[-1]
                destination = temp_dir / filename
            
            print(f"Downloading update from {download_url}...")
            
            # Download with progress
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rDownloading: {progress:.1f}%", end="")
            
            print("\n✓ Download complete")
            return destination
        
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    def verify_download(self, file_path: Path, expected_checksum: str = None) -> bool:
        """
        Verify downloaded file integrity.
        
        Args:
            file_path: Path to downloaded file
            expected_checksum: Expected SHA256 checksum
            
        Returns:
            True if verification successful
        """
        if not file_path.exists():
            return False
        
        if expected_checksum is None:
            # No checksum to verify against
            print("Warning: No checksum provided for verification")
            return True
        
        try:
            # Calculate SHA256
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            
            actual_checksum = sha256.hexdigest()
            
            if actual_checksum == expected_checksum:
                print("✓ Checksum verified")
                return True
            else:
                print("✗ Checksum mismatch!")
                print(f"  Expected: {expected_checksum}")
                print(f"  Actual:   {actual_checksum}")
                return False
        
        except Exception as e:
            print(f"Verification failed: {e}")
            return False
    
    def install_update(self, update_file: Path) -> bool:
        """
        Install downloaded update.
        
        Args:
            update_file: Path to update package
            
        Returns:
            True if installation successful
        """
        try:
            print(f"Installing update from {update_file}...")
            
            # Backup current installation
            backup_dir = self._create_backup()
            if backup_dir:
                print(f"✓ Backup created at {backup_dir}")
            
            # Install based on file type
            if update_file.suffix == ".whl" or update_file.suffix == ".tar.gz":
                # Python package
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", str(update_file)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✓ Update installed successfully")
                    return True
                else:
                    print(f"✗ Installation failed: {result.stderr}")
                    return False
            
            elif update_file.suffix in [".exe", ".msi", ".deb", ".rpm", ".pkg", ".dmg"]:
                # Platform-specific installer
                print("Please run the installer manually:")
                print(f"  {update_file}")
                return False
            
            else:
                print(f"Unsupported update format: {update_file.suffix}")
                return False
        
        except Exception as e:
            print(f"Installation failed: {e}")
            return False
    
    def _create_backup(self) -> Optional[Path]:
        """Create backup of current installation"""
        try:
            backup_dir = Path.home() / ".void" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"void_{self.current_version}_{timestamp}"
            
            # Get package location
            import void
            package_path = Path(void.__file__).parent
            
            # Copy package
            shutil.copytree(package_path, backup_path)
            
            return backup_path
        
        except Exception as e:
            print(f"Warning: Backup failed: {e}")
            return None
    
    def rollback(self, backup_dir: Path) -> bool:
        """
        Rollback to a previous version.
        
        Args:
            backup_dir: Path to backup directory
            
        Returns:
            True if rollback successful
        """
        try:
            import void
            package_path = Path(void.__file__).parent
            
            # Remove current installation
            shutil.rmtree(package_path)
            
            # Restore from backup
            shutil.copytree(backup_dir, package_path)
            
            print("✓ Rollback successful")
            return True
        
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False
    
    def skip_version(self, version: str):
        """Skip a specific version"""
        self.config["skip_version"] = version
        self._save_config(self.config)
        print(f"Version {version} will be skipped")
    
    def enable_auto_check(self):
        """Enable automatic update checks"""
        self.config["auto_check"] = True
        self._save_config(self.config)
    
    def disable_auto_check(self):
        """Disable automatic update checks"""
        self.config["auto_check"] = False
        self._save_config(self.config)


def prompt_update_cli(update_info: Dict):
    """Prompt user to update via CLI"""
    print("\n" + "=" * 70)
    print("🎉 Update Available!")
    print("=" * 70)
    print(f"Current version: {update_info['current_version']}")
    print(f"Latest version:  {update_info['version']}")
    print(f"Released: {update_info['release_date'][:10]}")
    print("\nWhat's new:")
    print("-" * 70)
    
    # Display changelog (first 10 lines)
    changelog_lines = update_info["changelog"].split("\n")[:10]
    for line in changelog_lines:
        print(line)
    
    if len(update_info["changelog"].split("\n")) > 10:
        print("... (see full changelog at release URL)")
    
    print("-" * 70)
    print(f"\nRelease URL: {update_info['release_url']}")
    print("=" * 70 + "\n")
    
    try:
        response = input("Would you like to update now? [Y/n]: ").strip().lower()
        
        if response in ["", "y", "yes"]:
            manager = UpdateManager()
            
            # Download
            update_file = manager.download_update(update_info)
            if not update_file:
                print("✗ Download failed")
                return
            
            # Install
            if manager.install_update(update_file):
                print("\n✓ Update installed! Please restart Void Suite.")
            else:
                print("\n✗ Installation failed. Please update manually.")
        
        elif response in ["s", "skip"]:
            manager = UpdateManager()
            manager.skip_version(update_info["version"])
        
        else:
            print("Update skipped. You can update later with: void update")
    
    except (EOFError, KeyboardInterrupt):
        print("\nUpdate cancelled.")
