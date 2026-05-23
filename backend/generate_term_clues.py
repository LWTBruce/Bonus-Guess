from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORDS_DIR = ROOT / "words"
OUTPUT_DIR = ROOT / "clues"

NAME_FIELD = "概念中文名"
DIFFICULTY_FIELD = "难度"
ENGLISH_FIELD = "概念英文名"
PINYIN_FIELD = "概念中文拼音"
INITIALS_FIELD = "中文首字母"
NUMBER_FIELD = "编号"


TOPIC_LABELS = {
    "mechanics": "力学",
    "electromagnetism": "电磁学",
    "electrodynamics": "电动力学",
    "optics": "光学",
    "thermal": "热学",
    "thermo_stat_mech": "热统",
    "modern_physics": "近代物理",
    "quantum_mechanics": "量子力学",
    "theoretical_mechanics": "理论力学",
    "high_school_mechanics": "高中力学",
    "high_school_electromagnetism": "高中电磁",
    "high_school_optics": "高中光学",
    "high_school_thermal": "高中热学",
    "advanced_calculus": "高等微积分",
    "linear_algebra": "线性代数",
    "complex_analysis": "复分析",
    "mathematical_physics_equations": "数理方程",
    "mathematical_statistics": "数理统计",
    "probability_theory": "概率论",
    "field_theory": "域论",
    "group_theory": "群论",
    "topology": "拓扑学",
    "high_school_geometry": "高中几何",
    "high_school_probability_statistics": "高中统计",
    "high_school_sequences_inequalities": "数列不等式",
    "high_school_sets_functions": "集合函数",
    "high_school_trigonometry_vectors": "三角向量",
    "原子分子光物理": "原子分子光",
    "固体物理": "固体物理",
    "天体物理": "天体物理",
    "广义相对论": "相对论",
    "核物理与粒子物理": "核粒子",
    "量子场论": "量子场论",
}


DIFFICULTY_LABELS = {
    1: "很基础",
    2: "较基础",
    3: "入门偏上",
    4: "常规难度",
    5: "需要推理",
    6: "进阶常见",
    7: "进阶核心",
    8: "高阶概念",
    9: "困难专题",
    10: "挑战级别",
}


TOPIC_CLUE_BANK = {
    "力学": ("运动和相互作用", "受力分析", "守恒律或运动方程"),
    "理论力学": ("约束、变分和广义坐标", "建立拉氏量或哈密顿量", "对称性与守恒量"),
    "电磁学": ("电场、磁场和电路问题", "场量与源的关系", "积分形式或微分形式公式"),
    "电动力学": ("时变场和相对论协变表述", "麦克斯韦方程组", "规范、波动和辐射问题"),
    "光学": ("光线、波前和成像问题", "干涉、衍射或偏振", "几何关系或相位关系"),
    "热学": ("热现象和物态变化", "状态量与过程量", "能量交换或分子图像"),
    "热统": ("宏观热力学与微观统计", "配分函数或状态方程", "平衡、涨落和系综"),
    "近代物理": ("相对论或旧量子模型", "能量、频率和轨道关系", "经典模型的边界"),
    "量子力学": ("态、算符和测量问题", "薛定谔方程或本征值", "近似方法和势场模型"),
    "原子分子光": ("原子能级与光谱", "跃迁、选择定则或相互作用", "实验谱线分析"),
    "固体物理": ("晶格、能带和集体激发", "周期结构或输运性质", "材料性质分析"),
    "天体物理": ("恒星、星系和宇宙尺度", "辐射、引力或演化模型", "观测量与理论模型对应"),
    "相对论": ("时空几何和引力场", "度规、测地线或曲率", "强引力场景"),
    "核粒子": ("核结构、衰变和基本粒子", "守恒量或散射过程", "反应道与能谱判断"),
    "量子场论": ("场、粒子和相互作用", "拉氏量、传播子或费曼图", "对称性和重整化问题"),
    "高等微积分": ("极限、导数和积分", "局部变化或累积量", "一元与多元函数分析"),
    "线性代数": ("向量空间和线性映射", "矩阵、秩或特征结构", "方程组与变换判断"),
    "复分析": ("复函数和解析性", "围道积分或级数展开", "奇点和留数计算"),
    "数理方程": ("偏微分方程和边值问题", "分离变量或变换法", "波、热和势问题"),
    "概率论": ("随机试验和分布", "条件、独立或极限定理", "随机变量运算"),
    "数理统计": ("样本、估计和检验", "统计量或抽样分布", "由数据反推模型"),
    "拓扑学": ("连续变形和空间性质", "开集、紧性或连通性", "不依赖距离的结构"),
    "群论": ("代数结构和对称性", "运算、子结构或作用", "抽象对称问题"),
    "域论": ("域扩张和多项式", "代数数或伽罗瓦对应", "可解性与结构分析"),
    "高中力学": ("高中运动和相互作用", "受力、功和能量", "图像或公式应用"),
    "高中电磁": ("电路、电场和磁场", "电压、电流或感应关系", "实验和基本公式"),
    "高中光学": ("成像和光的传播", "反射、折射或干涉", "作图和公式判断"),
    "高中热学": ("温度、内能和气体", "热量或状态变化", "分子动理论图像"),
    "高中几何": ("图形、位置和度量", "角、线、面或体", "作图和证明"),
    "高中统计": ("随机事件和数据", "概率、频率或统计图", "样本信息判断"),
    "数列不等式": ("离散变化和大小关系", "递推、求和或估计", "通项和证明"),
    "集合函数": ("集合关系和函数变化", "定义域、值域或图像", "代数式与图像判断"),
    "三角向量": ("角度、方向和投影", "三角恒等式或坐标表示", "几何与代数互译"),
}


