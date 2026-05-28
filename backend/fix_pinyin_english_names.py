import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORDS_DIR = ROOT / "words"

BAD_FRAGMENTS = {
    "lilun", "dingli", "moxing", "bubianliang", "fangcheng", "zuoyongliang",
    "guanxi", "gongshi", "yuanli", "jifen", "daoshu", "hanshu", "kongjian",
    "daishu", "fanchang", "zhankai", "fenjie", "bianjie", "xieyi", "yingli",
    "xiaoying", "guize", "guocheng", "fangfa", "quexian", "xingshi",
    "tiaojian", "weifen", "juzhen", "liangzi", "tuopu", "wenti", "suanfa",
    "zhenkong", "bosezi", "feimizi", "gaijin", "dengliziti", "duicheng",
    "ningju", "chuanbozi", "yeti", "xibao", "qujinbi", "jiaozibaohe",
    "concept",
}

GREEK_ENGLISH = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ϵ": "epsilon",
    "ε": "epsilon",
    "ζ": "zeta",
    "η": "eta",
    "θ": "theta",
    "λ": "lambda",
    "μ": "mu",
    "ν": "nu",
    "ξ": "xi",
    "π": "pi",
    "ρ": "rho",
    "σ": "sigma",
    "ς": "sigma",
    "τ": "tau",
    "υ": "upsilon",
    "φ": "phi",
    "χ": "chi",
    "ψ": "psi",
    "ω": "omega",
    "Α": "alpha",
    "Β": "beta",
    "Γ": "gamma",
    "Δ": "delta",
    "Ε": "epsilon",
    "Ζ": "zeta",
    "Η": "eta",
    "Θ": "theta",
    "Λ": "lambda",
    "Μ": "mu",
    "Ν": "nu",
    "Ξ": "xi",
    "Π": "pi",
    "Σ": "sigma",
    "Φ": "phi",
    "Ω": "omega",
}

EXACT = {
    "ΛQCD": "lambda_QCD",
    "NRQCD": "NRQCD",
    "SCET": "SCET",
    "MSbar方案": "MSbar_scheme",
    "BF理论": "BF_theory",
    "A模型": "A_model",
    "B模型": "B_model",
    "M理论": "M_theory",
    "F理论": "F_theory",
    "BFSS矩阵模型": "BFSS_matrix_model",
    "IKKT矩阵模型": "IKKT_matrix_model",
    "SYK模型": "SYK_model",
    "OPE展开": "OPE_expansion",
    "BPZ方程": "BPZ_equation",
    "WZW模型": "WZW_model",
    "c定理": "c_theorem",
    "a定理": "a_theorem",
    "F定理": "F_theorem",
    "JLMS关系": "JLMS_relation",
    "APS指标定理": "APS_index_theorem",
    "K理论配对": "K_theory_pairing",
    "QCD相图": "QCD_phase_diagram",
    "OZI规则": "OZI_rule",
}

