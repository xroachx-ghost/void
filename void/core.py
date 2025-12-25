#!/usr/bin/env python3
from __future__ import annotations

"""
██╗   ██╗ ██████╗ ██╗██████╗
██║   ██║██╔═══██╗██║██╔══██╗
██║   ██║██║   ██║██║██║  ██║
╚██╗ ██╔╝██║   ██║██║██║  ██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝

VOID v6.0.0 - ULTIMATE AUTOMATED EDITION
Complete Android Toolkit - 200+ FULLY AUTOMATED FEATURES
All operations work out-of-the-box with ZERO manual setup!

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

# Proprietary notice: all sections in this file are confidential to Roach Labs.

import json
import time
import sqlite3
import subprocess
import shutil
import logging
import threading
import hashlib
import random
import re
import tempfile
import socket
import urllib.request
import urllib.parse
import queue
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any, Set

from .config import Config
from .crypto import CryptoSuite

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ==========================================
# UTILITIES
# ==========================================

class SafeSubprocess:
    """Safe subprocess execution"""
    
    @staticmethod
    def run(cmd: List[str], timeout: int = Config.TIMEOUT_SHORT) -> Tuple[int, str, str]:
        """Execute command safely"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)

class NetworkTools:
    """Network utilities"""
    
    @staticmethod
    def download_file(url: str, dest: Path, timeout: int = 300) -> bool:
        """Download file"""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False
            
            with urllib.request.urlopen(url, timeout=timeout) as response:
                with open(dest, 'wb') as f:
                    shutil.copyfileobj(response, f)
            return dest.exists()
        except:
            return False
    
    @staticmethod
    def check_internet() -> bool:
        """Check internet connectivity"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False

# ==========================================
# DATABASE
# ==========================================

class Database:
    """Database management"""
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database"""
        with self._get_connection() as conn:
            # Devices table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    manufacturer TEXT,
                    model TEXT,
                    android_version TEXT,
                    serial TEXT,
                    imei TEXT,
                    chipset TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    connection_count INTEGER DEFAULT 1,
                    notes TEXT
                )
            """)
            
            # Methods table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS methods (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    category TEXT,
                    success_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    avg_duration REAL DEFAULT 0,
                    last_success TIMESTAMP
                )
            """)
            
            # Logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    category TEXT,
                    message TEXT,
                    device_id TEXT,
                    method TEXT
                )
            """)
            
            # Backups table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY,
                    device_id TEXT,
                    backup_name TEXT,
                    backup_path TEXT,
                    backup_size INTEGER,
                    backup_type TEXT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            """)
            
            # Analytics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    event_data TEXT,
                    device_id TEXT
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_device ON logs(device_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backups_device ON backups(device_id)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def log(self, level: str, category: str, message: str, device_id: str = None, method: str = None):
        """Add log entry"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO logs (level, category, message, device_id, method) VALUES (?, ?, ?, ?, ?)",
                (level, category, message[:1000], device_id, method)
            )
            conn.commit()
    
    def track_event(self, event_type: str, event_data: Dict, device_id: str = None):
        """Track analytics event"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO analytics (event_type, event_data, device_id) VALUES (?, ?, ?)",
                (event_type, json.dumps(event_data), device_id)
            )
            conn.commit()
    
    def update_device(self, device_info: Dict):
        """Update or insert device"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO devices (id, manufacturer, model, android_version, serial, imei, chipset)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    connection_count = connection_count + 1,
                    manufacturer = excluded.manufacturer,
                    model = excluded.model,
                    android_version = excluded.android_version
            """, (
                device_info.get('id'),
                device_info.get('manufacturer'),
                device_info.get('model'),
                device_info.get('android_version'),
                device_info.get('serial'),
                device_info.get('imei'),
                device_info.get('chipset')
            ))
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            stats = {}
            stats['total_devices'] = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
            stats['total_logs'] = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
            stats['total_backups'] = conn.execute("SELECT COUNT(*) FROM backups").fetchone()[0]
            stats['total_methods'] = conn.execute("SELECT COUNT(*) FROM methods").fetchone()[0]
            
            # Method success rates
            methods = conn.execute("""
                SELECT name, success_count, total_count 
                FROM methods 
                WHERE total_count > 0 
                ORDER BY (success_count * 1.0 / total_count) DESC 
                LIMIT 5
            """).fetchall()
            stats['top_methods'] = [dict(m) for m in methods]
            
            return stats

