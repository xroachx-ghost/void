"""
Process management for Android devices.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from typing import Dict, List

from .utils import SafeSubprocess


class ProcessManager:
    """Process management"""

    @staticmethod
    def list_processes(device_id: str) -> List[Dict]:
        """List running processes"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'ps', '-A'])
        
        processes = []
        if code == 0:
            lines = stdout.strip().split('\n')
            if len(lines) > 1:
                # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        processes.append({
                            'user': parts[0],
                            'pid': parts[1],
                            'ppid': parts[2],
                            'vsz': parts[3],
                            'rss': parts[4],
                            'wchan': parts[5],
                            'addr': parts[6],
                            'state': parts[7],
                            'name': ' '.join(parts[8:])
                        })
        
        return processes

    @staticmethod
    def get_top_processes(device_id: str, sort_by: str = 'cpu') -> List[Dict]:
        """Get top processes sorted by CPU or memory usage
        
        Args:
            device_id: Device identifier
            sort_by: 'cpu' or 'memory'
        """
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'top', '-n', '1'])
        
        processes = []
        if code == 0:
            lines = stdout.strip().split('\n')
            parsing = False
            
            for line in lines:
                if 'PID' in line and 'USER' in line:
                    parsing = True
                    continue
                
                if parsing and line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        processes.append({
                            'pid': parts[0],
                            'user': parts[1],
                            'pr': parts[2],
                            'ni': parts[3],
                            'virt': parts[4],
                            'res': parts[5],
                            'shr': parts[6],
                            'state': parts[7],
                            'cpu': parts[8].replace('%', ''),
                            'mem': parts[9].replace('%', '') if len(parts) > 9 else '0',
                            'time': parts[10] if len(parts) > 10 else '0',
                            'name': ' '.join(parts[11:]) if len(parts) > 11 else ''
                        })
        
        # Sort processes
        if sort_by == 'cpu':
            processes.sort(key=lambda p: float(p['cpu']) if p['cpu'].replace('.', '').isdigit() else 0, reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda p: float(p['mem']) if p['mem'].replace('.', '').isdigit() else 0, reverse=True)
        
        return processes[:20]  # Return top 20

    @staticmethod
    def kill_process(device_id: str, pid: str) -> bool:
        """Kill process by PID"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'kill', pid])
        return code == 0

    @staticmethod
    def force_kill_process(device_id: str, pid: str) -> bool:
        """Force kill process by PID (kill -9)"""
        code, _, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'kill', '-9', pid])
        return code == 0

    @staticmethod
    def get_process_info(device_id: str, package: str) -> Dict:
        """Get detailed process information for a package"""
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'meminfo', package])
        
        info = {'package': package}
        if code == 0:
            lines = stdout.split('\n')
            for line in lines:
                if 'TOTAL' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        info['total_memory'] = parts[1]
                elif 'Native Heap' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        info['native_heap'] = parts[1]
                elif 'Dalvik Heap' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        info['dalvik_heap'] = parts[1]
        
        return info
