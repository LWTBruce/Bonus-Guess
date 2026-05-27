import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import rank_system  # noqa: E402
from cosmetics import rank_title_source_label  # noqa: E402


class RankBadgeLabelTests(unittest.TestCase):
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
