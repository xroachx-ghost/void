"""UI helpers and optional Rich integration."""
from __future__ import annotations

import importlib.util

if importlib.util.find_spec("rich") is not None:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.tree import Tree
    from rich.live import Live

    RICH_AVAILABLE = True
else:  # pragma: no cover - optional dependency
    Console = None
    Table = None
    Panel = None
    Progress = None
    SpinnerColumn = None
    TextColumn = None
    BarColumn = None
    Tree = None
    Live = None
    RICH_AVAILABLE = False


def build_banner(version: str, codename: str, features_count: int = 200) -> str:
    """Build the CLI banner."""
    return f"""
╔══════════════════════════════════════════════════════════════╗
║  VOID FRP SUITE v{version} - {codename}                    ║
║  Ultimate Android Toolkit - {features_count}+ Automated Features      ║
╚══════════════════════════════════════════════════════════════╝

✨ All features work automatically - zero manual setup required!

Type 'help' to see all available commands.
"""


HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║                   VOID FRP SUITE - HELP                      ║
╚══════════════════════════════════════════════════════════════╝

📋 AVAILABLE COMMANDS:

DEVICE MANAGEMENT:
  devices                          - List all connected devices
  info <device_id>                 - Show detailed device info
  
BACKUP & DATA:
  backup <device_id>               - Create automated backup
  recover <device_id> <type>       - Recover data (contacts/sms)
  screenshot <device_id>           - Take screenshot
  
APP MANAGEMENT:
  apps <device_id> [filter]        - List apps (system/user/all)
  
FILE OPERATIONS:
  files <device_id> list [path]    - List files
  files <device_id> pull <path>    - Pull file from device
  
ANALYSIS:
  analyze <device_id>              - Performance analysis
  report <device_id>               - Generate full report
  logcat <device_id> [tag]         - View real-time logs
  
TWEAKS:
  tweak <device_id> <type> <value> - System tweaks
    Types: dpi, animation, timeout
  
FRP BYPASS:
  execute <method> <device_id>     - Execute bypass method
    Methods: adb_shell_reset, fastboot_erase, etc.
  
SYSTEM:
  stats                            - Show suite statistics
  monitor                          - Show system monitor
  help                             - Show this help
  exit                             - Exit suite

🎯 EXAMPLES:

  void> devices
  void> info emulator-5554
  void> backup emulator-5554
  void> screenshot emulator-5554
  void> apps emulator-5554 user
  void> analyze emulator-5554
  void> recover emulator-5554 contacts
  void> tweak emulator-5554 dpi 320
  void> report emulator-5554
  void> execute adb_shell_reset emulator-5554

💡 TIP: All commands work automatically with no setup required!

╚══════════════════════════════════════════════════════════════╝
"""
