DEFAULT_HOME_MUSIC_ID = "plains_luminescence"


HOME_MUSIC_OPTIONS = [
    {
        "id": "plains_luminescence",
        "track": "home",
        "title": "Plains of Luminescence",
        "author": "vitalezzz",
        "unlock_rating": 0.0,
        "source_url": "https://opengameart.org/content/plains-of-luminescence",
    },
    {
        "id": "four_loop",
        "track": "menu",
        "title": "Four",
        "author": "pauliuw",
        "unlock_rating": 3.0,
        "source_url": "https://opengameart.org/content/music-loops",
    },
    {
        "id": "menu_loop",
        "track": "home_menu_loop",
        "title": "Menu Loop",
        "author": "Akikazer",
        "unlock_rating": 5.0,
        "source_url": "https://opengameart.org/content/menu-loop",
    },
    {
        "id": "once_upon_a_time",
        "track": "home_once_upon_time",
        "title": "Once Upon a Time (loop)",
        "author": "TAD",
        "unlock_rating": 8.0,
        "source_url": "https://opengameart.org/content/once-upon-a-time-loop",
    },
    {
        "id": "pointless_loop",
        "track": "home_pointless_loop",
        "title": "Pointless loop",
        "author": "iamoneabe",
        "unlock_rating": 10.0,
        "source_url": "https://opengameart.org/content/pointless-loop",
    },
    {
        "id": "tempo",
        "track": "crossword",
        "title": "Tempo",
        "author": "pauliuw",
        "unlock_rating": 12.0,
        "source_url": "https://opengameart.org/content/music-loops",
    },
    {
        "id": "background_music_loop",
        "track": "home_background_loop",
        "title": "Background Music (LOOP)",
        "author": "Pro Sensory / Alex McCulloch",
        "unlock_rating": 14.0,
        "source_url": "https://opengameart.org/content/background-music-loop",
    },
    {
        "id": "dumus",
        "track": "archive",
        "title": "Dumus",
        "author": "pauliuw",
        "unlock_rating": 16.0,
        "source_url": "https://opengameart.org/content/music-loops",
    },
    {
        "id": "boss_battle",
        "track": "rank_16_20",
        "title": "Boss Battle Loop",
        "author": "Pro Sensory / Alex McCulloch",
        "unlock_rating": 18.0,
        "source_url": "https://opengameart.org/content/boss-battle-loop",
    },
]

_HOME_MUSIC_BY_ID = {option["id"]: option for option in HOME_MUSIC_OPTIONS}


def all_home_music_options():
    return [dict(option) for option in HOME_MUSIC_OPTIONS]


def normalize_home_music_id(music_id):
    text = str(music_id or "").strip()
    return text if text in _HOME_MUSIC_BY_ID else DEFAULT_HOME_MUSIC_ID


def unlocked_home_music_options(rating, reveal_all=False):
    if reveal_all:
        return all_home_music_options()
    try:
        value = float(rating)
    except (TypeError, ValueError):
        value = 0.0
    return [
        dict(option)
        for option in HOME_MUSIC_OPTIONS
        if value + 1e-9 >= float(option.get("unlock_rating") or 0.0)
    ]


def unlocked_home_music_ids(rating, reveal_all=False):
    return {option["id"] for option in unlocked_home_music_options(rating, reveal_all=reveal_all)}


def coerce_home_music_id(music_id, rating=0.0, reveal_all=False):
    music_id = normalize_home_music_id(music_id)
    if music_id in unlocked_home_music_ids(rating, reveal_all=reveal_all):
        return music_id
    return DEFAULT_HOME_MUSIC_ID


def home_music_option(music_id):
    return dict(_HOME_MUSIC_BY_ID.get(normalize_home_music_id(music_id), _HOME_MUSIC_BY_ID[DEFAULT_HOME_MUSIC_ID]))


def home_music_track(music_id):
    return home_music_option(music_id)["track"]


def home_music_label(music_id):
    option = home_music_option(music_id)
    return f"{option['title']} / {option['author']}"
