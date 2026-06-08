SFX_EVENT_OPTIONS = [
    ("click", "普通点击"),
    ("confirm", "确认/开始/保存"),
    ("back", "返回/取消/关闭"),
    ("hint", "提示/词库"),
    ("warning", "警告/删除/揭晓"),
    ("success", "成功反馈"),
    ("fail", "失败反馈"),
    ("popup", "弹窗提示"),
]

SFX_SOUND_OPTIONS = [
    ("click", "轻触"),
    ("confirm", "确认铃"),
    ("back", "回退"),
    ("hint", "提示音"),
    ("warning", "警告"),
    ("success", "成功"),
    ("fail", "失败"),
    ("popup", "弹窗"),
]

SFX_EVENT_IDS = {event_id for event_id, _label in SFX_EVENT_OPTIONS}
SFX_SOUND_IDS = {sound_id for sound_id, _label in SFX_SOUND_OPTIONS}
DEFAULT_SFX_CHOICES = {event_id: event_id for event_id, _label in SFX_EVENT_OPTIONS}


def normalize_sfx_choices(choices):
    result = dict(DEFAULT_SFX_CHOICES)
    if not isinstance(choices, dict):
        return result
    for event_id, sound_id in choices.items():
        event_id = str(event_id or "").strip()
        sound_id = str(sound_id or "").strip()
        if event_id in SFX_EVENT_IDS and sound_id in SFX_SOUND_IDS:
            result[event_id] = sound_id
    return result


def sfx_event_label(event_id):
    for item_id, label in SFX_EVENT_OPTIONS:
        if item_id == event_id:
            return label
    return str(event_id or "音效")


def sfx_sound_label(sound_id):
    for item_id, label in SFX_SOUND_OPTIONS:
        if item_id == sound_id:
            return label
    return sfx_sound_label(DEFAULT_SFX_CHOICES["click"])


def sfx_sound_display(sound_id):
    sound_id = str(sound_id or "").strip()
    if sound_id not in SFX_SOUND_IDS:
        sound_id = DEFAULT_SFX_CHOICES["click"]
    return f"{sfx_sound_label(sound_id)} ({sound_id})"


def sfx_sound_display_options():
    return [sfx_sound_display(sound_id) for sound_id, _label in SFX_SOUND_OPTIONS]


def sfx_sound_id_from_display(display_text):
    text = str(display_text or "").strip()
    for sound_id, _label in SFX_SOUND_OPTIONS:
        if text == sfx_sound_display(sound_id) or text == sound_id:
            return sound_id
    return DEFAULT_SFX_CHOICES["click"]
