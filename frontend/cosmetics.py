from rank_system import rank_badge_name, rank_title_rewards


RATING_REWARDS = [
    (0.0, "rating_0", "初入题场", 0),
    (5.0, "rating_5", "公式拾荒者", 1),
    (8.0, "rating_8", "符号巡航员", 2),
    (10.0, "rating_10", "题面破译员", 3),
    (12.0, "rating_12", "概念猎手", 4),
    (14.0, "rating_14", "相空间旅人", 5),
    (15.0, "rating_15", "边界条件师", 6),
    (16.0, "rating_16", "谱线调音师", 7),
    (17.0, "rating_17", "场方程行者", 8),
    (17.5, "rating_17_5", "临界点守望者", 9),
    (18.0, "rating_18", "正则变换家", 10),
    (18.5, "rating_18_5", "希尔伯特漫游者", 11),
    (19.0, "rating_19", "重整化旅客", 12),
    (19.5, "rating_19_5", "光锥外侧的人", 13),
    (20.0, "rating_20", "无奖竞猜之王", 14),
]

ACHIEVEMENT_TITLE_REWARDS = [
    ("first_success", "ach_first_success", "首战观测者"),
    ("first_out_of_scope", "ach_out_of_scope", "超纲边境巡逻员"),
    ("no_hint_success", "ach_no_hint", "裸答主义者"),
    ("slow_success", "ach_slow_success", "长考型选手"),
    ("difficulty_ten_success", "ach_difficulty_ten", "十级概念搬运工"),
    ("effective_over_11_success", "ach_effective_over_11", "十一维访客"),
    ("streak_ten", "ach_streak_ten", "连续性很好"),
    ("masked_success_50", "ach_masked_50", "星号翻译官"),
    ("timed_success_100", "ach_timed_100", "五分钟生产队"),
    ("total_score_100000", "ach_score_100000", "积分矿脉持有人"),
    ("play_time_30h", "ach_time_30h", "三十小时常驻民"),
    ("backdrop_overdrive", "ach_backdrop", "背景风暴驾驶员"),
]


def title_name(title_id):
    if str(title_id or "").startswith("rank_title:"):
        return rank_badge_name(str(title_id).split(":", 1)[1])
    for _threshold, reward_id, name, _avatar_id in RATING_REWARDS:
        if reward_id == title_id:
            return name
    for _achievement_id, reward_id, name in ACHIEVEMENT_TITLE_REWARDS:
        if reward_id == title_id:
            return name
    return RATING_REWARDS[0][2]


def unlocked_rating_rewards(rating):
    try:
        value = float(rating)
    except (TypeError, ValueError):
        value = 0.0
    return [reward for reward in RATING_REWARDS if value + 1e-9 >= reward[0]]


def completed_achievement_ids(achievements_data):
    if not isinstance(achievements_data, dict):
        return set()
    completed = achievements_data.get("completed") or {}
    if isinstance(completed, dict):
        return {str(key) for key, value in completed.items() if value}
    return set()


def unlocked_achievement_titles(achievements_data):
    completed = completed_achievement_ids(achievements_data)
    return [reward for reward in ACHIEVEMENT_TITLE_REWARDS if reward[0] in completed]


def unlocked_title_options(rating, achievements_data, rank_progress=None):
    options = [(reward_id, name, f"Rating {threshold:g}") for threshold, reward_id, name, _avatar_id in unlocked_rating_rewards(rating)]
    options.extend((reward_id, name, "成就") for _achievement_id, reward_id, name in unlocked_achievement_titles(achievements_data))
    options.extend((reward_id, name, "段位") for reward_id, name in rank_title_rewards(rank_progress))
    seen = set()
    unique = []
    for option in options:
        if option[0] in seen:
            continue
        seen.add(option[0])
        unique.append(option)
    return unique


def unlocked_avatar_ids(rating):
    return {avatar_id for _threshold, _reward_id, _name, avatar_id in unlocked_rating_rewards(rating)}


def coerce_title_id(title_id, rating, achievements_data, rank_progress=None):
    unlocked = {option[0] for option in unlocked_title_options(rating, achievements_data, rank_progress)}
    if title_id in unlocked:
        return title_id
    return RATING_REWARDS[0][1]


def coerce_avatar_id(avatar_id, rating):
    unlocked = unlocked_avatar_ids(rating)
    try:
        value = int(avatar_id)
    except (TypeError, ValueError):
        value = RATING_REWARDS[0][3]
    if value in unlocked:
        return value
    return RATING_REWARDS[0][3]
