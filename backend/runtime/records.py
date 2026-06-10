import json
import random
from collections import Counter
from datetime import datetime

from .game_config import (
    ACHIEVEMENTS,
    ACHIEVEMENTS_FILE,
    DAILY_TERMS_FILE,
    FREE_HINT_DECAY,
    FREE_HINT_ZERO_PROB,
    MASK_PROBABILITIES,
    RECORD_DIR,
    RANK_PROGRESS_FILE,
    SCORE_MODE_WEIGHTS,
    TERM_DIFFICULTY_WEIGHTS,
)


UNKNOWN_LABEL = "未知"
DEFAULT_PLAY_MODE = "自由"
RANDOM_LABEL = "随机"
RATING_CAP = 20.5
EQUAL_DIFFICULTY_MODE_RANDOM = {"混合模式", "真·随机"}
DIFFICULTY_MODE_BUCKETS = [
    ("入门", range(1, 3)),
    ("简单", range(3, 5)),
    ("普通", range(5, 8)),
    ("困难", range(8, 11)),
    ("噩梦", range(11, 13)),
]
DIFFICULTY_MODE_BY_VALUE = {
    difficulty: name
    for name, values in DIFFICULTY_MODE_BUCKETS
    for difficulty in values
}
_RECORD_ENTRIES_CACHE = {
    "roots": {},
}
_RECORD_SUMMARY_CACHE = {}
_ACHIEVEMENTS_CACHE = {}
_DAILY_TERMS_CACHE = {
    "date": None,
    "mtime_ns": None,
    "state": None,
}


def _record_root_key(root):
    try:
        return str(root.resolve())
    except OSError:
        return str(root.absolute())


def _record_root_cache(root):
    key = _record_root_key(root)
    return key, _RECORD_ENTRIES_CACHE.setdefault("roots", {}).get(key)


def _copy_record_entries(entries):
    return [dict(entry) for entry in entries]


def _clear_summary_cache_for_root(root_key=None):
    if root_key is None:
        _RECORD_SUMMARY_CACHE.clear()
        return
    for key in list(_RECORD_SUMMARY_CACHE):
        if key[0] == root_key:
            _RECORD_SUMMARY_CACHE.pop(key, None)


def clear_record_caches(record_dir=None):
    if record_dir is None:
        _RECORD_ENTRIES_CACHE["roots"] = {}
        _RECORD_SUMMARY_CACHE.clear()
        _ACHIEVEMENTS_CACHE.clear()
        return
    root_key = _record_root_key(record_dir)
    _RECORD_ENTRIES_CACHE.setdefault("roots", {}).pop(root_key, None)
    _clear_summary_cache_for_root(root_key)


def load_record_entries(record_dir=None):
    root = record_dir or RECORD_DIR
    if not root.exists():
        return []
    cache_root, cached = _record_root_cache(root)
    if cached and cached.get("entries") is not None:
        return _copy_record_entries(cached["entries"])
    entries = []
    for path in root.rglob("*.json"):
        if path.name in {ACHIEVEMENTS_FILE.name, RANK_PROGRESS_FILE.name}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        data["_path"] = path
        entries.append(data)
    entries.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    _RECORD_ENTRIES_CACHE.setdefault("roots", {})[cache_root] = {
        "entries": _copy_record_entries(entries),
        "revision": (cached or {}).get("revision", 0) if isinstance(cached, dict) else 0,
    }
    _clear_summary_cache_for_root(cache_root)
    return _copy_record_entries(entries)


def add_record_entry_to_cache(record, path, record_dir=None):
    root = record_dir or RECORD_DIR
    cache_root, cached = _record_root_cache(root)
    if not cached or cached.get("entries") is None:
        return
    cached = dict(record)
    cached["_path"] = path
    entries = [entry for entry in _RECORD_ENTRIES_CACHE["roots"][cache_root]["entries"] if entry.get("_path") != path]
    entries.insert(0, cached)
    entries.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    _RECORD_ENTRIES_CACHE["roots"][cache_root]["entries"] = entries
    _RECORD_ENTRIES_CACHE["roots"][cache_root]["revision"] = int(_RECORD_ENTRIES_CACHE["roots"][cache_root].get("revision") or 0) + 1
    _clear_summary_cache_for_root(cache_root)


