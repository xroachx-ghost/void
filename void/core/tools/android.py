"""ADB/Fastboot tool wrappers."""

from __future__ import annotations

import platform

from .base import ToolSpec, check_tool_specs, first_available
from ..utils import SafeSubprocess, ToolCheckResult


ADB_SPEC = ToolSpec(name="adb", version_args=("version",), label="ADB")
FASTBOOT_SPEC = ToolSpec(name="fastboot", version_args=("--version",), label="Fastboot")
ANDROID_PLATFORM_TOOLS_URL = "https://developer.android.com/tools/releases/platform-tools"
ANDROID_DEV_OPTIONS_URL = "https://developer.android.com/studio/debug/dev-options"


def check_android_tools() -> list[ToolCheckResult]:
    """Return validation results for Android platform tools."""
    return check_tool_specs((ADB_SPEC, FASTBOOT_SPEC))


def resolve_android_fallback() -> tuple[str | None, list[ToolCheckResult]]:
    """Return the preferred available Android tool as a fallback."""
    results = check_android_tools()
    selected = first_available(results)
    return (selected.name if selected else None, results)


def check_usb_debugging_status(
    tools: list[ToolCheckResult] | None = None,
) -> dict[str, object]:
    """Check whether USB debugging is authorized for connected devices."""
    if tools is None:
        tools = check_android_tools()

    adb_result = next((tool for tool in tools if tool.name == "adb"), None)
    if not adb_result or not adb_result.available:
        return {
            "status": "warn",
            "message": "ADB not available to verify USB debugging.",
            "detail": "Install Android platform tools to check device authorization.",
            "links": [
                {"label": "Download Android platform tools", "url": ANDROID_PLATFORM_TOOLS_URL},
            ],
        }

    code, stdout, stderr = SafeSubprocess.run(["adb", "devices", "-l"])
    if code != 0:
        output = (stdout or stderr).strip()
        return {
            "status": "warn",
            "message": "ADB returned an error while checking devices.",
            "detail": output or "Unable to query adb devices.",
            "links": [
                {"label": "Android platform tools docs", "url": ANDROID_PLATFORM_TOOLS_URL},
            ],
        }

    statuses: list[str] = []
    for line in stdout.splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            statuses.append(parts[1].lower())

    if not statuses:
        return {
            "status": "warn",
            "message": "No ADB devices detected.",
            "detail": "Connect a device with USB debugging enabled and recheck.",
            "links": [
                {"label": "Enable USB debugging", "url": ANDROID_DEV_OPTIONS_URL},
            ],
        }
    if "unauthorized" in statuses:
        return {
            "status": "fail",
            "message": "USB debugging authorization required.",
            "detail": "Unlock the device and accept the RSA prompt.",
            "links": [
                {"label": "Enable USB debugging", "url": ANDROID_DEV_OPTIONS_URL},
            ],
        }
    if "offline" in statuses:
        return {
            "status": "fail",
            "message": "ADB reports the device as offline.",
            "detail": "Reconnect the USB cable and restart ADB.",
            "links": [
                {"label": "Android platform tools docs", "url": ANDROID_PLATFORM_TOOLS_URL},
            ],
        }
    if "device" in statuses:
        return {
            "status": "pass",
            "message": "USB debugging authorized.",
            "detail": "At least one device is responding over ADB.",
            "links": [],
        }
    return {
        "status": "warn",
        "message": "ADB devices detected but not fully ready.",
        "detail": "Confirm USB debugging and authorization prompts.",
        "links": [
            {"label": "Enable USB debugging", "url": ANDROID_DEV_OPTIONS_URL},
        ],
    }


def android_driver_hints() -> dict[str, object]:
    """Return OS-specific USB driver guidance."""
    system = platform.system().lower()
    if system == "windows":
        return {
            "status": "warn",
            "message": "Windows USB drivers may be required for ADB/Fastboot.",
            "detail": "Install OEM or Google USB drivers if devices are missing.",
            "links": [
                {"label": "Windows USB driver setup", "url": "https://developer.android.com/studio/run/win-usb"},
                {"label": "OEM USB drivers", "url": "https://developer.android.com/studio/run/oem-usb"},
            ],
        }
    if system == "darwin":
        return {
            "status": "pass",
            "message": "macOS does not require USB drivers.",
            "detail": "Install Android platform tools and connect via USB.",
            "links": [
                {"label": "Android platform tools docs", "url": ANDROID_PLATFORM_TOOLS_URL},
            ],
        }
    if system == "linux":
        return {
            "status": "warn",
            "message": "Linux may require udev rules for USB access.",
            "detail": "Add udev rules and reload to allow ADB/Fastboot access.",
            "links": [
                {"label": "Linux udev rules guidance", "url": "https://developer.android.com/studio/run/device#setting-up"},
            ],
        }
    return {
        "status": "warn",
        "message": "Install the required USB drivers for your OS.",
        "detail": "Ensure Android platform tools are installed.",
        "links": [
            {"label": "Android platform tools docs", "url": ANDROID_PLATFORM_TOOLS_URL},
        ],
    }
