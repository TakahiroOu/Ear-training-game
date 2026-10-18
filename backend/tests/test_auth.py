"""Checks login tokens with keys made up for the test (no Supabase needed)."""

import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.auth import verify_token
from app.main import app

PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())  # like Supabase's signing key


class FakeKeyClient:
    """Stands in for Supabase's public key download."""

    def get_signing_key_from_jwt(self, token):
        return jwt.PyJWK.from_dict(jwt.algorithms.ECAlgorithm.to_jwk(PRIVATE_KEY.public_key(), as_dict=True) | {"alg": "ES256"})


def make_token(key=PRIVATE_KEY, algorithm="ES256", **changes):
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "student@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    } | changes
    return jwt.encode(claims, key, algorithm=algorithm)


def check(token, legacy_secret=""):
    return verify_token(token, get_key_client=FakeKeyClient, legacy_secret=legacy_secret)


def test_valid_token():
    assert check(make_token())["email"] == "student@example.com"


def test_expired_token_is_rejected():
    with pytest.raises(jwt.ExpiredSignatureError):
        check(make_token(exp=int(time.time()) - 10))


def test_token_signed_by_someone_else_is_rejected():
    with pytest.raises(jwt.InvalidSignatureError):
        check(make_token(key=ec.generate_private_key(ec.SECP256R1())))


def test_token_for_another_audience_is_rejected():
    with pytest.raises(jwt.InvalidAudienceError):
        check(make_token(aud="something-else"))


def test_legacy_secret_tokens():
    secret = "a-legacy-secret-at-least-32-characters-long"
    token = make_token(key=secret, algorithm="HS256")
    assert check(token, legacy_secret=secret)["aud"] == "authenticated"
    with pytest.raises(jwt.InvalidTokenError):
        check(token, legacy_secret="")  # secret not configured


def test_api_rejects_garbage_tokens():
    response = TestClient(app).get("/api/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
