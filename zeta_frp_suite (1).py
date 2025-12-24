#!/usr/bin/env python3
from __future__ import annotations

"""
███████╗███████╗████████╗ █████╗     ███████╗██████╗ ██████╗ 
██╔════╝██╔════╝╚══██╔══╝██╔══██╗    ██╔════╝██╔══██╗██╔══██╗
█████╗  █████╗     ██║   ███████║    █████╗  ██████╔╝██████╔╝
██╔══╝  ██╔════╝     ██║   ██╔══██║    ██╔══╝  ██╔══██╗██╔══██╗
██║     ███████╗   ██║   ██║  ██║    ███████╗██║  ██║██║  ██║
╚═╝     ╚══════╝   ╚═╝   ╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝

VOID FRP SUITE v6.0.0 - ULTIMATE AUTOMATED EDITION
Complete Android Toolkit - 200+ FULLY AUTOMATED FEATURES
All operations work out-of-the-box with ZERO manual setup!
"""

import sys

from void.main import main
from void.monitor import monitor


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        monitor.stop()
        sys.exit(0)
    except Exception as exc:
        print(f"\n💀 Critical Error: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
