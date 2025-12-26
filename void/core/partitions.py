from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from ..config import Config
from .device import DeviceDetector
from .utils import SafeSubprocess


class PartitionManager:
    """Partition browsing and dump utilities."""

    @staticmethod
    def detect_device_mode(device_id: str) -> str:
        """Detect the device mode (adb or fastboot) based on current device list."""
        devices = DeviceDetector.detect_all()
        for device in devices:
            if device.get("id") == device_id:
                return device.get("mode", "adb")
        return "adb"

    @staticmethod
    def list_partitions(device_id: str, mode: str = "adb") -> List[Dict[str, str]]:
        """List partitions using adb or fastboot."""
        if mode == "fastboot":
            return PartitionManager._list_fastboot_partitions(device_id)
        return PartitionManager._list_adb_partitions(device_id)

    @staticmethod
    def dump_partition(
        device_id: str, partition: str, output_path: Path, mode: str = "adb"
    ) -> Dict[str, str | bool]:
        """Dump a partition image to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "fastboot":
            return PartitionManager._dump_fastboot_partition(device_id, partition, output_path)
        return PartitionManager._dump_adb_partition(device_id, partition, output_path)

    @staticmethod
    def hash_partition(device_id: str, partition: str, mode: str = "adb") -> Dict[str, str | bool]:
        """Compute SHA-256 hash of a partition."""
        if mode == "fastboot":
            return PartitionManager._hash_fastboot_partition(device_id, partition)
        return PartitionManager._hash_adb_partition(device_id, partition)

    @staticmethod
    def _list_adb_partitions(device_id: str) -> List[Dict[str, str]]:
        paths = ["/dev/block/by-name", "/dev/block/platform/*/by-name"]
        partitions: List[Dict[str, str]] = []
        for path in paths:
            code, stdout, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "shell", "ls", "-1", path]
            )
            if code != 0 or not stdout.strip():
                continue
            for line in stdout.splitlines():
                name = line.strip()
                if not name or name in {"." , ".."}:
                    continue
                partitions.append({"name": name, "source": path})
            if partitions:
                break
        return sorted(partitions, key=lambda item: item["name"])

    @staticmethod
    def _list_fastboot_partitions(device_id: str) -> List[Dict[str, str]]:
        code, stdout, _ = SafeSubprocess.run(["fastboot", "-s", device_id, "getvar", "all"])
        if code != 0:
            return []
        partitions: Dict[str, Dict[str, str]] = {}
        for line in stdout.splitlines():
            cleaned = line.replace("(bootloader)", "").strip()
            size_match = re.search(r"partition-size:([^:]+):\s*(\S+)", cleaned)
            type_match = re.search(r"partition-type:([^:]+):\s*(\S+)", cleaned)
            if size_match:
                name, size = size_match.group(1), size_match.group(2)
                partitions.setdefault(name, {})["size"] = size
            if type_match:
                name, part_type = type_match.group(1), type_match.group(2)
                partitions.setdefault(name, {})["type"] = part_type
        return [
            {"name": name, **info}
            for name, info in sorted(partitions.items(), key=lambda item: item[0])
        ]

    @staticmethod
    def _dump_adb_partition(device_id: str, partition: str, output_path: Path) -> Dict[str, str | bool]:
        cmd = [
            "adb",
            "-s",
            device_id,
            "exec-out",
            "sh",
            "-c",
            f"dd if=/dev/block/by-name/{partition} 2>/dev/null",
        ]
        try:
            with output_path.open("wb") as handle:
                result = subprocess.run(cmd, stdout=handle, stderr=subprocess.PIPE, check=False)
            if result.returncode == 0:
                return {"success": True, "path": str(output_path)}
            return {
                "success": False,
                "message": result.stderr.decode(errors="ignore") or "Dump failed.",
            }
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    @staticmethod
    def _dump_fastboot_partition(
        device_id: str, partition: str, output_path: Path
    ) -> Dict[str, str | bool]:
        cmd = ["fastboot", "-s", device_id, "fetch", partition, str(output_path)]
        code, stdout, stderr = SafeSubprocess.run(cmd, timeout=Config.TIMEOUT_LONG)
        if code == 0:
            return {"success": True, "path": str(output_path), "message": stdout.strip()}
        return {"success": False, "message": stderr.strip() or stdout.strip()}

    @staticmethod
    def _hash_adb_partition(device_id: str, partition: str) -> Dict[str, str | bool]:
        cmd = [
            "adb",
            "-s",
            device_id,
            "exec-out",
            "sh",
            "-c",
            f"dd if=/dev/block/by-name/{partition} 2>/dev/null",
        ]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            digest = hashlib.sha256()
            if process.stdout:
                for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
                    digest.update(chunk)
            _, stderr = process.communicate()
            if process.returncode == 0:
                return {"success": True, "hash": digest.hexdigest(), "algorithm": "sha256"}
            return {"success": False, "message": stderr.decode(errors="ignore")}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    @staticmethod
    def _hash_fastboot_partition(device_id: str, partition: str) -> Dict[str, str | bool]:
        Config.setup()
        temp_path = Config.CACHE_DIR / f"{device_id}_{partition}_{uuid4().hex}.img"
        dump_result = PartitionManager._dump_fastboot_partition(device_id, partition, temp_path)
        if not dump_result.get("success"):
            return dump_result
        digest = hashlib.sha256()
        with temp_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        temp_path.unlink(missing_ok=True)
        return {"success": True, "hash": digest.hexdigest(), "algorithm": "sha256"}
