import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import sfx_catalog  # noqa: E402


class SfxCatalogTests(unittest.TestCase):
    def test_every_event_has_default_sound_without_unlocks(self):
        choices = sfx_catalog.normalize_sfx_choices({})

        self.assertEqual(set(choices), sfx_catalog.SFX_EVENT_IDS)
        self.assertEqual(set(choices.values()), sfx_catalog.SFX_SOUND_IDS)

    def test_each_event_can_choose_any_available_sound(self):
        choices = {
            event_id: "success"
            for event_id, _label in sfx_catalog.SFX_EVENT_OPTIONS
        }
        normalized = sfx_catalog.normalize_sfx_choices(choices)

        self.assertTrue(all(sound_id == "success" for sound_id in normalized.values()))

    def test_display_label_round_trips_to_sound_id(self):
        for sound_id, _label in sfx_catalog.SFX_SOUND_OPTIONS:
            with self.subTest(sound_id=sound_id):
                display = sfx_catalog.sfx_sound_display(sound_id)
                self.assertEqual(sfx_catalog.sfx_sound_id_from_display(display), sound_id)


if __name__ == "__main__":
    unittest.main()