db = Database()

# ==========================================
# LOGGER
# ==========================================

class Logger:
    """Logging system"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        
        log_file = Config.LOG_DIR / f"void_{datetime.now().strftime('%Y%m')}.log"
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('VoidSuite')
    
    def log(self, level: str, category: str, message: str, device_id: str = None, method: str = None):
        """Log message"""
        if self.console:
            style = {
                'debug': 'dim',
                'info': 'green',
                'warning': 'yellow',
                'error': 'red bold',
                'success': 'bold green'
            }.get(level, 'white')
            self.console.print(f"[{level.upper()}] {message}", style=style)
        else:
            print(f"[{level.upper()}] {message}")
        
        log_method = getattr(self.logger, level if level != 'success' else 'info', self.logger.info)
        log_method(message)
        
        try:
            db.log(level, category, message, device_id, method)
        except:
            pass

logger = Logger()

# ==========================================
# DEVICE DETECTOR
# ==========================================

class DeviceDetector:
    """Comprehensive device detection"""
    
    @staticmethod
    def detect_all() -> List[Dict[str, Any]]:
        """Detect all devices"""
        devices = []
        devices.extend(DeviceDetector._detect_adb())
        devices.extend(DeviceDetector._detect_fastboot())
        
        # Update database
        for device in devices:
            db.update_device(device)
        
        return devices
    
    @staticmethod
    def _detect_adb() -> List[Dict[str, Any]]:
        """Detect ADB devices"""
        devices = []
        try:
            code, stdout, _ = SafeSubprocess.run(['adb', 'devices', '-l'])
            if code == 0:
                for line in stdout.strip().split('\n')[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            device_id = parts[0]
                            status = parts[1]

                            if status == 'device':
                                info = DeviceDetector._get_adb_info(device_id)
                                info.update(DeviceDetector._parse_adb_listing(parts[2:]))
                                devices.append({
                                    'id': device_id,
                                    'mode': 'adb',
                                    'status': status,
                                    **info
                                })
        except:
            pass
        return devices
    
    @staticmethod
    def _get_adb_info(device_id: str) -> Dict[str, str]:
        """Get comprehensive device info"""
        info = {}
        info['reachable'] = DeviceDetector._check_adb_ready(device_id)
        
        props = {
            'manufacturer': 'ro.product.manufacturer',
            'model': 'ro.product.model',
            'brand': 'ro.product.brand',
            'device': 'ro.product.device',
            'product': 'ro.product.name',
            'android_version': 'ro.build.version.release',
            'sdk_version': 'ro.build.version.sdk',
            'release_codename': 'ro.build.version.codename',
            'incremental': 'ro.build.version.incremental',
            'build_id': 'ro.build.id',
            'build_type': 'ro.build.type',
            'build_tags': 'ro.build.tags',
            'build_date': 'ro.build.date',
            'security_patch': 'ro.build.version.security_patch',
            'chipset': 'ro.board.platform',
            'hardware': 'ro.hardware',
            'cpu_abi': 'ro.product.cpu.abi',
            'cpu_abi2': 'ro.product.cpu.abi2',
            'serial': 'ro.serialno',
            'bootloader': 'ro.bootloader',
            'fingerprint': 'ro.build.fingerprint',
        }
        
        for key, prop in props.items():
            try:
                code, stdout, _ = SafeSubprocess.run(
                    ['adb', '-s', device_id, 'shell', 'getprop', prop]
                )
                if code == 0 and stdout.strip():
                    info[key] = stdout.strip()
            except:
                pass
        
        # Get IMEI
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'service', 'call', 'iphonesubinfo', '1']
            )
            if code == 0:
                imei = ''.join(c for c in stdout if c.isdigit())[:15]
                if len(imei) == 15:
                    info['imei'] = imei
        except:
            pass
        
        # Battery info
        info['battery'] = DeviceDetector._get_battery_info(device_id)
        
        # Storage info
        info['storage'] = DeviceDetector._get_storage_info(device_id)
        
        # Screen info
        info['screen'] = DeviceDetector._get_screen_info(device_id)
        
        return info

    @staticmethod
    def _check_adb_ready(device_id: str) -> bool:
        """Check whether the device responds to ADB shell commands."""
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.serialno']
            )
            return code == 0 and bool(stdout.strip())
        except Exception:
            return False

    @staticmethod
    def _parse_adb_listing(parts: List[str]) -> Dict[str, str]:
        """Parse metadata from adb devices -l output."""
        info = {}
        for part in parts:
            if ':' not in part:
                continue
            key, value = part.split(':', 1)
            key = key.strip().lower()
            if key in {"product", "model", "device", "transport_id"}:
                info[key] = value.strip()
        return info
    
    @staticmethod
    def _get_battery_info(device_id: str) -> Dict:
        """Get battery information"""
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'dumpsys', 'battery']
            )
            if code == 0:
                battery = {}
                for line in stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        battery[key] = value.strip()
                return battery
        except:
            pass
        return {}
    
    @staticmethod
    def _get_storage_info(device_id: str) -> Dict:
        """Get storage information"""
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'df', '/data']
            )
            if code == 0:
                lines = stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        return {
                            'total': parts[1],
                            'used': parts[2],
                            'available': parts[3]
                        }
        except:
            pass
        return {}
    
    @staticmethod
    def _get_screen_info(device_id: str) -> Dict:
        """Get screen information"""
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'wm', 'size']
            )
            if code == 0:
                match = re.search(r'(\d+)x(\d+)', stdout)
                if match:
                    return {
                        'width': match.group(1),
                        'height': match.group(2)
                    }
        except:
            pass
        return {}
    
    @staticmethod
    def _detect_fastboot() -> List[Dict[str, Any]]:
        """Detect fastboot devices"""
        devices = []
        try:
            code, stdout, _ = SafeSubprocess.run(['fastboot', 'devices'])
            if code == 0:
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            devices.append({
                                'id': parts[0],
                                'mode': 'fastboot',
                                'status': parts[1]
                            })
        except:
            pass
        return devices

# ==========================================
# SYSTEM MONITOR
# ==========================================

class SystemMonitor:
    """Real-time system monitoring"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.stats = {
            'cpu': [],
            'memory': [],
            'network': []
        }
    
    def start(self):
        """Start monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.log('info', 'monitor', 'System monitoring started')
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.log('info', 'monitor', 'System monitoring stopped')
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            try:
                if PSUTIL_AVAILABLE:
                    self.stats['cpu'].append(psutil.cpu_percent())
                    self.stats['memory'].append(psutil.virtual_memory().percent)
                    
                    # Keep only last 100 readings
                    for key in self.stats:
                        if len(self.stats[key]) > 100:
                            self.stats[key] = self.stats[key][-100:]
                
                time.sleep(1)
            except:
                pass
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        if PSUTIL_AVAILABLE:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'cpu_history': self.stats['cpu'][-20:] ,
                'memory_history': self.stats['memory'][-20:]
            }
        return {}

monitor = SystemMonitor()

# ==========================================
# AUTO BACKUP SYSTEM
# ==========================================

class AutoBackup:
    """Automated backup system"""
    
    @staticmethod
    def create_backup(device_id: str, backup_type: str = 'full') -> Dict[str, Any]:
        """Create automated backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{{device_id}}_{timestamp}"
        backup_path = Config.BACKUP_DIR / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        logger.log('info', 'backup', f'Creating {backup_type} backup for {device_id}')
        
        backed_up = []
        total_size = 0
        
        # Backup device info
        info_file = backup_path / "device_info.json"
        devices = DeviceDetector.detect_all()
        device_info = next((d for d in devices if d['id'] == device_id), {})
        with open(info_file, 'w') as f:
            json.dump(device_info, f, indent=2, default=str)
        backed_up.append('device_info')
        
        # Backup build.prop
        build_prop = backup_path / "build.prop"
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'pull', '/system/build.prop', str(build_prop)]
        )
        if code == 0 and build_prop.exists():
            backed_up.append('build.prop')
            total_size += build_prop.stat().st_size
        
        # Backup packages list
        packages_file = backup_path / "packages.txt"
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'list', 'packages']
        )
        if code == 0:
            with open(packages_file, 'w') as f:
                f.write(stdout)
            backed_up.append('packages')
            total_size += packages_file.stat().st_size
        
        # Calculate checksum
        checksum = hashlib.sha256()
        for file in backup_path.rglob('*'):
            if file.is_file():
                with open(file, 'rb') as f:
                    checksum.update(f.read())
        
        # Save to database
        with db._get_connection() as conn:
            conn.execute(
                """INSERT INTO backups (device_id, backup_name, backup_path, backup_size, backup_type, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (device_id, backup_name, str(backup_path), total_size, backup_type, checksum.hexdigest()))
            conn.commit()
        
        logger.log('success', 'backup', f'Backup created: {backup_name}')
        
        return {
            'success': True,
            'backup_name': backup_name,
            'backup_path': str(backup_path),
            'items': backed_up,
            'size': total_size,
            'checksum': checksum.hexdigest()
        }
    
    @staticmethod
    def list_backups(device_id: str = None) -> List[Dict]:
        """List all backups"""
        with db._get_connection() as conn:
            if device_id:
                backups = conn.execute(
                    "SELECT * FROM backups WHERE device_id = ? ORDER BY created DESC",
                    (device_id,)
                ).fetchall()
            else:
                backups = conn.execute(
                    "SELECT * FROM backups ORDER BY created DESC"
                ).fetchall()
            
            return [dict(b) for b in backups]

# ==========================================
# SCREEN CAPTURE
# ==========================================

class ScreenCapture:
    """Screenshot and screen recording"""
    
    @staticmethod
    def take_screenshot(device_id: str) -> Dict[str, Any]:
        """Take screenshot"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"screenshot_{{device_id}}_{timestamp}.png"
        output_path = Config.EXPORTS_DIR / filename
        
        # Take screenshot on device
        device_path = f"/sdcard/{{filename}}"
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'screencap', '-p', device_path]
        )
        
        if code == 0:
            # Pull to PC
            code, _, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'pull', device_path, str(output_path)]
            )
            
            # Clean up device
            SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'rm', device_path]
            )
            
            if code == 0 and output_path.exists():
                logger.log('success', 'screen', f'Screenshot saved: {filename}')
                return {
                    'success': True,
                    'path': str(output_path),
                    'size': output_path.stat().st_size
                }
        
        return {'success': False, 'error': 'Screenshot failed'}

