"""
Setup wizard for Void.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .utils import SafeSubprocess


@dataclass
class SetupWizardDiagnostics:
    """Collect boot/setup wizard diagnostics for a connected Android device."""

    _PACKAGE_CANDIDATES = (
        "com.google.android.setupwizard",
        "com.android.setupwizard",
        "com.samsung.android.setupwizard",
        "com.sec.android.app.setupwizard",
        "com.htc.android.setupwizard",
        "com.motorola.setup",
        "com.motorola.setupwizard",
    )

    @staticmethod
    def _parse_setting(raw: str) -> Optional[bool]:
        value = raw.strip().lower()
        if value in {"1", "true", "yes"}:
            return True
        if value in {"0", "false", "no"}:
            return False
        return None

    @staticmethod
    def _parse_boot_completed(raw: str) -> Optional[bool]:
        value = raw.strip().lower()
        if value in {"1", "y", "yes", "true"}:
            return True
        if value in {"0", "n", "no", "false"}:
            return False
        return None

    @classmethod
    def _detect_resumed_activity(cls, device_id: str) -> Optional[str]:
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "activity", "activities"]
        )
        if code != 0:
            return None

        for line in stdout.splitlines():
            if not any(
                key in line
                for key in ("mResumedActivity", "topResumedActivity", "mFocusedActivity")
            ):
                continue
            return line.strip()
        return None

    @classmethod
    def _detect_setup_packages(cls, device_id: str) -> List[str]:
        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "cmd", "package", "list", "packages"]
        )
        if code != 0:
            return []
        packages = []
        for line in stdout.splitlines():
            if not line.startswith("package:"):
                continue
            package = line.split("package:", 1)[-1].strip()
            if package in cls._PACKAGE_CANDIDATES or "setupwizard" in package:
                packages.append(package)
        return packages

    @classmethod
    def _detect_wizard_activity(cls, activity_line: Optional[str]) -> Optional[str]:
        if not activity_line:
            return None
        if any(package in activity_line for package in cls._PACKAGE_CANDIDATES):
            match = re.search(r"(com\.[\w.]+setupwizard\w*)", activity_line)
            return match.group(1) if match else activity_line
        return None

    @classmethod
    def analyze(cls, device_id: str) -> Dict[str, Any]:
        boot_completed = None
        user_setup_complete = None

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "getprop", "sys.boot_completed"]
        )
        if code == 0:
            boot_completed = cls._parse_boot_completed(stdout)

        code, stdout, _ = SafeSubprocess.run(
            [
                "adb",
                "-s",
                device_id,
                "shell",
                "settings",
                "get",
                "secure",
                "user_setup_complete",
            ]
        )
        if code == 0:
            user_setup_complete = cls._parse_setting(stdout)

        resumed_activity = cls._detect_resumed_activity(device_id)
        setup_packages = cls._detect_setup_packages(device_id)
        wizard_activity = cls._detect_wizard_activity(resumed_activity)

        wizard_running = False
        if wizard_activity:
            wizard_running = True
        elif resumed_activity and "setupwizard" in resumed_activity.lower():
            wizard_running = True

        status = "unknown"
        if boot_completed is False:
            status = "boot incomplete"
        elif boot_completed is True:
            if wizard_running and user_setup_complete is True:
                status = "wizard loop suspected"
            elif user_setup_complete is False:
                status = "setup incomplete"
            elif wizard_running:
                status = "wizard loop suspected"
            elif user_setup_complete is True:
                status = "setup complete"

        return {
            "boot_completed": boot_completed,
            "user_setup_complete": user_setup_complete,
            "resumed_activity": resumed_activity,
            "setup_packages": setup_packages,
            "wizard_activity": wizard_activity,
            "wizard_running": wizard_running,
            "status": status,
        }
