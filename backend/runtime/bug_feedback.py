import json
import uuid
from datetime import datetime

from .game_config import PROJECT_DIR


FEEDBACK_FILE = PROJECT_DIR / "profile" / "admin" / "bug_feedback.json"
FEEDBACK_VERSION = 2


STATUS_LABELS = {
    "pending": "待处理",
    "accepted": "同意",
    "rejected": "拒绝",
    "modified": "修改",
}

TERM_ACTION_LABELS = {
    "delete": "删除",
    "modify": "改动",
}


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _empty_data():
    return {"version": FEEDBACK_VERSION, "items": []}


def _normalize_text(value, limit=3000):
    text = str(value or "").strip()
    return text[:limit]


def _normalize_item(item):
    if not isinstance(item, dict):
        item = {}
    status = str(item.get("status") or "pending")
    if status not in STATUS_LABELS:
        status = "pending"
    player_name = str(item.get("player_name") or item.get("player_nickname") or "")
    term_action = str(item.get("term_action") or "")
    term_action_label = str(item.get("term_action_label") or TERM_ACTION_LABELS.get(term_action, ""))
    normalized = {
        "id": str(item.get("id") or uuid.uuid4().hex[:12]),
        "created_at": str(item.get("created_at") or _now()),
        "updated_at": str(item.get("updated_at") or item.get("created_at") or _now()),
        "feedback_type": str(item.get("feedback_type") or "general"),
        "player_id": str(item.get("player_id") or ""),
        "player_name": player_name,
        "player_nickname": player_name,
        "suggestion": _normalize_text(item.get("suggestion")),
        "term_action": term_action,
        "term_action_label": term_action_label,
        "mode_context": _normalize_text(item.get("mode_context"), limit=500),
        "source_label": _normalize_text(item.get("source_label"), limit=300),
        "source_file": _normalize_text(item.get("source_file"), limit=800),
        "term_name": _normalize_text(item.get("term_name"), limit=200),
        "proposed_change": _normalize_text(item.get("proposed_change"), limit=1000),
        "record_path": _normalize_text(item.get("record_path"), limit=800),
        "status": status,
        "status_label": STATUS_LABELS[status],
        "admin_id": str(item.get("admin_id") or ""),
        "admin_nickname": str(item.get("admin_nickname") or ""),
        "reviewed_at": str(item.get("reviewed_at") or ""),
        "modification": _normalize_text(item.get("modification")),
        "fixed": bool(item.get("fixed", False)),
        "fixed_at": str(item.get("fixed_at") or ""),
        "fixed_note": _normalize_text(item.get("fixed_note")),
        "history": item.get("history") if isinstance(item.get("history"), list) else [],
    }
    normalized["history"] = [entry for entry in normalized["history"] if isinstance(entry, dict)]
    return normalized


def normalize_feedback_data(data):
    if not isinstance(data, dict):
        data = _empty_data()
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return {
        "version": FEEDBACK_VERSION,
        "items": [_normalize_item(item) for item in items],
    }


def load_feedback(path=None):
    target = path or FEEDBACK_FILE
    if not target.exists():
        return _empty_data()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return _empty_data()
    return normalize_feedback_data(data)


def save_feedback(data, path=None):
    target = path or FEEDBACK_FILE
    normalized = normalize_feedback_data(data)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def feedback_file_path():
    return FEEDBACK_FILE


def submit_feedback(account, suggestion, path=None):
    text = _normalize_text(suggestion)
    if not text:
        raise ValueError("请输入反馈内容。")
    now = _now()
    player_name = str((account or {}).get("nickname") or "")
    item = {
        "id": f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        "created_at": now,
        "updated_at": now,
        "player_id": str((account or {}).get("id") or ""),
        "player_name": player_name,
        "player_nickname": player_name,
        "suggestion": text,
        "status": "pending",
        "status_label": STATUS_LABELS["pending"],
        "admin_id": "",
        "admin_nickname": "",
        "reviewed_at": "",
        "modification": "",
        "fixed": False,
        "fixed_at": "",
        "fixed_note": "",
        "history": [
            {
                "at": now,
                "action": "submit",
                "player_id": str((account or {}).get("id") or ""),
                "player_name": player_name,
                "player_nickname": player_name,
            }
        ],
    }
    data = load_feedback(path)
    data["items"].insert(0, item)
    save_feedback(data, path)
    return item


