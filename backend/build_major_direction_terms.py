import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS_DIR = ROOT / "words"
PHYSICS_MAJOR_DIR = WORDS_DIR / "物理" / "困难模式：四大方向"

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
    "原子分子光物理_terms.csv": """
原子分子光物理|atomic_molecular_and_optical_physics|yuan zi fen zi guang wu li
原子|atom|yuan zi
分子|molecule|fen zi
离子|ion|li zi
电子态|electronic_state|dian zi tai
振动态|vibrational_state|zhen dong tai
转动态|rotational_state|zhuan dong tai
能级|energy_level|neng ji
能级结构|energy_level_structure|neng ji jie gou
精细结构|fine_structure|jing xi jie gou
超精细结构|hyperfine_structure|chao jing xi jie gou
塞曼效应|zeeman_effect|sai man xiao ying
斯塔克效应|stark_effect|si ta ke xiao ying
兰德因子|lande_factor|lan de yin zi
量子数|quantum_number|liang zi shu
主量子数|principal_quantum_number|zhu liang zi shu
角量子数|azimuthal_quantum_number|jiao liang zi shu
磁量子数|magnetic_quantum_number|ci liang zi shu
自旋量子数|spin_quantum_number|zi xuan liang zi shu
选择定则|selection_rule|xuan ze ding ze
跃迁|transition|yue qian
电偶极跃迁|electric_dipole_transition|dian ou ji yue qian
磁偶极跃迁|magnetic_dipole_transition|ci ou ji yue qian
四极跃迁|quadrupole_transition|si ji yue qian
禁戒跃迁|forbidden_transition|jin jie yue qian
振子强度|oscillator_strength|zhen zi qiang du
寿命|lifetime|shou ming
谱线|spectral_line|pu xian
谱线宽度|spectral_linewidth|pu xian kuan du
自然线宽|natural_linewidth|zi ran xian kuan
多普勒展宽|doppler_broadening|duo pu le zhan kuan
碰撞展宽|collisional_broadening|peng zhuang zhan kuan
压力展宽|pressure_broadening|ya li zhan kuan
饱和展宽|saturation_broadening|bao he zhan kuan
吸收光谱|absorption_spectrum|xi shou guang pu
发射光谱|emission_spectrum|fa she guang pu
荧光光谱|fluorescence_spectrum|ying guang guang pu
拉曼光谱|raman_spectrum|la man guang pu
红外光谱|infrared_spectrum|hong wai guang pu
微波光谱|microwave_spectrum|wei bo guang pu
分子光谱|molecular_spectrum|fen zi guang pu
原子光谱|atomic_spectrum|yuan zi guang pu
光谱分辨率|spectral_resolution|guang pu fen bian lv
激光|laser|ji guang
激光器|laser_device|ji guang qi
受激辐射|stimulated_emission|shou ji fu she
自发辐射|spontaneous_emission|zi fa fu she
受激吸收|stimulated_absorption|shou ji xi shou
粒子数反转|population_inversion|li zi shu fan zhuan
光泵浦|optical_pumping|guang beng pu
谐振腔|resonant_cavity|xie zhen qiang
腔模|cavity_mode|qiang mo
纵模|longitudinal_mode|zong mo
横模|transverse_mode|heng mo
模式竞争|mode_competition|mo shi jing zheng
阈值条件|threshold_condition|yu zhi tiao jian
激光增益|laser_gain|ji guang zeng yi
增益介质|gain_medium|zeng yi jie zhi
饱和吸收|saturable_absorption|bao he xi shou
锁模|mode_locking|suo mo
调Q|q_switching|tiao q
脉冲激光|pulsed_laser|mai chong ji guang
连续激光|continuous_wave_laser|lian xu ji guang
光频梳|optical_frequency_comb|guang pin shu
非线性光学|nonlinear_optics|fei xian xing guang xue
二次谐波|second_harmonic_generation|er ci xie bo
三次谐波|third_harmonic_generation|san ci xie bo
参量下转换|parametric_down_conversion|can liang xia zhuan huan
四波混频|four_wave_mixing|si bo hun pin
拉比频率|rabi_frequency|la bi pin lv
拉比振荡|rabi_oscillation|la bi zhen dang
布洛赫球|bloch_sphere|bu luo he qiu
二能级系统|two_level_system|er neng ji xi tong
三能级系统|three_level_system|san neng ji xi tong
暗态|dark_state|an tai
亮态|bright_state|liang tai
相干布居囚禁|coherent_population_trapping|xiang gan bu ju qiu jin
电磁诱导透明|electromagnetically_induced_transparency|dian ci you dao tou ming
绝热快速通道|adiabatic_rapid_passage|jue re kuai su tong dao
拉曼跃迁|raman_transition|la man yue qian
受激拉曼散射|stimulated_raman_scattering|shou ji la man san she
布里渊散射|brillouin_scattering|bu li yuan san she
光俘获|optical_trapping|guang fu huo
偶极力|dipole_force|ou ji li
光偶极阱|optical_dipole_trap|guang ou ji jing
磁光阱|magneto_optical_trap|ci guang jing
磁阱|magnetic_trap|ci jing
离子阱|ion_trap|li zi jing
保罗阱|paul_trap|bao luo jing
彭宁阱|penning_trap|peng ning jing
激光冷却|laser_cooling|ji guang leng que
多普勒冷却|doppler_cooling|duo pu le leng que
西西弗斯冷却|sisyphus_cooling|xi xi fu si leng que
蒸发冷却|evaporative_cooling|zheng fa leng que
冷原子|cold_atom|leng yuan zi
超冷原子|ultracold_atom|chao leng yuan zi
玻色爱因斯坦凝聚|bose_einstein_condensation|bo se ai yin si tan ning ju
费米简并气体|degenerate_fermi_gas|fei mi jian bing qi ti
光晶格|optical_lattice|guang jing ge
原子钟|atomic_clock|yuan zi zhong
频率标准|frequency_standard|pin lv biao zhun
腔量子电动力学|cavity_quantum_electrodynamics|qiang liang zi dian dong li xue
强耦合|strong_coupling|qiang ou he
真空拉比分裂|vacuum_rabi_splitting|zhen kong la bi fen lie
单光子源|single_photon_source|dan guang zi yuan
里德堡原子|rydberg_atom|li de bao yuan zi
里德堡阻塞|rydberg_blockade|li de bao zu se
冷分子|cold_molecule|leng fen zi
光缔合|photoassociation|guang di he
飞秒光谱|femtosecond_spectroscopy|fei miao guang pu
阿秒物理|attosecond_physics|a miao wu li
高次谐波产生|high_harmonic_generation|gao ci xie bo chan sheng
""",
    "天体物理_terms.csv": """
天体物理|astrophysics|tian ti wu li
天体|celestial_body|tian ti
恒星|star|heng xing
行星|planet|xing xing
卫星|satellite|wei xing
小行星|asteroid|xiao xing xing
彗星|comet|hui xing
星云|nebula|xing yun
星团|star_cluster|xing tuan
球状星团|globular_cluster|qiu zhuang xing tuan
疏散星团|open_cluster|shu san xing tuan
星系|galaxy|xing xi
星系团|galaxy_cluster|xing xi tuan
超星系团|supercluster|chao xing xi tuan
星际介质|interstellar_medium|xing ji jie zhi
星际尘埃|interstellar_dust|xing ji chen ai
分子云|molecular_cloud|fen zi yun
电离氢区|hii_region|dian li qing qu
原恒星|protostar|yuan heng xing
主序星|main_sequence_star|zhu xu xing
红巨星|red_giant|hong ju xing
白矮星|white_dwarf|bai ai xing
中子星|neutron_star|zhong zi xing
脉冲星|pulsar|mai chong xing
黑洞|black_hole|hei dong
恒星形成|star_formation|heng xing xing cheng
恒星演化|stellar_evolution|heng xing yan hua
赫罗图|hertzsprung_russell_diagram|he luo tu
光度|luminosity|guang du
视星等|apparent_magnitude|shi xing deng
绝对星等|absolute_magnitude|jue dui xing deng
色指数|color_index|se zhi shu
有效温度|effective_temperature|you xiao wen du
金属丰度|metallicity|jin shu feng du
恒星风|stellar_wind|heng xing feng
吸积|accretion|xi ji
吸积盘|accretion_disk|xi ji pan
喷流|jet|pen liu
双星|binary_star|shuang xing
食双星|eclipsing_binary|shi shuang xing
造父变星|cepheid_variable|zao fu bian xing
变星|variable_star|bian xing
新星|nova|xin xing
超新星|supernova|chao xin xing
一型超新星|type_one_supernova|yi xing chao xin xing
二型超新星|type_two_supernova|er xing chao xin xing
超新星遗迹|supernova_remnant|chao xin xing yi ji
核合成|nucleosynthesis|he he cheng
氢燃烧|hydrogen_burning|qing ran shao
氦燃烧|helium_burning|hai ran shao
碳氮氧循环|cno_cycle|tan dan yang xun huan
质子质子链|proton_proton_chain|zhi zi zhi zi lian
钱德拉塞卡极限|chandrasekhar_limit|qian de la sai ka ji xian
奥本海默极限|oppenheimer_limit|ao ben hai mo ji xian
事件视界|event_horizon|shi jian shi jie
史瓦西半径|schwarzschild_radius|shi wa xi ban jing
引力红移|gravitational_redshift|yin li hong yi
引力透镜|gravitational_lens|yin li tou jing
弱透镜|weak_lensing|ruo tou jing
强透镜|strong_lensing|qiang tou jing
微引力透镜|microlensing|wei yin li tou jing
宇宙学|cosmology|yu zhou xue
宇宙微波背景|cosmic_microwave_background|yu zhou wei bo bei jing
哈勃定律|hubble_law|ha bo ding lv
哈勃常数|hubble_constant|ha bo chang shu
宇宙红移|cosmological_redshift|yu zhou hong yi
尺度因子|scale_factor|chi du yin zi
弗里德曼方程|friedmann_equation|fu li de man fang cheng
暗物质|dark_matter|an wu zhi
暗能量|dark_energy|an neng liang
宇宙常数|cosmological_constant|yu zhou chang shu
宇宙暴胀|cosmic_inflation|yu zhou bao zhang
大爆炸模型|big_bang_model|da bao zha mo xing
重子声波振荡|baryon_acoustic_oscillation|zhong zi sheng bo zhen dang
星系旋转曲线|galaxy_rotation_curve|xing xi xuan zhuan qu xian
活动星系核|active_galactic_nucleus|huo dong xing xi he
类星体|quasar|lei xing ti
射电星系|radio_galaxy|she dian xing xi
伽马射线暴|gamma_ray_burst|jia ma she xian bao
宇宙线|cosmic_ray|yu zhou xian
高能天体物理|high_energy_astrophysics|gao neng tian ti wu li
射电天文学|radio_astronomy|she dian tian wen xue
红外天文学|infrared_astronomy|hong wai tian wen xue
紫外天文学|ultraviolet_astronomy|zi wai tian wen xue
X射线天文学|x_ray_astronomy|x she xian tian wen xue
伽马射线天文学|gamma_ray_astronomy|jia ma she xian tian wen xue
光谱型|spectral_type|guang pu xing
谱线红移|spectral_line_redshift|pu xian hong yi
自行|proper_motion|zi xing
视差|parallax|shi cha
年周视差|annual_parallax|nian zhou shi cha
距离模数|distance_modulus|ju li mo shu
天文单位|astronomical_unit|tian wen dan wei
秒差距|parsec|miao cha ju
光年|light_year|guang nian
开普勒轨道|keplerian_orbit|kai pu le gui dao
轨道偏心率|orbital_eccentricity|gui dao pian xin lv
近星点|periastron|jin xing dian
远星点|apastron|yuan xing dian
潮汐力|tidal_force|chao xi li
洛希瓣|roche_lobe|luo xi ban
洛希极限|roche_limit|luo xi ji xian
维里定理|virial_theorem|wei li ding li
珍斯质量|jeans_mass|zhen si zhi liang
珍斯长度|jeans_length|zhen si chang du
""",
    "固体物理_terms.csv": """
固体物理|solid_state_physics|gu ti wu li
晶体|crystal|jing ti
非晶体|amorphous_solid|fei jing ti
晶格|lattice|jing ge
布拉菲格子|bravais_lattice|bu la fei ge zi
原胞|primitive_cell|yuan bao
晶胞|unit_cell|jing bao
基元|basis|ji yuan
晶格常数|lattice_constant|jing ge chang shu
晶向|crystal_direction|jing xiang
晶面|crystal_plane|jing mian
密勒指数|miller_index|mi le zhi shu
倒格子|reciprocal_lattice|dao ge zi
倒格矢|reciprocal_lattice_vector|dao ge shi
布里渊区|brillouin_zone|bu li yuan qu
第一布里渊区|first_brillouin_zone|di yi bu li yuan qu
维格纳塞茨胞|wigner_seitz_cell|wei ge na sai ci bao
点群|point_group|dian qun
空间群|space_group|kong jian qun
晶体对称性|crystal_symmetry|jing ti dui chen xing
平移对称性|translational_symmetry|ping yi dui chen xing
布洛赫定理|bloch_theorem|bu luo he ding li
布洛赫波|bloch_wave|bu luo he bo
能带|energy_band|neng dai
能隙|band_gap|neng xi
价带|valence_band|jia dai
导带|conduction_band|dao dai
费米能级|fermi_level|fei mi neng ji
费米面|fermi_surface|fei mi mian
态密度|density_of_states|tai mi du
有效质量|effective_mass|you xiao zhi liang
近自由电子模型|nearly_free_electron_model|jin zi you dian zi mo xing
紧束缚模型|tight_binding_model|jin shu fu mo xing
自由电子气|free_electron_gas|zi you dian zi qi
费米气体|fermi_gas|fei mi qi ti
金属|metal|jin shu
绝缘体|insulator|jue yuan ti
半导体|semiconductor|ban dao ti
本征半导体|intrinsic_semiconductor|ben zheng ban dao ti
杂质半导体|extrinsic_semiconductor|za zhi ban dao ti
施主|donor|shi zhu
受主|acceptor|shou zhu
n型半导体|n_type_semiconductor|n xing ban dao ti
p型半导体|p_type_semiconductor|p xing ban dao ti
载流子|charge_carrier|zai liu zi
电子空穴对|electron_hole_pair|dian zi kong xue dui
迁移率|mobility|qian yi lv
电导率|conductivity|dian dao lv
霍尔效应|hall_effect|huo er xiao ying
量子霍尔效应|quantum_hall_effect|liang zi huo er xiao ying
整数量子霍尔效应|integer_quantum_hall_effect|zheng shu liang zi huo er xiao ying
pn结|pn_junction|p n jie
耗尽层|depletion_layer|hao jin ceng
晶格振动|lattice_vibration|jing ge zhen dong
声子|phonon|sheng zi
声学支|acoustic_branch|sheng xue zhi
光学支|optical_branch|guang xue zhi
声子色散|phonon_dispersion|sheng zi se san
德拜模型|debye_model|de bai mo xing
爱因斯坦模型|einstein_model|ai yin si tan mo xing
德拜温度|debye_temperature|de bai wen du
晶格热容|lattice_heat_capacity|jing ge re rong
热导率|thermal_conductivity|re dao lv
电子热容|electronic_heat_capacity|dian zi re rong
晶格缺陷|lattice_defect|jing ge que xian
点缺陷|point_defect|dian que xian
空位|vacancy|kong wei
间隙原子|interstitial_atom|jian xi yuan zi
替位原子|substitutional_atom|ti wei yuan zi
位错|dislocation|wei cuo
刃位错|edge_dislocation|ren wei cuo
螺位错|screw_dislocation|luo wei cuo
晶界|grain_boundary|jing jie
表面态|surface_state|biao mian tai
磁性|magnetism|ci xing
抗磁性|diamagnetism|kang ci xing
顺磁性|paramagnetism|shun ci xing
铁磁性|ferromagnetism|tie ci xing
反铁磁性|antiferromagnetism|fan tie ci xing
亚铁磁性|ferrimagnetism|ya tie ci xing
交换相互作用|exchange_interaction|jiao huan xiang hu zuo yong
磁畴|magnetic_domain|ci chou
畴壁|domain_wall|chou bi
居里温度|curie_temperature|ju li wen du
奈尔温度|neel_temperature|nai er wen du
自旋波|spin_wave|zi xuan bo
磁振子|magnon|ci zhen zi
超导|superconductivity|chao dao
超导体|superconductor|chao dao ti
临界温度|critical_temperature|lin jie wen du
临界磁场|critical_magnetic_field|lin jie ci chang
迈斯纳效应|meissner_effect|mai si na xiao ying
库珀对|cooper_pair|ku po dui
BCS理论|bcs_theory|b c s li lun
能隙函数|gap_function|neng xi han shu
约瑟夫森效应|josephson_effect|yue se fu sen xiao ying
第一类超导体|type_one_superconductor|di yi lei chao dao ti
第二类超导体|type_two_superconductor|di er lei chao dao ti
磁通涡旋|flux_vortex|ci tong wo xuan
拓扑绝缘体|topological_insulator|tuo pu jue yuan ti
狄拉克点|dirac_point|di la ke dian
石墨烯|graphene|shi mo xi
量子阱|quantum_well|liang zi jing
超晶格|superlattice|chao jing ge
""",
    "核物理与粒子物理_terms.csv": """
核物理与粒子物理|nuclear_and_particle_physics|he wu li yu li zi wu li
原子核|atomic_nucleus|yuan zi he
核子|nucleon|he zi
质子|proton|zhi zi
中子|neutron|zhong zi
核素|nuclide|he su
同位素|isotope|tong wei su
同量异位素|isobar|tong liang yi wei su
同中子异位素|isotone|tong zhong zi yi wei su
质量数|mass_number|zhi liang shu
原子序数|atomic_number|yuan zi xu shu
中子数|neutron_number|zhong zi shu
核半径|nuclear_radius|he ban jing
核密度|nuclear_density|he mi du
结合能|binding_energy|jie he neng
比结合能|binding_energy_per_nucleon|bi jie he neng
质量亏损|mass_defect|zhi liang kui sun
液滴模型|liquid_drop_model|ye di mo xing
壳模型|shell_model|ke mo xing
集体模型|collective_model|ji ti mo xing
费米气体模型|fermi_gas_model|fei mi qi ti mo xing
核力|nuclear_force|he li
强相互作用|strong_interaction|qiang xiang hu zuo yong
弱相互作用|weak_interaction|ruo xiang hu zuo yong
电磁相互作用|electromagnetic_interaction|dian ci xiang hu zuo yong
引力相互作用|gravitational_interaction|yin li xiang hu zuo yong
核自旋|nuclear_spin|he zi xuan
核磁矩|nuclear_magnetic_moment|he ci ju
核电四极矩|nuclear_electric_quadrupole_moment|he dian si ji ju
宇称|parity|yu cheng
同位旋|isospin|tong wei xuan
放射性|radioactivity|fang she xing
衰变|decay|shuai bian
α衰变|alpha_decay|a er fa shuai bian
β衰变|beta_decay|bei ta shuai bian
γ衰变|gamma_decay|ga ma shuai bian
电子俘获|electron_capture|dian zi fu huo
内转换|internal_conversion|nei zhuan huan
半衰期|half_life|ban shuai qi
平均寿命|mean_lifetime|ping jun shou ming
衰变常数|decay_constant|shuai bian chang shu
活度|activity|huo du
衰变链|decay_chain|shuai bian lian
核反应|nuclear_reaction|he fan ying
反应截面|reaction_cross_section|fan ying jie mian
散射截面|scattering_cross_section|san she jie mian
微分截面|differential_cross_section|wei fen jie mian
卢瑟福散射|rutherford_scattering|lu se fu san she
弹性散射|elastic_scattering|tan xing san she
非弹性散射|inelastic_scattering|fei tan xing san she
复合核|compound_nucleus|fu he he
直接反应|direct_reaction|zhi jie fan ying
共振反应|resonant_reaction|gong zhen fan ying
核裂变|nuclear_fission|he lie bian
核聚变|nuclear_fusion|he ju bian
链式反应|chain_reaction|lian shi fan ying
临界质量|critical_mass|lin jie zhi liang
反应堆|reactor|fan ying dui
中子慢化|neutron_moderation|zhong zi man hua
热中子|thermal_neutron|re zhong zi
快中子|fast_neutron|kuai zhong zi
截面|cross_section|jie mian
靶核|target_nucleus|ba he
入射粒子|incident_particle|ru she li zi
探测器|detector|tan ce qi
闪烁计数器|scintillation_counter|shan shuo ji shu qi
盖革计数器|geiger_counter|gai ge ji shu qi
云室|cloud_chamber|yun shi
气泡室|bubble_chamber|qi pao shi
半导体探测器|semiconductor_detector|ban dao ti tan ce qi
切伦科夫探测器|cherenkov_detector|qie lun ke fu tan ce qi
粒子物理|particle_physics|li zi wu li
基本粒子|elementary_particle|ji ben li zi
标准模型|standard_model|biao zhun mo xing
费米子|fermion|fei mi zi
玻色子|boson|bo se zi
夸克|quark|kua ke
轻子|lepton|qing zi
强子|hadron|qiang zi
重子|baryon|zhong zi
介子|meson|jie zi
胶子|gluon|jiao zi
光子|photon|guang zi
W玻色子|w_boson|w bo se zi
Z玻色子|z_boson|z bo se zi
希格斯玻色子|higgs_boson|xi ge si bo se zi
电子|electron|dian zi
μ子|muon|miu zi
τ子|tauon|tao zi
中微子|neutrino|zhong wei zi
电子中微子|electron_neutrino|dian zi zhong wei zi
μ子中微子|muon_neutrino|miu zi zhong wei zi
τ子中微子|tau_neutrino|tao zi zhong wei zi
上夸克|up_quark|shang kua ke
下夸克|down_quark|xia kua ke
奇异夸克|strange_quark|qi yi kua ke
粲夸克|charm_quark|can kua ke
底夸克|bottom_quark|di kua ke
顶夸克|top_quark|ding kua ke
反粒子|antiparticle|fan li zi
反物质|antimatter|fan wu zhi
味|flavor|wei
色荷|color_charge|se he
禁闭|confinement|jin bi
渐近自由|asymptotic_freedom|jian jin zi you
弱混合角|weak_mixing_angle|ruo hun he jiao
宇称破坏|parity_violation|yu cheng po huai
CP破坏|cp_violation|c p po huai
中微子振荡|neutrino_oscillation|zhong wei zi zhen dang
希格斯机制|higgs_mechanism|xi ge si ji zhi
费曼图|feynman_diagram|fei man tu
散射振幅|scattering_amplitude|san she zhen fu
衰变宽度|decay_width|shuai bian kuan du
分支比|branching_ratio|fen zhi bi
""",
    "广义相对论_terms.csv": """
广义相对论|general_relativity|guang yi xiang dui lun
等效原理|equivalence_principle|deng xiao yuan li
强等效原理|strong_equivalence_principle|qiang deng xiao yuan li
弱等效原理|weak_equivalence_principle|ruo deng xiao yuan li
广义协变性|general_covariance|guang yi xie bian xing
时空|spacetime|shi kong
流形|manifold|liu xing
黎曼流形|riemannian_manifold|li man liu xing
洛伦兹流形|lorentzian_manifold|luo lun zi liu xing
度规|metric|du gui
度规张量|metric_tensor|du gui zhang liang
逆度规|inverse_metric|ni du gui
线元|line_element|xian yuan
固有时|proper_time|gu you shi
固有距离|proper_distance|gu you ju li
四维速度|four_velocity|si wei su du
四维加速度|four_acceleration|si wei jia su du
四动量|four_momentum|si dong liang
测地线|geodesic|ce di xian
测地线方程|geodesic_equation|ce di xian fang cheng
仿射参数|affine_parameter|fang she can shu
克氏符|christoffel_symbol|ke shi fu
联络|connection|lian luo
协变导数|covariant_derivative|xie bian dao shu
平行移动|parallel_transport|ping xing yi dong
曲率|curvature|qu lv
黎曼张量|riemann_tensor|li man zhang liang
里奇张量|ricci_tensor|li qi zhang liang
里奇标量|ricci_scalar|li qi biao liang
爱因斯坦张量|einstein_tensor|ai yin si tan zhang liang
能量动量张量|stress_energy_tensor|neng liang dong liang zhang liang
爱因斯坦场方程|einstein_field_equation|ai yin si tan chang fang cheng
宇宙常数|cosmological_constant|yu zhou chang shu
真空场方程|vacuum_field_equation|zhen kong chang fang cheng
测地偏离|geodesic_deviation|ce di pian li
潮汐力|tidal_force|chao xi li
杀矢量|killing_vector|sha shi liang
守恒流|conserved_current|shou heng liu
局域惯性系|local_inertial_frame|ju yu guan xing xi
局域洛伦兹系|local_lorentz_frame|ju yu luo lun zi xi
弱场近似|weak_field_approximation|ruo chang jin si
牛顿极限|newtonian_limit|niu dun ji xian
后牛顿近似|post_newtonian_approximation|hou niu dun jin si
史瓦西解|schwarzschild_solution|shi wa xi jie
史瓦西度规|schwarzschild_metric|shi wa xi du gui
史瓦西半径|schwarzschild_radius|shi wa xi ban jing
事件视界|event_horizon|shi jian shi jie
视界|horizon|shi jie
黑洞|black_hole|hei dong
克尔黑洞|kerr_black_hole|ke er hei dong
克尔度规|kerr_metric|ke er du gui
克尔纽曼度规|kerr_newman_metric|ke er niu man du gui
雷斯纳诺斯特朗度规|reissner_nordstrom_metric|lei si na nuo si te lang du gui
引力红移|gravitational_redshift|yin li hong yi
光线偏折|deflection_of_light|guang xian pian zhe
水星近日点进动|perihelion_precession_of_mercury|shui xing jin ri dian jin dong
夏皮罗时延|shapiro_time_delay|xia pi luo shi yan
引力透镜|gravitational_lensing|yin li tou jing
爱因斯坦环|einstein_ring|ai yin si tan huan
引力波|gravitational_wave|yin li bo
横向无迹规范|transverse_traceless_gauge|heng xiang wu ji gui fan
四极辐射|quadrupole_radiation|si ji fu she
引力波源|gravitational_wave_source|yin li bo yuan
双黑洞并合|binary_black_hole_merger|shuang hei dong bing he
双中子星并合|binary_neutron_star_merger|shuang zhong zi xing bing he
弗里德曼度规|friedmann_metric|fu li de man du gui
罗伯逊沃克度规|robertson_walker_metric|luo bo xun wo ke du gui
弗里德曼方程|friedmann_equation|fu li de man fang cheng
尺度因子|scale_factor|chi du yin zi
哈勃参数|hubble_parameter|ha bo can shu
宇宙红移|cosmological_redshift|yu zhou hong yi
共动坐标|comoving_coordinate|gong dong zuo biao
宇宙学原理|cosmological_principle|yu zhou xue yuan li
均匀性|homogeneity|jun yun xing
各向同性|isotropy|ge xiang tong xing
临界密度|critical_density|lin jie mi du
密度参数|density_parameter|mi du can shu
暗能量|dark_energy|an neng liang
暗物质|dark_matter|an wu zhi
宇宙微波背景|cosmic_microwave_background|yu zhou wei bo bei jing
德西特时空|de_sitter_spacetime|de xi te shi kong
反德西特时空|anti_de_sitter_spacetime|fan de xi te shi kong
奇点|singularity|qi dian
奇点定理|singularity_theorem|qi dian ding li
彭罗斯图|penrose_diagram|peng luo si tu
克鲁斯卡尔坐标|kruskal_coordinate|ke lu si ka er zuo biao
爱丁顿芬克尔斯坦坐标|eddington_finkelstein_coordinate|ai ding dun fen ke er si tan zuo biao
雷恰杜里方程|raychaudhuri_equation|lei qia du li fang cheng
能量条件|energy_condition|neng liang tiao jian
弱能量条件|weak_energy_condition|ruo neng liang tiao jian
强能量条件|strong_energy_condition|qiang neng liang tiao jian
零能量条件|null_energy_condition|ling neng liang tiao jian
正交标架|orthonormal_frame|zheng jiao biao jia
四脚场|tetrad_field|si jiao chang
挠率|torsion|nao lv
ADM分解|adm_decomposition|a d m fen jie
空间度规|spatial_metric|kong jian du gui
拉普斯函数|lapse_function|la pu si han shu
位移矢量|shift_vector|wei yi shi liang
外曲率|extrinsic_curvature|wai qu lv
初值问题|initial_value_problem|chu zhi wen ti
哈密顿约束|hamiltonian_constraint|ha mi dun yue shu
动量约束|momentum_constraint|dong liang yue shu
约束方程|constraint_equation|yue shu fang cheng
旋量联络|spin_connection|xuan liang lian luo
""",
    "量子场论_terms.csv": """
量子场论|quantum_field_theory|liang zi chang lun
场|field|chang
经典场|classical_field|jing dian chang
量子场|quantum_field|liang zi chang
标量场|scalar_field|biao liang chang
实标量场|real_scalar_field|shi biao liang chang
复标量场|complex_scalar_field|fu biao liang chang
旋量场|spinor_field|xuan liang chang
矢量场|vector_field|shi liang chang
规范场|gauge_field|gui fan chang
拉格朗日密度|lagrangian_density|la ge lang ri mi du
作用量|action|zuo yong liang
欧拉拉格朗日方程|euler_lagrange_equation|ou la la ge lang ri fang cheng
正则量子化|canonical_quantization|zheng ze liang zi hua
路径积分|path_integral|lu jing ji fen
泛函积分|functional_integral|fan han ji fen
生成泛函|generating_functional|sheng cheng fan han
配分泛函|partition_functional|pei fen fan han
源场|source_field|yuan chang
传播子|propagator|chuan bo zi
费曼传播子|feynman_propagator|fei man chuan bo zi
格林函数|green_function|ge lin han shu
n点函数|n_point_function|n dian han shu
关联函数|correlation_function|guan lian han shu
时间有序乘积|time_ordered_product|shi jian you xu cheng ji
正规乘积|normal_product|zheng gui cheng ji
威克定理|wick_theorem|wei ke ding li
费曼图|feynman_diagram|fei man tu
费曼规则|feynman_rule|fei man gui ze
顶角|vertex|ding jiao
内线|internal_line|nei xian
外线|external_line|wai xian
圈图|loop_diagram|quan tu
树图|tree_diagram|shu tu
散射矩阵|scattering_matrix|san she ju zhen
散射振幅|scattering_amplitude|san she zhen fu
截面|cross_section|jie mian
衰变宽度|decay_width|shuai bian kuan du
LSZ约化公式|lsz_reduction_formula|l s z yue hua gong shi
克莱因戈登方程|klein_gordon_equation|ke lai yin ge deng fang cheng
狄拉克方程|dirac_equation|di la ke fang cheng
旋量|spinor|xuan liang
狄拉克旋量|dirac_spinor|di la ke xuan liang
外尔旋量|weyl_spinor|wai er xuan liang
马约拉纳旋量|majorana_spinor|ma yue la na xuan liang
伽马矩阵|gamma_matrix|ga ma ju zhen
反粒子|antiparticle|fan li zi
真空态|vacuum_state|zhen kong tai
粒子产生算符|particle_creation_operator|li zi chan sheng suan fu
粒子湮灭算符|particle_annihilation_operator|li zi yan mie suan fu
费米场|fermi_field|fei mi chang
玻色场|bose_field|bo se chang
对易子|commutator|dui yi zi
反对易子|anticommutator|fan dui yi zi
规范对称性|gauge_symmetry|gui fan dui chen xing
整体对称性|global_symmetry|zheng ti dui chen xing
局域对称性|local_symmetry|ju yu dui chen xing
诺特定理|noether_theorem|nuo te ding li
诺特流|noether_current|nuo te liu
守恒荷|conserved_charge|shou heng he
阿贝尔规范理论|abelian_gauge_theory|a bei er gui fan li lun
非阿贝尔规范理论|nonabelian_gauge_theory|fei a bei er gui fan li lun
杨米尔斯理论|yang_mills_theory|yang mi er si li lun
规范固定|gauge_fixing|gui fan gu ding
法捷耶夫波波夫鬼场|faddeev_popov_ghost|fa jie ye fu bo bo fu gui chang
BRST对称性|brst_symmetry|b r s t dui chen xing
量子电动力学|quantum_electrodynamics|liang zi dian dong li xue
量子色动力学|quantum_chromodynamics|liang zi se dong li xue
弱电理论|electroweak_theory|ruo dian li lun
标准模型|standard_model|biao zhun mo xing
希格斯场|higgs_field|xi ge si chang
希格斯机制|higgs_mechanism|xi ge si ji zhi
自发对称性破缺|spontaneous_symmetry_breaking|zi fa dui chen xing po que
戈德斯通定理|goldstone_theorem|ge de si tong ding li
戈德斯通玻色子|goldstone_boson|ge de si tong bo se zi
质量生成|mass_generation|zhi liang sheng cheng
手征对称性|chiral_symmetry|shou zheng dui chen xing
手征破缺|chiral_symmetry_breaking|shou zheng po que
反常|anomaly|fan chang
轴反常|axial_anomaly|zhou fan chang
重整化|renormalization|chong zheng hua
重整化群|renormalization_group|chong zheng hua qun
重整化尺度|renormalization_scale|chong zheng hua chi du
跑动耦合常数|running_coupling_constant|pao dong ou he chang shu
紫外发散|ultraviolet_divergence|zi wai fa san
红外发散|infrared_divergence|hong wai fa san
正规化|regularization|zheng gui hua
维数正规化|dimensional_regularization|wei shu zheng gui hua
反项|counterterm|fan xiang
有效场论|effective_field_theory|you xiao chang lun
低能有效理论|low_energy_effective_theory|di neng you xiao li lun
非线性西格玛模型|nonlinear_sigma_model|fei xian xing xi ge ma mo xing
自能|self_energy|zi neng
顶角修正|vertex_correction|ding jiao xiu zheng
真空极化|vacuum_polarization|zhen kong ji hua
瞬子|instanton|shun zi
孤子|soliton|gu zi
拓扑荷|topological_charge|tuo pu he
θ真空|theta_vacuum|theta zhen kong
渐近自由|asymptotic_freedom|jian jin zi you
禁闭|confinement|jin bi
夸克场|quark_field|kua ke chang
胶子场|gluon_field|jiao zi chang
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
    path.parent.mkdir(parents=True, exist_ok=True)
    seen_cn = set()
    seen_en = set()
    deduped = []
    for row in rows:
        cn, _, english, _ = row
        if cn in seen_cn or english in seen_en:
            continue
        seen_cn.add(cn)
        seen_en.add(english)
        deduped.append(row)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        for idx, (cn, initials, english, pinyin) in enumerate(deduped, 1):
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
    return len(deduped)


def main():
    for filename, text in TABLES.items():
        path = PHYSICS_MAJOR_DIR / filename
        count = write_table(path, parse_rows(text))
        print(f"{path.relative_to(ROOT)}: {count} rows")


if __name__ == "__main__":
    main()
