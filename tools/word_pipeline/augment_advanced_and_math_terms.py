import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORDS_DIR = ROOT / "words"
PHYSICS_ADVANCED_DIR = WORDS_DIR / "物理" / "普通模式：四大力学"
MATH_SIMPLE_DIR = WORDS_DIR / "数学" / "简单模式"
MATH_NORMAL_DIR = WORDS_DIR / "数学" / "普通模式"
MATH_HARD_DIR = WORDS_DIR / "数学" / "困难模式"

OUTPUT_DIRS = {
    "theoretical_mechanics_terms.csv": PHYSICS_ADVANCED_DIR,
    "electrodynamics_terms.csv": PHYSICS_ADVANCED_DIR,
    "thermo_stat_mech_terms.csv": PHYSICS_ADVANCED_DIR,
    "quantum_mechanics_terms.csv": PHYSICS_ADVANCED_DIR,
    "advanced_calculus_terms.csv": MATH_SIMPLE_DIR,
    "linear_algebra_terms.csv": MATH_SIMPLE_DIR,
    "complex_analysis_terms.csv": MATH_NORMAL_DIR,
    "mathematical_physics_equations_terms.csv": MATH_NORMAL_DIR,
    "probability_theory_terms.csv": MATH_NORMAL_DIR,
    "mathematical_statistics_terms.csv": MATH_NORMAL_DIR,
    "topology_terms.csv": MATH_HARD_DIR,
    "group_theory_terms.csv": MATH_HARD_DIR,
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
    "theoretical_mechanics_terms.csv": """
拉格朗日力学|lagrangian_mechanics|la ge lang ri li xue
哈密顿力学|hamiltonian_mechanics|ha mi dun li xue
牛顿力学|newtonian_mechanics|niu dun li xue
分析力学|analytical_mechanics|fen xi li xue
完整约束|holonomic_constraint|wan zheng yue shu
非完整约束|nonholonomic_constraint|fei wan zheng yue shu
定常约束|scleronomic_constraint|ding chang yue shu
非定常约束|rheonomic_constraint|fei ding chang yue shu
单面约束|unilateral_constraint|dan mian yue shu
双面约束|bilateral_constraint|shuang mian yue shu
广义加速度|generalized_acceleration|guang yi jia su du
第一类拉格朗日方程|lagrange_equation_of_first_kind|di yi lei la ge lang ri fang cheng
第二类拉格朗日方程|lagrange_equation_of_second_kind|di er lei la ge lang ri fang cheng
拉格朗日乘子|lagrange_multiplier|la ge lang ri cheng zi
拉格朗日乘子法|method_of_lagrange_multipliers|la ge lang ri cheng zi fa
能量积分|energy_integral|neng liang ji fen
雅可比积分|jacobi_integral|ya ke bi ji fen
广义能量|generalized_energy|guang yi neng liang
相空间|phase_space|xiang kong jian
位形空间|configuration_space|wei xing kong jian
勒让德变换|legendre_transformation|le rang de bian huan
勒让德矩阵|legendre_matrix|le rang de ju zhen
辛结构|symplectic_structure|xin jie gou
辛矩阵|symplectic_matrix|xin ju zhen
辛变换|symplectic_transformation|xin bian huan
刘维尔定理|liouville_theorem|liu wei er ding li
可积系统|integrable_system|ke ji xi tong
常数变易法|variation_of_constants|chang shu bian yi fa
诺特定理|noether_theorem|nuo te ding li
空间平移对称性|space_translation_symmetry|kong jian ping yi dui chen xing
时间平移对称性|time_translation_symmetry|shi jian ping yi dui chen xing
转动对称性|rotational_symmetry|zhuan dong dui chen xing
惯量椭球|inertia_ellipsoid|guan liang tuo qiu
惯性主轴|principal_axis_of_inertia|guan xing zhu zhou
本体坐标系|body_fixed_frame|ben ti zuo biao xi
空间坐标系|space_fixed_frame|kong jian zuo biao xi
角速度矢量|angular_velocity_vector|jiao su du shi liang
角动量矢量|angular_momentum_vector|jiao dong liang shi liang
欧拉运动学方程|euler_kinematic_equation|ou la yun dong xue fang cheng
无力矩运动|torque_free_motion|wu li ju yun dong
对称陀螺|symmetric_top|dui chen tuo luo
重陀螺|heavy_top|zhong tuo luo
拉莫尔进动|larmor_precession|la mo er jin dong
线性化|linearization|xian xing hua
平衡位置|equilibrium_position|ping heng wei zhi
耦合振动|coupled_oscillation|ou he zhen dong
质量矩阵|mass_matrix|zhi liang ju zhen
刚度矩阵|stiffness_matrix|gang du ju zhen
本征频率|eigenfrequency|ben zheng pin lv
本征振型|eigenmode|ben zheng zhen xing
相轨道|phase_trajectory|xiang gui dao
庞加莱截面|poincare_section|pang jia lai jie mian
混沌运动|chaotic_motion|hun dun yun dong
稳定性|stability|wen ding xing
有效质量|effective_mass|you xiao zhi liang
有效力|effective_force|you xiao li
拉格朗日括号|lagrange_bracket|la ge lang ri kuo hao
可分离变量|separable_variable|ke fen li bian liang
作用角变量|action_angle_variable|zuo yong jiao bian liang
""",
    "electrodynamics_terms.csv": """
静电学|electrostatics|jing dian xue
静磁学|magnetostatics|jing ci xue
泊松方程|poisson_equation|bo song fang cheng
拉普拉斯方程|laplace_equation|la pu la si fang cheng
镜像法|method_of_images|jing xiang fa
分离变量法|separation_of_variables|fen li bian liang fa
边值问题|boundary_value_problem|bian zhi wen ti
狄利克雷边界条件|dirichlet_boundary_condition|di li ke lei bian jie tiao jian
诺伊曼边界条件|neumann_boundary_condition|nuo yi man bian jie tiao jian
电位移矢量|electric_displacement_vector|dian wei yi shi liang
磁场强度|magnetic_field_strength|ci chang qiang du
极化强度|polarization_density|ji hua qiang du
磁化强度|magnetization_intensity|ci hua qiang du
束缚电荷|bound_charge|shu fu dian he
自由电荷|free_charge|zi you dian he
束缚电流|bound_current|shu fu dian liu
自由电流|free_current|zi you dian liu
表面电荷密度|surface_charge_density|biao mian dian he mi du
表面电流密度|surface_current_density|biao mian dian liu mi du
体电荷密度|volume_charge_density|ti dian he mi du
传导电流|conduction_current|chuan dao dian liu
位移电流|displacement_current|wei yi dian liu
欧姆定律微分形式|differential_form_of_ohms_law|ou mu ding lv wei fen xing shi
洛伦兹互易定理|lorentz_reciprocity_theorem|luo lun zi hu yi ding li
唯一性定理|uniqueness_theorem|wei yi xing ding li
介质极化|dielectric_polarization|jie zhi ji hua
线性介质|linear_medium|xian xing jie zhi
各向同性介质|isotropic_medium|ge xiang tong xing jie zhi
各向异性介质|anisotropic_medium|ge xiang yi xing jie zhi
均匀介质|homogeneous_medium|jun yun jie zhi
非均匀介质|inhomogeneous_medium|fei jun yun jie zhi
导电介质|conducting_medium|dao dian jie zhi
理想导体|perfect_conductor|li xiang dao ti
理想介质|perfect_dielectric|li xiang jie zhi
亥姆霍兹方程|helmholtz_equation|hai mu huo zi fang cheng
达朗贝尔算符|d_alembert_operator|da lang bei er suan fu
赫兹矢量|hertz_vector|he zi shi liang
电偶极矩|electric_dipole_moment|dian ou ji ju
磁偶极矩|magnetic_dipole_moment|ci ou ji ju
辐射场|radiation_field|fu she chang
近场区|near_field_region|jin chang qu
远场区|far_field_region|yuan chang qu
天线|antenna|tian xian
偶极天线|dipole_antenna|ou ji tian xian
辐射功率|radiated_power|fu she gong lv
拉莫尔公式|larmor_formula|la mo er gong shi
切伦科夫辐射|cherenkov_radiation|qie lun ke fu fu she
同步辐射|synchrotron_radiation|tong bu fu she
反射定律|law_of_reflection|fan she ding lv
折射定律|law_of_refraction|zhe she ding lv
菲涅耳公式|fresnel_equations|fei nie er gong shi
全反射|total_internal_reflection|quan fan she
波阻抗|wave_impedance|bo zu kang
驻波|standing_wave|zhu bo
传输线|transmission_line|chuan shu xian
谐振模式|resonant_mode|xie zhen mo shi
TE模|te_mode|t e mo
TM模|tm_mode|t m mo
TEM模|tem_mode|t e m mo
群速色散|group_velocity_dispersion|qun su se san
克尔效应|kerr_effect|ke er xiao ying
法拉第效应|faraday_effect|fa la di xiao ying
电磁质量|electromagnetic_mass|dian ci zhi liang
""",
    "thermo_stat_mech_terms.csv": """
温度|temperature|wen du
热量|quantity_of_heat|re liang
热容|heat_capacity|re rong
定压热容|heat_capacity_at_constant_pressure|ding ya re rong
定容热容|heat_capacity_at_constant_volume|ding rong re rong
比热容|specific_heat_capacity|bi re rong
热膨胀系数|thermal_expansion_coefficient|re peng zhang xi shu
等温压缩系数|isothermal_compressibility|deng wen ya suo xi shu
绝热压缩系数|adiabatic_compressibility|jue re ya suo xi shu
热力学势|thermodynamic_potential|re li xue shi
巨势|grand_potential|ju shi
自由能|free_energy|zi you neng
热力学恒等式|thermodynamic_identity|re li xue heng deng shi
欧拉关系|euler_relation|ou la guan xi
吉布斯杜亥姆关系|gibbs_duhem_relation|ji bu si du hai mu guan xi
焦耳汤姆孙效应|joule_thomson_effect|jiao er tang mu sun xiao ying
焦耳汤姆孙系数|joule_thomson_coefficient|jiao er tang mu sun xi shu
等焓过程|isenthalpic_process|deng han guo cheng
等熵过程|isentropic_process|deng shang guo cheng
多方过程|polytropic_process|duo fang guo cheng
焓变|enthalpy_change|han bian
熵变|entropy_change|shang bian
可用能|availability|ke yong neng
熵判据|entropy_criterion|shang pan ju
自由能判据|free_energy_criterion|zi you neng pan ju
稳定平衡条件|condition_of_stable_equilibrium|wen ding ping heng tiao jian
范德瓦尔斯气体|van_der_waals_gas|fan de wa er si qi ti
范德瓦尔斯方程|van_der_waals_equation|fan de wa er si fang cheng
麦克斯韦等面积法则|maxwell_equal_area_rule|mai ke si wei deng mian ji fa ze
一级相变|first_order_phase_transition|yi ji xiang bian
二级相变|second_order_phase_transition|er ji xiang bian
潜热|latent_heat|qian re
过冷|supercooling|guo leng
过热|superheating|guo re
三相点|triple_point|san xiang dian
临界温度|critical_temperature|lin jie wen du
临界压强|critical_pressure|lin jie ya qiang
热浴|heat_bath|re yu
系综平均|ensemble_average|xi zong ping jun
时间平均|time_average|shi jian ping jun
遍历假设|ergodic_hypothesis|bian li jia she
刘维尔方程|liouville_equation|liu wei er fang cheng
玻尔兹曼方程|boltzmann_equation|bo er zi man fang cheng
H定理|h_theorem|h ding li
分子混沌假设|molecular_chaos_assumption|fen zi hun dun jia she
碰撞积分|collision_integral|peng zhuang ji fen
输运系数|transport_coefficient|shu yun xi shu
扩散系数|diffusion_coefficient|kuo san xi shu
黏滞系数|viscosity_coefficient|nian zhi xi shu
热导率|thermal_conductivity|re dao lv
平均自由程|mean_free_path|ping jun zi you cheng
配分函数对数|logarithm_of_partition_function|pei fen han shu dui shu
单粒子配分函数|single_particle_partition_function|dan li zi pei fen han shu
玻色分布|bose_distribution|bo se fen bu
费米分布|fermi_distribution|fei mi fen bu
经典极限|classical_limit|jing dian ji xian
简并气体|degenerate_gas|jian bing qi ti
费米能级|fermi_energy_level|fei mi neng ji
费米温度|fermi_temperature|fei mi wen du
声子|phonon|sheng zi
晶格热容|lattice_heat_capacity|jing ge re rong
德拜温度|debye_temperature|de bai wen du
""",
    "quantum_mechanics_terms.csv": """
态函数|state_function|tai han shu
量子态|quantum_state|liang zi tai
态叠加|state_superposition|tai die jia
本征方程|eigenvalue_equation|ben zheng fang cheng
完备性关系|completeness_relation|wan bei xing guan xi
正交归一性|orthonormality|zheng jiao gui yi xing
概率流密度|probability_current_density|gai lv liu mi du
连续性方程|continuity_equation|lian xu xing fang cheng
定态|stationary_state|ding tai
束缚态|bound_state|shu fu tai
散射态|scattering_state|san she tai
自由粒子|free_particle|zi you li zi
无限深势阱|infinite_square_well|wu xian shen shi jing
有限深势阱|finite_square_well|you xian shen shi jing
势阶|potential_step|shi jie
势阱|potential_well|shi jing
一维谐振子|one_dimensional_harmonic_oscillator|yi wei xie zhen zi
零点能|zero_point_energy|ling dian neng
产生算符|creation_operator|chan sheng suan fu
湮灭算符|annihilation_operator|yan mie suan fu
数算符|number_operator|shu suan fu
轨道角动量|orbital_angular_momentum|gui dao jiao dong liang
角动量量子数|angular_momentum_quantum_number|jiao dong liang liang zi shu
磁量子数|magnetic_quantum_number|ci liang zi shu
自旋量子数|spin_quantum_number|zi xuan liang zi shu
总角动量|total_angular_momentum|zong jiao dong liang
角动量耦合|angular_momentum_coupling|jiao dong liang ou he
克莱布希戈登系数|clebsch_gordan_coefficient|ke lai bu xi ge deng xi shu
泡利不相容原理|pauli_exclusion_principle|pao li bu xiang rong yuan li
对称波函数|symmetric_wave_function|dui chen bo han shu
反对称波函数|antisymmetric_wave_function|fan dui chen bo han shu
二能级系统|two_level_system|er neng ji xi tong
塞曼效应|zeeman_effect|sai man xiao ying
斯塔克效应|stark_effect|si ta ke xiao ying
精细结构|fine_structure|jing xi jie gou
超精细结构|hyperfine_structure|chao jing xi jie gou
矩阵力学|matrix_mechanics|ju zhen li xue
波动力学|wave_mechanics|bo dong li xue
海森堡不确定性原理|heisenberg_uncertainty_principle|hai sen bao bu que ding xing yuan li
埃伦费斯特定理|ehrenfest_theorem|ai lun fei si te ding li
含时微扰论|time_dependent_perturbation_theory|han shi wei rao lun
费米黄金规则|fermi_golden_rule|fei mi huang jin gui ze
散射振幅|scattering_amplitude|san she zhen fu
相移|phase_shift|xiang yi
玻恩近似|born_approximation|bo en jin si
偏波展开|partial_wave_expansion|pian bo zhan kai
密度算符|density_operator|mi du suan fu
约化密度矩阵|reduced_density_matrix|yue hua mi du ju zhen
纠缠态|entangled_state|jiu chan tai
纯态密度矩阵|pure_state_density_matrix|chun tai mi du ju zhen
混态密度矩阵|mixed_state_density_matrix|hun tai mi du ju zhen
投影测量|projective_measurement|tou ying ce liang
量子数|quantum_number|liang zi shu
径向方程|radial_equation|jing xiang fang cheng
球谐函数|spherical_harmonic|qiu xie han shu
主量子数|principal_quantum_number|zhu liang zi shu
退相干|decoherence|tui xiang gan
""",
    "advanced_calculus_terms.csv": """
一元函数|function_of_one_variable|yi yuan han shu
有界函数|bounded_function|you jie han shu
单调函数|monotone_function|dan diao han shu
无穷小量|infinitesimal|wu qiong xiao liang
无穷大量|infinite_quantity|wu qiong da liang
等价无穷小|equivalent_infinitesimal|deng jia wu qiong xiao
夹逼定理|squeeze_theorem|jia bi ding li
单调有界定理|monotone_bounded_theorem|dan diao you jie ding li
柯西收敛准则|cauchy_convergence_criterion|ke xi shou lian zhun ze
左极限|left_limit|zuo ji xian
右极限|right_limit|you ji xian
间断点|discontinuity_point|jian duan dian
可去间断点|removable_discontinuity|ke qu jian duan dian
跳跃间断点|jump_discontinuity|tiao yue jian duan dian
导函数|derived_function|dao han shu
单侧导数|one_sided_derivative|dan ce dao shu
微分中值定理|mean_value_theorem|wei fen zhong zhi ding li
罗尔定理|rolle_theorem|luo er ding li
拉格朗日中值定理|lagrange_mean_value_theorem|la ge lang ri zhong zhi ding li
柯西中值定理|cauchy_mean_value_theorem|ke xi zhong zhi ding li
凹凸性|convexity_and_concavity|ao tu xing
拐点|inflection_point|guai dian
渐近线|asymptote|jian jin xian
有理函数积分|integration_of_rational_functions|you li han shu ji fen
换元积分法|integration_by_substitution|huan yuan ji fen fa
分部积分法|integration_by_parts|fen bu ji fen fa
绝对收敛|absolute_convergence|jue dui shou lian
条件收敛|conditional_convergence|tiao jian shou lian
一致收敛|uniform_convergence|yi zhi shou lian
点态收敛|pointwise_convergence|dian tai shou lian
函数项级数|series_of_functions|han shu xiang ji shu
阿贝尔定理|abel_theorem|a bei er ding li
狄利克雷判别法|dirichlet_test|di li ke lei pan bie fa
傅里叶系数|fourier_coefficient|fu li ye xi shu
偏微分|partial_differential|pian wei fen
二阶偏导数|second_order_partial_derivative|er jie pian dao shu
混合偏导数|mixed_partial_derivative|hun he pian dao shu
黑塞矩阵|hessian_matrix|hei sai ju zhen
局部极值|local_extremum|ju bu ji zhi
全局极值|global_extremum|quan ju ji zhi
驻点|stationary_point|zhu dian
鞍点|saddle_point|an dian
极坐标|polar_coordinate|ji zuo biao
柱坐标|cylindrical_coordinate|zhu zuo biao
球坐标|spherical_coordinate|qiu zuo biao
坐标变换|coordinate_transformation|zuo biao bian huan
变量替换|change_of_variables|bian liang ti huan
积分区域|region_of_integration|ji fen qu yu
第一型曲线积分|line_integral_of_first_kind|di yi xing qu xian ji fen
第二型曲线积分|line_integral_of_second_kind|di er xing qu xian ji fen
第一型曲面积分|surface_integral_of_first_kind|di yi xing qu mian ji fen
第二型曲面积分|surface_integral_of_second_kind|di er xing qu mian ji fen
保守场|conservative_field|bao shou chang
路径无关|path_independence|lu jing wu guan
通量|flux|tong liang
环量|circulation|huan liang
""",
    "linear_algebra_terms.csv": """
行向量|row_vector|hang xiang liang
列向量|column_vector|lie xiang liang
线性包|linear_span|xian xing bao
生成元|generator|sheng cheng yuan
基变换|change_of_basis|ji bian huan
过渡矩阵|transition_matrix|guo du ju zhen
坐标向量|coordinate_vector|zuo biao xiang liang
商空间|quotient_space|shang kong jian
直和|direct_sum|zhi he
张成空间|span_space|zhang cheng kong jian
线性泛函|linear_functional|xian xing fan han
对偶空间|dual_space|dui ou kong jian
对偶基|dual_basis|dui ou ji
双线性型|bilinear_form|shuang xian xing xing
对称双线性型|symmetric_bilinear_form|dui chen shuang xian xing xing
交替双线性型|alternating_bilinear_form|jiao ti shuang xian xing xing
外积|exterior_product|wai ji
张量积|tensor_product|zhang liang ji
线性算子|linear_operator|xian xing suan zi
不变子空间|invariant_subspace|bu bian zi kong jian
最小多项式|minimal_polynomial|zui xiao duo xiang shi
代数重数|algebraic_multiplicity|dai shu chong shu
几何重数|geometric_multiplicity|ji he chong shu
特征空间|eigenspace|te zheng kong jian
谱|spectrum|pu
谱半径|spectral_radius|pu ban jing
凯莱哈密顿定理|cayley_hamilton_theorem|kai lai ha mi dun ding li
实对称矩阵|real_symmetric_matrix|shi dui chen ju zhen
厄米矩阵|hermitian_matrix|e mi ju zhen
反对称矩阵|skew_symmetric_matrix|fan dui chen ju zhen
正规矩阵|normal_matrix|zheng gui ju zhen
幂等矩阵|idempotent_matrix|mi deng ju zhen
投影矩阵|projection_matrix|tou ying ju zhen
正交投影|orthogonal_projection|zheng jiao tou ying
酉空间|unitary_space|you kong jian
欧氏空间|euclidean_space|ou shi kong jian
距离|distance|ju li
范数|norm|fan shu
矩阵范数|matrix_norm|ju zhen fan shu
迹|trace|ji
合同矩阵|congruent_matrix|he tong ju zhen
惯性指数|index_of_inertia|guan xing zhi shu
惯性定理|law_of_inertia|guan xing ding li
半正定矩阵|positive_semidefinite_matrix|ban zheng ding ju zhen
负定矩阵|negative_definite_matrix|fu ding ju zhen
奇异值|singular_value|qi yi zhi
奇异值分解|singular_value_decomposition|qi yi zhi fen jie
QR分解|qr_decomposition|q r fen jie
LU分解|lu_decomposition|l u fen jie
矩阵分解|matrix_decomposition|ju zhen fen jie
克罗内克积|kronecker_product|ke luo nei ke ji
""",
    "complex_analysis_terms.csv": """
复变量|complex_variable|fu bian liang
复值函数|complex_valued_function|fu zhi han shu
区域|domain|qu yu
曲线|curve|qu xian
光滑曲线|smooth_curve|guang hua qu xian
简单闭曲线|simple_closed_curve|jian dan bi qu xian
约当曲线|jordan_curve|yue dang qu xian
约当引理|jordan_lemma|yue dang yin li
柯西定理|cauchy_theorem|ke xi ding li
柯西估计|cauchy_estimate|ke xi gu ji
刘维尔定理|liouville_theorem|liu wei er ding li
代数基本定理|fundamental_theorem_of_algebra|dai shu ji ben ding li
莫雷拉定理|morera_theorem|mo lei la ding li
解析分支|analytic_branch|jie xi fen zhi
对数函数|logarithm_function|dui shu han shu
指数函数|exponential_function|zhi shu han shu
三角函数|trigonometric_function|san jiao han shu
双曲函数|hyperbolic_function|shuang qu han shu
亚纯函数|meromorphic_function|ya chun han shu
整函数|entire_function|zheng han shu
有理函数|rational_function|you li han shu
孤立奇点|isolated_singularity|gu li qi dian
n阶极点|pole_of_order_n|n jie ji dian
无穷远点|point_at_infinity|wu qiong yuan dian
黎曼球面|riemann_sphere|li man qiu mian
留数计算|calculation_of_residues|liu shu ji suan
主部|principal_part|zhu bu
正则部|regular_part|zheng ze bu
解析部分|analytic_part|jie xi bu fen
辐角增量|increment_of_argument|fu jiao zeng liang
零点阶数|order_of_zero|ling dian jie shu
极点阶数|order_of_pole|ji dian jie shu
最大模定理|maximum_modulus_theorem|zui da mo ding li
开映射定理|open_mapping_theorem|kai ying she ding li
施瓦茨引理|schwarz_lemma|shi wa ci yin li
解析同构|analytic_isomorphism|jie xi tong gou
单位圆盘|unit_disk|dan wei yuan pan
上半平面|upper_half_plane|shang ban ping mian
共形等价|conformal_equivalence|gong xing deng jia
双解析映射|biholomorphic_mapping|shuang jie xi ying she
保角变换|angle_preserving_transformation|bao jiao bian huan
调和共轭|harmonic_conjugate|tiao he gong e
泊松积分公式|poisson_integral_formula|bo song ji fen gong shi
施瓦茨积分公式|schwarz_integral_formula|shi wa ci ji fen gong shi
解析函数唯一性定理|identity_theorem_for_analytic_functions|jie xi han shu wei yi xing ding li
米塔列夫勒定理|mittag_leffler_theorem|mi ta lie fu le ding li
魏尔斯特拉斯乘积定理|weierstrass_product_theorem|wei er si te la si cheng ji ding li
留数和|sum_of_residues|liu shu he
主值积分|principal_value_integral|zhu zhi ji fen
鞍点法|saddle_point_method|an dian fa
""",
    "mathematical_physics_equations_terms.csv": """
线性偏微分方程|linear_partial_differential_equation|xian xing pian wei fen fang cheng
非线性偏微分方程|nonlinear_partial_differential_equation|fei xian xing pian wei fen fang cheng
一阶偏微分方程|first_order_partial_differential_equation|yi jie pian wei fen fang cheng
二阶偏微分方程|second_order_partial_differential_equation|er jie pian wei fen fang cheng
常微分方程|ordinary_differential_equation|chang wei fen fang cheng
齐次方程|homogeneous_equation|qi ci fang cheng
非齐次方程|nonhomogeneous_equation|fei qi ci fang cheng
源项|source_term|yuan xiang
边界值问题|boundary_value_problem|bian jie zhi wen ti
柯西问题|cauchy_problem|ke xi wen ti
混合问题|mixed_problem|hun he wen ti
适定性|well_posedness|shi ding xing
解的唯一性|uniqueness_of_solution|jie de wei yi xing
解的稳定性|stability_of_solution|jie de wen ding xing
能量法|energy_method|neng liang fa
最大值原理|maximum_principle|zui da zhi yuan li
弱解|weak_solution|ruo jie
强解|strong_solution|qiang jie
广义函数|generalized_function|guang yi han shu
狄拉克函数|dirac_delta_function|di la ke han shu
阶跃函数|step_function|jie yue han shu
冲激函数|impulse_function|chong ji han shu
卷积|convolution|juan ji
傅里叶级数|fourier_series|fu li ye ji shu
正弦级数|sine_series|zheng xian ji shu
余弦级数|cosine_series|yu xian ji shu
本征函数展开|eigenfunction_expansion|ben zheng han shu zhan kai
分离常数|separation_constant|fen li chang shu
径向方程|radial_equation|jing xiang fang cheng
角向方程|angular_equation|jiao xiang fang cheng
柱坐标系|cylindrical_coordinate_system|zhu zuo biao xi
球坐标系|spherical_coordinate_system|qiu zuo biao xi
圆域|circular_domain|yuan yu
球域|spherical_domain|qiu yu
半空间|half_space|ban kong jian
无界区域|unbounded_domain|wu jie qu yu
边界算子|boundary_operator|bian jie suan zi
初值算子|initial_operator|chu zhi suan zi
拉普拉斯算子|laplace_operator|la pu la si suan zi
达朗贝尔算子|d_alembert_operator|da lang bei er suan zi
梯度算子|gradient_operator|ti du suan zi
散度算子|divergence_operator|san du suan zi
旋度算子|curl_operator|xuan du suan zi
正交曲线坐标|orthogonal_curvilinear_coordinate|zheng jiao qu xian zuo biao
拉梅系数|lame_coefficient|la mei xi shu
贝塞尔级数|bessel_series|bei sai er ji shu
第一类贝塞尔函数|bessel_function_of_first_kind|di yi lei bei sai er han shu
第二类贝塞尔函数|bessel_function_of_second_kind|di er lei bei sai er han shu
修正贝塞尔函数|modified_bessel_function|xiu zheng bei sai er han shu
球贝塞尔函数|spherical_bessel_function|qiu bei sai er han shu
埃尔米特方程|hermite_equation|ai er mi te fang cheng
埃尔米特多项式|hermite_polynomial|ai er mi te duo xiang shi
拉盖尔方程|laguerre_equation|la gai er fang cheng
拉盖尔多项式|laguerre_polynomial|la gai er duo xiang shi
格林公式|green_formula|ge lin gong shi
格林恒等式|green_identity|ge lin heng deng shi
泊松积分|poisson_integral|bo song ji fen
泊松核|poisson_kernel|bo song he
热核|heat_kernel|re he
""",
    "probability_theory_terms.csv": """
事件域|event_field|shi jian yu
概率空间|probability_space|gai lv kong jian
可测空间|measurable_space|ke ce kong jian
可测函数|measurable_function|ke ce han shu
概率测度|probability_measure|gai lv ce du
必然事件|certain_event|bi ran shi jian
不可能事件|impossible_event|bu ke neng shi jian
互斥事件|mutually_exclusive_events|hu chi shi jian
对立事件|complementary_event|dui li shi jian
事件独立性|independence_of_events|shi jian du li xing
条件独立|conditional_independence|tiao jian du li
随机向量|random_vector|sui ji xiang liang
随机序列|random_sequence|sui ji xu lie
分布律|probability_distribution|fen bu lv
生存函数|survival_function|sheng cun han shu
危险率函数|hazard_function|wei xian lv han shu
分位数|quantile|fen wei shu
中位数|median|zhong wei shu
众数|mode|zhong shu
累积分布函数|cumulative_distribution_function|lei ji fen bu han shu
矩母函数|moment_generating_function|ju mu han shu
概率母函数|probability_generating_function|gai lv mu han shu
拉普拉斯变换|laplace_transform|la pu la si bian huan
切比雪夫不等式|chebyshev_inequality|qie bi xue fu bu deng shi
马尔可夫不等式|markov_inequality|ma er ke fu bu deng shi
詹森不等式|jensen_inequality|zhan sen bu deng shi
伯努利试验|bernoulli_trial|bo nu li shi yan
超几何分布|hypergeometric_distribution|chao ji he fen bu
负二项分布|negative_binomial_distribution|fu er xiang fen bu
伽马分布|gamma_distribution|jia ma fen bu
贝塔分布|beta_distribution|bei ta fen bu
卡方分布|chi_square_distribution|ka fang fen bu
t分布|t_distribution|t fen bu
柯西分布|cauchy_distribution|ke xi fen bu
多项分布|multinomial_distribution|duo xiang fen bu
二维正态分布|bivariate_normal_distribution|er wei zheng tai fen bu
联合密度函数|joint_density_function|lian he mi du han shu
边缘密度函数|marginal_density_function|bian yuan mi du han shu
条件密度函数|conditional_density_function|tiao jian mi du han shu
独立随机变量|independent_random_variables|du li sui ji bian liang
同分布|identically_distributed|tong fen bu
独立同分布|independent_and_identically_distributed|du li tong fen bu
依概率收敛|convergence_in_probability|yi gai lv shou lian
几乎处处收敛|almost_sure_convergence|ji hu chu chu shou lian
依分布收敛|convergence_in_distribution|yi fen bu shou lian
均方收敛|mean_square_convergence|jun fang shou lian
弱大数定律|weak_law_of_large_numbers|ruo da shu ding lv
强大数定律|strong_law_of_large_numbers|qiang da shu ding lv
林德伯格条件|lindeberg_condition|lin de bo ge tiao jian
泊松过程|poisson_process|bo song guo cheng
更新过程|renewal_process|geng xin guo cheng
布朗运动|brownian_motion|bu lang yun dong
平稳过程|stationary_process|ping wen guo cheng
独立增量|independent_increment|du li zeng liang
转移概率|transition_probability|zhuan yi gai lv
转移矩阵|transition_matrix|zhuan yi ju zhen
吸收态|absorbing_state|xi shou tai
遍历性|ergodicity|bian li xing
""",
    "mathematical_statistics_terms.csv": """
参数空间|parameter_space|can shu kong jian
参数估计|parameter_estimation|can shu gu ji
充分统计量|sufficient_statistic|chong fen tong ji liang
完全统计量|complete_statistic|wan quan tong ji liang
最小充分统计量|minimal_sufficient_statistic|zui xiao chong fen tong ji liang
因子分解定理|factorization_theorem|yin zi fen jie ding li
拉奥布莱克韦尔定理|rao_blackwell_theorem|la ao bu lai ke wei er ding li
克拉默拉奥不等式|cramer_rao_inequality|ke la mo la ao bu deng shi
费希尔信息量|fisher_information|fei xi er xin xi liang
信息矩阵|information_matrix|xin xi ju zhen
相合估计|consistent_estimation|xiang he gu ji
渐近正态性|asymptotic_normality|jian jin zheng tai xing
充分性|sufficiency|chong fen xing
完备性|completeness|wan bei xing
贝叶斯估计|bayesian_estimation|bei ye si gu ji
先验分布|prior_distribution|xian yan fen bu
后验分布|posterior_distribution|hou yan fen bu
损失函数|loss_function|sun shi han shu
风险函数|risk_function|feng xian han shu
最小最大估计|minimax_estimation|zui xiao zui da gu ji
似然函数|likelihood_function|si ran han shu
对数似然函数|log_likelihood_function|dui shu si ran han shu
似然比检验|likelihood_ratio_test|si ran bi jian yan
广义似然比检验|generalized_likelihood_ratio_test|guang yi si ran bi jian yan
p值|p_value|p zhi
临界值|critical_value|lin jie zhi
双侧检验|two_sided_test|shuang ce jian yan
单侧检验|one_sided_test|dan ce jian yan
拟合优度检验|goodness_of_fit_test|ni he you du jian yan
独立性检验|test_of_independence|du li xing jian yan
正态性检验|normality_test|zheng tai xing jian yan
符号检验|sign_test|fu hao jian yan
秩和检验|rank_sum_test|zhi he jian yan
秩相关|rank_correlation|zhi xiang guan
协方差分析|analysis_of_covariance|xie fang cha fen xi
多元统计分析|multivariate_statistical_analysis|duo yuan tong ji fen xi
主成分分析|principal_component_analysis|zhu cheng fen fen xi
判别分析|discriminant_analysis|pan bie fen xi
聚类分析|cluster_analysis|ju lei fen xi
列联表|contingency_table|lie lian biao
相关系数|correlation_coefficient|xiang guan xi shu
偏相关系数|partial_correlation_coefficient|pian xiang guan xi shu
复相关系数|multiple_correlation_coefficient|fu xiang guan xi shu
残差|residual|can cha
残差平方和|residual_sum_of_squares|can cha ping fang he
回归系数|regression_coefficient|hui gui xi shu
决定系数|coefficient_of_determination|jue ding xi shu
置信带|confidence_band|zhi xin dai
预测区间|prediction_interval|yu ce qu jian
方差齐性|homogeneity_of_variance|fang cha qi xing
单因素方差分析|one_way_analysis_of_variance|dan yin su fang cha fen xi
双因素方差分析|two_way_analysis_of_variance|shuang yin su fang cha fen xi
实验设计|design_of_experiments|shi yan she ji
随机化|randomization|sui ji hua
""",
    "topology_terms.csv": """
集合族|family_of_sets|ji he zu
开覆盖|open_cover|kai fu gai
有限子覆盖|finite_subcover|you xian zi fu gai
闭覆盖|closed_cover|bi fu gai
覆盖维数|covering_dimension|fu gai wei shu
局部紧空间|locally_compact_space|ju bu jin kong jian
仿紧空间|paracompact_space|fang jin kong jian
连通分支|connected_component|lian tong fen zhi
道路分支|path_component|dao lu fen zhi
全不连通空间|totally_disconnected_space|quan bu lian tong kong jian
局部连通空间|locally_connected_space|ju bu lian tong kong jian
局部道路连通空间|locally_path_connected_space|ju bu dao lu lian tong kong jian
紧致化|compactification|jin zhi hua
一点紧致化|one_point_compactification|yi dian jin zhi hua
滤子|filter|lv zi
网|net|wang
序列紧|sequentially_compact|xu lie jin
极限点紧|limit_point_compact|ji xian dian jin
完全正则空间|completely_regular_space|wan quan zheng ze kong jian
提赫诺夫空间|tychonoff_space|ti he nuo fu kong jian
乌雷松引理|urysohn_lemma|wu lei song yin li
蒂茨扩张定理|tietze_extension_theorem|di ci kuo zhang ding li
分离公理|separation_axiom|fen li gong li
T0空间|t0_space|t ling kong jian
T1空间|t1_space|t yi kong jian
T2空间|t2_space|t er kong jian
可缩空间|contractible_space|ke suo kong jian
道路同伦|path_homotopy|dao lu tong lun
同伦等价|homotopy_equivalence|tong lun deng jia
强形变收缩|strong_deformation_retract|qiang xing bian shou suo
形变收缩|deformation_retract|xing bian shou suo
胞腔复形|cell_complex|bao qiang fu xing
CW复形|cw_complex|c w fu xing
单纯形|simplex|dan chun xing
链复形|chain_complex|lian fu xing
边缘算子|boundary_operator|bian yuan suan zi
闭链|cycle|bi lian
边界链|boundary_chain|bian jie lian
上同调群|cohomology_group|shang tong diao qun
欧拉示性数|euler_characteristic|ou la shi xing shu
流形|manifold|liu xing
拓扑流形|topological_manifold|tuo pu liu xing
n维流形|n_dimensional_manifold|n wei liu xing
图册|atlas|tu ce
坐标卡|coordinate_chart|zuo biao ka
局部欧氏性|local_euclidean_property|ju bu ou shi xing
可定向性|orientability|ke ding xiang xing
闭曲面|closed_surface|bi qu mian
亏格|genus|kui ge
莫比乌斯带|mobius_strip|mo bi wu si dai
环面|torus|huan mian
克莱因瓶|klein_bottle|ke lai yin ping
纤维丛|fiber_bundle|xian wei cong
覆盖映射|covering_map|fu gai ying she
提升|lifting|ti sheng
万有覆盖空间|universal_covering_space|wan you fu gai kong jian
基本群胚|fundamental_groupoid|ji ben qun pei
""",
    "group_theory_terms.csv": """
群运算|group_operation|qun yun suan
结合律|associative_law|jie he lv
生成子群|generated_subgroup|sheng cheng zi qun
生成集|generating_set|sheng cheng ji
换位子|commutator|huan wei zi
换位子群|commutator_subgroup|huan wei zi qun
导群|derived_group|dao qun
导列|derived_series|dao lie
上中心列|upper_central_series|shang zhong xin lie
下中心列|lower_central_series|xia zhong xin lie
幂零群|nilpotent_group|mi ling qun
自由群|free_group|zi you qun
自由阿贝尔群|free_abelian_group|zi you a bei er qun
群的表示|presentation_of_group|qun de biao shi
生成元与关系|generators_and_relations|sheng cheng yuan yu guan xi
直和|direct_sum|zhi he
内直积|internal_direct_product|nei zhi ji
外直积|external_direct_product|wai zhi ji
群同态基本定理|fundamental_theorem_of_group_homomorphism|qun tong tai ji ben ding li
第一同构定理|first_isomorphism_theorem|di yi tong gou ding li
第二同构定理|second_isomorphism_theorem|di er tong gou ding li
第三同构定理|third_isomorphism_theorem|di san tong gou ding li
自同构群|automorphism_group|zi tong gou qun
内自同构|inner_automorphism|nei zi tong gou
外自同构|outer_automorphism|wai zi tong gou
共轭作用|conjugation_action|gong e zuo yong
类方程|class_equation|lei fang cheng
p群|p_group|p qun
西罗子群|sylow_subgroup|xi luo zi qun
正规列|normal_series|zheng gui lie
组成列|composition_series|zu cheng lie
若尔当赫尔德定理|jordan_holder_theorem|ruo er dang he er de ding li
可解列|solvable_series|ke jie lie
换位子长度|commutator_length|huan wei zi chang du
单同态|monomorphism|dan tong tai
满同态|epimorphism|man tong tai
同态像|homomorphic_image|tong tai xiang
反同构|anti_isomorphism|fan tong gou
二面体群|dihedral_group|er mian ti qun
四元数群|quaternion_group|si yuan shu qun
克莱因四元群|klein_four_group|ke lai yin si yuan qun
矩阵群|matrix_group|ju zhen qun
一般线性群|general_linear_group|yi ban xian xing qun
特殊线性群|special_linear_group|te shu xian xing qun
正交群|orthogonal_group|zheng jiao qun
酉群|unitary_group|you qun
环的单位群|unit_group_of_ring|huan de dan wei qun
左作用|left_action|zuo zuo yong
右作用|right_action|you zuo yong
传递作用|transitive_action|chuan di zuo yong
忠实作用|faithful_action|zhong shi zuo yong
诱导表示|induced_representation|you dao biao shi
不可约表示|irreducible_representation|bu ke yue biao shi
正则表示|regular_representation|zheng ze biao shi
舒尔引理|schur_lemma|shu er yin li
""",
    "field_theory_terms.csv": """
域同态|field_homomorphism|yu tong tai
域同构|field_isomorphism|yu tong gou
嵌入|embedding|qian ru
代数闭域|algebraically_closed_field|dai shu bi yu
可分闭包|separable_closure|ke fen bi bao
正规闭包|normal_closure|zheng gui bi bao
纯不可分扩张|purely_inseparable_extension|chun bu ke fen kuo zhang
单扩张|simple_extension|dan kuo zhang
有限生成扩张|finitely_generated_extension|you xian sheng cheng kuo zhang
超越基|transcendence_basis|chao yue ji
超越次数|transcendence_degree|chao yue ci shu
代数无关|algebraic_independence|dai shu wu guan
分裂多项式|split_polynomial|fen lie duo xiang shi
可分多项式|separable_polynomial|ke fen duo xiang shi
不可约多项式|irreducible_polynomial|bu ke yue duo xiang shi
本原多项式|primitive_polynomial|ben yuan duo xiang shi
艾森斯坦判别法|eisenstein_criterion|ai sen si tan pan bie fa
有限域乘法群|multiplicative_group_of_finite_field|you xian yu cheng fa qun
弗罗贝尼乌斯自同构|frobenius_automorphism|fu luo bei ni wu si zi tong gou
完美域|perfect_field|wan mei yu
分圆多项式|cyclotomic_polynomial|fen yuan duo xiang shi
根式可解|solvable_by_radicals|gen shi ke jie
伽罗瓦闭包|galois_closure|jia luo wa bi bao
中间域|intermediate_field|zhong jian yu
基本定理|fundamental_theorem|ji ben ding li
正规基|normal_basis|zheng gui ji
正规基定理|normal_basis_theorem|zheng gui ji ding li
阿廷定理|artin_theorem|a ting ding li
库默扩张|kummer_extension|ku mo kuo zhang
阿贝尔扩张|abelian_extension|a bei er kuo zhang
循环扩张|cyclic_extension|xun huan kuo zhang
分歧|ramification|fen qi
未分歧扩张|unramified_extension|wei fen qi kuo zhang
完全分解|complete_splitting|wan quan fen jie
惯性群|inertia_group|guan xing qun
分解群|decomposition_group|fen jie qun
剩余域|residue_field|sheng yu yu
离散赋值|discrete_valuation|li san fu zhi
赋值环|valuation_ring|fu zhi huan
局部化|localization|ju bu hua
p进数域|p_adic_field|p jin shu yu
有理函数域|rational_function_field|you li han shu yu
形式幂级数域|field_of_formal_power_series|xing shi mi ji shu yu
代数函数域|algebraic_function_field|dai shu han shu yu
复数域|field_of_complex_numbers|fu shu yu
实数域|field_of_real_numbers|shi shu yu
有理数域|field_of_rational_numbers|you li shu yu
素子域|prime_subfield|su zi yu
域的特征|characteristic_of_field|yu de te zheng
""",
}


def parse_additions(text):
    rows = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split("|")
        if len(parts) != 3:
            raise ValueError(f"Bad row: {raw!r}")
        cn, english, spaced_pinyin = parts
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
