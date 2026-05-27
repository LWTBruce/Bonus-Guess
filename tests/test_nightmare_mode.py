import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from app import BonusGuessApp  # noqa: E402
from crossword_puzzle import size_for_difficulty  # noqa: E402
from game_config import (  # noqa: E402
    FREE_HINT_DECAY,
    FREE_HINT_ZERO_PROB,
    HINT_COOLDOWN_SECONDS,
    MASK_PROBABILITIES,
    SCORE_MODE_WEIGHTS,
    TERM_DIFFICULTY_WEIGHTS,
)
from term_library import TermLibrary  # noqa: E402


class NightmareModeConfigTests(unittest.TestCase):
    def test_nightmare_is_registered_between_hard_and_mixed(self):
        self.assertIn("噩梦", TermLibrary.DIFFICULTIES)
        self.assertLess(TermLibrary.DIFFICULTIES.index("困难"), TermLibrary.DIFFICULTIES.index("噩梦"))
        self.assertLess(TermLibrary.DIFFICULTIES.index("噩梦"), TermLibrary.DIFFICULTIES.index("混合模式"))

    def test_nightmare_single_answer_rules_are_harder_than_hard(self):
        hard_weights = TERM_DIFFICULTY_WEIGHTS["困难"]
        nightmare_weights = TERM_DIFFICULTY_WEIGHTS["噩梦"]
        self.assertGreater(nightmare_weights[10], hard_weights[10])
        self.assertGreater(FREE_HINT_ZERO_PROB["噩梦"], FREE_HINT_ZERO_PROB["困难"])
        self.assertLess(FREE_HINT_DECAY["噩梦"], FREE_HINT_DECAY["困难"])
        self.assertGreater(HINT_COOLDOWN_SECONDS["噩梦"], HINT_COOLDOWN_SECONDS["困难"])
        self.assertGreater(SCORE_MODE_WEIGHTS["噩梦"], SCORE_MODE_WEIGHTS["困难"])

    def test_nightmare_masks_more_than_hard_for_free_and_crossword(self):
        for tier in (4, 5, 6):
            hard_total = sum(MASK_PROBABILITIES["困难"][tier].values())
            nightmare_total = sum(MASK_PROBABILITIES["噩梦"][tier].values())
            self.assertGreater(nightmare_total, hard_total)
        self.assertEqual(BonusGuessApp.difficulty_label_for_value(None, 10), "噩梦")

    def test_nightmare_crossword_size_extends_hard(self):
        self.assertGreater(size_for_difficulty("噩梦"), size_for_difficulty("困难"))


if __name__ == "__main__":
    unittest.main()
