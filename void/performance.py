"""Performance analysis."""
from __future__ import annotations

from typing import Any, Dict

from .utils import SafeSubprocess


class PerformanceAnalyzer:
    """Device performance analysis"""

    @staticmethod
    def analyze(device_id: str) -> Dict[str, Any]:
        """Comprehensive performance analysis"""
        analysis: Dict[str, Any] = {}

        # CPU info
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "cat", "/proc/cpuinfo"])
        if code == 0:
            analysis["cpu_cores"] = stdout.count("processor")

            # Parse CPU model
            for line in stdout.split("\n"):
                if "Hardware" in line:
                    analysis["cpu_model"] = line.split(":")[1].strip()
                    break

        # Memory info
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "cat", "/proc/meminfo"])
        if code == 0:
            for line in stdout.split("\n"):
                if "MemTotal" in line:
                    analysis["total_memory"] = line.split()[1]
                elif "MemAvailable" in line:
                    analysis["available_memory"] = line.split()[1]

        # Storage info
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "df"])
        if code == 0:
            storage = []
            for line in stdout.split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    storage.append(
                        {
                            "filesystem": parts[0],
                            "size": parts[1],
                            "used": parts[2],
                            "available": parts[3],
                            "use_percent": parts[4],
                            "mount": parts[5],
                        }
                    )
            analysis["storage"] = storage

        # Battery stats
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "dumpsys", "battery"])
        if code == 0:
            battery: Dict[str, Any] = {}
            for line in stdout.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    battery[key.strip().lower().replace(" ", "_")] = value.strip()
            analysis["battery"] = battery

        # Top processes
        code, stdout, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "top", "-n", "1"])
        if code == 0:
            processes = []
            for line in stdout.split("\n"):
                if "%" in line and not line.startswith("User"):
                    parts = line.split()
                    if len(parts) >= 9:
                        processes.append(
                            {"pid": parts[0], "cpu": parts[2], "mem": parts[5], "name": parts[-1]}
                        )
            analysis["top_processes"] = processes[:10]

        return analysis
