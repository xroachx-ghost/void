"""
Chipset abstraction layer for device workflows.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from .base import BaseChipsetProtocol, ChipsetActionResult, ChipsetDetection
from .dispatcher import (
    detect_chipset_for_device,
    enter_device_mode,
    enter_chipset_mode,
    recover_chipset_device,
    resolve_chipset,
)
from .generic import GenericChipset
from .mediatek import MediaTekChipset
from .qualcomm import QualcommChipset
from .samsung import SamsungExynosChipset

__all__ = [
    "BaseChipsetProtocol",
    "ChipsetActionResult",
    "ChipsetDetection",
    "detect_chipset_for_device",
    "enter_device_mode",
    "enter_chipset_mode",
    "recover_chipset_device",
    "resolve_chipset",
    "GenericChipset",
    "MediaTekChipset",
    "QualcommChipset",
    "SamsungExynosChipset",
]