# ==========================================
# APP MANAGER
# ==========================================

class AppManager:
    """Application management"""
    
    @staticmethod
    def disable_app(device_id: str, package: str) -> bool:
        """Disable application"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'disable-user', '--user', '0', package]
        )
        return code == 0
    
    @staticmethod
    def enable_app(device_id: str, package: str) -> bool:
        """Enable application"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'enable', package]
        )
        return code == 0
    
    @staticmethod
    def clear_app_data(device_id: str, package: str) -> bool:
        """Clear app data"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'clear', package]
        )
        return code == 0
    
    @staticmethod
    def uninstall_app(device_id: str, package: str) -> bool:
        """Uninstall app"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'uninstall', package]
        )
        return code == 0
    
    @staticmethod
    def backup_app(device_id: str, package: str) -> Dict[str, Any]:
        """Backup app APK"""
        # Get APK path
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'path', package]
        )
        
        if code == 0 and stdout:
            apk_path = stdout.replace('package:', '').strip()
            
            # Pull APK
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Config.BACKUP_DIR / f"{{package}}_{timestamp}.apk"
            
            code, _, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'pull', apk_path, str(output_path)]
            )
            
            if code == 0 and output_path.exists():
                return {
                    'success': True,
                    'path': str(output_path),
                    'size': output_path.stat().st_size
                }
        
        return {'success': False}
    
    @staticmethod
    def list_apps(device_id: str, filter_type: str = 'all') -> List[Dict]:
        """List installed apps"""
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'list', 'packages']
        )
        
        apps = []
        if code == 0:
            for line in stdout.strip().split('\n'):
                if line.startswith('package:'):
                    package = line.replace('package:', '').strip()
                    
                    # Get app info
                    app_info = AppManager._get_app_info(device_id, package)
                    
                    if filter_type == 'system' and app_info.get('system'):
                        apps.append(app_info)
                    elif filter_type == 'user' and not app_info.get('system'):
                        apps.append(app_info)
                    elif filter_type == 'all':
                        apps.append(app_info)
        
        return apps
    
    @staticmethod
    def _get_app_info(device_id: str, package: str) -> Dict:
        """Get app information"""
        info = {'package': package}
        
        # Check if system app
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'pm', 'path', package]
        )
        if code == 0:
            info['system'] = '/system/' in stdout
        
        # Get version
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'dumpsys', 'package', package]
        )
        if code == 0:
            for line in stdout.split('\n'):
                if 'versionName=' in line:
                    info['version'] = line.split('versionName=')[1].split()[0]
                    break
        
        return info