KEYWORD_CLUES = {
    "angular_momentum": "它关心绕某点或某轴转动时守恒的那类量",
    "center_of_mass": "它把多个质点的分布等效到一个代表位置上",
    "moment_of_inertia": "它衡量物体抗拒角加速度改变的本领",
    "displacement": "它比较始末位置，而不是实际走过的轨迹长度",
    "velocity": "它描述位置随时间变化的快慢和方向",
    "acceleration": "它描述速度随时间变化的快慢和方向",
    "momentum": "它常和冲量、碰撞和守恒律一起出现",
    "torque": "它衡量力使物体发生转动的效果",
    "force": "它是改变运动状态或形变的相互作用",
    "energy": "它常作为不同过程之间可转化的守恒量",
    "work": "它常由力沿位移方向的累积效果给出",
    "power": "它描述单位时间内做功或能量转化的快慢",
    "pressure": "它常由单位面积上的垂直作用效果刻画",
    "mass": "它和惯性、引力源以及物质量度有关",
    "charge": "它是产生电磁相互作用的一种基本属性",
    "current": "它描述电荷定向通过截面的快慢",
    "voltage": "它常表现为单位电荷能量差",
    "resistance": "它衡量电路元件阻碍电流的程度",
    "capacitance": "它衡量储存电荷和电势差之间的比例关系",
    "inductance": "它和电流变化产生的自感效应有关",
    "electric_field": "它让单位正电荷感受到力的空间分布",
    "magnetic_field": "它常和运动电荷、磁矩以及洛伦兹力相连",
    "flux": "它衡量场穿过某个面的总量",
    "potential": "它常把场的问题转化为能量或函数的问题",
    "wave": "它描述扰动在空间和时间中的传播",
    "frequency": "它描述周期现象单位时间重复的次数",
    "wavelength": "它描述相邻同相位点之间的空间距离",
    "phase": "它标记周期运动或波动进行到哪一步",
    "interference": "它来自相干叠加后强弱重新分布",
    "diffraction": "它让波在孔缝或障碍物边缘后偏离几何直线传播",
    "polarization": "它关心横波振动方向的取向状态",
    "temperature": "它表征热平衡状态下冷热程度的状态量",
    "entropy": "它常与不可逆性、微观状态数和热力学方向有关",
    "heat": "它是在温差驱动下传递的能量",
    "partition_function": "它把各能级权重汇总成统计热力学的核心量",
    "state_function": "它只由状态决定，与具体路径无关",
    "operator": "它作用在态或函数上并产生新的数学对象",
    "eigenvalue": "它出现在作用后方向不变、只差比例因子的情形",
    "eigenvector": "它在变换后仍沿原方向，只改变倍数",
    "wave_function": "它用来承载概率幅的信息",
    "uncertainty": "它说明某些物理量无法同时任意精确确定",
    "perturbation": "它把复杂问题看成简单问题加上小修正",
    "well": "它常把粒子限制在某个空间区域里",
    "oscillator": "它围绕平衡位置作周期性响应",
    "spin": "它是量子态中没有经典转轴图像的内禀角动量",
    "matrix": "它把线性关系排列成可计算的数表",
    "determinant": "它把方阵压缩成一个反映伸缩和可逆性的数",
    "rank": "它刻画线性无关信息的有效数量",
    "vector": "它通常同时带有大小、方向或分量信息",
    "linear": "它强调加法和数乘结构被保持",
    "basis": "它是一组能唯一展开空间中对象的参照",
    "dimension": "它刻画独立自由度的个数",
    "limit": "它描述变量逼近某处时对象趋向的值",
    "derivative": "它刻画局部变化率或线性近似",
    "integral": "它把局部量累积成整体量",
    "series": "它用无限项和表示函数或数值",
    "gradient": "它指向函数增长最快的方向",
    "divergence": "它衡量向量场从一点向外散开的程度",
    "curl": "它衡量向量场局部旋转的趋势",
    "function": "它把输入按规则对应到输出",
    "set": "它把对象收集成一个整体来讨论",
    "group": "它把带有封闭运算和逆元的对称结构抽象出来",
    "field": "它既可能是空间分布的物理量，也可能是可四则运算的代数结构",
    "ring": "它保留加法和乘法两种运算结构",
    "topology": "它只关心连续变形下不变的空间性质",
    "compact": "它常把无限覆盖问题压缩到有限子覆盖",
    "connected": "它刻画空间是否能被分成互不相连的两块",
    "probability": "它刻画随机事件发生可能性的大小",
    "distribution": "它描述随机变量取值规律",
    "expectation": "它是随机变量按概率加权后的平均趋势",
    "variance": "它衡量随机变量偏离平均值的程度",
    "hypothesis": "它把待检验的统计判断写成可计算命题",
    "estimator": "它用样本构造对未知参数的猜测",
    "confidence": "它给出区间估计的可靠程度表述",
    "fourier": "它把函数拆成不同频率的正弦余弦成分",
    "laplace": "它常把微分问题转到代数式或复频域中处理",
    "green": "它用点源响应来拼出一般源的解",
    "boundary": "它强调区域边界上必须满足的条件",
    "tensor": "它在坐标变换下按固定规则改变分量",
    "metric": "它规定时空或空间中距离与间隔怎样计算",
    "geodesic": "它对应弯曲空间里最自然的直线推广",
    "curvature": "它衡量空间或时空偏离平直的程度",
    "black_hole": "它对应连光也无法逃离的强引力区域",
    "scattering": "它通过入射和出射关系研究相互作用",
    "decay": "它描述不稳定对象自发转变为其他对象的过程",
    "cross_section": "它把反应概率包装成等效面积",
    "lagrangian": "它常由动能与势能的组合进入变分原理",
    "hamiltonian": "它常表示系统能量并生成时间演化",
    "action": "它在变分原理中沿路径累积并取驻值",
}