def record_entries_signature(record_dir=None):
    root = record_dir or RECORD_DIR
    root_key, cached = _record_root_cache(root)
    if not cached or cached.get("entries") is None:
        load_record_entries(root)
        root_key, cached = _record_root_cache(root)
    entries = cached.get("entries") if cached else []
    return (root_key, int((cached or {}).get("revision") or 0), len(entries or []))


def record_storage_dir(moment):
    return RECORD_DIR / moment.strftime("%Y-%m") / moment.strftime("%Y-%m-%d")


def record_datetime(record):
    raw = record.get("created_at") or ""
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return datetime.min


def is_crossword_rank_rating_record(record):
    return bool(record.get("crossword_mode")) and record.get("rank_kind") == "crossword"


def is_counted_record(record):
    crossword_rank_rating = is_crossword_rank_rating_record(record)
    if record.get("custom_mode"):
        return False
    if record.get("rank_mode") and not crossword_rank_rating:
        return False
    if record.get("exclude_from_stats") and not crossword_rank_rating:
        return False
    if record.get("finished_by") == "abandoned":
        return False
    if "finished_by" in record:
        return record.get("finished_by") in {"answered", "hint_failure", "cheated", "revealed"}
    return bool(record.get("success")) or bool(record.get("all_answers"))


def is_abandoned_record(record):
    crossword_rank_rating = is_crossword_rank_rating_record(record)
    if record.get("custom_mode"):
        return False
    if record.get("rank_mode") and not crossword_rank_rating:
        return False
    if record.get("exclude_from_stats") and not crossword_rank_rating:
        return False
    if record.get("finished_by") == "abandoned":
        return True
    if "finished_by" in record:
        return False
    return not record.get("success") and not record.get("all_answers")


def _clean_record_label(value, default=UNKNOWN_LABEL):
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def normalize_play_mode_label(value, default=DEFAULT_PLAY_MODE):
    text = _clean_record_label(value, default)
    if text in {"段位", "自由段位"}:
        return "限时段位"
    return text


def _looks_random_label(value):
    text = _clean_record_label(value, "")
    normalized = text.replace(" ", "").replace("・", "·").lower()
    return normalized in {"随机", "真·随机", "真随机", "random", "true_random", "truerandom"}


def is_random_record(record):
    return (
        _looks_random_label(record.get("subject"))
        or _looks_random_label(record.get("mode"))
        or _looks_random_label(record.get("play_mode"))
    )


def record_mode(record):
    if record.get("rank_mode"):
        return _clean_record_label(record.get("rank_subject") or record.get("subject") or record.get("mode"))
    if record.get("custom_mode"):
        return _clean_record_label(record.get("subject") or record.get("mode") or "自定义")
    raw_subject = _clean_record_label(record.get("subject"), "")
    raw_mode = _clean_record_label(record.get("mode"), "")
    raw_play_mode = _clean_record_label(record.get("play_mode"), "")
    if any(_looks_random_label(value) for value in (raw_subject, raw_mode, raw_play_mode)):
        return RANDOM_LABEL
    return raw_subject or raw_mode or UNKNOWN_LABEL


def record_play_mode(record):
    if record.get("rank_mode"):
        rank_id = record.get("rank_id") or ""
        if record.get("rank_kind") == "crossword" or record.get("play_mode") == "字谜段位":
            label = "字谜段位"
        elif record.get("rank_kind") == "timed":
            label = "旧限时段位"
        elif record.get("rank_kind") == "clue" or record.get("play_mode") == "线索段位":
            label = "线索段位"
        else:
            label = "限时段位"
        return f"{label} Class {int(rank_id):02d}" if str(rank_id).isdigit() else label
    if record.get("crossword_mode"):
        return _clean_record_label(record.get("play_mode"), "字谜")
    if record.get("custom_mode"):
        kind = _clean_record_label(record.get("custom_play_kind"), "")
        config = record.get("custom_config") if isinstance(record.get("custom_config"), dict) else {}
        parts = [kind] if kind else []
        if config.get("timed_enabled") or kind == "限时首字母":
            parts.append("限时")
        if config.get("challenge_enabled"):
            try:
                target = int(config.get("challenge_target") or 5)
            except (TypeError, ValueError):
                target = 5
            parts.append(f"{target}题挑战")
        return f"自定义-{' / '.join(parts)}" if parts else "自定义"
    if _looks_random_label(record.get("play_mode")):
        return RANDOM_LABEL
    if _looks_random_label(record.get("mode")):
        play = normalize_play_mode_label(record.get("play_mode"), DEFAULT_PLAY_MODE)
        return f"{RANDOM_LABEL}-{play}" if play and play != RANDOM_LABEL else RANDOM_LABEL
    return normalize_play_mode_label(record.get("play_mode"), DEFAULT_PLAY_MODE)


