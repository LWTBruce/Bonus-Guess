import webbrowser

from ._shared import *


class RoundPlayMixin:
    def themed_legacy_color(self, color, option="bg"):
        mapper = getattr(super(RoundPlayMixin, self), "themed_legacy_color", None)
        if callable(mapper):
            return mapper(color, option)
        return color

    def daily_term_bucket_key(self):
        file_part = ",".join(sorted(str(path).replace("\\", "/") for path in self.library_files))
        return "|".join([
            self.mode or "真·随机",
            self.play_mode or "自由",
            self.difficulty or "未知",
            file_part,
        ])

    def is_custom_clue_mode(self):
        return self.custom_mode and self.custom_config.get("play_kind") == "线索"

    def is_custom_timed_enabled(self):
        if not self.custom_mode:
            return False
        return bool(self.custom_config.get("timed_enabled")) or self.custom_config.get("play_kind") in {"限时", "限时首字母"}

    def is_custom_challenge_mode(self):
        return self.custom_mode and bool(self.custom_config.get("challenge_enabled"))

    def custom_challenge_target(self):
        try:
            return max(1, min(50, int(self.custom_config.get("challenge_target") or 5)))
        except (TypeError, ValueError):
            return 5

    def custom_status_text(self):
        if self.is_custom_challenge_mode():
            target = self.custom_challenge_target()
            text = f"挑战进度 {self.timed_correct}/{target} 题"
            if self.is_custom_timed_enabled():
                text += f"\n限时 {int(self.custom_config.get('minutes', 5))} 分钟"
            return text
        if self.custom_mode and self.is_custom_timed_enabled():
            return f"已答对 {self.timed_correct} 题\n自定义练习"
        return ""

    def is_timed_mode(self):
        return self.play_mode == "限时" or self.rank_mode or self.is_custom_timed_enabled()

    def is_clue_mode(self):
        return self.play_mode == "线索" or self.is_custom_clue_mode() or (self.rank_mode and self.rank_kind == "clue")

    def can_reveal_answer(self):
        return self.is_clue_mode() or self.play_mode == "自由" or (self.custom_mode and (not self.is_timed_mode() or self.is_custom_challenge_mode()))

    def clue_fragment_probability(self):
        if self.custom_mode:
            return float(self.custom_config.get("fragment_probability", 0))
        if self.difficulty == "普通":
            return 0.25
        if self.difficulty in {"困难", "噩梦"}:
            return 0.40
        return 0.0

    def prepare_clue_round(self):
        self.clue_entry = self.clue_library.get(self.current)
        complete = list(self.clue_entry.get("complete") or [])
        fragments = list(self.clue_entry.get("fragments") or [])
        self.clue_lines = []
        self.clue_line_types = []
        probability = self.clue_fragment_probability()
        for index in range(5):
            use_fragment = probability > 0 and random.random() < probability
            if use_fragment and index < len(fragments):
                self.clue_lines.append(fragments[index])
                self.clue_line_types.append("fragment")
            else:
                self.clue_lines.append(complete[index] if index < len(complete) else "")
                self.clue_line_types.append("complete")
        if self.rank_mode and self.rank_kind == "clue":
            needed = max(0, int((self.rank_target_difficulty - self.current.difficulty) * 2 + 0.999))
            needed = min(needed, len(fragments), len(self.clue_lines))
            current_fragments = sum(1 for line_type in self.clue_line_types if line_type == "fragment")
            if current_fragments < needed:
                candidates = [index for index in range(min(len(fragments), len(self.clue_lines))) if self.clue_line_types[index] != "fragment"]
                for index in random.sample(candidates, min(needed - current_fragments, len(candidates))):
                    self.clue_lines[index] = fragments[index]
                    self.clue_line_types[index] = "fragment"
        self.clue_fragment_count = sum(1 for line_type in self.clue_line_types if line_type == "fragment")
        if self.custom_mode:
            try:
                visible = int(self.custom_config.get("clue_initial_lines") or 2)
            except (TypeError, ValueError):
                visible = 2
            self.clue_visible_count = max(1, min(len(self.clue_lines), visible))
        else:
            self.clue_visible_count = min(len(self.clue_lines), 2)

    def automatic_mask_difficulty(self):
        if not self.current and self.custom_mode:
            return "普通"
        if self.current and self.current.difficulty >= 10:
            return "噩梦"
        if self.current and self.current.difficulty >= 8:
            return "困难"
        if self.current and self.current.difficulty >= 5:
            return "普通"
        return "入门"

    def custom_mask_positions_for_initials(self, initials):
        setting = self.custom_config.get("mask", "自动")
        mode = self.custom_config.get("mask_mode", setting)
        if mode == "自动":
            if self.crossword_mode:
                return self.crossword_random_mask_positions(initials, self.automatic_mask_difficulty())
            return random_mask_positions(initials, self.automatic_mask_difficulty())
        if mode in {"无", "0"}:
            return []
        if mode == "概率":
            try:
                probability = float(self.custom_config.get("mask_probability", 0)) / 100
            except (TypeError, ValueError):
                probability = 0
            try:
                max_count = int(self.custom_config.get("mask_max", 3))
            except (TypeError, ValueError):
                max_count = 3
            positions = [index for index in range(len(initials)) if random.random() < probability]
            positions = positions[: max(0, min(max_count, len(initials)))]
            return sorted(positions)
        if mode == "固定":
            setting = self.custom_config.get("mask_fixed", setting)
        try:
            count = int(setting)
        except (TypeError, ValueError):
            count = 0
        count = max(0, min(6, count, len(initials)))
        if count <= 0:
            return []
        return sorted(random.sample(range(len(initials)), count))

    def custom_mask_positions(self):
        return self.custom_mask_positions_for_initials(self.current.initials)

    def custom_free_hint_quota(self):
        setting = self.custom_config.get("free_hint", "自动")
        if setting == "自动":
            return random_free_hint_quota(len(self.current.chinese), self.automatic_mask_difficulty())
        try:
            value = int(setting)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(value, max(0, len(self.current.chinese) - 1)))

    def max_extra_mask_count(self, term, difficulty):
        if difficulty not in {"普通", "困难", "噩梦"}:
            return 0
        limit = 4 if difficulty == "噩梦" else 3
        return min(limit, len(term.initials))

    def max_rank_extra_count(self, term, difficulty):
        if self.rank_kind == "clue":
            return 5 if difficulty in {"普通", "困难", "噩梦"} else 0
        return self.max_extra_mask_count(term, difficulty)

    def choose_rank_term(self):
        requirement = self.rank_requirements[self.rank_question_index]
        difficulty, target = requirement
        terms, files = self.library.load(self.rank_subject, difficulty)
        relaxed_target = float(target)
        candidates = []
        while relaxed_target >= 1:
            candidates = [term for term in terms if term.difficulty >= relaxed_target]
            if candidates:
                break
            relaxed_target -= 0.5
        if not candidates:
            candidates = terms
        self.terms = candidates
        self.library_files = files
        self.scope_text = f"{subject_label(self.rank_subject)}{rank_kind_label(self.rank_kind)}：{self.library.scope_text(files)}"
        self.difficulty = difficulty
        self.rank_target_difficulty = float(target)
        self.rank_relaxed = relaxed_target < float(target)
        return choose_daily_term_by_difficulty(candidates, difficulty, self.daily_term_bucket_key())

    def rank_mask_positions(self):
        return random_mask_positions(self.current.initials, self.difficulty)

    def start_round(self, transition=True):
        if self.is_timed_mode() and self.timed_deadline and time.perf_counter() >= self.timed_deadline:
            if self.rank_mode:
                self.fail_rank_challenge("时间到")
            elif self.is_custom_challenge_mode():
                self.fail_custom_challenge("限时结束")
            else:
                self.show_timed_result()
            return
        if self.rank_mode:
            self.current = self.choose_rank_term()
        elif self.custom_mode:
            self.current = choose_term_by_length(self.terms)
        elif self.tutorial_active:
            tutorial_terms = [term for term in self.terms if len(term.chinese) >= 2]
            self.current = choose_term_by_length(tutorial_terms or self.terms)
        else:
            self.current = choose_daily_term_by_difficulty(self.terms, self.difficulty, self.daily_term_bucket_key())
        if self.current and len(self.current.chinese) == 1 and not self.custom_mode:
            self.complete_achievement("one_char_term")
        if self.current:
            self.mark_greek_term_encounter([self.current.chinese])
        if self.is_clue_mode():
            self.mask_positions = []
        elif self.rank_mode:
            self.mask_positions = self.rank_mask_positions()
        elif self.custom_mode:
            self.mask_positions = self.custom_mask_positions()
        else:
            self.mask_positions = random_mask_positions(self.current.initials, self.difficulty)
        self.mask_count = len(self.mask_positions)
        self.display_initials = "线索题" if self.is_clue_mode() else apply_initial_mask(self.current.initials, self.mask_positions)
        self.clue_entry = {}
        self.clue_lines = []
        self.clue_line_types = []
        self.clue_visible_count = 0
        self.clue_fragment_count = 0
        if self.is_clue_mode():
            self.prepare_clue_round()
        self.effective_difficulty = self.current.difficulty + 0.5 * self.mask_count + 0.5 * self.clue_fragment_count
        self.accepted_answers = [self.current.chinese] if self.is_clue_mode() else sorted(
            {term.chinese for term in self.terms if self.initials_match_question(term.initials)}
        )
        self.accepted_answer_keys = self.build_answer_key_set(self.accepted_answers)
        self.round_initial_lookup = self.build_round_initial_lookup(self.terms)
        self.revealed_positions = set()
        self.hint_lines = []
        self.hint_penalties = []
        if self.is_clue_mode():
            self.free_hint_quota = 0
        elif self.custom_mode:
            self.free_hint_quota = self.custom_free_hint_quota()
        else:
            self.free_hint_quota = random_free_hint_quota(len(self.current.chinese), self.difficulty)
        if self.tutorial_active and not self.is_clue_mode():
            self.free_hint_quota = max(1, self.free_hint_quota)
        self.free_hint_count = 0
        self.paid_hint_count = 0
        self.attempts = []
        self.score_penalty = 0
        self.library_hint_used = False
        self.library_hint_text = ""
        self.hint_button = None
        self.hint_text_widget = None
        self.hint_scrollbar = None
        self.clue_box = None
        self.hint_cooldown_until = 0.0
        self.initial_input_warnings = 0
        self.initial_warning_until = 0.0
        self.blocked_initial_input = ""
        self.raw_initial_buffer = ""
        self.raw_initial_last_at = 0.0
        self.suppress_answer_trace = False
        self.cheat_pending = False
        self.cheat_info = {}
        self.start_time = time.perf_counter()
        self.timed_round_start = self.start_time
        self.game_active = True
        self.record_saved = False
        self.show_game(transition=transition)

    def show_game(self, transition=True):
        self.play_music(self.round_music_track())
        self.clear(transition=transition)
        self.timed_status_label = None
        if self.rank_mode:
            rank = rank_by_id(self.rank_id)
            title = f"{subject_label(self.rank_subject)}{rank_kind_label(self.rank_kind)} / {rank['name']} / {self.rank_question_index + 1}"
        elif self.custom_mode:
            title_parts = [self.custom_config.get("play_kind", "首字母")]
            if self.is_custom_timed_enabled():
                title_parts.append(f"{int(self.custom_config.get('minutes', 5))}分钟")
            if self.is_custom_challenge_mode():
                title_parts.append(f"{self.custom_challenge_target()}题挑战")
            title = "自定义 / " + " / ".join(title_parts)
        elif self.play_mode == "限时":
            title = f"{self.mode} / 限时 / {self.difficulty}"
        elif self.play_mode == "线索":
            title = f"{self.mode} / 线索 / {self.difficulty}"
        elif self.is_random_group_mode():
            random_label = "真·随机" if self.is_true_random_mode() else "随机"
            title = f"{random_label} / {self.play_mode} / {self.difficulty}"
        else:
            title = f"{self.mode} / {self.difficulty}"
        if self.rank_mode:
            back_command = lambda: self.abandon_game(self.show_rank_select)
        elif self.custom_mode:
            back_command = lambda: self.abandon_game(self.show_custom_config)
        else:
            back_command = lambda: self.abandon_game(self.show_difficulty_for_current_mode)
        self._topbar(title, back_command)
        self.render_tutorial_banner(self.container, answer=self.current.chinese if self.current else None)
        base_bg = self.theme_color("base")
        root = tk.Frame(self.container, bg=base_bg)
        root.pack(fill="both", expand=True, padx=36, pady=24)
        self._start_backdrop("wind", root)

        available_width = max(self.winfo_width(), int(self.player_settings.get("window_width", 1274))) - 72
        side_width = min(460, max(330, int(available_width * 0.34)))
        gap_width = 28
        if self.is_clue_mode():
            panel_width = min(840, max(600, available_width - side_width - gap_width))
        else:
            panel_width = min(740, max(540, available_width - side_width - gap_width))
        side_width = max(320, available_width - panel_width - gap_width)
        side_text_width = max(290, min(560, side_width - 26))
        panel = tk.Frame(root, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(side="left", fill="both", expand=False, padx=(0, gap_width))
        panel.configure(width=panel_width)
        panel.pack_propagate(False)
        self.decorate_surface(panel, "wind", opacity_scale=0.34)
        self.tutorial_question_panel = panel
        notice_text = self.current_term_notice_text()

        if self.is_clue_mode():
            tk.Label(panel, text="本题线索", fg="#7ed6ff", bg="#182033", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", padx=48, pady=(34, 10))
            tk.Label(
                panel,
                text=f"答案字数：{len(self.current.chinese)} 字",
                fg="#fff2bd",
                bg="#182033",
                font=("Microsoft YaHei UI", 18, "bold"),
            ).pack(anchor="w", padx=48, pady=(0, 8))
            tk.Label(
                panel,
                text=f"基础难度 {self.current.difficulty} / 12    本题总难度 {self.effective_difficulty:g}",
                fg="#f6d36b",
                bg="#182033",
                font=("Microsoft YaHei UI", 14, "bold"),
            ).pack(anchor="w", padx=48, pady=(0, 8))
            if self.clue_fragment_count:
                tk.Label(
                    panel,
                    text=f"本题含 {self.clue_fragment_count} 条破碎线索",
                    fg="#f6a6ff",
                    bg="#182033",
                    font=("Microsoft YaHei UI", 12, "bold"),
                ).pack(anchor="w", padx=48, pady=(0, 8))
            if notice_text:
                tk.Label(
                    panel,
                    text=notice_text,
                    fg="#f6a6ff",
                    bg="#182033",
                    font=("Microsoft YaHei UI", 12, "bold"),
                ).pack(anchor="w", padx=48, pady=(0, 8))
            self.clue_box = tk.Frame(panel, bg="#182033")
            self.clue_box.pack(fill="x", padx=48, pady=(4, 16))
            self._render_clues()
        else:
            tk.Label(panel, text="本题首字母", fg="#7ed6ff", bg="#182033", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", padx=48, pady=(40, 10))
            tk.Label(panel, text=self.display_initials, fg="#fff2bd", bg="#182033", font=("Consolas", 58, "bold")).pack(pady=(0, 22))
            if self.mask_count:
                tk.Label(
                    panel,
                    text=f"已掩码 {self.mask_count} 个首字母字符",
                    fg="#f6a6ff",
                    bg="#182033",
                    font=("Microsoft YaHei UI", 12, "bold"),
                ).pack(anchor="w", padx=48, pady=(0, 10))
            tk.Label(
                panel,
                text=f"基础难度 {self.current.difficulty} / 12    本题总难度 {self.effective_difficulty:g}",
                fg="#f6d36b",
                bg="#182033",
                font=("Microsoft YaHei UI", 14, "bold"),
            ).pack(anchor="w", padx=48, pady=(0, 18))
            if notice_text:
                tk.Label(
                    panel,
                    text=notice_text,
                    fg="#f6a6ff",
                    bg="#182033",
                    font=("Microsoft YaHei UI", 12, "bold"),
                ).pack(anchor="w", padx=48, pady=(0, 12))
            tk.Label(
                panel,
                text=self.hint_cooldown_note(),
                fg="#9ff2b2",
                bg="#182033",
                font=("Microsoft YaHei UI", 12, "bold"),
            ).pack(anchor="w", padx=48, pady=(0, 16))

        self.answer_var = tk.StringVar()
        self.answer_var.trace_add("write", self.on_answer_change)
        self.answer_entry_frame = tk.Frame(panel, bg="#182033")
        self.answer_entry_frame.pack(fill="x", padx=54)
        self.build_answer_entry()
        self.schedule_anti_cheat_poll()

        if not self.is_clue_mode():
            window_height = max(self.winfo_height(), int(self.player_settings.get("window_height", 806)))
            self.hint_box_rows = 4 if window_height >= 760 else 3
            self.hint_box = tk.Frame(
                panel,
                bg=self.themed_legacy_color("#101827", "bg"),
                highlightbackground=self.themed_legacy_color("#30384e", "highlightbackground"),
                highlightthickness=1,
            )
            self.hint_box.pack(fill="x", padx=54, pady=(14, 0))
            self._render_hints()

        self.feedback = tk.Label(
            panel,
            text="请输入汉语专有名词",
            fg="#9ca8c7",
            bg="#182033",
            justify="left",
            anchor="w",
            wraplength=620,
            font=("Microsoft YaHei UI", 14),
        )
        self.feedback.pack(fill="x", padx=54, pady=(12, 10))

        buttons = tk.Frame(panel, bg="#182033")
        buttons.pack(pady=6)
        button_width = 150 if self.can_reveal_answer() else 170
        confirm_button = HoverButton(buttons, "确认", self.check_answer, width=button_width, height=58, accent="#9ff2b2")
        confirm_button.grid(row=0, column=0, padx=10)
        self.tutorial_confirm_button = confirm_button
        self.hint_button = HoverButton(buttons, "提示", self.show_hint, width=button_width, height=58, accent="#f6d36b")
        self.hint_button.grid(row=0, column=1, padx=10)
        self.tutorial_hint_button = self.hint_button
        if self.can_reveal_answer():
            HoverButton(buttons, "揭晓答案", self.reveal_answer, width=button_width, height=58, accent="#ff9b89").grid(row=0, column=2, padx=10)

        if self.is_clue_mode():
            if self.clue_visible_count >= len(self.clue_lines):
                self.hint_button.disable("无")
        if self.rank_mode:
            self.start_hint_cooldown(initial=True)
        else:
            self.update_hint_cooldown_button()

        side_x = panel_width + gap_width + 10
        side_y = 8

        def add_side_widget(widget, after=0, width=None):
            nonlocal side_y
            place_kwargs = {"x": side_x, "y": side_y, "anchor": "nw"}
            if width is not None:
                place_kwargs["width"] = width
            widget.place(**place_kwargs)
            widget.update_idletasks()
            side_y += widget.winfo_reqheight() + after
            return widget

        def add_side_label(text, fg, font, after=0, wrap=False):
            label = tk.Label(
                root,
                text=text,
                fg=fg,
                bg=base_bg,
                justify="left",
                anchor="nw",
                wraplength=side_text_width if wrap else 0,
                font=font,
            )
            return add_side_widget(label, after=after, width=side_text_width if wrap else None)

        def add_side_button(button, after=0):
            nonlocal side_y
            button.place(x=side_x, y=side_y, anchor="nw")
            button.update_idletasks()
            side_y += button.winfo_reqheight() + after
            return button

        add_side_label("剩余" if self.is_timed_mode() else "计时", self.theme_color("accent"), ("Microsoft YaHei UI", 15, "bold"), after=4)
        self.timer_label = add_side_label("0.0 秒", self.theme_color("title"), ("Consolas", 28, "bold"), after=14)
        if self.is_timed_mode() or self.is_custom_challenge_mode():
            if self.rank_mode:
                label = f"{rank_kind_label(self.rank_kind)}题"
                status_text = (
                    f"{label} {self.rank_question_index + 1}/{len(self.rank_requirements)}\n"
                    f"已答对 {self.timed_correct} 题\n"
                    f"总分 {self.rank_session_score}｜提示 {self.rank_hint_used}/{rank_hint_limit(self.rank_id)}"
                )
            elif self.custom_mode:
                status_text = self.custom_status_text()
            else:
                status_text = f"已答对 {self.timed_correct} 题\n计入 {format_score(self.timed_score)} 分"
            self.timed_status_label = add_side_label(status_text, self.theme_color("text"), ("Microsoft YaHei UI", 11, "bold"), after=18, wrap=True)
        add_side_label("积分", self.theme_color("accent"), ("Microsoft YaHei UI", 15, "bold"), after=4)
        self.score_label = add_side_label("1000 分", self.theme_color("success"), ("Consolas", 24, "bold"), after=20)
        add_side_label("词库", self.theme_color("accent"), ("Microsoft YaHei UI", 15, "bold"), after=4)
        add_side_label(f"{len(self.terms)} 个词条\n{len(self.library_files)} 个文件", self.theme_color("text"), ("Microsoft YaHei UI", 12), after=24, wrap=True)
        add_side_label("规则", self.theme_color("accent"), ("Microsoft YaHei UI", 15, "bold"), after=4)
        if self.rank_mode:
            if self.rank_kind == "clue":
                rule_text = "线索段位必须在限时内全题答对。\n普通错误提交不会立刻失败，可以继续作答。\n提示会追加线索；主动揭晓、时间到或中途退出都会导致挑战失败。\n线索段位题不计总积分和 Rating。"
            elif self.rank_kind == "timed":
                rule_text = "旧限时段位记录仅用于历史兼容。\n普通错误提交不会立刻失败，可以继续作答。\n时间到、揭晓、提示揭完或中途退出都会导致挑战失败。\n旧限时段位题不计总积分和 Rating。"
            else:
                rule_text = "限时段位必须在限时内全题答对。\n普通错误提交不会立刻失败，可以继续作答。\n时间到、揭晓、提示揭完或中途退出都会导致挑战失败。\n限时段位题不计总积分和 Rating。"
        elif self.custom_mode:
            if self.is_custom_challenge_mode():
                rule_text = (
                    f"自定义挑战需连续完成 {self.custom_challenge_target()} 题。\n"
                    "普通错误提交不会立刻失败，可以继续作答。\n"
                    "揭晓、提示揭完、中途退出或限时结束都会导致挑战失败。\n"
                    "记录会保存，但不计总积分、Rating、成就和正式段位。"
                )
            elif self.is_custom_timed_enabled():
                rule_text = "自定义限时连续练习。\n答对后自动换题，时间结束后看答对题数。\n记录会保存，但不计总积分、Rating 和成就。"
            else:
                rule_text = "自定义模式是练习沙盒。\n记录会保存，但不计总积分、Rating 和成就。\n你可以在配置页调节词库、词长、提示和掩码。"
        elif self.is_clue_mode():
            rule_text = "本题不显示首字母，但会显示答案字数。\n初始显示前两句线索。\n继续提示会从第三条线索开始扣分。\n共五条线索，普通/困难/噩梦可能出现破碎线索。\n揭晓答案会记为未答出。"
        else:
            rule_text = "同首字母的词库内答案都算对。\n普通/困难/噩梦可能用 * 掩码首字母；* 处不限，只检查未掩码位置。\n当前模式总词库里、但不在本轮范围内的匹配词，才会提示超纲。\n提示揭开全部汉字或主动揭晓答案时，本题失败。"
        add_side_label(rule_text, self.theme_color("muted"), ("Microsoft YaHei UI", 11), after=18, wrap=True)
        add_side_label("范围", self.theme_color("accent"), ("Microsoft YaHei UI", 15, "bold"), after=4)
        side_y = self.render_side_scope_text_placed(root, self.scope_text, side_x, side_y, side_text_width, base_bg) + 8
        self.library_hint_button = add_side_button(HoverButton(root, "提示词库", self.show_library_hint, width=170, height=54, accent="#ffbd7e"), after=8)
        self.tutorial_library_hint_button = self.library_hint_button
        self.library_hint_label = tk.Label(
            root,
            text="",
            justify="left",
            fg=self.theme_color("warning"),
            bg=base_bg,
            wraplength=side_text_width,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        add_side_widget(self.library_hint_label, width=side_text_width)
        self.library_hint_label.bind(
            "<Configure>",
            lambda event, widget=self.library_hint_label: widget.configure(wraplength=max(220, event.width - 8)),
            add="+",
        )
        self.reveal_background_surface(panel)
        self._tick()
        self.render_tutorial_game_overlay()

    def render_side_text_block(self, parent, text, fg="#c8d2ee", bg="#111725", base_size=11, pady=(4, 18), max_lines=None):
        widget = tk.Text(
            parent,
            height=1,
            width=1,
            wrap="word",
            fg=fg,
            bg=bg,
            relief="flat",
            bd=0,
            highlightthickness=0,
            insertbackground=fg,
            padx=0,
            pady=0,
            cursor="arrow",
            font=("Microsoft YaHei UI", base_size),
            spacing1=2,
            spacing2=2,
            spacing3=5,
        )
        widget.insert("1.0", str(text or ""))
        widget.configure(state="disabled")
        widget.pack(anchor="w", fill="x", pady=pady)
        self.bind_side_text_height(widget, max_lines=max_lines)
        return widget

    def bind_side_text_height(self, widget, max_lines=None):
        def cancel_pending():
            pending = getattr(widget, "_side_text_height_after", None)
            if pending:
                try:
                    widget.after_cancel(pending)
                except tk.TclError:
                    pass
                widget._side_text_height_after = None

        def schedule(delay=None):
            try:
                if not widget.winfo_exists():
                    return
            except tk.TclError:
                return
            cancel_pending()
            try:
                if delay is None:
                    widget._side_text_height_after = widget.after_idle(update_height)
                else:
                    widget._side_text_height_after = widget.after(delay, update_height)
            except tk.TclError:
                pass

        def update_height():
            widget._side_text_height_after = None
            if not widget.winfo_exists():
                return
            if widget.winfo_width() <= 20:
                schedule(30)
                return
            try:
                count = widget.count("1.0", "end-1c", "displaylines")
            except tk.TclError:
                return
            if not count:
                return
            desired = max(1, int(count[0]))
            if max_lines is not None:
                desired = min(max_lines, desired)
            if str(widget.cget("height")) != str(desired):
                widget.configure(height=desired)

        def on_destroy(event):
            if event.widget is widget:
                cancel_pending()

        widget.bind("<Configure>", lambda _event: schedule(), add="+")
        widget.bind("<Destroy>", on_destroy, add="+")
        schedule()

    def render_side_scope_text(self, parent, text, side_text_width):
        text = str(text or "")
        wrap_chars = max(16, min(46, int(side_text_width / 13)))
        estimated_lines = 0
        for line in text.splitlines() or [""]:
            estimated_lines += max(1, math.ceil(len(line) / wrap_chars))
        if estimated_lines <= 4:
            return self.render_side_text_block(parent, text, fg="#c8d2ee", bg="#111725", base_size=11, pady=(4, 18))

        visible_lines = 7
        box = tk.Frame(parent, bg=self.themed_legacy_color("#101827", "bg"), highlightbackground=self.themed_legacy_color("#30384e", "highlightbackground"), highlightthickness=1)
        box.pack(fill="x", pady=(4, 18))
        text_widget = tk.Text(
            box,
            height=visible_lines,
            width=1,
            wrap="word",
            fg=self.themed_legacy_color("#c8d2ee", "fg"),
            bg=self.themed_legacy_color("#101827", "bg"),
            bd=0,
            relief="flat",
            insertbackground=self.themed_legacy_color("#fff8dc", "insertbackground"),
            font=("Microsoft YaHei UI", 10),
        )
        scrollbar = tk.Scrollbar(box, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")
        text_widget.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(4, 6), pady=8)
        self.bind_scroll_wheel(box, text_widget, units=2)
        return text_widget

    def render_side_scope_text_placed(self, parent, text, x, y, side_text_width, base_bg):
        text = str(text or "")
        wrap_chars = max(16, min(46, int(side_text_width / 13)))
        estimated_lines = 0
        for line in text.splitlines() or [""]:
            estimated_lines += max(1, math.ceil(len(line) / wrap_chars))
        if estimated_lines <= 4:
            label = tk.Label(
                parent,
                text=text,
                fg=self.theme_color("text"),
                bg=base_bg,
                justify="left",
                anchor="nw",
                wraplength=side_text_width,
                font=("Microsoft YaHei UI", 11),
            )
            label.place(x=x, y=y, width=side_text_width, anchor="nw")
            label.update_idletasks()
            return y + label.winfo_reqheight() + 18

        visible_lines = 7
        box_height = 150
        box = tk.Frame(parent, bg=self.theme_color("entry_bg"), highlightbackground=self.theme_color("grid_a"), highlightthickness=1)
        box.place(x=x, y=y, width=side_text_width, height=box_height, anchor="nw")
        text_widget = tk.Text(
            box,
            height=visible_lines,
            width=1,
            wrap="word",
            fg=self.theme_color("text"),
            bg=self.theme_color("entry_bg"),
            bd=0,
            relief="flat",
            insertbackground=self.theme_color("title"),
            font=("Microsoft YaHei UI", 10),
        )
        scrollbar = tk.Scrollbar(box, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")
        text_widget.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(4, 6), pady=8)
        self.bind_scroll_wheel(box, text_widget, units=2)
        return y + box_height + 18

    def show_difficulty_for_current_mode(self):
        if self.rank_mode:
            self.show_rank_select()
            return
        if self.custom_mode:
            self.show_custom_config()
            return
        if self.mode:
            self.show_difficulty()
        else:
            self.show_mode_select()

    @staticmethod
    def normalize_initial_input(value):
        text = unicodedata.normalize("NFKC", value or "").upper()
        return "".join(char for char in text if "A" <= char <= "Z")

    def blocked_initial_sequence(self):
        if self.is_clue_mode():
            return ""
        return self.normalize_initial_input(self.current.initials if self.current else "")

    def blocked_initials_are_unavoidable_pinyin_input(self, normalized_answer):
        if not self.current:
            return False
        chinese = str(getattr(self.current, "chinese", "") or "")
        if len(chinese) <= 1:
            return True
        pinyin = self.normalize_initial_input(getattr(self.current, "pinyin", ""))
        return bool(pinyin and (normalized_answer in pinyin or pinyin in normalized_answer))

    def contains_blocked_initials(self, normalized_answer):
        blocked = self.blocked_initial_sequence()
        if not (blocked and blocked in normalized_answer):
            return False
        return not self.blocked_initials_are_unavoidable_pinyin_input(normalized_answer)

    def initials_match_question(self, initials):
        if self.is_clue_mode():
            return initials == (self.current.initials if self.current else "")
        normalized = self.normalize_initial_input(initials)
        pattern = self.display_initials or (self.current.initials if self.current else "")
        if not pattern or "*" not in pattern:
            return normalized == self.normalize_initial_input(self.current.initials if self.current else "")
        pattern = unicodedata.normalize("NFKC", pattern or "").upper()
        if len(normalized) != len(pattern):
            return False
        return all(mask == "*" or normalized[index] == mask for index, mask in enumerate(pattern))

    def is_accepted_answer(self, answer):
        keys = self.answer_equivalence_keys(answer)
        if keys and getattr(self, "accepted_answer_keys", None):
            return any(key in self.accepted_answer_keys for key in keys)
        return any(answers_equivalent(answer, accepted) for accepted in self.accepted_answers)

    @staticmethod
    def answer_equivalence_keys(answer):
        keys = []
        for key in (canonical_answer_text(answer), person_name_answer_key(answer)):
            if key and key not in keys:
                keys.append(key)
        return keys

    @classmethod
    def build_answer_key_set(cls, answers):
        keys = set()
        for answer in answers or []:
            keys.update(cls.answer_equivalence_keys(answer))
        return keys

    @classmethod
    def build_round_initial_lookup(cls, terms):
        lookup = {}
        for term in terms or []:
            initials = getattr(term, "initials", "")
            if not initials:
                continue
            for key in cls.answer_equivalence_keys(getattr(term, "chinese", "")):
                lookup.setdefault(key, initials)
        return lookup

    def current_term_notice_text(self):
        return term_notice_text(self.current.chinese) if self.current else ""

    def term_entry_for_answer(self, answer, terms=None):
        text = str(answer or "").strip()
        if not text:
            return {}
        search_terms = list(terms if terms is not None else self.terms)
        for term in search_terms:
            if answers_equivalent(getattr(term, "chinese", ""), text):
                return self.clue_library.get(term)
        entry = getattr(self.clue_library, "by_chinese", {}).get(text)
        return entry or {}

    def term_explanation_for_answer(self, answer, terms=None):
        entry = self.term_entry_for_answer(answer, terms=terms)
        return str(entry.get("explanation_markdown") or "").strip()

    def term_explanation_sources_for_answer(self, answer, terms=None):
        entry = self.term_entry_for_answer(answer, terms=terms)
        sources = entry.get("source_links") or entry.get("explanation_sources") or []
        return sources if isinstance(sources, list) else []

    def show_term_explanation_dialog(self, answer, explanation=None, sources=None):
        title = str(answer or "").strip()
        if not title:
            return
        content = str(explanation or self.term_explanation_for_answer(title) or "").strip()
        if not content:
            content = "这个词条的解释还没有写好。"
        if sources is None:
            sources = self.term_explanation_sources_for_answer(title)
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.configure(bg="#111725")
        popup.geometry("920x660")
        popup.minsize(720, 500)
        popup.transient(self)
        popup.grab_set()

        panel = tk.Frame(popup, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=20, pady=20)
        header = tk.Frame(panel, bg="#182033")
        header.pack(fill="x", padx=28, pady=(22, 10))
        header.grid_columnconfigure(0, weight=1)
        title_label = tk.Label(
            header,
            text=title,
            fg="#fff2bd",
            bg="#182033",
            justify="left",
            anchor="w",
            wraplength=720,
            font=("Microsoft YaHei UI", 24, "bold"),
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        HoverButton(header, "关闭", popup.destroy, width=96, height=42, accent="#ff9b89").grid(row=0, column=1, sticky="ne")
        header.bind("<Configure>", lambda event: title_label.configure(wraplength=max(360, event.width - 136)))

        body = tk.Frame(panel, bg="#182033")
        body.pack(fill="both", expand=True, padx=0, pady=(0, 14))
        markdown_inner = render_markdown(body, content, mode="detail")
        self.render_explanation_sources(markdown_inner, sources)
        self.apply_static_theme(popup)
        popup.bind("<Escape>", lambda _event: popup.destroy())

    def render_explanation_sources(self, parent, sources):
        normalized = []
        for source in sources or []:
            if not isinstance(source, dict):
                continue
            label = str(source.get("label") or "").strip()
            title = str(source.get("title") or "").strip()
            url = str(source.get("url") or "").strip()
            if label and (url.startswith("https://") or url.startswith("http://")):
                normalized.append({"label": label, "title": title, "url": url})
        if not normalized:
            return
        bg = self.themed_legacy_color(parent.cget("bg"), "bg")
        tk.Label(
            parent,
            text="参考资料",
            fg=self.theme_color("title"),
            bg=bg,
            font=("Microsoft YaHei UI", 15, "bold"),
        ).pack(anchor="w", padx=28, pady=(18, 7))
        for source in normalized:
            text = f"{source['label']}：{source['title'] or source['url']}"
            link = tk.Label(
                parent,
                text=text,
                fg=self.theme_color("link_fg", self.theme_color("accent")),
                bg=bg,
                wraplength=1080,
                justify="left",
                anchor="w",
                cursor="hand2",
                font=("Microsoft YaHei UI", 12, "bold"),
            )
            link.pack(anchor="w", fill="x", padx=28, pady=3)

            def open_url(_event, url=source["url"]):
                webbrowser.open_new_tab(url)
                return "break"

            def on_enter(_event, widget=link):
                widget.configure(fg=self.theme_color("title"))

            def on_leave(_event, widget=link):
                widget.configure(fg=self.theme_color("link_fg", self.theme_color("accent")))

            link.bind("<Button-1>", open_url)
            link.bind("<Enter>", on_enter)
            link.bind("<Leave>", on_leave)
            link.bind("<Configure>", lambda event, widget=link: widget.configure(wraplength=max(260, event.width - 8)))

    def render_clickable_answers(self, parent, answers, height=3, base_size=11, numbered=False, wrap="char"):
        entries = []
        for index, answer in enumerate(answers, 1):
            prefix = f"{index:02d} " if numbered else ""
            entries.append({"prefix": prefix, "answers": [answer]})
        return self.render_clickable_answer_entries(parent, entries, height=height, base_size=base_size, wrap=wrap)

    def render_clickable_answer_entries(self, parent, entries, height=3, base_size=11, wrap="char"):
        normalized_entries = []
        for entry in entries:
            answers = [str(answer or "").strip() for answer in entry.get("answers", []) if str(answer or "").strip()]
            if answers:
                normalized_entries.append({"prefix": str(entry.get("prefix") or ""), "answers": answers})
        answer_box = tk.Text(
            parent,
            height=height,
            wrap=wrap,
            fg=self.themed_legacy_color("#dce6ff", "fg"),
            bg=self.themed_legacy_color("#111827", "bg"),
            insertbackground=self.themed_legacy_color("#dce6ff", "insertbackground"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.themed_legacy_color("#30384e", "highlightbackground"),
            font=("Microsoft YaHei UI", base_size),
            padx=8,
            pady=7,
            cursor="arrow",
        )
        answer_box.tag_configure("link", foreground=self.themed_legacy_color("#9fb7ff", "fg"), underline=False)
        answer_box.tag_configure("link_hover", foreground=self.themed_legacy_color("#fff2bd", "fg"), underline=True, background=self.themed_legacy_color("#26344f", "bg"))
        answer_box.tag_configure("muted", foreground=self.themed_legacy_color("#7683a3", "fg"))

        link_index = 0
        for entry_index, entry in enumerate(normalized_entries):
            if entry_index:
                answer_box.insert("end-1c", "\n" if entry.get("prefix") else "、")
            if entry.get("prefix"):
                answer_box.insert("end-1c", entry["prefix"], ("muted",))
            for answer_index, answer in enumerate(entry["answers"]):
                if answer_index:
                    answer_box.insert("end-1c", "、", ("muted",))
                link_index += 1
                start = answer_box.index("end-1c")
                answer_box.insert("end-1c", answer, ("link",))
                end = answer_box.index("end-1c")
                tag = f"term_{link_index}"
                answer_box.tag_add(tag, start, end)
                explanation = self.term_explanation_for_answer(answer)
                self.bind_term_link(answer_box, tag, answer, explanation)

        answer_box.config(state="disabled")
        return answer_box

    def bind_term_link(self, text_widget, tag, answer, explanation):
        targets = getattr(text_widget, "_term_link_targets", {})
        targets[tag] = {"answer": answer, "explanation": explanation}
        text_widget._term_link_targets = targets
        if not getattr(text_widget, "_term_link_widget_bound", False):
            text_widget._term_link_widget_bound = True
            text_widget.bind(
                "<Motion>",
                lambda event, widget=text_widget: self.update_term_link_hover(widget, event),
                add="+",
            )
            text_widget.bind(
                "<Leave>",
                lambda _event, widget=text_widget: self.clear_term_link_hover(widget),
                add="+",
            )
            text_widget.bind(
                "<Button-1>",
                lambda event, widget=text_widget: self.open_term_link_at_event(widget, event),
                add="+",
            )

    def term_link_tag_at_event(self, text_widget, event):
        targets = getattr(text_widget, "_term_link_targets", {})
        if not targets:
            return None
        try:
            index = text_widget.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return None
        for tag in text_widget.tag_names(index):
            if tag in targets:
                return tag
        return None

    def set_term_link_hover(self, text_widget, tag):
        current = getattr(text_widget, "_term_link_hover_tag", None)
        if current and current != tag:
            self.clear_term_link_hover(text_widget)
        ranges = text_widget.tag_ranges(tag)
        if ranges:
            text_widget.tag_add("link_hover", ranges[0], ranges[-1])
            text_widget._term_link_hover_tag = tag
            text_widget.configure(cursor="hand2")

    def clear_term_link_hover(self, text_widget):
        current = getattr(text_widget, "_term_link_hover_tag", None)
        if current:
            ranges = text_widget.tag_ranges(current)
            if ranges:
                text_widget.tag_remove("link_hover", ranges[0], ranges[-1])
        text_widget._term_link_hover_tag = None
        text_widget.configure(cursor="arrow")

    def update_term_link_hover(self, text_widget, event):
        tag = self.term_link_tag_at_event(text_widget, event)
        if tag:
            self.set_term_link_hover(text_widget, tag)
        else:
            self.clear_term_link_hover(text_widget)

    def open_term_link_at_event(self, text_widget, event):
        tag = self.term_link_tag_at_event(text_widget, event)
        if not tag:
            return None
        target = getattr(text_widget, "_term_link_targets", {}).get(tag) or {}
        answer = target.get("answer")
        explanation = target.get("explanation")
        self.show_term_explanation_dialog(answer, explanation)
        return "break"

    @staticmethod
    def record_greek_answers(record):
        answers = set()

        def add_answer(value):
            text = str(value or "").strip()
            if text and term_has_greek_letter(text):
                answers.add(text)

        add_answer(record.get("selected_answer"))
        accepted_answers = record.get("accepted_answers")
        if isinstance(accepted_answers, list):
            for answer in accepted_answers:
                add_answer(answer)
        placements = record.get("crossword_placements")
        if isinstance(placements, list):
            for placement in placements:
                if not isinstance(placement, dict):
                    continue
                add_answer(placement.get("answer"))
                add_answer(placement.get("filled_answer"))
                placement_answers = placement.get("accepted_answers")
                if isinstance(placement_answers, list):
                    for answer in placement_answers:
                        add_answer(answer)
        rank_answers = record.get("rank_session_answers")
        if isinstance(rank_answers, list):
            for entry in rank_answers:
                if not isinstance(entry, dict):
                    continue
                add_answer(entry.get("answer"))
                entry_answers = entry.get("accepted_answers")
                if isinstance(entry_answers, list):
                    for answer in entry_answers:
                        add_answer(answer)
        return sorted(answers)

    @staticmethod
    def record_success_greek_answers(record):
        if not record.get("success"):
            return []
        if record.get("crossword_mode"):
            answers = set()
            placements = record.get("crossword_placements")
            if isinstance(placements, list):
                for placement in placements:
                    if not isinstance(placement, dict) or not placement.get("solved"):
                        continue
                    answer = str(placement.get("filled_answer") or placement.get("answer") or "").strip()
                    if term_has_greek_letter(answer):
                        answers.add(answer)
            return sorted(answers)
        return RoundPlayMixin.record_greek_answers(record)

    def mark_greek_term_encounter(self, answers, crossword=False):
        if self.custom_mode or self.tutorial_active or self.is_spectating():
            return
        if not any(term_has_greek_letter(answer) for answer in answers):
            return
        self.complete_achievement("first_greek_term")
        if crossword:
            self.complete_achievement("crossword_greek_term")

    def build_answer_entry(self):
        if not self.answer_entry_frame or not self.answer_entry_frame.winfo_exists():
            return
        for child in self.answer_entry_frame.winfo_children():
            child.destroy()
        validate_answer = (self.register(self.validate_answer_change), "%P")
        entry = tk.Entry(
            self.answer_entry_frame,
            textvariable=self.answer_var,
            justify="left",
            fg=self.themed_legacy_color("#fff8dc", "fg"),
            bg=self.themed_legacy_color("#101827", "bg"),
            insertbackground=self.themed_legacy_color("#fff8dc", "insertbackground"),
            relief="flat",
            validate="key",
            validatecommand=validate_answer,
            font=("Microsoft YaHei UI", 23, "bold"),
        )
        entry.pack(fill="x", ipady=12)
        self.answer_entry = entry
        entry.bind("<KeyPress>", self.on_answer_keypress)
        entry.bind("<KeyRelease>", self.on_answer_keyrelease)
        entry.bind("<Return>", lambda _event: self.check_answer())
        entry.focus_set()

    def rebuild_answer_entry(self):
        if self.answer_entry and self.answer_entry.winfo_exists():
            try:
                self.answer_entry.destroy()
            except tk.TclError:
                pass
        self.cancel_input_method_composition()
        self.build_answer_entry()

    def clear_answer_input(self, rebuild=False):
        self.suppress_answer_trace = True
        try:
            self.cancel_input_method_composition()
            self.answer_var.set("")
            if self.answer_entry and self.answer_entry.winfo_exists():
                self.answer_entry.delete(0, tk.END)
            if rebuild:
                self.rebuild_answer_entry()
        finally:
            self.suppress_answer_trace = False

    def cancel_input_method_composition(self):
        if not self.answer_entry or not self.answer_entry.winfo_exists():
            return
        try:
            self.answer_entry.event_generate("<Escape>")
        except tk.TclError:
            pass
        try:
            self.tk.call("tk", "useinputmethods", False)
            self.after(350, lambda: self.tk.call("tk", "useinputmethods", True))
        except tk.TclError:
            pass

    def read_ime_composition_text(self):
        if sys.platform != "win32" or not self.answer_entry or not self.answer_entry.winfo_exists():
            return ""
        try:
            if self.focus_get() is not self.answer_entry:
                return ""
        except tk.TclError:
            return ""
        try:
            import ctypes

            imm32 = ctypes.windll.imm32
            user32 = ctypes.windll.user32
            imm32.ImmGetContext.argtypes = [ctypes.c_void_p]
            imm32.ImmGetContext.restype = ctypes.c_void_p
            imm32.ImmReleaseContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            imm32.ImmReleaseContext.restype = ctypes.c_bool
            imm32.ImmGetCompositionStringW.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
            imm32.ImmGetCompositionStringW.restype = ctypes.c_long
            user32.GetFocus.argtypes = []
            user32.GetFocus.restype = ctypes.c_void_p

            hwnds = []
            for hwnd in (user32.GetFocus(), self.answer_entry.winfo_id(), self.winfo_id()):
                if hwnd and hwnd not in hwnds:
                    hwnds.append(hwnd)
            pieces = []
            for hwnd in hwnds:
                context = imm32.ImmGetContext(ctypes.c_void_p(hwnd))
                if not context:
                    continue
                try:
                    for flag in (0x0008, 0x0001, 0x0800):  # GCS_COMPSTR, GCS_COMPREADSTR, GCS_RESULTSTR
                        size = imm32.ImmGetCompositionStringW(context, flag, None, 0)
                        if size and size > 0:
                            buffer = ctypes.create_unicode_buffer(size // 2 + 1)
                            imm32.ImmGetCompositionStringW(context, flag, buffer, size)
                            if buffer.value and buffer.value not in pieces:
                                pieces.append(buffer.value)
                finally:
                    imm32.ImmReleaseContext(ctypes.c_void_p(hwnd), context)
            return " ".join(pieces)
        except Exception:
            return ""

    def handle_blocked_initial_input(self, blocked_text, clear_now=True):
        if self.initial_warning_active():
            return
        self.initial_input_warnings += 1
        self.blocked_initial_input = blocked_text
        self.raw_initial_buffer = ""
        self.raw_initial_last_at = 0.0
        if clear_now:
            self.clear_answer_input(rebuild=True)
        else:
            self.after_idle(lambda: self.clear_answer_input(rebuild=True))
        if self.initial_input_warnings == 1:
            self.initial_warning_until = time.perf_counter() + 0.8
            if not self.custom_mode:
                self.complete_achievement("first_initial_block")
            if self.feedback:
                self.feedback.config(text="题面首字母已清空。再试一次会触发隐藏彩蛋。", fg=self.themed_legacy_color("#f6d36b", "fg"))
            title = "段位输入警告" if self.rank_mode else "输入已拦截"
            message = "题面首字母不应直接进入输入框。\n已为你清空；再尝试一次会进入隐藏彩蛋。"
            self.after_idle(lambda warning_title=title, warning_message=message: messagebox.showwarning(warning_title, warning_message))
            return
        self.cheat_pending = True
        self.after_idle(lambda blocked=blocked_text: self.cheat_game(blocked))

    def initial_warning_active(self):
        return self.initial_input_warnings == 1 and time.perf_counter() < self.initial_warning_until

    @staticmethod
    def normalize_key_event(event):
        char = getattr(event, "char", "") or ""
        normalized = RoundPlayMixin.normalize_initial_input(char)
        if normalized:
            return normalized
        keysym = str(getattr(event, "keysym", "") or "")
        if len(keysym) == 1:
            normalized = RoundPlayMixin.normalize_initial_input(keysym)
            if normalized:
                return normalized
        keycode = getattr(event, "keycode", None)
        if isinstance(keycode, int) and 65 <= keycode <= 90:
            return chr(keycode)
        return ""

    def on_answer_keypress(self, event):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.cheat_pending or not self.current:
            return None
        normalized_char = self.normalize_key_event(event)
        if not normalized_char:
            self.after(1, self.scan_answer_entry_for_blocked_initials)
            return None
        now = time.perf_counter()
        if now - self.raw_initial_last_at > 2.5:
            self.raw_initial_buffer = ""
        self.raw_initial_last_at = now
        self.raw_initial_buffer = (self.raw_initial_buffer + normalized_char)[-32:]
        if not self.contains_blocked_initials(self.raw_initial_buffer):
            self.after(1, self.scan_answer_entry_for_blocked_initials)
            return None
        blocked_text = self.answer_var.get().strip() or self.raw_initial_buffer
        self.handle_blocked_initial_input(blocked_text, clear_now=False)
        return "break"

    def on_answer_keyrelease(self, _event):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.cheat_pending:
            return None
        self.after(1, self.scan_answer_entry_for_blocked_initials)
        return None

    def schedule_anti_cheat_poll(self):
        if self.anti_cheat_poll_job:
            self.after_cancel(self.anti_cheat_poll_job)
        self.anti_cheat_poll_job = self.after(140, self.poll_anti_cheat_input)

    def poll_anti_cheat_input(self):
        self.anti_cheat_poll_job = None
        if not self.game_active or self.record_saved:
            return
        self.scan_answer_entry_for_blocked_initials()
        if self.game_active and not self.record_saved:
            self.schedule_anti_cheat_poll()

    def scan_answer_entry_for_blocked_initials(self):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.cheat_pending or not self.current:
            return
        values = []
        if self.answer_var:
            values.append(self.answer_var.get())
        if self.answer_entry and self.answer_entry.winfo_exists():
            try:
                values.append(self.answer_entry.get())
            except tk.TclError:
                pass
        ime_text = self.read_ime_composition_text()
        if ime_text:
            values.append(ime_text)
        for value in values:
            normalized = self.normalize_initial_input(value)
            if self.contains_blocked_initials(normalized):
                self.handle_blocked_initial_input(value, clear_now=True)
                return

    def validate_answer_change(self, proposed):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.cheat_pending or not self.current:
            return True
        normalized = self.normalize_initial_input(proposed)
        if not self.contains_blocked_initials(normalized):
            return True
        self.handle_blocked_initial_input(proposed, clear_now=False)
        return False

    def on_answer_change(self, *_args):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.cheat_pending or not self.current:
            return
        answer = self.answer_var.get().strip()
        normalized = self.normalize_initial_input(answer)
        if not self.contains_blocked_initials(normalized):
            return
        self.handle_blocked_initial_input(answer, clear_now=True)

    def check_answer(self):
        answer = self.answer_var.get().strip()
        if not answer:
            self.feedback.config(text="先写一个答案吧。", fg=self.themed_legacy_color("#f6d36b", "fg"))
            return
        if self.tutorial_active:
            if self.free_hint_count + self.paid_hint_count <= 0:
                self.feedback.config(text="教程会先带你试用一次字词提示。点击“提示”后再作答。", fg=self.themed_legacy_color("#f6d36b", "fg"))
                self.advance_tutorial_game_step("hint")
                return
            if not self.library_hint_used:
                self.feedback.config(text="还要试用一次“提示词库”。教程中免费，正式局通常会扣分。", fg=self.themed_legacy_color("#f6d36b", "fg"))
                self.advance_tutorial_game_step("library")
                return

        answer_initials = self._lookup_initials(answer)
        attempt = {
            "answer": answer,
            "answer_initials": answer_initials,
            "time_seconds": round(time.perf_counter() - self.start_time, 3),
        }

        if self.is_accepted_answer(answer):
            attempt["result"] = "success"
            self.attempts.append(attempt)
            self.finish_game(True)
        elif self.is_clue_mode():
            attempt["result"] = "wrong"
            self.attempts.append(attempt)
            if self.tutorial_active:
                self.feedback.config(text=f"教程提示：本题答案是“{self.current.chinese}”，输入后点击确认即可完成。", fg=self.themed_legacy_color("#f6d36b", "fg"))
            else:
                self.feedback.config(text="还不对，顺着线索再想想。", fg=self.themed_legacy_color("#ff9b89", "fg"))
        elif self.initials_match_question(answer_initials):
            attempt["result"] = "out_of_scope"
            self.attempts.append(attempt)
            if self.tutorial_active:
                self.feedback.config(text=f"这个答案首字母匹配，但教程题要填写“{self.current.chinese}”。", fg=self.themed_legacy_color("#f6d36b", "fg"))
            else:
                self.feedback.config(text="超纲啦，再想想~", fg=self.themed_legacy_color("#f6d36b", "fg"))
        else:
            attempt["result"] = "wrong"
            self.attempts.append(attempt)
            if self.tutorial_active:
                self.feedback.config(text=f"教程提示：本题答案是“{self.current.chinese}”，再试一次。", fg=self.themed_legacy_color("#f6d36b", "fg"))
            else:
                self.feedback.config(text="还不对，换个词试试。", fg=self.themed_legacy_color("#ff9b89", "fg"))

    def current_score(self, elapsed=None):
        if elapsed is None:
            elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        return 1000 - int(elapsed) - self.score_penalty

    def round_failure_score(self, elapsed=None, unanswered_count=1):
        current = self.current_score(elapsed)
        return max(current - max(0, int(unanswered_count or 0)) * 1000, 0)

    def current_score_weight(self):
        if self.tutorial_active:
            return 0.0
        if self.custom_mode or self.rank_mode:
            return 0.0
        return score_weight_for_difficulty(self.difficulty)

    def difficulty_penalty_factor(self):
        difficulty = self.effective_difficulty if self.current else 5
        return 1.18 - 0.045 * difficulty

    def library_hint_cost(self):
        return max(90, round(210 * self.difficulty_penalty_factor()))

    @staticmethod
    def library_hint_penalty_cost(tutorial_active, normal_cost):
        return 0 if tutorial_active else normal_cost

    def character_hint_cost(self, hint_number):
        length = max(len(self.current.chinese), 1)
        raw = max(100, round(520 / length)) + 55 * (hint_number - 1)
        return max(65, round(raw * self.difficulty_penalty_factor()))

    def clue_hint_cost(self, hint_number):
        if hint_number <= 1:
            return 0
        mode_base = {
            "入门": 120,
            "简单": 170,
            "普通": 240,
            "困难": 330,
            "噩梦": 440,
            "混合模式": 230,
        }.get(self.difficulty or "", 230)
        difficulty_bonus = max(0, self.effective_difficulty - 1) * 18
        paid_order = hint_number - 1
        return round(mode_base + difficulty_bonus + 70 * max(0, paid_order - 1))

    def hint_cooldown_seconds(self):
        if self.rank_mode:
            return rank_hint_cooldown_seconds(self.rank_id)
        if self.custom_mode:
            setting = self.custom_config.get("hint_cooldown", "自动")
            if setting != "自动":
                try:
                    return max(0, min(180, int(float(setting))))
                except (TypeError, ValueError):
                    pass
        return HINT_COOLDOWN_SECONDS.get(self.difficulty or "", HINT_COOLDOWN_SECONDS["混合模式"])

    def initial_hint_cooldown_seconds(self):
        seconds = int(self.hint_cooldown_seconds())
        if self.rank_mode:
            return max(1, (seconds + 1) // 2)
        return 0

    def hint_cooldown_note(self):
        full = self.hint_cooldown_seconds()
        if self.rank_mode:
            initial = self.initial_hint_cooldown_seconds()
            return f"本局前 {self.free_hint_quota} 次字词提示免费，开局冷却 {initial} 秒；提示后冷却 {full} 秒"
        return f"本局前 {self.free_hint_quota} 次字词提示免费，提示冷却 {full} 秒"

    def rank_hint_remaining(self):
        if not self.rank_mode:
            return None
        return max(0, rank_hint_limit(self.rank_id) - self.rank_hint_used)

    def can_take_hint(self):
        remaining = self.rank_hint_remaining()
        return remaining is None or remaining > 0

    def note_hint_used(self):
        if self.rank_mode:
            self.rank_hint_used += 1

    def hint_cooldown_remaining(self):
        return max(0, int(self.hint_cooldown_until - time.perf_counter() + 0.999))

    def start_hint_cooldown(self, initial=False):
        seconds = self.initial_hint_cooldown_seconds() if initial else self.hint_cooldown_seconds()
        if seconds <= 0:
            return
        self.hint_cooldown_until = time.perf_counter() + seconds
        self.update_hint_cooldown_button()

    def update_hint_cooldown_button(self):
        if self.hint_cooldown_job:
            self.after_cancel(self.hint_cooldown_job)
            self.hint_cooldown_job = None
        if not self.game_active or not self.hint_button:
            return
        if not self.can_take_hint():
            self.hint_button.disable("0")
            return
        if self.is_clue_mode() and self.clue_visible_count >= len(self.clue_lines):
            self.hint_button.disable("无")
            return
        seconds_left = self.hint_cooldown_until - time.perf_counter()
        remaining = max(0, int(math.ceil(seconds_left)))
        if remaining > 0:
            self.hint_button.disable(str(remaining))
            next_tick = seconds_left - (remaining - 1)
            delay_ms = max(80, min(1000, int(next_tick * 1000) + 20))
            self.hint_cooldown_job = self.after(delay_ms, self.update_hint_cooldown_button)
        else:
            self.hint_button.enable("提示")

    def add_score_penalty(self, amount):
        self.score_penalty += amount
        self.update_score_label()

    def update_score_label(self):
        if self.score_label:
            score = self.current_score()
            color = self.theme_color("danger") if score < 0 else self.theme_color("success")
            self.score_label.config(text=f"{score} 分", fg=color)

    def show_library_hint(self):
        if self.library_hint_used:
            return
        self.library_hint_used = True
        self.library_hint_text = f"这个词属于：{self.current.source_label}"
        normal_cost = self.library_hint_cost()
        cost = self.library_hint_penalty_cost(self.tutorial_active, normal_cost)
        if cost:
            self.add_score_penalty(cost)
        self.hint_penalties.append({"type": "library", "cost": cost, "normal_cost": normal_cost})
        if self.library_hint_button:
            self.library_hint_button.disable("已提示")
        if self.library_hint_label:
            if self.tutorial_active:
                self.library_hint_label.config(text=f"{self.library_hint_text}\n教程免费（正式局约 -{normal_cost} 分）")
            else:
                self.library_hint_label.config(text=f"{self.library_hint_text}\n-{cost} 分")
        if self.tutorial_active and self.tutorial_step in {"question", "hint", "library"}:
            self.advance_tutorial_game_step("answer")

    def _lookup_initials(self, answer):
        round_lookup = getattr(self, "round_initial_lookup", None)
        for key in self.answer_equivalence_keys(answer):
            initials = (round_lookup or {}).get(key)
            if initials:
                return initials
        if round_lookup is None:
            for term in self.terms:
                if answers_equivalent(term.chinese, answer):
                    return term.initials
        lookup_mode = None if self.is_random_group_mode() or self.custom_mode else self.mode
        return self.library.lookup_initials(answer, lookup_mode)

    def show_clue_hint(self):
        if self.clue_visible_count >= len(self.clue_lines):
            if self.feedback:
                self.feedback.config(text="五条线索已经全部显示。", fg=self.themed_legacy_color("#9ca8c7", "fg"))
            if self.hint_button:
                self.hint_button.disable("无")
            return False
        try:
            reveal_count = int(self.custom_config.get("clue_reveal_count") or 1) if self.custom_mode else 1
        except (TypeError, ValueError):
            reveal_count = 1
        reveal_count = max(1, min(5, reveal_count))
        for _ in range(reveal_count):
            if self.clue_visible_count >= len(self.clue_lines):
                break
            hint_number = self.clue_visible_count
            self.clue_visible_count += 1
            normal_cost = self.clue_hint_cost(hint_number)
            cost = 0 if getattr(self, "tutorial_active", False) else normal_cost
            if cost > 0:
                self.add_score_penalty(cost)
                self.paid_hint_count += 1
            else:
                self.free_hint_count += 1
            line = self.clue_lines[self.clue_visible_count - 1]
            line_type = self.clue_line_types[self.clue_visible_count - 1] if self.clue_visible_count - 1 < len(self.clue_line_types) else "complete"
            cost_text = f"-{cost} 分" if cost > 0 else "免费"
            self.hint_lines.append(f"线索提示 {self.clue_visible_count}：{line}    {cost_text}")
            self.hint_penalties.append({
                "type": "clue" if cost > 0 else "free_clue",
                "line_index": self.clue_visible_count,
                "line_type": line_type,
                "cost": cost,
                "normal_cost": normal_cost,
            })
        self._render_clues()
        if self.hint_button and self.clue_visible_count >= len(self.clue_lines):
            self.hint_button.disable("无")
        if self.is_custom_challenge_mode() and self.clue_visible_count >= len(self.clue_lines):
            self.fail_game("提示已经把线索揭完，本次挑战失败。")
        return True

    def show_hint(self):
        if not self.game_active:
            return
        if self.hint_cooldown_remaining() > 0:
            self.update_hint_cooldown_button()
            return
        if not self.can_take_hint():
            if self.feedback:
                self.feedback.config(text="本段位的提示次数已经用完。", fg=self.themed_legacy_color("#f6d36b", "fg"))
            self.update_hint_cooldown_button()
            return
        if self.is_clue_mode():
            if self.show_clue_hint():
                self.note_hint_used()
                self.start_hint_cooldown()
                if getattr(self, "tutorial_active", False) and self.tutorial_step in {"question", "hint"}:
                    self.advance_tutorial_game_step("library")
            return
        answer = self.current.chinese
        candidates = [idx for idx in range(len(answer)) if idx not in self.revealed_positions]
        if not candidates:
            self.fail_game("提示已经把答案全部揭晓，本题失败。")
            return
        idx = random.choice(candidates)
        self.revealed_positions.add(idx)
        masked = "".join(ch if i in self.revealed_positions else "＿" for i, ch in enumerate(answer))
        hint_number = self.free_hint_count + self.paid_hint_count + 1
        normal_cost = self.character_hint_cost(hint_number)
        if self.free_hint_count < self.free_hint_quota:
            self.free_hint_count += 1
            self.hint_penalties.append({"type": "free_character", "index": idx, "char": answer[idx], "cost": 0, "normal_cost": normal_cost})
            line = f"免费提示 {self.free_hint_count}/{self.free_hint_quota}：第 {idx + 1} 个字是“{answer[idx]}”    {masked}"
        else:
            self.paid_hint_count += 1
            char_cost = normal_cost
            self.add_score_penalty(char_cost)
            self.hint_penalties.append({"type": "character", "index": idx, "char": answer[idx], "cost": char_cost})
            line = f"付费提示 {self.paid_hint_count}：第 {idx + 1} 个字是“{answer[idx]}”    {masked}    -{char_cost} 分"
        self.hint_lines.append(line)
        self._render_hints()
        self.note_hint_used()
        if len(self.revealed_positions) >= len(answer):
            self.fail_game("提示已经把答案全部揭晓，本题失败。")
            return
        self.start_hint_cooldown()
        if self.tutorial_active and self.tutorial_step in {"question", "hint"}:
            self.advance_tutorial_game_step("library")

    def _render_hints(self):
        if not self.hint_box:
            return
        widget = getattr(self, "hint_text_widget", None)
        if not widget or not widget.winfo_exists():
            for child in self.hint_box.winfo_children():
                child.destroy()
            body = tk.Frame(self.hint_box, bg=self.themed_legacy_color("#101827", "bg"))
            body.pack(fill="both", expand=True, padx=12, pady=8)
            widget = tk.Text(
                body,
                height=getattr(self, "hint_box_rows", 4),
                width=1,
                wrap="word",
                fg=self.themed_legacy_color("#dce6ff", "fg"),
                bg=self.themed_legacy_color("#101827", "bg"),
                relief="flat",
                bd=0,
                highlightthickness=0,
                insertwidth=0,
                padx=0,
                pady=0,
                font=("Microsoft YaHei UI", 12, "bold"),
            )
            scrollbar = tk.Scrollbar(
                body,
                orient="vertical",
                command=widget.yview,
                width=12,
                bg=self.themed_legacy_color("#1f2a44", "bg"),
                activebackground=self.themed_legacy_color("#3b4560", "highlightbackground"),
                troughcolor=self.themed_legacy_color("#101827", "troughcolor"),
                bd=0,
                highlightthickness=0,
            )
            widget.configure(yscrollcommand=scrollbar.set)
            widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y", padx=(8, 0))
            widget.tag_configure("placeholder", foreground=self.themed_legacy_color("#64708f", "fg"), font=("Microsoft YaHei UI", 11))
            widget.tag_configure("hint", foreground=self.themed_legacy_color("#dce6ff", "fg"), font=("Microsoft YaHei UI", 12, "bold"))
            self.hint_text_widget = widget
            self.hint_scrollbar = scrollbar
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        if not self.hint_lines:
            text = "提示会出现在这里。"
            if self.free_hint_quota:
                text = f"提示会出现在这里。本局前 {self.free_hint_quota} 次字词提示免费；每次提示后冷却 {self.hint_cooldown_seconds()} 秒。"
            widget.insert("1.0", text, "placeholder")
            widget.config(state="disabled")
            return
        widget.insert("1.0", "\n".join(self.hint_lines), "hint")
        widget.see(tk.END)
        widget.config(state="disabled")

    def _render_clue_markdown_line(self, parent, index, line, line_type, *, base_size, wrap_chars, pady):
        prefix = "破碎" if line_type == "fragment" else "线索"
        fg = self.themed_legacy_color("#f6d36b", "fg") if line_type == "fragment" else self.themed_legacy_color("#dce6ff", "fg")
        return render_inline_markdown(
            parent,
            content=f"{index}. **{prefix}**：{line}",
            fg=fg,
            bg=self.themed_legacy_color("#182033", "bg"),
            base_size=base_size,
            bold=line_type == "fragment",
            wrap_chars=wrap_chars,
            pady=pady,
        )

    def _render_clues(self):
        if not self.clue_box:
            return
        for child in self.clue_box.winfo_children():
            child.destroy()
        for index, line in enumerate(self.clue_lines[:self.clue_visible_count], 1):
            line_type = self.clue_line_types[index - 1] if index - 1 < len(self.clue_line_types) else "complete"
            self._render_clue_markdown_line(
                self.clue_box,
                index,
                line,
                line_type,
                base_size=13,
                wrap_chars=60 if self.rank_mode and self.rank_kind == "clue" else 46,
                pady=5,
            )
        if self.clue_visible_count < len(self.clue_lines):
            remaining = len(self.clue_lines) - self.clue_visible_count
            next_cost = self.clue_hint_cost(self.clue_visible_count)
            cost_text = "下次提示免费。" if next_cost <= 0 else f"下次提示扣 {next_cost} 分。"
            tk.Label(
                self.clue_box,
                text=f"还有 {remaining} 条线索可提示；{cost_text}",
                fg=self.themed_legacy_color("#9ca8c7", "fg"),
                bg=self.themed_legacy_color("#182033", "bg"),
                justify="left",
                anchor="w",
                wraplength=620,
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(anchor="w", fill="x", pady=(7, 0))

    def finish_game(self, success=True):
        elapsed = time.perf_counter() - self.start_time
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        record_path = self.save_record(success, elapsed, "answered")
        self.game_active = False
        self.record_saved = True
        final_score = self.current_score(elapsed) if success else self.round_failure_score(elapsed)
        weighted_score = final_score * self.current_score_weight()
        if self.tutorial_active:
            if success:
                self.show_tutorial_complete(elapsed, record_path)
            else:
                self.show_result(elapsed, record_path, success=success)
            return
        if self.rank_mode:
            if success:
                self.timed_correct += 1
                self.rank_session_score += final_score
                if self.rank_question_index + 1 >= len(self.rank_requirements):
                    mark_rank_passed(self.rank_subject, self.rank_id, self.rank_kind, score=self.rank_session_score)
                    self.show_rank_result(True, elapsed=elapsed, record_path=record_path)
                    return
                self.rank_question_index += 1
                self.start_round(transition=False)
                return
            self.show_rank_result(False, reason=f"{rank_kind_label(self.rank_kind)}题未答出", elapsed=elapsed, record_path=record_path)
            return
        if self.is_custom_challenge_mode():
            if success:
                self.timed_correct += 1
                if self.timed_correct >= self.custom_challenge_target():
                    self.show_custom_challenge_result(True, elapsed=elapsed, record_path=record_path)
                    return
                self.start_round(transition=False)
                return
            self.show_custom_challenge_result(False, reason="自定义挑战题未答出", elapsed=elapsed, record_path=record_path)
            return
        if self.is_timed_mode():
            if success:
                self.timed_correct += 1
                self.timed_score += weighted_score
            self.continue_or_finish_timed()
            return
        self.feedback.config(text=f"答对啦！用时 {elapsed:.1f} 秒", fg=self.themed_legacy_color("#9ff2b2", "fg"))
        self.show_result(elapsed, record_path, success=success)

    def cheat_game(self, blocked_initials):
        if not self.game_active or self.record_saved:
            return
        self.cheat_pending = False
        elapsed = time.perf_counter() - self.start_time
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        normal_score = self.current_score(elapsed)
        self.cheat_info = {
            "trigger": "repeated_initials",
            "input_initials": blocked_initials,
            "warning_count": self.initial_input_warnings,
            "normal_score": normal_score,
        }
        self.attempts.append({
            "answer": blocked_initials,
            "answer_initials": self.current.initials,
            "time_seconds": round(elapsed, 3),
            "result": "cheat",
            "cheat_input_initials": blocked_initials,
            "cheat_warning_count": self.initial_input_warnings,
        })
        record_path = self.save_record(False, elapsed, "cheated", "再次输入题面首字母")
        self.game_active = False
        self.record_saved = True
        if self.rank_mode:
            self.show_rank_result(False, reason="触发隐藏彩蛋", elapsed=elapsed, record_path=record_path, cheated=True)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason="触发隐藏彩蛋", elapsed=elapsed, record_path=record_path, cheated=True)
            return
        self.show_result(elapsed, record_path, success=False, failed_reason="再次输入题面首字母", cheated=True)

    def fail_game(self, reason):
        if not self.game_active or self.record_saved:
            return
        elapsed = time.perf_counter() - self.start_time
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        record_path = self.save_record(False, elapsed, "hint_failure", reason)
        self.game_active = False
        self.record_saved = True
        if self.rank_mode:
            self.show_rank_result(False, reason=reason, elapsed=elapsed, record_path=record_path)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason=reason, elapsed=elapsed, record_path=record_path)
            return
        if self.is_timed_mode():
            self.continue_or_finish_timed()
            return
        self.show_result(elapsed, record_path, success=False, failed_reason=reason)

    def reveal_answer(self):
        if not self.game_active or self.record_saved or not self.can_reveal_answer():
            return
        if not messagebox.askyesno("揭晓答案", "确定要揭晓答案吗？本题会记为未答出。"):
            return
        elapsed = time.perf_counter() - self.start_time
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.attempts.append({
            "answer": "",
            "answer_initials": "",
            "time_seconds": round(elapsed, 3),
            "result": "revealed",
        })
        reason = "主动揭晓答案"
        record_path = self.save_record(False, elapsed, "revealed", reason)
        self.game_active = False
        self.record_saved = True
        if self.rank_mode:
            self.show_rank_result(False, reason=reason, elapsed=elapsed, record_path=record_path)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason=reason, elapsed=elapsed, record_path=record_path)
            return
        self.show_result(elapsed, record_path, success=False, failed_reason=reason)

    def continue_or_finish_timed(self):
        if self.rank_mode:
            self.fail_rank_challenge("段位挑战中断")
            return
        if self.timed_deadline and time.perf_counter() < self.timed_deadline:
            self.start_round(transition=False)
        else:
            self.show_timed_result()

    def fail_rank_challenge(self, reason, finished_by="timeout"):
        if not self.rank_mode:
            return
        elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        record_path = None
        if self.game_active and not self.record_saved and self.current:
            self.attempts.append({
                "answer": "",
                "answer_initials": "",
                "time_seconds": round(elapsed, 3),
                "result": finished_by,
            })
            record_path = self.save_record(False, elapsed, finished_by, reason)
            self.record_saved = True
        self.game_active = False
        self.show_rank_result(False, reason=reason, elapsed=elapsed, record_path=record_path)

    def fail_custom_challenge(self, reason, finished_by="timeout"):
        if not self.is_custom_challenge_mode():
            return
        elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        record_path = None
        if self.game_active and not self.record_saved and self.current:
            self.attempts.append({
                "answer": "",
                "answer_initials": "",
                "time_seconds": round(elapsed, 3),
                "result": finished_by,
            })
            record_path = self.save_record(False, elapsed, finished_by, reason)
            self.record_saved = True
        self.game_active = False
        self.show_custom_challenge_result(False, reason=reason, elapsed=elapsed, record_path=record_path)

    def abandon_game(self, next_screen):
        if self.game_active and not self.record_saved and self.start_time and self.current:
            elapsed = time.perf_counter() - self.start_time
            record_path = self.save_record(False, elapsed, "abandoned", "中途退出")
            self.record_saved = True
            if self.rank_mode:
                self.game_active = False
                self.show_rank_result(False, reason="中途退出", elapsed=elapsed, record_path=record_path)
                return
            if self.is_custom_challenge_mode():
                self.game_active = False
                self.show_custom_challenge_result(False, reason="自定义挑战中断", elapsed=elapsed, record_path=record_path)
                return
        self.game_active = False
        next_screen()

    def term_feedback_mode_context(self):
        parts = []
        if self.tutorial_active:
            parts.append("教程模式")
        elif self.rank_mode:
            parts.append(f"{subject_label(self.rank_subject)}{rank_kind_label(self.rank_kind)}")
            try:
                rank = rank_by_id(self.rank_id)
            except Exception:
                rank = None
            if rank:
                parts.append(rank.get("name") or f"Class {self.rank_id}")
            if self.rank_kind != "crossword":
                parts.append(f"第 {self.rank_question_index + 1} 题")
        elif self.custom_mode:
            parts.append("自定义模式")
            subject = self.custom_config.get("subject") or self.mode
            play_kind = self.custom_config.get("play_kind") or self.play_mode
            if subject:
                parts.append(str(subject))
            if play_kind:
                parts.append(str(play_kind))
        else:
            if self.mode:
                parts.append(str(self.mode))
            if self.play_mode:
                parts.append(str(self.play_mode))
        if self.difficulty:
            parts.append(str(self.difficulty))
        return " / ".join(part for part in parts if part) or "未知模式"

    def term_feedback_record_path_text(self, record_path):
        if not record_path:
            return ""
        path = Path(record_path)
        try:
            return path.relative_to(PROJECT_DIR).as_posix()
        except ValueError:
            return str(path)

    def submit_result_term_feedback(self, action, proposed_change="", record_path=None, popup=None):
        if not self.current:
            messagebox.showerror("反馈失败", "当前没有可反馈的词条。", parent=popup or self)
            return
        source_label = getattr(self.current, "source_label", "") or Path(getattr(self.current, "source", "")).stem or "未知"
        try:
            submit_term_feedback(
                self.current_account,
                action,
                self.term_feedback_mode_context(),
                source_label,
                self.current.chinese,
                proposed_change=proposed_change,
                source_file=getattr(self.current, "source", ""),
                record_path=self.term_feedback_record_path_text(record_path),
            )
        except ValueError as exc:
            messagebox.showerror("反馈失败", str(exc), parent=popup or self)
            return
        if popup and popup.winfo_exists():
            popup.destroy()
        messagebox.showinfo("反馈成功", "反馈成功。", parent=self)

    def show_term_feedback_dialog(self, record_path=None):
        if not self.current:
            messagebox.showerror("反馈失败", "当前没有可反馈的词条。")
            return
        popup = tk.Toplevel(self)
        popup.title("词条反馈")
        popup.configure(bg="#111725")
        popup.geometry("520x320")
        popup.minsize(460, 280)
        popup.transient(self)
        popup.grab_set()
        panel = tk.Frame(popup, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(panel, text="反馈这个词", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=22, pady=(20, 8))
        info = f"{self.current.source_label} / {self.current.chinese}"
        tk.Label(panel, text=info, fg="#c8d2ee", bg="#182033", wraplength=450, justify="left", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=22, pady=(0, 18))
        buttons = tk.Frame(panel, bg="#182033")
        buttons.pack(anchor="w", padx=22, pady=(8, 0))
        HoverButton(
            buttons,
            "这个词应该删掉",
            lambda: self.submit_result_term_feedback("delete", record_path=record_path, popup=popup),
            width=190,
            height=54,
            accent="#ff9b89",
        ).grid(row=0, column=0, padx=(0, 12), pady=8)
        HoverButton(
            buttons,
            "这个词应该改动",
            lambda: self.show_term_modify_feedback_dialog(record_path, popup),
            width=190,
            height=54,
            accent="#ffcf8f",
        ).grid(row=0, column=1, padx=12, pady=8)
        HoverButton(panel, "取消", popup.destroy, width=112, height=46, accent="#8fb6ff").pack(anchor="w", padx=22, pady=(16, 0))
        self.apply_static_theme(popup)

    def show_term_modify_feedback_dialog(self, record_path=None, previous_popup=None):
        if previous_popup and previous_popup.winfo_exists():
            previous_popup.destroy()
        popup = tk.Toplevel(self)
        popup.title("词条改动反馈")
        popup.configure(bg="#111725")
        popup.geometry("620x420")
        popup.minsize(520, 360)
        popup.transient(self)
        popup.grab_set()
        panel = tk.Frame(popup, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(panel, text="这个词应该改为什么？", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w", padx=22, pady=(18, 8))
        tk.Label(panel, text=f"当前词：{self.current.chinese}", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=22, pady=(0, 10))
        entry = tk.Text(
            panel,
            height=6,
            wrap="word",
            fg=self.themed_legacy_color("#fff8dc", "fg"),
            bg=self.themed_legacy_color("#101827", "bg"),
            insertbackground=self.themed_legacy_color("#fff8dc", "insertbackground"),
            relief="flat",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        entry.configure(
            highlightthickness=1,
            highlightbackground=self.themed_legacy_color("#30384e", "highlightbackground"),
            highlightcolor=self.theme_color("accent"),
        )
        entry.pack(fill="both", expand=True, padx=22, pady=(0, 14))

        def submit():
            proposed = entry.get("1.0", "end").strip()
            self.submit_result_term_feedback("modify", proposed_change=proposed, record_path=record_path, popup=popup)

        row = tk.Frame(panel, bg="#182033")
        row.pack(anchor="w", padx=22, pady=(0, 18))
        HoverButton(row, "提交反馈", submit, width=150, height=52, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 10))
        HoverButton(row, "取消", popup.destroy, width=112, height=52, accent="#ff9b89").grid(row=0, column=1)
        self.apply_static_theme(panel)
        self.after(80, entry.focus_set)

    def show_result(self, elapsed, record_path, success=True, failed_reason="", cheated=False):
        self.play_music("result")
        self.play_sfx("fail" if (cheated or not success) else "success")
        self.clear(transition=False)
        frame = tk.Frame(self.container, bg=self.theme_color("base"))
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.74, relheight=0.76)
        self.decorate_surface(card, "constellation", opacity_scale=0.26)
        if cheated:
            final_score = -abs(int(self.cheat_info.get("normal_score", self.current_score(elapsed))))
        else:
            final_score = self.current_score(elapsed) if success else self.round_failure_score(elapsed)
        score_weight = self.current_score_weight()
        weighted_score = final_score * score_weight
        score_color = "#ff9b89" if final_score < 0 else "#9ff2b2"
        if cheated:
            title = "隐藏彩蛋触发"
            title_color = "#ff9b89"
        else:
            title = "答对啦" if success else "本题失败"
            title_color = "#9ff2b2" if success else "#ff9b89"
        tk.Label(card, text=title, fg=title_color, bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(38, 8))
        if failed_reason:
            tk.Label(card, text=failed_reason, fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(0, 8))
        tk.Label(card, text=f"用时 {elapsed:.1f} 秒", fg="#fff2bd", bg="#182033", font=("Consolas", 26, "bold")).pack(pady=4)
        tk.Label(card, text=f"积分 {final_score} 分", fg=score_color, bg="#182033", font=("Consolas", 22, "bold")).pack(pady=4)
        if score_weight > 0:
            score_note = f"计入总积分 {format_score(weighted_score)} 分（权重 {score_weight:g}）"
        else:
            score_note = "本模式不计入总积分、Rating 和成就"
        tk.Label(card, text=score_note, fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(pady=2)
        detail_frame = tk.Frame(card, bg="#182033")
        detail_frame.pack(fill="x", padx=82, pady=(20, 0))
        topic_text = "题目：线索模式" if self.is_clue_mode() else f"题目：{self.display_initials}"
        if self.mask_count and not self.is_clue_mode():
            topic_text += f"（原始 {self.current.initials}，掩码 {self.mask_count} 个）"
        tk.Label(detail_frame, text=topic_text, fg="#c8d2ee", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 14)).pack(anchor="w", fill="x", pady=(0, 4))
        tk.Label(detail_frame, text=f"本题总难度：{self.effective_difficulty:g}", fg="#9ca8c7", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", pady=2)
        notice_text = self.current_term_notice_text()
        answer_text = f"本轮答案：{self.current.chinese}"
        if notice_text:
            answer_text += f"（{notice_text}）"
        tk.Label(detail_frame, text=answer_text, fg="#c8d2ee", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 14)).pack(anchor="w", fill="x", pady=4)
        if self.is_clue_mode():
            tk.Label(detail_frame, text="本轮线索", fg="#8fb6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", pady=(8, 3))
            for index, line in enumerate(self.clue_lines[:self.clue_visible_count], 1):
                line_type = self.clue_line_types[index - 1] if index - 1 < len(self.clue_line_types) else "complete"
                self._render_clue_markdown_line(
                    detail_frame,
                    index,
                    line,
                    line_type,
                    base_size=10,
                    wrap_chars=82,
                    pady=(0, 3),
                )
        else:
            answer_title = "本词库同首字母可接受解"
            if self.mask_count:
                answer_title = "本词库匹配当前掩码的可接受解"
            tk.Label(detail_frame, text=answer_title, fg="#8fb6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", pady=(10, 3))
            answer_box = self.render_clickable_answers(detail_frame, self.accepted_answers, height=3, base_size=11)
            answer_box.pack(fill="x", pady=(0, 8))
        try:
            record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
        except ValueError:
            record_display = f"record/{record_path.name}"
        tk.Label(detail_frame, text=f"记录已保存：{record_display}", fg="#7683a3", bg="#182033", justify="left", anchor="w", wraplength=760, font=("Microsoft YaHei UI", 10)).pack(anchor="w", fill="x", pady=(4, 18))
        buttons = tk.Frame(card, bg="#182033")
        buttons.pack()
        if self.tutorial_active:
            HoverButton(buttons, "再试教程题", self.start_tutorial_round, width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "跳过教程", self.skip_tutorial, width=180, height=62, accent="#ff9b89").grid(row=0, column=1, padx=12)
        elif self.custom_mode:
            HoverButton(buttons, "再练一局", self.restart_custom_session, width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回配置", self.show_custom_config, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)
        else:
            HoverButton(buttons, "再来一局", lambda: self.start_game(self.difficulty), width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回模式", self.show_mode_select, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)
        HoverButton(buttons, "反馈", lambda record_path=record_path: self.show_term_feedback_dialog(record_path), width=150, height=62, accent="#ffcf8f").grid(row=0, column=2, padx=12)
        self.reveal_background_surface(card)

    def show_custom_challenge_result(self, passed, reason="", elapsed=None, record_path=None, cheated=False):
        self.play_music("result")
        self.play_sfx("success" if passed and not cheated else "fail")
        self.clear(transition=False)
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        frame = tk.Frame(self.container, bg=self.theme_color("base"))
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.66)
        self.decorate_surface(card, "constellation", opacity_scale=0.26)
        if cheated:
            title = "隐藏彩蛋触发"
            title_color = "#ff6b8a"
        else:
            title = "自定义挑战成功" if passed else "自定义挑战失败"
            title_color = "#9ff2b2" if passed else "#ff9b89"
        target = self.custom_challenge_target()
        tk.Label(card, text=title, fg=title_color, bg="#182033", font=("Microsoft YaHei UI", 36, "bold")).pack(pady=(48, 10))
        if self.custom_config.get("play_kind") == "字谜" and self.crossword_puzzle:
            progress_text = f"进度 {len(self.crossword_solved_ids)}/{len(self.crossword_puzzle.placements)} 词"
        else:
            progress_text = f"进度 {self.timed_correct}/{target} 题"
        tk.Label(card, text=progress_text, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).pack(pady=6)
        mode_parts = [self.custom_config.get("play_kind", "首字母")]
        if self.is_custom_timed_enabled():
            mode_parts.append(f"限时 {int(self.custom_config.get('minutes', 5))} 分钟")
        tk.Label(card, text=" / ".join(mode_parts), fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(4, 8))
        if reason:
            tk.Label(card, text=reason, fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(0, 8))
        if elapsed is not None:
            tk.Label(card, text=f"本题用时 {elapsed:.1f} 秒", fg="#9ca8c7", bg="#182033", font=("Consolas", 13, "bold")).pack(pady=2)
        tk.Label(card, text="自定义挑战不计总积分、Rating、成就和正式段位", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(pady=(8, 12))
        if record_path:
            try:
                record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
            except ValueError:
                record_display = f"record/{record_path.name}"
            tk.Label(card, text=f"最近记录：{record_display}", fg="#7683a3", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(pady=(0, 12))
        buttons = tk.Frame(card, bg="#182033")
        buttons.pack(pady=(6, 0))
        HoverButton(buttons, "再挑战", self.restart_custom_session, width=170, height=58, accent="#9ff2b2").grid(row=0, column=0, padx=10)
        HoverButton(buttons, "返回配置", self.show_custom_config, width=170, height=58, accent="#9fb7ff").grid(row=0, column=1, padx=10)
        HoverButton(buttons, "返回主页", self.show_home, width=170, height=58, accent="#ffbd7e").grid(row=0, column=2, padx=10)
        self.reveal_background_surface(card)

    def show_timed_result(self):
        self.play_music("result")
        self.play_sfx("success" if self.timed_correct else "fail")
        self.clear()
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        frame = tk.Frame(self.container, bg=self.theme_color("base"))
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.68, relheight=0.62)
        self.decorate_surface(card, "constellation", opacity_scale=0.26)
        title = "自定义限时结束" if self.custom_mode else "限时结束"
        tk.Label(card, text=title, fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(52, 12))
        tk.Label(card, text=f"答对 {self.timed_correct} 题", fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 26, "bold")).pack(pady=7)
        score_text = "本模式不计入总积分" if self.custom_mode else f"计入总积分 {format_score(self.timed_score)} 分"
        tk.Label(card, text=score_text, fg="#fff2bd", bg="#182033", font=("Consolas", 22, "bold")).pack(pady=7)
        minutes = self.custom_config.get("minutes", 5) if self.custom_mode else 5
        desc = f"自定义 / {minutes} 分钟" if self.custom_mode else f"{self.mode} / {self.difficulty} / 5 分钟"
        tk.Label(
            card,
            text=desc,
            fg="#c8d2ee",
            bg="#182033",
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(pady=(10, 24))
        buttons = tk.Frame(card, bg="#182033")
        buttons.pack()
        if self.custom_mode:
            HoverButton(buttons, "再练一轮", self.restart_custom_session, width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回配置", self.show_custom_config, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)
        else:
            HoverButton(buttons, "再来一轮", lambda: self.start_game(self.difficulty), width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回模式", self.show_mode_select, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)
        self.reveal_background_surface(card)

    def restart_custom_session(self):
        if not self.custom_mode or not self.terms:
            self.show_custom_config()
            return
        self.timed_deadline = None
        self.timed_correct = 0
        self.timed_score = 0
        self.custom_session_id = uuid.uuid4().hex
        if self.is_custom_timed_enabled():
            self.timed_deadline = time.perf_counter() + int(self.custom_config.get("minutes", 5)) * 60
        if self.custom_config.get("play_kind") == "字谜":
            self.start_crossword_game("自定义")
            return
        self.start_round()

    def current_rank_answer_entry(self, record=None):
        if not self.rank_mode or self.rank_kind == "crossword" or not self.current:
            return None
        accepted = list(self.accepted_answers or [])
        if not any(answers_equivalent(self.current.chinese, item) for item in accepted):
            accepted.insert(0, self.current.chinese)
        entry = {
            "index": self.rank_question_index + 1,
            "difficulty": self.difficulty,
            "target_difficulty": self.rank_target_difficulty,
            "displayed_initials": self.display_initials,
            "answer": self.current.chinese,
            "accepted_answers": accepted,
            "source_label": self.current.source_label,
            "notice": self.current_term_notice_text(),
        }
        if record:
            entry["success"] = bool(record.get("success"))
            entry["finished_by"] = record.get("finished_by", "")
        return entry

    def remember_rank_answer_entry(self, entry):
        if not entry:
            return
        if not isinstance(getattr(self, "rank_answer_history", None), list):
            self.rank_answer_history = []
        if self.rank_answer_history and self.rank_answer_history[-1].get("index") == entry.get("index"):
            self.rank_answer_history[-1] = entry
        else:
            self.rank_answer_history.append(entry)

    def rank_answer_summary_lines(self):
        return [
            f"{entry['prefix']}{'、'.join(entry['answers'])}"
            for entry in self.rank_answer_summary_entries()
        ]

    def rank_answer_summary_entries(self):
        if self.rank_kind == "crossword":
            if not self.crossword_puzzle:
                return []
            entries = []
            for placement in self.crossword_puzzle.placements:
                direction = "横" if placement.direction == "across" else "纵"
                initials = self.crossword_initials_for_placement(placement)
                accepted = self.crossword_answer_candidates(placement)
                notice = term_notice_text(placement.answer, prefix="含有")
                notice_part = f" {notice}" if notice else ""
                entries.append({
                    "prefix": f"{placement.id:02d} {direction} {len(placement.answer)}字 {initials}{notice_part}：",
                    "answers": [str(answer) for answer in accepted if str(answer or "").strip()],
                })
            return entries
        entries = list(getattr(self, "rank_answer_history", []) or [])
        if not entries:
            current = self.current_rank_answer_entry()
            if current:
                entries = [current]
        result = []
        for entry in entries:
            target = entry.get("target_difficulty")
            try:
                target_text = f"≥{float(target):g}"
            except (TypeError, ValueError):
                target_text = ""
            initials = entry.get("displayed_initials") or "线索题"
            accepted = entry.get("accepted_answers") or [entry.get("answer", "")]
            notice = entry.get("notice") or term_notice_text(entry.get("answer", ""), prefix="含有")
            notice_part = f" {notice}" if notice else ""
            result.append({
                "prefix": f"{int(entry.get('index') or 0):02d} {entry.get('difficulty', '')}{target_text} {initials}{notice_part}：",
                "answers": [str(answer) for answer in accepted if str(answer or "").strip()],
            })
        return result

    def render_rank_failure_answers(self, parent):
        if not self.rank_mode:
            return
        entries = self.rank_answer_summary_entries()
        if not entries:
            return
        title = "本张字谜全部认可答案" if self.rank_kind == "crossword" else "本次已作答题目的认可答案"
        tk.Label(
            parent,
            text=title,
            fg="#8fb6ff",
            bg="#182033",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", fill="x", padx=64, pady=(8, 3))
        shell = tk.Frame(parent, bg="#182033")
        shell.pack(fill="x", padx=64, pady=(0, 10))
        answer_box = tk.Text(
            shell,
            height=max(4, min(9, len(entries))),
            wrap="char",
            fg=self.themed_legacy_color("#dce6ff", "fg"),
            bg=self.themed_legacy_color("#111827", "bg"),
            insertbackground=self.themed_legacy_color("#dce6ff", "insertbackground"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.themed_legacy_color("#30384e", "highlightbackground"),
            font=("Microsoft YaHei UI", 10),
            padx=8,
            pady=6,
        )
        answer_box.tag_configure("link", foreground=self.themed_legacy_color("#9fb7ff", "fg"), underline=False)
        answer_box.tag_configure("link_hover", foreground=self.themed_legacy_color("#fff2bd", "fg"), underline=True, background=self.themed_legacy_color("#26344f", "bg"))
        answer_box.tag_configure("muted", foreground=self.themed_legacy_color("#7683a3", "fg"))
        scrollbar = tk.Scrollbar(shell, orient="vertical", command=answer_box.yview)
        answer_box.configure(yscrollcommand=scrollbar.set)
        answer_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        tag_index = 0
        for line_index, entry in enumerate(entries):
            if line_index:
                answer_box.insert("end-1c", "\n")
            answer_box.insert("end-1c", entry["prefix"], ("muted",))
            for answer_index, answer in enumerate(entry["answers"]):
                if answer_index:
                    answer_box.insert("end-1c", "、", ("muted",))
                tag_index += 1
                start = answer_box.index("end-1c")
                answer_box.insert("end-1c", answer, ("link",))
                end = answer_box.index("end-1c")
                tag = f"rank_term_{tag_index}"
                answer_box.tag_add(tag, start, end)
                explanation = self.term_explanation_for_answer(answer)
                self.bind_term_link(answer_box, tag, answer, explanation)
        answer_box.config(state="disabled")
        self.bind_scroll_wheel(shell, answer_box)

    def show_rank_result(self, passed, reason="", elapsed=None, record_path=None, cheated=False):
        self.play_music("result")
        self.play_sfx("success" if passed and not cheated else "fail")
        self.clear(transition=False)
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        rank = rank_by_id(self.rank_id)
        frame = tk.Frame(self.container, bg=self.theme_color("base"))
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.76, relheight=0.78)
        self.decorate_surface(card, "constellation", opacity_scale=0.26)
        if cheated:
            title = "隐藏彩蛋触发"
            title_color = "#ff6b8a"
        else:
            label = rank_kind_label(self.rank_kind)
            title = f"{label}通过" if passed else f"{label}失败"
            title_color = "#9ff2b2" if passed else "#ff9b89"
        tk.Label(card, text=title, fg=title_color, bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(40, 8))
        tk.Label(card, text=f"{subject_label(self.rank_subject)}{rank_kind_label(self.rank_kind)} / {rank['name']}", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 19, "bold")).pack(pady=4)
        if reason:
            tk.Label(card, text=reason, fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(2, 8))
        if self.rank_kind == "crossword":
            progress_text = (
                f"进度 {len(self.crossword_solved_ids)}/{len(self.crossword_puzzle.placements)} 词    "
                f"总分 {self.rank_session_score}    时限 {format_rank_time(self.crossword_rank_seconds)}"
            )
        else:
            progress_text = f"进度 {self.timed_correct}/{len(self.rank_requirements)} 题    总分 {self.rank_session_score}    时限 {format_rank_time(rank['seconds'])}"
        tk.Label(
            card,
            text=progress_text,
            fg="#c8d2ee",
            bg="#182033",
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(pady=6)
        if elapsed is not None:
            tk.Label(card, text=f"本题用时 {elapsed:.1f} 秒", fg="#9ca8c7", bg="#182033", font=("Consolas", 14, "bold")).pack(pady=2)
        if passed:
            badge_id = rank_badge_id(self.rank_subject, self.rank_id, self.rank_kind)
            badge_width = scaled_int(230)
            badge_height = scaled_int(46)
            badge_canvas = tk.Canvas(card, width=badge_width, height=badge_height, bd=0, highlightthickness=0, bg=self.theme_color("base"))
            badge_canvas.pack(pady=(14, 8))
            draw_rank_badge(badge_canvas, badge_id, badge_width, badge_height, selected=True, transparent=True, background=self.theme_color("base"))
            tk.Label(card, text=f"已解锁：{rank_badge_name(badge_id)}", fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(0, 10))
        else:
            if self.rank_kind == "crossword":
                req_text = f"字谜规格：{self.crossword_rank_size}×{self.crossword_rank_size}，约 {self.crossword_rank_word_count} 词"
            else:
                req_text = "本段题组：" + "、".join(f"{difficulty}≥{target:g}" for difficulty, target in self.rank_requirements)
            tk.Label(card, text=req_text, fg="#9ca8c7", bg="#182033", wraplength=760, justify="left", font=("Microsoft YaHei UI", 11)).pack(padx=64, pady=(12, 10))
            self.render_rank_failure_answers(card)
        if record_path:
            try:
                record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
            except ValueError:
                record_display = f"record/{record_path.name}"
            tk.Label(card, text=f"最近记录：{record_display}", fg="#7683a3", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(pady=(0, 12))
        buttons = tk.Frame(card, bg="#182033")
        buttons.pack(pady=(6, 0))
        HoverButton(buttons, "再挑战", lambda: self.start_rank_challenge(self.rank_id), width=170, height=58, accent="#9ff2b2").grid(row=0, column=0, padx=10)
        HoverButton(buttons, "段位列表", self.show_rank_select, width=170, height=58, accent="#9fb7ff").grid(row=0, column=1, padx=10)
        HoverButton(buttons, "返回主页", self.show_home, width=170, height=58, accent="#ffbd7e").grid(row=0, column=2, padx=10)
        self.reveal_background_surface(card)

    def save_record(self, success, elapsed, finished_by="answered", failed_reason=""):
        now = datetime.now()
        storage_dir = record_storage_dir(now)
        storage_dir.mkdir(parents=True, exist_ok=True)
        is_custom = bool(self.custom_mode)
        is_rank = bool(self.rank_mode)
        is_tutorial = bool(self.tutorial_active)
        final_score = self.current_score(elapsed)
        if finished_by == "cheated":
            final_score = -abs(final_score)
        elif not success:
            final_score = self.round_failure_score(elapsed)
        score_weight = self.current_score_weight()
        subject_value = self.rank_subject if is_rank else (self.custom_config.get("subject", self.mode) if is_custom else self.mode)
        mode_value = self.rank_subject if is_rank else ("自定义" if is_custom else self.mode)
        play_value = rank_kind_label(self.rank_kind) if is_rank else ("自定义" if is_custom else self.play_mode)
        try:
            custom_files = [path.relative_to(WORDS_DIR).as_posix() for path in self.library_files]
        except ValueError:
            custom_files = [path.name for path in self.library_files]
        notice_tags = term_notice_tags(self.current.chinese)
        clue_hint_count = sum(1 for item in self.hint_penalties if item.get("type") in {"clue", "free_clue"})
        record = {
            "version": APP_VERSION,
            "id": uuid.uuid4().hex,
            "created_at": now.isoformat(timespec="seconds"),
            "mode": mode_value,
            "subject": subject_value,
            "play_mode": play_value,
            "difficulty": self.difficulty,
            "custom_mode": 1 if is_custom else 0,
            "rank_mode": 1 if is_rank else 0,
            "tutorial_mode": 1 if is_tutorial else 0,
            "exclude_from_stats": 1 if (is_custom or is_rank or is_tutorial) else 0,
            "custom_config": self.custom_config if is_custom else {},
            "custom_play_kind": self.custom_config.get("play_kind", "") if is_custom else "",
            "custom_files": custom_files if is_custom else [],
            "custom_session_id": self.custom_session_id if is_custom else "",
            "custom_timed_enabled": 1 if (is_custom and self.is_custom_timed_enabled()) else 0,
            "custom_challenge_enabled": 1 if (is_custom and self.is_custom_challenge_mode()) else 0,
            "custom_challenge_target": self.custom_challenge_target() if (is_custom and self.is_custom_challenge_mode()) else 0,
            "custom_challenge_progress": self.timed_correct + (1 if success and self.is_custom_challenge_mode() else 0) if is_custom else 0,
            "rank_subject": self.rank_subject if is_rank else "",
            "rank_kind": self.rank_kind if is_rank else "",
            "rank_progress_key": rank_progress_key(self.rank_subject, self.rank_kind) if is_rank else "",
            "rank_id": self.rank_id if is_rank else 0,
            "rank_question_index": self.rank_question_index + 1 if is_rank else 0,
            "rank_passed_session_id": self.rank_session_id if is_rank else "",
            "rank_target_difficulty": self.rank_target_difficulty if is_rank else 0,
            "rank_relaxed": 1 if (is_rank and self.rank_relaxed) else 0,
            "rank_session_score": self.rank_session_score + (final_score if (is_rank and success) else 0) if is_rank else 0,
            "rank_hint_used": self.rank_hint_used if is_rank else 0,
            "rank_hint_limit": rank_hint_limit(self.rank_id) if is_rank else 0,
            "question_initials": self.current.initials,
            "displayed_initials": self.display_initials,
            "mask_positions": self.mask_positions,
            "mask_count": self.mask_count,
            "clue_mode": 1 if self.is_clue_mode() else 0,
            "clue_source": self.clue_entry.get("source_type", ""),
            "clue_lines": self.clue_lines,
            "shown_clue_lines": self.clue_lines[:self.clue_visible_count],
            "clue_line_types": self.clue_line_types,
            "clue_visible_count": self.clue_visible_count,
            "clue_fragment_count": self.clue_fragment_count,
            "clue_hint_count": clue_hint_count if self.is_clue_mode() else 0,
            "clue_penalty": sum(item.get("cost", 0) for item in self.hint_penalties if item.get("type") == "clue"),
            "selected_answer": self.current.chinese,
            "base_term_difficulty": self.current.difficulty,
            "term_difficulty": self.current.difficulty,
            "effective_difficulty": self.effective_difficulty,
            "accepted_answers": self.accepted_answers,
            "term_notice": self.current_term_notice_text(),
            "term_notice_tags": notice_tags,
            "has_person_name": 1 if "人名" in notice_tags else 0,
            "has_english_letter": 1 if "英文字母" in notice_tags else 0,
            "has_greek_letter": 1 if term_has_greek_letter(self.current.chinese) else 0,
            "source_file": self.current.source,
            "source_label": self.current.source_label,
            "library_files": [path.name for path in self.library_files],
            "scope": self.scope_text,
            "all_answers": self.attempts,
            "success": success,
            "finished_by": finished_by,
            "failed_reason": failed_reason,
            "cheat_detected": 1 if finished_by == "cheated" else 0,
            "cheat_info": self.cheat_info if finished_by == "cheated" else {},
            "elapsed_seconds": round(elapsed, 3),
            "hint_count": len(self.hint_lines),
            "hint_cooldown_seconds": self.hint_cooldown_seconds(),
            "free_hint_quota": self.free_hint_quota,
            "free_hint_count": self.free_hint_count,
            "paid_hint_count": self.paid_hint_count,
            "hints": self.hint_lines,
            "hint_penalties": self.hint_penalties,
            "used_library_hint": 1 if self.library_hint_used else 0,
            "library_hint_text": self.library_hint_text,
            "score_start": 1000,
            "score_time_cost": int(elapsed),
            "score_penalty": self.score_penalty,
            "score": final_score,
            "score_weight": score_weight,
            "weighted_score": round(final_score * score_weight, 3),
            "timed_session": 1 if self.is_timed_mode() else 0,
        }
        if is_rank and self.rank_kind != "crossword":
            self.remember_rank_answer_entry(self.current_rank_answer_entry(record))
            record["rank_session_answers"] = list(self.rank_answer_history)
        path = storage_dir / f"{now.strftime('%Y%m%d_%H%M%S')}_{record['id'][:8]}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        add_record_entry_to_cache(record, path)
        self.refresh_achievements()
        return path
