"""
Network analysis and tools.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import shutil
import socket
import urllib.parse
import urllib.request
import re
from pathlib import Path
from typing import Any, Dict

from .utils import SafeSubprocess


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
        except Exception:
            return False

    @staticmethod
    def check_internet() -> bool:
        """Check internet connectivity"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception:
            return False


class NetworkAnalyzer:
    """Network analysis"""

    @staticmethod
    def analyze(device_id: str) -> Dict[str, Any]:
        """Analyze network"""
        analysis = {}

        # IP configuration
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'ip', 'addr'])
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
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'dumpsys', 'wifi'])
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
        code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'cat', '/proc/net/dev'])
        if code == 0:
            stats = []
            for line in stdout.split('\n')[2:]:
                if ':' in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        stats.append(
                            {
                                'interface': parts[0].replace(':', ''),
                                'rx_bytes': parts[1],
                                'tx_bytes': parts[9],
                            }
                        )
            analysis['network_stats'] = stats

        return analysis