def record_difficulty(record):
    return _clean_record_label(record.get("difficulty"))


def record_hint_count(record):
    if "hint_count" in record:
        try:
            return int(record.get("hint_count") or 0)
        except (TypeError, ValueError):
            return 0
    return len(record.get("hints") or [])


def record_paid_hint_count(record):
    if "paid_hint_count" in record:
        try:
            return int(record.get("paid_hint_count") or 0)
        except (TypeError, ValueError):
            return 0
    return record_hint_count(record)


def record_free_hint_count(record):
    if "free_hint_count" in record:
        try:
            return int(record.get("free_hint_count") or 0)
        except (TypeError, ValueError):
            return 0
    return 0


def record_library_hint_count(record):
    try:
        return max(0, int(record.get("used_library_hint") or 0))
    except (TypeError, ValueError):
        return 0


def record_score(record):
    if is_counted_record(record) and not record.get("success") and not record.get("cheat_detected"):
        return 0
    if "score" in record:
        try:
            return int(record.get("score") or 0)
        except (TypeError, ValueError):
            pass
    elapsed = int(float(record.get("elapsed_seconds") or 0))
    penalty = int(record.get("score_penalty") or 0)
    return 1000 - elapsed - penalty


def record_term_difficulty(record):
    try:
        value = int(float(record.get("base_term_difficulty") or record.get("term_difficulty") or 0))
    except (TypeError, ValueError):
        return 0
    return value if 1 <= value <= 12 else 0


def record_effective_difficulty(record):
    try:
        value = float(record.get("effective_difficulty") or record.get("term_difficulty") or 0)
    except (TypeError, ValueError):
        return float(record_term_difficulty(record))
    return value if value >= 1 else float(record_term_difficulty(record))


def score_weight_for_difficulty(difficulty):
    return SCORE_MODE_WEIGHTS.get(difficulty or "", 0.0)


def weighted_record_score(record):
    return record_score(record) * score_weight_for_difficulty(record.get("difficulty"))


def record_weighted_score(record):
    if not record.get("exclude_from_stats"):
        return weighted_record_score(record)
    if "weighted_score" in record:
        try:
            return float(record.get("weighted_score") or 0)
        except (TypeError, ValueError):
            pass
    if "score_weight" in record:
        try:
            return record_score(record) * float(record.get("score_weight") or 0)
        except (TypeError, ValueError):
            pass
    return weighted_record_score(record)


def clamp(value, low, high):
    return max(low, min(high, value))


def format_rating(value):
    return f"{value:.3f}"


def record_chart_constant(record):
    difficulty_bonus = {
        "入门": -0.7,
        "简单": 0.0,
        "普通": 1.0,
        "困难": 3.3,
        "噩梦": 4.8,
        "混合模式": 1.0,
        "真·随机": 1.0,
    }.get(record.get("difficulty") or "", 0.0)
    play_bonus = {
        "自由": 0.0,
        "限时": 0.25,
        "线索": 0.20,
        "字谜": 0.35,
        "随机字谜": 0.45,
        RANDOM_LABEL: 0.40,
    }.get(record_play_mode(record), 0.0)
    if is_random_record(record):
        play_bonus = 0.0
    term_difficulty = record_effective_difficulty(record) or 1
    return clamp(0.5 + 1.62 * term_difficulty + difficulty_bonus + play_bonus, 0.5, RATING_CAP)


def record_rating_key(record):
    if record.get("crossword_mode"):
        return record.get("mode") or "未知", record.get("id") or record_datetime(record).isoformat()
    answer = (
        record.get("selected_answer")
        or record.get("answer")
        or record.get("question_initials")
        or record.get("id")
        or record_datetime(record).isoformat()
    )
    return record.get("mode") or "未知", answer


