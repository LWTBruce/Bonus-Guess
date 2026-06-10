import json
from datetime import datetime

from .game_config import RANK_PROGRESS_FILE


RANK_CLASS_NAMES = [
    "Spark",
    "Vector",
    "Field",
    "Orbit",
    "Flux",
    "Tensor",
    "Spectrum",
    "Resonance",
    "Symmetry",
    "Manifold",
    "Operator",
    "Critical",
    "Entropy",
    "Noether",
    "Hilbert",
    "Axiom",
    "Horizon",
    "Singularity",
    "Zenith",
    "Absolute",
]

RANK_TARGETS = [
    1.0,
    1.5,
    2.0,
    2.6,
    3.2,
    3.8,
    4.4,
    5.0,
    5.6,
    6.3,
    7.0,
    7.6,
    8.2,
    8.8,
    9.4,
    10.0,
    10.5,
    11.0,
    11.5,
    12.0,
]


def rank_difficulty_name(rank_id):
    rank_id = int(rank_id or 1)
    if rank_id <= 4:
        return "入门"
    if rank_id <= 8:
        return "简单"
    if rank_id <= 11:
        return "普通"
    if rank_id <= 16:
        return "困难"
    return "噩梦"


def rank_target_difficulty(rank_id):
    rank_id = max(1, min(len(RANK_TARGETS), int(rank_id or 1)))
    return RANK_TARGETS[rank_id - 1]


def _half_step(value):
    return round(float(value) * 2) / 2


