import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import music_catalog  # noqa: E402
from cosmetics import coerce_avatar_id, unlocked_avatar_ids  # noqa: E402


class MusicCatalogTests(unittest.TestCase):
    def test_home_music_unlocks_follow_rating(self):
        starter_ids = music_catalog.unlocked_home_music_ids(0)
        mid_ids = music_catalog.unlocked_home_music_ids(10)

        self.assertIn("plains_luminescence", starter_ids)
        self.assertNotIn("pointless_loop", starter_ids)
        self.assertIn("pointless_loop", mid_ids)

    def test_hidden_home_music_requires_reveal_all_to_coerce(self):
        locked = music_catalog.coerce_home_music_id("boss_battle", rating=2, reveal_all=False)
        revealed = music_catalog.coerce_home_music_id("boss_battle", rating=2, reveal_all=True)

        self.assertEqual(locked, music_catalog.DEFAULT_HOME_MUSIC_ID)
        self.assertEqual(revealed, "boss_battle")

    def test_reveal_all_unlocks_all_avatars(self):
        self.assertNotIn(14, unlocked_avatar_ids(0))
        self.assertIn(14, unlocked_avatar_ids(0, reveal_all=True))
        self.assertEqual(coerce_avatar_id(14, 0, reveal_all=True), 14)


if __name__ == "__main__":
    unittest.main()
