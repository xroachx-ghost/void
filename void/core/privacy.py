from __future__ import annotations

import re
from typing import Any

from ..config import Config

SENSITIVE_FIELDS = {"imei", "serial", "fingerprint"}

_MESSAGE_PATTERN = re.compile(r"(?i)\b(imei|serial|fingerprint)\b\s*[:=]\s*([^\s,;]+)")


def should_collect(field: str) -> bool:
    """Return True when collection is allowed for a sensitive field."""
    field = field.lower()
    if field == "imei":
        return Config.COLLECT_IMEI
    if field == "serial":
        return Config.COLLECT_SERIAL
    if field == "fingerprint":
        return Config.COLLECT_FINGERPRINT
    return True


def should_store(field: str) -> bool:
    """Return True when storage is allowed for a sensitive field."""
    field = field.lower()
    if field == "imei":
        return Config.STORE_IMEI
    if field == "serial":
        return Config.STORE_SERIAL
    if field == "fingerprint":
        return Config.STORE_FINGERPRINT
    return True


def mask_value(value: Any, keep: int = 4) -> str:
    """Mask sensitive values while keeping the last few characters visible."""
    if value is None:
        return ""
    text = str(value)
    if not text:
        return text
    if len(text) <= keep:
        return "*" * len(text)
    return f"{'*' * (len(text) - keep)}{text[-keep:]}"


def redact_device_info(device_info: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy of device info."""
    redacted = dict(device_info)
    for field in SENSITIVE_FIELDS:
        if field in redacted and not should_store(field):
            redacted[field] = mask_value(redacted[field])
    return redacted


def redact_event_data(data: Any) -> Any:
    """Recursively redact sensitive fields from analytics or report payloads."""
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for key, value in data.items():
            if key in SENSITIVE_FIELDS and not should_store(key):
                cleaned[key] = mask_value(value)
            else:
                cleaned[key] = redact_event_data(value)
        return cleaned
    if isinstance(data, list):
        return [redact_event_data(item) for item in data]
    return data


def redact_message(message: str) -> str:
    """Mask sensitive identifiers in log messages when storage is disabled."""

    def _replace(match: re.Match[str]) -> str:
        field = match.group(1)
        value = match.group(2)
        if should_store(field):
            return match.group(0)
        return f"{field}={mask_value(value)}"

    return _MESSAGE_PATTERN.sub(_replace, message)
