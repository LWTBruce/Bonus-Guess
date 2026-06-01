import json
import re
import sys
import unittest
import csv
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from clue_library import ClueLibrary  # noqa: E402
from term_library import Term  # noqa: E402


PHYSICS_EXPLANATION_MODES = [
    "入门模式：高中物理",
    "简单模式：普通物理",
    "普通模式：四大力学",
    "困难模式：四大方向",
    "噩梦模式：前沿物理",
]

MATH_EXPLANATION_MODES = [
    "入门模式：高中数学",
    "简单模式",
    "普通模式",
    "困难模式",
    "噩梦模式",
]

EXPLANATION_MODE_GROUPS = {
    "物理": PHYSICS_EXPLANATION_MODES,
    "数学": MATH_EXPLANATION_MODES,
}

EMPTY_CLUE_JSONS = {
    "clues/物理/普通模式：四大力学/continuum_mechanics_terms.json",
    "clues/物理/困难模式：四大方向/cosmology_terms.json",
    "clues/物理/困难模式：四大方向/quantum_information_terms.json",
    "clues/物理/噩梦模式：前沿物理/advanced_qcd_terms.json",
    "clues/物理/噩梦模式：前沿物理/conformal_field_theory_terms.json",
    "clues/物理/噩梦模式：前沿物理/holographic_principle_terms.json",
    "clues/物理/噩梦模式：前沿物理/loop_quantum_gravity_terms.json",
    "clues/物理/噩梦模式：前沿物理/noncommutative_geometry_physics_terms.json",
    "clues/物理/噩梦模式：前沿物理/quantum_gravity_black_hole_information_terms.json",
    "clues/物理/噩梦模式：前沿物理/superstring_m_theory_terms.json",
    "clues/物理/噩梦模式：前沿物理/topological_quantum_field_theory_terms.json",
    "clues/数学/简单模式/analytic_geometry_terms.json",
    "clues/数学/简单模式/combinatorics_basics_terms.json",
    "clues/数学/简单模式/elementary_number_theory_terms.json",
    "clues/数学/普通模式/calculus_of_variations_terms.json",
    "clues/数学/普通模式/integral_equations_terms.json",
    "clues/数学/普通模式/operations_research_terms.json",
    "clues/数学/普通模式/vector_tensor_analysis_terms.json",
    "clues/数学/困难模式/algebraic_geometry_terms.json",
    "clues/数学/困难模式/differential_geometry_terms.json",
    "clues/数学/困难模式/homological_algebra_terms.json",
    "clues/数学/困难模式/lie_groups_lie_algebras_terms.json",
    "clues/数学/噩梦模式/advanced_algebraic_geometry_terms.json",
    "clues/数学/噩梦模式/advanced_representation_theory_terms.json",
    "clues/数学/噩梦模式/arithmetic_geometry_terms.json",
    "clues/数学/噩梦模式/derived_categories_terms.json",
    "clues/数学/噩梦模式/mathematical_quantum_groups_terms.json",
    "clues/数学/噩梦模式/moduli_space_theory_terms.json",
    "clues/数学/噩梦模式/noncommutative_geometry_terms.json",
    "clues/数学/噩梦模式/operator_algebras_terms.json",
    "clues/数学/噩梦模式/random_matrix_theory_terms.json",
    "clues/数学/噩梦模式/spectral_geometry_terms.json",
}

DISALLOWED_FOCUS_PHRASES = [
    "在高中题目中",
    "在电路题中",
    "在磁场题中",
    "在电磁感应和交流题中",
    "在题目中",
    "题目中",
    "解题时",
    "做题时",
    "分析时",
    "判断时",
    "这个式子把概念同可测量量联系起来",
    "这个关系把概念同可测量量联系起来",
    "它的价值在于把",
    "必要时还可以",
    "若条件改变，应重新确认",
    "这个关系把概念同可测量量联系起来，也提示哪些量依赖过程、材料或平衡条件",
    "这个式子把概念同可测量量联系起来，并明确哪些量由坐标、参考点或过程约束决定",
]

MATH_TEMPLATE_PHRASES = [
    "常用关系可写作",
    "这个式子把",
    "这个关系把",
    "边界也很重要",
    "这样既保留",
    "这些概念的共同特点",
    "使用时还要注意定义范围和特殊情形",
    "常出现在常用来",
    "好处是，",
]


def han_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def has_unwanted_control(text):
    return any((ord(char) < 32 and char != "\n") for char in text)


def md_formulas(text):
    return re.findall(r"\$([^$]+)\$", text)


