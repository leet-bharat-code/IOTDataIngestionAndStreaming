"""Unit tests for the core security module (JWT + password hashing)."""

import time

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_then_verify(self):
        hashed = hash_password("my-secret")
        assert verify_password("my-secret", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("my-secret")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_input(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # salt differs


class TestJWT:
    def test_roundtrip(self):
        token = create_access_token("U1001")
        payload = decode_access_token(token)
        assert payload["sub"] == "U1001"

    def test_extra_claims_preserved(self):
        token = create_access_token("U1001", extra={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_tampered_token_rejected(self):
        token = create_access_token("U1001")
        with pytest.raises(AuthenticationError, match="Invalid or expired"):
            decode_access_token(token + "tampered")

    def test_garbage_token_rejected(self):
        with pytest.raises(AuthenticationError):
            decode_access_token("not.a.jwt")