def record_expected_time(record):
    if record.get("crossword_mode"):
        try:
            word_count = int(record.get("crossword_word_count") or 0)
        except (TypeError, ValueError):
            word_count = 0
        try:
            cell_count = int(record.get("crossword_cell_count") or 0)
        except (TypeError, ValueError):
            cell_count = 0
        term_difficulty = record_effective_difficulty(record) or 5
        return 20.0 + 8.0 * max(word_count, 1) + 1.2 * max(cell_count, word_count) + 2.0 * term_difficulty
    answer_length = max(len(record.get("selected_answer") or ""), 1)
    term_difficulty = record_effective_difficulty(record) or 5
    return 8.0 + 2.4 * answer_length + 1.6 * term_difficulty


def record_wrong_attempt_count(record):
    attempts = record.get("all_answers") or []
    return sum(1 for attempt in attempts if attempt.get("result") != "success")


def record_performance_quality(record):
    if not record.get("success"):
        return 0.0
    try:
        score_start = float(record.get("score_start") or 1000)
    except (TypeError, ValueError):
        score_start = 1000
    score_quality = clamp(record_score(record) / max(score_start, 1.0), 0.0, 1.0)
    elapsed = float(record.get("elapsed_seconds") or 0)
    expected = record_expected_time(record)
    speed_ratio = (expected - elapsed) / max(expected, 1.0)
    if speed_ratio >= 0:
        speed_adjust = min(0.035, speed_ratio * 0.04)
    else:
        speed_adjust = max(-0.06, speed_ratio * 0.04)
    hint_penalty = (
        0.025 * record_free_hint_count(record)
        + 0.015 * record_paid_hint_count(record)
        + 0.020 * record_library_hint_count(record)
    )
    wrong_penalty = min(0.12, 0.020 * record_wrong_attempt_count(record))
    return clamp(score_quality + speed_adjust - hint_penalty - wrong_penalty, 0.0, 1.0)


def record_single_rating(record):
    quality = record_performance_quality(record)
    if quality < 0.70:
        return 0.0
    rating = record_chart_constant(record) * ((quality - 0.55) / 0.45) ** 2
    return round(clamp(rating, 0.0, RATING_CAP), 3)


def achievement_rating_bonus(achievements_data=None):
    if achievements_data is None:
        achievements_data = read_achievements()
    completed = achievements_data.get("completed") if isinstance(achievements_data, dict) else {}
    if isinstance(completed, dict):
        completed_count = sum(1 for achievement_id, _title, _description in ACHIEVEMENTS if achievement_id in completed)
    else:
        completed_count = 0
    total = max(len(ACHIEVEMENTS), 1)
    ratio = completed_count / total
    broad_bonus = 1.35 * (ratio ** 0.62)
    early_bonus = 0.35 * min(1.0, completed_count / 18)
    long_bonus = 0.45 * min(1.0, completed_count / 45)
    return {
        "completed": completed_count,
        "total": total,
        "bonus": round(clamp(broad_bonus + early_bonus + long_bonus, 0.0, 2.15), 3),
    }


def summarize_rating(records, achievements_data=None, include_achievements=True):
    rated_records = [
        (record_datetime(record), record_single_rating(record), record_rating_key(record))
        for record in records
    ]
    achievement_part = achievement_rating_bonus(achievements_data) if include_achievements else {
        "completed": 0,
        "total": len(ACHIEVEMENTS),
        "bonus": 0.0,
    }
    ratings = [rating for _created_at, rating, _key in rated_records]
    if not ratings:
        return {
            "rating": round(achievement_part["bonus"], 3),
            "play_rating": 0.0,
            "best_average": 0.0,
            "recent_average": 0.0,
            "best_values": [],
            "recent_values": [],
            "achievement_bonus": achievement_part["bonus"],
            "achievement_count": achievement_part["completed"],
            "achievement_total": achievement_part["total"],
        }
    best_by_key = {}
    for _created_at, rating, key in rated_records:
        best_by_key[key] = max(best_by_key.get(key, 0.0), rating)
    unique_best_ratings = list(best_by_key.values())
    best_denominator = min(20, max(5, len(unique_best_ratings)))
    best_values = sorted(unique_best_ratings, reverse=True)[:best_denominator]
    best_average = sum(best_values) / best_denominator

    recent_denominator = min(10, max(3, len(ratings)))
    recent_values = [rating for _created_at, rating, _key in sorted(rated_records, key=lambda item: item[0])][-recent_denominator:]
    recent_average = sum(recent_values) / recent_denominator
    play_rating = clamp(0.85 * best_average + 0.15 * recent_average, 0.0, RATING_CAP)
    rating = clamp(play_rating + achievement_part["bonus"], 0.0, RATING_CAP)
    return {
        "rating": round(rating, 3),
        "play_rating": round(play_rating, 3),
        "best_average": round(best_average, 3),
        "recent_average": round(recent_average, 3),
        "best_values": [round(value, 3) for value in best_values[:5]],
        "recent_values": [round(value, 3) for value in recent_values],
        "achievement_bonus": achievement_part["bonus"],
        "achievement_count": achievement_part["completed"],
        "achievement_total": achievement_part["total"],
    }


