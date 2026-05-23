import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS_DIR = ROOT / "words"
MATH_SIMPLE_DIR = WORDS_DIR / "数学" / "简单模式"
MATH_NORMAL_DIR = WORDS_DIR / "数学" / "普通模式"
MATH_HARD_DIR = WORDS_DIR / "数学" / "困难模式"

OUTPUT_DIRS = {
    "linear_algebra_terms.csv": MATH_SIMPLE_DIR,
    "complex_analysis_terms.csv": MATH_NORMAL_DIR,
    "mathematical_physics_equations_terms.csv": MATH_NORMAL_DIR,
    "probability_theory_terms.csv": MATH_NORMAL_DIR,
    "mathematical_statistics_terms.csv": MATH_NORMAL_DIR,
    "topology_terms.csv": MATH_HARD_DIR,
    "field_theory_terms.csv": MATH_HARD_DIR,
}

HEADER = [
    "编号",
    "概念中文名",
    "中文首字母",
    "中文首字母串长度",
    "概念英文名",
    "英文字符串长度",
    "概念中文拼音",
    "拼音字符串长度",
]


ADDITIONS = {
    "linear_algebra_terms.csv": """
列空间|column_space|lie kong jian
行空间|row_space|hang kong jian
零空间|null_space|ling kong jian
左零空间|left_null_space|zuo ling kong jian
基础解系|fundamental_solution_set|ji chu jie xi
自由变量|free_variable|zi you bian liang
主变量|pivot_variable|zhu bian liang
主元|pivot|zhu yuan
主元列|pivot_column|zhu yuan lie
列秩|column_rank|lie zhi
行秩|row_rank|hang zhi
""",
    "complex_analysis_terms.csv": """
解析曲线|analytic_curve|jie xi qu xian
闭路|closed_contour|bi lu
正向边界|positive_boundary|zheng xiang bian jie
围道|contour|wei dao
圆周积分|circle_integral|yuan zhou ji fen
小圆弧引理|small_arc_lemma|xiao yuan hu yin li
大圆弧引理|large_arc_lemma|da yuan hu yin li
留数求和|residue_summation|liu shu qiu he
有界整函数|bounded_entire_function|you jie zheng han shu
单叶函数|univalent_function|dan ye han shu
双全纯映射|biholomorphic_map|shuang quan chun ying she
黎曼映射定理|riemann_mapping_theorem|li man ying she ding li
解析开拓|analytic_extension|jie xi kai tuo
多值函数|multivalued_function|duo zhi han shu
根式函数|radical_function|gen shi han shu
""",
    "mathematical_physics_equations_terms.csv": """
第三类边界条件|third_kind_boundary_condition|di san lei bian jie tiao jian
混合边界条件|mixed_boundary_condition|hun he bian jie tiao jian
自然边界条件|natural_boundary_condition|zi ran bian jie tiao jian
齐次边界条件|homogeneous_boundary_condition|qi ci bian jie tiao jian
非齐次边界条件|nonhomogeneous_boundary_condition|fei qi ci bian jie tiao jian
非齐次项|nonhomogeneous_term|fei qi ci xiang
格林算子|green_operator|ge lin suan zi
传播子|propagator|chuan bo zi
解算子|solution_operator|jie suan zi
固有函数|proper_function|gu you han shu
""",
    "probability_theory_terms.csv": """
上确界事件|limsup_event|shang que jie shi jian
下确界事件|liminf_event|xia que jie shi jian
博雷尔集|borel_set|bo lei er ji
博雷尔域|borel_field|bo lei er yu
零一律|zero_one_law|ling yi lv
柯尔莫哥洛夫公理|kolmogorov_axioms|ke er mo ge luo fu gong li
可加性|additivity|ke jia xing
完全可加性|complete_additivity|wan quan ke jia xing
分布列|distribution_sequence|fen bu lie
联合分布函数|joint_distribution_function|lian he fen bu han shu
""",
    "mathematical_statistics_terms.csv": """
抽样|sampling|chou yang
简单随机样本|simple_random_sample|jian dan sui ji yang ben
样本矩|sample_moment|yang ben ju
中心矩|central_moment|zhong xin ju
样本中心矩|sample_central_moment|yang ben zhong xin ju
偏度|skewness|pian du
峰度|kurtosis|feng du
经验矩|empirical_moment|jing yan ju
统计推断|statistical_inference|tong ji tui duan
区间长度|interval_length|qu jian chang du
覆盖概率|coverage_probability|fu gai gai lv
枢轴量|pivot_quantity|shu zhou liang
""",
    "topology_terms.csv": """
拓扑不变量|topological_invariant|tuo pu bu bian liang
开核|open_kernel|kai he
闭核|closed_kernel|bi he
导集|derived_set|dao ji
稠密性|density|chou mi xing
无处稠密集|nowhere_dense_set|wu chu chou mi ji
第一纲集|set_of_first_category|di yi gang ji
第二纲集|set_of_second_category|di er gang ji
贝尔空间|baire_space|bei er kong jian
贝尔纲定理|baire_category_theorem|bei er gang ding li
""",
    "field_theory_terms.csv": """
域扩张|extension_field|yu kuo zhang
复合域|composite_field|fu he yu
线性无关|linear_independence|xian xing wu guan
线性基|linear_basis|xian xing ji
扩张基|basis_of_extension|kuo zhang ji
张量积|tensor_product|zhang liang ji
标量扩张|extension_of_scalars|biao liang kuo zhang
共轭多项式|conjugate_polynomial|gong e duo xiang shi
根域|root_field|gen yu
零点|zero|ling dian
多项式根|root_of_polynomial|duo xiang shi gen
重根|multiple_root|chong gen
判别式|discriminant|pan bie shi
导多项式|derived_polynomial|dao duo xiang shi
正规性|normality|zheng gui xing
可分性|separability|ke fen xing
线性不交|linear_disjointness|xian xing bu jiao
伽罗瓦群作用|action_of_galois_group|jia luo wa qun zuo yong
自同构群|automorphism_group|zi tong gou qun
中间扩张|intermediate_extension|zhong jian kuo zhang
固定子群|fixed_subgroup|gu ding zi qun
可解群|solvable_group|ke jie qun
阿廷施赖尔扩张|artin_schreier_extension|a ting shi lai er kuo zhang
有限域扩张|finite_field_extension|you xian yu kuo zhang
伽罗瓦闭域|galois_closed_field|jia luo wa bi yu
""",
}


def parse_additions(text):
    rows = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        cn, english, spaced_pinyin = raw.split("|")
        syllables = [part.strip().lower() for part in spaced_pinyin.split() if part.strip()]
        initials = "".join(part[0].upper() for part in syllables)
        pinyin = "".join(syllables)
        rows.append((cn.strip(), initials, english.strip(), pinyin))
    return rows


def read_existing(path):
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        return [(row[1], row[2], row[4], row[6]) for row in reader if row]


def write_table(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        for idx, (cn, initials, english, pinyin) in enumerate(rows, 1):
            writer.writerow([
                idx,
                cn,
                initials,
                len(initials),
                english,
                len(english),
                pinyin,
                len(pinyin),
            ])


def main():
    for filename, text in ADDITIONS.items():
        path = OUTPUT_DIRS[filename] / filename
        rows = read_existing(path)
        seen = {row[0] for row in rows}
        for row in parse_additions(text):
            if row[0] not in seen:
                rows.append(row)
                seen.add(row[0])
        write_table(path, rows)
        print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
