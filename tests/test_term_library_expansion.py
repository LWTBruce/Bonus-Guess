import csv
import re
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

MATH_PREFIX_GUARD = {
    "words/数学/简单模式/analytic_geometry_terms.csv": "解析几何",
    "words/数学/简单模式/elementary_number_theory_terms.csv": "初等数论",
    "words/数学/简单模式/combinatorics_basics_terms.csv": "组合",
    "words/数学/普通模式/calculus_of_variations_terms.csv": "变分法",
    "words/数学/普通模式/integral_equations_terms.csv": "积分方程",
    "words/数学/普通模式/vector_tensor_analysis_terms.csv": "张量分析",
    "words/数学/普通模式/operations_research_terms.csv": "运筹学",
    "words/数学/困难模式/differential_geometry_terms.csv": "微分几何",
    "words/数学/困难模式/algebraic_geometry_terms.csv": "代数几何",
    "words/数学/困难模式/lie_groups_lie_algebras_terms.csv": "李群",
    "words/数学/困难模式/homological_algebra_terms.csv": "同调代数",
    "words/数学/噩梦模式/operator_algebras_terms.csv": "算子代数",
    "words/数学/噩梦模式/noncommutative_geometry_terms.csv": "非交换几何",
    "words/数学/噩梦模式/advanced_representation_theory_terms.csv": "表示论",
    "words/数学/噩梦模式/moduli_space_theory_terms.csv": "模空间",
    "words/数学/噩梦模式/arithmetic_geometry_terms.csv": "算术几何",
    "words/数学/噩梦模式/geometric_analysis_terms.csv": "几何分析",
    "words/数学/噩梦模式/random_matrix_theory_terms.csv": "随机矩阵",
    "words/数学/噩梦模式/spectral_geometry_terms.csv": "谱几何",
    "words/数学/噩梦模式/derived_categories_terms.csv": "导出范畴",
    "words/数学/噩梦模式/mathematical_quantum_groups_terms.csv": "量子群",
}

ALLOWED_CHINESE_NAME_ASCII_TOKENS = {
    "A",
    "ADM",
    "ADHM",
    "AdS",
    "AdS2",
    "AKSZ",
    "AMPS",
    "APS",
    "B",
    "BB84",
    "BCS",
    "BDF",
    "BF",
    "BFSS",
    "BFKL",
    "BMO",
    "BMS",
    "BPZ",
    "BQP",
    "BRST",
    "BTZ",
    "BV",
    "C",
    "CDM",
    "CFL",
    "CFT",
    "CG",
    "CMB",
    "CP",
    "CW",
    "D",
    "D0",
    "D1",
    "D1D5",
    "D3",
    "D5",
    "D7",
    "DNA",
    "DGLAP",
    "E",
    "E8E8",
    "E91",
    "EM",
    "EPR",
    "EPRL",
    "ER",
    "F",
    "FK",
    "G",
    "GFT",
    "GHZ",
    "GKPW",
    "GSO",
    "H",
    "HHL",
    "HOMFLY",
    "HaPPY",
    "I",
    "IIA",
    "IIB",
    "IKKT",
    "J",
    "JLMS",
    "K",
    "K3",
    "KO",
    "KKLT",
    "KSS",
    "L",
    "LDPC",
    "LLM",
    "LQG",
    "LSZ",
    "LU",
    "Lp",
    "M",
    "M2",
    "M5",
    "MCMC",
    "MERA",
    "MSbar",
    "N",
    "NCOS",
    "N1",
    "N2",
    "N4",
    "NFW",
    "NHEK",
    "NISQ",
    "NRQCD",
    "NS5",
    "NSNS",
    "O",
    "OM",
    "OPE",
    "OTOC",
    "OZI",
    "P",
    "PBH",
    "PCAC",
    "POVM",
    "Q",
    "QCD",
    "QMA",
    "QR",
    "R",
    "RG",
    "RNA",
    "RNS",
    "RR",
    "S",
    "S8",
    "SCET",
    "SL2C",
    "SO32",
    "SOR",
    "SU2",
    "SWAP",
    "SYK",
    "T",
    "T0",
    "T1",
    "T2",
    "TE",
    "TEM",
    "TM",
    "TQFT",
    "U",
    "U1A",
    "UVIR",
    "V",
    "W",
    "WKB",
    "WZW",
    "X",
    "Y",
    "Z",
    "a",
    "bc",
    "c",
    "d",
    "dS",
    "g",
    "k",
    "l",
    "m",
    "n",
    "p",
    "pn",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
}

BANNED_CHINESE_NAME_FRAGMENTS = [
    "杀矢量",
    "基林型",
]


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

    def test_expanded_lists_are_not_mechanical_prefix_expansions(self):
        guards = {**PHYSICS_NIGHTMARE_PREFIX_GUARD, **MATH_PREFIX_GUARD}
        for rel_path, prefix in guards.items():
            with self.subTest(path=rel_path):
                names = [row["概念中文名"].strip() for row in self.read_rows(rel_path)]
                prefixed = [name for name in names if name.startswith(prefix) and name != prefix]
                self.assertLessEqual(len(prefixed), 3, prefixed[:5])

    def test_chinese_names_only_keep_allowed_ascii_abbreviations(self):
        offenders = []
        for file in self.word_files():
            for row in self.read_rows(file):
                name = row["概念中文名"].strip()
                tokens = re.findall(r"[A-Za-z][A-Za-z0-9]*", name)
                bad_tokens = [
                    token
                    for token in tokens
                    if token not in ALLOWED_CHINESE_NAME_ASCII_TOKENS and len(token) > 1
                ]
                if bad_tokens:
                    offenders.append((str(file.relative_to(ROOT)), name, bad_tokens))
        self.assertEqual(offenders, [])

    def test_chinese_names_do_not_use_known_bad_translations(self):
        offenders = []
        for file in self.word_files():
            for row in self.read_rows(file):
                name = row["概念中文名"].strip()
                bad_fragments = [fragment for fragment in BANNED_CHINESE_NAME_FRAGMENTS if fragment in name]
                if bad_fragments:
                    offenders.append((str(file.relative_to(ROOT)), name, bad_fragments))
        self.assertEqual(offenders, [])

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

    @staticmethod
    def word_files():
        return sorted((ROOT / "words").rglob("*.csv"))


if __name__ == "__main__":
    unittest.main()