def _empty_record_group_summary(label):
    return {
        "label": label,
        "records": [],
        "total_count": 0,
        "success_count": 0,
        "wrong_count": 0,
        "raw_total_score": 0,
        "total_score": 0,
        "weighted_total_score": 0,
        "rating": 0.0,
        "play_rating": 0.0,
        "achievement_bonus": 0.0,
        "achievement_count": 0,
        "achievement_total": len(ACHIEVEMENTS),
        "rating_best_average": 0.0,
        "rating_recent_average": 0.0,
        "rating_best_values": [],
        "rating_recent_values": [],
        "char_hints": 0,
        "paid_char_hints": 0,
        "free_char_hints": 0,
        "library_hints": 0,
        "hint_count": 0,
        "abandoned_count": 0,
        "exit_count": 0,
    }


def summarize_record_group(records, label=None, abandoned_records=None):
    counted = [record for record in records if is_counted_record(record)]
    exits = list(abandoned_records or [])
    summary = _empty_record_group_summary(label)
    rating_summary = summarize_rating(counted, include_achievements=False)
    raw_total_score = sum(record_score(record) for record in counted)
    weighted_total_score = sum(record_weighted_score(record) for record in counted)
    char_hints = sum(record_hint_count(record) for record in counted)
    library_hints = sum(record_library_hint_count(record) for record in counted)

    summary.update({
        "records": counted,
        "total_count": len(counted),
        "success_count": sum(1 for record in counted if record.get("success")),
        "raw_total_score": raw_total_score,
        "total_score": weighted_total_score,
        "weighted_total_score": weighted_total_score,
        "rating": rating_summary["rating"],
        "play_rating": rating_summary["play_rating"],
        "achievement_bonus": rating_summary["achievement_bonus"],
        "achievement_count": rating_summary["achievement_count"],
        "achievement_total": rating_summary["achievement_total"],
        "rating_best_average": rating_summary["best_average"],
        "rating_recent_average": rating_summary["recent_average"],
        "rating_best_values": rating_summary["best_values"],
        "rating_recent_values": rating_summary["recent_values"],
        "char_hints": char_hints,
        "paid_char_hints": sum(record_paid_hint_count(record) for record in counted),
        "free_char_hints": sum(record_free_hint_count(record) for record in counted),
        "library_hints": library_hints,
        "hint_count": char_hints + library_hints,
        "abandoned_count": len(exits),
        "exit_count": len(exits),
    })
    summary["wrong_count"] = summary["total_count"] - summary["success_count"]
    return summary


def _summarize_by_dimension(records, key_func):
    grouped_records = {}
    grouped_exits = {}
    for record in records:
        key = key_func(record)
        if is_abandoned_record(record):
            grouped_exits.setdefault(key, []).append(record)
        elif is_counted_record(record):
            grouped_records.setdefault(key, []).append(record)

    keys = sorted(set(grouped_records) | set(grouped_exits), key=str)
    return {
        key: summarize_record_group(grouped_records.get(key, []), key, grouped_exits.get(key, []))
        for key in keys
    }


def summarize_record_dimensions(records):
    subject_summary = _summarize_by_dimension(records, record_mode)
    return {
        "subject": subject_summary,
        "mode": subject_summary,
        "play_mode": _summarize_by_dimension(records, record_play_mode),
        "difficulty": _summarize_by_dimension(records, record_difficulty),
    }


def format_score(value):
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}"
    return str(int(value))


TERM_LENGTH_WEIGHTS = {
    1: 0.22,
    2: 0.55,
    3: 1.15,
    4: 1.25,
}


def term_length_weight(term):
    cached = getattr(term, "_length_weight", None)
    if cached is not None:
        return cached
    length = len(getattr(term, "chinese", "") or "")
    if length <= 0:
        weight = 1.0
    elif length >= 5:
        weight = 1.35
    else:
        weight = TERM_LENGTH_WEIGHTS.get(length, 1.0)
    try:
        setattr(term, "_length_weight", weight)
    except Exception:
        pass
    return weight


