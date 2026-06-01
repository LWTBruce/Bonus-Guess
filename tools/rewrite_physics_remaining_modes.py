import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHYSICS = "物理"
NORMAL_MODE = "普通模式：四大力学"
SIMPLE_MODE = "简单模式：普通物理"

NORMAL_DIR = ROOT / "clues" / PHYSICS / NORMAL_MODE
SIMPLE_DIR = ROOT / "clues" / PHYSICS / SIMPLE_MODE

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？])")


def dedupe(items):
    result = []
    for item in items:
        item = item.strip(" ，、；;:：。")
        if not item:
            continue
        item = item.replace("所指的", "、").replace("中的", "、").replace("里的", "、")
        for sub in re.split(r"[、，,]\s*", item):
            sub = sub.strip(" ，、；;:：。")
            if not sub:
                continue
            if sub in {"核心线索", "主要变量", "主要符号", "物理角色", "动力学框架"}:
                continue
            if sub not in result:
                result.append(sub)
    return result


def keywords_from(text, name):
    first = text.split("\n\n", 1)[0]
    candidates = []
    for pattern in [
        r"核心线索是([^，。；]+)",
        r"关注([^，。；]+)",
        r"围绕([^，。；]+)展开",
        r"先要固定([^，。；]+)",
        r"固定([^，。；]+)",
        r"用来描述([^。]+)",
    ]:
        match = re.search(pattern, first)
        if match:
            candidates.extend(dedupe([match.group(1)]))

    cleaned = []
    for item in candidates:
        if item == name or item in cleaned:
            continue
        if len(item) > 12 and "、" not in item:
            continue
        cleaned.append(item)
    return (cleaned or [name])[:4]


def formula_sentence(text):
    first = text.split("\n\n", 1)[0]
    for sentence in [s.strip() for s in SENTENCE_SPLIT_RE.split(first) if s.strip()]:
        if "$" not in sentence:
            continue
        sentence = sentence.replace("核心式可写作", "常用关系可写作")
        sentence = sentence.replace("一个紧凑写法是", "常用关系可写作")
        sentence = sentence.replace("标准表达可取", "常用关系可写作")
        sentence = sentence.replace("常用关系写作", "常用关系可写作")
        sentence = re.sub(
            r"其中([^；。]+?)标出该式涉及的主要符号或物理角色",
            r"其中\1是这里的主要符号",
            sentence,
        )
        sentence = re.sub(
            r"这里([^；。]+?)标出该式涉及的主要符号或物理角色",
            r"这里\1是这里的主要符号",
            sentence,
        )
        sentence = re.sub(
            r"符号中([^；。]+?)标出该式涉及的主要符号或物理角色",
            r"其中\1是这里的主要符号",
            sentence,
        )
        sentence = re.sub(
            r"式中([^；。]+?)标出该式涉及的主要变量或物理角色",
            r"式中\1是主要变量",
            sentence,
        )
        sentence = re.sub(
            r"其中([^；。]+?)标出该式涉及的主要变量或物理角色",
            r"其中\1是主要变量",
            sentence,
        )
        sentence = re.sub(
            r"这里([^；。]+?)标出该式涉及的主要变量或物理角色",
            r"这里\1是主要变量",
            sentence,
        )
        sentence = sentence.replace(
            "；H、ψ、A、E等字母按此量子模型中的哈密顿量、态、算符、能量或耦合参数理解",
            "；H、ψ、A、E等按哈密顿量、态、算符、能量或耦合参数理解",
        )
        sentence = sentence.replace(
            "$Born dP=|ψ(x)|^2 dx,\\quad ∫|ψ|^2 dx=1$",
            "$dP=|\\psi(x)|^2dx,\\quad \\int |\\psi|^2dx=1$",
        )
        return sentence
    return ""


def lead_sentence(text):
    parts = text.split("\n\n", 1)
    if len(parts) < 2:
        return ""
    second = re.split(r"对[^。]{1,30}而言，|使用[^。]{1,30}时", parts[1])[0]
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(second) if s.strip()]
    if not sentences:
        return ""
    lead = "".join(sentences[:2])
    return lead if lead.endswith("。") else f"{lead}。"


def han_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def trim_to_count(text, max_han=310):
    if han_count(text) <= max_han:
        return text
    paragraphs = text.split("\n\n")
    sentences = [s for s in SENTENCE_SPLIT_RE.split(paragraphs[-1]) if s.strip()]
    while len(sentences) > 1 and han_count("\n\n".join(paragraphs)) > max_han:
        sentences.pop()
        paragraphs[-1] = "".join(sentences).strip()
    return "\n\n".join(paragraphs)


def ensure_min(text, sentence):
    if han_count(text) >= 200:
        return text
    return f"{text}{sentence}"


