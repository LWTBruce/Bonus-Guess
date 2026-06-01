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


TABLES = {
    "theoretical_mechanics_terms.csv": """
理论力学|theoretical_mechanics|li lun li xue
质点|particle|zhi dian
质点系|system_of_particles|zhi dian xi
约束|constraint|yue shu
约束力|constraint_force|yue shu li
广义坐标|generalized_coordinate|guang yi zuo biao
广义速度|generalized_velocity|guang yi su du
广义动量|generalized_momentum|guang yi dong liang
广义力|generalized_force|guang yi li
自由度|degree_of_freedom|zi you du
虚位移|virtual_displacement|xu wei yi
虚功|virtual_work|xu gong
理想约束|ideal_constraint|li xiang yue shu
虚功原理|principle_of_virtual_work|xu gong yuan li
达朗贝尔原理|d_alembert_principle|da lang bei er yuan li
拉格朗日方程|lagrange_equation|la ge lang ri fang cheng
拉格朗日量|lagrangian|la ge lang ri liang
欧拉拉格朗日方程|euler_lagrange_equation|ou la la ge lang ri fang cheng
哈密顿原理|hamilton_principle|ha mi dun yuan li
变分原理|variational_principle|bian fen yuan li
作用量|action|zuo yong liang
最小作用量原理|principle_of_least_action|zui xiao zuo yong liang yuan li
哈密顿量|hamiltonian|ha mi dun liang
正则坐标|canonical_coordinate|zheng ze zuo biao
正则动量|canonical_momentum|zheng ze dong liang
正则方程|canonical_equation|zheng ze fang cheng
泊松括号|poisson_bracket|bo song kuo hao
守恒量|conserved_quantity|shou heng liang
循环坐标|cyclic_coordinate|xun huan zuo biao
正则变换|canonical_transformation|zheng ze bian huan
母函数|generating_function|mu han shu
哈密顿雅可比方程|hamilton_jacobi_equation|ha mi dun ya ke bi fang cheng
惯性张量|inertia_tensor|guan xing zhang liang
主轴|principal_axis|zhu zhou
主转动惯量|principal_moment_of_inertia|zhu zhuan dong guan liang
欧拉角|euler_angle|ou la jiao
欧拉方程|euler_equation|ou la fang cheng
刚体运动|rigid_body_motion|gang ti yun dong
定点转动|rotation_about_fixed_point|ding dian zhuan dong
陀螺|gyroscope|tuo luo
进动|precession|jin dong
章动|nutation|zhang dong
小振动|small_oscillation|xiao zhen dong
简正坐标|normal_coordinate|jian zheng zuo biao
简正频率|normal_frequency|jian zheng pin lv
简正模式|normal_mode|jian zheng mo shi
稳定平衡|stable_equilibrium|wen ding ping heng
不稳定平衡|unstable_equilibrium|bu wen ding ping heng
中心力|central_force|zhong xin li
中心力场|central_force_field|zhong xin li chang
有效势能|effective_potential_energy|you xiao shi neng
两体问题|two_body_problem|liang ti wen ti
约化质量|reduced_mass|yue hua zhi liang
开普勒问题|kepler_problem|kai pu le wen ti
散射|scattering|san she
散射角|scattering_angle|san she jiao
散射截面|scattering_cross_section|san she jie mian
拉普拉斯龙格楞次矢量|laplace_runge_lenz_vector|la pu la si long ge leng ci shi liang
""",
    "electrodynamics_terms.csv": """
电动力学|electrodynamics|dian dong li xue
电荷密度|charge_density|dian he mi du
电流密度|current_density|dian liu mi du
连续性方程|continuity_equation|lian xu xing fang cheng
电磁场|electromagnetic_field|dian ci chang
麦克斯韦方程组|maxwell_equations|mai ke si wei fang cheng zu
洛伦兹力|lorentz_force|luo lun zi li
标量势|scalar_potential|biao liang shi
矢量势|vector_potential|shi liang shi
规范变换|gauge_transformation|gui fan bian huan
库仑规范|coulomb_gauge|ku lun gui fan
洛伦兹规范|lorenz_gauge|luo lun zi gui fan
达朗贝尔方程|d_alembert_equation|da lang bei er fang cheng
电磁势|electromagnetic_potential|dian ci shi
推迟势|retarded_potential|tui chi shi
李纳维谢尔势|lienard_wiechert_potential|li na wei xie er shi
格林函数|green_function|ge lin han shu
电偶极子|electric_dipole|dian ou ji zi
磁偶极子|magnetic_dipole|ci ou ji zi
多极展开|multipole_expansion|duo ji zhan kai
电四极矩|electric_quadrupole_moment|dian si ji ju
磁矢势|magnetic_vector_potential|ci shi shi
电磁波|electromagnetic_wave|dian ci bo
平面波|plane_wave|ping mian bo
球面波|spherical_wave|qiu mian bo
波矢|wave_vector|bo shi
角频率|angular_frequency|jiao pin lv
偏振|polarization|pian zhen
横波|transverse_wave|heng bo
色散关系|dispersion_relation|se san guan xi
相速度|phase_velocity|xiang su du
群速度|group_velocity|qun su du
波导|waveguide|bo dao
谐振腔|resonant_cavity|xie zhen qiang
坡印廷矢量|poynting_vector|po yin ting shi liang
能流密度|energy_flux_density|neng liu mi du
动量密度|momentum_density|dong liang mi du
麦克斯韦应力张量|maxwell_stress_tensor|mai ke si wei ying li zhang liang
电磁场能量|energy_of_electromagnetic_field|dian ci chang neng liang
电磁场动量|momentum_of_electromagnetic_field|dian ci chang dong liang
辐射|radiation|fu she
偶极辐射|dipole_radiation|ou ji fu she
电偶极辐射|electric_dipole_radiation|dian ou ji fu she
磁偶极辐射|magnetic_dipole_radiation|ci ou ji fu she
辐射阻尼|radiation_damping|fu she zu ni
边界条件|boundary_condition|bian jie tiao jian
导体边界|conductor_boundary|dao ti bian jie
介质边界|dielectric_boundary|jie zhi bian jie
反射系数|reflection_coefficient|fan she xi shu
透射系数|transmission_coefficient|tou she xi shu
趋肤效应|skin_effect|qu fu xiao ying
等离子体频率|plasma_frequency|deng li zi ti pin lv
相对论电动力学|relativistic_electrodynamics|xiang dui lun dian dong li xue
四电流|four_current|si dian liu
四势|four_potential|si shi
电磁场张量|electromagnetic_field_tensor|dian ci chang zhang liang
洛伦兹协变性|lorentz_covariance|luo lun zi xie bian xing
达朗贝尔算符|d_alembert_operator|da lang bei er suan fu
""",
    "thermo_stat_mech_terms.csv": """
热力学与统计力学|thermodynamics_and_statistical_mechanics|re li xue yu tong ji li xue
热力学系统|thermodynamic_system|re li xue xi tong
孤立系统|isolated_system|gu li xi tong
封闭系统|closed_system|feng bi xi tong
开放系统|open_system|kai fang xi tong
状态参量|state_variable|zhuang tai can liang
状态函数|state_function|zhuang tai han shu
平衡态|equilibrium_state|ping heng tai
态方程|equation_of_state|tai fang cheng
内能|internal_energy|nei neng
焓|enthalpy|han
熵|entropy|shang
亥姆霍兹自由能|helmholtz_free_energy|hai mu huo zi zi you neng
吉布斯自由能|gibbs_free_energy|ji bu si zi you neng
化学势|chemical_potential|hua xue shi
热力学第一定律|first_law_of_thermodynamics|re li xue di yi ding lv
热力学第二定律|second_law_of_thermodynamics|re li xue di er ding lv
热力学第三定律|third_law_of_thermodynamics|re li xue di san ding lv
可逆过程|reversible_process|ke ni guo cheng
不可逆过程|irreversible_process|bu ke ni guo cheng
准静态过程|quasi_static_process|zhun jing tai guo cheng
卡诺循环|carnot_cycle|ka nuo xun huan
热效率|thermal_efficiency|re xiao lv
麦克斯韦关系|maxwell_relation|mai ke si wei guan xi
勒让德变换|legendre_transformation|le rang de bian huan
相平衡|phase_equilibrium|xiang ping heng
相图|phase_diagram|xiang tu
克拉珀龙方程|clapeyron_equation|ke la po long fang cheng
吉布斯相律|gibbs_phase_rule|ji bu si xiang lv
临界点|critical_point|lin jie dian
临界指数|critical_exponent|lin jie zhi shu
序参量|order_parameter|xu can liang
相变|phase_transition|xiang bian
配分函数|partition_function|pei fen han shu
微观态|microstate|wei guan tai
宏观态|macrostate|hong guan tai
统计权重|statistical_weight|tong ji quan zhong
态密度|density_of_states|tai mi du
能级简并度|degeneracy_of_energy_level|neng ji jian bing du
系综|ensemble|xi zong
微正则系综|microcanonical_ensemble|wei zheng ze xi zong
正则系综|canonical_ensemble|zheng ze xi zong
巨正则系综|grand_canonical_ensemble|ju zheng ze xi zong
玻尔兹曼分布|boltzmann_distribution|bo er zi man fen bu
麦克斯韦分布|maxwell_distribution|mai ke si wei fen bu
费米狄拉克分布|fermi_dirac_distribution|fei mi di la ke fen bu
玻色爱因斯坦分布|bose_einstein_distribution|bo se ai yin si tan fen bu
玻尔兹曼因子|boltzmann_factor|bo er zi man yin zi
平均值|mean_value|ping jun zhi
涨落|fluctuation|zhang luo
涨落耗散定理|fluctuation_dissipation_theorem|zhang luo hao san ding li
能均分定理|equipartition_theorem|neng jun fen ding li
玻色子|boson|bo se zi
费米子|fermion|fei mi zi
理想费米气体|ideal_fermi_gas|li xiang fei mi qi ti
理想玻色气体|ideal_bose_gas|li xiang bo se qi ti
玻色爱因斯坦凝聚|bose_einstein_condensation|bo se ai yin si tan ning ju
德拜模型|debye_model|de bai mo xing
爱因斯坦模型|einstein_model|ai yin si tan mo xing
""",
    "quantum_mechanics_terms.csv": """
量子力学|quantum_mechanics|liang zi li xue
波函数|wave_function|bo han shu
态矢量|state_vector|tai shi liang
希尔伯特空间|hilbert_space|xi er bo te kong jian
算符|operator|suan fu
线性算符|linear_operator|xian xing suan fu
厄米算符|hermitian_operator|e mi suan fu
幺正算符|unitary_operator|yao zheng suan fu
本征值|eigenvalue|ben zheng zhi
本征态|eigenstate|ben zheng tai
可观测量|observable|ke guan ce liang
对易关系|commutation_relation|dui yi guan xi
不确定性关系|uncertainty_relation|bu que ding xing guan xi
薛定谔方程|schrodinger_equation|xue ding e fang cheng
定态薛定谔方程|time_independent_schrodinger_equation|ding tai xue ding e fang cheng
哈密顿算符|hamiltonian_operator|ha mi dun suan fu
动量算符|momentum_operator|dong liang suan fu
角动量算符|angular_momentum_operator|jiao dong liang suan fu
升降算符|ladder_operator|sheng jiang suan fu
叠加原理|superposition_principle|die jia yuan li
概率幅|probability_amplitude|gai lv fu
概率密度|probability_density|gai lv mi du
归一化|normalization|gui yi hua
期望值|expectation_value|qi wang zhi
表象|representation|biao xiang
坐标表象|coordinate_representation|zuo biao biao xiang
动量表象|momentum_representation|dong liang biao xiang
狄拉克符号|dirac_notation|di la ke fu hao
左矢|bra_vector|zuo shi
右矢|ket_vector|you shi
投影算符|projection_operator|tou ying suan fu
密度矩阵|density_matrix|mi du ju zhen
纯态|pure_state|chun tai
混合态|mixed_state|hun he tai
量子测量|quantum_measurement|liang zi ce liang
波包|wave_packet|bo bao
隧穿效应|tunneling_effect|sui chuan xiao ying
方势阱|square_well|fang shi jing
势垒|potential_barrier|shi lei
量子谐振子|quantum_harmonic_oscillator|liang zi xie zhen zi
氢原子|hydrogen_atom|qing yuan zi
自旋|spin|zi xuan
泡利矩阵|pauli_matrix|pao li ju zhen
自旋轨道耦合|spin_orbit_coupling|zi xuan gui dao ou he
全同粒子|identical_particle|quan tong li zi
交换对称性|exchange_symmetry|jiao huan dui chen xing
玻色子|boson|bo se zi
费米子|fermion|fei mi zi
微扰论|perturbation_theory|wei rao lun
定态微扰论|time_independent_perturbation_theory|ding tai wei rao lun
简并微扰|degenerate_perturbation|jian bing wei rao
变分法|variational_method|bian fen fa
绝热近似|adiabatic_approximation|jue re jin si
WKB近似|wkb_approximation|w k b jin si
散射理论|scattering_theory|san she li lun
散射截面|scattering_cross_section|san she jie mian
选择定则|selection_rule|xuan ze ding ze
薛定谔绘景|schrodinger_picture|xue ding e hui jing
海森堡绘景|heisenberg_picture|hai sen bao hui jing
相互作用绘景|interaction_picture|xiang hu zuo yong hui jing
""",
    "advanced_calculus_terms.csv": """
高等微积分|advanced_calculus|gao deng wei ji fen
极限|limit|ji xian
数列极限|limit_of_sequence|shu lie ji xian
函数极限|limit_of_function|han shu ji xian
连续|continuity|lian xu
一致连续|uniform_continuity|yi zhi lian xu
导数|derivative|dao shu
微分|differential|wei fen
高阶导数|higher_order_derivative|gao jie dao shu
隐函数|implicit_function|yin han shu
反函数|inverse_function|fan han shu
泰勒公式|taylor_formula|tai le gong shi
麦克劳林公式|maclaurin_formula|mai ke lao lin gong shi
洛必达法则|l_hopital_rule|luo bi da fa ze
不定积分|indefinite_integral|bu ding ji fen
定积分|definite_integral|ding ji fen
反常积分|improper_integral|fan chang ji fen
黎曼积分|riemann_integral|li man ji fen
积分中值定理|mean_value_theorem_for_integrals|ji fen zhong zhi ding li
微积分基本定理|fundamental_theorem_of_calculus|wei ji fen ji ben ding li
无穷级数|infinite_series|wu qiong ji shu
幂级数|power_series|mi ji shu
傅里叶级数|fourier_series|fu li ye ji shu
收敛半径|radius_of_convergence|shou lian ban jing
逐项求导|termwise_differentiation|zhu xiang qiu dao
逐项积分|termwise_integration|zhu xiang ji fen
多元函数|multivariable_function|duo yuan han shu
偏导数|partial_derivative|pian dao shu
全微分|total_differential|quan wei fen
方向导数|directional_derivative|fang xiang dao shu
梯度|gradient|ti du
散度|divergence|san du
旋度|curl|xuan du
雅可比矩阵|jacobian_matrix|ya ke bi ju zhen
雅可比行列式|jacobian_determinant|ya ke bi hang lie shi
链式法则|chain_rule|lian shi fa ze
隐函数定理|implicit_function_theorem|yin han shu ding li
极值|extremum|ji zhi
条件极值|constrained_extremum|tiao jian ji zhi
拉格朗日乘数法|lagrange_multiplier_method|la ge lang ri cheng shu fa
重积分|multiple_integral|chong ji fen
二重积分|double_integral|er chong ji fen
三重积分|triple_integral|san chong ji fen
曲线积分|line_integral|qu xian ji fen
曲面积分|surface_integral|qu mian ji fen
格林公式|green_formula|ge lin gong shi
高斯公式|gauss_formula|gao si gong shi
斯托克斯公式|stokes_formula|si tuo ke si gong shi
""",
    "linear_algebra_terms.csv": """
线性代数|linear_algebra|xian xing dai shu
向量|vector|xiang liang
向量空间|vector_space|xiang liang kong jian
线性空间|linear_space|xian xing kong jian
子空间|subspace|zi kong jian
线性组合|linear_combination|xian xing zu he
线性相关|linear_dependence|xian xing xiang guan
线性无关|linear_independence|xian xing wu guan
基|basis|ji
维数|dimension|wei shu
坐标|coordinate|zuo biao
矩阵|matrix|ju zhen
方阵|square_matrix|fang zhen
单位矩阵|identity_matrix|dan wei ju zhen
零矩阵|zero_matrix|ling ju zhen
转置矩阵|transpose_matrix|zhuan zhi ju zhen
逆矩阵|inverse_matrix|ni ju zhen
伴随矩阵|adjugate_matrix|ban sui ju zhen
行列式|determinant|hang lie shi
余子式|minor|yu zi shi
代数余子式|cofactor|dai shu yu zi shi
矩阵的秩|rank_of_matrix|ju zhen de zhi
初等变换|elementary_operation|chu deng bian huan
阶梯形矩阵|row_echelon_matrix|jie ti xing ju zhen
线性方程组|system_of_linear_equations|xian xing fang cheng zu
齐次方程组|homogeneous_system|qi ci fang cheng zu
非齐次方程组|nonhomogeneous_system|fei qi ci fang cheng zu
解空间|solution_space|jie kong jian
线性映射|linear_map|xian xing ying she
线性变换|linear_transformation|xian xing bian huan
核|kernel|he
像|image|xiang
特征值|eigenvalue|te zheng zhi
特征向量|eigenvector|te zheng xiang liang
特征多项式|characteristic_polynomial|te zheng duo xiang shi
相似矩阵|similar_matrix|xiang si ju zhen
对角化|diagonalization|dui jiao hua
约当标准形|jordan_normal_form|yue dang biao zhun xing
内积|inner_product|nei ji
正交|orthogonality|zheng jiao
正交基|orthogonal_basis|zheng jiao ji
标准正交基|orthonormal_basis|biao zhun zheng jiao ji
施密特正交化|gram_schmidt_orthogonalization|shi mi te zheng jiao hua
正交矩阵|orthogonal_matrix|zheng jiao ju zhen
酉矩阵|unitary_matrix|you ju zhen
二次型|quadratic_form|er ci xing
正定矩阵|positive_definite_matrix|zheng ding ju zhen
""",
    "complex_analysis_terms.csv": """
复变函数|complex_analysis|fu bian han shu
复数|complex_number|fu shu
复平面|complex_plane|fu ping mian
实部|real_part|shi bu
虚部|imaginary_part|xu bu
模|modulus|mo
辐角|argument|fu jiao
主辐角|principal_argument|zhu fu jiao
共轭复数|complex_conjugate|gong e fu shu
复函数|complex_function|fu han shu
解析函数|analytic_function|jie xi han shu
全纯函数|holomorphic_function|quan chun han shu
调和函数|harmonic_function|tiao he han shu
柯西黎曼方程|cauchy_riemann_equations|ke xi li man fang cheng
复导数|complex_derivative|fu dao shu
幂级数|power_series|mi ji shu
泰勒级数|taylor_series|tai le ji shu
洛朗级数|laurent_series|luo lang ji shu
收敛圆|circle_of_convergence|shou lian yuan
奇点|singularity|qi dian
可去奇点|removable_singularity|ke qu qi dian
极点|pole|ji dian
本性奇点|essential_singularity|ben xing qi dian
留数|residue|liu shu
留数定理|residue_theorem|liu shu ding li
复积分|complex_integral|fu ji fen
围道积分|contour_integral|wei dao ji fen
柯西积分定理|cauchy_integral_theorem|ke xi ji fen ding li
柯西积分公式|cauchy_integral_formula|ke xi ji fen gong shi
最大模原理|maximum_modulus_principle|zui da mo yuan li
辐角原理|argument_principle|fu jiao yuan li
儒歇定理|rouche_theorem|ru xie ding li
保形映射|conformal_mapping|bao xing ying she
分式线性变换|fractional_linear_transformation|fen shi xian xing bian huan
莫比乌斯变换|mobius_transformation|mo bi wu si bian huan
解析延拓|analytic_continuation|jie xi yan tuo
单连通域|simply_connected_domain|dan lian tong yu
多连通域|multiply_connected_domain|duo lian tong yu
支点|branch_point|zhi dian
支割线|branch_cut|zhi ge xian
""",
    "mathematical_physics_equations_terms.csv": """
数学物理方程|equations_of_mathematical_physics|shu xue wu li fang cheng
偏微分方程|partial_differential_equation|pian wei fen fang cheng
定解问题|well_posed_problem|ding jie wen ti
初始条件|initial_condition|chu shi tiao jian
边界条件|boundary_condition|bian jie tiao jian
初边值问题|initial_boundary_value_problem|chu bian zhi wen ti
波动方程|wave_equation|bo dong fang cheng
热传导方程|heat_equation|re chuan dao fang cheng
拉普拉斯方程|laplace_equation|la pu la si fang cheng
泊松方程|poisson_equation|bo song fang cheng
亥姆霍兹方程|helmholtz_equation|hai mu huo zi fang cheng
薛定谔方程|schrodinger_equation|xue ding e fang cheng
双曲型方程|hyperbolic_equation|shuang qu xing fang cheng
抛物型方程|parabolic_equation|pao wu xing fang cheng
椭圆型方程|elliptic_equation|tuo yuan xing fang cheng
特征线|characteristic_curve|te zheng xian
行波解|traveling_wave_solution|xing bo jie
达朗贝尔公式|d_alembert_formula|da lang bei er gong shi
分离变量法|separation_of_variables|fen li bian liang fa
傅里叶方法|fourier_method|fu li ye fang fa
格林函数|green_function|ge lin han shu
基本解|fundamental_solution|ji ben jie
本征值问题|eigenvalue_problem|ben zheng zhi wen ti
斯图姆刘维尔问题|sturm_liouville_problem|si tu mu liu wei er wen ti
正交函数系|orthogonal_function_system|zheng jiao han shu xi
完备性|completeness|wan bei xing
狄利克雷条件|dirichlet_condition|di li ke lei tiao jian
狄利克雷边界条件|dirichlet_boundary_condition|di li ke lei bian jie tiao jian
诺伊曼边界条件|neumann_boundary_condition|nuo yi man bian jie tiao jian
罗宾边界条件|robin_boundary_condition|luo bin bian jie tiao jian
傅里叶变换|fourier_transform|fu li ye bian huan
拉普拉斯变换|laplace_transform|la pu la si bian huan
贝塞尔方程|bessel_equation|bei sai er fang cheng
贝塞尔函数|bessel_function|bei sai er han shu
勒让德方程|legendre_equation|le rang de fang cheng
勒让德多项式|legendre_polynomial|le rang de duo xiang shi
球谐函数|spherical_harmonic|qiu xie han shu
变分法|calculus_of_variations|bian fen fa
泛函|functional|fan han
欧拉方程|euler_equation|ou la fang cheng
""",
    "probability_theory_terms.csv": """
概率论|probability_theory|gai lv lun
随机试验|random_experiment|sui ji shi yan
样本空间|sample_space|yang ben kong jian
随机事件|random_event|sui ji shi jian
基本事件|elementary_event|ji ben shi jian
概率|probability|gai lv
古典概型|classical_probability_model|gu dian gai xing
几何概型|geometric_probability_model|ji he gai xing
条件概率|conditional_probability|tiao jian gai lv
全概率公式|law_of_total_probability|quan gai lv gong shi
贝叶斯公式|bayes_formula|bei ye si gong shi
独立事件|independent_events|du li shi jian
随机变量|random_variable|sui ji bian liang
离散型随机变量|discrete_random_variable|li san xing sui ji bian liang
连续型随机变量|continuous_random_variable|lian xu xing sui ji bian liang
分布函数|distribution_function|fen bu han shu
概率质量函数|probability_mass_function|gai lv zhi liang han shu
概率密度函数|probability_density_function|gai lv mi du han shu
数学期望|mathematical_expectation|shu xue qi wang
方差|variance|fang cha
标准差|standard_deviation|biao zhun cha
协方差|covariance|xie fang cha
相关系数|correlation_coefficient|xiang guan xi shu
矩|moment|ju
特征函数|characteristic_function|te zheng han shu
伯努利分布|bernoulli_distribution|bo nu li fen bu
二项分布|binomial_distribution|er xiang fen bu
几何分布|geometric_distribution|ji he fen bu
泊松分布|poisson_distribution|bo song fen bu
均匀分布|uniform_distribution|jun yun fen bu
指数分布|exponential_distribution|zhi shu fen bu
正态分布|normal_distribution|zheng tai fen bu
多维随机变量|multidimensional_random_variable|duo wei sui ji bian liang
联合分布|joint_distribution|lian he fen bu
边缘分布|marginal_distribution|bian yuan fen bu
条件分布|conditional_distribution|tiao jian fen bu
大数定律|law_of_large_numbers|da shu ding lv
中心极限定理|central_limit_theorem|zhong xin ji xian ding li
随机过程|stochastic_process|sui ji guo cheng
马尔可夫链|markov_chain|ma er ke fu lian
""",
    "mathematical_statistics_terms.csv": """
数理统计|mathematical_statistics|shu li tong ji
总体|population|zong ti
样本|sample|yang ben
样本容量|sample_size|yang ben rong liang
统计量|statistic|tong ji liang
样本均值|sample_mean|yang ben jun zhi
样本方差|sample_variance|yang ben fang cha
样本标准差|sample_standard_deviation|yang ben biao zhun cha
经验分布函数|empirical_distribution_function|jing yan fen bu han shu
抽样分布|sampling_distribution|chou yang fen bu
点估计|point_estimation|dian gu ji
估计量|estimator|gu ji liang
无偏性|unbiasedness|wu pian xing
有效性|efficiency|you xiao xing
一致性|consistency|yi zhi xing
最大似然估计|maximum_likelihood_estimation|zui da si ran gu ji
矩估计|method_of_moments|ju gu ji
区间估计|interval_estimation|qu jian gu ji
置信区间|confidence_interval|zhi xin qu jian
置信水平|confidence_level|zhi xin shui ping
假设检验|hypothesis_testing|jia she jian yan
原假设|null_hypothesis|yuan jia she
备择假设|alternative_hypothesis|bei ze jia she
显著性水平|significance_level|xian zhu xing shui ping
拒绝域|rejection_region|ju jue yu
检验统计量|test_statistic|jian yan tong ji liang
第一类错误|type_one_error|di yi lei cuo wu
第二类错误|type_two_error|di er lei cuo wu
功效函数|power_function|gong xiao han shu
正态总体|normal_population|zheng tai zong ti
卡方分布|chi_square_distribution|ka fang fen bu
t分布|t_distribution|t fen bu
F分布|f_distribution|f fen bu
方差分析|analysis_of_variance|fang cha fen xi
回归分析|regression_analysis|hui gui fen xi
线性回归|linear_regression|xian xing hui gui
最小二乘法|least_squares_method|zui xiao er cheng fa
相关分析|correlation_analysis|xiang guan fen xi
非参数检验|nonparametric_test|fei can shu jian yan
""",
    "topology_terms.csv": """
拓扑学|topology|tuo pu xue
拓扑空间|topological_space|tuo pu kong jian
拓扑|topology_structure|tuo pu
开集|open_set|kai ji
闭集|closed_set|bi ji
邻域|neighborhood|lin yu
内点|interior_point|nei dian
外点|exterior_point|wai dian
边界点|boundary_point|bian jie dian
聚点|accumulation_point|ju dian
闭包|closure|bi bao
内部|interior|nei bu
边界|boundary|bian jie
基|basis|ji
子基|subbasis|zi ji
连续映射|continuous_map|lian xu ying she
同胚|homeomorphism|tong pei
子空间拓扑|subspace_topology|zi kong jian tuo pu
积拓扑|product_topology|ji tuo pu
商拓扑|quotient_topology|shang tuo pu
连通空间|connected_space|lian tong kong jian
道路连通|path_connectedness|dao lu lian tong
紧空间|compact_space|jin kong jian
列紧性|sequential_compactness|lie jin xing
豪斯多夫空间|hausdorff_space|hao si duo fu kong jian
正则空间|regular_space|zheng ze kong jian
正规空间|normal_space|zheng gui kong jian
可数公理|countability_axiom|ke shu gong li
第一可数空间|first_countable_space|di yi ke shu kong jian
第二可数空间|second_countable_space|di er ke shu kong jian
度量空间|metric_space|du liang kong jian
完备空间|complete_space|wan bei kong jian
稠密集|dense_set|chou mi ji
可分空间|separable_space|ke fen kong jian
同伦|homotopy|tong lun
基本群|fundamental_group|ji ben qun
覆盖空间|covering_space|fu gai kong jian
单纯复形|simplicial_complex|dan chun fu xing
同调群|homology_group|tong diao qun
""",
    "group_theory_terms.csv": """
群论|group_theory|qun lun
群|group|qun
半群|semigroup|ban qun
幺半群|monoid|yao ban qun
子群|subgroup|zi qun
真子群|proper_subgroup|zhen zi qun
循环群|cyclic_group|xun huan qun
阿贝尔群|abelian_group|a bei er qun
有限群|finite_group|you xian qun
无限群|infinite_group|wu xian qun
群元|group_element|qun yuan
单位元|identity_element|dan wei yuan
逆元|inverse_element|ni yuan
阶|order|jie
元素的阶|order_of_element|yuan su de jie
陪集|coset|pei ji
左陪集|left_coset|zuo pei ji
右陪集|right_coset|you pei ji
正规子群|normal_subgroup|zheng gui zi qun
商群|quotient_group|shang qun
同态|homomorphism|tong tai
同构|isomorphism|tong gou
自同构|automorphism|zi tong gou
核|kernel|he
像|image|xiang
拉格朗日定理|lagrange_theorem|la ge lang ri ding li
群作用|group_action|qun zuo yong
轨道|orbit|gui dao
稳定子|stabilizer|wen ding zi
共轭类|conjugacy_class|gong e lei
中心|center|zhong xin
中心化子|centralizer|zhong xin hua zi
正规化子|normalizer|zheng gui hua zi
对称群|symmetric_group|dui chen qun
交错群|alternating_group|jiao cuo qun
置换|permutation|zhi huan
置换群|permutation_group|zhi huan qun
直积|direct_product|zhi ji
半直积|semidirect_product|ban zhi ji
西罗定理|sylow_theorem|xi luo ding li
可解群|solvable_group|ke jie qun
单群|simple_group|dan qun
表示|representation|biao shi
群表示|group_representation|qun biao shi
特征标|character|te zheng biao
""",
    "field_theory_terms.csv": """
场论|field_theory|chang lun
域|field|yu
子域|subfield|zi yu
素域|prime_field|su yu
扩域|field_extension|kuo yu
代数扩张|algebraic_extension|dai shu kuo zhang
超越扩张|transcendental_extension|chao yue kuo zhang
有限扩张|finite_extension|you xian kuo zhang
无限扩张|infinite_extension|wu xian kuo zhang
扩张次数|degree_of_extension|kuo zhang ci shu
代数元|algebraic_element|dai shu yuan
超越元|transcendental_element|chao yue yuan
最小多项式|minimal_polynomial|zui xiao duo xiang shi
共轭元|conjugate_element|gong e yuan
分裂域|splitting_field|fen lie yu
正规扩张|normal_extension|zheng gui kuo zhang
可分扩张|separable_extension|ke fen kuo zhang
不可分扩张|inseparable_extension|bu ke fen kuo zhang
伽罗瓦扩张|galois_extension|jia luo wa kuo zhang
伽罗瓦群|galois_group|jia luo wa qun
伽罗瓦对应|galois_correspondence|jia luo wa dui ying
固定域|fixed_field|gu ding yu
有限域|finite_field|you xian yu
代数闭包|algebraic_closure|dai shu bi bao
代数闭域|algebraically_closed_field|dai shu bi yu
特征|characteristic|te zheng
本原元|primitive_element|ben yuan yuan
本原元定理|primitive_element_theorem|ben yuan yuan ding li
迹|trace|ji
范数|norm|fan shu
迹映射|trace_map|ji ying she
范数映射|norm_map|fan shu ying she
根式扩张|radical_extension|gen shi kuo zhang
可解扩张|solvable_extension|ke jie kuo zhang
分圆域|cyclotomic_field|fen yuan yu
完备域|complete_field|wan bei yu
赋值|valuation|fu zhi
局部域|local_field|ju bu yu
全局域|global_field|quan ju yu
""",
}


def parse_rows(text):
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
    for filename, text in TABLES.items():
        rows = parse_rows(text)
        path = OUTPUT_DIRS[filename] / filename
        write_table(path, rows)
        print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
