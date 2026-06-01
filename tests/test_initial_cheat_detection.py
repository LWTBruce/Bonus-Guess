from types import SimpleNamespace
import unittest

from backend.app_modules.crossword import CrosswordMixin
from backend.app_modules.round_play import RoundPlayMixin


class DummyRound(RoundPlayMixin):
    def __init__(self, chinese, initials, pinyin, play_mode="\u81ea\u7531"):
        self.play_mode = play_mode
        self.custom_mode = False
        self.custom_config = {}
        self.rank_mode = False
        self.rank_kind = ""
        self.current = SimpleNamespace(chinese=chinese, initials=initials, pinyin=pinyin)


class DummyCrossword(CrosswordMixin, RoundPlayMixin):
    def __init__(self, answer, initials, pinyin):
        self.placement = SimpleNamespace(
            answer=answer,
            initials=initials,
            term=SimpleNamespace(pinyin=pinyin),
        )

    def crossword_selected_placement(self):
        return self.placement


class InitialCheatDetectionTests(unittest.TestCase):
    def test_single_character_terms_do_not_block_pinyin_input(self):
        round_play = DummyRound("\u71b5", "S", "shang")

        self.assertFalse(round_play.contains_blocked_initials("S"))
        self.assertFalse(round_play.contains_blocked_initials("SHANG"))

    def test_pinyin_text_that_contains_initials_is_allowed(self):
        round_play = DummyRound("\u6d4b\u8bd5", "CS", "xcsao")

        self.assertFalse(round_play.contains_blocked_initials("CS"))
        self.assertFalse(round_play.contains_blocked_initials("XCSAO"))

    def test_direct_initials_are_still_blocked_when_not_pinyin_input(self):
        round_play = DummyRound("\u8d28\u70b9", "ZD", "zhidian")

        self.assertTrue(round_play.contains_blocked_initials("ZD"))

    def test_clue_mode_still_skips_initial_cheat_detection(self):
        round_play = DummyRound("\u8d28\u70b9", "ZD", "zhidian", play_mode="\u7ebf\u7d22")

        self.assertFalse(round_play.contains_blocked_initials("ZD"))

    def test_crossword_single_character_terms_do_not_block_pinyin_input(self):
        crossword = DummyCrossword("\u71b5", "S", "shang")

        self.assertFalse(crossword.crossword_contains_blocked_initials("S"))
        self.assertFalse(crossword.crossword_contains_blocked_initials("SHANG"))

    def test_crossword_direct_initials_are_still_blocked_when_not_pinyin_input(self):
        crossword = DummyCrossword("\u8d28\u70b9", "ZD", "zhidian")

        self.assertTrue(crossword.crossword_contains_blocked_initials("ZD"))


if __name__ == "__main__":
    unittest.main()
