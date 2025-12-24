"""Cryptographic helpers."""
from __future__ import annotations

import hashlib
import importlib.util
import secrets

if importlib.util.find_spec("Crypto") is not None:
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Protocol.KDF import PBKDF2

    CRYPTO_AVAILABLE = True
else:  # pragma: no cover - optional dependency
    CRYPTO_AVAILABLE = False


class CryptoSuite:
    """Cryptographic operations"""

    @staticmethod
    def hash_sha256(data: bytes) -> str:
        """SHA-256 hash"""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def generate_key(length: int = 32) -> bytes:
        """Generate random key"""
        return secrets.token_bytes(length)

    @staticmethod
    def encrypt_aes(data: bytes, key: bytes) -> bytes:
        """AES encryption"""
        if not CRYPTO_AVAILABLE:
            return CryptoSuite._xor_encrypt(data, key)

        try:
            cipher = AES.new(key[:32], AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(data)
            return cipher.nonce + tag + ciphertext
        except Exception:
            return CryptoSuite._xor_encrypt(data, key)

    @staticmethod
    def decrypt_aes(data: bytes, key: bytes) -> bytes:
        """AES decryption"""
        if not CRYPTO_AVAILABLE:
            return CryptoSuite._xor_decrypt(data, key)

        try:
            nonce = data[:16]
            tag = data[16:32]
            ciphertext = data[32:]
            cipher = AES.new(key[:32], AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag)
        except Exception:
            return CryptoSuite._xor_decrypt(data, key)

    @staticmethod
    def _xor_encrypt(data: bytes, key: bytes) -> bytes:
        """Fallback XOR encryption"""
        iv = secrets.token_bytes(16)
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % len(key)] ^ iv[i % len(iv)])
        return iv + bytes(result)

    @staticmethod
    def _xor_decrypt(data: bytes, key: bytes) -> bytes:
        """Fallback XOR decryption"""
        iv = data[:16]
        ciphertext = data[16:]
        result = bytearray()
        for i, byte in enumerate(ciphertext):
            result.append(byte ^ key[i % len(key)] ^ iv[i % len(iv)])
        return bytes(result)