def rewrite_quantum(text, name):
    keywords = keywords_from(text, name)
    keyword_text = "、".join(keywords)
    formula = formula_sentence(text)
    lead = lead_sentence(text) or "它把抽象态、可观测量和测量概率联系起来，矩阵、波函数和狄拉克符号只是不同表象下的写法。"

    if any(token in name for token in ["算符", "本征", "对易", "厄米", "幺正", "投影", "矩阵", "哈密顿"]):
        tail = f"使用{name}时要说明定义域、谱、对易关系和边界条件；这些细节会改变矩阵形式，却不改变由{keyword_text}限定的可观测量、能级或演化规则。"
    elif any(token in name for token in ["态", "波函数", "叠加", "纠缠", "相位", "希尔伯特"]):
        tail = f"使用{name}时要交代表象、归一化和相位约定；这些约定会改变函数外形，却不改变由{keyword_text}决定的概率分布、干涉和跃迁规则。"
    elif any(token in name for token in ["势", "振子", "隧穿", "散射", "近似"]):
        tail = f"使用{name}时要说明势能模型、边界条件和近似层级；模型一变，能级、相移或跃迁概率也会随之改变。"
    else:
        tail = f"使用{name}时要交代表象、归一化约定、守恒量和近似层级；这些选择会改变计算外形，但概率、能级或跃迁规则仍由{keyword_text}决定。"

    if name == "量子力学":
        first = "量子力学是描述原子、分子和微观粒子运动规律的理论，核心是用态、算符和概率幅取代经典轨道。"
    else:
        first = f"{name}是普通量子力学中的概念，用来描述{keyword_text}。"
    if formula:
        first += formula
    result = f"{first}\n\n{lead}{tail}"
    result = ensure_min(result, "在能谱、散射、测量或近似求解中，它把抽象公设落到可计算的矩阵元和概率上，这些量还能同谱线、截面或寿命比较。")
    return trim_to_count(result)


def rewrite_thermo(text, name):
    keywords = keywords_from(text, name)
    keyword_text = "、".join(keywords)
    formula = formula_sentence(text)
    lead = lead_sentence(text) or "它把宏观约束、微观状态和可测热量联系起来，适用范围取决于系统边界和平衡条件。"

    if any(token in name for token in ["系统", "系综", "开放", "封闭", "孤立"]):
        tail = f"使用{name}时要先说明能量、体积和粒子数能否与环境交换；边界条件不同，微正则、正则或巨正则描述也会不同。"
    elif any(token in name for token in ["势", "内能", "焓", "自由能", "化学势", "熵"]):
        tail = f"使用{name}时要说明自然变量和约束条件；勒让德变换会改变势函数形式，但平衡判据仍由{keyword_text}给出。"
    elif any(token in name for token in ["相", "临界", "转变", "涨落", "关联"]):
        tail = f"使用{name}时要说明控制参量、热力学极限和涨落尺度；有限体系中的圆滑变化，在极限下才可能表现为尖锐的相变或临界行为。"
    else:
        tail = f"使用{name}时要明确约束条件、自然变量和极限过程；这些选择会改变偏导数或概率权重的写法，但平衡含义仍由{keyword_text}限定。"

    first = f"{name}是热力学与统计力学中的概念，用来描述{keyword_text}。"
    if formula:
        first += formula
    result = f"{first}\n\n{lead}{tail}"
    result = ensure_min(result, "在实验和模型计算中，它把可控边界条件、微观统计和可测响应量连在一起。")
    return trim_to_count(result)


def cleanup_general(text):
    text = text.replace(
        "状态函数的变化可通过任意方便路径计算，这是热力学解题的强大技巧。",
        "状态函数的变化可沿任意方便路径计算，关键是初末态相同。",
    )
    text = text.replace(
        "它常把解题的难点从检验变换，转移为寻找合适的生成函数。",
        "它常把检验变换的问题，转化为寻找合适生成函数的问题。",
    )
    text = re.sub(
        r"对([^。]{1,30})而言，材料模型的核心不是公式复杂，而是说明哪些变量被认为足够描述历史和状态。",
        r"\1在连续介质模型中要先说明哪些变量足以描述材料的历史和状态。",
        text,
    )
    text = re.sub(
        r"对([^。]{1,30})而言，在完整电动力学中，它应与源、场、能量和边界条件一起理解。",
        r"\1要和源分布、场、能量流及边界条件一起理解。",
        text,
    )
    text = re.sub(
        r"对([^。]{1,30})而言，使用时要先分清它代表",
        r"使用\1时要先分清它代表",
        text,
    )
    text = re.sub(r"对([^。]{1,30})而言，还需说明", r"\1还要说明", text)
    text = re.sub(r"对([^。]{1,30})而言，", r"\1中，", text)
    text = ensure_min(text, "实际使用时还要说明适用条件、符号约定和测量方式，避免把形式相近的量混为一谈。")
    return text


def save_if_changed(path, data, before, changed):
    after = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if before == after:
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changed.append(path.relative_to(ROOT).as_posix())


def main():
    changed = []
    for filename in [
        "quantum_mechanics_terms.json",
        "thermo_stat_mech_terms.json",
        "continuum_mechanics_terms.json",
        "electrodynamics_terms.json",
        "theoretical_mechanics_terms.json",
    ]:
        path = NORMAL_DIR / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        before = json.dumps(data, ensure_ascii=False, sort_keys=True)
        for entry in data["entries"]:
            name = entry["chinese_name"]
            text = entry.get("explanation_markdown", "")
            if filename == "quantum_mechanics_terms.json":
                entry["explanation_markdown"] = rewrite_quantum(text, name)
            elif filename == "thermo_stat_mech_terms.json":
                entry["explanation_markdown"] = rewrite_thermo(text, name)
            else:
                entry["explanation_markdown"] = cleanup_general(text)
        save_if_changed(path, data, before, changed)

    path = SIMPLE_DIR / "thermal_terms.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    for entry in data["entries"]:
        if entry["chinese_name"] == "状态函数":
            entry["explanation_markdown"] = cleanup_general(entry["explanation_markdown"])
    save_if_changed(path, data, before, changed)

    for path in changed:
        print(path)


if __name__ == "__main__":
    main()
