import os
import sys
from pathlib import Path


LOCAL_TCL_DIR = Path(__file__).resolve().parent / "tcl"
if LOCAL_TCL_DIR.exists():
    os.environ.setdefault("TCL_LIBRARY", str(LOCAL_TCL_DIR / "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", str(LOCAL_TCL_DIR / "tk8.6"))


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_dir()
if getattr(sys, "frozen", False):
    PROJECT_DIR = APP_DIR
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
    RESOURCE_DIR = PROJECT_DIR
RECORD_DIR = PROJECT_DIR / "record"
ACHIEVEMENTS_FILE = RECORD_DIR / "achievements.json"
RANK_PROGRESS_FILE = RECORD_DIR / "rank_progress.json"
GAME_MECHANICS_FILE = RESOURCE_DIR / "docs" / "game_mechanics.md"
TERM_CLUES_DIR = RESOURCE_DIR / "clues"
TERM_CLUES_FILE = TERM_CLUES_DIR / "term_clues.json"
WORDS_DIR = RESOURCE_DIR / "words"
PROFILE_DIR = PROJECT_DIR / "profile"
PLAYER_SETTINGS_FILE = PROFILE_DIR / "player_settings.json"
DAILY_TERMS_FILE = PROFILE_DIR / "daily_terms.json"

APP_VERSION = "0.1.22"
TITLE_CN = "有（×）无奖竞猜"
TITLE_EN = "Bonus-（×）Guess"


ACHIEVEMENTS = [
    ("first_launch", "开幕雷击", "第一次启动游戏"),
    ("entered_game", "我只是看看", "第一次进入任意一局游戏"),
    ("first_success", "首战告捷", "第一次答对题目"),
    ("three_hints_one_round", "真的想不出来！", "在同一道题中使用三个提示"),
    ("first_out_of_scope", "老师，这题超纲吗", "第一次触发“超纲啦，再想想~”"),
    ("negative_score", "溢出？", "在一道题中获得负分"),
    ("fifty_char_hints", "我与提示共存亡", "累计使用字词或线索提示 50 次"),
    ("twenty_library_hints", "问问词库怎么了", "累计使用“提示词库”20 次"),
    ("no_hint_success", "省流大师", "不使用任何提示答对一题"),
    ("quick_success", "闪电战", "10 秒内答对一题"),
    ("slow_success", "沉思者", "单题用时超过 180 秒并最终答对"),
    ("hard_success", "硬骨头也会开花", "答对一个难度 8 及以上的词"),
    ("difficulty_ten_success", "十级词汇受害者", "答对一个难度 10 的词"),
    ("effective_over_10_success", "十级以上禁止通行", "答对一道总难度大于 10 的题"),
    ("effective_over_11_success", "十一维入口", "答对一道总难度大于 11 的题"),
    ("streak_five", "稳定发挥", "连续答对 5 题"),
    ("streak_ten", "这不是肌肉记忆吗", "连续答对 10 题"),
    ("score_guard", "分数守门员", "单题得分达到 900 分以上"),
    ("total_score_5000", "高分低调路过", "累计总积分达到 5000 分"),
    ("total_score_20000", "积分银行开张", "累计总积分达到 20000 分"),
    ("completed_50", "题海浮沉", "累计完成 50 道题"),
    ("completed_200", "知识点清仓中", "累计完成 200 道题"),
    ("exit_ten", "战略性转进", "累计中途退出 10 次"),
    ("play_time_10h", "上班打卡", "累计游戏用时 10 小时"),
    ("play_time_30h", "这已经是副业了", "累计游戏用时 30 小时"),
    ("play_time_100h", "时间都去哪儿了", "累计游戏用时 100 小时"),
    ("completed_500", "做题如呼吸", "累计完成 500 道题"),
    ("completed_1000", "题库搬运工", "累计完成 1000 道题"),
    ("success_500", "稳定输出机器", "累计答对 500 道题"),
    ("total_score_100000", "知识矿工", "累计总积分达到 100000 分"),
    ("total_score_500000", "积分通胀时代", "累计总积分达到 500000 分"),
    ("five_hundred_char_hints", "提示学派宗师", "累计使用字词或线索提示 500 次"),
    ("two_hundred_library_hints", "词库导游", "累计使用“提示词库”200 次"),
    ("hard_success_100", "硬题啃咬机", "累计答对 100 个难度 8 及以上的词"),
    ("difficulty_ten_success_30", "十级风暴眼", "累计答对 30 个难度 10 的词"),
    ("effective_over_10_success_20", "十级以上常客", "累计答对 20 道总难度大于 10 的题"),
    ("effective_over_11_success_5", "十一楼住户", "累计答对 5 道总难度大于 11 的题"),
    ("exit_hundred", "暂时撤退也是前进", "累计中途退出 100 次"),
    ("first_masked_round", "星号来客", "第一次遇到带掩码的首字母题"),
    ("first_masked_success", "星号破译员", "第一次答对带掩码的题"),
    ("three_mask_success", "三颗星也照样认", "答对一道被掩码 3 个字符的题"),
    ("masked_success_50", "星号清扫工", "累计答对 50 道带掩码的题"),
    ("masked_success_300", "掩码考古队", "累计答对 300 道带掩码的题"),
    ("first_timed_success", "五分钟热度", "第一次在限时模式中答对题目"),
    ("timed_success_20", "倒计时小冲刺", "限时模式累计答对 20 题"),
    ("timed_success_100", "计时器熟人", "限时模式累计答对 100 题"),
    ("timed_success_500", "五分钟流水线", "限时模式累计答对 500 题"),
    ("timed_time_5h", "倒计时常住民", "限时模式累计用时 5 小时"),
    ("timed_time_30h", "秒针合伙人", "限时模式累计用时 30 小时"),
    ("first_initial_block", "手离键盘！", "第一次输入题面首字母并触发拦截警告"),
    ("first_cheat", "二次作案", "同一题第二次输入题面首字母，被判作弊"),
    ("cheat_three", "输入法背锅三连", "累计触发 3 次题面首字母作弊判定"),
    ("cheat_ten", "候选框老熟人", "累计触发 10 次题面首字母作弊判定"),
    ("timed_cheat", "倒计时也敢？", "在限时模式中触发题面首字母作弊判定"),
    ("backdrop_overdrive", "显卡说它想静静", "将背景速度和背景密度同时调到 10 倍"),
]

HIDDEN_ACHIEVEMENT_IDS = {
    "negative_score",
    "three_hints_one_round",
    "slow_success",
    "exit_ten",
    "three_mask_success",
    "first_initial_block",
    "first_cheat",
    "cheat_three",
    "cheat_ten",
    "timed_cheat",
    "backdrop_overdrive",
}

ACHIEVEMENT_CATEGORIES = [
    (
        "通用入门",
        [
            "first_launch",
            "entered_game",
            "first_success",
            "no_hint_success",
            "quick_success",
            "score_guard",
        ],
    ),
    (
        "自由与常规",
        [
            "first_out_of_scope",
            "hard_success",
            "difficulty_ten_success",
            "streak_five",
            "streak_ten",
        ],
    ),
    (
        "线索与高难",
        [
            "effective_over_10_success",
            "effective_over_11_success",
            "effective_over_10_success_20",
            "effective_over_11_success_5",
        ],
    ),
    (
        "提示与词库",
        [
            "twenty_library_hints",
            "fifty_char_hints",
            "two_hundred_library_hints",
            "five_hundred_char_hints",
        ],
    ),
    (
        "掩码首字母",
        [
            "first_masked_round",
            "first_masked_success",
            "masked_success_50",
            "masked_success_300",
        ],
    ),
    (
        "限时模式",
        [
            "first_timed_success",
            "timed_success_20",
            "timed_success_100",
            "timed_time_5h",
            "timed_success_500",
            "timed_time_30h",
        ],
    ),
    (
        "长期积累",
        [
            "total_score_5000",
            "total_score_20000",
            "completed_50",
            "completed_200",
            "play_time_10h",
            "play_time_30h",
            "play_time_100h",
            "completed_500",
            "completed_1000",
            "success_500",
            "hard_success_100",
            "difficulty_ten_success_30",
            "total_score_100000",
            "total_score_500000",
        ],
    ),
    (
        "系统与退出",
        [
            "exit_hundred",
        ],
    ),
]

TERM_DIFFICULTY_WEIGHTS = {
    "入门": {1: 34, 2: 36, 3: 18, 4: 7, 5: 3, 6: 1, 7: 0.6, 8: 0.3, 9: 0.1, 10: 0.05},
    "简单": {1: 5, 2: 12, 3: 30, 4: 30, 5: 13, 6: 6, 7: 2.5, 8: 1, 9: 0.4, 10: 0.1},
    "普通": {1: 1, 2: 2.5, 3: 7, 4: 14, 5: 28, 6: 27, 7: 13, 8: 5.5, 9: 1.5, 10: 0.5},
    "困难": {1: 0.2, 2: 0.5, 3: 1, 4: 2.5, 5: 5, 6: 9, 7: 16, 8: 27, 9: 23, 10: 15.8},
    "混合模式": {difficulty: 1 for difficulty in range(1, 11)},
}

FREE_HINT_DECAY = {
    "入门": 0.78,
    "简单": 0.55,
    "普通": 0.38,
    "困难": 0.25,
    "混合模式": 0.45,
}

FREE_HINT_ZERO_PROB = {
    "入门": 0.50,
    "简单": 0.55,
    "普通": 0.60,
    "困难": 0.65,
    "混合模式": 0.60,
}

HINT_COOLDOWN_SECONDS = {
    "入门": 30,
    "简单": 45,
    "普通": 60,
    "困难": 75,
    "混合模式": 60,
}

MASK_PROBABILITIES = {
    "普通": {
        4: {1: 0.30},
        5: {1: 0.20, 2: 0.10},
        6: {1: 0.15, 2: 0.10, 3: 0.05},
    },
    "困难": {
        4: {1: 0.45},
        5: {1: 0.30, 2: 0.20},
        6: {1: 0.25, 2: 0.20, 3: 0.15},
    },
}

SCORE_MODE_WEIGHTS = {
    "入门": 0.1,
    "简单": 0.2,
    "普通": 0.3,
    "困难": 0.4,
    "混合模式": 0.25,
    "真·随机": 0.25,
}
