import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_nightmare_masks_match_hard_until_eight_initials(self):
        for tier in (4, 5, 6):
            self.assertEqual(MASK_PROBABILITIES["噩梦"][tier], MASK_PROBABILITIES["困难"][tier])
        self.assertNotIn(4, MASK_PROBABILITIES["噩梦"][6])
        self.assertEqual(MASK_PROBABILITIES["噩梦"][8][4], 0.10)
        self.assertEqual(BonusGuessApp.difficulty_label_for_value(None, 10), "困难")
        self.assertEqual(BonusGuessApp.difficulty_label_for_value(None, 11), "噩梦")

    def test_crossword_mask_boost_adds_three_percentage_points(self):
        captured = {}

        def fake_choices(counts, weights=None, k=1):
            captured["counts"] = list(counts)
            captured["weights"] = list(weights or [])
            return [0]

        random_module = BonusGuessApp.crossword_random_mask_positions.__globals__["random"]
        with patch.object(random_module, "choices", side_effect=fake_choices):
            BonusGuessApp.crossword_random_mask_positions("ABCDEFGH", "噩梦")

        self.assertEqual(captured["counts"], [0, 1, 2, 3, 4])
        self.assertEqual([round(value, 2) for value in captured["weights"]], [0.18, 0.28, 0.23, 0.18, 0.13])

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
        self.assertAlmostEqual(target_density_for_difficulty("混合模式"), 0.68)
        self.assertEqual(target_word_count_for_size(11, difficulty="简单"), 25)
        self.assertEqual(target_word_count_for_size((11, 11), difficulty="简单", cell_shape="hex"), 25)
        self.assertEqual(size_for_difficulty("混合模式"), 15)
        self.assertGreater(target_word_count_for_size(22, difficulty="噩梦"), target_word_count_for_size(18, difficulty="困难"))

    def test_crossword_difficulty_page_includes_mixed_mode(self):
        source = inspect.getsource(BonusGuessApp.show_difficulty)
        self.assertIn('options.append(("混合模式"', source)
        self.assertNotIn('self.play_mode != "字谜"', source)

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
