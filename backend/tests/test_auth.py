import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt

from app.auth import (
    ALGORITHM,
    AuthError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class PasswordHashingTests(unittest.TestCase):
    def test_hash_password_returns_different_hash_than_input(self) -> None:
        password = "mysecretpassword"
        hashed = hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$2b$"))

    def test_verify_password_returns_true_for_correct_password(self) -> None:
        password = "test123"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))

    def test_verify_password_returns_false_for_wrong_password(self) -> None:
        hashed = hash_password("correct")
        self.assertFalse(verify_password("wrong", hashed))

    def test_different_passwords_produce_different_hashes(self) -> None:
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        self.assertNotEqual(hash1, hash2)

    def test_same_password_produces_different_hashes_due_to_salt(self) -> None:
        hash1 = hash_password("same")
        hash2 = hash_password("same")
        self.assertNotEqual(hash1, hash2)


class TokenTests(unittest.TestCase):
    def test_create_and_decode_access_token(self) -> None:
        token = create_access_token(user_id=42, username="testuser")
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["username"], "testuser")

    def test_expired_token_raises_auth_error(self) -> None:
        expired_payload = {
            "sub": "1",
            "username": "expired",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iat": datetime.now(UTC) - timedelta(hours=2),
        }
        from app.auth import _get_secret_key
        token = jwt.encode(expired_payload, _get_secret_key(), algorithm=ALGORITHM)
        with self.assertRaises(AuthError) as ctx:
            decode_access_token(token)
        self.assertIn("expired", str(ctx.exception))

    def test_invalid_token_raises_auth_error(self) -> None:
        with self.assertRaises(AuthError) as ctx:
            decode_access_token("not-a-valid-token")
        self.assertIn("Invalid", str(ctx.exception))

    def test_token_with_wrong_secret_raises_auth_error(self) -> None:
        token = jwt.encode(
            {"sub": "1", "username": "test", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "wrong-secret",
            algorithm=ALGORITHM,
        )
        with self.assertRaises(AuthError):
            decode_access_token(token)


if __name__ == "__main__":
    unittest.main()
