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
            if parsed.scheme not in ["http", "https"]:
                return False

            with urllib.request.urlopen(url, timeout=timeout) as response:
                with open(dest, "wb") as f:
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
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "ip", "addr"])
        if code == 0:
            interfaces = []
            current = {}
            for line in stdout.split("\n"):
                if line and line[0].isdigit():
                    if current:
                        interfaces.append(current)
                    parts = line.split(":")
                    if len(parts) >= 2:
                        current = {"name": parts[1].strip()}
                elif "inet" in line and current:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        current["ip"] = parts[1]
            if current:
                interfaces.append(current)
            analysis["interfaces"] = interfaces

        # WiFi info
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "dumpsys", "wifi"])
        if code == 0:
            wifi = {}
            for line in stdout.split("\n"):
                if "Wi-Fi is" in line:
                    wifi["status"] = "enabled" if "enabled" in line else "disabled"
                elif "mNetworkInfo" in line and "SSID" in line:
                    match = re.search(r"SSID: (\S+)", line)
                    if match:
                        wifi["ssid"] = match.group(1)
            analysis["wifi"] = wifi

        # Network stats
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "cat", "/proc/net/dev"]
        )
        if code == 0:
            stats = []
            for line in stdout.split("\n")[2:]:
                if ":" in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        stats.append(
                            {
                                "interface": parts[0].replace(":", ""),
                                "rx_bytes": parts[1],
                                "tx_bytes": parts[9],
                            }
                        )
            analysis["network_stats"] = stats

        return analysis

    @staticmethod
    def toggle_wifi(device_id: str, enable: bool) -> bool:
        """Toggle WiFi on/off"""
        action = "enable" if enable else "disable"
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "svc", "wifi", action])
        return code == 0

    @staticmethod
    def toggle_mobile_data(device_id: str, enable: bool) -> bool:
        """Toggle mobile data on/off"""
        action = "enable" if enable else "disable"
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "svc", "data", action])
        return code == 0

    @staticmethod
    def list_wifi_networks(device_id: str) -> list:
        """List saved WiFi networks"""
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "cmd", "wifi", "list-networks"]
        )

        networks = []
        if code == 0:
            lines = stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                if line.strip():
                    networks.append(line.strip())

        return networks

    @staticmethod
    def forget_wifi_network(device_id: str, network_id: str) -> bool:
        """Forget saved WiFi network"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "cmd", "wifi", "forget-network", network_id]
        )
        return code == 0

    @staticmethod
    def get_network_info(device_id: str) -> Dict[str, Any]:
        """Get IP and MAC address info"""
        info = {}

        # Get IP address
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "ip", "addr", "show", "wlan0"]
        )
        if code == 0:
            for line in stdout.split("\n"):
                if "inet " in line:
                    info["ip"] = line.strip().split()[1].split("/")[0]
                elif "link/ether" in line:
                    info["mac"] = line.strip().split()[1]

        # Get default gateway
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "ip", "route"])
        if code == 0:
            for line in stdout.split("\n"):
                if "default" in line:
                    parts = line.split()
                    if "via" in parts:
                        idx = parts.index("via")
                        if idx + 1 < len(parts):
                            info["gateway"] = parts[idx + 1]

        return info

    @staticmethod
    def ping_host(device_id: str, host: str, count: int = 4) -> Dict[str, Any]:
        """Ping a host from the device"""
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "ping", "-c", str(count), host]
        )

        result = {"success": code == 0, "output": stdout}

        # Parse ping statistics
        if code == 0:
            for line in stdout.split("\n"):
                if "packets transmitted" in line:
                    result["stats"] = line.strip()
                elif "min/avg/max" in line:
                    result["timing"] = line.strip()

        return result

    @staticmethod
    def forward_port(local_port: int, device_id: str, remote_port: int) -> bool:
        """Forward local port to device port (adb forward)"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "forward", f"tcp:{local_port}", f"tcp:{remote_port}"]
        )
        return code == 0

    @staticmethod
    def reverse_port(device_id: str, remote_port: int, local_port: int) -> bool:
        """Reverse port forwarding (adb reverse)"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "reverse", f"tcp:{remote_port}", f"tcp:{local_port}"]
        )
        return code == 0

    @staticmethod
    def list_port_forwards(device_id: str) -> list:
        """List active port forwards"""
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "forward", "--list"])

        forwards = []
        if code == 0:
            for line in stdout.strip().split("\n"):
                if line.strip():
                    forwards.append(line.strip())

        return forwards

    @staticmethod
    def remove_port_forward(device_id: str, local_port: int) -> bool:
        """Remove port forward"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "forward", "--remove", f"tcp:{local_port}"]
        )
        return code == 0
