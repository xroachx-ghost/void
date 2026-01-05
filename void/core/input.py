"""
Input event injection for Android devices.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .utils import SafeSubprocess


class InputController:
    """Input event injection"""

    @staticmethod
    def send_text(device_id: str, text: str) -> bool:
        """Send text input to device"""
        # Escape special characters
        text = text.replace(" ", "%s")
        code, _, _ = SafeSubprocess.run(["adb", "-s", device_id, "shell", "input", "text", text])
        return code == 0

    @staticmethod
    def send_keyevent(device_id: str, keycode: str) -> bool:
        """Send key event to device

        Args:
            device_id: Device identifier
            keycode: Key code (e.g., 'KEYCODE_HOME', 'KEYCODE_BACK', '3')
        """
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "input", "keyevent", keycode]
        )
        return code == 0

    @staticmethod
    def tap(device_id: str, x: int, y: int) -> bool:
        """Tap at coordinates"""
        code, _, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "input", "tap", str(x), str(y)]
        )
        return code == 0

    @staticmethod
    def swipe(device_id: str, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """Swipe from one point to another

        Args:
            device_id: Device identifier
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration: Duration in milliseconds
        """
        code, _, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "input",
                "swipe",
                str(x1),
                str(y1),
                str(x2),
                str(y2),
                str(duration),
            ]
        )
        return code == 0

    @staticmethod
    def open_url(device_id: str, url: str) -> bool:
        """Open URL in device browser"""
        code, _, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "am",
                "start",
                "-a",
                "android.intent.action.VIEW",
                "-d",
                url,
            ]
        )
        return code == 0

    @staticmethod
    def press_home(device_id: str) -> bool:
        """Press Home button"""
        return InputController.send_keyevent(device_id, "KEYCODE_HOME")

    @staticmethod
    def press_back(device_id: str) -> bool:
        """Press Back button"""
        return InputController.send_keyevent(device_id, "KEYCODE_BACK")

    @staticmethod
    def press_menu(device_id: str) -> bool:
        """Press Menu button"""
        return InputController.send_keyevent(device_id, "KEYCODE_MENU")

    @staticmethod
    def press_power(device_id: str) -> bool:
        """Press Power button"""
        return InputController.send_keyevent(device_id, "KEYCODE_POWER")

    @staticmethod
    def volume_up(device_id: str) -> bool:
        """Press Volume Up button"""
        return InputController.send_keyevent(device_id, "KEYCODE_VOLUME_UP")

    @staticmethod
    def volume_down(device_id: str) -> bool:
        """Press Volume Down button"""
        return InputController.send_keyevent(device_id, "KEYCODE_VOLUME_DOWN")