TOKEN_MEANINGS = {
    "absolute": "绝对取值或无方向大小",
    "acceleration": "速度变化率",
    "action": "沿路径累积的量",
    "addition": "把对象相加",
    "adjoint": "伴随关系",
    "algebra": "代数结构",
    "angle": "方向夹角",
    "angular": "绕轴或绕点转动",
    "approximation": "用可控误差替代原问题",
    "area": "二维区域大小",
    "asymptote": "曲线无限贴近某个参照对象",
    "basis": "展开对象的参照组",
    "boundary": "区域边缘条件",
    "branch": "多值关系中的分支",
    "capacity": "容纳或储存能力",
    "charge": "电相互作用属性",
    "closed": "封闭性",
    "coefficient": "比例因子",
    "compact": "有限子覆盖性质",
    "complex": "复数背景",
    "component": "分量拆解",
    "condition": "必须满足的限制",
    "conjugate": "成对对应关系",
    "conservation": "过程中保持不变",
    "constraint": "运动或变量受限制",
    "continuous": "无跳跃变化",
    "coordinate": "用数值标定位置",
    "correlation": "变量间关联",
    "cross": "横向组合或截面",
    "curl": "局部旋转趋势",
    "current": "通过截面的流动",
    "curve": "弯曲轨迹",
    "density": "单位量中的分布",
    "derivative": "局部变化率",
    "determinant": "方阵伸缩因子",
    "difference": "作差比较",
    "differential": "微小变化",
    "dimension": "独立自由度个数",
    "displacement": "始末位置差",
    "distribution": "取值规律",
    "divergence": "向外散开的趋势",
    "domain": "允许输入范围",
    "eigenvalue": "本征比例因子",
    "eigenvector": "变换后方向不变",
    "electric": "电现象",
    "energy": "可转化的量",
    "entropy": "微观状态数或不可逆性",
    "equation": "等式约束关系",
    "equilibrium": "相互作用达到平衡",
    "event": "随机试验结果",
    "extension": "把结构扩大",
    "field": "空间分布或可运算结构",
    "flux": "穿过面的总量",
    "force": "改变运动或形变的作用",
    "form": "表达形式",
    "formula": "可直接代入的关系",
    "fourier": "按频率分解",
    "function": "输入输出对应",
    "gauge": "冗余自由度选择",
    "generalized": "把具体坐标推广",
    "geodesic": "弯曲空间中的最直路径",
    "gradient": "增长最快方向",
    "graph": "图像表达",
    "group": "对称运算结构",
    "hamiltonian": "生成演化的能量函数",
    "heat": "由温差传递的能量",
    "ideal": "特殊子结构",
    "induction": "由变化引发响应",
    "infinite": "没有有限边界或上限",
    "inertia": "抗拒运动状态改变",
    "integral": "局部量累积",
    "integration": "累积运算",
    "interference": "相干叠加",
    "inverse": "逆向对应",
    "isomorphism": "保持结构的对应",
    "kernel": "映到零的部分",
    "lagrangian": "变分中使用的函数",
    "law": "规律关系",
    "limit": "逼近时的趋势",
    "linear": "保持加法与数乘",
    "line": "一维几何对象",
    "magnetic": "磁现象",
    "mapping": "对象间对应",
    "mass": "惯性或物质量度",
    "matrix": "按行列组织的线性数据",
    "mean": "平均趋势",
    "metric": "距离或间隔规则",
    "mode": "允许的振动形态",
    "momentum": "运动量度",
    "normal": "垂直、标准或在变换下保持稳定",
    "operator": "作用在对象上的规则",
    "orbit": "运动轨道",
    "order": "排列层次或阶数",
    "oscillation": "围绕平衡往复变化",
    "parts": "分拆成若干部分",
    "phase": "周期过程位置",
    "plane": "二维平面对象",
    "point": "理想化位置对象",
    "polar": "极坐标或取向",
    "potential": "位置相关能量函数",
    "power": "单位时间变化率",
    "probability": "随机可能性大小",
    "product": "乘积或组合",
    "projection": "投影到某方向",
    "quantum": "离散化或量子层级",
    "rank": "独立信息数量",
    "rate": "单位量变化快慢",
    "ray": "有方向的半直线",
    "reciprocal": "倒数关系",
    "reflection": "反射对称或光线返回",
    "residue": "奇点附近的系数",
    "resistance": "阻碍流动程度",
    "ring": "加法乘法结构",
    "rotation": "绕轴转动",
    "scalar": "无方向数量",
    "scattering": "入射出射关系",
    "section": "截面或截口",
    "sequence": "按序排列的对象",
    "series": "无限项求和",
    "square": "平方、方形或二次结构",
    "space": "承载对象的集合",
    "speed": "运动快慢",
    "spin": "内禀角动量",
    "state": "系统状态",
    "stokes": "边界与内部的联系",
    "subgroup": "较小的运算结构",
    "subset": "较小的集合",
    "surface": "二维曲面",
    "symmetry": "变换下保持不变",
    "tensor": "多指标几何量",
    "theorem": "可证明命题",
    "transform": "换一种表达域",
    "transformation": "变量或坐标变换",
    "transition": "状态跃变",
    "vector": "有方向或分量的信息",
    "velocity": "有方向的运动快慢",
    "voltage": "单位电荷能量差",
    "wave": "扰动传播",
    "wavelength": "同相位点间距",
    "well": "把对象限制在某个区域内",
    "work": "作用沿路径的累积",
    "zero": "零点或消失位置",
}


