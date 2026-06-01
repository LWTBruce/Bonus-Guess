import sys
import tempfile
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import accounts  # noqa: E402
import backend.runtime.records as runtime_records  # noqa: E402


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
        self.original_runtime_record_paths = (
            runtime_records.RECORD_DIR,
            runtime_records.ACHIEVEMENTS_FILE,
            runtime_records.RANK_PROGRESS_FILE,
            runtime_records.DAILY_TERMS_FILE,
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
        (
            runtime_records.RECORD_DIR,
            runtime_records.ACHIEVEMENTS_FILE,
            runtime_records.RANK_PROGRESS_FILE,
            runtime_records.DAILY_TERMS_FILE,
        ) = self.original_runtime_record_paths
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

    def test_fresh_install_does_not_bootstrap_admin(self):
        account = accounts.ensure_local_bruce_account()

        self.assertIsNone(account)
        self.assertIsNone(accounts.active_account())
        self.assertEqual(accounts.list_public_accounts(), [])

    def test_existing_owner_bruce_account_stays_admin_and_active(self):
        accounts.create_account("Bruce", "test001", account_id="bruce", is_admin=True)

        account = accounts.ensure_local_bruce_account()

        self.assertEqual(account["id"], "bruce")
        self.assertTrue(account["is_admin"])
        self.assertEqual(accounts.active_account()["id"], "bruce")
        self.assertTrue((accounts.USERS_DIR / "bruce" / "record").exists())

    def test_existing_owner_bruce_merges_legacy_records_into_profile(self):
        legacy_day = accounts.LEGACY_RECORD_DIR / "2026-05" / "2026-05-20"
        legacy_day.mkdir(parents=True)
        legacy_record = legacy_day / "20260520_120000_legacy.json"
        legacy_record.write_text(json.dumps({"created_at": "2026-05-20T12:00:00", "success": True}), encoding="utf-8")
        (accounts.LEGACY_RECORD_DIR / "achievements.json").write_text(
            json.dumps({"completed": {"old_win": "2026-05-20T12:01:00"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        (accounts.LEGACY_RECORD_DIR / "rank_progress.json").write_text(
            json.dumps({"subjects": {"physics": {"highest": 7, "passed": {"7": {"best_score": 700}}}}}, ensure_ascii=False),
            encoding="utf-8",
        )
        accounts.create_account("Bruce", "test001", account_id="bruce", is_admin=True)
        paths = accounts.account_paths("bruce")
        paths["achievements_file"].write_text(
            json.dumps({"completed": {"new_win": "2026-05-22T12:01:00"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        paths["rank_progress_file"].write_text(
            json.dumps({"subjects": {"physics": {"highest": 3, "passed": {"3": {"best_score": 300}}}}}, ensure_ascii=False),
            encoding="utf-8",
        )

        accounts.ensure_local_bruce_account()

        migrated_record = paths["record_dir"] / "2026-05" / "2026-05-20" / legacy_record.name
        self.assertTrue(migrated_record.exists())
        self.assertFalse(accounts.LEGACY_RECORD_DIR.exists())
        achievements = json.loads(paths["achievements_file"].read_text(encoding="utf-8"))
        self.assertIn("old_win", achievements["completed"])
        self.assertIn("new_win", achievements["completed"])
        progress = json.loads(paths["rank_progress_file"].read_text(encoding="utf-8"))
        self.assertEqual(progress["subjects"]["physics"]["highest"], 7)
        self.assertIn("3", progress["subjects"]["physics"]["passed"])
        self.assertIn("7", progress["subjects"]["physics"]["passed"])

    def test_bruce_owner_id_without_owner_password_is_not_promoted(self):
        accounts.create_account("Bruce", "pass1234", account_id="bruce", is_admin=False)

        account = accounts.ensure_local_bruce_account()

        self.assertIsNone(account)
        self.assertFalse(accounts.authenticate("Bruce", "pass1234")["is_admin"])

    def test_local_bruce_nickname_is_not_promoted_when_not_owner_id(self):
        account = accounts.create_account("Bruce", "pass1234")

        boot = accounts.ensure_local_bruce_account()

        self.assertIsNone(boot)
        self.assertIsNone(accounts.active_account())
        self.assertFalse(accounts.authenticate("Bruce", "pass1234")["is_admin"])
        self.assertEqual(accounts.active_account()["id"], account["id"])

    def test_admin_can_promote_existing_account(self):
        account = accounts.create_account("Alice", "pass1234")

        promoted = accounts.set_account_admin(account["id"], True)

        self.assertTrue(promoted["is_admin"])
        self.assertTrue(accounts.authenticate("Alice", "pass1234")["is_admin"])

    def test_string_admin_flag_is_not_treated_as_admin(self):
        account = accounts.create_account("Alice", "pass1234")
        data = accounts.load_accounts()
        data["accounts"][account["id"]]["is_admin"] = "false"
        accounts.save_accounts(data)

        loaded = accounts.authenticate("Alice", "pass1234")

        self.assertFalse(loaded["is_admin"])
        self.assertFalse(accounts.is_admin_account(loaded))

    def test_account_context_updates_backend_runtime_record_path(self):
        account = accounts.create_account("Alice", "pass1234")

        paths = accounts.apply_account_context(account["id"])

        self.assertEqual(runtime_records.RECORD_DIR, paths["record_dir"])


if __name__ == "__main__":
    unittest.main()