def choose_term_by_length(terms):
    weights = [term_length_weight(term) for term in terms]
    return random.choices(terms, weights=weights, k=1)[0]


def difficulty_mode_for_value(value):
    try:
        difficulty = int(value)
    except (TypeError, ValueError):
        difficulty = 5
    return DIFFICULTY_MODE_BY_VALUE.get(max(1, min(12, difficulty)), "普通")


def group_terms_by_difficulty_mode(terms):
    buckets = {name: [] for name, _values in DIFFICULTY_MODE_BUCKETS}
    for term in terms:
        buckets[difficulty_mode_for_value(getattr(term, "difficulty", 5))].append(term)
    return {name: bucket for name, bucket in buckets.items() if bucket}


def choose_term_by_equal_difficulty_mode(terms):
    buckets = group_terms_by_difficulty_mode(terms)
    if not buckets:
        return choose_term_by_length(terms)
    available_modes = [name for name, _values in DIFFICULTY_MODE_BUCKETS if name in buckets]
    chosen_mode = random.choice(available_modes)
    bucket = buckets[chosen_mode]
    weights = [term_length_weight(term) for term in bucket]
    return random.choices(bucket, weights=weights, k=1)[0]


def balanced_terms_by_equal_difficulty_mode(terms, per_mode=None, rng=None):
    source_terms = list(terms)
    buckets = group_terms_by_difficulty_mode(source_terms)
    if len(buckets) <= 1:
        return source_terms
    rng = rng or random
    available_modes = [name for name, _values in DIFFICULTY_MODE_BUCKETS if name in buckets]
    if per_mode is None:
        per_mode = max(1, len(source_terms) // max(len(available_modes), 1))
    balanced = []
    for mode_name in available_modes:
        bucket = list(buckets[mode_name])
        rng.shuffle(bucket)
        balanced.extend(bucket[: max(1, int(per_mode))])
    rng.shuffle(balanced)
    return balanced or source_terms


def choose_term_by_difficulty(terms, gameplay_difficulty):
    if gameplay_difficulty in EQUAL_DIFFICULTY_MODE_RANDOM:
        return choose_term_by_equal_difficulty_mode(terms)
    weights_by_difficulty = TERM_DIFFICULTY_WEIGHTS.get(gameplay_difficulty, TERM_DIFFICULTY_WEIGHTS["混合模式"])
    weights = [
        max(0.001, weights_by_difficulty.get(term.difficulty, 0.001)) * term_length_weight(term)
        for term in terms
    ]
    return random.choices(terms, weights=weights, k=1)[0]


def term_cycle_key(term):
    cached = getattr(term, "_cycle_key", None)
    if cached:
        return cached
    key = "|".join(str(part) for part in (term.chinese, term.initials, term.source_label, term.source))
    try:
        setattr(term, "_cycle_key", key)
    except Exception:
        pass
    return key


def load_daily_terms_state(today=None):
    current_day = today or datetime.now().date().isoformat()
    if not DAILY_TERMS_FILE.exists():
        state = {"date": current_day, "buckets": {}}
        _DAILY_TERMS_CACHE.update({"date": current_day, "mtime_ns": None, "state": state})
        return state
    try:
        mtime_ns = DAILY_TERMS_FILE.stat().st_mtime_ns
    except OSError:
        mtime_ns = None
    if (
        _DAILY_TERMS_CACHE.get("date") == current_day
        and _DAILY_TERMS_CACHE.get("mtime_ns") == mtime_ns
        and isinstance(_DAILY_TERMS_CACHE.get("state"), dict)
    ):
        return _DAILY_TERMS_CACHE["state"]
    try:
        data = json.loads(DAILY_TERMS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {"date": current_day, "buckets": {}}
    if data.get("date") != current_day:
        data = {"date": current_day, "buckets": {}}
    if not isinstance(data.get("buckets"), dict):
        data["buckets"] = {}
    _DAILY_TERMS_CACHE.update({"date": current_day, "mtime_ns": mtime_ns, "state": data})
    return data


def save_daily_terms_state(state):
    try:
        DAILY_TERMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        DAILY_TERMS_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            mtime_ns = DAILY_TERMS_FILE.stat().st_mtime_ns
        except OSError:
            mtime_ns = None
        _DAILY_TERMS_CACHE.update({"date": state.get("date"), "mtime_ns": mtime_ns, "state": state})
    except Exception:
        pass


def choose_daily_term_by_difficulty(terms, gameplay_difficulty, bucket_key):
    if not terms:
        raise ValueError("词库为空")
    state = load_daily_terms_state()
    all_keys = {term_cycle_key(term) for term in terms}
    bucket = state.setdefault("buckets", {}).setdefault(bucket_key, {"seen": []})
    seen = {key for key in bucket.get("seen", []) if key in all_keys}
    if len(seen) >= len(all_keys):
        seen = set()
    unseen = [term for term in terms if term_cycle_key(term) not in seen]
    chosen = choose_term_by_difficulty(unseen or terms, gameplay_difficulty)
    seen.add(term_cycle_key(chosen))
    bucket["seen"] = sorted(seen)
    bucket["total"] = len(all_keys)
    bucket["remaining"] = max(0, len(all_keys) - len(seen))
    save_daily_terms_state(state)
    return chosen


def random_free_hint_quota(length, gameplay_difficulty):
    max_count = max(0, length // 2)
    if max_count <= 0:
        return 0
    zero_prob = FREE_HINT_ZERO_PROB.get(gameplay_difficulty, FREE_HINT_ZERO_PROB["混合模式"])
    if random.random() < zero_prob:
        return 0
    decay = FREE_HINT_DECAY.get(gameplay_difficulty, FREE_HINT_DECAY["混合模式"])
    choices = list(range(1, max_count + 1))
    weights = [decay ** (value - 1) for value in choices]
    return random.choices(choices, weights=[(1 - zero_prob) * weight for weight in weights], k=1)[0]


def random_mask_positions(initials, gameplay_difficulty):
    table = MASK_PROBABILITIES.get(gameplay_difficulty)
    if not table:
        return []
    length = len(initials)
    if length >= 8 and 8 in table:
        tier = 8
    elif length >= 6:
        tier = 6
    elif length >= 5:
        tier = 5
    elif length >= 4:
        tier = 4
    else:
        return []
    count_probs = table.get(tier, {})
    if not count_probs:
        return []
    counts = [0] + sorted(count_probs)
    probabilities = [max(0.0, 1.0 - sum(count_probs.values()))] + [count_probs[count] for count in counts[1:]]
    mask_count = random.choices(counts, weights=probabilities, k=1)[0]
    if mask_count <= 0:
        return []
    mask_count = min(mask_count, length)
    return sorted(random.sample(range(length), mask_count))


def apply_initial_mask(initials, positions):
    masked = list(initials)
    for position in positions:
        if 0 <= position < len(masked):
            masked[position] = "*"
    return "".join(masked)


def summarize_records(records, achievements_data=None):
    counted = [record for record in records if is_counted_record(record)]
    rating_summary = summarize_rating(counted, achievements_data=achievements_data)
    abandoned_count = sum(1 for record in records if is_abandoned_record(record))
    total_time = sum(float(record.get("elapsed_seconds") or 0) for record in counted)
    raw_total_score = sum(record_score(record) for record in counted)
    total_score = sum(record_weighted_score(record) for record in counted)
    char_hints = sum(record_hint_count(record) for record in counted)
    paid_char_hints = sum(record_paid_hint_count(record) for record in counted)
    free_char_hints = sum(record_free_hint_count(record) for record in counted)
    library_hints = sum(record_library_hint_count(record) for record in counted)
    success_count = sum(1 for record in counted if record.get("success"))
    cheat_count = sum(1 for record in counted if record.get("cheat_detected") or record.get("finished_by") == "cheated")
    wrong_count = len(counted) - success_count
    difficulty_counts = Counter(record_term_difficulty(record) for record in counted)
    mode_counts = Counter(record.get("difficulty") or "未知" for record in counted)
    mode_scores = Counter()
    record_dimensions = summarize_record_dimensions(records)
    answer_results = Counter()
    for record in counted:
        mode_scores[record.get("difficulty") or "未知"] += record_weighted_score(record)
        for attempt in record.get("all_answers") or []:
            answer_results[attempt.get("result") or "unknown"] += 1
    return {
        "records": counted,
        "total_time": total_time,
        "total_score": total_score,
        "raw_total_score": raw_total_score,
        "total_count": len(counted),
        "success_count": success_count,
        "cheat_count": cheat_count,
        "wrong_count": wrong_count,
        "abandoned_count": abandoned_count,
        "char_hints": char_hints,
        "paid_char_hints": paid_char_hints,
        "free_char_hints": free_char_hints,
        "library_hints": library_hints,
        "hint_count": char_hints + library_hints,
        "exit_count": abandoned_count,
        "difficulty_counts": difficulty_counts,
        "mode_counts": mode_counts,
        "mode_scores": mode_scores,
        "record_dimensions": record_dimensions,
        "by_subject": record_dimensions["subject"],
        "by_mode": record_dimensions["mode"],
        "by_play_mode": record_dimensions["play_mode"],
        "by_difficulty": record_dimensions["difficulty"],
        "answer_results": answer_results,
        "avg_time": total_time / len(counted) if counted else 0,
        "avg_score": total_score / len(counted) if counted else 0,
        "avg_raw_score": raw_total_score / len(counted) if counted else 0,
        "rating": rating_summary["rating"],
        "play_rating": rating_summary["play_rating"],
        "achievement_bonus": rating_summary["achievement_bonus"],
        "achievement_count": rating_summary["achievement_count"],
        "achievement_total": rating_summary["achievement_total"],
        "rating_best_average": rating_summary["best_average"],
        "rating_recent_average": rating_summary["recent_average"],
        "rating_best_values": rating_summary["best_values"],
        "rating_recent_values": rating_summary["recent_values"],
    }


def _achievements_signature(achievements_data):
    completed = achievements_data.get("completed") if isinstance(achievements_data, dict) else {}
    if not isinstance(completed, dict):
        return ()
    return tuple(sorted((str(key), str(value)) for key, value in completed.items() if value))


def _copy_achievements_data(data):
    result = dict(data or {})
    completed = result.get("completed")
    result["completed"] = dict(completed) if isinstance(completed, dict) else {}
    return result


def load_record_summary(record_dir=None, achievements_data=None):
    root = record_dir or RECORD_DIR
    root_key, cached = _record_root_cache(root)
    records = None
    if not cached or cached.get("entries") is None:
        records = load_record_entries(root)
        root_key, cached = _record_root_cache(root)
    revision = int((cached or {}).get("revision") or 0)
    cached_entries = (cached or {}).get("entries") or []
    count = len(cached_entries)
    if achievements_data is None:
        achievements_path = (root / ACHIEVEMENTS_FILE.name) if record_dir is not None else ACHIEVEMENTS_FILE
        achievements_data = read_achievements(achievements_path)
    cache_key = (root_key, revision, count, _achievements_signature(achievements_data))
    cached = _RECORD_SUMMARY_CACHE.get(cache_key)
    if cached is not None:
        return cached
    if records is None:
        records = _copy_record_entries(cached_entries)
    summary = summarize_records(records, achievements_data=achievements_data)
    _RECORD_SUMMARY_CACHE[cache_key] = summary
    return summary


def format_duration(seconds):
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    if hours:
        return f"{hours}时{minutes}分{sec}秒"
    if minutes:
        return f"{minutes}分{sec}秒"
    return f"{sec}秒"


def read_achievements(path=None):
    target = path or ACHIEVEMENTS_FILE
    if not target.exists():
        return {"completed": {}}
    cache_key = str(target.resolve())
    try:
        mtime_ns = target.stat().st_mtime_ns
    except OSError:
        mtime_ns = None
    cached = _ACHIEVEMENTS_CACHE.get(cache_key)
    if cached and cached.get("mtime_ns") == mtime_ns:
        return _copy_achievements_data(cached["data"])
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {"completed": {}}
    if not isinstance(data.get("completed"), dict):
        data["completed"] = {}
    _ACHIEVEMENTS_CACHE[cache_key] = {"mtime_ns": mtime_ns, "data": _copy_achievements_data(data)}
    return data


def write_achievements(data):
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    ACHIEVEMENTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        cache_key = str(ACHIEVEMENTS_FILE.resolve())
        mtime_ns = ACHIEVEMENTS_FILE.stat().st_mtime_ns
        _ACHIEVEMENTS_CACHE[cache_key] = {"mtime_ns": mtime_ns, "data": _copy_achievements_data(data)}
    except OSError:
        pass
    _RECORD_SUMMARY_CACHE.clear()
