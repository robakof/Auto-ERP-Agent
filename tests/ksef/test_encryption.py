"""Unit tests encryption — AES-256-CBC + RSA-OAEP + SHA-256."""
from __future__ import annotations

import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.x509 import (
    CertificateBuilder,
    Name,
    NameAttribute,
)
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes as crypto_hashes
import datetime as dt

import pytest

from core.ksef.adapters.encryption import (
    EncryptedInvoice,
    KSeFEncryption,
    SessionEncryption,
    rsa_oaep_encrypt,
)


# ---- helpers: self-signed test certificate ----------------------------------

def _make_test_cert_b64() -> tuple[str, rsa.RSAPrivateKey]:
    """Generate self-signed cert + private key for testing RSA-OAEP."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = Name([NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(1)
        .not_valid_before(dt.datetime(2026, 1, 1))
        .not_valid_after(dt.datetime(2027, 1, 1))
        .sign(private_key, crypto_hashes.SHA256())
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    return base64.b64encode(der).decode("ascii"), private_key


_CERT_B64, _PRIVATE_KEY = _make_test_cert_b64()


# ---- rsa_oaep_encrypt -------------------------------------------------------

def test_rsa_oaep_encrypt_with_mock_cert() -> None:
    plaintext = b"secret-payload-123"
    encrypted = rsa_oaep_encrypt(_CERT_B64, plaintext)
    assert encrypted != plaintext
    assert len(encrypted) > 0

    from cryptography.hazmat.primitives.asymmetric import padding
    decrypted = _PRIVATE_KEY.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=crypto_hashes.SHA256()),
            algorithm=crypto_hashes.SHA256(),
            label=None,
        ),
    )
    assert decrypted == plaintext


# ---- SessionEncryption -------------------------------------------------------

def test_prepare_session_key_is_32_bytes() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    assert len(session.symmetric_key) == 32


def test_prepare_session_iv_is_16_bytes() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    assert len(session.iv) == 16


def test_prepare_session_key_is_random() -> None:
    enc = KSeFEncryption(_CERT_B64)
    s1 = enc.prepare_session()
    s2 = enc.prepare_session()
    assert s1.symmetric_key != s2.symmetric_key


def test_prepare_session_encrypted_key_is_base64() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    raw = base64.b64decode(session.encrypted_key_b64)
    assert len(raw) > 0


def test_prepare_session_iv_b64_roundtrips() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    assert base64.b64decode(session.iv_b64) == session.iv


# ---- EncryptedInvoice --------------------------------------------------------

def test_encrypt_invoice_aes_cbc_round_trip() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    original = b"<Faktura>test content</Faktura>"
    result = enc.encrypt_invoice(original, session)

    encrypted_bytes = base64.b64decode(result.encrypted_content_b64)
    cipher = Cipher(algorithms.AES(session.symmetric_key), modes.CBC(session.iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    decrypted = unpadder.update(padded) + unpadder.finalize()
    assert decrypted == original


def test_encrypt_invoice_pkcs7_padding_correct() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    xml = b"<Faktura>odd-length-content</Faktura>"
    result = enc.encrypt_invoice(xml, session)
    encrypted_bytes = base64.b64decode(result.encrypted_content_b64)
    assert len(encrypted_bytes) % 16 == 0


def test_encrypt_invoice_hashes_match() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    xml = b"<Faktura>hash test</Faktura>"
    result = enc.encrypt_invoice(xml, session)

    plain_hash = base64.b64encode(hashlib.sha256(xml).digest()).decode("ascii")
    assert result.plain_hash_b64 == plain_hash

    encrypted_bytes = base64.b64decode(result.encrypted_content_b64)
    enc_hash = base64.b64encode(hashlib.sha256(encrypted_bytes).digest()).decode("ascii")
    assert result.encrypted_hash_b64 == enc_hash


def test_encrypt_invoice_sizes_match() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    xml = b"<Faktura>size test</Faktura>"
    result = enc.encrypt_invoice(xml, session)
    assert result.plain_size == len(xml)
    encrypted_bytes = base64.b64decode(result.encrypted_content_b64)
    assert result.encrypted_size == len(encrypted_bytes)


def test_encrypted_invoice_is_frozen() -> None:
    enc = KSeFEncryption(_CERT_B64)
    session = enc.prepare_session()
    result = enc.encrypt_invoice(b"<X/>", session)
    with pytest.raises(AttributeError):
        result.plain_size = 999  # type: ignore[misc]
