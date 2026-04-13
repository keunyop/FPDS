from __future__ import annotations

import unittest

from api_service.security import hash_password, hash_session_token, verify_password


class SecurityTests(unittest.TestCase):
    def test_password_hash_round_trip(self) -> None:
        hashed = hash_password("correct horse battery staple")
        self.assertTrue(verify_password("correct horse battery staple", hashed))
        self.assertFalse(verify_password("incorrect", hashed))

    def test_session_token_hash_is_stable(self) -> None:
        token = "session-token-example"
        self.assertEqual(
            hash_session_token(token, "secret-a"),
            hash_session_token(token, "secret-a"),
        )
        self.assertNotEqual(
            hash_session_token(token, "secret-a"),
            hash_session_token(token, "secret-b"),
        )


if __name__ == "__main__":
    unittest.main()