APPLICATION_CLUES = {
    "integration_by_parts": "常用于处理两个函数相乘后的积分，把它转化成边界项和另一个积分。",
    "asymptote": "常用来描述函数图像在远处或奇点附近无限贴近某个参照对象的行为。",
    "limit": "常用来判断变量逼近某处时，函数值或数列项是否稳定到某个目标。",
    "derivative": "常用于求瞬时变化率，也用于写切线、判断单调性和做局部线性近似。",
    "partial_derivative": "常用于多元函数里只放开一个变量，观察它沿某个坐标方向的变化。",
    "integral": "常用于把小片贡献累加成面积、体积、总量或平均意义下的整体结果。",
    "gradient": "常用于找函数增长最快的方向，也常出现在多元函数极值和场论公式中。",
    "divergence": "常用于判断向量场在某点附近像源一样流出，还是像汇一样流入。",
    "curl": "常用于判断向量场局部是否带旋转趋势，电磁学和流体问题里尤其常见。",
    "fourier": "常用于把复杂函数拆成不同频率成分，方便处理振动、波动和边值问题。",
    "laplace": "常用于把微分方程转换到另一个变量域，使求解过程更像代数运算。",
    "green": "常用于先求点源响应，再把一般源的效果叠加出来。",
    "matrix": "常用于把线性方程组、线性变换或二次型整理成行列形式计算。",
    "determinant": "常用于判断方阵是否可逆，也能给出面积、体积伸缩因子。",
    "rank": "常用于判断线性方程组的自由度、解的存在性和独立信息量。",
    "eigenvalue": "常用于把线性变换化到特殊方向上，使复杂作用变成比例变化。",
    "eigenvector": "常用于寻找在变换下方向保持不变的特殊对象。",
    "basis": "常用于把空间里的对象唯一展开成若干基本方向的组合。",
    "subspace": "常用于在大空间里截取一个仍保持线性结构的小空间。",
    "linear_transformation": "常用于描述输入向量经过规则后怎样变成输出向量。",
    "probability": "常用于把随机事件发生的可能性量化，并与频率或模型相联系。",
    "distribution": "常用于描述随机变量取值怎样分散在不同区域。",
    "expectation": "常用于计算随机变量的平均趋势，而不是某一次试验的结果。",
    "variance": "常用于衡量随机变量围绕平均值波动得有多大。",
    "hypothesis": "常用于把统计判断转成可检验的原假设和备择假设。",
    "confidence": "常用于说明区间估计在重复抽样意义下的可靠程度。",
    "group": "常用于把对称操作组织起来，研究复合、逆元和不变量。",
    "subgroup": "常用于在一个大运算结构中挑出仍封闭的小结构。",
    "normal_subgroup": "常用于把整体结构按等价类分层，进而构造商结构。",
    "field_extension": "常用于把可运算的数域扩大，以便容纳新的根或代数元素。",
    "galois": "常用于把方程根的对称性与域扩张结构联系起来。",
    "topology": "常用于忽略长度和角度，只保留连续变形下不变的性质。",
    "compact": "常用于把无限覆盖问题压缩成有限子覆盖的判断。",
    "connected": "常用于判断一个空间是否能被连续地分成互不相连的两块。",
    "displacement": "常用于比较始末位置，和实际走过的路程区分开。",
    "velocity": "常用于描述位置变化的快慢和方向，是运动学题里的核心量。",
    "acceleration": "常用于连接速度变化与受力关系，也是判断运动类型的入口。",
    "momentum": "常用于碰撞、反冲和冲量题，重点看过程前后是否守恒。",
    "angular_momentum": "常用于分析绕点或绕轴的运动，尤其关注外力矩是否为零。",
    "torque": "常用于判断一个力是否会让物体绕某点或某轴转动。",
    "moment_of_inertia": "常用于转动方程，作用类似平动中质量对加速度的影响。",
    "center_of_mass": "常用于把多质点系统等效成一个代表位置来处理整体运动。",
    "force": "常用于受力图和运动方程，是把相互作用转成计算的桥梁。",
    "work": "常用于把力沿路径的累积效果转化为能量变化。",
    "power": "常用于比较能量转化或做功在时间上的快慢。",
    "energy": "常用于跨过程比较，把运动、位置和热等形式联系起来。",
    "electric_field": "常用于由源电荷推断空间中试探电荷受力。",
    "electric_potential": "常用于把电场问题转成能量差或标量函数问题。",
    "voltage": "常用于电路和静电题，表示单位电荷跨两点的能量变化。",
    "current": "常用于描述电荷通过导体截面的快慢，是电路方程的基本量。",
    "resistance": "常用于判断电路中电流被削弱的程度，并和电压电流相连。",
    "capacitance": "常用于描述导体系统储存电荷的能力。",
    "magnetic_field": "常用于分析运动电荷、通电导线或磁矩受到的作用。",
    "magnetic_flux": "常用于电磁感应题，重点看穿过面积的磁场总量怎样变化。",
    "induction": "常用于由变化的场或电流推出感应响应。",
    "interference": "常用于判断相干波叠加后哪里增强、哪里减弱。",
    "diffraction": "常用于解释波绕过障碍物或通过小孔后不再按几何直线传播。",
    "polarization": "常用于判断横波振动方向是否被选定或筛选。",
    "wavelength": "常用于把空间周期和频率、波速联系起来。",
    "frequency": "常用于描述周期过程单位时间内重复的次数。",
    "temperature": "常用于判断热平衡和状态方程中的冷热程度。",
    "entropy": "常用于判断过程方向、不可逆性和微观状态数变化。",
    "partition_function": "常用于把所有微观态的权重汇总，再推出宏观热力学量。",
    "heat_capacity": "常用于比较系统升高同样温度时需要吸收多少热量。",
    "wave_function": "常用于承载概率幅信息，并通过模平方联系可观测概率。",
    "operator": "常用于把物理量写成作用规则，再通过本征值联系测量结果。",
    "uncertainty": "常用于判断两类物理量是否能同时被任意精确给出。",
    "perturbation": "常用于从一个已知可解问题出发，计算小修正带来的变化。",
    "well": "常用于把粒子限制在有限区域内，再由边界条件推出能级。",
    "oscillator": "常用于分析围绕平衡位置的周期运动或量子化振动。",
    "spin": "常用于区分态的内禀角动量性质，而不是经典转轴运动。",
    "lagrangian": "常用于从广义坐标出发，经由变分得到运动方程。",
    "hamiltonian": "常用于描述系统能量并生成时间演化。",
    "poisson_bracket": "常用于判断力学量随时间如何演化，以及守恒量之间的关系。",
    "metric": "常用于计算时空间隔，并决定测地线和曲率的表达。",
    "geodesic": "常用于描述自由粒子在弯曲时空中的自然运动路径。",
    "curvature": "常用于刻画时空或空间偏离平直的程度。",
    "black_hole": "常用于讨论强引力区域、视界和逃逸条件。",
    "scattering": "常用于由入射态和出射态反推出相互作用信息。",
    "decay": "常用于描述不稳定对象按一定概率转变为其他对象。",
    "cross_section": "常用于把散射或反应概率换成等效面积来比较。",
    "feynman": "常用于把相互作用过程画成顶点和线，并据此写振幅。",
    "renormalization": "常用于处理发散量，把可观测结果重新定义到有限参数上。",
}


CHINESE_APPLICATION_RULES = [
    (("验电器",), "常在实验题中用来判断物体是否带电，重点看金属箔或指针的变化。"),
    (("电容器",), "常作为储能元件出现，题目会围绕带电量、两端电压和板间结构展开。"),
    (("变阻器",), "常在实验电路中用来连续改变阻值，从而调节电流或分压。"),
    (("恒定",), "使用时重点看相关量是否随时间保持不变，电路方程通常更稳定。"),
    (("交变",), "使用时重点看周期变化、有效值、峰值以及相位关系。"),
    (("电路",), "常用于把电源、用电器和导线连接关系整理成可列方程的图。"),
    (("电动势",), "常用于描述电源把其他形式能量转化为电能的本领。"),
    (("安培",), "常用于判断通电导线在磁场中受到的作用方向和大小。"),
    (("洛伦兹",), "常用于判断运动电荷在电磁场中的受力和偏转。"),
    (("欧姆",), "常用于在电压、电流和阻值之间快速建立比例关系。"),
    (("楞次",), "常用于判断感应响应的方向，总是阻碍引起它的变化。"),
    (("参考系",), "常用于说明同一运动在不同观察者看来可能有不同描述。"),
    (("坐标",), "常用于把几何或运动问题转成数值关系。"),
    (("位置",), "常用于在选定参照下标出物体所在点，并作为位移的起点或终点。"),
    (("路程",), "常用于累计实际走过的路径长度，不关心方向抵消。"),
    (("位移",), "常用于只比较始末两点之间的有向变化。"),
    (("平抛",), "常用于把水平方向匀速和竖直方向加速分开处理。"),
    (("圆周",), "常用于把运动分解为切向变化和指向圆心的变化。"),
    (("碰撞",), "常用于过程很短、相互作用很强的题，优先检查动量关系。"),
    (("弹性",), "常用于判断碰撞或形变过程中机械能是否额外守恒。"),
    (("时间",), "常用于把运动过程切成可比较的前后阶段。"),
    (("速度",), "常用于描述运动快慢，并进一步接入位移或加速度关系。"),
    (("加速度",), "常用于把运动变化同受力或斜率联系起来。"),
    (("质量",), "常用于衡量惯性大小，也常和受力方程一起出现。"),
    (("质心",), "常用于把多个物体的整体平动等效到一个代表点。"),
    (("转动",), "常用于把平动中的力、质量和动量换成力矩、转动惯量和角动量。"),
    (("能级",), "常用于判断系统允许的离散能量状态。"),
    (("跃迁",), "常用于分析系统从一个状态变到另一个状态时吸收或放出的能量。"),
    (("光谱",), "常用于由谱线位置或强度反推能级、成分或运动状态。"),
    (("晶格",), "常用于描述固体中重复排列的空间骨架。"),
    (("能带",), "常用于判断固体中电子能量允许区间与禁带。"),
    (("子群",), "常用于在一个运算结构内部挑出仍能独立封闭运算的部分。"),
    (("正规",), "常用于保证按陪集分块后还能形成良好的商结构。"),
    (("同态",), "常用于比较两个结构之间哪些运算关系被保留下来。"),
    (("紧",), "常用于把无限覆盖或无限序列问题转成有限可控的判断。"),
    (("连通",), "常用于判断空间是否能被分裂成互不相连的部分。"),
    (("估计",), "常用于用样本数据推断未知参数。"),
    (("检验",), "常用于判断样本证据是否足以拒绝某个统计命题。"),
]


