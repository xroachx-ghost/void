"""
Fastboot operations wrapper.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .utils import SafeSubprocess


class FastbootController:
    """Fastboot operations"""

    @staticmethod
    def flash_partition(device_id: str, partition: str, image_path: Path) -> bool:
        """Flash partition with image file
        
        Args:
            device_id: Device identifier
            partition: Partition name (e.g., 'boot', 'recovery', 'system')
            image_path: Path to image file
        """
        if not image_path.exists():
            return False
        
        code, _, _ = SafeSubprocess.run([
            'fastboot', '-s', device_id, 'flash', partition, str(image_path)
        ])
        return code == 0

    @staticmethod
    def erase_partition(device_id: str, partition: str) -> bool:
        """Erase partition"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'erase', partition])
        return code == 0

    @staticmethod
    def get_var(device_id: str, variable: str) -> str:
        """Get fastboot variable value
        
        Args:
            device_id: Device identifier
            variable: Variable name (e.g., 'product', 'version', 'unlocked')
        """
        code, stdout, stderr = SafeSubprocess.run(['fastboot', '-s', device_id, 'getvar', variable])
        
        # Fastboot outputs to stderr
        output = stderr if stderr else stdout
        if code == 0 or output:
            for line in output.split('\n'):
                if ':' in line:
                    return line.split(':', 1)[1].strip()
        
        return ''

    @staticmethod
    def get_all_vars(device_id: str) -> Dict[str, str]:
        """Get all fastboot variables"""
        code, stdout, stderr = SafeSubprocess.run(['fastboot', '-s', device_id, 'getvar', 'all'])
        
        variables = {}
        output = stderr if stderr else stdout  # Fastboot outputs to stderr
        
        if code == 0 or output:
            for line in output.split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().replace('(bootloader) ', '')
                        value = parts[1].strip()
                        variables[key] = value
        
        return variables

    @staticmethod
    def boot_image(device_id: str, image_path: Path) -> bool:
        """Boot from image without flashing
        
        Args:
            device_id: Device identifier
            image_path: Path to boot image
        """
        if not image_path.exists():
            return False
        
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'boot', str(image_path)])
        return code == 0

    @staticmethod
    def reboot(device_id: str, mode: str = 'system') -> bool:
        """Reboot from fastboot
        
        Args:
            device_id: Device identifier
            mode: 'system', 'bootloader', or 'recovery'
        """
        if mode == 'system':
            code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'reboot'])
        elif mode == 'bootloader':
            code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'reboot-bootloader'])
        elif mode == 'recovery':
            code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'reboot-recovery'])
        else:
            return False
        
        return code == 0

    @staticmethod
    def continue_boot(device_id: str) -> bool:
        """Continue to system boot"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'continue'])
        return code == 0

    @staticmethod
    def oem_unlock(device_id: str) -> bool:
        """Unlock bootloader (OEM unlock)"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'oem', 'unlock'])
        return code == 0

    @staticmethod
    def oem_lock(device_id: str) -> bool:
        """Lock bootloader (OEM lock)"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'oem', 'lock'])
        return code == 0

    @staticmethod
    def flashing_unlock(device_id: str) -> bool:
        """Unlock critical partitions (modern devices)"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'flashing', 'unlock'])
        return code == 0

    @staticmethod
    def flashing_lock(device_id: str) -> bool:
        """Lock critical partitions (modern devices)"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'flashing', 'lock'])
        return code == 0

    @staticmethod
    def format_partition(device_id: str, partition: str, fs_type: str = 'ext4') -> bool:
        """Format partition
        
        Args:
            device_id: Device identifier
            partition: Partition name
            fs_type: Filesystem type (e.g., 'ext4', 'f2fs')
        """
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'format', partition])
        return code == 0

    @staticmethod
    def flash_all(device_id: str, images_dir: Path) -> bool:
        """Flash all partitions from directory (flashall)"""
        if not images_dir.exists():
            return False
        
        # Change to directory and run flashall
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'flashall'], cwd=str(images_dir))
        return code == 0