def submit_term_feedback(
    account,
    action,
    mode_context,
    source_label,
    term_name,
    proposed_change="",
    source_file="",
    record_path="",
    path=None,
):
    action = str(action or "").strip()
    if action not in TERM_ACTION_LABELS:
        raise ValueError("未知的词条反馈类型。")
    term_name = _normalize_text(term_name, limit=200)
    if not term_name:
        raise ValueError("缺少词条名称。")
    mode_context = _normalize_text(mode_context, limit=500) or "未知模式"
    source_label = _normalize_text(source_label, limit=300) or "未知"
    proposed_change = _normalize_text(proposed_change, limit=1000)
    if action == "modify" and not proposed_change:
        raise ValueError("请输入这个词应该改为什么。")

    if action == "delete":
        suggestion = f"在进行{mode_context}时，{source_label}词库里的{term_name}词应该被删掉"
    else:
        suggestion = f"在进行{mode_context}时，{source_label}词库里的{term_name}词应该改为{proposed_change}"

    now = _now()
    player_name = str((account or {}).get("nickname") or "")
    item = {
        "id": f"tf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        "created_at": now,
        "updated_at": now,
        "feedback_type": "term",
        "player_id": str((account or {}).get("id") or ""),
        "player_name": player_name,
        "player_nickname": player_name,
        "suggestion": suggestion,
        "term_action": action,
        "term_action_label": TERM_ACTION_LABELS[action],
        "mode_context": mode_context,
        "source_label": source_label,
        "source_file": _normalize_text(source_file, limit=800),
        "term_name": term_name,
        "proposed_change": proposed_change,
        "record_path": _normalize_text(record_path, limit=800),
        "status": "pending",
        "status_label": STATUS_LABELS["pending"],
        "admin_id": "",
        "admin_nickname": "",
        "reviewed_at": "",
        "modification": "",
        "fixed": False,
        "fixed_at": "",
        "fixed_note": "",
        "history": [
            {
                "at": now,
                "action": "submit_term_feedback",
                "player_id": str((account or {}).get("id") or ""),
                "player_name": player_name,
                "player_nickname": player_name,
                "term_action": action,
                "term_name": term_name,
                "proposed_change": proposed_change,
            }
        ],
    }
    data = load_feedback(path)
    data["items"].insert(0, item)
    save_feedback(data, path)
    return item


def update_feedback_status(feedback_id, status, admin_account, modification="", path=None):
    if status not in {"accepted", "rejected", "modified"}:
        raise ValueError("未知的反馈处理状态。")
    data = load_feedback(path)
    now = _now()
    for item in data["items"]:
        if item.get("id") != feedback_id:
            continue
        item["status"] = status
        item["status_label"] = STATUS_LABELS[status]
        item["updated_at"] = now
        item["reviewed_at"] = now
        item["admin_id"] = str((admin_account or {}).get("id") or "")
        item["admin_nickname"] = str((admin_account or {}).get("nickname") or "")
        item["modification"] = _normalize_text(modification) if status == "modified" else ""
        item.setdefault("history", []).append(
            {
                "at": now,
                "action": status,
                "admin_id": item["admin_id"],
                "admin_nickname": item["admin_nickname"],
                "modification": item["modification"],
            }
        )
        save_feedback(data, path)
        return item
    raise ValueError("找不到这条反馈。")


def mark_feedback_fixed(feedback_id, fixed=True, note="", path=None):
    data = load_feedback(path)
    now = _now()
    for item in data["items"]:
        if item.get("id") != feedback_id:
            continue
        item["fixed"] = bool(fixed)
        item["fixed_at"] = now if fixed else ""
        item["fixed_note"] = _normalize_text(note)
        item["updated_at"] = now
        item.setdefault("history", []).append(
            {
                "at": now,
                "action": "fixed" if fixed else "unfixed",
                "fixed": bool(fixed),
                "fixed_note": item["fixed_note"],
            }
        )
        save_feedback(data, path)
        return item
    raise ValueError("找不到这条反馈。")
