import os
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

LOCAL_TCL_DIR = FRONTEND_DIR / "tcl"
if LOCAL_TCL_DIR.exists():
    os.environ.setdefault("TCL_LIBRARY", str(LOCAL_TCL_DIR / "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", str(LOCAL_TCL_DIR / "tk8.6"))


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return FRONTEND_DIR


APP_DIR = app_dir()
if getattr(sys, "frozen", False):
    PROJECT_DIR = APP_DIR
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    PROJECT_DIR = PROJECT_ROOT
    RESOURCE_DIR = PROJECT_DIR
RECORD_DIR = PROJECT_DIR / "record"
ACHIEVEMENTS_FILE = RECORD_DIR / "achievements.json"
RANK_PROGRESS_FILE = RECORD_DIR / "rank_progress.json"
GAME_MECHANICS_FILE = RESOURCE_DIR / "docs" / "game_mechanics.md"
TERM_CLUES_DIR = RESOURCE_DIR / "clues"
TERM_CLUES_FILE = TERM_CLUES_DIR / "term_clues.json"
WORDS_DIR = RESOURCE_DIR / "words"
ASSETS_DIR = (RESOURCE_DIR / "assets") if getattr(sys, "frozen", False) else (APP_DIR / "assets")
APP_ICON_FILE = ASSETS_DIR / "bonus_guess.ico"
PROFILE_DIR = PROJECT_DIR / "profile"
PLAYER_SETTINGS_FILE = PROFILE_DIR / "player_settings.json"
DAILY_TERMS_FILE = PROFILE_DIR / "daily_terms.json"

APP_VERSION = "0.3.24"
TITLE_CN = "有（×）无奖竞猜"
TITLE_EN = "Bonus-（×）Guess"


ACHIEVEMENTS = [
    ("first_launch", "开幕雷击", "第一次启动游戏"),
    ("entered_game", "我只是看看", "第一次进入任意一局游戏"),
    ("first_success", "首战告捷", "第一次答对题目"),
    ("first_free_success", "自由落体第一跳", "第一次在自由模式中答对题目"),
    ("three_hints_one_round", "真的想不出来！", "在同一道题中使用三个提示"),
    ("first_out_of_scope", "老师，这题超纲吗", "第一次触发“超纲啦，再想想~”"),
    ("negative_score", "溢出？", "在一道题中获得负分"),
    ("fifty_char_hints", "我与提示共存亡", "累计使用字词或线索提示 50 次"),
    ("twenty_library_hints", "问问词库怎么了", "累计使用“提示词库”20 次"),
    ("no_hint_success", "省流大师", "不使用任何提示答对一题"),
    ("quick_success", "闪电战", "10 秒内答对一题"),
    ("slow_success", "沉思者", "单题用时超过 180 秒并最终答对"),
    ("hard_success", "硬骨头也会开花", "答对一个难度 8 及以上的词"),
    ("difficulty_ten_success", "十级词汇受害者", "答对一道单题总难度达到 10 级的题"),
    ("difficulty_eleven_success", "十一维入口", "答对一道单题总难度达到 11 级的题"),
    ("difficulty_twelve_success", "十二级边界", "答对一道单题总难度达到 12 级的题"),
    ("difficulty_thirteen_success", "十三级禁区", "答对一道单题总难度达到 13 级的题"),
    ("effective_over_10_success", "十级以上常客", "答对一道总难度大于 10 的题"),
    ("effective_over_11_success", "十一楼住户", "答对一道总难度大于 11 的题"),
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
    ("first_clue_success", "线索刚刚够用", "第一次在线索模式中答对题目"),
    ("clue_no_hint_success", "只看一行也行", "只看初始线索答对一题"),
    ("clue_success_20", "线索串联员", "线索模式累计答对 20 题"),
    ("clue_success_100", "描述场论家", "线索模式累计答对 100 题"),
    ("first_random_success", "跨学科第一跃迁", "第一次在随机模式中答对题目"),
    ("random_success_20", "随机游走稳定了", "随机模式累计答对 20 题"),
    ("true_random_success", "全库相遇事件", "第一次在真·随机中答对题目"),
    ("first_greek_term", "希腊字母来敲门", "第一次遇见中文名中含有希腊字母的词"),
    ("first_greek_success", "Σ 不是 S", "第一次答对含有希腊字母的词"),
    ("greek_success_10", "希腊字母巡礼", "累计答对 10 个含有希腊字母的词"),
    ("crossword_greek_term", "格线里的希腊星座", "在字谜模式中遇见含有希腊字母的词"),
    ("first_initial_block", "手离键盘！", "第一次触发题面首字母拦截彩蛋"),
    ("first_cheat", "二次作案", "同一题第二次触发题面首字母彩蛋"),
    ("cheat_three", "输入法背锅三连", "累计触发 3 次题面首字母彩蛋"),
    ("cheat_ten", "候选框老熟人", "累计触发 10 次题面首字母彩蛋"),
    ("timed_cheat", "倒计时也敢？", "在限时模式中触发题面首字母彩蛋"),
    ("first_rank_pass", "初段确认", "第一次通过正式段位挑战"),
    ("first_free_rank_pass", "限时段位起步", "第一次通过限时段位"),
    ("first_timed_rank_pass", "旧限时段位起步", "第一次通过旧限时段位"),
    ("first_clue_rank_pass", "线索段位起步", "第一次通过线索段位"),
    ("first_crossword_rank_pass", "字谜段位起步", "第一次通过字谜段位"),
    ("rank_class_5_pass", "五阶入场", "通过任意 Class 05 或以上段位"),
    ("rank_class_10_pass", "十阶登临", "通过任意 Class 10 或以上段位"),
    ("rank_class_15_pass", "十五阶登临", "通过任意 Class 15 段位"),
    ("rank_distinct_5", "段位收藏家", "累计解锁 5 个不同正式段位标识"),
    ("rank_distinct_15", "段位星图", "累计解锁 15 个不同正式段位标识"),
    ("rank_no_hint_pass", "冷却从未开始", "不使用提示通过一次正式段位"),
    ("rank_cheat", "段位考场的回声", "在段位挑战中触发隐藏彩蛋"),
    ("first_crossword_success", "纵横起笔", "第一次完成字谜模式"),
    ("crossword_words_50", "格线熟手", "在字谜模式中累计填对 50 个词"),
    ("crossword_crossings_10", "交点密度上升", "完成一局至少 10 个交叉的字谜"),
    ("crossword_no_hint_success", "空格不空", "不使用任何提示完成一局字谜"),
    ("crossword_triangle_success", "三角密铺者", "完成一次三角格字谜"),
    ("crossword_hex_success", "六边星图师", "完成一次六边格字谜"),
    ("one_char_term", "一个字也算词", "抽到一个字的词"),
    ("crossword_cheat", "格线外的回声", "在字谜模式中触发隐藏彩蛋"),
    ("backdrop_overdrive", "显卡说它想静静", "将背景速度和背景密度同时调到 10 倍"),
]

HIDDEN_ACHIEVEMENT_IDS = {
    "negative_score",
    "three_hints_one_round",
    "slow_success",
    "exit_ten",
    "three_mask_success",
    "first_initial_block",
    "first_greek_term",
    "first_greek_success",
    "greek_success_10",
    "crossword_greek_term",
    "first_cheat",
    "cheat_three",
    "cheat_ten",
    "timed_cheat",
    "rank_cheat",
    "one_char_term",
    "crossword_cheat",
    "backdrop_overdrive",
}

ACHIEVEMENT_CATEGORIES = [
    (
        "通用入门",
        [
            "first_launch",
            "entered_game",
            "first_success",
            "first_free_success",
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
            "difficulty_eleven_success",
            "difficulty_twelve_success",
            "difficulty_thirteen_success",
            "streak_five",
            "streak_ten",
        ],
    ),
    (
        "线索与高难",
        [
            "first_clue_success",
            "clue_no_hint_success",
            "clue_success_20",
            "clue_success_100",
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
        "随机模式",
        [
            "first_random_success",
            "random_success_20",
            "true_random_success",
        ],
    ),
    (
        "段位挑战",
        [
            "first_rank_pass",
            "first_free_rank_pass",
            "first_timed_rank_pass",
            "first_clue_rank_pass",
            "first_crossword_rank_pass",
            "rank_class_5_pass",
            "rank_class_10_pass",
            "rank_class_15_pass",
            "rank_no_hint_pass",
            "rank_distinct_5",
            "rank_distinct_15",
        ],
    ),
    (
        "字谜模式",
        [
            "first_crossword_success",
            "crossword_no_hint_success",
            "crossword_triangle_success",
            "crossword_hex_success",
            "crossword_crossings_10",
            "crossword_words_50",
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
    "入门": {1: 34, 2: 36, 3: 18, 4: 7, 5: 3, 6: 1, 7: 0.6, 8: 0.3, 9: 0.1, 10: 0.05, 11: 0.02, 12: 0.01},
    "简单": {1: 5, 2: 12, 3: 30, 4: 30, 5: 13, 6: 6, 7: 2.5, 8: 1, 9: 0.4, 10: 0.1, 11: 0.03, 12: 0.01},
    "普通": {1: 1, 2: 2.5, 3: 7, 4: 14, 5: 28, 6: 27, 7: 13, 8: 5.5, 9: 1.5, 10: 0.5, 11: 0.15, 12: 0.05},
    "困难": {1: 0.2, 2: 0.5, 3: 1, 4: 2.5, 5: 5, 6: 9, 7: 16, 8: 27, 9: 23, 10: 15.8, 11: 4.5, 12: 1.5},
    "噩梦": {1: 0.02, 2: 0.05, 3: 0.1, 4: 0.2, 5: 0.4, 6: 0.8, 7: 2, 8: 7, 9: 16, 10: 32, 11: 28, 12: 13.43},
    "混合模式": {difficulty: 1 for difficulty in range(1, 13)},
    "真·随机": {difficulty: 1 for difficulty in range(1, 13)},
}

FREE_HINT_DECAY = {
    "入门": 0.78,
    "简单": 0.55,
    "普通": 0.38,
    "困难": 0.25,
    "噩梦": 0.16,
    "混合模式": 0.45,
    "真·随机": 0.45,
}

FREE_HINT_ZERO_PROB = {
    "入门": 0.50,
    "简单": 0.55,
    "普通": 0.60,
    "困难": 0.65,
    "噩梦": 0.75,
    "混合模式": 0.60,
    "真·随机": 0.60,
}

HINT_COOLDOWN_SECONDS = {
    "入门": 30,
    "简单": 45,
    "普通": 60,
    "困难": 75,
    "噩梦": 90,
    "混合模式": 60,
    "真·随机": 60,
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
    "噩梦": {
        4: {1: 0.55, 2: 0.15},
        5: {1: 0.35, 2: 0.35, 3: 0.10},
        6: {1: 0.25, 2: 0.30, 3: 0.25, 4: 0.10},
    },
}

SCORE_MODE_WEIGHTS = {
    "入门": 0.1,
    "简单": 0.2,
    "普通": 0.3,
    "困难": 0.4,
    "噩梦": 0.6,
    "混合模式": 0.3,
    "真·随机": 0.3,
}
