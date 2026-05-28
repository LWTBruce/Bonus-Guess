import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from app import BonusGuessApp  # noqa: E402
from cosmetics import ACHIEVEMENT_TITLE_REWARDS  # noqa: E402
from game_config import ACHIEVEMENTS, HIDDEN_ACHIEVEMENT_IDS  # noqa: E402


class GreekAchievementTests(unittest.TestCase):
    def test_greek_hidden_achievements_are_registered(self):
        expected = {
            "first_greek_term",
            "first_greek_success",
            "greek_success_10",
            "crossword_greek_term",
        }
        achievement_ids = {achievement_id for achievement_id, _title, _description in ACHIEVEMENTS}
        title_reward_ids = {achievement_id for achievement_id, _reward_id, _title in ACHIEVEMENT_TITLE_REWARDS}
        self.assertTrue(expected <= achievement_ids)
        self.assertTrue(expected <= HIDDEN_ACHIEVEMENT_IDS)
        self.assertIn("first_greek_success", title_reward_ids)
        self.assertIn("greek_success_10", title_reward_ids)

    def test_record_greek_answer_detection(self):
        record = {
            "selected_answer": "σ代数",
            "accepted_answers": ["σ代数"],
            "success": True,
        }
        self.assertEqual(BonusGuessApp.record_greek_answers(record), ["σ代数"])
        self.assertEqual(BonusGuessApp.record_success_greek_answers(record), ["σ代数"])

    def test_crossword_greek_answer_detection_only_counts_solved_successes(self):
        record = {
            "crossword_mode": 1,
            "success": True,
            "crossword_placements": [
                {"answer": "普通词", "solved": 1},
                {"answer": "ΛCDM模型", "solved": 1},
                {"answer": "βγ系统", "solved": 0},
            ],
        }
        self.assertEqual(BonusGuessApp.record_greek_answers(record), ["ΛCDM模型", "βγ系统"])
        self.assertEqual(BonusGuessApp.record_success_greek_answers(record), ["ΛCDM模型"])


if __name__ == "__main__":
    unittest.main()
