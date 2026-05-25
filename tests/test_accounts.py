import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import accounts  # noqa: E402


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.original_paths = (
            accounts.ACCOUNTS_FILE,
            accounts.SESSION_FILE,
            accounts.USERS_DIR,
            accounts.LEGACY_RECORD_DIR,
            accounts.LEGACY_PROFILE_DIR,
        )
        accounts.ACCOUNTS_FILE = root / "profile" / "accounts.json"
        accounts.SESSION_FILE = root / "profile" / "session.json"
        accounts.USERS_DIR = root / "profile" / "users"
        accounts.LEGACY_RECORD_DIR = root / "record"
        accounts.LEGACY_PROFILE_DIR = root / "legacy_profile"

    def tearDown(self):
        (
            accounts.ACCOUNTS_FILE,
            accounts.SESSION_FILE,
            accounts.USERS_DIR,
            accounts.LEGACY_RECORD_DIR,
            accounts.LEGACY_PROFILE_DIR,
        ) = self.original_paths
        self.tmp.cleanup()

    def test_create_authenticate_and_change_password(self):
        account = accounts.create_account("Alice", "pass1234")

        self.assertEqual(account["nickname"], "Alice")
        self.assertFalse(account["is_admin"])
        self.assertFalse(accounts.is_admin_account(account))
        self.assertEqual(accounts.authenticate("alice", "pass1234")["id"], account["id"])

        accounts.change_password(account["id"], "pass1234", "nextpass")
        with self.assertRaises(accounts.AccountError):
            accounts.authenticate("Alice", "pass1234")
        self.assertEqual(accounts.authenticate("Alice", "nextpass")["id"], account["id"])

    def test_duplicate_nickname_registration_is_rejected(self):
        accounts.create_account("Alice", "pass1234")

        with self.assertRaises(accounts.AccountError):
            accounts.create_account("alice", "otherpass")

    def test_rename_keeps_nickname_index_unique(self):
        alice = accounts.create_account("Alice", "pass1234")
        accounts.create_account("Bob", "pass1234")

        renamed = accounts.rename_account(alice["id"], "Carol")

        self.assertEqual(renamed["nickname"], "Carol")
        self.assertEqual(accounts.authenticate("carol", "pass1234")["id"], alice["id"])
        with self.assertRaises(accounts.AccountError):
            accounts.rename_account(alice["id"], "Bob")

    def test_bruce_bootstrap_is_admin_and_active(self):
        account = accounts.ensure_local_bruce_account()

        self.assertEqual(account["id"], "bruce")
        self.assertEqual(account["nickname"], "Bruce")
        self.assertTrue(account["is_admin"])
        self.assertEqual(accounts.active_account()["id"], "bruce")
        self.assertTrue((accounts.USERS_DIR / "bruce" / "record").exists())
        self.assertEqual(accounts.authenticate("Bruce", "test001")["id"], "bruce")


if __name__ == "__main__":
    unittest.main()