def _rank_requirement_count(rank_id):
    return min(12, 3 + (int(rank_id or 1) - 1) // 2)


def _rank_requirements(rank_id):
    difficulty = rank_difficulty_name(rank_id)
    target = rank_target_difficulty(rank_id)
    count = _rank_requirement_count(rank_id)
    start = max(1.0, target - 1.0)
    if count <= 1:
        return [(difficulty, _half_step(target))]
    values = []
    for index in range(count):
        raw = start + (target - start) * index / (count - 1)
        values.append((difficulty, _half_step(raw)))
    return values


def _rank_seconds(rank_id):
    return int(round(300 + (int(rank_id or 1) - 1) * 150 / 14))


RANK_CHALLENGES = [
    {
        "id": index + 1,
        "name": f"Class {index + 1:02d}: {name}",
        "seconds": _rank_seconds(index + 1),
        "requirements": _rank_requirements(index + 1),
    }
    for index, name in enumerate(RANK_CLASS_NAMES)
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


def rank_count_for_kind(rank_kind="free"):
    return len(RANK_CHALLENGES)


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
    return int(round(60 + (rank_id - 1) * 60 / 14))


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
        _base_subject, rank_kind = split_rank_progress_key(subject)
        base["subjects"][subject]["highest"] = max(0, min(rank_count_for_kind(rank_kind), highest))
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


def rank_unlock_progress(subject_info, rank_kind="free"):
    max_rank = rank_count_for_kind(rank_kind)
    passed = (subject_info or {}).get("passed") or {}
    explicit_ids = set()
    for key, value in passed.items():
        try:
            rank_id = int(key)
        except (TypeError, ValueError):
            continue
        if 1 <= rank_id <= max_rank and _rank_pass_entry(value):
            explicit_ids.add(rank_id)
    if not explicit_ids:
        try:
            highest = int((subject_info or {}).get("highest") or 0)
        except (TypeError, ValueError):
            highest = 0
        return max(0, min(max_rank, highest))
    current = 9
    while current + 1 <= max_rank and (current + 1) in explicit_ids:
        current += 1
    return max(0, min(max_rank, current))


def rank_visible_limit(subject_info=None, rank_kind="free"):
    max_rank = rank_count_for_kind(rank_kind)
    base_limit = min(15, max_rank)
    progress = rank_unlock_progress(subject_info, rank_kind)
    if max_rank <= base_limit or progress < base_limit:
        return base_limit
    return min(max_rank, progress + 1)


def rank_unlock_limit(subject_info=None, rank_kind="free"):
    max_rank = rank_count_for_kind(rank_kind)
    progress = rank_unlock_progress(subject_info, rank_kind)
    return min(max_rank, max(10, progress + 1))


def rank_is_unlocked(subject_info, rank_id, rank_kind="free"):
    try:
        rank_id = int(rank_id)
    except (TypeError, ValueError):
        return False
    return 1 <= rank_id <= rank_unlock_limit(subject_info, rank_kind)


def visible_rank_challenges(subject_info=None, rank_kind="free"):
    limit = rank_visible_limit(subject_info, rank_kind)
    return [rank for rank in RANK_CHALLENGES if int(rank.get("id") or 0) <= limit]


def mark_rank_passed(subject, rank_id, rank_kind="free", score=None):
    progress = read_rank_progress()
    subject_key = rank_progress_key(subject, rank_kind)
    info = progress.setdefault("subjects", {}).setdefault(subject_key, {"highest": 0, "passed": {}})
    rank_id = int(rank_id)
    max_rank = rank_count_for_kind(rank_kind)
    if rank_id < 1 or rank_id > max_rank:
        raise ValueError(f"rank_id must be between 1 and {max_rank}")
    info["highest"] = max(int(info.get("highest") or 0), rank_id)
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
        _base_subject, rank_kind = split_rank_progress_key(subject)
        max_rank = rank_count_for_kind(rank_kind)
        for rank_id in rank_passed_ids(info):
            if rank_id > max_rank:
                continue
            badge_id = rank_badge_id(subject, rank_id)
            badges.append((badge_id, rank_badge_name(badge_id)))
    return badges


def coerce_rank_badge_id(badge_id, progress=None):
    unlocked = {item[0] for item in unlocked_rank_badges(progress)}
    return badge_id if badge_id in unlocked else ""


def rank_title_rewards(progress=None):
    return [(f"rank_title:{badge_id}", name) for badge_id, name in unlocked_rank_badges(progress)]


def draw_rank_badge(canvas, badge_id, width=170, height=34, selected=False, transparent=False, background=None):
    canvas.delete("all")
    scale = max(0.65, height / 34)

    if background is None:
        try:
            background = canvas.cget("bg")
        except Exception:
            background = None

    def readable_color(default="#f8fafc"):
        text = str(background or "").strip()
        if not transparent or not text.startswith("#") or len(text) != 7:
            return default
        try:
            r = int(text[1:3], 16) / 255
            g = int(text[3:5], 16) / 255
            b = int(text[5:7], 16) / 255
        except ValueError:
            return default
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "#111725" if luminance > 0.42 else default

    def s(value):
        return value * scale

    def font_size(value):
        return max(6, int(round(value * scale)))

    subject, rank_id = parse_rank_badge_id(badge_id)
    if not subject or not rank_id:
        canvas.create_rectangle(s(2), s(2), width - s(2), height - s(2), outline="#3b4560", fill="" if transparent else "#182033", width=max(1, int(round(s(2)))))
        canvas.create_text(width / 2, height / 2, text="无段位标识", fill=readable_color("#64708f"), font=("Microsoft YaHei UI", font_size(10), "bold"))
        return
    if rank_id >= 16:
        high_styles = {
            16: ("#031724", "#38f8ff", "#dffbff", "#0f4a71", "#9ff2ff"),
            17: ("#0d102b", "#9b7cff", "#f4edff", "#31206f", "#dbb7ff"),
            18: ("#210817", "#ff5fa2", "#fff0f6", "#6f143d", "#ffd166"),
            19: ("#1b1202", "#ffd166", "#fff7d1", "#654200", "#7cf4b8"),
            20: ("#020617", "#f8fafc", "#ffffff", "#075985", "#67e8f9"),
        }
        fill, accent, text_color, shadow, particle = high_styles.get(rank_id, high_styles[20])
        text_color = readable_color(text_color)
        outline = readable_color("#ffffff") if selected else accent
        stroke = max(1, int(round(s(2))))
        x0, y0 = s(4), s(4)
        x1, y1 = width - s(5), height - s(5)
        bubble = [
            x0 + s(9), y0,
            x1 - s(18), y0,
            x1 - s(6), y0 + s(7),
            x1 - s(6), y1 - s(12),
            width - s(1), y1 - s(4),
            x1 - s(25), y1 - s(7),
            x0 + s(9), y1,
            x0, y1 - s(8),
            x0, y0 + s(8),
        ]
        if transparent:
            canvas.create_polygon(bubble, fill="", outline=outline, width=stroke, smooth=True, splinesteps=16)
        else:
            canvas.create_polygon(bubble, fill=shadow, outline="", smooth=True, splinesteps=16)
            canvas.move("all", s(1.5), s(1.5))
            canvas.create_polygon(bubble, fill=fill, outline=outline, width=stroke, smooth=True, splinesteps=16)
        canvas.create_line(x0 + s(18), y0 + s(4), x1 - s(38), y0 + s(4), fill=accent, width=max(1, int(round(s(1)))))
        canvas.create_line(x0 + s(26), y1 - s(4), x1 - s(46), y1 - s(4), fill=accent, width=max(1, int(round(s(1)))))

        nucleus_x = width - s(33)
        nucleus_y = height / 2
        orbit_w = max(s(22), width * 0.14)
        orbit_h = max(s(8), height * 0.30)
        orbit_color = "#7dd3fc" if rank_id != 18 else "#fbcfe8"
        canvas.create_oval(nucleus_x - orbit_w, nucleus_y - orbit_h, nucleus_x + orbit_w, nucleus_y + orbit_h, outline=orbit_color, width=max(1, int(round(s(1)))))
        canvas.create_line(nucleus_x - orbit_w * 0.80, nucleus_y + orbit_h * 1.15, nucleus_x + orbit_w * 0.80, nucleus_y - orbit_h * 1.15, fill=accent, width=max(1, int(round(s(1)))))
        canvas.create_line(nucleus_x - orbit_w * 0.65, nucleus_y - orbit_h * 1.05, nucleus_x + orbit_w * 0.65, nucleus_y + orbit_h * 1.05, fill=shadow, width=max(1, int(round(s(1)))))
        canvas.create_oval(nucleus_x - s(3), nucleus_y - s(3), nucleus_x + s(3), nucleus_y + s(3), fill=particle, outline=accent)
        for dx, dy, radius in [(-18, -9, 1.6), (-9, 8, 1.2), (12, -8, 1.3), (21, 6, 1.1)]:
            px = nucleus_x + s(dx)
            py = nucleus_y + s(dy)
            canvas.create_oval(px - s(radius), py - s(radius), px + s(radius), py + s(radius), fill=particle, outline="")

        label = rank_badge_short_label(badge_id)
        class_x = s(16)
        label_x = width * 0.54
        if width < s(185):
            label_x = width * 0.57
        canvas.create_text(class_x, height / 2, anchor="w", text=f"CLASS {rank_id:02d}", fill=text_color, font=("Consolas", font_size(8), "bold"))
        canvas.create_text(label_x, height / 2, text=label, fill=text_color, font=("Microsoft YaHei UI", font_size(9), "bold"))
        if selected:
            canvas.create_line(x0 + s(10), y0 - s(1), x1 - s(22), y0 - s(1), fill="#ffffff", width=max(1, int(round(s(1)))))
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
        ("#0b1020", "#93c5fd", "#eff6ff"),
        ("#120d2a", "#c084fc", "#faf5ff"),
        ("#220b16", "#fb7185", "#fff1f2"),
        ("#1b1304", "#facc15", "#fffbeb"),
        ("#020617", "#f8fafc", "#ffffff"),
    ]
    fill, accent, text_color = styles[max(0, min(rank_id, len(styles)) - 1)]
    text_color = readable_color(text_color)
    outline = readable_color("#f8fafc") if selected or rank_id >= 15 else accent
    canvas.create_rectangle(s(1), s(1), width - s(1), height - s(1), outline=outline, fill="" if transparent else fill, width=max(1, int(round(s(2)))))
    if rank_id >= 12 and not transparent:
        vivid = ["#67e8f9", "#9ff2b2", "#f6d36b", "#ff6b8a", "#c084fc"]
        stripe_w = max(s(10), width / 18)
        for index in range(int(width // stripe_w) + 2):
            color = vivid[(index + rank_id) % len(vivid)]
            x0 = index * stripe_w - (rank_id % 3) * s(3)
            canvas.create_polygon(x0, s(3), x0 + stripe_w, s(3), x0 + stripe_w - s(8), height - s(3), x0 - s(8), height - s(3), fill=color, outline="")
        canvas.create_rectangle(s(4), s(4), width - s(4), height - s(4), fill=fill, outline=accent, width=max(1, int(round(s(1)))))
    else:
        canvas.create_rectangle(s(4), s(4), width - s(4), height - s(4), outline=accent, width=max(1, int(round(s(1)))))
    inner_fill = "" if transparent else ("#111725" if rank_id != 11 else "#e2e8f0")
    inner_text = text_color
    left_right = min(width * 0.40, s(62))
    left_center = (s(8) + left_right) / 2
    canvas.create_rectangle(s(8), s(7), left_right, height - s(7), fill=inner_fill, outline=accent, width=max(1, int(round(s(1)))))
    canvas.create_text(left_center, height / 2, text=f"CLASS {rank_id:02d}", fill=inner_text, font=("Consolas", font_size(8), "bold"))
    canvas.create_rectangle(left_right + s(4), s(7), width - s(8), height - s(7), fill=inner_fill, outline=accent, width=max(1, int(round(s(1)))))
    label = rank_badge_short_label(badge_id)
    canvas.create_text((width + left_right) / 2, height / 2, text=label, fill=inner_text, font=("Microsoft YaHei UI", font_size(9), "bold"))