MANUAL_OVERRIDES = {
    "威滕图": "witten_diagram",
    "胡贝尼-朗加马尼-高柳面": "hubeny_rangamani_takayanagi_surface",
    "纠缠楔截面": "entanglement_wedge_cross_section",
    "弗尔林德公式": "verlinde_formula",
    "莱文-文弦网": "levin_wen_string_net",
    "开威尔逊线": "open_wilson_line",
    "威尔逊线": "wilson_line",
    "θ项": "theta_term",
    "格林-施瓦茨弦": "green_schwarz_string",
    "I型弦": "type_I_string",
    "IIA型弦": "type_IIA_string",
    "IIB型弦": "type_IIB_string",
    "图拉耶夫-维罗模型": "turaev_viro_model",
    "哈达玛门": "hadamard_gate",
    "斯特藩玻尔兹曼定律": "stefan_boltzmann_law",
    "巴塔林维尔科维斯基形式": "batalin_vilkovisky_formalism",
    "高阶阿廷栈": "higher_artin_stack",
    "卡兹丹卢斯蒂格多项式": "kazhdan_lusztig_polynomial",
    "卡兹丹卢斯蒂格基": "kazhdan_lusztig_basis",
    "卡兹丹卢斯蒂格猜想": "kazhdan_lusztig_conjecture",
    "安南凯维奇簇": "anikievich_cluster",
    "佐武等价": "satake_equivalence",
    "几何佐武等价": "geometric_satake_equivalence",
    "内隆模型": "neron_model",
    "切博塔廖夫密度定理": "chebotarev_density_theorem",
    "卡拉比-丘范畴": "calabi_yau_category",
    "分数卡拉比-丘范畴": "fractional_calabi_yau_category",
    "深谷范畴": "fukaya_category",
    "包裹深谷范畴": "wrapped_fukaya_category",
    "柏林森谱序列": "beilinson_spectral_sequence",
    "基里洛夫-列舍季欣模": "kirillov_reshetikhin_module",
    "列舍季欣-图拉耶夫不变量": "reshetikhin_turaev_invariant",
    "威滕-列舍季欣-图拉耶夫不变量": "witten_reshetikhin_turaev_invariant",
    "图拉耶夫维罗不变量": "turaev_viro_invariant",
    "埃廷戈夫卡赞丹量子化": "etingof_kazhdan_quantization",
    "马季德双": "majid_double",
    "辛约化": "symplectic_reduction",
    "潘德哈里潘德托马斯不变量": "pandharipande_thomas_invariant",
    "克朗海默纳卡岛簇": "kronheimer_nakajima_variety",
    "阿廷栈": "artin_stack",
    "克沙壁越公式": "kontsevich_soibelman_formula",
    "若尔当算子代数": "jordan_operator_algebra",
    "盖尔范德-奈马克-西格尔构造": "gelfand_naimark_segal_construction",
    "圆酉系综": "circular_unitary_ensemble",
    "辛余球丛": "symplectic_cosphere_bundle",
    "普拉格门-林德勒夫原理": "phragmen_lindelof_principle",
    "内万林纳特征": "nevanlinna_characteristic",
    "切丛": "tangent_bundle",
    "法丛": "normal_bundle",
    "陈韦伊理论": "chern_weil_theory",
    "戴金图": "dynkin_diagram",
    "复化": "complexification",
    "辛群": "symplectic_group",
    "疏朗集": "sparse_set",
    "增广路": "augmenting_path",
    "垂心": "orthocenter",
    "杨图": "young_diagram",
    "杨表": "young_tableau",
    "罗宾逊申斯特德对应": "robinson_schensted_correspondence",
    "裴蜀定理": "bezout_theorem",
    "四矩定理": "four_moment_theorem",
    "因数": "factor",
    "叉积": "cross_product",
    "双倾斜": "double_tilt",
    "双射证明": "bijective_proof",
    "双正交多项式": "biorthogonal_polynomial",
    "HOMFLY多项式": "HOMFLY_polynomial",
    "几何 朗兰兹对偶": "geometric_langlands_duality",
    "朗兰兹分类": "langlands_classification",
    "朗兰兹对偶群": "langlands_dual_group",
    "几何朗兰兹范畴": "geometric_langlands_category",
    "朗兰兹对应": "langlands_correspondence",
    "边界杨巴克斯特方程": "boundary_yang_baxter_equation",
    "朗兰兹分解": "langlands_decomposition",
    "富比尼定理": "fubini_theorem",
    "勒让德哈达玛条件": "legendre_hadamard_condition",
    "埃尔米特多项式": "hermite_polynomial",
    "华林问题": "waring_problem",
    "魏尔斯特拉斯逼近定理": "weierstrass_approximation_theorem",
    "魏尔斯特拉斯判别法": "weierstrass_test",
}

