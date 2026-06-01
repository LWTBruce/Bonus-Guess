import csv
from pathlib import Path

from add_term_difficulty import estimate_difficulty

try:
    from pypinyin import Style, lazy_pinyin, pinyin
except Exception as exc:
    raise SystemExit("请先安装 pypinyin：python -m pip install --user pypinyin") from exc


ROOT = Path(__file__).resolve().parents[2]
WORDS_DIR = ROOT / "words"
HEADER = [
    "编号",
    "概念中文名",
    "难度",
    "中文首字母",
    "中文首字母串长度",
    "概念英文名",
    "英文字符串长度",
    "概念中文拼音",
    "拼音字符串长度",
]

ENGLISH_BY_CN = {
    "面电荷密度": "surface_charge_density",
    "面电流密度": "surface_current_density",
    "欧姆定律": "ohms_law",
    "极化": "polarization",
    "群速度": "group_velocity",
    "隧穿": "tunneling",
    "谐振子": "harmonic_oscillator",
    "粒子数算符": "number_operator",
    "CG系数": "clebsch_gordan_coefficient",
    "LRL矢量": "laplace_runge_lenz_vector",
    "简正模": "normal_mode",
    "混沌": "chaos",
    "泊松括号": "poisson_bracket",
    "稳定平衡": "stable_equilibrium",
    "功": "work",
    "热容": "heat_capacity",
    "热力学第零定律": "zeroth_law_of_thermodynamics",
    "内能": "internal_energy",
    "求和": "summation",
}

PINYIN_OVERRIDES = {
    "长度收缩": "changdushousuo",
    "固有长度": "guyouchangdu",
    "波长": "bochang",
    "康普顿波长": "kangpudunbochang",
    "德布罗意波长": "debuluoyibochang",
    "弧长": "huchang",
    "区间长度": "qujianchangdu",
    "珍斯长度": "zhensichangdu",
    "换位子长度": "huanweizichangdu",
    "行向量": "hangxiangliang",
    "行空间": "hangkongjian",
    "行秩": "hangzhi",
    "重积分": "chongjifen",
    "重根": "chonggen",
    "伽利略变换": "jialilvebianhuan",
    "勒让德变换": "lerangdebianhuan",
    "勒让德矩阵": "lerangdejuzhen",
    "勒让德方程": "lerangdefangcheng",
    "勒让德多项式": "lerangdeduoxiangshi",
}

INITIALS_OVERRIDES = {
    key: "".join(part[0].upper() for part in value.split())
    for key, value in {
        "长度收缩": "chang du shou suo",
        "固有长度": "gu you chang du",
        "波长": "bo chang",
        "康普顿波长": "kang pu dun bo chang",
        "德布罗意波长": "de bu luo yi bo chang",
        "弧长": "hu chang",
        "区间长度": "qu jian chang du",
        "珍斯长度": "zhen si chang du",
        "换位子长度": "huan wei zi chang du",
        "行向量": "hang xiang liang",
        "行空间": "hang kong jian",
        "行秩": "hang zhi",
        "重积分": "chong ji fen",
        "重根": "chong gen",
        "伽利略变换": "jia li lve bian huan",
        "勒让德变换": "le rang de bian huan",
        "勒让德矩阵": "le rang de ju zhen",
        "勒让德方程": "le rang de fang cheng",
        "勒让德多项式": "le rang de duo xiang shi",
    }.items()
}


def split_ascii_and_cjk(text):
    chunk = []
    cjk_chunk = []
    def flush_ascii():
        nonlocal chunk
        if chunk:
            value = "".join(chunk)
            chunk = []
            return value
        return None

    def flush_cjk():
        nonlocal cjk_chunk
        if cjk_chunk:
            value = "".join(cjk_chunk)
            cjk_chunk = []
            return value
        return None

    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch in "_"):
            value = flush_cjk()
            if value:
                yield value
            chunk.append(ch.lower())
        else:
            value = flush_ascii()
            if value:
                yield value
            if ch.strip():
                cjk_chunk.append(ch)
    value = flush_ascii()
    if value:
        yield value
    value = flush_cjk()
    if value:
        yield value


def make_pinyin(text):
    if text in PINYIN_OVERRIDES:
        return PINYIN_OVERRIDES[text]
    parts = []
    for token in split_ascii_and_cjk(text):
        if token.isascii():
            parts.append(token)
        else:
            parts.extend(lazy_pinyin(token, strict=False, errors=lambda chars: [""] * len(chars)))
    return "".join(parts).lower()


def make_initials(text):
    if text in INITIALS_OVERRIDES:
        return INITIALS_OVERRIDES[text]
    parts = []
    for token in split_ascii_and_cjk(text):
        if token.isascii():
            parts.append(token.upper())
        else:
            letters = pinyin(token, style=Style.FIRST_LETTER, strict=False, errors=lambda chars: [""] * len(chars))
            parts.extend(item[0].upper() for item in letters if item and item[0])
    return "".join(parts)


def extract_row(row):
    if not row or all(not cell.strip() for cell in row):
        return None
    difficulty = ""
    if len(row) >= 9:
        cn = row[1].strip()
        difficulty = row[2].strip()
        english = row[5].strip()
    elif len(row) >= 8:
        cn = row[1].strip()
        english = row[4].strip()
    elif len(row) >= 2 and row[0].strip().isdigit():
        cn = row[1].strip()
        english = ""
    elif len(row) == 1:
        cn = row[0].strip()
        english = ""
    else:
        cn = row[1].strip() if len(row) > 1 else row[0].strip()
        english = ""
    if not cn:
        return None
    if not english:
        english = ENGLISH_BY_CN.get(cn)
    if not english:
        raise ValueError(f"无法补全英文名：{cn}")
    return cn, difficulty, english


def repair_file(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    data = []
    seen_cn = set()
    seen_en = set()
    for raw in rows[1:]:
        extracted = extract_row(raw)
        if not extracted:
            continue
        cn, difficulty, english = extracted
        if cn in seen_cn or english in seen_en:
            continue
        seen_cn.add(cn)
        seen_en.add(english)
        initials = make_initials(cn)
        py = make_pinyin(cn)
        if difficulty not in {str(value) for value in range(1, 11)}:
            difficulty = str(estimate_difficulty(cn, english, path))
        if "入门模式" in path.name or any("入门模式" in part for part in path.parts):
            difficulty = str(min(3, max(1, int(difficulty))))
        data.append((cn, difficulty, initials, english, py))

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        for index, (cn, difficulty, initials, english, py) in enumerate(data, 1):
            writer.writerow([index, cn, difficulty, initials, len(initials), english, len(english), py, len(py)])
    return len(data)


def main():
    counts = []
    for path in sorted(WORDS_DIR.glob("**/*.csv")):
        count = repair_file(path)
        counts.append((path.relative_to(ROOT), count))
    for path, count in counts:
        print(f"{path}: {count}")


if __name__ == "__main__":
    main()
