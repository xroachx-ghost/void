"""
Startup wizard analysis.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .utils import SafeSubprocess


class StartupWizardAnalyzer:
    """Detect startup wizard state on a connected Android device."""

    _PACKAGE_CANDIDATES = [
        "com.google.android.setupwizard",
        "com.android.setupwizard",
        "com.samsung.android.setupwizard",
        "com.sec.android.app.setupwizard",
        "com.htc.android.setupwizard",
        "com.motorola.setup",
        "com.motorola.setupwizard",
    ]

    @staticmethod
    def _parse_setting(raw: str) -> Optional[bool]:
        value = raw.strip().lower()
        if value in {"1", "true", "yes"}:
            return True
        if value in {"0", "false", "no"}:
            return False
        return None

    @staticmethod
    def analyze(device_id: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "running": False,
            "active_package": None,
            "pid": None,
            "top_activity": None,
            "setup_complete": None,
            "device_provisioned": None,
            "installed_packages": [],
        }

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "list", "packages"]
        )
        installed = []
        if code == 0:
            for line in stdout.splitlines():
                if not line.startswith("package:"):
                    continue
                package = line.split("package:", 1)[-1].strip()
                if package in StartupWizardAnalyzer._PACKAGE_CANDIDATES:
                    installed.append(package)
        result["installed_packages"] = installed

        for package in installed or StartupWizardAnalyzer._PACKAGE_CANDIDATES:
            code, stdout, _ = SafeSubprocess.run(
                ["adb", "-s", device_id, "shell", "pidof", package]
            )
            if code == 0 and stdout.strip():
                result["running"] = True
                result["active_package"] = package
                result["pid"] = stdout.strip()
                break

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "dumpsys", "activity", "activities"]
        )
        if code == 0:
            for line in stdout.splitlines():
                if not any(
                    key in line
                    for key in ("mResumedActivity", "topResumedActivity", "mFocusedActivity")
                ):
                    continue
                if any(package in line for package in StartupWizardAnalyzer._PACKAGE_CANDIDATES):
                    result["top_activity"] = line.strip()
                    if result["active_package"] is None:
                        match = re.search(r"(com\.[\w.]+setupwizard\w*)", line)
                        if match:
                            result["active_package"] = match.group(1)
                        else:
                            result["active_package"] = next(
                                (
                                    pkg
                                    for pkg in StartupWizardAnalyzer._PACKAGE_CANDIDATES
                                    if pkg in line
                                ),
                                None,
                            )
                        result["running"] = True
                    break

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "get", "secure", "user_setup_complete"]
        )
        if code == 0:
            result["setup_complete"] = StartupWizardAnalyzer._parse_setting(stdout)

        code, stdout, _ = SafeSubprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "get", "global", "device_provisioned"]
        )
        if code == 0:
            result["device_provisioned"] = StartupWizardAnalyzer._parse_setting(stdout)

        return result