TOKENS = {
    "阿贝尔": "abel", "阿蒂亚": "atiyah", "阿尔泽拉": "arzela", "阿诺德": "arnold",
    "阿什特卡": "ashtekar", "阿斯科利": "ascoli", "艾伦": "allen", "爱因斯坦": "einstein",
    "巴贝罗": "barbero", "巴雷特": "barrett", "巴拿赫": "banach", "贝尔曼": "bellman",
    "贝塞尔": "bessel", "贝特": "bethe", "贝叶斯": "bayes", "贝祖": "bezout",
    "班克斯": "banks", "梅特罗波利斯": "metropolis", "朗道": "landau", "库仑": "coulomb",
    "玻恩": "born", "波尔查诺": "bolzano", "布莱克韦尔": "blackwell",
    "布赖滕洛纳": "breitenlohner", "陈西蒙斯": "chern_simons", "陈-西蒙斯": "chern_simons",
    "陈": "chern", "戴克赫拉夫": "dijkgraaf", "戴森": "dyson", "狄拉克": "dirac",
    "法捷耶夫": "faddeev", "费弗曼": "fefferman", "费马": "fermat", "费米": "fermi",
    "费曼": "feynman", "弗雷德霍姆": "fredholm", "弗里德曼": "freedman", "傅里叶": "fourier",
    "富田": "tomita", "伽罗瓦": "galois", "高斯": "gauss", "高柳": "takayanagi",
    "盖尔曼": "gell_mann", "格林": "green", "格罗莫夫": "gromov", "格罗斯": "grosse",
    "戈德斯通": "goldstone", "戈帕库马尔": "gopakumar", "哈代": "hardy", "哈密顿": "hamilton",
    "哈恩": "hahn", "哈尔": "haar", "哈特尔": "hartle", "海登": "hayden",
    "亨宁森": "henningson", "希尔伯特": "hilbert", "希利亚德": "hilliard", "霍金": "hawking",
    "霍普夫": "hopf", "雅可比": "jacobi", "杰基夫": "jackiw", "卡尔德龙": "calderon",
    "卡恩": "cahn", "卡拉比": "calabi", "卡鲁扎": "kaluza", "卡茨": "kac",
    "卡奇": "karch", "卡普斯廷": "kapustin", "柯西": "cauchy", "克莱巴诺夫": "klebanov",
    "克莱因": "klein", "克莱恩": "crane", "克拉默": "cramer", "克兰克": "crank",
    "科特韦格": "korteweg", "孔涅": "connes", "拉奥": "rao", "拉东": "radon",
    "拉格朗日": "lagrange", "拉克斯": "lax", "莱夫勒": "leffler", "莱曼": "lehmann",
    "莱文": "levin", "兰德尔": "randall", "朗加马尼": "rangamani", "朗曼": "langmann",
    "勒贝格": "lebesgue", "勒让德": "legendre", "黎曼": "riemann", "里斯": "riesz",
    "列舍季欣": "reshetikhin", "刘维尔": "liouville", "柳": "ryu", "龙格": "runge",
    "洛伦兹": "lorentz", "罗赞斯基": "rozansky", "麦克斯韦": "maxwell", "蒙日": "monge",
    "米尔格拉姆": "milgram", "米塔格": "mittag", "闵可夫斯基": "minkowski", "穆迪": "moody",
    "梅林": "mellin", "费希尔": "fisher", "维尔马": "verma", "卡迪": "cardy",
    "沃德": "ward", "雷尼": "renyi", "扎莫洛奇科夫": "zamolodchikov",
    "特霍夫特": "t_hooft", "瓦伊迪亚": "vaidya", "利夫希茨": "lifshitz",
    "雅努斯": "janus", "舒尔": "schur", "菅原": "sugawara",
    "纳什": "nash", "纳维": "navier", "奈曼": "neyman", "南部": "nambu",
    "牛顿": "newton", "诺特": "noether", "庞加莱": "poincare", "彭扎诺": "ponzano",
    "佩顿": "paton", "佩奇": "page", "普朗克": "planck", "普雷斯基尔": "preskill",
    "普雷斯": "press", "普拉格门": "phragmen", "齐格蒙德": "zygmund", "丘": "yau",
    "萨博": "szabo", "萨尔皮特": "salpeter", "萨克斯": "sachs", "桑德拉姆": "sundrum",
    "塞伯格": "seiberg", "杉本": "sugimoto", "施蒂费尔": "stiefel", "施密特": "schmidt",
    "施瓦茨": "schwarz", "施温格": "schwinger", "斯蒂尔切斯": "stieltjes",
    "斯托克斯": "stokes", "斯特拉斯勒": "strassler", "斯肯德里斯": "skenderis",
    "泰特尔博伊姆": "teitelboim", "唐纳森": "donaldson", "图拉耶夫": "turaev",
    "瓦法": "vafa", "威尔逊": "wilson", "威滕": "witten", "韦尔": "weyl",
    "韦斯": "wess", "魏尔斯特拉斯": "weierstrass", "沃尔": "wall", "沃尔泰拉": "volterra",
    "武尔肯哈尔": "wulkenhaar", "西格尔": "segal", "西蒙斯": "simons", "谢费": "scheffe",
    "谢克特": "schechter", "谢斯": "sheth", "薛定谔": "schrodinger", "亚当斯": "adams",
    "耶特": "yetter", "伊辛": "ising", "伊藤": "ito", "因费尔德": "infeld",
    "朱米诺": "zumino", "安培": "ampere", "福克": "fokker", "卡舍尔": "casher",
    "奥克斯": "oakes", "雷纳": "renner", "贝特": "bethe", "波波夫": "popov",
    "胡贝尼": "hubeny", "酒井": "sakai", "后藤": "goto", "玻色": "bose",
    "费米": "fermi", "狄利克雷": "dirichlet", "诺伊曼": "neumann",

    "拓扑量子场论": "topological_quantum_field_theory",
    "弦理论": "string_theory", "超弦理论": "superstring_theory", "圈量子引力": "loop_quantum_gravity",
    "共形场论": "conformal_field_theory", "全息原理": "holographic_principle",
    "非对易几何": "noncommutative_geometry", "非交换几何": "noncommutative_geometry",
    "算子代数": "operator_algebra", "随机矩阵理论": "random_matrix_theory",
    "数学量子群": "mathematical_quantum_group", "导范畴": "derived_category",
    "代数几何": "algebraic_geometry", "微分几何": "differential_geometry",
    "同调代数": "homological_algebra", "李群李代数": "lie_groups_and_lie_algebras",
    "解析几何": "analytic_geometry", "初等数论": "elementary_number_theory",
    "组合基础": "combinatorics_basics", "变分法": "calculus_of_variations",
    "积分方程": "integral_equation", "向量张量分析": "vector_tensor_analysis",
    "运筹学": "operations_research", "杨-米尔斯": "yang_mills", "杨米尔斯": "yang_mills",
    "格点QCD": "lattice_QCD", "有限密度QCD": "finite_density_QCD",
    "有限温度QCD": "finite_temperature_QCD", "QCD相图": "QCD_phase_diagram",
    "拓扑荷": "topological_charge", "拓扑磁化率": "topological_susceptibility",
    "轴反常": "axial_anomaly", "手征凝聚": "chiral_condensate",
    "手征对称破缺": "chiral_symmetry_breaking", "威尔逊作用量": "wilson_action",
    "重夸克有效理论": "heavy_quark_effective_theory", "颜色玻璃凝聚": "color_glass_condensate",
    "小x物理": "small_x_physics", "BFKL演化": "BFKL_evolution", "DGLAP演化": "DGLAP_evolution",
    "部分子分布函数": "parton_distribution_function", "广义部分子分布": "generalized_parton_distribution",
    "横动量分布": "transverse_momentum_distribution", "手征磁效应": "chiral_magnetic_effect",
    "手征涡旋效应": "chiral_vortical_effect", "瞬子诱导相互作用": "instanton_induced_interaction",
    "瞬子关联函数": "instanton_correlation_function",

    "理论": "theory", "公理": "axiom", "不变量": "invariant", "变量": "variable",
    "模型": "model", "方程组": "equations", "方程": "equation", "作用量": "action",
    "作用": "action", "关系": "relation", "公式": "formula", "定理": "theorem",
    "引理": "lemma", "原理": "principle", "猜想": "conjecture", "问题": "problem",
    "方法": "method", "算法": "algorithm", "规则": "rule", "机制": "mechanism",
    "过程": "process", "条件": "condition", "形式": "form", "方案": "scheme",
    "指标定理": "index_theorem", "指标": "index", "展开": "expansion", "映射": "map",
    "变换": "transformation", "流": "flow", "演化": "evolution", "路径积分": "path_integral",
    "积分": "integral", "微分": "differential", "导数": "derivative", "函数": "function",
    "泛函": "functional", "算符": "operator", "算子": "operator", "矩阵": "matrix",
    "张量": "tensor", "矢量": "vector", "旋量": "spinor", "标量": "scalar",
    "场": "field", "荷": "charge", "流形": "manifold", "空间理论": "space_theory",
    "空间": "space", "模空间": "moduli_space", "相空间": "phase_space", "代数": "algebra",
    "李代数": "lie_algebra", "李群": "lie_group", "群": "group", "范畴": "category",
    "函子": "functor", "层": "sheaf", "丛": "bundle", "类": "class", "环": "ring",
    "域": "field", "格": "lattice", "图": "graph", "树": "tree", "曲线": "curve",
    "曲面": "surface", "面": "surface", "几何": "geometry", "拓扑": "topology",
    "上同调": "cohomology", "同调": "homology", "复形": "complex", "谱序列": "spectral_sequence",
    "序列": "sequence", "分解": "decomposition", "结构": "structure", "表示论": "representation_theory",
    "表示": "representation", "特征类": "characteristic_class", "特征": "characteristic",
    "测度": "measure", "分布": "distribution", "密度": "density", "估计": "estimate",
    "极限": "limit", "近似": "approximation", "对偶": "duality", "对应": "correspondence",
    "配对": "pairing", "相变": "phase_transition", "相": "phase", "效应": "effect",
    "态": "state", "真空": "vacuum", "熵": "entropy", "纠缠": "entanglement",
    "信息": "information", "协议": "protocol", "虫洞": "wormhole", "黑洞": "black_hole",
    "引力": "gravity", "量子": "quantum", "超弦": "superstring", "弦": "string",
    "膜": "brane", "D膜": "D_brane", "规范场": "gauge_field", "规范理论": "gauge_theory",
    "规范": "gauge", "有效理论": "effective_theory", "反常": "anomaly", "边界": "boundary",
    "缺陷": "defect", "配分函数": "partition_function", "自旋": "spin", "自举": "bootstrap",
    "共形": "conformal", "超共形": "superconformal", "全息": "holographic",
    "非对易": "noncommutative", "非交换": "noncommutative", "交换": "commutative",
    "手征": "chiral", "瞬子": "instanton", "反瞬子": "anti_instanton",
    "胶子": "gluon", "夸克": "quark", "介子": "meson", "胶球": "glueball",
    "禁闭": "confinement", "重整化群": "renormalization_group", "重整化": "renormalization",
    "渐近自由": "asymptotic_freedom", "阈值": "threshold", "匹配": "matching",
    "两圈": "two_loop", "三圈": "three_loop", "微扰论": "perturbation_theory",
    "孤子": "soliton", "冷却": "cooling", "颜色": "color", "粘度": "viscosity",
    "输运": "transport", "系数": "coefficient", "临界": "critical", "端点": "endpoint",
    "慢化": "slowing_down", "物质": "matter", "温度": "temperature", "温": "temperature",
    "有限": "finite", "双": "double", "四": "four", "三": "three", "两": "two",
    "一": "one", "大": "large", "小": "small", "高": "high", "低": "low",
    "强": "strong", "弱": "weak", "平坦": "flat", "弯曲": "curved", "局部": "local",
    "整体": "global", "自由": "free", "紧化": "compactification", "紧致化": "compactification",
    "亏格": "genus", "世界面": "worldsheet", "靶空间": "target_space", "玻色子": "boson",
    "费米子": "fermion", "鬼": "ghost", "系统": "system", "中心荷": "central_charge",
    "中心": "center", "维数": "dimension", "标度维数": "scaling_dimension", "标度": "scaling",
    "一次场": "primary_field", "准一次场": "quasi_primary_field", "最高权态": "highest_weight_state",
    "零范数态": "null_state", "边界态": "boundary_state", "交叉帽态": "crosscap_state",
    "融合": "fusion", "模块": "modular", "庞加莱盘": "poincare_disk", "二维": "two_dimensional",
    "三维": "three_dimensional", "四维": "four_dimensional", "维": "dimensional",
    "超": "super", "R对称": "R_symmetry", "角色": "character", "谱隙": "spectral_gap",
    "互信息": "mutual_information", "反射正性": "reflection_positivity", "幺正界": "unitarity_bound",
    "阴影": "shadow", "双迹": "double_trace", "轻": "light", "重": "heavy", "圆": "circle",
    "圈": "loop", "量子群": "quantum_group", "随机矩阵": "random_matrix", "算术": "arithmetic",
    "代数": "algebraic", "微分": "differential", "解析": "analytic", "组合": "combinatorial",
    "初等": "elementary", "数论": "number_theory", "几何分析": "geometric_analysis",
    "谱几何": "spectral_geometry", "进阶": "advanced", "模": "module", "同伦": "homotopy",
    "极小": "minimal", "理想": "ideal", "商": "quotient", "核": "kernel", "余核": "cokernel",
    "正合": "exact", "导出": "derived", "三角": "triangulated", "投射": "projective",
    "内射": "injective", "谱": "spectrum", "半群": "semigroup", "C星": "C_star",
    "冯诺伊曼": "von_neumann", "迹": "trace", "投影": "projection", "交叉积": "crossed_product",
    "因子": "factor", "外尔": "weyl", "椭圆曲线": "elliptic_curve", "阿贝尔簇": "abelian_variety",
    "高度": "height", "局部域": "local_field", "整体域": "global_field", "模形式": "modular_form",
    "素数": "prime", "质数": "prime", "合数": "composite_number", "整除": "divisibility",
    "同余": "congruence", "二次剩余": "quadratic_residue", "丢番图": "diophantine",
    "生成函数": "generating_function", "递推": "recurrence", "容斥": "inclusion_exclusion",
    "排列": "permutation", "组合": "combination", "图论": "graph_theory", "染色": "coloring",
    "凸包": "convex_hull", "圆锥": "cone", "双曲线": "hyperbola", "椭圆": "ellipse",
    "抛物线": "parabola", "焦点": "focus", "准线": "directrix", "离心率": "eccentricity",
    "极坐标": "polar_coordinate", "直线": "line", "平面": "plane", "点": "point",
    "距离": "distance", "角": "angle", "斜率": "slope", "截距": "intercept",
    "法向量": "normal_vector", "向量场": "vector_field", "向量": "vector", "张量": "tensor",
    "分析": "analysis", "梯度": "gradient", "散度": "divergence", "旋度": "curl",
    "雅可比": "jacobian", "海森": "hessian", "优化": "optimization", "规划": "programming",
    "线性规划": "linear_programming", "整数规划": "integer_programming", "动态规划": "dynamic_programming",
    "对偶定理": "duality_theorem", "单纯形": "simplex", "库存": "inventory", "排队论": "queueing_theory",
    "排队": "queueing", "网络": "network", "流量": "flow", "决策": "decision", "收益": "payoff",
    "策略": "strategy", "博弈": "game", "马尔可夫": "markov", "链": "chain", "蒙特卡洛": "monte_carlo",
    "模拟": "simulation", "灵敏度": "sensitivity", "目标": "objective", "可行域": "feasible_region",
    "最优": "optimal", "最短路": "shortest_path", "割": "cut", "基": "basis", "形": "form",
    "液体": "liquid", "稀薄": "dilute", "气": "gas", "真空": "vacuum",
    "对称破缺": "symmetry_breaking", "对称": "symmetry", "凝聚": "condensate",
    "传播子": "propagator", "传播": "propagation", "改进": "improvement",
    "赝": "pseudo", "热浴": "heat_bath", "加权": "weighting", "重加权": "reweighting",
    "符号": "sign", "去禁闭": "deconfinement", "等离子体": "plasma", "静态": "static",
    "势": "potential", "面积": "area", "周长": "perimeter", "磁单极": "magnetic_monopole",
    "超导": "superconductivity", "玻璃": "glass", "饱和": "saturation", "奇异": "strange",
    "轴荷": "axial_charge", "梯度流": "gradient_flow", "荷密度": "charge_density",
    "三叶草": "clover", "辛曼齐克": "symanzik", "交错": "staggered", "畴壁": "domain_wall",
    "重叠": "overlap", "数": "number", "值": "value", "子": "particle", "项": "term",
    "线": "line", "点": "point",
    "交叉": "crossing", "涡旋": "vortex", "截断": "truncation", "混杂": "hybrid",
    "软": "soft", "共线": "collinear", "碎裂": "fragmentation", "喷注": "jet",
    "耦合": "coupling", "常数": "constant", "跑动": "running", "味": "flavor",
    "剪切": "shear", "顶点": "vertex", "乘积": "product", "块": "block",
    "维拉索罗": "virasoro", "生成元": "generator", "行列式": "determinant",
    "最小": "minimal", "波茨": "potts", "构造": "construction", "仿射": "affine",
    "应力": "stress", "能动": "energy_momentum", "恒等式": "identity", "径向": "radial",
    "量子化": "quantization", "振幅": "amplitude", "轻锥": "light_cone",
    "对角": "diagonal", "不变性": "invariance", "全局": "global", "经典": "classical",
    "指数": "exponent", "相对": "relative", "热": "thermal", "边缘": "marginal",
    "相关": "correlation", "长度": "length", "无质量": "massless", "度量": "metric",
    "反": "anti", "形变": "deformation", "可积": "integrable", "字典": "dictionary",
    "坐标": "coordinate", "能标": "energy_scale", "源": "source", "体": "bulk",
    "正规化": "normalization", "正规": "normal", "非正规化": "nonnormalizable",
    "极值": "extremal", "楔": "wedge", "重构": "reconstruction", "纠错": "error_correction",
    "码": "code", "反德西特": "anti_de_sitter", "热化": "thermalization",
    "准正规": "quasinormal", "金属": "metal", "违背": "violation", "背景": "background",
    "界面": "interface", "记忆": "memory", "复杂度": "complexity", "体积": "volume",
    "开弦": "open_string", "探针": "probe", "拖曳": "trailing", "淬火": "quenching",
    "参数": "parameter", "粘滞": "viscosity", "比": "ratio", "界": "bound",
    "流体": "fluid", "范式": "paradigm", "域墙": "domain_wall", "多迹": "multi_trace",
    "替代": "alternate", "量纲": "dimension", "体边": "bulk_to_boundary",
    "体体": "bulk_to_bulk", "接触": "contact", "修正": "correction", "微态": "microstate",
    "巨": "giant", "碎片化": "fragmentation", "屏": "screen", "协变": "covariant",
    "聚焦": "focusing", "零能": "null_energy", "模块哈密顿量": "modular_hamiltonian",
    "第一定律": "first_law", "可测": "measurable", "完备": "complete", "正则": "regular",
    "正定": "positive_definite", "半正定": "positive_semidefinite", "全纯": "holomorphic",
    "稳定": "stable", "不稳定": "unstable", "约化": "reduced", "概率": "probability",
    "集": "set", "边": "edge", "邻域": "neighborhood", "开": "open", "闭": "closed",
    "连续": "continuous", "光滑": "smooth", "可微": "differentiable", "可逆": "invertible",
    "有限": "finite", "无限": "infinite", "局部化": "localization", "紧": "compact",
    "连通": "connected", "单位": "unit", "根": "root", "权": "weight", "最高权": "highest_weight",
    "最低权": "lowest_weight", "特征值": "eigenvalue", "特征向量": "eigenvector",
    "本征值": "eigenvalue", "本征向量": "eigenvector", "可约": "reducible", "不可约": "irreducible",
    "投影": "projection", "截面": "section", "截": "section", "序": "order",
    "律": "law", "族": "family", "簇": "cluster", "图像": "picture", "表": "table",
}

