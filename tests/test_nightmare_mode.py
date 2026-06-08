import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from app import BonusGuessApp  # noqa: E402
from crossword_puzzle import size_for_difficulty, target_density_for_difficulty, target_word_count_for_size  # noqa: E402
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
        self.assertEqual(BonusGuessApp.difficulty_label_for_value(None, 10), "困难")
        self.assertEqual(BonusGuessApp.difficulty_label_for_value(None, 11), "噩梦")

    def test_nightmare_crossword_size_extends_hard(self):
        self.assertGreater(size_for_difficulty("噩梦"), size_for_difficulty("困难"))
        self.assertEqual(BonusGuessApp.crossword_rank_size_for_id(None, 1), 8)
        self.assertEqual(BonusGuessApp.crossword_rank_size_for_id(None, 20), 30)
        self.assertEqual(BonusGuessApp.crossword_rank_seconds_for_id(None, 1), 8 * 60)
        self.assertEqual(BonusGuessApp.crossword_rank_seconds_for_id(None, 20), 25 * 60)
        self.assertEqual(BonusGuessApp.crossword_rank_word_count_for_id(None, 20), 92)

    def test_crossword_word_count_uses_density_targets(self):
        self.assertAlmostEqual(target_density_for_difficulty("简单"), 0.60)
        self.assertAlmostEqual(target_density_for_difficulty("普通"), 0.65)
        self.assertAlmostEqual(target_density_for_difficulty("困难"), 0.70)
        self.assertAlmostEqual(target_density_for_difficulty("噩梦"), 0.75)
        self.assertEqual(target_word_count_for_size(11, difficulty="简单"), 25)
        self.assertEqual(target_word_count_for_size((11, 11), difficulty="简单", cell_shape="hex"), 25)
        self.assertGreater(target_word_count_for_size(22, difficulty="噩梦"), target_word_count_for_size(18, difficulty="困难"))

    def test_high_crossword_ranks_reach_nightmare_term_windows(self):
        self.assertEqual(BonusGuessApp.crossword_rank_difficulty_window_for_id(None, 16), (9, 11, 10.0))
        self.assertEqual(BonusGuessApp.crossword_rank_difficulty_window_for_id(None, 20), (11, 12, 12.0))
        _low, high, _center = BonusGuessApp.crossword_rank_difficulty_window_for_id(None, 16)
        self.assertEqual(BonusGuessApp.difficulty_label_for_value(None, high), "噩梦")

    def test_physics_nightmare_terms_include_difficulty_above_ten(self):
        library = TermLibrary(ROOT / "words")
        terms, _files = library.load("物理模式", "噩梦")
        difficulties = {term.difficulty for term in terms}
        self.assertIn(11, difficulties)
        self.assertIn(12, difficulties)


if __name__ == "__main__":
    unittest.main()
