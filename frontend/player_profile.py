import json

from game_config import PLAYER_SETTINGS_FILE, PROFILE_DIR


DEFAULT_PLAYER_SETTINGS = {
    "nickname": "PHOer",
    "avatar_id": 0,
    "title_id": "rating_0",
    "rank_badge_id": "",
    "backdrop_speed": 1.0,
    "backdrop_density": 1.0,
    "transitions_enabled": True,
    "window_width": 1274,
    "window_height": 806,
}


def clamp_float(value, low, high, fallback):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))


def clamp_int(value, low, high, fallback):
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))


def normalize_player_settings(settings):
    data = dict(DEFAULT_PLAYER_SETTINGS)
    if isinstance(settings, dict):
        data.update(settings)

    nickname = str(data.get("nickname") or "").strip()
    if nickname == "未命名玩家":
        nickname = DEFAULT_PLAYER_SETTINGS["nickname"]
    data["nickname"] = nickname[:16] or DEFAULT_PLAYER_SETTINGS["nickname"]

    try:
        avatar_id = int(data.get("avatar_id"))
    except (TypeError, ValueError):
        avatar_id = DEFAULT_PLAYER_SETTINGS["avatar_id"]
    data["avatar_id"] = max(0, min(14, avatar_id))
    title_id = str(data.get("title_id") or DEFAULT_PLAYER_SETTINGS["title_id"]).strip()
    data["title_id"] = title_id or DEFAULT_PLAYER_SETTINGS["title_id"]
    data["rank_badge_id"] = str(data.get("rank_badge_id") or "").strip()

    data["backdrop_speed"] = clamp_float(data.get("backdrop_speed"), 0.4, 10.0, 1.0)
    data["backdrop_density"] = clamp_float(data.get("backdrop_density"), 0.4, 10.0, 1.0)
    data["window_width"] = clamp_int(data.get("window_width"), 936, 2560, DEFAULT_PLAYER_SETTINGS["window_width"])
    data["window_height"] = clamp_int(data.get("window_height"), 598, 1600, DEFAULT_PLAYER_SETTINGS["window_height"])
    transitions_enabled = data.get("transitions_enabled")
    if isinstance(transitions_enabled, str):
        transitions_enabled = transitions_enabled.strip().lower() not in {"0", "false", "no", "off", "否", "关闭"}
    else:
        transitions_enabled = bool(transitions_enabled)
    data["transitions_enabled"] = transitions_enabled
    return data


def load_player_settings():
    if not PLAYER_SETTINGS_FILE.exists():
        return dict(DEFAULT_PLAYER_SETTINGS)
    try:
        data = json.loads(PLAYER_SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_PLAYER_SETTINGS)
    return normalize_player_settings(data)


def save_player_settings(settings):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    data = normalize_player_settings(settings)
    PLAYER_SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
