"""
VOID TERMS

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import json
from pathlib import Path
from .config import Config
from .logging import get_logger

TERMS_TEXT = (
    "By using Void, you agree to the Terms & Conditions and confirm you have "
    "authorization to access any connected device."
)


def terms_path() -> Path:
    return Config.BASE_DIR / "terms.json"


def ensure_terms_acceptance_cli() -> bool:
    """Require user acceptance of Terms & Conditions before use (CLI)."""
    logger = get_logger(__name__)
    terms_file = terms_path()
    if terms_file.exists():
        try:
            data = json.loads(terms_file.read_text())
            if data.get("accepted") is True:
                return True
        except Exception:
            pass

    logger.warning(
        "TERMS & CONDITIONS REQUIRED",
        extra={"category": "terms", "device_id": "-", "method": "-"},
    )
    logger.info(
        TERMS_TEXT,
        extra={"category": "terms", "device_id": "-", "method": "-"},
    )
    response = input("Type 'accept' to continue or anything else to exit: ").strip().lower()
    if response != "accept":
        logger.info(
            "Terms not accepted. Exiting.",
            extra={"category": "terms", "device_id": "-", "method": "-"},
        )
        return False

    terms_file.parent.mkdir(parents=True, exist_ok=True)
    terms_file.write_text(json.dumps({"accepted": True}))
    return True


def ensure_terms_acceptance_gui(messagebox) -> bool:
    """Require acceptance of Terms & Conditions before use (GUI)."""
    terms_file = terms_path()
    if terms_file.exists():
        try:
            data = json.loads(terms_file.read_text())
            if data.get("accepted") is True:
                return True
        except Exception:
            pass

    accepted = messagebox.askyesno(
        "Terms & Conditions",
        f"{TERMS_TEXT}\n\nDo you accept the Terms & Conditions?",
    )
    if not accepted:
        return False

    terms_file.parent.mkdir(parents=True, exist_ok=True)
    terms_file.write_text(json.dumps({"accepted": True}))
    return True
