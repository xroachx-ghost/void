"""
VOID Telemetry System

Opt-in privacy-first analytics and crash reporting.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ annotations

import hashlib
import json
import platform
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TelemetryManager:
    """
    Privacy-first telemetry and analytics system.
    
    Features:
    - Opt-in only (disabled by default)
    - Anonymous usage statistics
    - Crash reporting
    - No PII collection
    - Clear opt-out mechanism
    - Local storage with user control
    """
    
    CONFIG_FILE = Path.home() / ".void" / "telemetry.json"
    TELEMETRY_ENDPOINT = "https://telemetry.roach-labs.com/api/v1/events"
    
    def __init__(self):
        """Initialize telemetry manager"""
        self.config_file = self.CONFIG_FILE
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.session_id = str(uuid.uuid4())
        self.anonymous_id = self._get_or_create_anonymous_id()
    
    def _load_config(self) -> Dict:
        """Load telemetry configuration"""
        if not self.config_file.exists():
            # Default: telemetry disabled
            default_config = {
                "enabled": False,
                "crash_reporting": False,
                "usage_stats": False,
                "opted_in_at": None,
                "last_prompted": None,
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"enabled": False}
    
    def _save_config(self, config: Dict):
        """Save telemetry configuration"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save telemetry config: {e}")
    
    def _get_or_create_anonymous_id(self) -> str:
        """
        Get or create anonymous user ID.
        
        This is a stable anonymous identifier that does not contain PII.
        Uses SHA-256 hash of machine ID.
        """
        if "anonymous_id" in self.config:
            return self.config["anonymous_id"]
        
        # Generate anonymous ID from machine info
        machine_id = str(uuid.getnode())  # MAC address
        anonymous_id = hashlib.sha256(machine_id.encode()).hexdigest()[:16]
        
        self.config["anonymous_id"] = anonymous_id
        self._save_config(self.config)
        
        return anonymous_id
    
    def is_enabled(self) -> bool:
        """Check if telemetry is enabled"""
        return self.config.get("enabled", False)
    
    def opt_in(self, crash_reporting: bool = True, usage_stats: bool = True):
        """
        Opt in to telemetry collection.
        
        Args:
            crash_reporting: Enable crash reports
            usage_stats: Enable usage statistics
        """
        self.config["enabled"] = True
        self.config["crash_reporting"] = crash_reporting
        self.config["usage_stats"] = usage_stats
        self.config["opted_in_at"] = datetime.now().isoformat()
        self._save_config(self.config)
        
        # Send opt-in event
        self._send_event("telemetry_opt_in", {
            "crash_reporting": crash_reporting,
            "usage_stats": usage_stats,
        })
    
    def opt_out(self):
        """Opt out of telemetry collection"""
        # Send opt-out event before disabling
        if self.is_enabled():
            self._send_event("telemetry_opt_out", {})
        
        self.config["enabled"] = False
        self.config["crash_reporting"] = False
        self.config["usage_stats"] = False
        self.config["opted_out_at"] = datetime.now().isoformat()
        self._save_config(self.config)
    
    def get_status(self) -> Dict:
        """Get current telemetry status"""
        return {
            "enabled": self.is_enabled(),
            "crash_reporting": self.config.get("crash_reporting", False),
            "usage_stats": self.config.get("usage_stats", False),
            "anonymous_id": self.anonymous_id,
            "opted_in_at": self.config.get("opted_in_at"),
        }
    
    def track_event(self, event_name: str, properties: Dict[str, Any] = None):
        """
        Track a usage event (if opted in).
        
        Args:
            event_name: Name of the event
            properties: Event properties (no PII)
        """
        if not self.is_enabled() or not self.config.get("usage_stats", False):
            return
        
        self._send_event(event_name, properties or {})
    
    def track_feature_usage(self, feature_name: str):
        """Track feature usage"""
        self.track_event("feature_used", {
            "feature": feature_name,
        })
    
    def track_command_execution(self, command: str, success: bool):
        """Track command execution"""
        self.track_event("command_executed", {
            "command": command,
            "success": success,
        })
    
    def report_crash(self, error: Exception, context: Dict[str, Any] = None):
        """
        Report a crash/error (if opted in).
        
        Args:
            error: The exception that occurred
            context: Additional context (no PII)
        """
        if not self.is_enabled() or not self.config.get("crash_reporting", False):
            return
        
        # Collect error information
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
        }
        
        self._send_event("crash", error_info)
    
    def _send_event(self, event_name: str, properties: Dict[str, Any]):
        """Send event to telemetry server"""
        if not REQUESTS_AVAILABLE:
            return  # Silently skip if requests not available
        
        try:
            # Build event payload
            payload = {
                "event": event_name,
                "anonymous_id": self.anonymous_id,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "properties": properties,
                "system": self._get_system_info(),
            }
            
            # Send to server (with timeout)
            response = requests.post(
                self.TELEMETRY_ENDPOINT,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
        except Exception:
            # Silently fail - don't interrupt user experience
            pass
    
    def _get_system_info(self) -> Dict[str, Any]:
        """
        Get non-identifying system information.
        
        This includes only general system info, no PII.
        """
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
            "architecture": platform.machine(),
            "void_version": self._get_void_version(),
        }
    
    def _get_void_version(self) -> str:
        """Get Void Suite version"""
        try:
            from . import __version__
            return __version__
        except Exception:
            return "unknown"
    
    def should_prompt_opt_in(self) -> bool:
        """Check if we should prompt user to opt in"""
        # Don't prompt if already decided
        if self.config.get("enabled") or self.config.get("opted_out_at"):
            return False
        
        # Check if we've prompted recently
        last_prompted = self.config.get("last_prompted")
        if last_prompted:
            from datetime import datetime, timedelta
            last_prompt_date = datetime.fromisoformat(last_prompted)
            # Don't prompt more than once per 7 days
            if datetime.now() - last_prompt_date < timedelta(days=7):
                return False
        
        return True
    
    def mark_prompted(self):
        """Mark that we've prompted the user"""
        self.config["last_prompted"] = datetime.now().isoformat()
        self._save_config(self.config)