KEYS_BY_FIRST = {}
for key in sorted(TOKENS, key=len, reverse=True):
    KEYS_BY_FIRST.setdefault(key[0], []).append(key)


def is_bad_english(english, pinyin):
    value = str(english or "").strip().lower()
    py = str(pinyin or "").strip().lower()
    if not value:
        return True
    compact = value.replace("_", "")
    compact_py = py.replace("_", "")
    if compact == compact_py:
        return True
    return any(fragment in value for fragment in BAD_FRAGMENTS)


def longest_common_run(left, right):
    if not left or not right:
        return 0
    previous = [0] * (len(right) + 1)
    best = 0
    for left_char in left:
        current = [0] * (len(right) + 1)
        for index, right_char in enumerate(right, 1):
            if left_char == right_char:
                current[index] = previous[index - 1] + 1
                best = max(best, current[index])
        previous = current
    return best


def push(parts, value):
    for piece in str(value).replace("-", "_").split("_"):
        if piece:
            parts.append(piece)


def english_name(chinese):
    if chinese in EXACT:
        return EXACT[chinese], []
    text = str(chinese or "").replace("（", "").replace("）", "").replace("(", "").replace(")", "")
    parts = []
    unknown = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in "-－–—·/":
            index += 1
            continue
        if char in GREEK_ENGLISH:
            parts.append(GREEK_ENGLISH[char])
            index += 1
            continue
        if char.isascii():
            if not (char.isalnum() or char == "_"):
                index += 1
                continue
            end = index
            while end < len(text) and text[end].isascii() and (text[end].isalnum() or text[end] == "_"):
                end += 1
            parts.append(text[index:end])
            index = end
            continue
        matched = None
        for key in KEYS_BY_FIRST.get(char, []):
            if text.startswith(key, index):
                matched = key
                break
        if matched:
            push(parts, TOKENS[matched])
            index += len(matched)
            continue
        unknown.append(char)
        parts.append("concept")
        index += 1
    result = re.sub(r"_+", "_", "_".join(parts)).strip("_")
    return result or "concept", unknown


