"""KSeF session encryption — AES-256-CBC + RSA-OAEP(SHA-256).

KSeF online session wymaga szyfrowania symetrycznego (AES-256-CBC, PKCS#7)
z kluczem zaszyfrowanym asymetrycznie (RSA-OAEP SHA-256) certyfikatem
SymmetricKeyEncryption z /security/public-key-certificates.

Symmetric key zyje wylacznie w pamieci — nigdy na dysku.
"""
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.x509 import load_der_x509_certificate


@dataclass(frozen=True)
class SessionEncryption:
    """Gotowy payload encryption do open_online_session."""

    symmetric_key: bytes          # 32 bytes AES-256 key
    iv: bytes                     # 16 bytes IV
    encrypted_key_b64: str        # RSA-OAEP(symmetric_key) -> Base64
    iv_b64: str                   # Base64(iv)


@dataclass(frozen=True)
class EncryptedInvoice:
    """Gotowy payload do send_invoice."""

    encrypted_content_b64: str    # AES-256-CBC(XML) -> Base64
    encrypted_hash_b64: str       # SHA-256(encrypted_bytes) -> Base64
    encrypted_size: int           # len(encrypted_bytes)
    plain_hash_b64: str           # SHA-256(xml_bytes) -> Base64
    plain_size: int               # len(xml_bytes)


def rsa_oaep_encrypt(cert_b64: str, data: bytes) -> bytes:
    """Encrypt `data` with the cert's public key using RSA-OAEP(SHA-256).

    Shared between auth (token encryption) and session (symmetric key encryption).
    """
    der = base64.b64decode(cert_b64)
    cert = load_der_x509_certificate(der)
    public_key = cert.public_key()
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


class KSeFEncryption:
    """Szyfrowanie sesji i faktur dla KSeF online."""

    def __init__(self, sym_cert_b64: str) -> None:
        """sym_cert_b64 — certyfikat SymmetricKeyEncryption z /security/public-key-certificates."""
        self._sym_cert_b64 = sym_cert_b64

    def prepare_session(self) -> SessionEncryption:
        """Generuj nowy AES key + IV, zaszyfruj key certyfikatem."""
        key = os.urandom(32)
        iv = os.urandom(16)
        encrypted_key = rsa_oaep_encrypt(self._sym_cert_b64, key)
        return SessionEncryption(
            symmetric_key=key,
            iv=iv,
            encrypted_key_b64=base64.b64encode(encrypted_key).decode("ascii"),
            iv_b64=base64.b64encode(iv).decode("ascii"),
        )

    def encrypt_invoice(
        self, xml_bytes: bytes, session: SessionEncryption,
    ) -> EncryptedInvoice:
        """AES-256-CBC encrypt + SHA-256 hashes + sizes."""
        encrypted_bytes = _aes_cbc_encrypt(xml_bytes, session.symmetric_key, session.iv)
        return EncryptedInvoice(
            encrypted_content_b64=base64.b64encode(encrypted_bytes).decode("ascii"),
            encrypted_hash_b64=_sha256_b64(encrypted_bytes),
            encrypted_size=len(encrypted_bytes),
            plain_hash_b64=_sha256_b64(xml_bytes),
            plain_size=len(xml_bytes),
        )


def _aes_cbc_encrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-256-CBC with PKCS#7 padding."""
    padder = PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def _sha256_b64(data: bytes) -> str:
    """SHA-256 digest -> Base64."""
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")
