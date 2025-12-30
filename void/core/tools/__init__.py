"""
Tools module initialization.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from __future__ import annotations

from .android import (
    android_driver_hints,
    check_android_tools,
    check_usb_debugging_status,
    install_android_platform_tools,
    resolve_android_fallback,
)
from .mediatek import (
    build_sp_flash_script_command,
    check_mediatek_tools,
    resolve_mediatek_recovery_tool,
)
from .qualcomm import check_qualcomm_tools, resolve_qualcomm_recovery_tool

__all__ = [
    "build_sp_flash_script_command",
    "android_driver_hints",
    "check_android_tools",
    "check_usb_debugging_status",
    "install_android_platform_tools",
    "check_mediatek_tools",
    "check_qualcomm_tools",
    "resolve_android_fallback",
    "resolve_mediatek_recovery_tool",
    "resolve_qualcomm_recovery_tool",
]