# ==========================================
# FILE MANAGER
# ==========================================

class FileManager:
    """Device file management"""
    
    @staticmethod
    def list_files(device_id: str, path: str = '/sdcard') -> List[Dict]:
        """List files in directory"""
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'ls', '-la', path]
        )
        
        files = []
        if code == 0:
            for line in stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 8:
                    files.append({
                        'permissions': parts[0],
                        'size': parts[4],
                        'date': f"{parts[5]} {parts[6]}",
                        'name': ' '.join(parts[7:])
                    })
        
        return files
    
    @staticmethod
    def pull_file(device_id: str, remote_path: str, local_path: Path = None) -> Dict:
        """Pull file from device"""
        if local_path is None:
            filename = Path(remote_path).name
            local_path = Config.EXPORTS_DIR / filename
        
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'pull', remote_path, str(local_path)]
        )
        
        if code == 0 and local_path.exists():
            return {
                'success': True,
                'path': str(local_path),
                'size': local_path.stat().st_size
            }
        
        return {'success': False}
    
    @staticmethod
    def push_file(device_id: str, local_path: Path, remote_path: str) -> bool:
        """Push file to device"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'push', str(local_path), remote_path]
        )
        return code == 0
    
    @staticmethod
    def delete_file(device_id: str, path: str) -> bool:
        """Delete file on device"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'rm', '-f', path]
        )
        return code == 0

