import csv
import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = ("数学", "物理")


def relative_posix(path):
    return path.relative_to(ROOT).as_posix()


def read_term_english_names():
    names = {}
    fallback_by_chinese = {}
    for subject in SUBJECTS:
        for path in sorted((ROOT / "words" / subject).rglob("*.csv")):
            source = relative_posix(path)
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    chinese = str(row.get("概念中文名") or "").strip()
                    english = str(row.get("概念英文名") or "").strip()
                    if not chinese:
                        continue
                    names[(source, chinese)] = english
                    fallback_by_chinese.setdefault(chinese, english)
    return names, fallback_by_chinese


def wiki_search_url(term):
    return f"https://zh.wikipedia.org/w/index.php?search={quote(term, safe='')}"


def wikipedia_search_url(term):
    query = str(term or "").replace("_", " ").strip()
    return f"https://en.wikipedia.org/w/index.php?search={quote(query, safe='')}"


def baidu_baike_search_url(term):
    return f"https://www.baidu.com/s?wd={quote(f'{term} 百度百科', safe='')}"


def source_entries(chinese, english):
    sources = [
        {
            "label": "百度百科",
            "title": chinese,
            "url": baidu_baike_search_url(chinese),
        },
        {
            "label": "维基百科",
            "title": chinese,
            "url": wiki_search_url(chinese),
        },
    ]
    english_query = str(english or "").strip()
    if english_query:
        sources.append({
            "label": "Wikipedia",
            "title": english_query.replace("_", " "),
            "url": wikipedia_search_url(english_query),
        })
    return sources


def attach_sources_to_entry(entry, default_source, english_by_source, english_by_chinese):
    chinese = str(entry.get("chinese_name") or entry.get("chinese") or "").strip()
    if not chinese:
        return False
    source = str(entry.get("source_file") or entry.get("source") or default_source or "").strip()
    english = english_by_source.get((source, chinese)) or english_by_chinese.get(chinese, "")
    sources = source_entries(chinese, english)

    updated = {}
    inserted = False
    for key, value in entry.items():
        if key in {"source_links", "explanation_sources"}:
            continue
        updated[key] = value
        if key == "explanation_markdown":
            updated["source_links"] = sources
            inserted = True
    if not inserted:
        updated["source_links"] = sources

    changed = entry.get("source_links") != sources or list(entry.keys()) != list(updated.keys())
    if changed:
        entry.clear()
        entry.update(updated)
    return changed


def main():
    english_by_source, english_by_chinese = read_term_english_names()
    changed_files = []
    entry_count = 0
    for subject in SUBJECTS:
        for path in sorted((ROOT / "clues" / subject).rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data.get("entries", []) if isinstance(data, dict) else []
            default_source = str(data.get("source_file") or "").strip() if isinstance(data, dict) else ""
            changed = False
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if attach_sources_to_entry(entry, default_source, english_by_source, english_by_chinese):
                    changed = True
                entry_count += 1
            if changed:
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                changed_files.append(relative_posix(path))
    print(f"updated_files={len(changed_files)}")
    print(f"entries_seen={entry_count}")
    for path in changed_files:
        print(path)


if __name__ == "__main__":
    main()