def read_json_entries(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["entries"]


def read_csv_terms(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def explanation_csv_paths():
    for subject, modes in EXPLANATION_MODE_GROUPS.items():
        for mode in modes:
            yield from sorted((ROOT / "words" / subject / mode).glob("*.csv"))


class TermExplanationTests(unittest.TestCase):
    def test_high_school_electromagnetism_explanations_are_complete(self):
        path = next((ROOT / "clues").rglob("high_school_electromagnetism_terms.json"))
        entries = read_json_entries(path)

        self.assertEqual(len(entries), 59)
        for entry in entries:
            explanation = entry.get("explanation_markdown", "")
            count = han_count(explanation)
            self.assertIn("$", explanation, entry.get("chinese_name"))
            self.assertGreaterEqual(count, 200, entry.get("chinese_name"))
            self.assertLessEqual(count, 320, entry.get("chinese_name"))
            self.assertLessEqual(explanation.count("\n\n") + 1, 3, entry.get("chinese_name"))
            for phrase in DISALLOWED_FOCUS_PHRASES:
                self.assertNotIn(phrase, explanation, entry.get("chinese_name"))

    def test_target_explanations_are_complete(self):
        for csv_path in explanation_csv_paths():
            with self.subTest(csv=csv_path.relative_to(ROOT).as_posix()):
                subject = csv_path.relative_to(ROOT / "words").parts[0]
                json_path = (ROOT / "clues" / csv_path.relative_to(ROOT / "words")).with_suffix(".json")
                self.assertTrue(json_path.exists(), json_path.relative_to(ROOT).as_posix())

                rows = read_csv_terms(csv_path)
                entries = read_json_entries(json_path)
                self.assertEqual(len(entries), len(rows), json_path.relative_to(ROOT).as_posix())

                for entry in entries:
                    name = entry.get("chinese_name")
                    explanation = entry.get("explanation_markdown", "")
                    count = han_count(explanation)
                    self.assertGreaterEqual(count, 200, name)
                    self.assertLessEqual(count, 320, name)
                    self.assertGreaterEqual(explanation.count("$"), 2, name)
                    self.assertLessEqual(explanation.count("\n\n") + 1, 3, name)
                    self.assertFalse(has_unwanted_control(explanation), name)
                    self.assertNotIn("，，", explanation, name)
                    if subject == "数学":
                        self.assertFalse(explanation.startswith(f"{name}是{name}"), name)
                        self.assertNotIn(f"主要用来描述{name}", explanation, name)
                        for phrase in MATH_TEMPLATE_PHRASES:
                            self.assertNotIn(phrase, explanation, name)
                    for formula in md_formulas(explanation):
                        self.assertNotRegex(formula, r"[\n\r\t]", name)
                    for phrase in DISALLOWED_FOCUS_PHRASES:
                        self.assertNotIn(phrase, explanation, name)

    def test_target_explanations_have_source_links(self):
        for csv_path in explanation_csv_paths():
            with self.subTest(csv=csv_path.relative_to(ROOT).as_posix()):
                json_path = (ROOT / "clues" / csv_path.relative_to(ROOT / "words")).with_suffix(".json")
                entries = read_json_entries(json_path)
                for entry in entries:
                    name = entry.get("chinese_name")
                    links = entry.get("source_links")
                    self.assertIsInstance(links, list, name)
                    self.assertGreaterEqual(len(links), 2, name)
                    labels = {str(link.get("label") or "") for link in links if isinstance(link, dict)}
                    self.assertIn("百度百科", labels, name)
                    self.assertTrue({"维基百科", "Wikipedia"} & labels, name)
                    for link in links:
                        self.assertIsInstance(link, dict, name)
                        self.assertTrue(str(link.get("label") or "").strip(), name)
                        self.assertTrue(str(link.get("title") or "").strip(), name)
                        url = str(link.get("url") or "").strip()
                        parsed = urlparse(url)
                        self.assertIn(parsed.scheme, {"http", "https"}, name)
                        self.assertTrue(parsed.netloc, name)

    def test_placeholder_clues_stay_empty_for_created_jsons(self):
        for relative_path in sorted(EMPTY_CLUE_JSONS):
            path = ROOT / relative_path
            with self.subTest(path=relative_path):
                self.assertTrue(path.exists(), relative_path)
                entries = read_json_entries(path)
                for entry in entries:
                    self.assertEqual(entry.get("complete_clues"), [], entry.get("chinese_name"))
                    self.assertEqual(entry.get("fragmented_clues"), [], entry.get("chinese_name"))

    def test_clue_library_loads_explanation_markdown(self):
        source = "words/物理/入门模式：高中物理/high_school_electromagnetism_terms.csv"
        term = Term(source, "高中电磁学", "1", "电荷", 1, "DH", "electric_charge", "dianhe")

        entry = ClueLibrary(ROOT / "clues").get(term)

        self.assertIn("explanation_markdown", entry)
        self.assertIn("电荷是物体参与电相互作用", entry["explanation_markdown"])
        self.assertIn("$q=ne$", entry["explanation_markdown"])
        self.assertGreaterEqual(len(entry.get("source_links") or []), 2)

    def test_clue_library_loads_explanation_when_clues_are_empty(self):
        source = "words/物理/普通模式：四大力学/continuum_mechanics_terms.csv"
        term = Term(source, "连续介质力学", "7", "连续介质力学", 7, "LXJZLX", "continuum_mechanics", "lianxujiezhilixue")

        entry = ClueLibrary(ROOT / "clues").get(term)

        self.assertEqual(entry["source_type"], "fallback")
        self.assertEqual(len(entry["complete"]), 5)
        self.assertEqual(len(entry["fragments"]), 5)
        self.assertIn("explanation_markdown", entry)
        self.assertIn("连续介质力学把固体、流体和软材料", entry["explanation_markdown"])
        self.assertGreaterEqual(len(entry.get("source_links") or []), 2)


if __name__ == "__main__":
    unittest.main()
