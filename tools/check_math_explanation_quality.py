import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET_DIRS = [
    ROOT / "clues" / "数学" / "入门模式：高中数学",
    ROOT / "clues" / "数学" / "简单模式",
    ROOT / "clues" / "数学" / "普通模式",
    ROOT / "clues" / "数学" / "困难模式",
    ROOT / "clues" / "数学" / "噩梦模式",
]

TEMPLATE_PHRASES = [
    "这类概念常把",
    "使用时先确认",
    "使用时还要注意",
    "它常用来说明结构是否保留",
    "抽象条件由此变成可计算的判断",
    "相近概念往往只差一个量词",
    "这个术语常用来说明",
    "好处是",
    "常用关系可写作",
    "常用关系可写成",
    "这个式子把",
    "这个关系把",
    "题目中",
    "判断时",
    "做题时",
    "解题时",
    "做证明时",
    "分析时",
    "这里的重点是",
    "公式中的条件同时限定",
    "这个公式给出",
    "这个公式说明",
    "这个记号明确",
    "这个记号说明",
    "这种表述",
    "这种写法",
    "这种说法",
    "它同相近概念的差别",
    "它和相近概念的差别",
    "与相近概念相比",
    "同相近概念的差别",
    "相近概念的差别",
    "相近术语的差别",
    "相邻术语的差别",
    "相邻模型的差别",
    "这能把",
    "这能避免",
    "这样才能",
    "常见作用包括",
]

SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？])")


def han_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def has_bad_control(text):
    return any(ord(ch) < 32 and ch != "\n" for ch in text)


def sentences(text):
    result = []
    for part in SENTENCE_SPLIT_RE.split(text):
        cleaned = part.strip()
        if cleaned:
            result.append(cleaned)
    return result


def iter_entries():
    for directory in TARGET_DIRS:
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for index, entry in enumerate(data.get("entries", []), start=1):
                yield path, index, entry


def main():
    errors = []
    global_sentences = {}
    rows = list(iter_entries())

    for path, index, entry in rows:
        name = entry.get("chinese_name", f"#{index}")
        text = entry.get("explanation_markdown", "")
        count = han_count(text)
        if count < 200 or count > 320:
            errors.append((path, name, f"中文字符数 {count} 不在 200-320"))
        if text.count("$") < 2:
            errors.append((path, name, "公式标记少于 2 个 $"))
        if text.count("\n\n") + 1 > 3:
            errors.append((path, name, "段落超过 3 段"))
        if has_bad_control(text):
            errors.append((path, name, "含控制字符"))
        if text.startswith(f"{name}是{name}"):
            errors.append((path, name, "开头重复词条名"))
        for formula in re.findall(r"\$(.*?)\$", text, flags=re.S):
            if re.search(r"[\n\r\t]", formula):
                errors.append((path, name, "公式内部含换行或制表符"))
        seen = {}
        for sentence in sentences(text):
            key = sentence.rstrip("。！？")
            if han_count(key) >= 12:
                seen[key] = seen.get(key, 0) + 1
                global_sentences.setdefault(key, set()).add(path)
        for sentence, times in seen.items():
            if times > 1:
                errors.append((path, name, f"同条解释内重复句子：{sentence[:28]}"))
        for phrase in TEMPLATE_PHRASES:
            if phrase in text:
                errors.append((path, name, f"疑似模板句：{phrase}"))

    for sentence, paths in global_sentences.items():
        if len(paths) >= 8:
            for path, _, entry in rows:
                if path in paths and sentence in entry.get("explanation_markdown", ""):
                    name = entry.get("chinese_name", "#")
                    errors.append((path, name, f"跨文件高频套句：{sentence[:28]}"))
                    break

    if errors:
        for path, name, message in errors[:160]:
            rel = path.relative_to(ROOT).as_posix()
            print(f"{rel} | {name}: {message}")
        if len(errors) > 160:
            print(f"... and {len(errors) - 160} more")
        return 1
    print("math explanation quality check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
