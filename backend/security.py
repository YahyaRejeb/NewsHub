import os
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt  # type: ignore

try:
    import bcrypt  # type: ignore
except ImportError:  # pragma: no cover - fallback used only when bcrypt is missing
    bcrypt = None


def _read_access_token_expiry_minutes() -> int:
    configured_value = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    try:
        return max(1, int(configured_value))
    except ValueError:
        return 1440


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _read_access_token_expiry_minutes()


def _hash_password_with_pbkdf2(password: str) -> str:
    iterations = 600_000
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_text = base64.b64encode(salt).decode("utf-8")
    digest_text = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_text}${digest_text}"


def _verify_password_with_pbkdf2(password: str, password_hash: str) -> bool:
    try:
        _, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_text.encode("utf-8"))
        expected_digest = base64.b64decode(digest_text.encode("utf-8"))
    except (ValueError, TypeError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def hash_password(password: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return _hash_password_with_pbkdf2(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("pbkdf2_sha256$"):
        return _verify_password_with_pbkdf2(password, password_hash)

    if bcrypt is not None:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expiration_time = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expiration_time})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