TOKEN_USE_CASES = {
    "absolute": "比较大小时忽略方向或符号",
    "acceleration": "由速度变化反推受力或运动类型",
    "action": "沿路径累积并寻找驻值",
    "addition": "把多个对象合成为一个对象",
    "algebra": "保留运算规则来研究结构",
    "angle": "把方向差异转化为可计算量",
    "angular": "把平动问题改写成绕点或绕轴的问题",
    "approximation": "用可控误差换取可计算形式",
    "area": "把二维区域的大小或通量转成数值",
    "basis": "把对象展开到一组基本方向上",
    "boundary": "用边界上的条件限制内部解",
    "capacitance": "比较储存电荷的能力",
    "charge": "判断电磁相互作用的源",
    "compact": "把无限条件压缩到有限子情形",
    "component": "把整体拆成可分别处理的分量",
    "condition": "筛掉不满足限制的候选对象",
    "conjugate": "把成对对象放在同一个关系里比较",
    "conservation": "比较过程前后的不变量",
    "constraint": "把自由变化限制在允许范围内",
    "continuous": "判断对象能否无跳跃地变化",
    "coordinate": "把几何对象转成数值位置",
    "correlation": "判断两个变量是否一起变化",
    "curl": "检测局部旋转趋势",
    "current": "把通过截面的流动量化",
    "density": "把总量分摊到单位长度、面积或体积",
    "derivative": "用局部变化率处理趋势",
    "determinant": "判断可逆性或体积伸缩",
    "dimension": "统计独立自由度的数量",
    "distribution": "描述取值分散在哪些位置",
    "divergence": "判断某点附近是否有源或汇",
    "domain": "先确定输入或定义允许的范围",
    "energy": "用可转化的守恒量连接前后状态",
    "equation": "把条件集中到一个待求解关系里",
    "equilibrium": "判断各作用是否达到平衡",
    "extension": "把原有结构扩大到能容纳新对象",
    "field": "把每个空间点上的量组织成整体",
    "flux": "统计穿过某个面的场总量",
    "force": "把相互作用转化为运动变化",
    "function": "把输入变化和输出变化联系起来",
    "gradient": "寻找增长最快方向",
    "group": "研究操作复合后的对称结构",
    "heat": "把温差引起的能量转移量化",
    "induction": "由变化推出相应的感应结果",
    "integral": "把局部贡献累加成整体",
    "interference": "判断叠加后增强还是减弱",
    "inverse": "从结果反推原对象或反向操作",
    "kernel": "找出被映到零的部分",
    "law": "用稳定关系约束过程",
    "limit": "研究逼近时的稳定趋势",
    "linear": "利用加法和数乘保持不变来简化",
    "mapping": "追踪对象在规则下如何对应",
    "mass": "衡量惯性或作为源的强弱",
    "matrix": "用行列计算承载线性关系",
    "mean": "提取平均趋势",
    "metric": "规定距离或间隔的计算方式",
    "mode": "区分允许出现的振动形态",
    "momentum": "用运动量分析碰撞和守恒",
    "normal": "判断垂直、标准或稳定子结构",
    "operator": "把物理量或变换写成作用规则",
    "orbit": "追踪对象在作用下走过的轨道",
    "phase": "标记周期过程进行到哪一步",
    "potential": "把场或位置关系转化为能量函数",
    "probability": "量化随机事件可能性",
    "projection": "只取某个方向上的成分",
    "rank": "判断独立信息量",
    "reflection": "利用镜像关系或返回路径",
    "residue": "用奇点附近的系数计算围道积分",
    "rotation": "分析绕轴或绕点的变化",
    "scattering": "由入射和出射比较相互作用",
    "sequence": "按项研究离散变化",
    "series": "用无限项求和表达对象",
    "space": "给对象提供可运算或可比较的背景",
    "state": "记录系统当前可区分的信息",
    "subgroup": "在大结构里找仍封闭的小结构",
    "surface": "把问题限制在二维边界或曲面上",
    "symmetry": "找出变换下保持不变的东西",
    "tensor": "让多分量对象在坐标变化下仍有规则",
    "theorem": "把已知条件推进到可用结论",
    "transform": "换一种变量或表达域处理问题",
    "transition": "描述状态之间的转变",
    "vector": "用分量和方向组织信息",
    "velocity": "量化有方向的运动快慢",
    "wave": "把扰动传播过程联系起来",
    "work": "把沿路径的作用累积为能量变化",
    "zero": "定位对象消失或取零的位置",
}


