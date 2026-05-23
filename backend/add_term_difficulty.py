import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORDS_DIR = ROOT / "words"
HEADER = [
    "编号",
    "概念中文名",
    "难度",
    "中文首字母",
    "中文首字母串长度",
    "概念英文名",
    "英文字符串长度",
    "概念中文拼音",
    "拼音字符串长度",
]

VALID_DIFFICULTIES = {str(value) for value in range(1, 11)}

DIFFICULTY_OVERRIDES = {
    "力": 1,
    "功": 1,
    "热": 1,
    "光": 1,
    "波": 1,
    "速度": 1,
    "质量": 1,
    "温度": 1,
    "电荷": 1,
    "电流": 1,
    "矩阵": 1,
    "向量": 1,
    "导数": 1,
    "积分": 1,
    "角动量": 3,
    "波函数": 4,
    "光子": 3,
    "黑洞": 4,
    "熵": 3,
    "势阱": 4,
    "微扰论": 5,
    "方势阱": 5,
    "无限深势阱": 6,
    "有限深势阱": 6,
    "纯滚动": 6,
    "斜面": 6,
    "滑轮": 6,
    "杠杆": 6,
    "表面张力": 7,
    "体积模量": 8,
    "支点": 8,
    "力偶矩": 8,
    "玻尔原子模型": 6,
    "玻尔假设": 6,
    "主辐角": 8,
    "范数映射": 8,
    "正规化子": 8,
    "乌雷松引理": 10,
}

CORE_WORDS = {
    "位移", "路程", "运动", "速度", "速率", "加速度", "力", "质量", "重力", "摩擦力", "动量", "冲量",
    "功", "功率", "动能", "势能", "机械能", "力矩", "角动量", "转动", "振动", "波", "周期", "频率",
    "电荷", "电场", "磁场", "电流", "电压", "电阻", "电容", "电感", "电磁波", "温度", "热量", "内能",
    "熵", "光", "反射", "折射", "干涉", "衍射", "偏振", "光谱", "原子", "电子", "质子", "中子",
    "波函数", "算符", "本征值", "本征态", "自旋", "势阱", "势垒", "散射", "微扰论", "变分法",
    "极限", "连续", "导数", "微分", "积分", "级数", "梯度", "散度", "旋度", "矩阵", "行列式",
    "向量", "基", "维数", "特征值", "特征向量", "概率", "样本", "总体", "群", "子群", "域", "扩域",
}

EDGE_WORDS = {
    "体积模量", "剪切模量", "支点", "力偶", "力偶矩", "纯滚动", "章动", "进动", "势垒", "跃迁",
    "拉格朗日括号", "作用角变量", "法捷耶夫波波夫鬼场", "BRST对称性", "θ真空", "阿廷施赖尔扩张",
    "正规化子", "中心化子", "乌雷松引理", "蒂茨扩张定理", "米塔列夫勒定理", "魏尔斯特拉斯乘积定理",
}

CONCRETE_BUT_NOT_CORE = (
    "滑轮", "杠杆", "支点", "斜面", "轮轴", "滑块", "小球", "弹簧秤", "摆球", "砝码",
    "容器", "活塞", "薄膜", "狭缝", "透镜组", "光屏", "游标", "支架",
)

ABSTRACT_MARKERS = (
    "张量", "算符", "泛函", "规范", "协变", "联络", "曲率", "同调", "上同调", "伽罗瓦",
    "正规", "可分", "不可约", "表示", "重整化", "反常", "超精细", "四极", "多极",
)

NAMED_MARKERS = (
    "定理", "定律", "方程", "公式", "原理", "模型", "效应", "分布", "变换", "判据", "条件",
)


def clamp(value):
    return max(1, min(10, int(value)))


def base_from_path(path):
    parts = path.parts
    joined = "\\".join(parts)
    if "入门模式" in joined:
        return 2
    if "简单模式" in joined:
        return 4
    if "普通模式" in joined:
        return 6
    if "困难模式" in joined:
        return 8
    return 6


def estimate_difficulty(chinese, english, path):
    if chinese in DIFFICULTY_OVERRIDES:
        return DIFFICULTY_OVERRIDES[chinese]

    score = base_from_path(path)
    length = len(chinese)
    joined_path = "\\".join(path.parts)

    if chinese in CORE_WORDS:
        score -= 2 if "简单模式" in joined_path else 1
    if chinese in EDGE_WORDS:
        score += 2

    if length <= 2 and chinese in CORE_WORDS:
        score -= 1
    elif length >= 7:
        score += 2
    elif length >= 5:
        score += 1
    elif length == 4 and any(marker in chinese for marker in ABSTRACT_MARKERS):
        score += 1

    if any(marker in chinese for marker in CONCRETE_BUT_NOT_CORE) and chinese not in CORE_WORDS:
        score += 2
    if any(marker in chinese for marker in ABSTRACT_MARKERS):
        score += 1
    if any(marker in chinese for marker in NAMED_MARKERS) and chinese not in CORE_WORDS:
        score += 1

    if any(name in chinese for name in ("阿廷", "乌雷松", "蒂茨", "米塔", "魏尔斯特拉斯", "法捷耶夫", "彭罗斯")):
        score = 10
    if any(name in chinese for name in ("玻尔兹曼", "斯特藩", "康普顿", "德布罗意", "洛伦兹", "哈密顿", "拉格朗日")):
        score += 1
    if "量子" in chinese and "简单模式" in joined_path:
        score += 1
    if english in {"eigenvalue", "matrix", "vector", "probability", "entropy", "photon"}:
        score = min(score, 4)
    if "入门模式" in joined_path:
        score = min(score, 3)

    return clamp(score)


def parse_row(row):
    if len(row) >= 9:
        return {
            "cn": row[1].strip(),
            "difficulty": row[2].strip(),
            "initials": row[3].strip(),
            "english": row[5].strip(),
            "pinyin": row[7].strip(),
        }
    if len(row) >= 8:
        return {
            "cn": row[1].strip(),
            "difficulty": "",
            "initials": row[2].strip(),
            "english": row[4].strip(),
            "pinyin": row[6].strip(),
        }
    return None


def update_file(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    data = []
    seen = set()
    for raw in rows[1:]:
        parsed = parse_row(raw)
        if not parsed or not parsed["cn"] or not parsed["initials"] or not parsed["english"] or not parsed["pinyin"]:
            continue
        key = (parsed["cn"], parsed["english"])
        if key in seen:
            continue
        seen.add(key)
        difficulty = estimate_difficulty(parsed["cn"], parsed["english"], path)
        data.append((parsed["cn"], difficulty, parsed["initials"], parsed["english"], parsed["pinyin"]))

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        for index, (cn, difficulty, initials, english, pinyin) in enumerate(data, 1):
            writer.writerow([
                index,
                cn,
                difficulty,
                initials,
                len(initials),
                english,
                len(english),
                pinyin,
                len(pinyin),
            ])
    return len(data)


def main():
    for path in sorted(WORDS_DIR.glob("**/*.csv")):
        count = update_file(path)
        print(f"{path.relative_to(ROOT)}: {count}")


if __name__ == "__main__":
    main()
