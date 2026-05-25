import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import player_profile  # noqa: E402


class PlayerProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.original_paths = (
            player_profile.PROFILE_DIR,
            player_profile.PLAYER_SETTINGS_FILE,
        )
        player_profile.PROFILE_DIR = root / "profile"
        player_profile.PLAYER_SETTINGS_FILE = root / "profile" / "player_settings.json"

    def tearDown(self):
        (
            player_profile.PROFILE_DIR,
            player_profile.PLAYER_SETTINGS_FILE,
        ) = self.original_paths
        self.tmp.cleanup()

    def test_existing_profiles_default_to_tutorial_completed(self):
        settings = player_profile.normalize_player_settings({"nickname": "Old Player"})

        self.assertTrue(settings["tutorial_completed"])

    def test_new_profile_can_require_tutorial(self):
        saved = player_profile.save_player_settings({"nickname": "New Player", "tutorial_completed": False})
        loaded = player_profile.load_player_settings()

        self.assertFalse(saved["tutorial_completed"])
        self.assertFalse(loaded["tutorial_completed"])

    def test_tutorial_completed_string_is_normalized(self):
        settings = player_profile.normalize_player_settings({"tutorial_completed": "false"})

        self.assertFalse(settings["tutorial_completed"])


if __name__ == "__main__":
    unittest.main()
