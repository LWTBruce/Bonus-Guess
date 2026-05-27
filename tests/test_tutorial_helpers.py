import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from app import BonusGuessApp  # noqa: E402


class TutorialHintCostTests(unittest.TestCase):
    def test_library_hint_is_free_only_in_tutorial(self):
        self.assertEqual(BonusGuessApp.library_hint_penalty_cost(True, 210), 0)
        self.assertEqual(BonusGuessApp.library_hint_penalty_cost(False, 210), 210)


if __name__ == "__main__":
    unittest.main()
