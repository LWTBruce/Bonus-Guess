import csv
import re
import sys
import threading
import unicodedata
from pathlib import Path

try:
    from pypinyin import Style, pinyin
except Exception:
    Style = None
    pinyin = None


class Term:
    def __init__(self, source, source_label, number, chinese, difficulty, initials, english, pinyin):
        self.source = source
        self.source_label = source_label
        self.number = number
        self.chinese = chinese
        self.difficulty = difficulty
        self.initials = initials
        self.english = english
        self.pinyin = pinyin


class TermLibrary:
    MODE_DIRS = {
        "物理模式": "物理",
        "数学模式": "数学",
    }
    DIFFICULTIES = ["入门", "简单", "普通", "困难", "噩梦", "混合模式"]
    FILE_LABELS = {
        "mechanics_terms.csv": "普通物理力学",
        "electromagnetism_terms.csv": "普通物理电磁学",
        "thermal_terms.csv": "普通物理热学",
        "optics_terms.csv": "普通物理光学",
        "modern_physics_terms.csv": "近代物理",
        "theoretical_mechanics_terms.csv": "理论力学",
        "electrodynamics_terms.csv": "电动力学",
        "quantum_mechanics_terms.csv": "量子力学",
        "thermo_stat_mech_terms.csv": "热力学与统计力学",
        "原子分子光物理_terms.csv": "原子分子光物理",
        "天体物理_terms.csv": "天体物理",
        "固体物理_terms.csv": "固体物理",
        "核物理与粒子物理_terms.csv": "核物理与粒子物理",
        "广义相对论_terms.csv": "广义相对论",
        "量子场论_terms.csv": "量子场论",
        "continuum_mechanics_terms.csv": "连续介质力学",
        "cosmology_terms.csv": "宇宙学",
        "quantum_information_terms.csv": "量子信息",
        "superstring_m_theory_terms.csv": "超弦理论与M理论",
        "loop_quantum_gravity_terms.csv": "圈量子引力",
        "conformal_field_theory_terms.csv": "共形场论",
        "holographic_principle_terms.csv": "全息原理",
        "topological_quantum_field_theory_terms.csv": "拓扑量子场论",
        "noncommutative_geometry_physics_terms.csv": "非对易几何",
        "quantum_gravity_black_hole_information_terms.csv": "量子引力与黑洞信息悖论",
        "advanced_qcd_terms.csv": "进阶QCD",
        "advanced_calculus_terms.csv": "高等微积分",
        "mathematical_analysis_terms.csv": "数学分析",
        "linear_algebra_terms.csv": "线性代数",
        "analytic_geometry_terms.csv": "解析几何",
        "elementary_number_theory_terms.csv": "初等数论",
        "combinatorics_basics_terms.csv": "组合基础",
        "complex_analysis_terms.csv": "复变函数",
        "mathematical_physics_equations_terms.csv": "数学物理方程",
        "partial_differential_equations_terms.csv": "偏微分方程",
        "ordinary_differential_equations_terms.csv": "常微分方程",
        "numerical_analysis_terms.csv": "数值分析",
        "probability_theory_terms.csv": "概率论",
        "mathematical_statistics_terms.csv": "数理统计",
        "calculus_of_variations_terms.csv": "变分法",
        "integral_equations_terms.csv": "积分方程",
        "vector_tensor_analysis_terms.csv": "向量张量分析",
        "operations_research_terms.csv": "运筹学",
        "field_theory_terms.csv": "场论",
        "group_theory_terms.csv": "群论",
        "topology_terms.csv": "拓扑学",
        "real_analysis_terms.csv": "实分析",
        "complex_analysis_advanced_terms.csv": "复分析",
        "functional_analysis_terms.csv": "泛函分析",
        "statistical_inference_terms.csv": "统计推断",
        "measure_and_integration_terms.csv": "测度与积分",
        "differential_geometry_terms.csv": "微分几何",
        "algebraic_geometry_terms.csv": "代数几何",
        "lie_groups_lie_algebras_terms.csv": "李群李代数",
        "homological_algebra_terms.csv": "同调代数",
        "operator_algebras_terms.csv": "算子代数",
        "noncommutative_geometry_terms.csv": "非交换几何",
        "noncommutative_geometry_math_terms.csv": "非交换几何",
        "advanced_representation_theory_terms.csv": "表示论（进阶）",
        "moduli_space_theory_terms.csv": "模空间理论",
        "arithmetic_geometry_terms.csv": "算术几何",
        "advanced_algebraic_geometry_terms.csv": "代数几何（进阶）",
        "random_matrix_theory_terms.csv": "随机矩阵理论",
        "spectral_geometry_terms.csv": "谱几何",
        "derived_categories_terms.csv": "导范畴",
        "mathematical_quantum_groups_terms.csv": "数学量子群",
        "high_school_mechanics_terms.csv": "高中物理力学",
        "high_school_electromagnetism_terms.csv": "高中物理电磁学",
        "high_school_thermal_terms.csv": "高中物理热学",
        "high_school_optics_terms.csv": "高中物理光学",
        "high_school_sets_functions_terms.csv": "高中数学集合与函数",
        "high_school_trigonometry_vectors_terms.csv": "高中数学三角函数与向量",
        "high_school_geometry_terms.csv": "高中数学几何",
        "high_school_sequences_inequalities_terms.csv": "高中数学数列与不等式",
        "high_school_probability_statistics_terms.csv": "高中数学概率与统计",
    }

    def __init__(self, root):
        self.root = root
        set_person_name_directory(self.root / "人名")
        self.mode_initials = {}
        self.mode_initial_keys = {}
        self._csv_cache = {}
        self._cache_lock = threading.RLock()

    def load(self, mode, difficulty):
        base_name = self.MODE_DIRS[mode]
        base = self.root / base_name
        if not base.exists():
            raise FileNotFoundError(f"找不到词库文件夹：{base_name}")

        if difficulty == "混合模式":
            folders = [p for p in base.iterdir() if p.is_dir()]
        else:
            folders = [p for p in base.iterdir() if p.is_dir() and p.name.startswith(difficulty)]

        files = []
        for folder in folders:
            files.extend(sorted(folder.glob("*.csv")))
        if not files:
            raise FileNotFoundError(f"没有找到 {mode} / {difficulty} 的 CSV 词库")

        terms = []
        seen = set()
        for file in files:
            terms.extend(self._read_csv(file, seen))
        if not terms:
            raise ValueError("词库为空")
        return terms, files

    def load_all(self):
        files = []
        for base_name in self.MODE_DIRS.values():
            base = self.root / base_name
            if base.exists():
                files.extend(sorted(base.rglob("*.csv")))
        if not files:
            raise FileNotFoundError("没有找到任何 CSV 词库")

        terms = []
        seen = set()
        for file in files:
            terms.extend(self._read_csv(file, seen))
        if not terms:
            raise ValueError("词库为空")
        return self._dedupe_terms_by_chinese(terms), files

    def load_all_for_difficulty(self, difficulty):
        files = []
        for base_name in self.MODE_DIRS.values():
            base = self.root / base_name
            if not base.exists():
                continue
            if difficulty == "混合模式":
                folders = [p for p in base.iterdir() if p.is_dir()]
            else:
                folders = [p for p in base.iterdir() if p.is_dir() and p.name.startswith(difficulty)]
            for folder in folders:
                files.extend(sorted(folder.glob("*.csv")))
        if not files:
            raise FileNotFoundError(f"没有找到随机 / {difficulty} 的 CSV 词库")

        terms = []
        seen = set()
        for file in files:
            terms.extend(self._read_csv(file, seen))
        if not terms:
            raise ValueError("词库为空")
        return self._dedupe_terms_by_chinese(terms), files

    @staticmethod
    def _dedupe_terms_by_chinese(terms):
        unique = []
        seen = set()
        for term in terms:
            key = str(getattr(term, "chinese", "") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(term)
        return unique

    def list_files(self, mode=None):
        modes = [mode] if mode in self.MODE_DIRS else list(self.MODE_DIRS)
        files = []
        for mode_name in modes:
            base = self.root / self.MODE_DIRS[mode_name]
            if base.exists():
                files.extend(sorted(base.rglob("*.csv")))
        return files

    def load_files(self, files):
        files = list(files)
        if not files:
            raise FileNotFoundError("没有选择任何 CSV 词库")
        terms = []
        seen = set()
        for file in files:
            terms.extend(self._read_csv(file, seen))
        if not terms:
            raise ValueError("词库为空")
        return terms, files

    def lookup_initials(self, chinese, mode=None):
        requested = str(chinese or "").strip()
        modes = [mode] if mode else list(self.MODE_DIRS)
        for mode_name in modes:
            self._ensure_initials_cache(mode_name)
            found = self.mode_initials[mode_name].get(requested)
            if found:
                return found
            requested_key = canonical_answer_text(requested)
            keys = self.mode_initial_keys.get(mode_name, {})
            if requested_key and requested_key in keys:
                return keys[requested_key]
            person_key = person_name_answer_key(requested)
            if person_key and person_key in keys:
                return keys[person_key]
        return None

    def warm_initials_cache(self, mode=None):
        modes = [mode] if mode else list(self.MODE_DIRS)
        for mode_name in modes:
            self._ensure_initials_cache(mode_name)

    def _ensure_initials_cache(self, mode_name):
        with self._cache_lock:
            if mode_name in self.mode_initials:
                return
            self.mode_initials[mode_name] = {}
            self.mode_initial_keys[mode_name] = {}
            base = self.root / self.MODE_DIRS[mode_name]
            if not base.exists():
                return
            seen = set()
            for file in sorted(base.rglob("*.csv")):
                for term in self._read_csv(file, seen):
                    self.mode_initials[mode_name].setdefault(term.chinese, term.initials)
                    for key in (canonical_answer_text(term.chinese), person_name_answer_key(term.chinese)):
                        if key:
                            self.mode_initial_keys[mode_name].setdefault(key, term.initials)

    def _read_csv(self, path, seen):
        cached_terms = self._read_csv_file(path)
        rows = []
        for term in cached_terms:
            key = (term.chinese, term.initials)
            if key in seen:
                continue
            seen.add(key)
            rows.append(term)
        return rows

    def _read_csv_file(self, path):
        path = Path(path)
        try:
            stat = path.stat()
            signature = (str(path), stat.st_mtime_ns, stat.st_size)
        except OSError:
            signature = (str(path), 0, 0)
        with self._cache_lock:
            cached = self._csv_cache.get(str(path))
            if cached and cached[0] == signature:
                return cached[1]
        rows = []
        source_label = self.file_label(path)
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 8:
                    continue
                chinese = row[1].strip()
                if len(row) >= 9:
                    difficulty = row[2].strip()
                    initials = row[3].strip().upper()
                    english = row[5].strip()
                    pinyin = row[7].strip()
                else:
                    difficulty = "3"
                    initials = row[2].strip().upper()
                    english = row[4].strip()
                    pinyin = row[6].strip()
                initials = normalize_term_initials(chinese, initials)
                if not chinese or not initials:
                    continue
                if difficulty not in {str(value) for value in range(1, 13)}:
                    difficulty = "5"
                rows.append(Term(path.name, source_label, row[0], chinese, int(difficulty), initials, english, pinyin))
        with self._cache_lock:
            self._csv_cache[str(path)] = (signature, rows)
        return rows

    def file_label(self, path):
        if path.name == "noncommutative_geometry_terms.csv":
            if any(str(part) == "物理" for part in path.parts):
                return "非对易几何"
            return "非交换几何"
        return self.FILE_LABELS.get(path.name, path.stem.replace("_terms", ""))

    def scope_text(self, files):
        labels = []
        seen = set()
        for path in sorted(files, key=lambda item: self.file_label(item)):
            label = self.file_label(path)
            if label not in seen:
                labels.append(label)
                seen.add(label)
        return "、".join(labels)


PINYIN_INITIAL_OVERRIDES = {
    "阿": "A",
    "艾": "A",
    "安": "A",
    "奥": "A",
    "爱": "A",
    "巴": "B",
    "贝": "B",
    "玻": "B",
    "布": "B",
    "德": "D",
    "狄": "D",
    "厄": "E",
    "法": "F",
    "费": "F",
    "伽": "G",
    "戈": "G",
    "哈": "H",
    "海": "H",
    "赫": "H",
    "霍": "H",
    "基": "J",
    "吉": "J",
    "柯": "K",
    "克": "K",
    "拉": "L",
    "朗": "L",
    "勒": "L",
    "洛": "L",
    "马": "M",
    "麦": "M",
    "闵": "M",
    "诺": "N",
    "欧": "O",
    "泡": "P",
    "普": "P",
    "切": "Q",
    "瑞": "R",
    "塞": "S",
    "薛": "X",
    "杨": "Y",
    "约": "Y",
}

GREEK_INITIALS = {
    "α": "Α",
    "β": "Β",
    "γ": "Γ",
    "δ": "Δ",
    "ϵ": "Ε",
    "ε": "Ε",
    "ζ": "Ζ",
    "η": "Η",
    "θ": "Θ",
    "ι": "Ι",
    "κ": "Κ",
    "λ": "Λ",
    "μ": "Μ",
    "ν": "Ν",
    "ξ": "Ξ",
    "ο": "Ο",
    "π": "Π",
    "ρ": "Ρ",
    "σ": "Σ",
    "ς": "Σ",
    "τ": "Τ",
    "υ": "Υ",
    "φ": "Φ",
    "χ": "Χ",
    "ψ": "Ψ",
    "ω": "Ω",
    "Α": "Α",
    "Β": "Β",
    "Γ": "Γ",
    "Δ": "Δ",
    "Ε": "Ε",
    "Ζ": "Ζ",
    "Η": "Η",
    "Θ": "Θ",
    "Ι": "Ι",
    "Κ": "Κ",
    "Λ": "Λ",
    "Μ": "Μ",
    "Ν": "Ν",
    "Ξ": "Ξ",
    "Ο": "Ο",
    "Π": "Π",
    "Ρ": "Ρ",
    "Σ": "Σ",
    "Τ": "Τ",
    "Υ": "Υ",
    "Φ": "Φ",
    "Χ": "Χ",
    "Ψ": "Ψ",
    "Ω": "Ω",
}

ANSWER_OPTIONAL_HYPHENS = "-－–—‑−"
# Person-name aliases are maintained in words/person-name Markdown tables.
PERSON_NAME_FRAGMENTS = ()

_PERSON_NAME_EXTRA_DIRS = []
_PERSON_NAME_CACHE = None
_PERSON_NAME_ALIAS_PAIR_CACHE = None
_PERSON_NAME_FRAGMENTS_CACHE = None
_PERSON_NAME_ANSWER_KEY_CACHE = {}
_CANONICAL_ANSWER_TEXT_CACHE = {}


def set_person_name_directory(path):
    global _PERSON_NAME_CACHE, _PERSON_NAME_ALIAS_PAIR_CACHE, _PERSON_NAME_FRAGMENTS_CACHE
    directory = Path(path)
    if directory not in _PERSON_NAME_EXTRA_DIRS:
        _PERSON_NAME_EXTRA_DIRS.insert(0, directory)
        _PERSON_NAME_CACHE = None
        _PERSON_NAME_ALIAS_PAIR_CACHE = None
        _PERSON_NAME_FRAGMENTS_CACHE = None
        _PERSON_NAME_ANSWER_KEY_CACHE.clear()
        _CANONICAL_ANSWER_TEXT_CACHE.clear()


def person_name_directories():
    directories = list(_PERSON_NAME_EXTRA_DIRS)
    module_root = Path(__file__).resolve().parents[1]
    directories.append(module_root / "words" / "人名")
    frozen_root = Path(getattr(sys, "_MEIPASS", module_root))
    directories.append(frozen_root / "words" / "人名")
    unique = []
    seen = set()
    for directory in directories:
        key = str(directory)
        if key in seen:
            continue
        seen.add(key)
        unique.append(directory)
    return unique


def split_person_aliases(value):
    text = str(value or "").strip()
    if not text:
        return []
    parts = re.split(r"[、,，;；/]+", text)
    return [part.strip() for part in parts if part.strip()]


def read_person_name_table(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text.startswith("|") or "---" in text:
            continue
        cells = [cell.strip() for cell in text.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "id":
            continue
        name_id, default, aliases = cells[:3]
        if not name_id or not default:
            continue
        alias_items = split_person_aliases(aliases)
        if default not in alias_items:
            alias_items.insert(0, default)
        rows.append({
            "id": name_id,
            "default": default,
            "aliases": alias_items,
        })
    return rows


def load_person_name_entries():
    global _PERSON_NAME_CACHE
    if _PERSON_NAME_CACHE is not None:
        return _PERSON_NAME_CACHE
    entries = []
    seen_ids = set()
    for directory in person_name_directories():
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            for entry in read_person_name_table(path):
                if entry["id"] in seen_ids:
                    continue
                seen_ids.add(entry["id"])
                entries.append(entry)
    if not entries:
        entries = [
            {"id": f"legacy_{index}", "default": name, "aliases": [name]}
            for index, name in enumerate(PERSON_NAME_FRAGMENTS, 1)
        ]
    _PERSON_NAME_CACHE = entries
    return entries


def person_name_alias_pairs():
    global _PERSON_NAME_ALIAS_PAIR_CACHE
    if _PERSON_NAME_ALIAS_PAIR_CACHE is not None:
        return _PERSON_NAME_ALIAS_PAIR_CACHE
    pairs = []
    for entry in load_person_name_entries():
        for alias in entry["aliases"]:
            key = canonical_answer_text(alias)
            if key:
                pairs.append((key, entry["id"]))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    _PERSON_NAME_ALIAS_PAIR_CACHE = pairs
    return pairs


def person_name_fragments():
    global _PERSON_NAME_FRAGMENTS_CACHE
    if _PERSON_NAME_FRAGMENTS_CACHE is not None:
        return _PERSON_NAME_FRAGMENTS_CACHE
    fragments = []
    seen = set()
    for entry in load_person_name_entries():
        for alias in entry["aliases"]:
            if alias and alias not in seen:
                seen.add(alias)
                fragments.append(alias)
    fragments.sort(key=len, reverse=True)
    _PERSON_NAME_FRAGMENTS_CACHE = fragments
    return fragments


def canonical_answer_text(value):
    raw = str(value or "").strip()
    cached = _CANONICAL_ANSWER_TEXT_CACHE.get(raw)
    if cached is not None:
        return cached
    text = unicodedata.normalize("NFKC", raw)
    normalized = "".join(ch for ch in text if ch not in ANSWER_OPTIONAL_HYPHENS and not ch.isspace())
    _CANONICAL_ANSWER_TEXT_CACHE[raw] = normalized
    return normalized


def person_name_answer_key(value):
    text = canonical_answer_text(value)
    if not text:
        return ""
    cached = _PERSON_NAME_ANSWER_KEY_CACHE.get(text)
    if cached is not None:
        return cached
    for alias_key, name_id in person_name_alias_pairs():
        text = text.replace(alias_key, f"\ufff0{name_id}\ufff1")
    _PERSON_NAME_ANSWER_KEY_CACHE[canonical_answer_text(value)] = text
    return text


def answers_equivalent(left, right):
    left_key = canonical_answer_text(left)
    right_key = canonical_answer_text(right)
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True
    return person_name_answer_key(left) == person_name_answer_key(right)


def answers_differ_only_by_person_alias(left, right):
    left_key = canonical_answer_text(left)
    right_key = canonical_answer_text(right)
    return bool(left_key and right_key) and left_key != right_key and person_name_answer_key(left) == person_name_answer_key(right)


def term_contains_person_name(chinese):
    text = canonical_answer_text(chinese)
    return any(alias_key and alias_key in text for alias_key, _name_id in person_name_alias_pairs())


def term_notice_tags(chinese):
    text = str(chinese or "")
    tags = []
    if term_contains_person_name(text):
        tags.append("人名")
    if term_has_greek_letter(text):
        tags.append("希腊字母")
    if re.search(r"[A-Za-z]", text):
        tags.append("英文字母")
    return tags


def term_has_greek_letter(chinese):
    return any(ch in GREEK_INITIALS for ch in str(chinese or ""))


def term_notice_text(chinese, prefix="本题含有"):
    tags = term_notice_tags(chinese)
    if not tags:
        return ""
    return f"{prefix}{'、'.join(tags)}"


def chinese_initials(text):
    result = []
    for ch in text:
        if ch.isascii():
            if ch.isalpha():
                result.append(ch.upper())
            elif ch.isdigit():
                result.append(ch)
            continue
        if ch in GREEK_INITIALS:
            result.append(GREEK_INITIALS[ch])
            continue
        if pinyin and Style:
            items = pinyin(ch, style=Style.FIRST_LETTER, strict=False, errors=lambda chars: [""] * len(chars))
            if items and items[0] and items[0][0]:
                result.append(items[0][0].upper())
                continue
        result.append(PINYIN_INITIAL_OVERRIDES.get(ch, ""))
    return "".join(result)


def normalize_term_initials(chinese, initials):
    answer = str(chinese or "").strip()
    raw = str(initials or "").strip().upper()
    if answer and len(raw) != len(answer):
        recalculated = chinese_initials(answer).strip().upper()
        if len(recalculated) == len(answer):
            return recalculated
    return raw
