import json
from datetime import datetime

from game_config import RANK_PROGRESS_FILE


RANK_CHALLENGES = [
    {"id": 1, "name": "Class 01: Vector", "seconds": 300, "requirements": [("入门", 1), ("入门", 1.5), ("简单", 2)]},
    {"id": 2, "name": "Class 02: Field", "seconds": 311, "requirements": [("入门", 2), ("简单", 2.5), ("简单", 3)]},
    {"id": 3, "name": "Class 03: Spectrum", "seconds": 321, "requirements": [("简单", 3), ("简单", 3.5), ("普通", 4), ("普通", 4.5)]},
    {"id": 4, "name": "Class 04: Matrix", "seconds": 332, "requirements": [("简单", 4), ("普通", 4.5), ("普通", 5), ("普通", 5.5)]},
    {"id": 5, "name": "Class 05: Orbit", "seconds": 343, "requirements": [("普通", 5), ("普通", 5.5), ("普通", 6), ("困难", 6.5), ("困难", 7)]},
    {"id": 6, "name": "Class 06: Tensor", "seconds": 354, "requirements": [("普通", 6), ("普通", 6.5), ("困难", 7), ("困难", 7), ("困难", 7.5)]},
    {"id": 7, "name": "Class 07: Resonance", "seconds": 364, "requirements": [("普通", 6.5), ("困难", 7), ("困难", 7.5), ("困难", 8), ("困难", 8), ("困难", 8.5)]},
    {"id": 8, "name": "Class 08: Critical", "seconds": 375, "requirements": [("困难", 7.5), ("困难", 8), ("困难", 8), ("困难", 8.5), ("困难", 8.5), ("困难", 9)]},
    {"id": 9, "name": "Class 09: Singularity", "seconds": 386, "requirements": [("困难", 8), ("困难", 8.5), ("困难", 8.5), ("困难", 9), ("困难", 9), ("困难", 9.5), ("困难", 9.5)]},
    {"id": 10, "name": "Class 10: Absolute", "seconds": 396, "requirements": [("困难", 8.5), ("困难", 9), ("困难", 9), ("困难", 9.5), ("困难", 9.5), ("困难", 10), ("困难", 10)]},
    {"id": 11, "name": "Class 11: Horizon", "seconds": 407, "requirements": [("困难", 9), ("困难", 9), ("困难", 9.5), ("困难", 9.5), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10)]},
    {"id": 12, "name": "Class 12: Axiom", "seconds": 418, "requirements": [("困难", 9.5), ("困难", 9.5), ("困难", 9.5), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10)]},
    {"id": 13, "name": "Class 13: Noether", "seconds": 429, "requirements": [("困难", 9.5), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10)]},
    {"id": 14, "name": "Class 14: Hilbert", "seconds": 439, "requirements": [("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10)]},
    {"id": 15, "name": "Class 15: Zenith", "seconds": 450, "requirements": [("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10), ("困难", 10)]},
]


SUBJECT_LABELS = {
    "物理模式": "物理",
    "数学模式": "数学",
}

RANK_KIND_LABELS = {
    "free": "限时段位",
    "timed": "旧限时段位",
    "clue": "线索段位",
    "crossword": "字谜段位",
}


def rank_by_id(rank_id):
    for rank in RANK_CHALLENGES:
        if rank["id"] == int(rank_id):
            return rank
    return RANK_CHALLENGES[0]


def subject_label(subject):
    base_subject, rank_kind = split_rank_progress_key(subject)
    label = SUBJECT_LABELS.get(base_subject, str(base_subject or "未知").replace("模式", ""))
    if rank_kind == "timed":
        return f"{label}限时"
    if rank_kind == "clue":
        return f"{label}线索"
    if rank_kind == "crossword":
        return f"{label}字谜"
    return label


def normalize_rank_kind(rank_kind):
    if rank_kind == "crossword":
        return "crossword"
    if rank_kind == "clue":
        return "clue"
    if rank_kind == "timed":
        return "timed"
    return "free"


def rank_kind_label(rank_kind):
    return RANK_KIND_LABELS.get(normalize_rank_kind(rank_kind), RANK_KIND_LABELS["free"])


def rank_progress_key(subject, rank_kind="free"):
    rank_kind = normalize_rank_kind(rank_kind)
    if rank_kind == "crossword":
        return f"{subject}::crossword"
    if rank_kind == "timed":
        return f"{subject}::timed"
    return f"{subject}::clue" if rank_kind == "clue" else subject


def split_rank_progress_key(subject_key):
    text = str(subject_key or "")
    if text.endswith("::clue"):
        return text[:-6], "clue"
    if text.endswith("::crossword"):
        return text[:-11], "crossword"
    if text.endswith("::timed"):
        return text[:-7], "timed"
    return text, "free"


def format_rank_time(seconds):
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}:{sec:02d}"


def rank_hint_cooldown_seconds(rank_id):
    rank_id = max(1, min(len(RANK_CHALLENGES), int(rank_id or 1)))
    if len(RANK_CHALLENGES) <= 1:
        return 60
    return int(round(60 + (rank_id - 1) * 60 / (len(RANK_CHALLENGES) - 1)))


def rank_hint_limit(rank_id):
    rank_id = max(1, min(len(RANK_CHALLENGES), int(rank_id or 1)))
    if rank_id <= 5:
        return 3
    if rank_id <= 10:
        return 2
    return 1


def default_rank_progress():
    subjects = {}
    for subject in ("物理模式", "数学模式"):
        subjects[rank_progress_key(subject, "free")] = {"highest": 0, "passed": {}}
        subjects[rank_progress_key(subject, "timed")] = {"highest": 0, "passed": {}}
        subjects[rank_progress_key(subject, "clue")] = {"highest": 0, "passed": {}}
        subjects[rank_progress_key(subject, "crossword")] = {"highest": 0, "passed": {}}
    return {"subjects": subjects}


def read_rank_progress():
    if not RANK_PROGRESS_FILE.exists():
        return default_rank_progress()
    try:
        data = json.loads(RANK_PROGRESS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return default_rank_progress()
    base = default_rank_progress()
    for subject, info in (data.get("subjects") or {}).items():
        if subject not in base["subjects"]:
            base["subjects"][subject] = {"highest": 0, "passed": {}}
        highest = int((info or {}).get("highest") or 0)
        base["subjects"][subject]["highest"] = max(0, min(len(RANK_CHALLENGES), highest))
        passed = (info or {}).get("passed") or {}
        base["subjects"][subject]["passed"] = {str(key): value for key, value in passed.items()}
    return base


def write_rank_progress(progress):
    RANK_PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RANK_PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def _rank_pass_entry(value):
    if isinstance(value, dict):
        return dict(value)
    if value:
        return {"first_passed_at": str(value), "latest_passed_at": str(value)}
    return {}


def rank_pass_score(subject_info, rank_id):
    passed = (subject_info or {}).get("passed") or {}
    entry = _rank_pass_entry(passed.get(str(rank_id)))
    score = entry.get("best_score")
    try:
        return int(score)
    except (TypeError, ValueError):
        return None


def rank_passed_ids(subject_info):
    passed = (subject_info or {}).get("passed") or {}
    ids = []
    for key, value in passed.items():
        try:
            rank_id = int(key)
        except (TypeError, ValueError):
            continue
        if 1 <= rank_id <= len(RANK_CHALLENGES) and _rank_pass_entry(value):
            ids.append(rank_id)
    if not ids:
        try:
            highest = int((subject_info or {}).get("highest") or 0)
        except (TypeError, ValueError):
            highest = 0
        if 1 <= highest <= len(RANK_CHALLENGES):
            ids.append(highest)
    return sorted(set(ids))


def rank_is_passed(subject_info, rank_id):
    try:
        rank_id = int(rank_id)
    except (TypeError, ValueError):
        return False
    return rank_id in set(rank_passed_ids(subject_info))


def rank_highest_passed(subject_info):
    ids = rank_passed_ids(subject_info)
    return max(ids) if ids else 0


def mark_rank_passed(subject, rank_id, rank_kind="free", score=None):
    progress = read_rank_progress()
    subject_key = rank_progress_key(subject, rank_kind)
    info = progress.setdefault("subjects", {}).setdefault(subject_key, {"highest": 0, "passed": {}})
    rank_id = int(rank_id)
    info["highest"] = max(int(info.get("highest") or 0), max(0, min(len(RANK_CHALLENGES), rank_id)))
    passed = info.setdefault("passed", {})
    now = datetime.now().isoformat(timespec="seconds")
    entry = _rank_pass_entry(passed.get(str(rank_id)))
    entry.setdefault("first_passed_at", now)
    entry["latest_passed_at"] = now
    if score is not None:
        score = int(score)
        entry["last_score"] = score
        entry["best_score"] = max(int(entry.get("best_score") or score), score)
    passed[str(rank_id)] = entry
    write_rank_progress(progress)
    return progress


def rank_badge_id(subject, rank_id, rank_kind="free"):
    subject = rank_progress_key(subject, rank_kind)
    return f"{subject}:{int(rank_id)}"


def parse_rank_badge_id(badge_id):
    text = str(badge_id or "")
    if ":" not in text:
        return None, 0
    subject, rank_id = text.rsplit(":", 1)
    try:
        return subject, int(rank_id)
    except ValueError:
        return None, 0


def rank_badge_name(badge_id):
    subject_key, rank_id = parse_rank_badge_id(badge_id)
    if not subject_key or not rank_id:
        return "不佩戴"
    rank = rank_by_id(rank_id)
    return f"{rank_badge_short_label(badge_id)} {rank['name']}"


def rank_badge_short_label(badge_id):
    subject_key, rank_id = parse_rank_badge_id(badge_id)
    if not subject_key or not rank_id:
        return "无段位"
    subject, rank_kind = split_rank_progress_key(subject_key)
    prefix = subject_label(subject)
    suffix = {
        "free": "限时",
        "timed": "旧限时",
        "clue": "线索",
        "crossword": "字谜",
    }.get(normalize_rank_kind(rank_kind), "限时")
    return f"{prefix}-{suffix}"


def unlocked_rank_badges(progress=None):
    progress = progress or read_rank_progress()
    badges = []
    order = [
        rank_progress_key("物理模式", "free"),
        rank_progress_key("物理模式", "timed"),
        rank_progress_key("物理模式", "clue"),
        rank_progress_key("物理模式", "crossword"),
        rank_progress_key("数学模式", "free"),
        rank_progress_key("数学模式", "timed"),
        rank_progress_key("数学模式", "clue"),
        rank_progress_key("数学模式", "crossword"),
    ]
    all_subjects = progress.get("subjects") or {}
    for subject in [*order, *(key for key in all_subjects if key not in order)]:
        info = all_subjects.get(subject, {})
        for rank_id in rank_passed_ids(info):
            badge_id = rank_badge_id(subject, rank_id)
            badges.append((badge_id, rank_badge_name(badge_id)))
    return badges


def coerce_rank_badge_id(badge_id, progress=None):
    unlocked = {item[0] for item in unlocked_rank_badges(progress)}
    return badge_id if badge_id in unlocked else ""


def rank_title_rewards(progress=None):
    return [(f"rank_title:{badge_id}", name) for badge_id, name in unlocked_rank_badges(progress)]


def draw_rank_badge(canvas, badge_id, width=170, height=34, selected=False):
    canvas.delete("all")
    scale = max(0.65, height / 34)

    def s(value):
        return value * scale

    def font_size(value):
        return max(6, int(round(value * scale)))

    subject, rank_id = parse_rank_badge_id(badge_id)
    if not subject or not rank_id:
        canvas.create_rectangle(s(2), s(2), width - s(2), height - s(2), outline="#3b4560", fill="#182033", width=max(1, int(round(s(2)))))
        canvas.create_text(width / 2, height / 2, text="无段位标识", fill="#64708f", font=("Microsoft YaHei UI", font_size(10), "bold"))
        return
    styles = [
        ("#050507", "#2a2f3a", "#f8fafc"),
        ("#2b2f36", "#6b7280", "#f8fafc"),
        ("#3b0b10", "#ef4444", "#fff7ed"),
        ("#4a1609", "#f97316", "#fff7ed"),
        ("#4a2c06", "#eab308", "#fff7ed"),
        ("#123018", "#22c55e", "#ecfdf5"),
        ("#063332", "#14b8a6", "#ecfeff"),
        ("#082f49", "#38bdf8", "#f0f9ff"),
        ("#172554", "#6366f1", "#eef2ff"),
        ("#2e1065", "#a855f7", "#faf5ff"),
        ("#f8fafc", "#cbd5e1", "#0f172a"),
        ("#06141f", "#00e5ff", "#f8fafc"),
        ("#071607", "#7cff6b", "#f8fafc"),
        ("#1f0a2a", "#ff4fd8", "#fff7ed"),
        ("#080b12", "#ffffff", "#f8fafc"),
    ]
    fill, accent, text_color = styles[max(0, min(rank_id, len(styles)) - 1)]
    outline = "#f8fafc" if selected or rank_id >= 15 else accent
    canvas.create_rectangle(s(1), s(1), width - s(1), height - s(1), outline=outline, fill=fill, width=max(1, int(round(s(2)))))
    if rank_id >= 12:
        vivid = ["#67e8f9", "#9ff2b2", "#f6d36b", "#ff6b8a", "#c084fc"]
        stripe_w = max(s(10), width / 18)
        for index in range(int(width // stripe_w) + 2):
            color = vivid[(index + rank_id) % len(vivid)]
            x0 = index * stripe_w - (rank_id % 3) * s(3)
            canvas.create_polygon(x0, s(3), x0 + stripe_w, s(3), x0 + stripe_w - s(8), height - s(3), x0 - s(8), height - s(3), fill=color, outline="")
        canvas.create_rectangle(s(4), s(4), width - s(4), height - s(4), fill=fill, outline=accent, width=max(1, int(round(s(1)))))
    else:
        canvas.create_rectangle(s(4), s(4), width - s(4), height - s(4), outline=accent, width=max(1, int(round(s(1)))))
    inner_fill = "#111725" if rank_id != 11 else "#e2e8f0"
    inner_text = text_color
    left_right = min(width * 0.40, s(62))
    left_center = (s(8) + left_right) / 2
    canvas.create_rectangle(s(8), s(7), left_right, height - s(7), fill=inner_fill, outline=accent, width=max(1, int(round(s(1)))))
    canvas.create_text(left_center, height / 2, text=f"CLASS {rank_id:02d}", fill=inner_text, font=("Consolas", font_size(8), "bold"))
    canvas.create_rectangle(left_right + s(4), s(7), width - s(8), height - s(7), fill=inner_fill, outline=accent, width=max(1, int(round(s(1)))))
    label = rank_badge_short_label(badge_id)
    canvas.create_text((width + left_right) / 2, height / 2, text=label, fill=inner_text, font=("Microsoft YaHei UI", font_size(9), "bold"))
