from __future__ import annotations

import re
from typing import Any, Dict, List

from .chipsets.dispatcher import detect_chipset_for_device
from .database import db
from .utils import SafeSubprocess
from ..config import Config


class DeviceDetector:
    """Comprehensive device detection"""

    @staticmethod
    def detect_all() -> List[Dict[str, Any]]:
        """Detect all devices"""
        devices = []
        devices.extend(DeviceDetector._detect_adb())
        devices.extend(DeviceDetector._detect_fastboot())
        devices.extend(DeviceDetector._detect_usb_modes())

        # Update database
        for device in devices:
            DeviceDetector._attach_chipset_metadata(device)
            db.update_device(device)

        return devices

    @staticmethod
    def _detect_adb() -> List[Dict[str, Any]]:
        """Detect ADB devices"""
        devices = []
        try:
            code, stdout, _ = SafeSubprocess.run(['adb', 'devices', '-l'])
            if code == 0:
                for line in stdout.strip().split('\n')[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            device_id = parts[0]
                            status = parts[1]

                            if status == 'device':
                                info = DeviceDetector._get_adb_info(device_id)
                                info.update(DeviceDetector._parse_adb_listing(parts[2:]))
                                devices.append(
                                    {
                                        'id': device_id,
                                        'mode': 'adb',
                                        'status': status,
                                        **info,
                                    }
                                )
        except Exception:
            pass
        return devices

    @staticmethod
    def _get_adb_info(device_id: str) -> Dict[str, str]:
        """Get comprehensive device info"""
        info = {}
        info['reachable'] = DeviceDetector._check_adb_ready(device_id)

        props = {
            'manufacturer': 'ro.product.manufacturer',
            'model': 'ro.product.model',
            'brand': 'ro.product.brand',
            'device': 'ro.product.device',
            'product': 'ro.product.name',
            'android_version': 'ro.build.version.release',
            'sdk_version': 'ro.build.version.sdk',
            'release_codename': 'ro.build.version.codename',
            'incremental': 'ro.build.version.incremental',
            'build_id': 'ro.build.id',
            'build_type': 'ro.build.type',
            'build_tags': 'ro.build.tags',
            'build_date': 'ro.build.date',
            'security_patch': 'ro.build.version.security_patch',
            'chipset': 'ro.board.platform',
            'hardware': 'ro.hardware',
            'cpu_abi': 'ro.product.cpu.abi',
            'cpu_abi2': 'ro.product.cpu.abi2',
            'serial': 'ro.serialno',
            'bootloader': 'ro.bootloader',
            'fingerprint': 'ro.build.fingerprint',
        }

        for key, prop in props.items():
            try:
                code, stdout, _ = SafeSubprocess.run(
                    ['adb', '-s', device_id, 'shell', 'getprop', prop]
                )
                if code == 0 and stdout.strip():
                    info[key] = stdout.strip()
            except Exception:
                pass

        # Get IMEI
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'service', 'call', 'iphonesubinfo', '1']
            )
            if code == 0:
                imei = ''.join(c for c in stdout if c.isdigit())[:15]
                if len(imei) == 15:
                    info['imei'] = imei
        except Exception:
            pass

        # Battery info
        info['battery'] = DeviceDetector._get_battery_info(device_id)

        # Storage info
        info['storage'] = DeviceDetector._get_storage_info(device_id)

        # Screen info
        info['screen'] = DeviceDetector._get_screen_info(device_id)

        return info

    @staticmethod
    def _check_adb_ready(device_id: str) -> bool:
        """Check whether the device responds to ADB shell commands."""
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.serialno']
            )
            return code == 0 and bool(stdout.strip())
        except Exception:
            return False

    @staticmethod
    def _parse_adb_listing(parts: List[str]) -> Dict[str, str]:
        """Parse metadata from adb devices -l output."""
        info = {}
        for part in parts:
            if ':' not in part:
                continue
            key, value = part.split(':', 1)
            key = key.strip().lower()
            if key in {"product", "model", "device", "transport_id"}:
                info[key] = value.strip()
        return info

    @staticmethod
    def _get_battery_info(device_id: str) -> Dict:
        """Get battery information"""
        try:
            code, stdout, _ = SafeSubprocess.run(
                ['adb', '-s', device_id, 'shell', 'dumpsys', 'battery']
            )
            if code == 0:
                battery = {}
                for line in stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        battery[key] = value.strip()
                return battery
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_storage_info(device_id: str) -> Dict:
        """Get storage information"""
        try:
            code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'df', '/data'])
            if code == 0:
                lines = stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        return {'total': parts[1], 'used': parts[2], 'available': parts[3]}
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_screen_info(device_id: str) -> Dict:
        """Get screen information"""
        try:
            code, stdout, _ = SafeSubprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'size'])
            if code == 0:
                match = re.search(r'(\d+)x(\d+)', stdout)
                if match:
                    return {'width': match.group(1), 'height': match.group(2)}
        except Exception:
            pass
        return {}

    @staticmethod
    def _detect_fastboot() -> List[Dict[str, Any]]:
        """Detect fastboot devices"""
        devices = []
        try:
            code, stdout, _ = SafeSubprocess.run(['fastboot', 'devices'])
            if code == 0:
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            device_id = parts[0]
                            device = {'id': device_id, 'mode': 'fastboot', 'status': parts[1]}
                            metadata, error = DeviceDetector._get_fastboot_metadata(device_id)
                            if metadata:
                                device['fastboot_vars'] = metadata
                                DeviceDetector._normalize_fastboot_metadata(device, metadata)
                            if error:
                                device['fastboot_metadata_error'] = error
                            devices.append(device)
        except Exception:
            pass
        return devices

    @staticmethod
    def _get_fastboot_metadata(device_id: str) -> tuple[Dict[str, str], str | None]:
        """Fetch and parse fastboot getvar metadata."""
        try:
            code, stdout, stderr = SafeSubprocess.run(
                ['fastboot', '-s', device_id, 'getvar', 'all'],
                timeout=Config.TIMEOUT_SHORT,
            )
        except Exception as exc:
            return {}, str(exc)

        output = "\n".join(part for part in (stdout, stderr) if part).strip()
        metadata = DeviceDetector._parse_fastboot_metadata(output)
        error = None
        if code != 0:
            error = (stderr or stdout).strip() or "fastboot getvar failed"
        elif not metadata and output:
            error = output
        return metadata, error

    @staticmethod
    def _parse_fastboot_metadata(output: str) -> Dict[str, str]:
        """Parse fastboot getvar output into metadata."""
        metadata: Dict[str, str] = {}
        for line in output.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            cleaned = re.sub(r"^\([^)]+\)\s*", "", cleaned)
            if cleaned.lower().startswith("all:"):
                cleaned = cleaned[4:].strip()
            if cleaned.lower().startswith("finished") or cleaned.lower().startswith("total time"):
                continue
            match = re.match(r"([A-Za-z0-9_.-]+)\s*:\s*(.*)", cleaned)
            if not match:
                continue
            key = match.group(1).strip().lower()
            value = match.group(2).strip().strip("'\"")
            if not key or not value:
                continue
            metadata[key] = value
        return metadata

    @staticmethod
    def _normalize_fastboot_metadata(device: Dict[str, Any], metadata: Dict[str, str]) -> None:
        """Populate common device fields from fastboot metadata."""
        field_map = {
            "manufacturer": ["manufacturer", "brand", "oem", "vendor", "product-manufacturer"],
            "model": ["model", "product-model"],
            "product": ["product", "product-name"],
            "device": ["device", "product-device"],
            "bootloader": ["bootloader", "version-bootloader"],
        }

        for target, keys in field_map.items():
            if device.get(target):
                continue
            for key in keys:
                value = metadata.get(key)
                if value:
                    device[target] = value
                    break

    @staticmethod
    def _detect_usb_modes() -> List[Dict[str, Any]]:
        """Detect USB devices in low-level modes (EDL/preloader/download)."""
        devices: List[Dict[str, Any]] = []
        try:
            code, stdout, _ = SafeSubprocess.run(["lsusb"])
            if code == 0:
                for line in stdout.strip().split("\n"):
                    if "ID" not in line:
                        continue
                    parts = line.split()
                    try:
                        id_index = parts.index("ID")
                    except ValueError:
                        continue
                    if id_index + 1 >= len(parts):
                        continue
                    usb_id = parts[id_index + 1].strip()
                    if ":" not in usb_id:
                        continue
                    vid, pid = usb_id.split(":", 1)
                    mode = DeviceDetector._classify_usb_mode(vid.lower(), pid.lower())
                    if not mode:
                        continue
                    devices.append(
                        {
                            "id": f"usb-{usb_id.lower()}",
                            "mode": mode,
                            "status": "detected",
                            "usb_vid": vid.lower(),
                            "usb_pid": pid.lower(),
                            "usb_id": usb_id.lower(),
                        }
                    )
        except Exception:
            pass
        return devices

    @staticmethod
    def _classify_usb_mode(vid: str, pid: str) -> str | None:
        """Classify USB VID/PID into a known chipset mode."""
        if vid == "05c6" and pid in {"9008", "900e"}:
            return "edl"
        if vid == "0e8d" and pid in {"2000", "2001"}:
            return "preloader"
        if vid == "0e8d" and pid == "0003":
            return "bootrom"
        if vid == "04e8" and pid in {"685d", "6860"}:
            return "download"
        return None

    @staticmethod
    def _attach_chipset_metadata(device: Dict[str, Any]) -> None:
        """Populate chipset detection metadata into the device record."""
        detection = detect_chipset_for_device({k: str(v) for k, v in device.items()})
        if not detection:
            return
        device["chipset"] = detection.chipset
        device["chipset_vendor"] = detection.vendor
        device["chipset_mode"] = detection.mode
        device["chipset_confidence"] = detection.confidence
        device["chipset_notes"] = list(detection.notes)
        device["chipset_metadata"] = detection.metadata
