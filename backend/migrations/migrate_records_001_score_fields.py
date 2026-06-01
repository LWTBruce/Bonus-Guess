import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORD_DIR = ROOT / "record"
SCORE_MODE_WEIGHTS = {
    "入门": 0.1,
    "简单": 0.2,
    "普通": 0.3,
    "困难": 0.4,
    "混合模式": 0.25,
}


def score_weight_for_difficulty(difficulty):
    return SCORE_MODE_WEIGHTS.get(difficulty or "", 0.0)


def is_failure_record(data):
    if data.get("finished_by") == "abandoned":
        return False
    if "finished_by" in data:
        return not data.get("success")
    return bool(data.get("all_answers")) and not data.get("success")


def main():
    if not RECORD_DIR.exists():
        return
    changed = 0
    for path in RECORD_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        updated = False
        elapsed = int(float(data.get("elapsed_seconds", 0) or 0))
        penalty = int(data.get("score_penalty", 0) or 0)
        score = int(data.get("score", 1000 - elapsed - penalty) or 0)
        if is_failure_record(data):
            score = 0
        hint_count = int(data.get("hint_count", len(data.get("hints") or [])) or 0)
        score_weight = score_weight_for_difficulty(data.get("difficulty"))
        defaults = {
            "used_library_hint": 0,
            "library_hint_text": "",
            "score_start": 1000,
            "score_time_cost": elapsed,
            "score_penalty": 0,
            "score": score,
            "score_weight": score_weight,
            "weighted_score": round(score * score_weight, 3),
            "scope": "",
            "source_label": "",
            "term_difficulty": 0,
            "failed_reason": "",
            "free_hint_quota": 0,
            "free_hint_count": 0,
            "paid_hint_count": hint_count,
        }
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
                updated = True
        if is_failure_record(data) and data.get("score") != 0:
            data["score"] = 0
            data["weighted_score"] = 0
            updated = True
        if "finished_by" not in data:
            data["finished_by"] = "answered" if data.get("success") or data.get("all_answers") else "abandoned"
            updated = True
        if updated:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            changed += 1
    print(f"updated_records={changed}")


if __name__ == "__main__":
    main()
