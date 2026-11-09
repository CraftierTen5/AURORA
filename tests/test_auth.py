import unittest
from unittest.mock import patch

from auth import authenticate, has_permission, verify_password


ADMIN_SALT = "aurora-admin-demo-salt-v1"
ADMIN_HASH = "f0fe0381097d5cd2c921bd14d8a895280be6d8cfe311e33852991d07ab735f90"
CUSTOMER_SALT = "aurora-customer-demo-salt-v1"
CUSTOMER_HASH = "7ef5946bf866cbbf9e09e9bbbb10c33a58a2f46a65aaef7a34f21ec7d3548300"


class AuthenticationTests(unittest.TestCase):
    def test_demo_password_hashes_verify(self):
        self.assertTrue(verify_password("AuroraAdmin!2026", ADMIN_SALT, ADMIN_HASH))
        self.assertTrue(verify_password("AuroraGuest!2026", CUSTOMER_SALT, CUSTOMER_HASH))

    def test_wrong_password_is_rejected(self):
        self.assertFalse(verify_password("not-the-password", ADMIN_SALT, ADMIN_HASH))

    @patch("auth.execute")
    @patch("auth.fetch_one")
    def test_authenticate_returns_minimal_admin_identity(self, fetch_one, execute):
        fetch_one.return_value = {
            "user_id": 7, "username": "admin", "password_hash": ADMIN_HASH,
            "password_salt": ADMIN_SALT, "is_active": 1,
            "role_code": "ADMIN", "role_name": "Administrator / ATC Controller",
        }
        user = authenticate("admin", "AuroraAdmin!2026")
        self.assertEqual(user, {
            "user_id": 7, "username": "admin",
            "role_code": "ADMIN", "role_name": "Administrator / ATC Controller",
        })
        execute.assert_called_once()

    @patch("auth.execute")
    @patch("auth.fetch_one")
    def test_disabled_user_cannot_authenticate(self, fetch_one, execute):
        fetch_one.return_value = {
            "user_id": 7, "username": "admin", "password_hash": ADMIN_HASH,
            "password_salt": ADMIN_SALT, "is_active": 0,
            "role_code": "ADMIN", "role_name": "Administrator",
        }
        self.assertIsNone(authenticate("admin", "AuroraAdmin!2026"))
        execute.assert_not_called()

    @patch("auth.fetch_one")
    def test_permission_check_denies_without_matching_grant(self, fetch_one):
        fetch_one.return_value = None
        self.assertFalse(has_permission({"user_id": 2}, "assignment.manage"))

    def test_permission_check_denies_missing_session(self):
        self.assertFalse(has_permission(None, "schedule.read"))


if __name__ == "__main__":
    unittest.main()
