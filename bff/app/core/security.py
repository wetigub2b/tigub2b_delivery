from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str, expires_delta: timedelta, scope: str, role: str = "driver") -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + expires_delta
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "scope": scope,
        "role": role
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(subject: str, role: str = "driver") -> str:
    settings = get_settings()
    return create_token(subject, timedelta(minutes=settings.access_token_expire_minutes), "access", role)


def create_refresh_token(subject: str, role: str = "driver") -> str:
    settings = get_settings()
    return create_token(subject, timedelta(minutes=settings.refresh_token_expire_minutes), "refresh", role)


def validate_token(token: str, scope: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        return None
    if payload.get("scope") != scope:
        return None
    return str(payload.get("sub"))


def get_token_payload(token: str) -> Dict[str, Any] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def validate_admin_token(token: str, scope: str) -> tuple[str, str] | None:
    """Validate token and return (user_id, role) if user is admin"""
    payload = get_token_payload(token)
    if not payload:
        return None
    if payload.get("scope") != scope:
        return None

    role = payload.get("role", "driver")
    if role not in ["admin", "super_admin"]:
        return None

    return str(payload.get("sub")), role


def require_admin_role(required_role: str = "admin") -> bool:
    """Check if required role has sufficient privileges"""
    role_hierarchy = {"super_admin": 3, "admin": 2, "driver": 1}
    return role_hierarchy.get(required_role, 0) >= role_hierarchy.get("admin", 0)
