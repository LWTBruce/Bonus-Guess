import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET_DIRS = [
    ROOT / "clues" / "物理" / "入门模式：高中物理",
    ROOT / "clues" / "物理" / "简单模式：普通物理",
    ROOT / "clues" / "物理" / "普通模式：四大力学",
    ROOT / "clues" / "物理" / "困难模式：四大方向",
    ROOT / "clues" / "物理" / "噩梦模式：前沿物理",
]

TEMPLATE_PHRASES = [
    "题目中",
    "题干",
    "解题",
    "做题",
    "解题时",
    "做题时",
    "判断时",
    "分析时",
    "这个式子把概念同可测量量联系起来",
    "这个关系把概念同可测量量联系起来",
    "它的价值在于把",
    "若条件改变，应重新确认",
    "必要时还可以",
    "是热力学与统计力学中的概念",
    "用来描述对象",
    "符号中",
    "该式涉及",
    "宏观变量不是孤立数字",
    "这个补充条件",
]

TEMPLATE_PATTERNS = [
    re.compile(r"使用[^。；，、]{0,20}时要"),
    re.compile(r"是[^。；，、]{0,20}中描述[^。；，、]{0,20}的术语"),
]

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；])")


def han_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def has_bad_control(text):
    return any(ord(ch) < 32 and ch != "\n" for ch in text)


def iter_entries():
    for directory in TARGET_DIRS:
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for index, entry in enumerate(data.get("entries", []), start=1):
                yield path, index, entry


def sentences(text):
    result = []
    for part in SENTENCE_SPLIT_RE.split(text):
        cleaned = part.strip()
        if cleaned:
            result.append(cleaned.rstrip("。！？"))
    return result


def main():
    errors = []
    repeated_sentence_locations = {}
    for path, index, entry in iter_entries():
        name = entry.get("chinese_name", f"#{index}")
        text = entry.get("explanation_markdown", "")
        count = han_count(text)
        if count < 200 or count > 320:
            errors.append((path, name, f"中文字符数 {count} 不在 200-320"))
        if text.count("$") < 2:
            errors.append((path, name, "公式标记少于 2 个 $"))
        paragraphs = text.count("\n\n") + 1 if text else 0
        if paragraphs < 2 or paragraphs > 3:
            errors.append((path, name, f"段落数 {paragraphs} 不在 2-3"))
        if has_bad_control(text):
            errors.append((path, name, "含控制字符"))
        if re.search(r"`\s*\$.*?\$\s*`", text):
            errors.append((path, name, "公式被反引号包裹"))
        for formula in re.findall(r"\$(.*?)\$", text, flags=re.S):
            if re.search(r"[\n\r\t]", formula):
                errors.append((path, name, "公式内部含换行或制表符"))
        seen = {}
        for sentence in sentences(text):
            if han_count(sentence) >= 12:
                seen[sentence] = seen.get(sentence, 0) + 1
            if ("困难模式" in str(path) or "噩梦模式" in str(path)) and han_count(sentence) >= 20:
                repeated_sentence_locations.setdefault((path, sentence), []).append(name)
        for sentence, times in seen.items():
            if times > 1:
                errors.append((path, name, f"同条解释内重复句子：{sentence[:28]}"))
        for phrase in TEMPLATE_PHRASES:
            if phrase in text:
                errors.append((path, name, f"疑似流程/模板句：{phrase}"))
        if "困难模式" in str(path) or "噩梦模式" in str(path):
            for pattern in TEMPLATE_PATTERNS:
                if pattern.search(text):
                    errors.append((path, name, f"疑似流程/模板句：{pattern.pattern}"))

    for (path, sentence), names in repeated_sentence_locations.items():
        if len(names) > 3:
            shown_names = "、".join(names[:4])
            errors.append((path, shown_names, f"跨词条重复句子 {len(names)} 次：{sentence[:28]}"))

    if errors:
        for path, name, message in errors[:160]:
            rel = path.relative_to(ROOT).as_posix()
            print(f"{rel} | {name}: {message}")
        if len(errors) > 160:
            print(f"... and {len(errors) - 160} more")
        return 1
    print("physics explanation quality check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