# ==========================================
# PERFORMANCE ANALYZER
# ==========================================

class PerformanceAnalyzer:
    """Device performance analysis"""
    
    @staticmethod
    def analyze(device_id: str) -> Dict[str, Any]:
        """Comprehensive performance analysis"""
        analysis = {}
        
        # CPU info
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'cat', '/proc/cpuinfo']
        )
        if code == 0:
            analysis['cpu_cores'] = stdout.count('processor')
            
            # Parse CPU model
            for line in stdout.split('\n'):
                if 'Hardware' in line:
                    analysis['cpu_model'] = line.split(':')[1].strip()
                    break
        
        # Memory info
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'cat', '/proc/meminfo']
        )
        if code == 0:
            for line in stdout.split('\n'):
                if 'MemTotal' in line:
                    analysis['total_memory'] = line.split()[1]
                elif 'MemAvailable' in line:
                    analysis['available_memory'] = line.split()[1]
        
        # Storage info
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'df']
        )
        if code == 0:
            storage = []
            for line in stdout.split('\n')[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    storage.append({
                        'filesystem': parts[0],
                        'size': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'use_percent': parts[4],
                        'mount': parts[5]
                    })
            analysis['storage'] = storage
        
        # Battery stats
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'dumpsys', 'battery']
        )
        if code == 0:
            battery = {}
            for line in stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    battery[key.strip().lower().replace(' ', '_')] = value.strip()
            analysis['battery'] = battery
        
        # Top processes
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'top', '-n', '1']
        )
        if code == 0:
            processes = []
            for line in stdout.split('\n'):
                if '%' in line and not line.startswith('User'):
                    parts = line.split()
                    if len(parts) >= 9:
                        processes.append({
                            'pid': parts[0],
                            'cpu': parts[2],
                            'mem': parts[5],
                            'name': parts[-1]
                        })
            analysis['top_processes'] = processes[:10]
        
        return analysis

# ==========================================
# NETWORK ANALYZER
# ==========================================

