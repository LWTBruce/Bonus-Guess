import json
import threading
from pathlib import Path


class ClueLibrary:
    def __init__(self, path):
        self.path = path
        self.by_key = {}
        self.by_chinese = {}
        self.loaded = False
        self._load_lock = threading.RLock()

    @staticmethod
    def key_for(term):
        return f"{term.source}|{term.chinese}"

    def load(self):
        with self._load_lock:
            if self.loaded:
                return
            self.loaded = True
            if not self.path.exists():
                return
            for path in self._json_paths():
                self._load_json_file(path)

    def _json_paths(self):
        if self.path.is_dir():
            paths = sorted(path for path in self.path.rglob("*.json") if path.name != "term_clues.json")
            if paths:
                return paths
            legacy = self.path / "term_clues.json"
            return [legacy] if legacy.exists() else []
        return [self.path]

    def _load_json_file(self, path):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        entries = data.get("entries", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        default_source = str(data.get("source_file") or "").strip() if isinstance(data, dict) else ""
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            chinese = str(entry.get("chinese") or entry.get("chinese_name") or "").strip()
            source = str(entry.get("source") or entry.get("source_file") or default_source).strip()
            source_name = Path(source).name if source else ""
            complete = self._clean_lines(entry.get("complete") or entry.get("complete_clues"), chinese)
            fragments = self._clean_lines(entry.get("fragments") or entry.get("fragmented_clues") or entry.get("fragment_clues"), chinese)
            explanation = str(entry.get("explanation_markdown") or entry.get("explanation") or "").strip()
            source_links = self._clean_sources(entry.get("source_links") or entry.get("explanation_sources") or entry.get("sources"))
            if not chinese or ((len(complete) < 5 or len(fragments) < 5) and not explanation):
                continue
            normalized = {
                "chinese": chinese,
                "source": source,
                "source_type": "file",
                "complete": complete[:5],
                "fragments": fragments[:5],
            }
            if explanation:
                normalized["explanation_markdown"] = explanation
            if source_links:
                normalized["source_links"] = source_links
            if source:
                self.by_key[f"{source}|{chinese}"] = normalized
            if source_name:
                self.by_key[f"{source_name}|{chinese}"] = normalized
            self.by_chinese.setdefault(chinese, normalized)

    def get(self, term):
        self.load()
        entry = self.by_key.get(self.key_for(term)) or self.by_chinese.get(term.chinese)
        if entry:
            if len(entry.get("complete") or []) < 5 or len(entry.get("fragments") or []) < 5:
                fallback = self.fallback(term)
                if entry.get("explanation_markdown"):
                    fallback["explanation_markdown"] = entry["explanation_markdown"]
                if entry.get("source_links"):
                    fallback["source_links"] = entry["source_links"]
                return fallback
            return entry
        return self.fallback(term)

    @staticmethod
    def _clean_lines(lines, answer):
        result = []
        for line in lines or []:
            if isinstance(line, (list, tuple)):
                text = "  ".join(str(part).strip() for part in line if str(part).strip())
            else:
                text = str(line).strip()
            if not text:
                continue
            if answer and answer in text:
                text = text.replace(answer, "这个对象")
            result.append(text)
        return result

    @staticmethod
    def _clean_sources(sources):
        result = []
        for source in sources or []:
            if not isinstance(source, dict):
                continue
            label = str(source.get("label") or source.get("name") or "").strip()
            title = str(source.get("title") or "").strip()
            url = str(source.get("url") or source.get("href") or "").strip()
            if not label or not url:
                continue
            if not (url.startswith("https://") or url.startswith("http://")):
                continue
            cleaned = {"label": label, "url": url}
            if title:
                cleaned["title"] = title
            result.append(cleaned)
        return result

    @staticmethod
    def fallback(term):
        label = term.source_label if term.chinese not in term.source_label else "相关学科"
        length = len(term.chinese)
        complete = [
            f"常在{label}中出现。",
            "多用于刻画对象间关系。",
            "常由定义、公式或条件逐步收窄。",
            "最后通常能被英文名或标准符号进一步锁定。",
            f"这是一个{length}字中文专有名词。",
        ]
        fragments = [
            f"{label} 关系",
            "定义 公式 条件",
            "场景 收窄",
            "对象 性质 判断",
            f"{length}字 专有名词",
        ]
        return {
            "chinese": term.chinese,
            "source": term.source,
            "source_type": "fallback",
            "complete": complete,
            "fragments": fragments,
        }
