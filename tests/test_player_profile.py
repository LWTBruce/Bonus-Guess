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

    def test_admin_reveal_hidden_flag_is_normalized(self):
        enabled = player_profile.normalize_player_settings({"admin_reveal_hidden": "on"})
        disabled = player_profile.normalize_player_settings({"admin_reveal_hidden": "false"})

        self.assertTrue(enabled["admin_reveal_hidden"])
        self.assertFalse(disabled["admin_reveal_hidden"])

    def test_audio_volumes_are_normalized(self):
        settings = player_profile.normalize_player_settings({"music_volume": 1.5, "sfx_volume": "-0.25"})
        fallback = player_profile.normalize_player_settings({"music_volume": "bad", "sfx_volume": None})

        self.assertEqual(settings["music_volume"], 1.0)
        self.assertEqual(settings["sfx_volume"], 0.0)
        self.assertEqual(fallback["music_volume"], player_profile.DEFAULT_PLAYER_SETTINGS["music_volume"])
        self.assertEqual(fallback["sfx_volume"], player_profile.DEFAULT_PLAYER_SETTINGS["sfx_volume"])

    def test_home_music_id_is_normalized(self):
        valid = player_profile.normalize_player_settings({"home_music_id": "menu_loop"})
        fallback = player_profile.normalize_player_settings({"home_music_id": "missing"})

        self.assertEqual(valid["home_music_id"], "menu_loop")
        self.assertEqual(fallback["home_music_id"], player_profile.DEFAULT_PLAYER_SETTINGS["home_music_id"])

    def test_sfx_choices_are_normalized(self):
        settings = player_profile.normalize_player_settings({
            "sfx_choices": {
                "click": "success",
                "confirm": "fail",
                "missing_event": "warning",
                "hint": "missing_sound",
            }
        })

        self.assertEqual(settings["sfx_choices"]["click"], "success")
        self.assertEqual(settings["sfx_choices"]["confirm"], "fail")
        self.assertEqual(settings["sfx_choices"]["hint"], "hint")
        self.assertNotIn("missing_event", settings["sfx_choices"])


if __name__ == "__main__":
    unittest.main()
