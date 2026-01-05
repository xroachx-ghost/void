"""
VOID CRYPTOGRAPHY

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import hashlib
import logging
import secrets

from .config import Config

try:
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Protocol.KDF import PBKDF2

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class CryptoSuite:
    """Cryptographic operations."""

    @staticmethod
    def hash_sha256(data: bytes) -> str:
        """SHA-256 hash."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        """Generate random key."""
        return secrets.token_bytes(length)

    @staticmethod
    def encrypt_aes(data: bytes, key: bytes) -> bytes:
        """AES encryption."""
        if not CRYPTO_AVAILABLE:
            if Config.ALLOW_INSECURE_CRYPTO:
                logger.warning(
                    "Insecure XOR fallback used for AES encryption: crypto backend unavailable."
                )
                return CryptoSuite._xor_encrypt(data, key)
            raise RuntimeError(
                "Cryptography backend unavailable. Install pycryptodome or set "
                "Config.ALLOW_INSECURE_CRYPTO = True to allow insecure XOR fallback."
            )

        try:
            cipher = AES.new(key[:32], AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(data)
            return cipher.nonce + tag + ciphertext
        except Exception as exc:
            if Config.ALLOW_INSECURE_CRYPTO:
                logger.warning(
                    "Insecure XOR fallback used for AES encryption due to error.",
                    exc_info=exc,
                )
                return CryptoSuite._xor_encrypt(data, key)
            raise RuntimeError(
                "AES encryption failed. Set Config.ALLOW_INSECURE_CRYPTO = True to "
                "allow insecure XOR fallback."
            ) from exc

    @staticmethod
    def decrypt_aes(data: bytes, key: bytes) -> bytes:
        """AES decryption."""
        if not CRYPTO_AVAILABLE:
            if Config.ALLOW_INSECURE_CRYPTO:
                logger.warning(
                    "Insecure XOR fallback used for AES decryption: crypto backend unavailable."
                )
                return CryptoSuite._xor_decrypt(data, key)
            raise RuntimeError(
                "Cryptography backend unavailable. Install pycryptodome or set "
                "Config.ALLOW_INSECURE_CRYPTO = True to allow insecure XOR fallback."
            )

        try:
            nonce = data[:16]
            tag = data[16:32]
            ciphertext = data[32:]
            cipher = AES.new(key[:32], AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag)
        except Exception as exc:
            if Config.ALLOW_INSECURE_CRYPTO:
                logger.warning(
                    "Insecure XOR fallback used for AES decryption due to error.",
                    exc_info=exc,
                )
                return CryptoSuite._xor_decrypt(data, key)
            raise RuntimeError(
                "AES decryption failed. Set Config.ALLOW_INSECURE_CRYPTO = True to "
                "allow insecure XOR fallback."
            ) from exc

    @staticmethod
    def _xor_encrypt(data: bytes, key: bytes) -> bytes:
        """Fallback XOR encryption."""
        iv = secrets.token_bytes(16)
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % len(key)] ^ iv[i % len(iv)])
        return iv + bytes(result)

    @staticmethod
    def _xor_decrypt(data: bytes, key: bytes) -> bytes:
        """Fallback XOR decryption."""
        iv = data[:16]
        ciphertext = data[16:]
        result = bytearray()
        for i, byte in enumerate(ciphertext):
            result.append(byte ^ key[i % len(key)] ^ iv[i % len(iv)])
        return bytes(result)


__all__ = [
    "CryptoSuite",
    "CRYPTO_AVAILABLE",
    "AES",
    "PKCS1_OAEP",
    "RSA",
    "get_random_bytes",
    "pad",
    "unpad",
    "PBKDF2",
]