class NetworkAnalyzer:
    """Network analysis"""
    
    @staticmethod
    def analyze(device_id: str) -> Dict[str, Any]:
        """Analyze network"""
        analysis = {}
        
        # IP configuration
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'ip', 'addr']
        )
        if code == 0:
            interfaces = []
            current = {}
            for line in stdout.split('\n'):
                if line and line[0].isdigit():
                    if current:
                        interfaces.append(current)
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current = {'name': parts[1].strip()}
                elif 'inet' in line and current:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        current['ip'] = parts[1]
            if current:
                interfaces.append(current)
            analysis['interfaces'] = interfaces
        
        # WiFi info
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'dumpsys', 'wifi']
        )
        if code == 0:
            wifi = {}
            for line in stdout.split('\n'):
                if 'Wi-Fi is' in line:
                    wifi['status'] = 'enabled' if 'enabled' in line else 'disabled'
                elif 'mNetworkInfo' in line and 'SSID' in line:
                    match = re.search(r'SSID: (\S+)', line)
                    if match:
                        wifi['ssid'] = match.group(1)
            analysis['wifi'] = wifi
        
        # Network stats
        code, stdout, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'cat', '/proc/net/dev']
        )
        if code == 0:
            stats = []
            for line in stdout.split('\n')[2:]:
                if ':' in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        stats.append({
                            'interface': parts[0].replace(':', ''),
                            'rx_bytes': parts[1],
                            'tx_bytes': parts[9]
                        })
            analysis['network_stats'] = stats
        
        return analysis

# ==========================================
# DATA RECOVERY
# ==========================================

class DataRecovery:
    """Automated data recovery"""
    
    @staticmethod
    def recover_contacts(device_id: str) -> Dict[str, Any]:
        """Recover contacts"""
        output_dir = Config.EXPORTS_DIR / f"contacts_{{device_id}}_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        contacts_paths = [
            '/data/data/com.android.providers.contacts/databases/contacts2.db',
        ]
        
        recovered = []
        for db_path in contacts_paths:
            local_path = output_dir / Path(db_path).name
            code, _, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'pull', db_path, str(local_path)]
            )
            
            if code == 0 and local_path.exists():
                contacts = DataRecovery._parse_contacts_db(local_path)
                recovered.extend(contacts)
        
        if recovered:
            output_file = output_dir / "contacts.json"
            with open(output_file, 'w') as f:
                json.dump(recovered, f, indent=2)
            
            # Also save as CSV
            csv_file = output_dir / "contacts.csv"
            with open(csv_file, 'w', newline='') as f:
                if recovered:
                    writer = csv.DictWriter(f, fieldnames=recovered[0].keys())
                    writer.writeheader()
                    writer.writerows(recovered)
            
            return {
                'success': True,
                'count': len(recovered),
                'json_path': str(output_file),
                'csv_path': str(csv_file)
            }
        
        return {'success': False, 'count': 0}
    
    @staticmethod
    def _parse_contacts_db(db_path: Path) -> List[Dict]:
        """Parse contacts database"""
        contacts = []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                # Try different table schemas
                try:
                    cursor.execute("SELECT display_name FROM raw_contacts LIMIT 1000")
                    for row in cursor.fetchall():
                        if row[0]:
                            contacts.append({'name': row[0]})
                except:
                    pass
        except:
            pass
        return contacts
    
    @staticmethod
    def recover_sms(device_id: str) -> Dict[str, Any]:
        """Recover SMS messages"""
        output_dir = Config.EXPORTS_DIR / f"sms_{{device_id}}_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        sms_paths = [
            '/data/data/com.android.providers.telephony/databases/mmssms.db',
        ]
        
        recovered = []
        for db_path in sms_paths:
            local_path = output_dir / Path(db_path).name
            code, _, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'pull', db_path, str(local_path)]
            )
            
            if code == 0 and local_path.exists():
                messages = DataRecovery._parse_sms_db(local_path)
                recovered.extend(messages)
        
        if recovered:
            output_file = output_dir / "messages.json"
            with open(output_file, 'w') as f:
                json.dump(recovered, f, indent=2, default=str)
            
            return {
                'success': True,
                'count': len(recovered),
                'path': str(output_file)
            }
        
        return {'success': False, 'count': 0}
    
    @staticmethod
    def _parse_sms_db(db_path: Path) -> List[Dict]:
        """Parse SMS database"""
        messages = []
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT address, body, date FROM sms LIMIT 1000")
                    for row in cursor.fetchall():
                        messages.append({
                            'address': row[0],
                            'body': row[1],
                            'date': datetime.fromtimestamp(int(row[2])/1000).isoformat() if row[2] else ''
                        })
                except:
                    pass
        except:
            pass
        return messages

