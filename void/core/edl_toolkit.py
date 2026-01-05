"""
Extended EDL workflows and root helpers.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from pathlib import Path
import shutil
import subprocess
from typing import Any, Iterable

from ..config import Config
from .device import DeviceDetector
from .edl import edl_dump, edl_flash
from .utils import SafeSubprocess, check_tool, check_tools


@dataclass(frozen=True)
class ToolkitResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


_EDL_TOOL_CANDIDATES = ("qdl", "edl", "emmcdl")
_FIREHOSE_EXTENSIONS = (".mbn", ".elf", ".bin")


def _resolve_edl_tool() -> str | None:
    for tool in _EDL_TOOL_CANDIDATES:
        if shutil.which(tool):
            return tool
    return None


def _read_json_config() -> dict[str, Any]:
    return Config.read_config()


def _write_json_config(data: dict[str, Any]) -> None:
    Config.write_config(data)


def detect_edl_devices() -> ToolkitResult:
    devices, errors = DeviceDetector.detect_all()
    edl_devices = [device for device in devices if str(device.get("mode", "")).lower() == "edl"]
    return ToolkitResult(
        success=bool(edl_devices),
        message="EDL detection complete.",
        data={"devices": edl_devices, "errors": errors},
    )


def list_firehose_programmers() -> ToolkitResult:
    base_dir = Config.SCRIPTS_DIR / "firehose"
    if not base_dir.exists():
        return ToolkitResult(
            success=False,
            message="No firehose directory found. Create ~/.void/scripts/firehose and drop programmers in it.",
            data={"path": str(base_dir)},
        )
    files = sorted(
        str(path)
        for path in base_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _FIREHOSE_EXTENSIONS
    )
    return ToolkitResult(
        success=bool(files),
        message="Firehose programmer list ready.",
        data={"path": str(base_dir), "files": files},
    )


def list_partitions_via_adb(device_id: str) -> ToolkitResult:
    code, stdout, stderr = SafeSubprocess.run(
        ["adb", "-s", device_id, "shell", "ls", "-1", "/dev/block/by-name"]
    )
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Unable to read partition map via ADB.",
            data={"error": stderr.strip()},
        )
    partitions = [line.strip() for line in stdout.splitlines() if line.strip()]
    return ToolkitResult(
        success=bool(partitions),
        message="Partition map retrieved from device.",
        data={"partitions": partitions},
    )


def read_partition_table(loader: str | None = None) -> ToolkitResult:
    tool = _resolve_edl_tool()
    if not tool:
        return ToolkitResult(
            success=False,
            message="No EDL tools available to query partitions.",
        )

    commands: dict[str, list[str]] = {
        "edl": [tool, "printgpt"],
        "emmcdl": [tool, "-g"],
        "qdl": [tool, "--printgpt"],
    }
    command = commands.get(tool)
    if loader:
        command = [tool, "--loader", loader, "printgpt"] if tool == "edl" else command

    if not command:
        return ToolkitResult(
            success=False,
            message=f"Partition table query not supported for tool {tool}.",
        )

    code, stdout, stderr = SafeSubprocess.run(command)
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Partition table query failed.",
            data={"tool": tool, "error": stderr.strip(), "command": " ".join(command)},
        )
    return ToolkitResult(
        success=True,
        message="Partition table retrieved.",
        data={"tool": tool, "output": stdout.strip(), "command": " ".join(command)},
    )


def backup_partition(context: dict[str, str], partition: str) -> ToolkitResult:
    result = edl_dump(context, partition)
    return ToolkitResult(
        success=result.success,
        message=result.message,
        data=result.data or {},
    )


def restore_partition(context: dict[str, str], loader: str, image: str) -> ToolkitResult:
    result = edl_flash(context, loader, image)
    return ToolkitResult(
        success=result.success,
        message=result.message,
        data=result.data or {},
    )


def convert_sparse_image(source: Path, dest: Path, to_sparse: bool) -> ToolkitResult:
    tool = "img2simg" if to_sparse else "simg2img"
    tool_result = check_tool(tool)
    if not tool_result.available:
        return ToolkitResult(
            success=False,
            message=f"{tool} not available in PATH.",
            data={"error": tool_result.error},
        )

    command = [tool, str(source), str(dest)]
    code, _, stderr = SafeSubprocess.run(command, timeout=Config.TIMEOUT_LONG)
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Sparse conversion failed.",
            data={"error": stderr.strip(), "command": " ".join(command)},
        )
    return ToolkitResult(
        success=True,
        message="Sparse conversion completed.",
        data={"output": str(dest), "command": " ".join(command)},
    )


def verify_hash(path: Path, expected: str | None = None) -> ToolkitResult:
    if not path.exists():
        return ToolkitResult(
            success=False,
            message="File not found for hash verification.",
            data={"path": str(path)},
        )
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    computed = digest.hexdigest()
    matches = expected.lower() == computed.lower() if expected else True
    return ToolkitResult(
        success=matches,
        message="Hash verification complete.",
        data={"path": str(path), "sha256": computed, "matches": matches},
    )


def load_profiles() -> dict[str, dict[str, Any]]:
    data = _read_json_config()
    profiles = data.get("edl_profiles", {})
    return profiles if isinstance(profiles, dict) else {}


def save_profile(name: str, profile: dict[str, Any]) -> ToolkitResult:
    data = _read_json_config()
    profiles = data.get("edl_profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[name] = profile
    data["edl_profiles"] = profiles
    _write_json_config(data)
    return ToolkitResult(
        success=True,
        message="EDL profile saved.",
        data={"name": name, "profile": profile},
    )


def delete_profile(name: str) -> ToolkitResult:
    data = _read_json_config()
    profiles = data.get("edl_profiles", {})
    if not isinstance(profiles, dict) or name not in profiles:
        return ToolkitResult(
            success=False,
            message="EDL profile not found.",
            data={"name": name},
        )
    profiles.pop(name, None)
    data["edl_profiles"] = profiles
    _write_json_config(data)
    return ToolkitResult(
        success=True,
        message="EDL profile removed.",
        data={"name": name},
    )


def edl_unbrick_plan(loader: str | None) -> ToolkitResult:
    tools = check_tools([(tool, ("--version",)) for tool in _EDL_TOOL_CANDIDATES])
    missing = [tool.name for tool in tools if not tool.available]
    steps = [
        "Verify you have explicit authorization for the device.",
        "Confirm device enters EDL (USB 9008).",
        "Ensure the correct firehose programmer is available.",
    ]
    if loader:
        steps.append(f"Using loader: {loader}")
    if missing:
        steps.append(f"Install EDL tooling: {', '.join(missing)}")
    return ToolkitResult(
        success=True,
        message="EDL unbrick checklist generated.",
        data={"steps": steps, "tools": [tool.__dict__ for tool in tools]},
    )


def device_notes(vendor: str | None) -> ToolkitResult:
    notes_map = {
        "qualcomm": [
            "Avoid flashing modem/efs unless you have backups.",
            "Always confirm firehose programmer matches the SoC.",
        ],
        "mediatek": [
            "Use SP Flash Tool or MTK client for preloader recovery.",
            "Keep a backup of NVRAM/NVDATA partitions.",
        ],
        "samsung": [
            "Use official Odin packages when possible.",
            "Ensure VaultKeeper is disabled before unlocking.",
        ],
    }
    key = (vendor or "").lower()
    notes = notes_map.get(key, ["No device-specific notes available."])
    return ToolkitResult(
        success=True,
        message="Device notes ready.",
        data={"vendor": vendor or "unknown", "notes": notes},
    )


def reboot_device(device_id: str, target: str) -> ToolkitResult:
    target_lower = target.lower()
    if target_lower in {"edl", "recovery", "bootloader"}:
        command = ["adb", "-s", device_id, "reboot", target_lower]
    elif target_lower == "fastboot":
        command = ["adb", "-s", device_id, "reboot", "bootloader"]
    elif target_lower == "system":
        command = ["adb", "-s", device_id, "reboot"]
    else:
        return ToolkitResult(
            success=False,
            message="Unsupported reboot target.",
            data={"target": target},
        )

    code, _, stderr = SafeSubprocess.run(command)
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Reboot command failed.",
            data={"error": stderr.strip(), "command": " ".join(command)},
        )
    return ToolkitResult(
        success=True,
        message="Reboot command issued.",
        data={"command": " ".join(command)},
    )


def capture_edl_log(extra_commands: Iterable[list[str]] | None = None) -> ToolkitResult:
    Config.setup()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Config.LOG_DIR / f"edl_session_{timestamp}.log"
    entries: list[str] = []
    commands = [
        ["adb", "devices", "-l"],
        ["fastboot", "devices"],
    ]
    if extra_commands:
        commands.extend(extra_commands)

    for command in commands:
        code, stdout, stderr = SafeSubprocess.run(command, timeout=Config.TIMEOUT_SHORT)
        entries.append(f"$ {' '.join(command)}")
        if code == 0:
            entries.append(stdout.strip())
        else:
            entries.append(stderr.strip())
        entries.append("")

    log_path.write_text("\n".join(entries), encoding="utf-8")
    return ToolkitResult(
        success=True,
        message="EDL log captured.",
        data={"path": str(log_path)},
    )


def extract_boot_image(boot_image: Path) -> ToolkitResult:
    if not boot_image.exists():
        return ToolkitResult(
            success=False,
            message="Boot image not found.",
            data={"path": str(boot_image)},
        )
    Config.setup()
    output_dir = Config.EXPORTS_DIR / f"boot_extract_{boot_image.stem}"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / boot_image.name
    if boot_image.resolve() != target.resolve():
        shutil.copy2(boot_image, target)

    if shutil.which("magiskboot"):
        try:
            result = subprocess.run(
                ["magiskboot", "unpack", str(target)],
                cwd=str(output_dir),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            return ToolkitResult(
                success=False,
                message="Failed to run magiskboot.",
                data={"error": str(exc)},
            )
        if result.returncode != 0:
            return ToolkitResult(
                success=False,
                message="magiskboot unpack failed.",
                data={"error": result.stderr.strip()},
            )
        return ToolkitResult(
            success=True,
            message="Boot image unpacked with magiskboot.",
            data={"output_dir": str(output_dir)},
        )

    return ToolkitResult(
        success=True,
        message="Boot image staged (magiskboot not found for unpack).",
        data={"output_dir": str(output_dir)},
    )


def stage_magisk_patch(device_id: str, boot_image: Path) -> ToolkitResult:
    if not boot_image.exists():
        return ToolkitResult(
            success=False,
            message="Boot image not found for Magisk patch.",
            data={"path": str(boot_image)},
        )
    remote_path = "/sdcard/Download/void_boot.img"
    code, _, stderr = SafeSubprocess.run(
        ["adb", "-s", device_id, "push", str(boot_image), remote_path],
        timeout=Config.TIMEOUT_MEDIUM,
    )
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Failed to push boot image to device.",
            data={"error": stderr.strip()},
        )

    code, stdout, stderr = SafeSubprocess.run(
        ["adb", "-s", device_id, "shell", "ls", "/sdcard/Download/magisk_patched-*.img"],
        timeout=Config.TIMEOUT_SHORT,
    )
    patched_files = [line.strip() for line in stdout.splitlines() if line.strip()]
    return ToolkitResult(
        success=True,
        message="Boot image staged for Magisk patching.",
        data={
            "remote_path": remote_path,
            "patched_candidates": patched_files,
            "note": "Patch the boot image in the Magisk app, then re-run to pull the patched image.",
            "error": stderr.strip() if code != 0 else "",
        },
    )


def pull_magisk_patched(device_id: str, output_dir: Path) -> ToolkitResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    code, stdout, _ = SafeSubprocess.run(
        ["adb", "-s", device_id, "shell", "ls", "-t", "/sdcard/Download/magisk_patched-*.img"],
        timeout=Config.TIMEOUT_SHORT,
    )
    candidates = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not candidates:
        return ToolkitResult(
            success=False,
            message="No Magisk patched images found in /sdcard/Download.",
        )
    remote = candidates[0]
    local = output_dir / Path(remote).name
    code, _, stderr = SafeSubprocess.run(
        ["adb", "-s", device_id, "pull", remote, str(local)],
        timeout=Config.TIMEOUT_MEDIUM,
    )
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Failed to pull Magisk patched image.",
            data={"error": stderr.strip()},
        )
    return ToolkitResult(
        success=True,
        message="Magisk patched image pulled.",
        data={"path": str(local)},
    )


def verify_twrp_image(device_id: str, image_path: Path) -> ToolkitResult:
    if not image_path.exists():
        return ToolkitResult(
            success=False,
            message="TWRP image not found.",
            data={"path": str(image_path)},
        )
    code, stdout, _ = SafeSubprocess.run(
        ["adb", "-s", device_id, "shell", "getprop", "ro.product.device"]
    )
    codename = stdout.strip()
    matches = codename and codename.lower() in image_path.name.lower()
    return ToolkitResult(
        success=matches,
        message="TWRP image validation complete.",
        data={"device_codename": codename, "matches": matches},
    )


def flash_recovery(device_id: str, image_path: Path, boot_only: bool = False) -> ToolkitResult:
    if not image_path.exists():
        return ToolkitResult(
            success=False,
            message="Recovery image not found.",
            data={"path": str(image_path)},
        )
    command = ["fastboot", "-s", device_id]
    if boot_only:
        command += ["boot", str(image_path)]
    else:
        command += ["flash", "recovery", str(image_path)]
    code, _, stderr = SafeSubprocess.run(command, timeout=Config.TIMEOUT_LONG)
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Recovery flash failed.",
            data={"error": stderr.strip(), "command": " ".join(command)},
        )
    return ToolkitResult(
        success=True,
        message="Recovery flash issued.",
        data={"command": " ".join(command)},
    )


def verify_root(device_id: str) -> ToolkitResult:
    code, stdout, stderr = SafeSubprocess.run(["adb", "-s", device_id, "shell", "su", "-c", "id"])
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Root check failed.",
            data={"error": stderr.strip()},
        )
    is_root = "uid=0" in stdout
    return ToolkitResult(
        success=is_root,
        message="Root verification complete.",
        data={"output": stdout.strip(), "root": is_root},
    )


def safety_check(device_id: str) -> ToolkitResult:
    checks: list[dict[str, Any]] = []
    tool_checks = check_tools(
        [("adb", ("version",)), ("fastboot", ("--version",)), ("edl", ("--version",))]
    )
    checks.append({"category": "tools", "tools": [tool.__dict__ for tool in tool_checks]})

    code, stdout, _ = SafeSubprocess.run(
        ["adb", "-s", device_id, "shell", "getprop", "ro.boot.flash.locked"]
    )
    if code == 0:
        checks.append({"category": "bootloader", "flash_locked": stdout.strip()})

    code, stdout, _ = SafeSubprocess.run(["fastboot", "-s", device_id, "getvar", "unlocked"])
    if code == 0:
        checks.append({"category": "fastboot", "unlocked": stdout.strip()})

    return ToolkitResult(
        success=True,
        message="Safety checklist complete.",
        data={"checks": checks},
    )


def rollback_flash(device_id: str, partition: str, image_path: Path) -> ToolkitResult:
    if not image_path.exists():
        return ToolkitResult(
            success=False,
            message="Rollback image not found.",
            data={"path": str(image_path)},
        )
    command = ["fastboot", "-s", device_id, "flash", partition, str(image_path)]
    code, _, stderr = SafeSubprocess.run(command, timeout=Config.TIMEOUT_LONG)
    if code != 0:
        return ToolkitResult(
            success=False,
            message="Rollback flash failed.",
            data={"error": stderr.strip(), "command": " ".join(command)},
        )
    return ToolkitResult(
        success=True,
        message="Rollback flash issued.",
        data={"command": " ".join(command)},
    )


def compatibility_matrix() -> ToolkitResult:
    matrix = [
        {
            "chipset": "Qualcomm",
            "edl_tools": ["edl", "qdl", "emmcdl"],
            "notes": "EDL available via 9008 mode with firehose.",
        },
        {
            "chipset": "MediaTek",
            "edl_tools": ["mtkclient", "spflashtool"],
            "notes": "Use bootrom/preloader workflows.",
        },
        {
            "chipset": "Samsung",
            "edl_tools": ["odin", "heimdall"],
            "notes": "Uses download mode, not EDL.",
        },
    ]
    return ToolkitResult(
        success=True,
        message="Compatibility matrix ready.",
        data={"matrix": matrix},
    )
