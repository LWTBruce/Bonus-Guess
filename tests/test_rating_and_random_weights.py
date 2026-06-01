import sys
import random
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

import records  # noqa: E402
from records import (  # noqa: E402
    RATING_CAP,
    choose_term_by_difficulty,
    group_terms_by_difficulty_mode,
    record_single_rating,
    score_weight_for_difficulty,
    summarize_rating,
)
from backend.app_modules.crossword import CrosswordMixin  # noqa: E402


class RatingAndRandomWeightTests(unittest.TestCase):
    def test_total_score_weights_match_current_rules(self):
        expected = {
            "入门": 0.1,
            "简单": 0.2,
            "普通": 0.3,
            "困难": 0.4,
            "噩梦": 0.6,
            "混合模式": 0.3,
            "真·随机": 0.3,
        }
        for difficulty, weight in expected.items():
            self.assertEqual(score_weight_for_difficulty(difficulty), weight)

    def test_random_modes_choose_difficulty_mode_before_term(self):
        terms = [
            SimpleNamespace(chinese="入门词", difficulty=1),
            SimpleNamespace(chinese="简单词", difficulty=3),
            SimpleNamespace(chinese="普通词", difficulty=5),
            SimpleNamespace(chinese="困难词", difficulty=8),
            SimpleNamespace(chinese="噩梦词", difficulty=11),
        ]
        buckets = group_terms_by_difficulty_mode(terms)
        self.assertEqual(set(buckets), {"入门", "简单", "普通", "困难", "噩梦"})

        old_choice = records.random.choice
        old_choices = records.random.choices
        try:
            records.random.choice = lambda values: "困难"
            records.random.choices = lambda population, weights, k: [population[0]]
            chosen = choose_term_by_difficulty(terms, "真·随机")
        finally:
            records.random.choice = old_choice
            records.random.choices = old_choices
        self.assertEqual(chosen.chinese, "困难词")

    def test_crossword_pool_selects_half_of_source_tables_with_equal_quota(self):
        terms = []
        for table_index in range(4):
            for term_index in range(100):
                terms.append(SimpleNamespace(
                    chinese=f"{table_index}-{term_index}",
                    difficulty=5,
                    source=f"table_{table_index}.csv",
                    source_label=f"表{table_index}",
                ))
        balanced = CrosswordMixin.balanced_crossword_terms_by_source_table(terms, max_words=5, rng=random.Random(1))
        table_counts = {}
        for term in balanced:
            table_counts[term.source] = table_counts.get(term.source, 0) + 1
        self.assertEqual(len(table_counts), 2)
        self.assertEqual(set(table_counts.values()), {35})

    def test_rating_cap_is_twenty_point_five_and_nightmare_can_reach_it(self):
        record = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "success": True,
            "score": 1000,
            "score_start": 1000,
            "elapsed_seconds": 0,
            "difficulty": "噩梦",
            "effective_difficulty": 12,
            "selected_answer": "超弦理论",
            "mode": "物理模式",
            "play_mode": "自由",
        }
        self.assertEqual(RATING_CAP, 20.5)
        self.assertEqual(record_single_rating(record), 20.5)

    def test_rating_summary_caps_after_b20_and_r10(self):
        now = datetime.now()
        records_for_rating = []
        for index in range(25):
            records_for_rating.append({
                "created_at": (now + timedelta(seconds=index)).isoformat(timespec="seconds"),
                "success": True,
                "score": 1000,
                "score_start": 1000,
                "elapsed_seconds": 0,
                "difficulty": "噩梦",
                "effective_difficulty": 12,
                "selected_answer": f"噩梦词{index}",
                "mode": "物理模式",
                "play_mode": "自由",
            })
        summary = summarize_rating(records_for_rating, include_achievements=False)
        self.assertEqual(summary["best_average"], 20.5)
        self.assertEqual(summary["recent_average"], 20.5)
        self.assertEqual(summary["play_rating"], 20.5)
        self.assertEqual(summary["rating"], 20.5)


if __name__ == "__main__":
    unittest.main()