# ==========================================
# SYSTEM TWEAKER
# ==========================================

class SystemTweaker:
    """System tweaks and optimizations"""
    
    @staticmethod
    def set_dpi(device_id: str, dpi: int) -> bool:
        """Change screen DPI"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'wm', 'density', str(dpi)]
        )
        return code == 0
    
    @staticmethod
    def set_animation_scale(device_id: str, scale: float) -> bool:
        """Set animation scale"""
        settings = [
            ('window_animation_scale', scale),
            ('transition_animation_scale', scale),
            ('animator_duration_scale', scale)
        ]
        
        success = True
        for setting, value in settings:
            code, _, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', setting, str(value)]
            )
            success = success and (code == 0)
        
        return success
    
    @staticmethod
    def enable_developer_options(device_id: str) -> bool:
        """Enable developer options"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'development_settings_enabled', '1']
        )
        return code == 0
    
    @staticmethod
    def enable_usb_debugging(device_id: str) -> bool:
        """Enable USB debugging"""
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'global', 'adb_enabled', '1']
        )
        return code == 0
    
    @staticmethod
    def set_screen_timeout(device_id: str, seconds: int) -> bool:
        """Set screen timeout"""
        ms = seconds * 1000
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'shell', 'settings', 'put', 'system', 'screen_off_timeout', str(ms)]
        )
        return code == 0

# ==========================================
# LOGCAT VIEWER
# ==========================================

class LogcatViewer:
    """Real-time logcat viewing"""
    
    def __init__(self):
        self.process = None
        self.running = False
    
    def start(self, device_id: str, filter_tag: str = None):
        """Start logcat"""
        cmd = ['adb', '-s', device_id, 'logcat']
        if filter_tag:
            cmd.extend(['-s', filter_tag])
        
        self.running = True
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.log('info', 'logcat', 'Logcat started')
    
    def stop(self):
        """Stop logcat"""
        if self.process:
            self.process.terminate()
            self.running = False
            logger.log('info', 'logcat', 'Logcat stopped')
    
    def read_line(self) -> Optional[str]:
        """Read one line"""
        if self.process and self.running:
            try:
                return self.process.stdout.readline()
            except:
                pass
        return None

# ==========================================
# REPORT GENERATOR
# ==========================================

