from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ..config import Config
from .device import DeviceDetector
from .edl_toolkit import list_partitions_via_adb
from .logging import logger
from .utils import SafeSubprocess


def _sanitize_device_id(device_id: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in device_id).strip("_")


def list_partitions(device_id: str) -> Dict[str, Any]:
    devices, _ = DeviceDetector.detect_all()
    device_info = next((device for device in devices if device.get("id") == device_id), None)
    mode = (device_info or {}).get("mode")
    if not device_info or mode != "adb":
        return {
            "success": False,
            "message": "Partition listing requires an ADB-connected device.",
            "device_id": device_id,
            "mode": mode,
        }

    result = list_partitions_via_adb(device_id)
    return {
        "success": result.success,
        "message": result.message,
        "device_id": device_id,
        "mode": mode,
        "partitions": result.data.get("partitions", []),
        "error": result.data.get("error"),
    }


def backup_partition(device_id: str, partition: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    devices, _ = DeviceDetector.detect_all()
    device_info = next((device for device in devices if device.get("id") == device_id), None)
    mode = (device_info or {}).get("mode")
    if not device_info or mode != "adb":
        return {
            "success": False,
            "message": "Partition backup requires an ADB-connected device.",
            "device_id": device_id,
            "mode": mode,
        }

    Config.ensure_directories()
    safe_device_id = _sanitize_device_id(device_id) or "unknown"
    output_dir = output_dir or (Config.BACKUP_DIR / "partitions" / safe_device_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    remote_dir = "/sdcard/Void/partitions"
    remote_path = f"{remote_dir}/{partition}.img"
    local_path = output_dir / f"{partition}.img"

    logger.log("info", "partitions", f"Backing up {partition} via ADB.", device_id=device_id)
    steps = []

    def run_step(command: list[str], label: str, timeout: int = Config.TIMEOUT_LONG) -> bool:
        code, stdout, stderr = SafeSubprocess.run(command, timeout=timeout)
        detail = (stderr or stdout or "").strip() or None
        steps.append({"step": label, "command": " ".join(command), "success": code == 0, "detail": detail})
        return code == 0

    if not run_step(["adb", "-s", device_id, "shell", "mkdir", "-p", remote_dir], "prepare_remote_dir"):
        return {"success": False, "message": "Failed to prepare remote directory.", "steps": steps}

    if not run_step(
        ["adb", "-s", device_id, "shell", "dd", f"if=/dev/block/by-name/{partition}", f"of={remote_path}", "bs=4M"],
        "dd_partition",
        timeout=Config.TIMEOUT_LONG,
    ):
        return {"success": False, "message": "Partition dump failed.", "steps": steps}

    if not run_step(["adb", "-s", device_id, "pull", remote_path, str(local_path)], "pull_partition"):
        return {"success": False, "message": "Failed to pull partition image.", "steps": steps}

    run_step(["adb", "-s", device_id, "shell", "rm", "-f", remote_path], "cleanup_remote")

    return {
        "success": True,
        "message": "Partition backup completed.",
        "device_id": device_id,
        "partition": partition,
        "path": str(local_path),
        "steps": steps,
    }


def wipe_partition(device_id: str, partition: str) -> Dict[str, Any]:
    devices, _ = DeviceDetector.detect_all()
    device_info = next((device for device in devices if device.get("id") == device_id), None)
    mode = (device_info or {}).get("mode")
    if not device_info:
        return {
            "success": False,
            "message": "Device not found.",
            "device_id": device_id,
        }

    if mode == "fastboot":
        command = ["fastboot", "-s", device_id, "erase", partition]
        code, stdout, stderr = SafeSubprocess.run(command, timeout=Config.TIMEOUT_LONG)
        detail = (stderr or stdout or "").strip()
        return {
            "success": code == 0,
            "message": "Fastboot erase issued." if code == 0 else "Fastboot erase failed.",
            "device_id": device_id,
            "mode": mode,
            "command": " ".join(command),
            "detail": detail,
        }

    if mode == "adb":
        command = ["adb", "-s", device_id, "shell", "dd", f"if=/dev/zero", f"of=/dev/block/by-name/{partition}"]
        code, stdout, stderr = SafeSubprocess.run(command, timeout=Config.TIMEOUT_LONG)
        detail = (stderr or stdout or "").strip()
        return {
            "success": code == 0,
            "message": "ADB wipe issued." if code == 0 else "ADB wipe failed.",
            "device_id": device_id,
            "mode": mode,
            "command": " ".join(command),
            "detail": detail,
        }

    return {
        "success": False,
        "message": "Partition wipe requires ADB or fastboot mode.",
        "device_id": device_id,
        "mode": mode,
    }
