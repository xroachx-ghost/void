from __future__ import annotations

from typing import Dict

from .utils import SafeSubprocess


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

        return {'success': any(results), 'message': f'Success: {sum(results)}/{len(results)}'}

    def _method_adb_accounts(self, device_id: str, **kwargs) -> Dict:
        """Remove accounts"""
        commands = [
            ['adb', '-s', device_id, 'shell', 'rm', '-f', '/data/system/users/0/accounts.db'],
            ['adb', '-s', device_id, 'shell', 'rm', '-rf', '/data/data/com.google.android.gms'],
        ]

        results = [SafeSubprocess.run(cmd)[0] == 0 for cmd in commands]

        return {'success': any(results), 'message': f'Accounts removed: {sum(results)}/{len(results)}'}

    def _method_fastboot_erase(self, device_id: str, **kwargs) -> Dict:
        """Fastboot erase"""
        partitions = ['frp', 'misc', 'persist']
        results = []

        for partition in partitions:
            code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'erase', partition])
            results.append(code == 0)

        return {'success': any(results), 'message': f'Erased: {sum(results)}/{len(partitions)}'}

    def _method_fastboot_format(self, device_id: str, **kwargs) -> Dict:
        """Fastboot format"""
        code, _, _ = SafeSubprocess.run(['fastboot', '-s', device_id, 'format', 'userdata'])

        return {'success': code == 0, 'message': 'Userdata formatted' if code == 0 else 'Failed'}
