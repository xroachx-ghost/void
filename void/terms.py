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
from .logging import get_logger, log_user_confirmation

TERMS_TEXT = (
    "By using Void, you agree to the Terms & Conditions and confirm you have "
    "authorization to access any connected device."
)

DESTRUCTIVE_ACTIONS = {
    "edl_flash": "EDL flash",
    "partition_dump": "partition dump",
}


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


def _requires_double_confirmation(action: str) -> bool:
    return action in DESTRUCTIVE_ACTIONS


def _action_label(action: str) -> str:
    return DESTRUCTIVE_ACTIONS.get(action, action.replace("_", " "))


def confirm_destructive_action_cli(
    action: str,
    device_id: str = "-",
    method: str = "-",
    interface: str = "cli",
) -> bool:
    """Confirm destructive actions on the CLI with explicit acknowledgement."""
    label = _action_label(action)
    prompt = (
        f"⚠️  Destructive action requested: {label}. "
        "Type 'confirm' to continue or anything else to cancel: "
    )
    response = input(prompt).strip().lower()
    confirmed = response == "confirm"
    log_user_confirmation(
        action,
        confirmed,
        device_id=device_id,
        method=method,
        interface=interface,
        step="primary",
    )
    if not confirmed:
        return False

    if _requires_double_confirmation(action):
        second_prompt = (
            f"Final confirmation required for {label}. "
            "Type 'I UNDERSTAND' to proceed: "
        )
        second_response = input(second_prompt).strip().lower()
        secondary_confirmed = second_response == "i understand"
        log_user_confirmation(
            action,
            secondary_confirmed,
            device_id=device_id,
            method=method,
            interface=interface,
            step="secondary",
        )
        return secondary_confirmed

    return True


def confirm_destructive_action_gui(
    messagebox,
    action: str,
    device_id: str = "-",
    method: str = "-",
    interface: str = "gui",
) -> bool:
    """Confirm destructive actions in the GUI with a secondary prompt."""
    label = _action_label(action)
    confirmed = messagebox.askyesno(
        "Confirm Destructive Action",
        f"This action will perform {label} on a connected device.\n\n"
        "Do you want to continue?",
    )
    log_user_confirmation(
        action,
        confirmed,
        device_id=device_id,
        method=method,
        interface=interface,
        step="primary",
    )
    if not confirmed:
        return False

    if _requires_double_confirmation(action):
        secondary = messagebox.askyesno(
            "Final Confirmation Required",
            f"{label} is highly destructive and may overwrite or expose data.\n\n"
            "I understand the risks and want to continue.",
        )
        log_user_confirmation(
            action,
            secondary,
            device_id=device_id,
            method=method,
            interface=interface,
            step="secondary",
        )
        return secondary

    return True
