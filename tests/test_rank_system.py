import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import rank_system  # noqa: E402
from cosmetics import rank_title_source_label  # noqa: E402


class RankBadgeLabelTests(unittest.TestCase):
    def test_rank_table_extends_non_clue_tracks_to_twenty(self):
        self.assertEqual(len(rank_system.RANK_CHALLENGES), 20)
        self.assertEqual(rank_system.RANK_CHALLENGES[0]["name"], "Class 01: Spark")
        self.assertEqual(rank_system.RANK_CHALLENGES[-1]["name"], "Class 20: Absolute")
        self.assertEqual(rank_system.rank_count_for_kind("free"), 20)
        self.assertEqual(rank_system.rank_count_for_kind("crossword"), 20)
        self.assertEqual(rank_system.rank_count_for_kind("clue"), 20)
        self.assertEqual(rank_system.rank_difficulty_name(16), "困难")
        self.assertEqual(rank_system.rank_difficulty_name(17), "噩梦")
        self.assertEqual(rank_system.rank_target_difficulty(20), 12.0)
        self.assertEqual(rank_system.RANK_CHALLENGES[14]["seconds"], 450)
        self.assertGreater(rank_system.RANK_CHALLENGES[19]["seconds"], rank_system.RANK_CHALLENGES[14]["seconds"])
        self.assertEqual(rank_system.rank_hint_cooldown_seconds(15), 120)
        self.assertGreater(rank_system.rank_hint_cooldown_seconds(20), 120)

    def test_rank_visibility_and_unlocks_expand_after_progress(self):
        info = {"highest": 0, "passed": {}}
        self.assertEqual([rank["id"] for rank in rank_system.visible_rank_challenges(info, "free")], list(range(1, 16)))
        self.assertTrue(rank_system.rank_is_unlocked(info, 10, "free"))
        self.assertFalse(rank_system.rank_is_unlocked(info, 11, "free"))

        info["passed"] = {"10": {"first_passed_at": "2026-05-27T00:00:00"}}
        self.assertTrue(rank_system.rank_is_unlocked(info, 11, "free"))
        self.assertEqual(rank_system.visible_rank_challenges(info, "free")[-1]["id"], 15)

        info["passed"] = {str(rank_id): {"first_passed_at": "2026-05-27T00:00:00"} for rank_id in range(10, 16)}
        self.assertTrue(rank_system.rank_is_unlocked(info, 16, "free"))
        self.assertEqual(rank_system.visible_rank_challenges(info, "free")[-1]["id"], 16)

        info["passed"]["16"] = {"first_passed_at": "2026-05-27T00:00:00"}
        self.assertTrue(rank_system.rank_is_unlocked(info, 17, "free"))
        self.assertEqual(rank_system.visible_rank_challenges(info, "free")[-1]["id"], 17)

    def test_rank_unlocks_require_a_chain_after_default_unlocked_ranks(self):
        info = {"highest": 15, "passed": {"15": {"first_passed_at": "2026-05-27T00:00:00"}}}
        self.assertFalse(rank_system.rank_is_unlocked(info, 16, "free"))
        self.assertEqual(rank_system.visible_rank_challenges(info, "free")[-1]["id"], 15)

        legacy_info = {"highest": 15, "passed": {}}
        self.assertTrue(rank_system.rank_is_unlocked(legacy_info, 16, "free"))
        self.assertEqual(rank_system.visible_rank_challenges(legacy_info, "free")[-1]["id"], 16)

    def test_clue_track_extends_to_twenty(self):
        info = {"highest": 15, "passed": {str(rank_id): "2026-05-27T00:00:00" for rank_id in range(1, 16)}}
        self.assertEqual(rank_system.visible_rank_challenges(info, "clue")[-1]["id"], 16)
        self.assertTrue(rank_system.rank_is_unlocked(info, 16, "clue"))
        info["passed"]["16"] = "2026-05-27T00:00:00"
        self.assertEqual(rank_system.visible_rank_challenges(info, "clue")[-1]["id"], 17)
        self.assertTrue(rank_system.rank_is_unlocked(info, 17, "clue"))

    def test_rank_badge_labels_include_subject_and_track(self):
        cases = [
            ("物理模式", "free", "物理-限时"),
            ("物理模式", "clue", "物理-线索"),
            ("物理模式", "crossword", "物理-字谜"),
            ("数学模式", "free", "数学-限时"),
            ("数学模式", "clue", "数学-线索"),
            ("数学模式", "crossword", "数学-字谜"),
            ("物理模式", "timed", "物理-旧限时"),
        ]
        for subject, kind, expected in cases:
            with self.subTest(subject=subject, kind=kind):
                badge_id = rank_system.rank_badge_id(subject, 7, kind)
                self.assertEqual(rank_system.rank_badge_short_label(badge_id), expected)
                self.assertTrue(rank_system.rank_badge_name(badge_id).startswith(f"{expected} "))
        self.assertEqual(rank_title_source_label(rank_system.rank_badge_id("物理模式", 7, "clue")), "物理-线索段位")

    def test_same_class_unlocks_distinct_badges_per_rank_track(self):
        progress = rank_system.default_rank_progress()
        for kind in ("free", "clue", "crossword"):
            subject_key = rank_system.rank_progress_key("物理模式", kind)
            progress["subjects"][subject_key]["passed"] = {"5": {"first_passed_at": "2026-05-27T00:00:00"}}
        badges = dict(rank_system.unlocked_rank_badges(progress))

        expected_ids = {
            rank_system.rank_badge_id("物理模式", 5, "free"),
            rank_system.rank_badge_id("物理模式", 5, "clue"),
            rank_system.rank_badge_id("物理模式", 5, "crossword"),
        }
        self.assertTrue(expected_ids.issubset(set(badges)))
        self.assertEqual({rank_system.rank_badge_short_label(item) for item in expected_ids}, {"物理-限时", "物理-线索", "物理-字谜"})


if __name__ == "__main__":
    unittest.main()
