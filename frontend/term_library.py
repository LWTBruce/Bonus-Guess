import csv

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
    DIFFICULTIES = ["入门", "简单", "普通", "困难", "混合模式"]
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
        "advanced_calculus_terms.csv": "高等微积分",
        "mathematical_analysis_terms.csv": "数学分析",
        "linear_algebra_terms.csv": "线性代数",
        "complex_analysis_terms.csv": "复变函数",
        "mathematical_physics_equations_terms.csv": "数学物理方程",
        "partial_differential_equations_terms.csv": "偏微分方程",
        "ordinary_differential_equations_terms.csv": "常微分方程",
        "numerical_analysis_terms.csv": "数值分析",
        "probability_theory_terms.csv": "概率论",
        "mathematical_statistics_terms.csv": "数理统计",
        "field_theory_terms.csv": "场论",
        "group_theory_terms.csv": "群论",
        "topology_terms.csv": "拓扑学",
        "real_analysis_terms.csv": "实分析",
        "complex_analysis_advanced_terms.csv": "复分析",
        "functional_analysis_terms.csv": "泛函分析",
        "statistical_inference_terms.csv": "统计推断",
        "measure_and_integration_terms.csv": "测度与积分",
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
        self.mode_initials = {}

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
        modes = [mode] if mode else list(self.MODE_DIRS)
        for mode_name in modes:
            if mode_name not in self.mode_initials:
                self.mode_initials[mode_name] = {}
                base = self.root / self.MODE_DIRS[mode_name]
                if not base.exists():
                    continue
                seen = set()
                for file in base.rglob("*.csv"):
                    for term in self._read_csv(file, seen):
                        self.mode_initials[mode_name].setdefault(term.chinese, term.initials)
            found = self.mode_initials[mode_name].get(chinese)
            if found:
                return found
        return None

    def _read_csv(self, path, seen):
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
                key = (chinese, initials)
                if key in seen:
                    continue
                seen.add(key)
                if difficulty not in {str(value) for value in range(1, 11)}:
                    difficulty = "5"
                rows.append(Term(path.name, source_label, row[0], chinese, int(difficulty), initials, english, pinyin))
        return rows

    def file_label(self, path):
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


def chinese_initials(text):
    if pinyin and Style:
        items = pinyin(text, style=Style.FIRST_LETTER, strict=False, errors=lambda chars: [""] * len(chars))
        return "".join(item[0].upper() for item in items if item and item[0])

    result = []
    for ch in text:
        if ch.isascii():
            if ch.isalpha():
                result.append(ch.upper())
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
