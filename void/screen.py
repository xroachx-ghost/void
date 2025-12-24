"""Screen capture utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .config import Config
from .logger import logger
from .utils import SafeSubprocess


class ScreenCapture:
    """Screenshot and screen recording"""

    @staticmethod
    def take_screenshot(device_id: str) -> Dict[str, Any]:
        """Take screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{{device_id}}_{timestamp}.png"
        output_path = Config.EXPORTS_DIR / filename

        # Take screenshot on device
        device_path = f"/sdcard/{{filename}}"
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", device_path])

        if code == 0:
            # Pull to PC
            code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "pull", device_path, str(output_path)])

            # Clean up device
            SafeSubprocess.run(["adb", "-s", device_id, "shell", "rm", device_path])

            if code == 0 and output_path.exists():
                logger.log("success", "screen", f"Screenshot saved: {filename}")
                return {"success": True, "path": str(output_path), "size": output_path.stat().st_size}

        return {"success": False, "error": "Screenshot failed"}
