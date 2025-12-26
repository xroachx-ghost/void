from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional


class RomValidator:
    """Checksum utilities for ROM validation."""

    _ALGORITHMS = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }

    @staticmethod
    def calculate_checksum(path: Path, algorithm: str = "sha256") -> str:
        """Calculate checksum for a ROM file."""
        algo = RomValidator._ALGORITHMS.get(algorithm.lower())
        if not algo:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        digest = algo()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def infer_algorithm(checksum: str) -> str:
        """Infer algorithm based on checksum length."""
        length_map = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}
        return length_map.get(len(checksum), "sha256")

    @staticmethod
    def load_expected_checksum(checksum_input: str, rom_path: Optional[Path] = None) -> Optional[str]:
        """Load checksum from a literal string or checksum file."""
        candidate = checksum_input.strip()
        if not candidate:
            return None

        checksum_path = Path(candidate)
        if checksum_path.exists() and checksum_path.is_file():
            lines = checksum_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if rom_path:
                for line in lines:
                    if rom_path.name in line:
                        return line.split()[0]
            for line in lines:
                line = line.strip()
                if line:
                    return line.split()[0]
            return None

        return candidate

    @staticmethod
    def validate_checksum(
        rom_path: Path, checksum_input: str, algorithm: Optional[str] = None
    ) -> Dict[str, str | bool]:
        """Validate a ROM file checksum against an expected value."""
        expected = RomValidator.load_expected_checksum(checksum_input, rom_path)
        if not expected:
            return {
                "success": False,
                "message": "No checksum provided or checksum file was empty.",
            }

        algo = algorithm or RomValidator.infer_algorithm(expected)
        actual = RomValidator.calculate_checksum(rom_path, algo)
        success = actual.lower() == expected.lower()
        message = "Checksum matches." if success else "Checksum mismatch."
        return {
            "success": success,
            "message": message,
            "algorithm": algo,
            "expected": expected,
            "actual": actual,
        }
