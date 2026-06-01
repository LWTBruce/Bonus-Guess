from .game_config import ACHIEVEMENT_CATEGORIES
from .rank_system import (
    parse_rank_badge_id,
    rank_badge_name,
    rank_badge_short_label,
    rank_kind_label,
    rank_title_rewards,
    split_rank_progress_key,
    subject_label,
)


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
    ("first_free_success", "ach_free_first", "自由落体员"),
    ("first_out_of_scope", "ach_out_of_scope", "超纲边境巡逻员"),
    ("no_hint_success", "ach_no_hint", "裸答主义者"),
    ("slow_success", "ach_slow_success", "长考型选手"),
    ("difficulty_ten_success", "ach_difficulty_ten", "十级概念搬运工"),
    ("difficulty_eleven_success", "ach_difficulty_eleven", "十一维访客"),
    ("difficulty_twelve_success", "ach_difficulty_twelve", "十二级边界客"),
    ("difficulty_thirteen_success", "ach_difficulty_thirteen", "十三级禁区来客"),
    ("streak_ten", "ach_streak_ten", "连续性很好"),
    ("masked_success_50", "ach_masked_50", "星号翻译官"),
    ("timed_success_100", "ach_timed_100", "五分钟生产队"),
    ("clue_success_100", "ach_clue_100", "线索编织者"),
    ("first_random_success", "ach_random_first", "随机游走者"),
    ("true_random_success", "ach_true_random", "全库漫游者"),
    ("first_greek_success", "ach_greek_first", "希腊字母观察员"),
    ("greek_success_10", "ach_greek_10", "Σ巡游者"),
    ("first_crossword_success", "ach_crossword_first", "格线观测者"),
    ("crossword_no_hint_success", "ach_crossword_no_hint", "空格独行者"),
    ("total_score_100000", "ach_score_100000", "积分矿脉持有人"),
    ("play_time_30h", "ach_time_30h", "三十小时常驻民"),
    ("first_rank_pass", "ach_rank_first", "段位挑战者"),
    ("first_free_rank_pass", "ach_free_rank_first", "限时段位挑战者"),
    ("first_timed_rank_pass", "ach_timed_rank_first", "旧限时段位挑战者"),
    ("first_clue_rank_pass", "ach_clue_rank_first", "线索段位挑战者"),
    ("first_crossword_rank_pass", "ach_crossword_rank_first", "字谜段位挑战者"),
    ("crossword_triangle_success", "ach_crossword_triangle", "三角密铺者"),
    ("crossword_hex_success", "ach_crossword_hex", "六边星图师"),
    ("rank_class_10_pass", "ach_rank_class_10", "十阶登临者"),
    ("rank_class_15_pass", "ach_rank_class_15", "十五阶登临者"),
    ("rank_cheat", "ach_rank_echo", "段位考场的回声"),
    ("one_char_term", "ach_one_char", "单字宇宙居民"),
    ("crossword_cheat", "ach_crossword_echo", "格线外的回声"),
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


def achievement_title_source_label(achievement_id):
    for category, ids in ACHIEVEMENT_CATEGORIES:
        if achievement_id in ids:
            return category
    return "成就"


def rank_title_source_label(title_reward_id):
    text = str(title_reward_id or "")
    if text.startswith("rank_title:"):
        text = text.split(":", 1)[1]
    subject_key, _rank_id = parse_rank_badge_id(text)
    if not subject_key:
        return "段位"
    return f"{rank_badge_short_label(text)}段位"


def unlocked_title_options(rating, achievements_data, rank_progress=None):
    options = [(reward_id, name, f"Rating {threshold:g}") for threshold, reward_id, name, _avatar_id in unlocked_rating_rewards(rating)]
    options.extend((reward_id, name, achievement_title_source_label(achievement_id)) for achievement_id, reward_id, name in unlocked_achievement_titles(achievements_data))
    options.extend((reward_id, name, rank_title_source_label(reward_id)) for reward_id, name in rank_title_rewards(rank_progress))
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
