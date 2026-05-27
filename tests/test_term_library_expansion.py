import csv
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from app import BonusGuessApp  # noqa: E402
from term_library import TermLibrary  # noqa: E402


REQUESTED_WORD_LISTS = [
    "words/物理/普通模式：四大力学/continuum_mechanics_terms.csv",
    "words/物理/困难模式：四大方向/cosmology_terms.csv",
    "words/物理/困难模式：四大方向/quantum_information_terms.csv",
    "words/物理/噩梦模式：前沿物理/superstring_m_theory_terms.csv",
    "words/物理/噩梦模式：前沿物理/loop_quantum_gravity_terms.csv",
    "words/物理/噩梦模式：前沿物理/conformal_field_theory_terms.csv",
    "words/物理/噩梦模式：前沿物理/holographic_principle_terms.csv",
    "words/物理/噩梦模式：前沿物理/topological_quantum_field_theory_terms.csv",
    "words/物理/噩梦模式：前沿物理/noncommutative_geometry_physics_terms.csv",
    "words/物理/噩梦模式：前沿物理/quantum_gravity_black_hole_information_terms.csv",
    "words/物理/噩梦模式：前沿物理/advanced_qcd_terms.csv",
    "words/数学/简单模式/analytic_geometry_terms.csv",
    "words/数学/简单模式/elementary_number_theory_terms.csv",
    "words/数学/简单模式/combinatorics_basics_terms.csv",
    "words/数学/普通模式/calculus_of_variations_terms.csv",
    "words/数学/普通模式/integral_equations_terms.csv",
    "words/数学/普通模式/vector_tensor_analysis_terms.csv",
    "words/数学/普通模式/operations_research_terms.csv",
    "words/数学/困难模式/differential_geometry_terms.csv",
    "words/数学/困难模式/algebraic_geometry_terms.csv",
    "words/数学/困难模式/lie_groups_lie_algebras_terms.csv",
    "words/数学/困难模式/homological_algebra_terms.csv",
    "words/数学/噩梦模式/operator_algebras_terms.csv",
    "words/数学/噩梦模式/noncommutative_geometry_terms.csv",
    "words/数学/噩梦模式/advanced_representation_theory_terms.csv",
    "words/数学/噩梦模式/moduli_space_theory_terms.csv",
    "words/数学/噩梦模式/arithmetic_geometry_terms.csv",
    "words/数学/噩梦模式/geometric_analysis_terms.csv",
    "words/数学/噩梦模式/random_matrix_theory_terms.csv",
    "words/数学/噩梦模式/spectral_geometry_terms.csv",
    "words/数学/噩梦模式/derived_categories_terms.csv",
    "words/数学/噩梦模式/mathematical_quantum_groups_terms.csv",
]

PHYSICS_NIGHTMARE_PREFIX_GUARD = {
    "words/物理/噩梦模式：前沿物理/superstring_m_theory_terms.csv": "超弦理论",
    "words/物理/噩梦模式：前沿物理/loop_quantum_gravity_terms.csv": "圈量子引力",
    "words/物理/噩梦模式：前沿物理/conformal_field_theory_terms.csv": "共形场论",
    "words/物理/噩梦模式：前沿物理/holographic_principle_terms.csv": "全息原理",
    "words/物理/噩梦模式：前沿物理/topological_quantum_field_theory_terms.csv": "拓扑量子场论",
    "words/物理/噩梦模式：前沿物理/noncommutative_geometry_physics_terms.csv": "非对易几何",
    "words/物理/噩梦模式：前沿物理/quantum_gravity_black_hole_information_terms.csv": "量子引力黑洞信息",
    "words/物理/噩梦模式：前沿物理/advanced_qcd_terms.csv": "进阶QCD",
}


class TermLibraryExpansionTests(unittest.TestCase):
    def test_requested_word_lists_have_at_least_100_complete_rows(self):
        required_columns = [
            "概念中文名",
            "难度",
            "中文首字母",
            "中文首字母串长度",
            "概念英文名",
            "英文字符串长度",
            "概念中文拼音",
            "拼音字符串长度",
        ]
        for rel_path in REQUESTED_WORD_LISTS:
            with self.subTest(path=rel_path):
                rows = self.read_rows(rel_path)
                self.assertGreaterEqual(len(rows), 100)
                names = [row["概念中文名"].strip() for row in rows]
                duplicates = [name for name, count in Counter(names).items() if count > 1]
                self.assertEqual(duplicates, [])
                for row in rows:
                    for column in required_columns:
                        self.assertTrue(str(row.get(column, "")).strip(), f"{rel_path} missing {column}")

    def test_expanded_modes_have_no_duplicate_chinese_terms(self):
        for subject, difficulty in [
            ("物理", "普通"),
            ("物理", "困难"),
            ("物理", "噩梦"),
            ("数学", "简单"),
            ("数学", "普通"),
            ("数学", "困难"),
            ("数学", "噩梦"),
        ]:
            with self.subTest(subject=subject, difficulty=difficulty):
                names = []
                for file in self.mode_files(subject, difficulty):
                    names.extend(row["概念中文名"].strip() for row in self.read_rows(file))
                duplicates = [name for name, count in Counter(names).items() if count > 1]
                self.assertEqual(duplicates, [])

    def test_nightmare_terms_load_through_term_library(self):
        library = TermLibrary(ROOT / "words")
        for mode in ("物理模式", "数学模式"):
            with self.subTest(mode=mode):
                terms, files = library.load(mode, "噩梦")
                self.assertGreaterEqual(len(terms), 100)
                self.assertTrue(all("噩梦" in str(file.parent.name) for file in files))

    def test_physics_nightmare_lists_are_not_mechanical_prefix_expansions(self):
        for rel_path, prefix in PHYSICS_NIGHTMARE_PREFIX_GUARD.items():
            with self.subTest(path=rel_path):
                names = [row["概念中文名"].strip() for row in self.read_rows(rel_path)]
                prefixed = [name for name in names if name.startswith(prefix) and name != prefix]
                self.assertLessEqual(len(prefixed), 3, prefixed[:5])

    def test_clue_true_random_filters_nightmare_terms(self):
        app = BonusGuessApp.__new__(BonusGuessApp)
        app.library = TermLibrary(ROOT / "words")
        app.terms, app.library_files = app.library.load_all()
        app.true_random_mode = True
        app.mode = "真·随机"
        app.random_group_mode = True
        app.remove_nightmare_terms_from_clue_scope("真·随机")
        self.assertTrue(app.terms)
        self.assertFalse(any("噩梦" in file.parent.name for file in app.library_files))
        self.assertIn("入门到困难", app.scope_text)

    @staticmethod
    def read_rows(path):
        file = path if isinstance(path, Path) else ROOT / path
        with file.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def mode_files(subject, difficulty):
        base = ROOT / "words" / subject
        files = []
        for folder in base.iterdir():
            if folder.is_dir() and folder.name.startswith(difficulty):
                files.extend(sorted(folder.glob("*.csv")))
        return files


if __name__ == "__main__":
    unittest.main()
