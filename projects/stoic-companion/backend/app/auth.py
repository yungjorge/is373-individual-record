import hashlib
import secrets
import time
from dataclasses import dataclass

import jwt
from fastapi import Cookie, Header, HTTPException

from .config import settings
from .db import GuestSession, Session

_jwks = None


@dataclass
class Principal:
    id: str
    guest: bool = False


def principal(authorization: str | None = Header(default=None), stoic_guest: str | None = Cookie(default=None)):
    global _jwks
    if authorization:
        try:
            if not settings.auth0_domain or not settings.auth0_audience:
                raise ValueError("Auth0 not configured")
            token = authorization.removeprefix("Bearer ")
            if _jwks is None:
                _jwks = jwt.PyJWKClient(f"https://{settings.auth0_domain}/.well-known/jwks.json", cache_keys=True)
            key = _jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=settings.auth0_audience,
                issuer=f"https://{settings.auth0_domain}/",
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
            return Principal(payload["sub"])
        except Exception:
            raise HTTPException(401, "Invalid access token") from None
    if settings.demo_mode and valid_guest(stoic_guest):
        return Principal("guest:" + hashlib.sha256(stoic_guest.encode()).hexdigest(), True)
    raise HTTPException(401, "Sign in or start a demo session")


def valid_guest(token):
    if not token:
        return False
    with Session() as db:
        row = db.get(GuestSession, hashlib.sha256(token.encode()).hexdigest())
        return bool(row and row.expires_at > time.time())


def guest_token():
    token = secrets.token_urlsafe(32)
    with Session() as db:
        db.add(GuestSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=time.time() + 86400))
        db.commit()
    return token


def admin(authorization: str | None = Header(default=None)):
    token = (authorization or "").removeprefix("Bearer ")
    if not settings.admin_token or not secrets.compare_digest(token, settings.admin_token):
        raise HTTPException(403, "Administrator access required")