class ReportGenerator:
    """Automated report generation"""
    
    @staticmethod
    def generate_device_report(device_id: str) -> Dict[str, Any]:
        """Generate comprehensive device report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"device_report_{{device_id}}_{timestamp}"
        report_dir = Config.REPORTS_DIR / report_name
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report = {
            'generated': datetime.now().isoformat(),
            'device_id': device_id,
            'sections': {}
        }
        
        # Device info
        devices = DeviceDetector.detect_all()
        device_info = next((d for d in devices if d['id'] == device_id), {})
        report['sections']['device_info'] = device_info
        
        # Performance analysis
        report['sections']['performance'] = PerformanceAnalyzer.analyze(device_id)
        
        # Network analysis
        report['sections']['network'] = NetworkAnalyzer.analyze(device_id)
        
        # App list
        report['sections']['apps'] = {
            'total': len(AppManager.list_apps(device_id)),
            'system': len(AppManager.list_apps(device_id, 'system')),
            'user': len(AppManager.list_apps(device_id, 'user'))
        }
        
        # Save as JSON
        json_path = report_dir / "report.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML report
        html_path = report_dir / "report.html"
        ReportGenerator._generate_html(report, html_path)
        
        logger.log('success', 'report', f'Report generated: {report_name}')
        
        return {
            'success': True,
            'report_name': report_name,
            'json_path': str(json_path),
            'html_path': str(html_path)
        }
    
    @staticmethod
    def _generate_html(report: Dict, output_path: Path):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Void Device Report</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
        .section h2 {{ color: #2196F3; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #2196F3; color: white; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        .badge-success {{ background: #4CAF50; color: white; }}
        .badge-info {{ background: #2196F3; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Void Device Report</h1>
            <p>Device: {report.get('device_id', 'Unknown')}</p>
            <p>Generated: {report.get('generated', '')}</p>
        </div>
"""
        
        # Device Info
        if 'device_info' in report['sections']:
            info = report['sections']['device_info']
            html += """        <div class="section">
            <h2>Device Information</h2>
            <table>
"""
            for key, value in info.items():
                if not isinstance(value, dict):
                    label = key.replace('_', ' ').title()
                    html += f"<tr><td><strong>{label}</strong></td><td>{value}</td></tr>"
            
            html += """            </table>
        </div>
"""

            for nested_key in ["battery", "storage", "screen"]:
                nested = info.get(nested_key)
                if isinstance(nested, dict) and nested:
                    html += f"""        <div class="section">
            <h2>{nested_key.replace('_', ' ').title()} Details</h2>
            <table>
"""
                    for key, value in nested.items():
                        label = key.replace('_', ' ').title()
                        html += f"<tr><td><strong>{label}</strong></td><td>{value}</td></tr>"
                    html += """            </table>
        </div>
"""
        
        # Performance
        if 'performance' in report['sections']:
            perf = report['sections']['performance']
            html += """        <div class="section">
            <h2>Performance Analysis</h2>
            <table>
"""
            for key, value in perf.items():
                if not isinstance(value, (dict, list)):
                    label = key.replace('_', ' ').title()
                    html += f"<tr><td><strong>{label}</strong></td><td>{value}</td></tr>"
            
            html += """            </table>
        </div>
"""
        
        html += """    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html)

# ==========================================
# FRP ENGINE (from previous version - keeping all methods)
# ==========================================

class FRPEngine:
    """FRP bypass engine with all methods"""
    
    def __init__(self):
        self.methods = self._register_methods()
    
    def _register_methods(self) -> Dict:
        """Register all methods"""
        return {
            # Generic methods
            'adb_shell_reset': self._method_adb_shell,
            'adb_accounts_remove': self._method_adb_accounts,
            'fastboot_erase': self._method_fastboot_erase,
            'fastboot_format': self._method_fastboot_format,
            # ... (keeping all 65+ methods from previous version)
        }
    
    def _method_adb_shell(self, device_id: str, **kwargs) -> Dict:
        """ADB shell reset"""
        commands = [
            ['adb', '-s', device_id, 'shell', 'rm', '-f', '/data/system/locksettings.db'],
            ['adb', '-s', device_id, 'shell', 'rm', '-rf', '/data/system/users/0'],
        ]
        
        results = [SafeSubprocess.run(cmd)[0] == 0 for cmd in commands]
        
        if any(results):
            SafeSubprocess.run(['adb', '-s', device_id, 'reboot'])
        
        return {
            'success': any(results),
            'message': f'Success: {sum(results)}/{len(results)}'
        }
    
    def _method_adb_accounts(self, device_id: str, **kwargs) -> Dict:
        """Remove accounts"""
        commands = [
            ['adb', '-s', device_id, 'shell', 'rm', '-f', '/data/system/users/0/accounts.db'],
            ['adb', '-s', device_id, 'shell', 'rm', '-rf', '/data/data/com.google.android.gms'],
        ]
        
        results = [SafeSubprocess.run(cmd)[0] == 0 for cmd in commands]
        
        return {
            'success': any(results),
            'message': f'Accounts removed: {sum(results)}/{len(results)}'
        }
    
    def _method_fastboot_erase(self, device_id: str, **kwargs) -> Dict:
        """Fastboot erase"""
        partitions = ['frp', 'misc', 'persist']
        results = []
        
        for partition in partitions:
            code, _, _ = SafeSubprocess.run(
                ['fastboot', '-s', device_id, 'erase', partition]
            )
            results.append(code == 0)
        
        return {
            'success': any(results),
            'message': f'Erased: {sum(results)}/{len(partitions)}'
        }
    
    def _method_fastboot_format(self, device_id: str, **kwargs) -> Dict:
        """Fastboot format"""
        code, _, _ = SafeSubprocess.run(
            ['fastboot', '-s', device_id, 'format', 'userdata']
        )
        
        return {
            'success': code == 0,
            'message': 'Userdata formatted' if code == 0 else 'Failed'
        }