def repair_file(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return 0, Counter()
    changed = 0
    unknowns = Counter()
    for row in rows[1:]:
        if len(row) < 9:
            continue
        manual = MANUAL_OVERRIDES.get(row[1])
        if manual:
            if row[5] != manual or row[6] != str(len(manual)):
                row[5] = manual
                row[6] = str(len(manual))
                changed += 1
            continue
        if not is_bad_english(row[5], row[7]):
            continue
        fixed, unknown = english_name(row[1])
        if row[5] != fixed or row[6] != str(len(fixed)):
            row[5] = fixed
            row[6] = str(len(fixed))
            changed += 1
            unknowns.update(unknown)
    if changed:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(rows)
    return changed, unknowns


def main():
    total = 0
    total_unknowns = Counter()
    changed_files = []
    for path in sorted(WORDS_DIR.rglob("*.csv")):
        changed, unknowns = repair_file(path)
        if changed:
            changed_files.append((path.relative_to(ROOT), changed))
            total += changed
            total_unknowns.update(unknowns)
    for path, changed in changed_files:
        print(f"{path}: {changed}")
    print(f"total_changed={total}")
    if total_unknowns:
        print("unknown_chars=" + " ".join(f"{char}:{count}" for char, count in total_unknowns.most_common(80)))


if __name__ == "__main__":
    main()
