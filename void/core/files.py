from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..config import Config
from .utils import SafeSubprocess


class FileManager:
    """Device file management"""

    @staticmethod
    def list_files(device_id: str, path: str = '/sdcard') -> List[Dict]:
        """List files in directory"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'ls', '-la', path])

        files = []
        if code == 0:
            for line in stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 8:
                    files.append(
                        {
                            'permissions': parts[0],
                            'size': parts[4],
                            'date': f"{parts[5]} {parts[6]}",
                            'name': ' '.join(parts[7:]),
                        }
                    )

        return files

    @staticmethod
    def pull_file(device_id: str, remote_path: str, local_path: Path = None) -> Dict:
        """Pull file from device"""
        if local_path is None:
            filename = Path(remote_path).name
            local_path = Config.EXPORTS_DIR / filename

        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'pull', remote_path, str(local_path)])

        if code == 0 and local_path.exists():
            return {'success': True, 'path': str(local_path), 'size': local_path.stat().st_size}

        return {'success': False}

    @staticmethod
    def push_file(device_id: str, local_path: Path, remote_path: str) -> bool:
        """Push file to device"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'push', str(local_path), remote_path])
        return code == 0

    @staticmethod
    def delete_file(device_id: str, path: str) -> bool:
        """Delete file on device"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'rm', '-f', path])
        return code == 0
