from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..config import Config
from .database import db
from .device import DeviceDetector
from .logging import logger
from .utils import SafeSubprocess


class AutoBackup:
    """Automated backup system"""

    @staticmethod
    def _sanitize_device_id(device_id: str) -> str:
        safe_id = re.sub(r'[^A-Za-z0-9]+', '_', device_id).strip('_')
        return safe_id or "unknown"

    @staticmethod
    def create_backup(
        device_id: str,
        backup_type: str = 'full',
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Create automated backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_device_id = AutoBackup._sanitize_device_id(device_id)
        backup_name = f"backup_{safe_device_id}_{timestamp}"
        backup_path = Config.BACKUP_DIR / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        if progress_callback:
            progress_callback("Collecting device info...")

        logger.log('info', 'backup', f'Creating {backup_type} backup for {device_id}')

        backed_up = []
        total_size = 0

        # Backup device info
        info_file = backup_path / "device_info.json"
        devices, _ = DeviceDetector.detect_all()
        device_info = next((d for d in devices if d.get('id') == device_id), {})
        if not device_info:
            logger.log(
                'warning',
                'backup',
                f'Device metadata could not be resolved for {device_id}.',
                device_id=device_id,
            )
        with open(info_file, 'w') as f:
            json.dump(device_info, f, indent=2, default=str)
        backed_up.append('device_info')

        # Backup build.prop
        if progress_callback:
            progress_callback("Pulling build.prop...")
        build_prop = backup_path / "build.prop"
        code, _, _ = SafeSubprocess.run(
            ['adb', '-s', device_id, 'pull', '/system/build.prop', str(build_prop)]
        )
        if code == 0 and build_prop.exists():
            backed_up.append('build.prop')
            total_size += build_prop.stat().st_size

        # Backup packages list
        if progress_callback:
            progress_callback("Listing installed packages...")
        packages_file = backup_path / "packages.txt"
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'pm', 'list', 'packages'])
        if code == 0:
            with open(packages_file, 'w') as f:
                f.write(stdout)
            backed_up.append('packages')
            total_size += packages_file.stat().st_size

        # Calculate checksum
        if progress_callback:
            progress_callback("Calculating backup checksum...")
        checksum = hashlib.sha256()
        for file in backup_path.rglob('*'):
            if file.is_file():
                with open(file, 'rb') as f:
                    checksum.update(f.read())

        # Save to database
        if progress_callback:
            progress_callback("Recording backup metadata...")
        with db._get_connection() as conn:
            conn.execute(
                """INSERT INTO backups (device_id, backup_name, backup_path, backup_size, backup_type, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (device_id, backup_name, str(backup_path), total_size, backup_type, checksum.hexdigest()),
            )
            conn.commit()

        logger.log('success', 'backup', f'Backup created: {backup_name}')
        if progress_callback:
            progress_callback("Backup complete.")

        return {
            'success': True,
            'backup_name': backup_name,
            'backup_path': str(backup_path),
            'items': backed_up,
            'size': total_size,
            'checksum': checksum.hexdigest(),
        }

    @staticmethod
    def list_backups(device_id: str = None) -> List[Dict]:
        """List all backups"""
        with db._get_connection() as conn:
            if device_id:
                backups = conn.execute(
                    "SELECT * FROM backups WHERE device_id = ? ORDER BY created DESC",
                    (device_id,),
                ).fetchall()
            else:
                backups = conn.execute("SELECT * FROM backups ORDER BY created DESC").fetchall()

            return [dict(b) for b in backups]