# Global telemetry instance
_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry() -> TelemetryManager:
    """Get global telemetry manager instance"""
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager


def track_event(event_name: str, properties: Dict[str, Any] = None):
    """Convenience function to track an event"""
    get_telemetry().track_event(event_name, properties)


def report_crash(error: Exception, context: Dict[str, Any] = None):
    """Convenience function to report a crash"""
    get_telemetry().report_crash(error, context)


def prompt_opt_in_cli():
    """Prompt user to opt in via CLI"""
    telemetry = get_telemetry()
    
    if not telemetry.should_prompt_opt_in():
        return
    
    print("\n" + "=" * 70)
    print("📊 Help Improve Void Suite")
    print("=" * 70)
    print("""
Void Suite can collect anonymous usage data to help improve the software.

What we collect (if you opt in):
  ✓ Feature usage (which commands you use)
  ✓ Error reports (to fix bugs faster)
  ✓ System info (OS, Python version)

What we DON'T collect:
  ✗ Personal information (names, emails)
  ✗ Device data (IMEIs, serial numbers)
  ✗ File contents or customer data
  ✗ Anything identifiable

Your privacy is important. Telemetry is:
  • Completely optional (opt-in)
  • Anonymous (no PII)
  • Secure (HTTPS only)
  • Transparent (see code in void/telemetry.py)

You can opt out anytime: void telemetry disable
    """)
    
    try:
        response = input("Enable telemetry? [y/N]: ").strip().lower()
        
        if response in ["y", "yes"]:
            telemetry.opt_in(crash_reporting=True, usage_stats=True)
            print("\n✓ Telemetry enabled. Thank you for helping improve Void Suite!")
        else:
            telemetry.mark_prompted()
            print("\n✗ Telemetry disabled. You can enable it later with: void telemetry enable")
    
    except (EOFError, KeyboardInterrupt):
        telemetry.mark_prompted()
        print("\n✗ Skipped telemetry prompt.")
    
    print("=" * 70 + "\n")