TERM_CLASS_RULES = [
    (("定律",), ("law",), "规律或守恒关系", "把几个量之间的联系压缩成可检验的规则", "常用于判断过程前后哪些量被约束", "规律 约束"),
    (("定理",), ("theorem",), "可证明命题", "在推导中作为已经证明的桥梁使用", "常把局部条件转化为整体结论", "命题 推导"),
    (("方程",), ("equation",), "方程关系", "把未知量和已知条件放进同一个等式框架", "通常通过求解或代入来锁定目标量", "等式 求解"),
    (("公式",), ("formula",), "计算公式", "把常见关系整理成可直接代入的表达式", "常用于从已知量快速推出未知量", "代入 关系"),
    (("原理",), ("principle",), "基本出发点", "给建模或推导提供高层约束", "往往比单个公式更像判断准则", "准则 建模"),
    (("模型",), ("model",), "理想化模型", "保留主要机制并舍去次要细节", "常用于把复杂对象化成可计算图像", "理想化 机制"),
    (("效应",), ("effect",), "可观察现象", "描述条件改变后出现的特征响应", "常可通过实验现象或图像识别", "现象 响应"),
    (("变换",), ("transform", "transformation"), "表达变换", "把同一对象改写到另一套变量或坐标中", "常用于让关系式变得更容易处理", "变量 改写"),
    (("近似",), ("approximation",), "近似方法", "用较简单的对象替代难以精确处理的对象", "关键在误差是否足够可控", "近似 误差"),
    (("方法", "法"), ("method",), "求解方法", "给出一套可重复执行的处理流程", "常在题目中表现为固定的化简套路", "流程 化简"),
    (("势阱", "阱"), ("well",), "约束势场模型", "把对象限制在某个空间区域中分析", "常通过边界条件和能级结构辨认", "限制 能级"),
    (("条件",), ("condition",), "限制条件", "规定对象必须满足的边界或约束", "常用于排除不符合要求的候选解", "限制 排除"),
    (("不等式",), ("inequality",), "大小关系", "比较两个表达式或对象的取值范围", "常用于估计、证明或划定可行区域", "比较 范围"),
    (("分布",), ("distribution",), "取值规律", "描述对象落在不同取值上的整体安排", "常用于从局部概率或密度看整体", "取值 规律"),
    (("矩阵",), ("matrix",), "线性数据结构", "用行列形式承载变换或方程组信息", "常通过行列运算揭示独立性", "行列 变换"),
    (("向量",), ("vector",), "有方向或分量的对象", "把多个分量合成一个可运算整体", "常用于表达方向、状态或线性组合", "分量 方向"),
    (("张量",), ("tensor",), "多指标对象", "在坐标改变时仍按固定规则变换", "常用于表达几何或物理量的协变结构", "多指标 变换"),
    (("算符",), ("operator",), "作用规则", "把一个对象送到另一个对象", "常通过本征问题或交换关系识别", "作用 本征"),
    (("函数",), ("function",), "输入输出规则", "把自变量变化转化为因变量变化", "常通过图像、解析式或性质研究", "输入 输出"),
    (("空间",), ("space",), "承载结构", "给对象提供运算、邻近或几何背景", "常通过维数、基或开集性质辨认", "承载 结构"),
    (("群",), ("group",), "对称运算结构", "把可复合并可逆的操作组织起来", "常用来描述变换或置换中的不变量", "对称 运算"),
    (("域",), ("field",), "可四则运算结构", "让加减乘除在合适对象中封闭", "常和多项式、扩张或解方程联系在一起", "四则 扩张"),
    (("环",), ("ring",), "双运算结构", "同时保留加法和乘法但不一定能除", "常用于研究理想、同态和多项式", "加法 乘法"),
    (("态",), ("state",), "状态描述", "概括系统在某一时刻或条件下的信息", "常通过能级、概率或演化来区分", "状态 演化"),
    (("能", "能量"), ("energy",), "能量量度", "在不同形式之间转化并参与守恒判断", "常通过势、功或状态差来计算", "能量 转化"),
    (("动量",), ("momentum",), "运动量度", "把质量和运动状态结合起来", "常在碰撞、冲量或守恒题中出现", "运动 守恒"),
    (("力",), ("force",), "相互作用量", "反映物体运动状态或形变被改变的原因", "常需要先画受力图再列方程", "作用 受力"),
    (("场",), ("field",), "空间分布对象", "给空间中每一点赋予某种物理或数学量", "常通过源、通量或势来刻画", "空间 分布"),
    (("波",), ("wave",), "传播扰动", "把空间变化和时间变化联系起来", "常由频率、波长、相位或边界条件区分", "传播 相位"),
    (("线",), ("line", "curve"), "几何线状对象", "通常用来描述轨迹、边界或图像特征", "常通过斜率、方程或趋近关系辨认", "线状 图像"),
    (("面",), ("surface", "plane"), "面状几何对象", "常作为边界、截面或二维承载对象出现", "可通过法向、面积或方程描述", "面状 边界"),
    (("角",), ("angle",), "方向差异", "衡量两条线、两个方向或两种状态之间的偏转", "常和投影、旋转或三角关系同题出现", "方向 偏转"),
    (("率",), ("rate", "frequency"), "变化快慢", "描述某个量相对时间或另一变量的变化程度", "常以单位量的变化来理解", "变化 快慢"),
    (("度",), ("degree", "density"), "强弱程度", "衡量某种属性的大小、密集或等级", "常通过单位量或标度来比较", "强弱 标度"),
    (("数",), ("number",), "数量参数", "用一个数值记录阶数、个数、比例或特征", "常在分类和计算中充当标签", "数值 参数"),
    (("量",), ("quantity",), "可比较量", "能被计算、比较或作为方程中的未知量", "常和单位、守恒或测量联系在一起", "量值 测量"),
    (("图",), ("graph", "diagram"), "图形表达", "把关系或结构画成可视对象", "常通过节点、曲线或坐标读出信息", "图形 读取"),
]


def topic_clues(topic: str) -> tuple[str, str, str]:
    return TOPIC_CLUE_BANK.get(topic, ("相关专题", "定义、公式或模型", "概念辨析"))


def csv_paths() -> list[Path]:
    paths: list[Path] = []
    for subject_dir in (WORDS_DIR / "物理", WORDS_DIR / "数学"):
        if subject_dir.exists():
            paths.extend(subject_dir.rglob("*.csv"))
    return sorted(paths, key=lambda path: path.as_posix())


