import importlib

import pytest


@pytest.fixture()
def crypto_module():
    import void.crypto as crypto

    return importlib.reload(crypto)


def test_hash_sha256(crypto_module):
    digest = crypto_module.CryptoSuite.hash_sha256(b"void")
    assert digest == "445be54d48a2e6294369c84c61cd0929209d4e1084536159bdf7002bddfe094b"


def test_generate_key_length(crypto_module):
    key = crypto_module.CryptoSuite.generate_key(48)
    assert isinstance(key, bytes)
    assert len(key) == 48


def test_encrypt_decrypt_with_xor_fallback(monkeypatch, crypto_module):
    monkeypatch.setattr(crypto_module, "CRYPTO_AVAILABLE", False)
    monkeypatch.setattr(crypto_module.Config, "ALLOW_INSECURE_CRYPTO", True)

    plaintext = b"secure message"
    key = b"k" * 32

    encrypted = crypto_module.CryptoSuite.encrypt_aes(plaintext, key)
    decrypted = crypto_module.CryptoSuite.decrypt_aes(encrypted, key)

    assert decrypted == plaintext


def test_encrypt_requires_crypto_backend(monkeypatch, crypto_module):
    monkeypatch.setattr(crypto_module, "CRYPTO_AVAILABLE", False)
    monkeypatch.setattr(crypto_module.Config, "ALLOW_INSECURE_CRYPTO", False)

    with pytest.raises(RuntimeError, match="Cryptography backend unavailable"):
        crypto_module.CryptoSuite.encrypt_aes(b"data", b"k" * 32)
