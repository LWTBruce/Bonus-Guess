import json

from .game_config import PLAYER_SETTINGS_FILE, PROFILE_DIR
from .music_catalog import DEFAULT_HOME_MUSIC_ID, normalize_home_music_id
from .sfx_catalog import DEFAULT_SFX_CHOICES, normalize_sfx_choices


DEFAULT_PLAYER_SETTINGS = {
    "nickname": "PHOer",
    "avatar_id": 0,
    "title_id": "rating_0",
    "rank_badge_id": "",
    "backdrop_theme": "blue",
    "backdrop_speed": 1.0,
    "backdrop_density": 1.0,
    "backdrop_opacity": 1.0,
    "font_scale": 1.0,
    "music_volume": 0.55,
    "sfx_volume": 0.75,
    "home_music_id": DEFAULT_HOME_MUSIC_ID,
    "sfx_choices": dict(DEFAULT_SFX_CHOICES),
    "transitions_enabled": True,
    "window_width": 1274,
    "window_height": 806,
    "tutorial_completed": True,
    "admin_reveal_hidden": False,
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
    backdrop_theme = str(data.get("backdrop_theme") or DEFAULT_PLAYER_SETTINGS["backdrop_theme"]).strip()
    if backdrop_theme not in {"blue", "green", "red", "yellow", "pink", "purple"}:
        backdrop_theme = DEFAULT_PLAYER_SETTINGS["backdrop_theme"]
    data["backdrop_theme"] = backdrop_theme

    data["backdrop_speed"] = clamp_float(data.get("backdrop_speed"), 0.4, 10.0, 1.0)
    data["backdrop_density"] = clamp_float(data.get("backdrop_density"), 0.4, 10.0, 1.0)
    data["backdrop_opacity"] = clamp_float(data.get("backdrop_opacity"), 0.0, 1.0, 1.0)
    data["font_scale"] = clamp_float(data.get("font_scale"), 0.8, 2.0, 1.0)
    data["music_volume"] = clamp_float(data.get("music_volume"), 0.0, 1.0, DEFAULT_PLAYER_SETTINGS["music_volume"])
    data["sfx_volume"] = clamp_float(data.get("sfx_volume"), 0.0, 1.0, DEFAULT_PLAYER_SETTINGS["sfx_volume"])
    data["home_music_id"] = normalize_home_music_id(data.get("home_music_id"))
    data["sfx_choices"] = normalize_sfx_choices(data.get("sfx_choices"))
    data["window_width"] = clamp_int(data.get("window_width"), 936, 2560, DEFAULT_PLAYER_SETTINGS["window_width"])
    data["window_height"] = clamp_int(data.get("window_height"), 598, 1600, DEFAULT_PLAYER_SETTINGS["window_height"])
    tutorial_completed = data.get("tutorial_completed", DEFAULT_PLAYER_SETTINGS["tutorial_completed"])
    if isinstance(tutorial_completed, str):
        tutorial_completed = tutorial_completed.strip().lower() not in {"0", "false", "no", "off", "否", "未完成"}
    else:
        tutorial_completed = bool(tutorial_completed)
    data["tutorial_completed"] = tutorial_completed
    admin_reveal_hidden = data.get("admin_reveal_hidden", DEFAULT_PLAYER_SETTINGS["admin_reveal_hidden"])
    if isinstance(admin_reveal_hidden, str):
        admin_reveal_hidden = admin_reveal_hidden.strip().lower() in {"1", "true", "yes", "on", "是", "开启"}
    else:
        admin_reveal_hidden = bool(admin_reveal_hidden)
    data["admin_reveal_hidden"] = admin_reveal_hidden
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