def relative_source(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def subject_from_path(path: Path) -> str:
    rel_parts = path.relative_to(WORDS_DIR).parts
    return rel_parts[0] if rel_parts else ""


def mode_from_path(path: Path) -> str:
    rel_parts = path.relative_to(WORDS_DIR).parts
    if len(rel_parts) < 2:
        return "综合"
    folder = rel_parts[1]
    if "入门" in folder:
        return "入门"
    if "简单" in folder:
        return "简单"
    if "普通" in folder:
        return "普通"
    if "困难" in folder:
        return "困难"
    return "综合"


def topic_from_path(path: Path) -> str:
    stem = path.stem.removesuffix("_terms")
    return TOPIC_LABELS.get(stem, TOPIC_LABELS.get(path.stem, "综合专题"))


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def english_shape(english: str) -> str:
    if not english:
        return "英文名未列"
    tokens = [token for token in english.replace("-", "_").split("_") if token]
    if len(tokens) >= 3:
        return "英文三段以上"
    if len(tokens) == 2:
        return "英文双词结构"
    return "英文单词结构"


def english_tokens(english: str) -> list[str]:
    return [token for token in re.split(r"[_\-\s]+", english.lower()) if token]


def stable_index(seed: str, modulo: int) -> int:
    if modulo <= 0:
        return 0
    digest = hashlib.sha1(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % modulo


def pick_variant(seed: str, variants: list[str]) -> str:
    return variants[stable_index(seed, len(variants))]


def difficulty_label(level: int) -> str:
    if level in DIFFICULTY_LABELS:
        return DIFFICULTY_LABELS[level]
    if level <= 0:
        return "难度未标"
    if level <= 3:
        return "基础层级"
    if level <= 6:
        return "常规层级"
    if level <= 8:
        return "进阶层级"
    return "挑战层级"


def without_answer(candidates: list[str], answer: str, count: int) -> list[str]:
    kept: list[str] = []
    seen: set[str] = set()
    for clue in candidates:
        clue = clue.strip()
        if not clue or answer in clue or clue in seen:
            continue
        kept.append(clue)
        seen.add(clue)
        if len(kept) == count:
            return kept
    raise ValueError(f"Not enough safe clues for {answer!r}")


def term_profile(answer: str, english: str) -> dict[str, str]:
    tokens = english_tokens(english)
    normalized = "_".join(tokens)
    for cn_markers, en_markers, kind, role, detail, fragment in TERM_CLASS_RULES:
        if any(marker in answer for marker in cn_markers) or any(marker in tokens or marker in normalized for marker in en_markers):
            return {
                "kind": kind,
                "role": role,
                "detail": detail,
                "fragment": fragment,
            }
    return {
        "kind": "核心概念",
        "role": "把题目中的对象、关系或过程命名",
        "detail": "常需要结合定义和出现语境来辨认",
        "fragment": "定义 语境",
    }


def structure_hint(answer: str, profile: dict[str, str]) -> str:
    length = len(answer)
    if length == 1:
        return f"中文名只有一个字，更像一个高度压缩的{profile['kind']}"
    if length == 2:
        return f"中文名是两个字，通常直接指向一个{profile['kind']}"
    if answer.endswith(("法", "方法")):
        return "中文结构暗示它是一套可操作的处理流程"
    if answer.endswith(("定律", "定理", "原理", "公式", "方程")):
        return "中文结构暗示它常被写成可引用的理论关系"
    if answer.endswith(("模型", "图像", "图")):
        return "中文结构暗示它把对象换成便于分析的图景"
    if answer.endswith(("量", "率", "度", "数")):
        return "中文结构暗示它是用来比较或计算的量化指标"
    if answer.endswith(("线", "面", "体", "点", "角")):
        return "中文结构暗示它带有明显的几何或位置意味"
    if answer.endswith(("群", "环", "域", "空间", "矩阵", "向量", "张量")):
        return "中文结构暗示它是承载运算或变换的对象"
    return f"中文名有{length}个字，通常比基础名词多了一层限定"


def token_meaning_parts(english: str) -> list[str]:
    parts: list[str] = []
    for token in english_tokens(english):
        if token in {"of", "the", "and", "or", "by", "in", "on", "for", "to", "a", "an"}:
            continue
        meaning = TOKEN_MEANINGS.get(token)
        if meaning and meaning not in parts:
            parts.append(meaning)
    return parts


def token_bridge_clue(english: str, profile: dict[str, str], answer: str = "", pinyin: str = "") -> str:
    meanings = token_meaning_parts(english)
    tokens = english_tokens(english)
    cn_shape = ""
    if answer:
        cn_shape = f"，中文长度{len(answer)}字"
        if pinyin:
            cn_shape += f"，拼音长度{len(pinyin)}"
    if tokens:
        first_hint = tokens[0][:2] if len(tokens[0]) >= 2 else tokens[0][0]
        edge = f"，英文开头约为 {first_hint}...，末尾为 ...{tokens[-1][-1]}"
        if len(tokens) == 1:
            shape = f"英文词长约{len(tokens[0])}个字母{edge}"
        else:
            shape = f"英文名有{len(tokens)}段，首段{len(tokens[0])}个字母、末段{len(tokens[-1])}个字母{edge}"
    else:
        shape = "英文结构信息不足"
    shape += cn_shape
    if len(meanings) >= 2:
        return f"英文拆词暗示“{meanings[0]}”和“{meanings[1]}”这两层信息，{shape}"
    if meanings:
        return f"英文拆词的核心指向“{meanings[0]}”，{shape}"
    if tokens:
        return f"{shape}，整体更像一个{profile['kind']}"
    return f"没有可靠英文拆词时，主要按{profile['role']}来识别"


def chinese_application_clue(answer: str) -> str:
    for markers, clue in CHINESE_APPLICATION_RULES:
        if any(marker in answer for marker in markers) and answer not in clue:
            return clue
    return ""


def scene_clue(answer: str, topic: str, scene: str, formula: str, task: str, profile: dict[str, str], difficulty: int) -> str:
    seed = f"{answer}:scene"
    variants = [
        f"在{topic}题里，它常夹在{scene}和{formula}之间使用",
        f"做{topic}相关题时，遇到{scene}，它常承担“{profile['role']}”的任务",
        f"它多在{scene}一类问题中出场，重点不是记名字，而是看清{formula}",
        f"如果题目正在讨论{task}，这个概念常会作为{profile['kind']}浮出来",
        f"它的难度标为{difficulty}级，通常需要从{scene}的语境里定位",
    ]
    return pick_variant(seed, variants)


def role_clue(answer: str, task: str, profile: dict[str, str]) -> str:
    seed = f"{answer}:role"
    structural = structure_hint(answer, profile)
    variants = [
        f"{structural}；关键判断点是：{profile['detail']}",
        f"从概念类型看，它偏向{profile['kind']}；使用场景集中在{task}",
        f"它不是单纯的背景词，通常承担的功能是：{profile['role']}",
        f"解题时可把它看成{profile['kind']}，再追问它怎样参与{task}",
    ]
    return pick_variant(seed, variants)


def application_clue(answer: str, english: str, topic: str, scene: str, formula: str, task: str, profile: dict[str, str]) -> str:
    chinese_clue = chinese_application_clue(answer)
    if chinese_clue:
        return chinese_clue

    normalized = english.lower().replace("-", "_").replace(" ", "_")
    for key in sorted(APPLICATION_CLUES, key=len, reverse=True):
        if key in normalized:
            return APPLICATION_CLUES[key]

    tokens = english_tokens(english)
    use_cases = []
    for token in tokens:
        use_case = TOKEN_USE_CASES.get(token)
        if use_case and use_case not in use_cases:
            use_cases.append(use_case)
        if len(use_cases) >= 2:
            break
    if len(use_cases) >= 2:
        variants = [
            f"具体用法上，常先{use_cases[0]}，再{use_cases[1]}。",
            f"题目里通常会把它放在“{use_cases[0]}”与“{use_cases[1]}”之间考察。",
            f"真正落到计算时，常要同时处理“{use_cases[0]}”和“{use_cases[1]}”。",
        ]
        return pick_variant(f"{answer}:use2", variants)
    if use_cases:
        variants = [
            f"具体用法上，常围绕“{use_cases[0]}”这一步来判断。",
            f"题目里遇到它，通常要先抓住“{use_cases[0]}”这一层关系。",
            f"它落到解题中，常把问题推进到“{use_cases[0]}”这一步。",
        ]
        return pick_variant(f"{answer}:use1", variants)

    if profile["kind"] == "方程关系":
        return "实际解题时，通常把初值、边界或约束条件代入，再求满足条件的未知量。"
    if profile["kind"] == "规律或守恒关系":
        return "实际使用时，常比较过程前后哪些量保持不变，哪些量由外部作用改变。"
    if profile["kind"] == "求解方法":
        return "实际使用时，它更像一套操作流程，用来把原问题化成更容易下手的形式。"
    if profile["kind"] == "限制条件":
        return "实际使用时，常先列出允许范围，再排除不满足限制的候选对象。"
    if profile["kind"] == "取值规律":
        return "实际使用时，常关心对象落在不同取值上的比例、密度或整体形状。"
    if profile["kind"] == "几何线状对象":
        return "实际使用时，常通过方程、斜率、趋近关系或交点来锁定它。"
    if profile["kind"] == "空间分布对象":
        return "实际使用时，常把每个位置上的取值组织起来，再看源、边界或通量。"
    if profile["kind"] == "约束势场模型":
        return "实际使用时，常从边界条件出发，判断允许状态和能量层级。"

    variants = [
        f"具体到题目里，常用它把{formula}转化为{task}中的可操作判断。",
        f"实际作答时，常先确认它对应的是对象、过程还是关系，再接入{task}。",
        f"它通常不是最后答案，而是把{scene}里的信息整理成可计算步骤的中间抓手。",
        f"遇到它时，可以先找题目里哪些已知量会限制它，再决定用{formula}还是定义。",
        f"它在题目中常负责把抽象描述落到一个可比较、可代入或可排除的对象上。",
        f"使用它时，重点是看清它参与的是分类、计算、建模还是条件筛选。",
    ]
    return pick_variant(f"{answer}:fallback_application", variants)


def application_fragments(answer: str, english: str, topic: str, scene: str, formula: str, task: str, profile: dict[str, str]) -> list[str]:
    clue = application_clue(answer, english, topic, scene, formula, task, profile)
    pieces = [
        part.strip(" ，。；：")
        for part in re.split(r"[，。；：、“”]+", clue)
        if part.strip(" ，。；：") and answer not in part
    ]
    if len(pieces) >= 2:
        return pieces[:3]
    return [task, profile["kind"], "具体运用"]


def staged_clues(stages: list[list[str]], answer: str) -> list[str]:
    clues: list[str] = []
    seen: set[str] = set()
    for candidates in stages:
        chosen = ""
        for clue in candidates:
            clue = str(clue).strip()
            if clue and answer not in clue and clue not in seen:
                chosen = clue
                break
        if not chosen:
            flat = [str(item).strip() for stage in stages for item in stage]
            for clue in flat:
                if clue and answer not in clue and clue not in seen:
                    chosen = clue
                    break
        if not chosen:
            raise ValueError(f"Not enough safe staged clues for {answer!r}")
        clues.append(chosen)
        seen.add(chosen)
    return clues


def keyword_clue(english: str, topic: str, scene: str, formula: str, task: str) -> str:
    normalized = english.lower().replace("-", "_").replace(" ", "_")
    for key in sorted(KEYWORD_CLUES, key=len, reverse=True):
        if key in normalized:
            return KEYWORD_CLUES[key]
    tokens = english_tokens(english)
    if tokens:
        if len(tokens) >= 3:
            shown = "、".join(tokens[:3])
            return f"英文关键词可拆出 {shown} 等片段"
        return f"英文关键词接近 {tokens[0]}"
    return f"它在{topic}中常用来连接{scene}与{formula}"


def near_answer_clue(english: str, pinyin: str, difficulty: int) -> str:
    if english:
        return f"英文名常写作 {english}"
    if pinyin:
        return f"拼音长度为 {len(pinyin)}，难度标为 {difficulty} 级"
    return f"难度标为 {difficulty} 级"


def complete_clues(row: dict[str, str], path: Path) -> list[str]:
    answer = row[NAME_FIELD].strip()
    difficulty = to_int(row.get(DIFFICULTY_FIELD, ""))
    english = row.get(ENGLISH_FIELD, "").strip()
    pinyin = row.get(PINYIN_FIELD, "").strip()
    topic = topic_from_path(path)
    scene, formula, task = topic_clues(topic)
    profile = term_profile(answer, english)
    sharp = keyword_clue(english, topic, scene, formula, task)
    near = near_answer_clue(english, pinyin, difficulty)
    stages = [
        [scene_clue(answer, topic, scene, formula, task, profile, difficulty), f"常在{scene}中出现，常与{formula}密切相关"],
        [role_clue(answer, task, profile), f"解题时可从{task}入手"],
        [application_clue(answer, english, topic, scene, formula, task, profile), f"具体到题目里，常用它把{formula}转化为{task}中的可操作判断"],
        [sharp, token_bridge_clue(english, profile, answer, pinyin), english_shape(english)],
        [near, f"难度标为{difficulty}级"],
    ]
    return staged_clues(stages, answer)


def fragmented_clues(row: dict[str, str], path: Path) -> list[list[str]]:
    answer = row[NAME_FIELD].strip()
    difficulty = to_int(row.get(DIFFICULTY_FIELD, ""))
    english = row.get(ENGLISH_FIELD, "").strip()
    pinyin = row.get(PINYIN_FIELD, "").strip()
    topic = topic_from_path(path)
    scene, formula, task = topic_clues(topic)
    profile = term_profile(answer, english)
    sharp = keyword_clue(english, topic, scene, formula, task)
    structure = structure_hint(answer, profile)
    application_piece = application_fragments(answer, english, topic, scene, formula, task, profile)
    pieces = [
        [scene, formula, profile["fragment"]],
        [task, profile["kind"], structure],
        [*application_piece, "运用"],
        [task, sharp, "收束"],
        [english or english_shape(english), "英文名", f"{difficulty}级"],
        [profile["role"], difficulty_label(difficulty), english_shape(english)],
        [scene, profile["fragment"], difficulty_label(difficulty)],
        [formula, task, "辨认"],
    ]

    safe: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for group in pieces:
        filtered = tuple(part for part in group if part and answer not in part)
        if 2 <= len(filtered) <= 4 and filtered not in seen:
            safe.append(list(filtered))
            seen.add(filtered)
        if len(safe) == 5:
            return safe
    raise ValueError(f"Not enough safe fragmented clues for {answer!r}")


def row_sort_key(row: dict[str, str], fallback: int) -> tuple[int, int]:
    number = to_int(row.get(NUMBER_FIELD, ""), fallback)
    return (number == 0, number or fallback)


def build_entries_for_file(path: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    indexed_rows = list(enumerate(rows, start=1))
    indexed_rows.sort(key=lambda item: row_sort_key(item[1], item[0]))
    for _, row in indexed_rows:
        term = row.get(NAME_FIELD, "").strip()
        if not term:
            continue
        entries.append(
            {
                "chinese_name": term,
                "source_file": relative_source(path),
                "complete_clues": complete_clues(row, path),
                "fragmented_clues": fragmented_clues(row, path),
            }
        )
    return entries


def output_path_for(csv_path: Path) -> Path:
    return (OUTPUT_DIR / csv_path.relative_to(WORDS_DIR)).with_suffix(".json")


def write_entries(path: Path, entries: list[dict[str, object]]) -> None:
    payload = {
        "source_file": relative_source(path),
        "entries": entries,
    }
    target = output_path_for(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def build_all() -> tuple[int, int]:
    file_count = 0
    entry_count = 0
    for path in csv_paths():
        entries = build_entries_for_file(path)
        write_entries(path, entries)
        file_count += 1
        entry_count += len(entries)
    return file_count, entry_count


def main() -> None:
    file_count, entry_count = build_all()
    print(f"Wrote {entry_count} entries into {file_count} clue files under {OUTPUT_DIR.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
