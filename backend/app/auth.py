"""Checks who is calling the API.

The browser logs in with Supabase and receives a login token (a "JWT": a signed note saying
"this is user X, valid until Y"). It sends the token with each request:
    Authorization: Bearer <token>
We check Supabase's signature on it, so nobody can pretend to be someone else.
"""

import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config

bearer = HTTPBearer(auto_error=False)
_jwks_client = None


@dataclass
class CurrentUser:
    id: uuid.UUID
    email: str | None


def get_jwks_client():
    """Downloads (and caches) Supabase's public keys used to check token signatures."""
    global _jwks_client
    if _jwks_client is None:
        if not config.SUPABASE_URL:
            raise HTTPException(503, "Login is not set up yet (SUPABASE_URL is missing in .env)")
        _jwks_client = jwt.PyJWKClient(f"{config.SUPABASE_URL}/auth/v1/.well-known/jwks.json")
    return _jwks_client


def verify_token(token, get_key_client=get_jwks_client, legacy_secret=None):
    """Returns the token's contents ("claims") if the signature and expiry are valid."""
    legacy_secret = config.SUPABASE_JWT_SECRET if legacy_secret is None else legacy_secret
    if jwt.get_unverified_header(token).get("alg") == "HS256":
        # Older Supabase projects sign with a shared secret instead of public/private keys
        if not legacy_secret:
            raise jwt.InvalidTokenError("HS256 token but SUPABASE_JWT_SECRET is not set")
        return jwt.decode(token, legacy_secret, algorithms=["HS256"], audience="authenticated")

    signing_key = get_key_client().get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated")


def user_from_token(token):
    """For WebSockets, where the token comes in a message instead of a header. Raises jwt.PyJWTError."""
    claims = verify_token(token)
    return CurrentUser(id=uuid.UUID(claims["sub"]), email=claims.get("email"))


def get_token_checker():
    """Dependency returning the token-checking function (tests swap it for a fake one)."""
    return user_from_token


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Like get_current_user, but guests get None instead of an error."""
    if credentials is None:
        return None
    return get_current_user(credentials)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Use as `user: CurrentUser = Depends(get_current_user)` in routes that need a login."""
    if credentials is None:
        raise HTTPException(401, "Please log in")
    try:
        claims = verify_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(401, "Your login is invalid or has expired. Please log in again")
    return CurrentUser(id=uuid.UUID(claims["sub"]), email=claims.get("email"))
