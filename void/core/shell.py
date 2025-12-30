"""
Interactive shell support for Android devices.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Dict, List

from .utils import SafeSubprocess


class ShellController:
    """Shell command execution"""

    @staticmethod
    def execute_command(device_id: str, command: str) -> Dict:
        """Execute shell command on device
        
        Args:
            device_id: Device identifier
            command: Shell command to execute
            
        Returns:
            Dict with success, output, and error
        """
        code, stdout, stderr = SafeSubprocess.run(['adb', '-s', device_id, 'shell', command])
        
        return {
            'success': code == 0,
            'exit_code': code,
            'output': stdout,
            'error': stderr
        }

    @staticmethod
    def execute_commands_batch(device_id: str, commands: List[str]) -> List[Dict]:
        """Execute multiple commands sequentially
        
        Args:
            device_id: Device identifier
            commands: List of shell commands
            
        Returns:
            List of results for each command
        """
        results = []
        for command in commands:
            result = ShellController.execute_command(device_id, command)
            results.append({
                'command': command,
                **result
            })
        
        return results

    @staticmethod
    def execute_script(device_id: str, script_content: str) -> Dict:
        """Execute shell script on device
        
        Args:
            device_id: Device identifier
            script_content: Shell script content
            
        Returns:
            Dict with success, output, and error
        """
        # Create temporary script on device
        script_path = '/data/local/tmp/void_script.sh'
        
        # Write script to device
        code, _, _ = SafeSubprocess.run([
            'adb', '-s', device_id, 'shell', 
            f'echo "{script_content}" > {script_path}'
        ])
        
        if code != 0:
            return {'success': False, 'error': 'Failed to write script'}
        
        # Make executable
        code, _, _ = SafeSubprocess.run([
            'adb', '-s', device_id, 'shell', 'chmod', '755', script_path
        ])
        
        if code != 0:
            return {'success': False, 'error': 'Failed to make script executable'}
        
        # Execute
        code, stdout, stderr = SafeSubprocess.run([
            'adb', '-s', device_id, 'shell', 'sh', script_path
        ])
        
        # Cleanup
        SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'rm', script_path])
        
        return {
            'success': code == 0,
            'exit_code': code,
            'output': stdout,
            'error': stderr
        }

    @staticmethod
    def get_root_status(device_id: str) -> bool:
        """Check if device has root access"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'su', '-c', 'id'])
        
        return code == 0 and 'uid=0' in stdout

    @staticmethod
    def execute_as_root(device_id: str, command: str) -> Dict:
        """Execute command as root
        
        Args:
            device_id: Device identifier
            command: Shell command to execute
            
        Returns:
            Dict with success, output, and error
        """
        code, stdout, stderr = SafeSubprocess.run([
            'adb', '-s', device_id, 'shell', 'su', '-c', command
        ])
        
        return {
            'success': code == 0,
            'exit_code': code,
            'output': stdout,
            'error': stderr
        }
