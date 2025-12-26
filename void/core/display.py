from __future__ import annotations

import importlib
import importlib.util
import re
from typing import Any, Dict, Optional

from .screen import ScreenCapture
from .utils import SafeSubprocess


def _parse_screen_state(power_output: str) -> tuple[Optional[str], Optional[str]]:
    screen_state = None
    display_power = None

    for line in power_output.splitlines():
        stripped = line.strip()
        if "Display Power" in stripped and "state=" in stripped:
            display_power = stripped.split("Display Power:", 1)[-1].strip()
            state_match = re.search(r"state=([A-Za-z]+)", stripped)
            if state_match:
                state = state_match.group(1).lower()
                screen_state = "on" if state == "on" else "off" if state == "off" else state
        elif "mScreenOn=" in stripped:
            value = stripped.split("mScreenOn=", 1)[-1].split()[0].strip().lower()
            screen_state = "on" if value == "true" else "off" if value == "false" else value
        elif "mWakefulness=" in stripped and screen_state is None:
            value = stripped.split("mWakefulness=", 1)[-1].split()[0].strip().lower()
            if value in {"awake", "dreaming"}:
                screen_state = "on"
            elif value in {"asleep", "dozing"}:
                screen_state = "off"

    return screen_state, display_power


def _parse_display_info(display_output: str) -> tuple[Optional[str], Optional[str]]:
    brightness = None
    refresh_rate = None

    for line in display_output.splitlines():
        stripped = line.strip()
        if brightness is None:
            brightness_match = re.search(r"brightness=([0-9.]+)", stripped)
            if brightness_match:
                brightness = brightness_match.group(1)
            elif any(key in stripped for key in ("mScreenBrightnessSetting", "mScreenBrightness", "mBrightness")):
                if "=" in stripped:
                    brightness = stripped.split("=", 1)[-1].strip()
                elif ":" in stripped:
                    brightness = stripped.split(":", 1)[-1].strip()
        if refresh_rate is None:
            refresh_match = re.search(r"refreshRate=([0-9.]+)", stripped)
            if refresh_match:
                refresh_rate = refresh_match.group(1)
            elif "mRefreshRate" in stripped:
                if "=" in stripped:
                    refresh_rate = stripped.split("=", 1)[-1].strip()
                elif ":" in stripped:
                    refresh_rate = stripped.split(":", 1)[-1].strip()
        if brightness is not None and refresh_rate is not None:
            break

    return brightness, refresh_rate


def _pillow_available() -> bool:
    return importlib.util.find_spec("PIL") is not None


class DisplayAnalyzer:
    """Display and framebuffer diagnostics."""

    @staticmethod
    def analyze(device_id: str) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {
            "screen_state": None,
            "display_power": None,
            "display_brightness": None,
            "refresh_rate": None,
            "surfaceflinger_ok": None,
            "surfaceflinger_source": None,
            "black_frame_detected": None,
            "screenshot_path": None,
            "screenshot_analysis": None,
        }

        code, power_out, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "power"]
        )
        if code == 0:
            screen_state, display_power = _parse_screen_state(power_out)
            analysis["screen_state"] = screen_state
            analysis["display_power"] = display_power

        code, display_out, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "display"]
        )
        if code == 0:
            brightness, refresh_rate = _parse_display_info(display_out)
            analysis["display_brightness"] = brightness
            analysis["refresh_rate"] = refresh_rate

        code, surface_out, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "SurfaceFlinger"]
        )
        source = "SurfaceFlinger"
        if code != 0 or not surface_out.strip():
            code, surface_out, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "shell", "dumpsys", "gfxinfo"]
            )
            source = "gfxinfo"
        analysis["surfaceflinger_ok"] = code == 0 and bool(surface_out.strip())
        analysis["surfaceflinger_source"] = source

        screenshot = ScreenCapture.take_screenshot(device_id)
        if screenshot.get("success"):
            analysis["screenshot_path"] = screenshot.get("path")
            if _pillow_available():
                image_module = importlib.import_module("PIL.Image")
                stat_module = importlib.import_module("PIL.ImageStat")
                with image_module.open(screenshot["path"]) as img:
                    rgb = img.convert("RGB")
                    stats = stat_module.Stat(rgb)
                mean = stats.mean
                avg = sum(mean) / 3 if mean else 0
                threshold = 10
                analysis["black_frame_detected"] = avg < threshold
                analysis["screenshot_analysis"] = {
                    "average_rgb": [round(channel, 2) for channel in mean],
                    "average_luminance": round(avg, 2),
                    "threshold": threshold,
                }
            else:
                analysis["screenshot_analysis"] = {
                    "note": "Pillow not installed; screenshot captured without pixel analysis.",
                }
        else:
            analysis["screenshot_analysis"] = {
                "error": screenshot.get("error", "Screenshot failed."),
            }

        return analysis
