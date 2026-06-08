from ._shared import *


class ModeFlowMixin:
    @staticmethod
    def normalize_play_mode_choice(play_mode):
        if play_mode in {"段位", "自由段位"}:
            return "限时段位"
        legacy_random = {
            "真·随机": "随机自由",
            "真随机": "随机自由",
            "随机": "随机自由",
            "真随机自由": "随机自由",
            "真随机限时": "随机限时",
            "真随机线索": "随机线索",
            "真随机字谜": "随机字谜",
            "真·随机自由": "随机自由",
            "真·随机限时": "随机限时",
            "真·随机线索": "随机线索",
            "真·随机字谜": "随机字谜",
            "随机字谜": "随机字谜",
        }
        if play_mode in legacy_random:
            return legacy_random[play_mode]
        return play_mode

    @staticmethod
    def random_play_mode_base(play_mode):
        return {
            "随机自由": "自由",
            "随机限时": "限时",
            "随机线索": "线索",
            "随机字谜": "字谜",
        }.get(play_mode)

    def is_random_play_choice(self, play_mode=None):
        return self.random_play_mode_base(play_mode or self.selected_play_mode) is not None

    def is_true_random_mode(self):
        return bool(self.true_random_mode or self.mode == "真·随机")

    def is_random_group_mode(self):
        return bool(getattr(self, "random_group_mode", False) or self.is_true_random_mode())

    @staticmethod
    def mode_selection_from_play_mode(play_mode):
        play_mode = ModeFlowMixin.normalize_play_mode_choice(play_mode)
        random_base = ModeFlowMixin.random_play_mode_base(play_mode)
        if random_base:
            return "随机", random_base
        if play_mode in {"限时段位", "自由段位"}:
            return "段位", "限时"
        if play_mode == "线索段位":
            return "段位", "线索"
        if play_mode == "字谜段位":
            return "段位", "字谜"
        if play_mode == "自定义":
            return "自定义", "自定义"
        if play_mode in {"自由", "限时", "线索", "字谜"}:
            return "普通", play_mode
        return "普通", "自由"

    @staticmethod
    def rule_modes_for_group(group):
        return {
            "普通": ["自由", "限时", "线索", "字谜"],
            "随机": ["自由", "限时", "线索", "字谜"],
            "真随机": ["自由", "限时", "线索", "字谜"],
            "段位": ["限时", "线索", "字谜"],
            "自定义": ["自定义"],
        }.get(group, ["自由"])

    @staticmethod
    def play_mode_from_selection(group, rule):
        if group in {"随机", "真随机"}:
            return {
                "自由": "随机自由",
                "限时": "随机限时",
                "线索": "随机线索",
                "字谜": "随机字谜",
            }.get(rule, "随机自由")
        if group == "段位":
            return {
                "限时": "限时段位",
                "线索": "线索段位",
                "字谜": "字谜段位",
            }.get(rule, "限时段位")
        if group == "自定义":
            return "自定义"
        return rule if rule in {"自由", "限时", "线索", "字谜"} else "自由"

    def normalize_mode_selection_state(self):
        if not getattr(self, "selected_game_group", None) or not getattr(self, "selected_rule_mode", None):
            self.selected_game_group, self.selected_rule_mode = self.mode_selection_from_play_mode(self.selected_play_mode)
        if self.selected_game_group == "真随机":
            self.selected_game_group = "随机"
        if self.selected_game_group not in {"普通", "随机", "段位", "自定义"}:
            self.selected_game_group, self.selected_rule_mode = self.mode_selection_from_play_mode(self.selected_play_mode)
        allowed = self.rule_modes_for_group(self.selected_game_group)
        if self.selected_rule_mode not in allowed:
            self.selected_rule_mode = allowed[0]
        self.selected_play_mode = self.play_mode_from_selection(self.selected_game_group, self.selected_rule_mode)

    def show_mode_select(self, transition=True):
        if self.block_spectator_action("进入游戏"):
            self.show_home()
            return
        self.play_music("menu")
        self.clear(transition=transition)
        self._start_backdrop("lines")
        self._topbar("选择模式", self.show_home)
        if self.tutorial_active:
            self.tutorial_step = "mode"
            self.selected_subject = "物理模式"
            self.selected_game_group = "普通"
            self.selected_rule_mode = "自由"
            self.selected_play_mode = "自由"
        self.normalize_mode_selection_state()

        left = tk.Frame(self.container, bg="#111725")
        left.place(x=52, y=128)
        right_panel = WobblePanel(self.container)
        right_panel.place(relx=0.55, rely=0.13, relwidth=0.41, relheight=0.80)
        right = right_panel.content

        subject_locked = self.selected_game_group == "随机"
        tk.Label(
            left,
            text="学科选择",
            fg="#53627f" if subject_locked else "#8fb6ff",
            bg="#111725",
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 12))
        subject_row = tk.Frame(left, bg="#111725")
        subject_row.pack(anchor="w", pady=(0, 8 if subject_locked else 34))
        self.choice_button(
            subject_row,
            "物理",
            subject_locked or self.selected_subject == "物理模式",
            lambda: self.set_mode_choice(subject="物理模式"),
            enabled=not subject_locked,
        ).grid(row=0, column=0, padx=(0, 14))
        self.choice_button(
            subject_row,
            "数学",
            subject_locked or self.selected_subject == "数学模式",
            lambda: self.set_mode_choice(subject="数学模式"),
            enabled=not subject_locked,
        ).grid(row=0, column=1, padx=14)
        if subject_locked:
            tk.Label(
                left,
                text="随机模式默认合并物理与数学词库",
                fg="#69738d",
                bg="#111725",
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(anchor="w", pady=(0, 28))

        tk.Label(left, text="游戏模式", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(0, 10))

        group_row = tk.Frame(left, bg="#111725")
        group_row.pack(anchor="w", pady=(0, 26))
        group_options = [("普通", "#9ff2b2"), ("随机", "#c4b5fd"), ("段位", "#f6d36b"), ("自定义", "#ffbd7e")]
        for index, (label, accent) in enumerate(group_options):
            self.choice_button(
                group_row,
                label,
                self.selected_game_group == label,
                lambda label=label: self.set_mode_choice(game_group=label),
                accent=accent,
                width=150,
                height=54,
            ).grid(row=0, column=index, padx=(0, 12), sticky="w")

        tk.Label(left, text="玩法选择", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(0, 10))
        play_grid = tk.Frame(left, bg="#111725")
        play_grid.pack(anchor="w")
        accents = {
            "自由": "#9ff2b2",
            "限时": "#f6d36b",
            "线索": "#7ed6ff",
            "字谜": "#b7f6ff",
            "自定义": "#ffbd7e",
        }
        for index, rule in enumerate(self.rule_modes_for_group(self.selected_game_group)):
            self.choice_button(
                play_grid,
                rule,
                self.selected_rule_mode == rule,
                lambda rule=rule: self.set_mode_choice(rule_mode=rule),
                accent=accents.get(rule, "#8fb6ff"),
                width=150 if self.selected_game_group != "自定义" else 220,
                height=54,
            ).grid(row=0, column=index, padx=(0, 12), pady=5, sticky="w")
        next_button = HoverButton(left, "下一步", self.confirm_mode_choice, width=250, height=60, accent="#8fb6ff")
        next_button.pack(anchor="w", pady=(22, 0))

        self.render_mode_explanation(right)
        if self.tutorial_active and self.tutorial_step == "mode":
            self.render_tutorial_overlay(
                next_button,
                "第二步：选择物理自由练习",
                "教程已经帮你固定为“物理 / 普通 / 自由”。点击高光的“下一步”，去选择入门难度。",
            )

    def choice_button(self, parent, text, selected, command, accent="#8fb6ff", width=220, height=62, enabled=True):
        button = HoverButton(parent, f"{'◆ ' if selected else ''}{text}", command, width=width, height=height, accent=accent if selected else "#4b5877")
        if not enabled:
            button.disable()
        return button

    def set_mode_choice(self, subject=None, play_mode=None, game_group=None, rule_mode=None):
        if subject:
            self.selected_subject = subject
        if play_mode:
            self.selected_game_group, self.selected_rule_mode = self.mode_selection_from_play_mode(play_mode)
        if game_group:
            self.selected_game_group = game_group
            allowed = self.rule_modes_for_group(game_group)
            if self.selected_rule_mode not in allowed:
                self.selected_rule_mode = allowed[0]
        if rule_mode:
            self.selected_rule_mode = rule_mode
        self.normalize_mode_selection_state()
        self.show_mode_select(transition=False)

    def confirm_mode_choice(self):
        self.custom_mode = False
        self.rank_mode = False
        self.crossword_random = False
        self.true_random_mode = False
        self.random_group_mode = False
        self.custom_config = {}
        if self.tutorial_active:
            self.tutorial_step = "difficulty"
            self.selected_subject = "物理模式"
            self.selected_game_group = "普通"
            self.selected_rule_mode = "自由"
            self.selected_play_mode = "自由"
        self.normalize_mode_selection_state()
        selected = self.selected_play_mode
        random_base = self.random_play_mode_base(selected)
        if random_base:
            self.random_group_mode = True
            self.play_mode = random_base
            self.mode = "随机"
            self.show_difficulty()
            return
        self.play_mode = selected
        if self.play_mode == "自定义":
            self.show_custom_config()
            return
        if self.play_mode in {"限时段位", "线索段位"}:
            self.mode = self.selected_subject
            self.rank_kind = {"限时段位": "free", "线索段位": "clue"}[self.play_mode]
            self.show_rank_select()
            return
        if self.play_mode == "字谜段位":
            self.mode = self.selected_subject
            self.rank_kind = "crossword"
            self.show_rank_select()
            return
        self.mode = self.selected_subject
        self.show_difficulty()

    def render_mode_explanation(self, parent):
        for child in parent.winfo_children():
            child.destroy()
        subject_text = "物理词库" if self.selected_subject == "物理模式" else "数学词库"
        self.normalize_mode_selection_state()
        selected = self.selected_play_mode
        group_name = f"{self.selected_game_group}模式" if self.selected_game_group != "自定义" else "自定义模式"
        base_selected = self.random_play_mode_base(selected) or self.selected_rule_mode
        random_scope = self.selected_game_group == "随机"
        mode_subject_text = "物理和数学同难度词库" if random_scope else subject_text
        if selected == "自定义":
            title = "自定义模式"
            lines = [
                "进入玩法编辑器，制作首字母、限时、线索、字谜或仿段位练习。",
                "可以细调词库、词长、难度、提示、掩码、线索和字谜生成参数。",
                "记录会保存，但不计总积分、Rating、成就和正式段位。",
            ]
        elif selected == "限时段位":
            title = "段位 / 限时"
            lines = [
                f"{subject_text}专属的正式限时首字母挑战。",
                "沿用旧首字母段位进度、通过总分、段位标识和称号。",
                "必须在总时限内全题答对；错误提交可以继续尝试。",
                "通过后会解锁可佩戴的段位标识和称号。",
            ]
        elif selected == "线索段位":
            title = "线索段位"
            lines = [
                f"{subject_text}专属的线索资格挑战。",
                "全部题目换成线索题，不显示首字母，只显示答案字数。",
                "每段由固定题组构成，必须全题答对并且未超时。",
                "段位数量、目标难度、时限和提示参数与限时段位一致。",
                "通过后会解锁可佩戴的段位标识和称号。",
            ]
        elif selected == "字谜段位":
            title = "字谜段位"
            lines = [
                f"{subject_text}专属的字谜资格挑战。",
                "格数、词量、词条难度、掩码和时限会逐步提升。",
                "在总时限内完成整张字谜才算通过。",
                "通过后会解锁可佩戴的字谜段位标识和称号。",
            ]
        elif base_selected == "自由":
            title = "自由模式"
            lines = [
                f"从{mode_subject_text}中按难度抽取单题。",
                "答对后立即结算，适合练习和熟悉词库。",
                "随机模式会跨物理和数学读取同一难度；下一步可选“真·随机”读取全部词库。" if random_scope else "混合模式会读取该学科下全部词库。",
            ]
        elif base_selected == "限时":
            title = "限时模式"
            lines = [
                f"从{mode_subject_text}中连续出题，限时 5 分钟。",
                "答对后立刻进入下一题。",
                "最终看答对题数、原始积分和计入总积分。",
            ]
        elif base_selected == "线索":
            title = "线索模式"
            lines = [
                f"从{mode_subject_text}中抽取词条，但不显示首字母。",
                "初始给两句描述，继续提示会从第三条线索开始扣分。",
                "从入门到噩梦都与自由模式使用同一套词库范围和抽题参数。",
            ]
            if random_scope:
                lines.append("线索的“真·随机”会读取物理和数学全部词库。")
        elif base_selected == "字谜":
            title = "字谜模式"
            lines = [
                f"从{mode_subject_text}中抽取多词，在矩形网格里尽量按相同汉字交叉。",
                "右侧填格，左侧按编号输入答案；答对一个词就会把对应汉字填入网格。",
                "随机字谜会跨物理和数学同难度词库生成；“真·随机”难度会读取全部词库。" if random_scope else "普通、困难和噩梦可能出现首字母掩码。",
            ]
        else:
            title = "自由模式"
            lines = [
                f"从{mode_subject_text}中按难度抽取单题。",
                "答对后立即结算，适合练习和熟悉词库。",
            ]
        tk.Label(parent, text=group_name, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=26, pady=(24, 4))
        tk.Label(parent, text=title, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=26, pady=(0, 14))
        for line in lines:
            tk.Label(parent, text=self.smart_wrap_text(line, 24), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 13)).pack(anchor="w", padx=26, pady=6)
        if selected == "自定义":
            footer = "下一步进入自定义配置页。"
        elif selected in {"限时段位", "线索段位", "字谜段位"}:
            footer = "下一步选择段位。限时和线索段位不计总积分和 Rating；字谜段位按整图难度、用时和积分计入 Rating。"
        else:
            footer = "下一步选择选词难度。难度会影响词条难度分布、提示代价、掩码或破碎线索概率和最终 Rating。"
        tk.Label(parent, text=self.smart_wrap_text(footer, 23), fg="#9ca8c7", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11)).pack(anchor="w", padx=26, pady=(18, 0))

    def show_custom_config(self):
        if self.block_spectator_action("进入自定义玩法"):
            self.show_home()
            return
        self.play_music("menu")
        self.clear()
        self._start_backdrop("grid")
        self._topbar("自定义玩法编辑器", self.show_mode_select)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=2, minsize=280)
        frame.grid_columnconfigure(1, weight=4, minsize=480)
        frame.grid_columnconfigure(2, weight=3, minsize=340)

        blueprint_panel = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        blueprint_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        params_panel = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        params_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 14))
        right = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        right.grid(row=0, column=2, sticky="nsew")
        blueprint = self.make_scroll_frame(blueprint_panel, bg="#182033")
        params = self.make_scroll_frame(params_panel, bg="#182033")

        self.custom_subject_var = tk.StringVar(value=self.selected_subject)
        self.custom_play_var = tk.StringVar(value="首字母")
        self.custom_timing_var = tk.StringVar(value="不限时")
        self.custom_challenge_var = tk.StringVar(value="不开启")
        self.custom_diff_min_var = tk.StringVar(value="1")
        self.custom_diff_max_var = tk.StringVar(value="10")
        self.custom_len_min_var = tk.StringVar(value="1")
        self.custom_len_max_var = tk.StringVar(value="12")
        self.custom_free_hint_var = tk.StringVar(value="自动")
        self.custom_mask_var = tk.StringVar(value="自动")
        self.custom_hint_cooldown_var = tk.StringVar(value="自动")
        self.custom_library_hint_var = tk.StringVar(value="自动")
        self.custom_mask_mode_var = tk.StringVar(value="自动")
        self.custom_mask_fixed_var = tk.StringVar(value="1")
        self.custom_mask_probability_var = tk.StringVar(value="30")
        self.custom_mask_max_var = tk.StringVar(value="3")
        self.custom_fragment_var = tk.StringVar(value="25")
        self.custom_clue_initial_var = tk.StringVar(value="2")
        self.custom_clue_reveal_var = tk.StringVar(value="1")
        self.custom_minutes_var = tk.StringVar(value="5")
        self.custom_challenge_count_var = tk.StringVar(value="5")
        self.custom_crossword_width_var = tk.StringVar(value="15")
        self.custom_crossword_height_var = tk.StringVar(value="15")
        self.custom_crossword_words_var = tk.StringVar(value="自动")
        self.custom_crossword_shape_var = tk.StringVar(value="随机")
        self.custom_crossword_triangle_var = tk.StringVar(value="15")
        self.custom_crossword_hex_var = tk.StringVar(value="15")

        tk.Label(blueprint, text="玩法蓝图", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 21, "bold")).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(
            blueprint,
            text="自定义是练习沙盒：可复刻正式玩法，但不计正式奖励。",
            fg="#9ca8c7",
            bg="#182033",
            justify="left",
            wraplength=230,
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor="w", padx=24, pady=(0, 14))
        self.custom_option_group(blueprint, "玩法", self.custom_play_var, ["首字母", "限时", "线索", "字谜"], self.update_custom_option_states)
        self.custom_option_group(blueprint, "时间", self.custom_timing_var, ["不限时", "限时"], self.update_custom_option_states)
        self.custom_minutes_entries = self.custom_range_inputs(blueprint, "时长（分钟）", self.custom_minutes_var, None, note="1-30")
        self.custom_option_group(blueprint, "仿段位挑战", self.custom_challenge_var, ["不开启", "开启"], self.update_custom_option_states)
        self.custom_challenge_entries = self.custom_range_inputs(blueprint, "目标题数", self.custom_challenge_count_var, None, note="1-50；字谜按整图完成")
        HoverButton(blueprint, "开始自定义", self.start_custom_game, width=218, height=60, accent="#ffbd7e").pack(anchor="w", padx=24, pady=(22, 28))

        tk.Label(params, text="生成参数", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 21, "bold")).pack(anchor="w", padx=26, pady=(24, 10))
        self.custom_option_group(params, "学科范围", self.custom_subject_var, ["物理模式", "数学模式", "全部"], self.refresh_custom_file_list)
        self.custom_range_inputs(params, "基础难度", self.custom_diff_min_var, self.custom_diff_max_var)
        self.custom_range_inputs(params, "中文词长", self.custom_len_min_var, self.custom_len_max_var)
        self.custom_option_group(params, "免费字词提示", self.custom_free_hint_var, ["自动", "0", "1", "2", "3", "4", "5"], self.update_custom_option_states)
        self.custom_option_group(params, "提示冷却", self.custom_hint_cooldown_var, ["自动", "0", "15", "30", "60", "120"], self.update_custom_option_states)
        self.custom_option_group(params, "词库提示", self.custom_library_hint_var, ["自动", "0", "1", "2", "3", "5", "10"], self.update_custom_option_states)

        tk.Label(params, text="首字母 / 掩码", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 4))
        self.custom_option_group(params, "掩码策略", self.custom_mask_mode_var, ["自动", "无", "固定", "概率"], self.update_custom_option_states)
        self.custom_range_inputs(params, "固定掩码数", self.custom_mask_fixed_var, None, note="0-6")
        self.custom_range_inputs(params, "掩码概率（%）", self.custom_mask_probability_var, None, note="0-100")
        self.custom_range_inputs(params, "最多掩码", self.custom_mask_max_var, None, note="0-6")

        tk.Label(params, text="线索", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 4))
        self.custom_option_group(params, "破碎线索概率", self.custom_fragment_var, ["0", "25", "40", "100"], self.update_custom_option_states)
        self.custom_range_inputs(params, "初始线索数", self.custom_clue_initial_var, None, note="1-5；默认 2")
        self.custom_range_inputs(params, "每次追加", self.custom_clue_reveal_var, None, note="1-5")

        tk.Label(params, text="字谜", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 4))
        self.custom_range_inputs(params, "网格宽高", self.custom_crossword_width_var, self.custom_crossword_height_var, note="5-30")
        self.custom_range_inputs(params, "目标词数", self.custom_crossword_words_var, None, note="自动或 5-160")
        self.custom_option_group(params, "格形", self.custom_crossword_shape_var, ["方格", "三角", "六边", "随机"], self.update_custom_option_states)
        self.custom_range_inputs(params, "随机三角概率（%）", self.custom_crossword_triangle_var, None, note="0-100")
        self.custom_range_inputs(params, "随机六边概率（%）", self.custom_crossword_hex_var, None, note="0-100")
        self.update_custom_option_states()

        tk.Label(right, text="词库多选", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(right, text="默认选中当前范围全部词库。按住 Ctrl 可以增减选择。", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(anchor="w", padx=24)
        list_shell = tk.Frame(right, bg="#182033")
        list_shell.pack(fill="both", expand=True, padx=24, pady=(14, 10))
        self.custom_file_listbox = tk.Listbox(
            list_shell,
            selectmode=tk.EXTENDED,
            exportselection=False,
            fg="#dce6ff",
            bg="#101827",
            selectforeground="#111725",
            selectbackground="#9ff2b2",
            relief="flat",
            font=("Microsoft YaHei UI", 10),
            height=22,
        )
        file_scrollbar = tk.Scrollbar(list_shell, orient="vertical", command=self.custom_file_listbox.yview)
        self.custom_file_listbox.configure(yscrollcommand=file_scrollbar.set)
        self.custom_file_listbox.pack(side="left", fill="both", expand=True)
        file_scrollbar.pack(side="right", fill="y")
        self.custom_file_listbox.bind("<<ListboxSelect>>", lambda _event: self.update_custom_summary())
        self.bind_scroll_wheel(list_shell, self.custom_file_listbox)
        self.custom_summary_label = tk.Label(right, text="", fg="#c8d2ee", bg="#182033", justify="left", anchor="w", wraplength=300, font=("Microsoft YaHei UI", 10, "bold"))
        self.custom_summary_label.pack(fill="x", padx=24, pady=(0, 18))
        self.refresh_custom_file_list()

    def custom_option_group(self, parent, title, variable, options, command):
        tk.Label(parent, text=title, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=30, pady=(11, 5))
        row = tk.Frame(parent, bg="#182033")
        row.pack(anchor="w", padx=28)
        for option in options:
            tk.Radiobutton(
                row,
                text=option.replace("模式", ""),
                value=option,
                variable=variable,
                command=command,
                fg="#dce6ff",
                bg="#182033",
                activeforeground="#fff2bd",
                activebackground="#182033",
                selectcolor="#101827",
                font=("Microsoft YaHei UI", 11, "bold"),
            ).pack(side="left", padx=4)

    def custom_range_inputs(self, parent, title, first_var, second_var, note=""):
        tk.Label(parent, text=title, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=30, pady=(11, 5))
        row = tk.Frame(parent, bg="#182033")
        row.pack(anchor="w", padx=30)
        entries = []
        for index, variable in enumerate([first_var] if second_var is None else [first_var, second_var]):
            entry = tk.Entry(row, textvariable=variable, width=6, justify="center", fg="#fff8dc", bg="#101827", insertbackground="#fff8dc", relief="flat", font=("Consolas", 13, "bold"))
            entry.grid(row=0, column=index * 2, ipady=5)
            entries.append(entry)
            if second_var is not None and index == 0:
                tk.Label(row, text=" 至 ", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 11)).grid(row=0, column=1)
        if note:
            tk.Label(row, text=f"  {note}", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 10, "bold")).grid(row=0, column=3 if second_var is not None else 1, padx=(6, 0), sticky="w")
        return entries

    def update_custom_option_states(self):
        play_kind = self.custom_play_var.get() if self.custom_play_var else "首字母"
        timed_enabled = self.custom_timing_var is not None and (self.custom_timing_var.get() == "限时" or play_kind == "限时")
        challenge_enabled = self.custom_challenge_var is not None and self.custom_challenge_var.get() == "开启"
        if play_kind == "限时" and self.custom_timing_var is not None:
            self.custom_timing_var.set("限时")
        for entry in self.custom_minutes_entries:
            entry.configure(state="normal" if timed_enabled else "disabled", disabledforeground="#64708f")
        for entry in self.custom_challenge_entries:
            entry.configure(state="normal" if challenge_enabled else "disabled", disabledforeground="#64708f")
        self.update_custom_summary()

    def update_custom_summary(self):
        if not self.custom_summary_label:
            return
        subject = self.custom_subject_var.get() if self.custom_subject_var else self.selected_subject
        play = self.custom_play_var.get() if self.custom_play_var else "首字母"
        timing = "限时" if self.custom_timing_var and self.custom_timing_var.get() == "限时" else "不限时"
        if play == "限时":
            timing = "限时"
        challenge = self.custom_challenge_var.get() if self.custom_challenge_var else "不开启"
        files = len(self.custom_file_paths)
        selected = len(self.custom_file_listbox.curselection()) if self.custom_file_listbox else files
        parts = [
            f"玩法：{play} / {timing}",
            f"挑战：{challenge}",
            f"词库：{selected}/{files} 个文件",
            f"难度：{self.custom_diff_min_var.get()}-{self.custom_diff_max_var.get()}",
            f"词长：{self.custom_len_min_var.get()}-{self.custom_len_max_var.get()}",
        ]
        if play == "字谜":
            parts.append(f"字谜：{self.custom_crossword_width_var.get()}×{self.custom_crossword_height_var.get()} / {self.custom_crossword_words_var.get()} 词 / {self.custom_crossword_shape_var.get()}")
        self.custom_summary_label.config(text="\n".join(parts))

    def refresh_custom_file_list(self):
        if not self.custom_file_listbox:
            return
        subject = self.custom_subject_var.get() if self.custom_subject_var else self.selected_subject
        if subject == "全部":
            files = self.library.list_files()
        else:
            files = self.library.list_files(subject)
        self.custom_file_paths = files
        self.custom_file_listbox.delete(0, tk.END)
        for path in files:
            try:
                display = path.relative_to(WORDS_DIR).as_posix()
            except ValueError:
                display = path.name
            self.custom_file_listbox.insert(tk.END, display)
        if files:
            self.custom_file_listbox.selection_set(0, tk.END)
        self.update_custom_summary()

    @staticmethod
    def parse_int_var(variable, default, low, high):
        try:
            value = int(float(variable.get()))
        except (TypeError, ValueError, tk.TclError):
            value = default
        return max(low, min(high, value))

    def start_custom_game(self):
        if self.block_spectator_action("开始游戏"):
            return
        selected = list(self.custom_file_listbox.curselection()) if self.custom_file_listbox else []
        files = [self.custom_file_paths[index] for index in selected if 0 <= index < len(self.custom_file_paths)]
        if not files:
            messagebox.showwarning("还没选词库", "至少选择一个 CSV 词库。")
            return
        try:
            terms, files = self.library.load_files(files)
        except Exception as exc:
            messagebox.showerror("词库加载失败", str(exc))
            return
        diff_min = self.parse_int_var(self.custom_diff_min_var, 1, 1, 12)
        diff_max = self.parse_int_var(self.custom_diff_max_var, 12, 1, 12)
        len_min = self.parse_int_var(self.custom_len_min_var, 1, 1, 30)
        len_max = self.parse_int_var(self.custom_len_max_var, 12, 1, 30)
        if diff_min > diff_max:
            diff_min, diff_max = diff_max, diff_min
        if len_min > len_max:
            len_min, len_max = len_max, len_min
        terms = [term for term in terms if diff_min <= term.difficulty <= diff_max and len_min <= len(term.chinese) <= len_max]
        if not terms:
            messagebox.showwarning("没有可用词条", "当前过滤条件下没有词条。")
            return
        play_kind = self.custom_play_var.get() if self.custom_play_var else "首字母"
        timed_enabled = self.custom_timing_var is not None and (self.custom_timing_var.get() == "限时" or play_kind == "限时")
        challenge_enabled = self.custom_challenge_var is not None and self.custom_challenge_var.get() == "开启"
        challenge_target = self.parse_int_var(self.custom_challenge_count_var, 5, 1, 50)
        minutes = self.parse_int_var(self.custom_minutes_var, 5, 1, 30)
        library_hint_limit = 0
        if self.custom_library_hint_var and self.custom_library_hint_var.get() != "自动":
            library_hint_limit = self.parse_int_var(self.custom_library_hint_var, 0, 0, 30)
        crossword_width = self.parse_int_var(self.custom_crossword_width_var, 15, 5, 30)
        crossword_height = self.parse_int_var(self.custom_crossword_height_var, 15, 5, 30)
        raw_crossword_words = str(self.custom_crossword_words_var.get() if self.custom_crossword_words_var else "").strip()
        if raw_crossword_words in {"", "自动"}:
            crossword_words = 0
        else:
            crossword_words = self.parse_int_var(self.custom_crossword_words_var, 0, 5, 160)
        self.custom_mode = True
        self.rank_mode = False
        self.crossword_mode = False
        self.custom_session_id = uuid.uuid4().hex
        self.custom_config = {
            "subject": self.custom_subject_var.get(),
            "play_kind": play_kind,
            "timed_enabled": 1 if timed_enabled else 0,
            "free_hint": self.custom_free_hint_var.get(),
            "mask": self.custom_mask_var.get(),
            "hint_cooldown": self.custom_hint_cooldown_var.get() if self.custom_hint_cooldown_var else "自动",
            "library_hint_limit": "自动" if (self.custom_library_hint_var is None or self.custom_library_hint_var.get() == "自动") else library_hint_limit,
            "mask_mode": self.custom_mask_mode_var.get() if self.custom_mask_mode_var else "自动",
            "mask_fixed": self.parse_int_var(self.custom_mask_fixed_var, 1, 0, 6),
            "mask_probability": self.parse_int_var(self.custom_mask_probability_var, 30, 0, 100),
            "mask_max": self.parse_int_var(self.custom_mask_max_var, 3, 0, 6),
            "fragment_probability": int(self.custom_fragment_var.get()) / 100,
            "clue_initial_lines": self.parse_int_var(self.custom_clue_initial_var, 2, 1, 5),
            "clue_reveal_count": self.parse_int_var(self.custom_clue_reveal_var, 1, 1, 5),
            "minutes": minutes,
            "challenge_enabled": 1 if challenge_enabled else 0,
            "challenge_target": challenge_target,
            "difficulty_min": diff_min,
            "difficulty_max": diff_max,
            "length_min": len_min,
            "length_max": len_max,
            "crossword_width": crossword_width,
            "crossword_height": crossword_height,
            "crossword_words": crossword_words,
            "crossword_shape": self.custom_crossword_shape_var.get() if self.custom_crossword_shape_var else "随机",
            "crossword_triangle_probability": self.parse_int_var(self.custom_crossword_triangle_var, 15, 0, 100),
            "crossword_hex_probability": self.parse_int_var(self.custom_crossword_hex_var, 15, 0, 100),
        }
        self.mode = "自定义"
        self.play_mode = "自定义"
        self.difficulty = "自定义"
        self.terms = terms
        self.library_files = files
        self.scope_text = f"自定义词库：{self.library.scope_text(files)}"
        self.timed_deadline = None
        self.timed_correct = 0
        self.timed_score = 0
        if timed_enabled:
            self.timed_deadline = time.perf_counter() + self.custom_config["minutes"] * 60
        if play_kind == "字谜":
            self.start_crossword_game("自定义")
            return
        self.start_round()

    def show_rank_select(self):
        if self.block_spectator_action("进入段位挑战"):
            self.show_home()
            return
        self.play_music("rank_menu")
        self.clear()
        self._start_backdrop("lines")
        rank_kind = getattr(self, "rank_kind", "free")
        rank_label = rank_kind_label(rank_kind)
        progress_key = rank_progress_key(self.mode, rank_kind)
        self._topbar(f"{subject_label(self.mode)}{rank_label}挑战", self.show_mode_select)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=28, pady=(0, 26))
        progress = read_rank_progress()
        subject_info = (progress.get("subjects") or {}).get(progress_key, {})
        highest = rank_highest_passed(subject_info)
        passed_ids = set(rank_passed_ids(subject_info))
        reveal_hidden = self.admin_reveal_hidden_enabled()
        if reveal_hidden:
            visible_ranks = [rank for rank in RANK_CHALLENGES if rank["id"] <= rank_count_for_kind(rank_kind)]
        else:
            visible_ranks = visible_rank_challenges(subject_info, rank_kind)

        left = tk.Frame(frame, bg="#111725", width=360)
        left.pack(side="left", fill="y", padx=(0, 24))
        left.pack_propagate(False)
        right = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="选择段位", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(6, 14))
        tk.Label(
            left,
            text="已通过的段位会带有菱形标记。\n可挑战段位会随进度开放。",
            fg="#7f8caf",
            bg="#111725",
            justify="left",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor="w", fill="x", pady=(0, 12))
        button_area = tk.Frame(left, bg="#111725")
        button_area.pack(fill="both", expand=True)
        button_list = self.make_scroll_frame(button_area, bg="#111725")
        button_height = 34
        for index, rank in enumerate(visible_ranks):
            passed = rank["id"] in passed_ids
            unlocked = reveal_hidden or rank_is_unlocked(subject_info, rank["id"], rank_kind)
            accent = "#9ff2b2" if passed else ("#9fb7ff" if unlocked else "#5c6680")
            label = f"{'◆ ' if passed else ''}{rank['name']}"
            if not unlocked:
                label = f"锁定  {rank['name']}"
            button = HoverButton(button_list, label, lambda rank_id=rank["id"]: self.start_rank_challenge(rank_id), width=300, height=button_height, accent=accent)
            button.pack(anchor="w", pady=2)
            if not unlocked:
                button.disable()

        header = tk.Frame(right, bg="#182033")
        header.pack(fill="x", padx=34, pady=(28, 16))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text=f"{subject_label(self.mode)}{rank_label}", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).grid(row=0, column=0, sticky="w")
        if rank_kind == "crossword":
            intro = "字谜整图挑战：边长、词量和难度逐步提升。"
        elif rank_kind == "timed":
            intro = "旧限时首字母挑战：保留历史轨道兼容。"
        elif rank_kind == "free":
            intro = "限时首字母挑战，沿用旧首字母段位进度和称号。"
        else:
            intro = "线索题挑战：不显示首字母，提示会逐步追加线索。"
        tk.Label(header, text=intro, fg="#dce6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 11)).grid(row=1, column=0, sticky="w", pady=(8, 0))
        if reveal_hidden:
            tk.Label(header, text="管理员隐藏已开启：锁定和隐藏段位已临时开放。", fg="#f6d36b", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(8, 0))
        summary_text = f"当前最高通过  Class {highest:02d}" if highest else "当前还没有通过段位"
        tk.Label(header, text=summary_text, fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).grid(row=0, column=1, sticky="e", padx=(20, 0))
        tk.Label(
            header,
            text="每张卡片显示时限、题数/词量、提示冷却或网格规格；通过后会记录最高总分。",
            fg="#7f8caf",
            bg="#182033",
            justify="right",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).grid(row=1, column=1, sticky="e", padx=(20, 0), pady=(8, 0))

        list_shell = tk.Frame(right, bg="#182033")
        list_shell.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        rank_grid = self.make_scroll_frame(list_shell, bg="#182033")
        columns = 2 if max(self.winfo_width(), int(self.player_settings.get("window_width", 1274))) >= 1180 else 1
        for column in range(columns):
            rank_grid.grid_columnconfigure(column, weight=1, uniform="rank")
        wraplength = 460 if columns == 2 else 820
        for index, rank in enumerate(visible_ranks):
            self.render_rank_select_card(rank_grid, index, columns, rank, subject_info, passed_ids, wraplength)

    def render_rank_select_card(self, parent, index, columns, rank, subject_info, passed_ids, wraplength):
        passed = rank["id"] in passed_ids
        reveal_hidden = self.admin_reveal_hidden_enabled()
        official_unlocked = rank_is_unlocked(subject_info, rank["id"], getattr(self, "rank_kind", "free"))
        unlocked = reveal_hidden or official_unlocked
        bg = "#182f2b" if passed else ("#171f31" if unlocked else "#141a28")
        border = "#4cae82" if passed else ("#30384e" if unlocked else "#252d40")
        title_color = "#b8ffd7" if passed else ("#dce6ff" if unlocked else "#8d96ad")
        muted = "#8fa0c2" if not passed else "#a7dcc0"
        card = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1)
        card.grid(row=index // columns, column=index % columns, sticky="nsew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(card, bg=bg)
        title_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(13, 5))
        title_row.grid_columnconfigure(0, weight=1)
        tk.Label(title_row, text=rank["name"], fg=title_color, bg=bg, font=("Microsoft YaHei UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        score = rank_pass_score(subject_info, rank["id"])
        state = f"最高总分 {score}" if score is not None else ("已通过" if passed else ("管理员开启" if (reveal_hidden and not official_unlocked) else ("可挑战" if unlocked else "锁定")))
        tk.Label(title_row, text=state, fg="#9ff2b2" if passed else "#7f8caf", bg=bg, font=("Microsoft YaHei UI", 10, "bold"), anchor="e").grid(row=0, column=1, sticky="e", padx=(12, 0))

        if getattr(self, "rank_kind", "free") == "crossword":
            size = self.crossword_rank_size_for_id(rank["id"])
            words = self.crossword_rank_word_count_for_id(rank["id"])
            seconds = self.crossword_rank_seconds_for_id(rank["id"])
            meta = f"{format_rank_time(seconds)}  ·  {size}×{size}  ·  约 {words} 词"
        else:
            meta = (
                f"{format_rank_time(rank['seconds'])}  ·  {len(rank['requirements'])} 题  ·  "
                f"提示 {rank_hint_cooldown_seconds(rank['id'])} 秒 / {rank_hint_limit(rank['id'])} 次"
            )
        tk.Label(card, text=meta, fg="#fff2bd", bg=bg, justify="left", anchor="w", font=("Microsoft YaHei UI", 10, "bold")).grid(row=1, column=0, sticky="ew", padx=16)
        if getattr(self, "rank_kind", "free") == "crossword":
            low, high, _center = self.crossword_rank_difficulty_window_for_id(rank["id"])
            if low == high:
                req_text = f"词条难度 {low}（{self.difficulty_label_for_value(low)}）"
            else:
                req_text = f"词条难度 {low}-{high}（{self.difficulty_label_for_value(low)}-{self.difficulty_label_for_value(high)}）"
        else:
            req_text = "、".join(f"{difficulty}≥{target:g}" for difficulty, target in rank["requirements"])
        tk.Label(card, text=req_text, fg=muted, bg=bg, justify="left", anchor="w", wraplength=wraplength, font=("Microsoft YaHei UI", 9, "bold")).grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 14))

    def crossword_rank_size_for_id(self, rank_id):
        rank_id = max(1, min(20, int(rank_id or 1)))
        return int(round(8 + (rank_id - 1) * 22 / 19))

    def crossword_rank_word_count_for_id(self, rank_id):
        rank_id = max(1, min(20, int(rank_id or 1)))
        if self is None:
            size = int(round(8 + (rank_id - 1) * 22 / 19))
            high_rank_centers = {16: 10.0, 17: 10.5, 18: 11.0, 19: 11.5, 20: 12.0}
            center = high_rank_centers.get(rank_id, rank_target_difficulty(rank_id))
            if center <= 2:
                difficulty = "入门"
            elif center <= 4:
                difficulty = "简单"
            elif center <= 7:
                difficulty = "普通"
            elif center <= 10:
                difficulty = "困难"
            else:
                difficulty = "噩梦"
        else:
            size = self.crossword_rank_size_for_id(rank_id)
            _low, _high, center = self.crossword_rank_difficulty_window_for_id(rank_id)
            difficulty = self.difficulty_label_for_value(center)
        return target_word_count_for_size(size, difficulty=difficulty)

    def crossword_rank_seconds_for_id(self, rank_id):
        rank_id = max(1, min(20, int(rank_id or 1)))
        return int(round(8 * 60 + (rank_id - 1) * (25 * 60 - 8 * 60) / 19))

    def difficulty_label_for_value(self, value):
        try:
            difficulty = int(round(float(value)))
        except (TypeError, ValueError):
            difficulty = 5
        if difficulty <= 2:
            return "入门"
        if difficulty <= 4:
            return "简单"
        if difficulty <= 7:
            return "普通"
        if difficulty <= 10:
            return "困难"
        return "噩梦"

    def crossword_rank_difficulty_window_for_id(self, rank_id):
        rank_id = max(1, min(20, int(rank_id or 1)))
        center = rank_target_difficulty(rank_id)
        if rank_id == 1:
            return 1, 2, center
        high_rank_windows = {
            16: (9, 11, 10.0),
            17: (10, 11, 10.5),
            18: (10, 12, 11.0),
            19: (11, 12, 11.5),
            20: (11, 12, 12.0),
        }
        if rank_id in high_rank_windows:
            return high_rank_windows[rank_id]
        low = max(1, int(center - 1.0))
        high = min(12, int(center + 1.0))
        return low, high, center

    def load_crossword_rank_terms(self, rank):
        all_terms, files = self.library.load(self.mode, "混合模式")
        low, high, center = self.crossword_rank_difficulty_window_for_id(rank["id"])
        target_words = self.crossword_rank_word_count_for_id(rank["id"])
        if int(rank["id"]) in {1, 20}:
            minimum_pool = target_words
        else:
            minimum_pool = max(target_words * 4, 60)
        usable = [term for term in all_terms if len(getattr(term, "initials", "") or "") == len(getattr(term, "chinese", "") or "")]
        primary = [term for term in usable if low <= int(getattr(term, "difficulty", 5) or 5) <= high]
        if len(primary) < minimum_pool:
            primary_keys = {(term.chinese, term.initials) for term in primary}
            fallback = sorted(
                (term for term in usable if (term.chinese, term.initials) not in primary_keys),
                key=lambda term: (
                    abs(int(getattr(term, "difficulty", 5) or 5) - center),
                    abs(int(getattr(term, "difficulty", 5) or 5) - low),
                    random.random(),
                ),
            )
            primary.extend(fallback[: max(0, minimum_pool - len(primary))])
        random.shuffle(primary)
        return primary, sorted(set(files), key=str)

    def start_rank_challenge(self, rank_id):
        if self.block_spectator_action("开始段位挑战"):
            return
        rank = rank_by_id(rank_id)
        rank_kind = normalize_rank_kind(getattr(self, "rank_kind", "free"))
        progress_key = rank_progress_key(self.mode, rank_kind)
        subject_info = (read_rank_progress().get("subjects") or {}).get(progress_key, {})
        official_unlocked = rank_is_unlocked(subject_info, rank["id"], rank_kind)
        reveal_hidden = self.admin_reveal_hidden_enabled()
        if not official_unlocked and not reveal_hidden:
            messagebox.showinfo("段位未开放", "先通过前面的段位，再来挑战这一段。")
            self.show_rank_select()
            return
        self.custom_mode = False
        self.crossword_mode = False
        self.rank_mode = True
        self.rank_kind = rank_kind
        if self.rank_kind == "crossword":
            self.start_crossword_rank_challenge(rank, official_unlocked=official_unlocked)
            return
        self.rank_subject = self.mode
        self.rank_id = rank["id"]
        self.rank_requirements = list(rank["requirements"])
        self.rank_question_index = 0
        self.rank_session_id = uuid.uuid4().hex
        self.rank_relaxed = False
        self.rank_target_difficulty = 0.0
        self.rank_hint_used = 0
        self.rank_session_score = 0
        self.rank_answer_history = []
        self.play_mode = rank_kind_label(self.rank_kind)
        self.difficulty = self.rank_requirements[0][0]
        self.timed_deadline = time.perf_counter() + rank["seconds"]
        self.timed_correct = 0
        self.timed_score = 0
        self.start_round()

    def start_crossword_rank_challenge(self, rank, official_unlocked=None):
        if self.block_spectator_action("开始字谜段位挑战"):
            return
        progress_key = rank_progress_key(self.mode, "crossword")
        subject_info = (read_rank_progress().get("subjects") or {}).get(progress_key, {})
        if official_unlocked is None:
            official_unlocked = rank_is_unlocked(subject_info, rank["id"], "crossword")
        reveal_hidden = self.admin_reveal_hidden_enabled()
        if not official_unlocked and not reveal_hidden:
            messagebox.showinfo("段位未开放", "先通过前面的段位，再来挑战这一段。")
            self.show_rank_select()
            return
        self.custom_mode = False
        self.rank_mode = True
        self.rank_kind = "crossword"
        self.rank_subject = self.mode
        self.rank_id = rank["id"]
        self.rank_requirements = list(rank["requirements"])
        self.rank_question_index = 0
        self.rank_session_id = uuid.uuid4().hex
        self.rank_relaxed = False
        self.rank_target_difficulty = 0.0
        self.rank_hint_used = 0
        self.rank_session_score = 0
        self.rank_answer_history = []
        self.play_mode = "字谜段位"
        self.crossword_rank_size = self.crossword_rank_size_for_id(self.rank_id)
        self.crossword_rank_word_count = self.crossword_rank_word_count_for_id(self.rank_id)
        self.crossword_rank_seconds = self.crossword_rank_seconds_for_id(self.rank_id)
        self.timed_deadline = time.perf_counter() + self.crossword_rank_seconds
        self.timed_correct = 0
        self.timed_score = 0
        _low, high, _center = self.crossword_rank_difficulty_window_for_id(self.rank_id)
        self.difficulty = self.difficulty_label_for_value(high)
        try:
            self.terms, self.library_files = self.load_crossword_rank_terms(rank)
            self.scope_text = f"{subject_label(self.mode)}字谜段位词库：{self.library.scope_text(self.library_files)}"
        except Exception as exc:
            messagebox.showerror("词库加载失败", str(exc))
            self.show_rank_select()
            return
        self.start_crossword_game(self.difficulty)

    def show_difficulty(self):
        self.play_music("menu")
        self.clear()
        self._start_backdrop("particles")
        if self.tutorial_active:
            self.tutorial_step = "difficulty"
            self.selected_subject = "物理模式"
            self.selected_game_group = "普通"
            self.selected_rule_mode = "自由"
            self.selected_play_mode = "自由"
            self.mode = "物理模式"
            self.play_mode = "自由"
            self.true_random_mode = False
            self.random_group_mode = False
        if self.is_true_random_mode():
            title = f"真·随机 / {self.play_mode}"
        elif self.is_random_group_mode():
            title = f"随机 / {self.play_mode}"
        elif self.play_mode == "字谜":
            title = f"{self.mode} / 字谜"
        else:
            title = f"{self.mode} / {self.play_mode}"
        self._topbar(title, self.show_mode_select)

        left = tk.Frame(self.container, bg="#111725")
        left.place(x=52, y=128)
        right_panel = WobblePanel(self.container)
        right_panel.place(relx=0.36, rely=0.13, relwidth=0.60, relheight=0.80)
        right = right_panel.content

        tk.Label(left, text="选择难度", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(0, 14))
        options = [
            ("入门", "#7fd9c6"),
            ("简单", "#9ff2b2"),
            ("普通", "#f6d36b"),
            ("困难", "#ff9b89"),
        ]
        options.append(("噩梦", "#c084fc"))
        if self.is_random_group_mode():
            options.append(("真·随机", "#c4b5fd"))
        elif self.play_mode != "字谜":
            options.append(("混合模式", "#9fb7ff"))
        intro_button = None
        for text, accent in options:
            button = HoverButton(
                left,
                text,
                lambda d=text: self.start_game(d),
                width=250,
                height=66,
                accent=accent,
            )
            if self.tutorial_active and text != "入门":
                button.disable("教程固定")
            button.pack(anchor="w", pady=9)
            if text == "入门":
                intro_button = button
        self.render_difficulty_explanation(right, options)
        if self.tutorial_active and intro_button:
            self.render_tutorial_overlay(
                intro_button,
                "第三步：选择入门难度",
                "入门题会给你最轻的起步难度。点击高光的“入门”，教程题会在真实答题页打开。",
            )

    def set_crossword_scope(self, mode_value, random_value=False):
        self.mode = mode_value
        self.crossword_random = bool(random_value)
        if not self.crossword_random and mode_value in {"物理模式", "数学模式"}:
            self.selected_subject = mode_value
        self.show_difficulty()

    def render_difficulty_explanation(self, parent, options):
        random_scope = self.is_random_group_mode()
        subject = "全部物理和数学词库" if random_scope else ("物理词库" if self.mode == "物理模式" else "数学词库")
        if self.play_mode == "限时":
            mode_text = "限时 5 分钟，答对后自动换题。"
        elif self.play_mode == "线索":
            mode_text = "不显示首字母，改用五句递进线索作答；初始显示两句，继续追加线索按规则处理。线索模式与自由模式使用同一套词库范围。"
        elif self.play_mode == "字谜":
            mode_text = "多词交叉填格：入门到噩梦约为 8/11/15/18/22 格，词量按占空比和平均词长估算。" + ("随机字谜会跨物理和数学同难度词库；真·随机会读取全部词库。" if random_scope else "")
        else:
            mode_text = "单题练习，答完后进入结算。" + ("随机模式会跨物理和数学同难度词库；真·随机会读取全部词库。" if random_scope else "")
        if random_scope and self.play_mode in {"限时", "线索"}:
            mode_text += " 入门到噩梦只限定选词难度；真·随机会改为全库五档等概率抽查。"
        tk.Label(parent, text="词库介绍", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=26, pady=(26, 12))
        tk.Label(parent, text=f"范围：{subject}", fg="#dce6ff", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=26, pady=5)
        tk.Label(parent, text=self.smart_wrap_text(mode_text, 30), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 12)).pack(anchor="w", padx=26, pady=5)
        tk.Label(parent, text="难度说明", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 8))
        descriptions = {
            "入门": "偏高中与基础词，低难高概率，免费提示更慷慨。",
            "简单": "偏核心基础概念，难度 3-4 高概率。",
            "普通": "偏大学基础和常见进阶概念，难度 5-6 高概率；首字母题可能出现 *，线索题可能出现破碎线索。",
            "困难": "偏高阶词库和更难想到的概念，难度 8-10 占比高，掩码或破碎线索概率更高。",
            "噩梦": "偏前沿和高度专门化词库，难度 10-12 占比最高；自由、限时、线索和字谜的掩码、冷却与免费提示都比困难更严苛。",
            "混合模式": "读取当前学科下全部难度文件，入门、简单、普通、困难、噩梦五档等概率抽取。",
            "真·随机": "读取物理和数学的全部词库，按中文答案去重；五档难度等概率抽取。",
        }
        for text, _accent in options:
            tk.Label(parent, text=self.smart_wrap_text(f"{text}：{descriptions[text]}", 32), fg="#c8d2ee", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11)).pack(anchor="w", padx=26, pady=4)

    def start_game(self, difficulty):
        if self.block_spectator_action("开始游戏"):
            return
        if self.tutorial_active:
            self.tutorial_step = "question"
            difficulty = "入门"
            self.selected_subject = "物理模式"
            self.selected_game_group = "普通"
            self.selected_rule_mode = "自由"
            self.selected_play_mode = "自由"
            self.mode = "物理模式"
            self.play_mode = "自由"
            self.true_random_mode = False
            self.random_group_mode = False
        self.custom_mode = False
        self.rank_mode = False
        self.crossword_mode = False
        self.custom_config = {}
        self.difficulty = difficulty
        if self.is_random_group_mode():
            self.true_random_mode = difficulty == "真·随机"
            self.mode = "真·随机" if self.true_random_mode else "随机"
        self.timed_deadline = None
        self.timed_correct = 0
        self.timed_score = 0
        try:
            self.load_terms_for_current_selection(difficulty)
        except Exception as exc:
            messagebox.showerror("词库加载失败", str(exc))
            return
        if self.play_mode == "限时":
            self.timed_deadline = time.perf_counter() + 300
        if not self.tutorial_active:
            self.complete_achievement("entered_game")
        if self.play_mode == "字谜":
            self.start_crossword_game(difficulty)
            return
        self.start_round()

    def is_crossword_random_scope(self):
        return self.play_mode == "字谜" and self.is_random_group_mode()

    def load_terms_for_current_selection(self, difficulty):
        if self.is_true_random_mode() or difficulty == "真·随机":
            self.terms, self.library_files = self.library.load_all()
            self.scope_text = f"全部物理和数学词库：{self.library.scope_text(self.library_files)}"
        elif self.is_random_group_mode():
            self.terms, self.library_files = self.library.load_all_for_difficulty(difficulty)
            self.scope_text = f"全部物理和数学{difficulty}词库：{self.library.scope_text(self.library_files)}"
        else:
            self.terms, self.library_files = self.library.load(self.mode, difficulty)
            self.scope_text = self.library.scope_text(self.library_files)
        if not self.terms:
            raise ValueError("词库为空")
