"""密码哈希、RSA 传输解密、JWT。"""
import base64
import time
from pathlib import Path

import bcrypt
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .config import BASE_DIR, settings

KEY_PATH = BASE_DIR / "data" / "rsa_private.pem"
_private_key: rsa.RSAPrivateKey | None = None


def _load_key() -> rsa.RSAPrivateKey:
    global _private_key
    if _private_key is not None:
        return _private_key
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        _private_key = serialization.load_pem_private_key(KEY_PATH.read_bytes(), password=None)
    else:
        _private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        KEY_PATH.write_bytes(
            _private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    return _private_key


def public_key_pem() -> str:
    return _load_key().public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


def decrypt_password(value: str) -> str:
    """前端用 RSA-OAEP(SHA256) 加密后 Base64 提交；此处解密。"""
    try:
        raw = base64.b64decode(value, validate=True)
        return _load_key().decrypt(
            raw,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        ).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise ValueError("密码解密失败，请刷新页面后重试") from exc


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8")[:72], bcrypt.gensalt(rounds=12)).decode()


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:72], hashed.encode())
    except ValueError:
        return False


def create_token(user_id: int, token_version: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "ver": token_version,
        "iat": now,
        "exp": now + settings.jwt_expire_days * 86400,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
