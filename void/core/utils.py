from __future__ import annotations

import subprocess
from typing import List, Tuple

from ..config import Config


class SafeSubprocess:
    """Safe subprocess execution"""

    @staticmethod
    def run(cmd: List[str], timeout: int = Config.TIMEOUT_SHORT) -> Tuple[int, str, str]:
        """Execute command safely"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as exc:
            return -1, "", str(exc)
