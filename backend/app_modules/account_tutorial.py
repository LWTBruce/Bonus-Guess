from ._shared import *


class AccountTutorialMixin:
    TUTORIAL_PLAY_MODES = ("自由", "限时", "线索", "字谜")

    def activate_account(self, account):
        self.switch_return_account = None
        self.spectator_admin_account = None
        self.spectated_account = None
        self.current_account = account
        apply_account_context(account["id"])
        settings = load_player_settings()
        if settings.get("nickname") == DEFAULT_PLAYER_SETTINGS["nickname"] and account.get("nickname"):
            settings["nickname"] = account["nickname"]
            settings = save_player_settings(settings)
        self.player_settings = settings
        self.apply_backdrop_theme()
        self.apply_audio_settings()
        self.apply_ui_font_scale()
        if not self.fullscreen:
            self.geometry(f"{self.player_settings['window_width']}x{self.player_settings['window_height']}")
        self.achievements = read_achievements()
        self.complete_achievement("first_launch")
        self.refresh_achievements()
        if self.should_auto_start_tutorial():
            self.start_tutorial(auto=True)
        else:
            self.show_home()

    def is_spectating(self):
        return self.spectator_admin_account is not None and self.spectated_account is not None

    def block_spectator_action(self, action="这个操作"):
        if not self.is_spectating():
            return False
        messagebox.showinfo("旁观模式", f"旁观模式只能查看数据，不能{action}。")
        return True

    def enter_spectator_mode(self, account):
        if not is_admin_account(self.current_account):
            messagebox.showerror("没有权限", "只有管理员账号可以进入旁观模式。")
            return
        self.spectator_admin_account = self.current_account
        self.spectated_account = account
        self.current_account = account
        apply_account_context(account["id"])
        self.player_settings = load_player_settings()
        self.apply_backdrop_theme()
        self.apply_audio_settings()
        self.apply_ui_font_scale()
        self.achievements = read_achievements()
        self.show_home()

    def enter_spectator_history(self, account):
        self.enter_spectator_mode(account)
        if self.is_spectating():
            self.show_history()

    def exit_spectator_mode(self):
        if not self.is_spectating():
            self.show_admin_dashboard()
            return
        admin = self.spectator_admin_account
        self.spectator_admin_account = None
        self.spectated_account = None
        self.current_account = admin
        apply_account_context(admin["id"])
        self.player_settings = load_player_settings()
        self.apply_backdrop_theme()
        self.apply_audio_settings()
        self.apply_ui_font_scale()
        self.achievements = read_achievements()
        self.show_admin_dashboard()

    def should_auto_start_tutorial(self):
        return bool(self.current_account) and not self.is_spectating() and not bool(self.player_settings.get("tutorial_completed", True))

    def admin_reveal_hidden_enabled(self):
        return (
            not self.is_spectating()
            and is_admin_account(self.current_account)
            and bool((self.player_settings or {}).get("admin_reveal_hidden", False))
        )

    def save_tutorial_completed(self):
        settings = dict(self.player_settings or DEFAULT_PLAYER_SETTINGS)
        settings["tutorial_completed"] = True
        self.player_settings = save_player_settings(settings)

    def tutorial_play_label(self):
        return self.normalize_tutorial_play_mode(getattr(self, "tutorial_play_mode", "自由"))

    def normalize_tutorial_play_mode(self, play_mode):
        text = str(play_mode or "自由").strip()
        return text if text in self.TUTORIAL_PLAY_MODES else "自由"

    def apply_tutorial_mode_selection(self):
        play_mode = self.tutorial_play_label()
        self.selected_subject = "物理模式"
        self.selected_game_group = "普通"
        self.selected_rule_mode = play_mode
        self.selected_play_mode = play_mode
        self.mode = "物理模式"
        self.play_mode = play_mode
        self.true_random_mode = False
        self.random_group_mode = False
        self.crossword_random = False

    def start_tutorial(self, auto=False, play_mode="自由"):
        if self.is_spectating():
            return
        self.tutorial_manual = not auto
        self.tutorial_play_mode = self.normalize_tutorial_play_mode(play_mode)
        self.tutorial_active = True
        self.tutorial_step = "home"
        self.apply_tutorial_mode_selection()
        self.show_home()

    def skip_tutorial(self):
        self.clear_tutorial_overlay()
        if self.timer_job:
            try:
                self.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        self.tutorial_active = False
        self.save_tutorial_completed()
        self.show_home()

    def clear_tutorial_overlay(self):
        for widget in getattr(self, "tutorial_overlay_widgets", []):
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except tk.TclError:
                pass
        self.tutorial_overlay_widgets = []

    def make_tutorial_overlay_window(self, x, y, w, h, color, alpha=None):
        if w <= 0 or h <= 0:
            return None
        root_x = self.container.winfo_rootx()
        root_y = self.container.winfo_rooty()
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.configure(bg=color)
        try:
            win.transient(self)
            if alpha is not None:
                win.attributes("-alpha", alpha)
        except tk.TclError:
            pass
        win.geometry(f"{int(max(1, w))}x{int(max(1, h))}+{int(root_x + x)}+{int(root_y + y)}")
        self.tutorial_overlay_widgets.append(win)
        return win

    def render_tutorial_overlay(self, targets, title, body, next_text=None, next_command=None):
        if not self.tutorial_active:
            return
        self.clear_tutorial_overlay()
        target_list = list(targets) if isinstance(targets, (list, tuple)) else [targets]
        self.after(90, lambda: self._place_tutorial_overlay(target_list, title, body, next_text, next_command))

    def _place_tutorial_overlay(self, targets, title, body, next_text=None, next_command=None):
        if not self.tutorial_active or not self.container.winfo_exists():
            return
        live_targets = []
        for widget in targets:
            try:
                if widget and widget.winfo_exists():
                    live_targets.append(widget)
            except tk.TclError:
                pass
        if not live_targets:
            return
        self.clear_tutorial_overlay()
        self.update_idletasks()
        root_x = self.container.winfo_rootx()
        root_y = self.container.winfo_rooty()
        width = max(self.container.winfo_width(), 1)
        height = max(self.container.winfo_height(), 1)
        margin = scaled_int(14)
        bounds = []
        for widget in live_targets:
            try:
                x = widget.winfo_rootx() - root_x
                y = widget.winfo_rooty() - root_y
                bounds.append((x, y, x + widget.winfo_width(), y + widget.winfo_height()))
            except tk.TclError:
                continue
        if not bounds:
            return
        left = max(0, min(item[0] for item in bounds) - margin)
        top = max(0, min(item[1] for item in bounds) - margin)
        right = min(width, max(item[2] for item in bounds) + margin)
        bottom = min(height, max(item[3] for item in bounds) + margin)

        def add_block(x, y, w, h, color="#070b13", alpha=None):
            if w <= 0 or h <= 0:
                return
            win = self.make_tutorial_overlay_window(x, y, w, h, color, alpha=alpha)
            if win:
                try:
                    win.lift()
                except tk.TclError:
                    pass

        dim_alpha = 0.40
        add_block(0, 0, width, top, alpha=dim_alpha)
        add_block(0, bottom, width, height - bottom, alpha=dim_alpha)
        add_block(0, top, left, bottom - top, alpha=dim_alpha)
        add_block(right, top, width - right, bottom - top, alpha=dim_alpha)
        ring = "#f6d36b"
        add_block(left, max(0, top - 3), right - left, 3, ring)
        add_block(left, bottom, right - left, 3, ring)
        add_block(max(0, left - 3), top, 3, bottom - top, ring)
        add_block(right, top, 3, bottom - top, ring)

        gap = scaled_int(18)
        edge = scaled_int(24)
        min_callout_width = scaled_int(340)
        default_callout_width = min(scaled_int(520), max(min_callout_width, width - scaled_int(72)))
        space_right = width - right - gap - edge
        space_left = left - gap - edge
        callout_width = default_callout_width
        if space_right >= min_callout_width:
            callout_width = min(default_callout_width, space_right)
        elif space_left >= min_callout_width:
            callout_width = min(default_callout_width, space_left)
        callout_window = self.make_tutorial_overlay_window(0, 0, callout_width, 1, "#182033")
        if not callout_window:
            return
        callout = tk.Frame(callout_window, bg="#182033", highlightbackground="#f6d36b", highlightthickness=1)
        tk.Label(callout, text=title, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 17, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        tk.Label(
            callout,
            text=self.smart_wrap_text(body, 28),
            fg="#dce6ff",
            bg="#182033",
            justify="left",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", padx=18, pady=(0, 12))
        row = tk.Frame(callout, bg="#182033")
        row.pack(anchor="w", padx=18, pady=(0, 16))
        if next_text and next_command:
            HoverButton(row, next_text, next_command, width=138, height=46, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 10))
        HoverButton(row, "跳过教程", self.skip_tutorial, width=138, height=46, accent="#ff9b89").grid(row=0, column=1 if next_text else 0, padx=(0, 10))
        callout.pack(fill="both", expand=True)
        self.apply_static_theme(callout_window)
        callout.update_idletasks()
        callout_height = callout.winfo_reqheight()
        if bottom + gap + callout_height <= height:
            callout_y = bottom + gap
            callout_x = min(max(left, edge), max(edge, width - callout_width - edge))
        elif top - gap - callout_height >= edge:
            callout_y = top - callout_height - gap
            callout_x = min(max(left, edge), max(edge, width - callout_width - edge))
        elif space_right >= min_callout_width:
            callout_x = right + gap
            callout_y = min(max(top, edge), max(edge, height - callout_height - edge))
        elif space_left >= min_callout_width:
            callout_x = max(edge, left - gap - callout_width)
            callout_y = min(max(top, edge), max(edge, height - callout_height - edge))
        else:
            callout_y = max(edge, min(height - callout_height - edge, top - callout_height - gap))
            callout_x = min(max(left, edge), max(edge, width - callout_width - edge))
        callout_window.geometry(
            f"{int(callout_width)}x{int(max(callout_height, 1))}+"
            f"{int(root_x + callout_x)}+{int(root_y + callout_y)}"
        )
        for widget in self.tutorial_overlay_widgets:
            try:
                widget.lift()
            except tk.TclError:
                pass

    def show_tutorial_page(self):
        if self.tutorial_manual:
            self.show_tutorial_select()
            return
        self.start_tutorial(auto=True, play_mode="自由")

    def show_tutorial_select(self):
        if self.is_spectating():
            return
        self.tutorial_active = False
        self.clear()
        self.play_music("menu")
        self._start_backdrop("lines")
        self._topbar("选择新手教程", self.show_settings)
        frame = tk.Frame(self.container, bg=self.theme_color("base"))
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 28))
        tk.Label(frame, text="选择要重温的玩法", fg="#fff2bd", bg=self.theme_color("base"), font=("Microsoft YaHei UI", 28, "bold")).pack(anchor="w", pady=(18, 8))
        tk.Label(
            frame,
            text="四种教程都会从物理入门题开始，带你走过模式选择、难度选择和真实作答页。",
            fg="#c8d2ee",
            bg=self.theme_color("base"),
            justify="left",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 20))
        cards = tk.Frame(frame, bg=self.theme_color("base"))
        cards.pack(anchor="w", fill="x")
        descriptions = {
            "自由": "单题首字母练习，体验字词提示、词库提示和结算。",
            "限时": "连续限时作答，教程会展示计时和单题作答流程。",
            "线索": "不显示首字母，体验追加线索、词库提示和线索作答。",
            "字谜": "多词交叉填格，体验词条列表、格子提示、词库提示和单词提交。",
        }
        accents = {"自由": "#9ff2b2", "限时": "#f6d36b", "线索": "#7ed6ff", "字谜": "#b7f6ff"}
        for index, play_mode in enumerate(self.TUTORIAL_PLAY_MODES):
            card = tk.Frame(cards, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0, 18), pady=(0, 18))
            cards.grid_columnconfigure(index % 2, weight=1)
            tk.Label(card, text=f"{play_mode}模式", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w", padx=22, pady=(20, 8))
            tk.Label(card, text=self.smart_wrap_text(descriptions[play_mode], 24), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", fill="x", padx=22, pady=(0, 18))
            HoverButton(card, "开始教程", lambda play_mode=play_mode: self.start_tutorial(auto=False, play_mode=play_mode), width=160, height=52, accent=accents[play_mode]).pack(anchor="w", padx=22, pady=(0, 22))
        self.reveal_background_surface(frame)

    def advance_tutorial_page(self):
        if self.tutorial_step == "home":
            self.tutorial_step = "mode"
            self.show_mode_select()
        elif self.tutorial_step == "mode":
            self.tutorial_step = "difficulty"
            self.show_difficulty()
        else:
            self.start_tutorial_round()

    def start_tutorial_round(self):
        self.tutorial_active = True
        self.tutorial_step = "question"
        self.apply_tutorial_mode_selection()
        self.start_game("入门")

    def render_tutorial_banner(self, parent, answer=None):
        if not self.tutorial_active:
            return
        box = tk.Frame(parent, bg="#101827", highlightbackground="#f6d36b", highlightthickness=1)
        box.pack(fill="x", padx=36, pady=(8, 0))
        play_mode = self.tutorial_play_label()
        if play_mode == "线索":
            text = "线索教程：跟着黄色高光操作。教程题会免费体验追加线索和词库提示。"
        elif play_mode == "限时":
            text = "限时教程：跟着黄色高光操作。教程题不会计入正式限时成绩。"
        else:
            text = "新手教程：跟着黄色高光操作。教程题会免费体验一次字词提示和一次词库提示。"
        if answer:
            text += f"  本题答案：{answer}"
        tk.Label(box, text=text, fg="#fff2bd", bg="#101827", justify="left", wraplength=1080, font=("Microsoft YaHei UI", 11, "bold")).pack(side="left", fill="x", expand=True, padx=16, pady=10)
        HoverButton(box, "跳过教程", self.skip_tutorial, width=132, height=44, accent="#ff9b89").pack(side="right", padx=12, pady=7)
        self.apply_static_theme(box)

    def render_tutorial_game_overlay(self):
        if not self.tutorial_active or not self.current:
            return
        answer = self.current.chinese
        play_mode = self.tutorial_play_label()
        if self.tutorial_step == "question":
            self.render_tutorial_overlay(
                self.tutorial_question_panel,
                "先看题面",
                f"这里是真实的{play_mode}作答页。先看题面、难度和规则；教程会带你体验提示与词库提示，再正式输入答案。",
                next_text="试用提示",
                next_command=lambda: self.advance_tutorial_game_step("hint"),
            )
        elif self.tutorial_step == "hint":
            self.render_tutorial_overlay(
                self.tutorial_hint_button,
                "点击提示",
                "线索题会追加下一条线索；首字母题会揭示一个字。教程里免费体验，正式游戏中过多提示会扣分。",
            )
        elif self.tutorial_step == "library":
            self.render_tutorial_overlay(
                self.tutorial_library_hint_button,
                "点击提示词库",
                "本教程题的词库提示也免费。正式游戏里词库提示通常会扣分，用它来缩小范围，但别太依赖。",
            )
        elif self.tutorial_step == "answer":
            self.render_tutorial_overlay(
                [self.answer_entry, self.tutorial_confirm_button],
                "最后输入答案",
                f"现在把“{answer}”填进输入框并点击“确认”。这道教程题不会计入正式 Rating、成就或总积分。",
            )

    def render_crossword_tutorial_overlay(self):
        if not self.tutorial_active or not self.crossword_puzzle:
            return
        placement = self.crossword_selected_placement()
        answer = placement.answer if placement else ""
        if self.tutorial_step == "question":
            target = self.crossword_word_listbox or self.crossword_canvas
            self.render_tutorial_overlay(
                target,
                "先选一个编号",
                "字谜模式左侧列出所有待填词，右侧是交叉格。先看当前高亮编号和它给出的首字母或掩码。",
                next_text="试用提示",
                next_command=lambda: self.advance_tutorial_game_step("hint"),
            )
        elif self.tutorial_step == "hint":
            self.render_tutorial_overlay(
                self.crossword_hint_button,
                "点击格子提示",
                "字谜提示会揭示一个尚未可见的格子。教程中可以先试一次，再看词库提示。",
            )
        elif self.tutorial_step == "library":
            self.render_tutorial_overlay(
                self.crossword_library_hint_button,
                "点击词库提示",
                "词库提示会告诉你某个未完成词属于哪个词库，用来缩小范围。",
            )
        elif self.tutorial_step == "answer":
            self.render_tutorial_overlay(
                [self.answer_entry, self.tutorial_confirm_button],
                "填写当前编号",
                f"现在把“{answer}”填进输入框并点击“确认”。字谜教程只要求你完成这一个词。",
            )

    def advance_tutorial_game_step(self, step):
        if not self.tutorial_active:
            return
        self.tutorial_step = step
        if self.tutorial_play_label() == "字谜":
            self.render_crossword_tutorial_overlay()
        else:
            self.render_tutorial_game_overlay()

    def show_tutorial_complete(self, elapsed, record_path):
        self.clear_tutorial_overlay()
        self.save_tutorial_completed()
        self.tutorial_active = False
        self.tutorial_step = "complete"
        self.play_music("result")
        self.play_sfx("success")
        self.clear()
        self._start_backdrop("constellation")
        frame = tk.Frame(self.container, bg=self.theme_color("base"))
        frame.pack(fill="both", expand=True)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.70, relheight=0.58)
        tk.Label(card, text="新手教程完成", fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(58, 12))
        tk.Label(card, text=f"你完成了一道物理入门{self.tutorial_play_label()}题，用时 {elapsed:.1f} 秒。", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 16, "bold")).pack(pady=5)
        tk.Label(card, text="教程题已保存为只读练习记录，不计入正式 Rating、成就或总积分。", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(pady=5)
        if record_path:
            try:
                record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
            except ValueError:
                record_display = f"record/{record_path.name}"
            tk.Label(card, text=f"教程记录：{record_display}", fg="#7683a3", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(pady=(6, 16))
        HoverButton(card, "回到主页", self.show_home, width=190, height=62, accent="#9ff2b2").pack(pady=(10, 0))
        self.reveal_background_surface(card)

    def show_login(self, allow_cancel=False):
        self.play_music("home")
        self.clear()
        self._start_backdrop("constellation")
        page = self.make_scroll_frame(self.container)
        if allow_cancel and self.switch_return_account:
            back = HoverButton(self.container, "返回", self.cancel_account_switch, width=110, height=48, accent="#8fb6ff")
            back.place(x=22, y=18)
        base_bg = self.theme_color("base")
        shell = tk.Frame(page, bg=base_bg)
        shell.pack(fill="x", padx=32, pady=(10, 34))
        self.draw_home_title(shell, compact=True).pack(pady=(0, 14))
        cards = tk.Frame(shell, bg=base_bg)
        cards.pack()
        stack_cards = scaled_int(1030) > max(self.winfo_width(), int(self.player_settings.get("window_width", 1274))) - 64

        def make_account_card(width, height):
            card = tk.Frame(
                cards,
                bg="#182033",
                highlightbackground="#3b4560",
                highlightthickness=1,
                width=width,
                height=height,
            )
            card.grid_propagate(False)
            content = tk.Frame(card, bg="#182033")
            content.grid(row=0, column=0, sticky="nsew", padx=22, pady=20)
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(0, weight=1)
            return card, content

        login, login_content = make_account_card(max(500, scaled_int(460)), max(390, scaled_int(380)))
        login.grid(row=0, column=0, padx=18, pady=(0, 20), sticky="n")
        tk.Label(login_content, text="登录", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(login_content, text="回到你的词库轨道。", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 16))
        self.login_nickname_var = tk.StringVar(value="")
        self.login_password_var = tk.StringVar(value="")
        login_name_entry = self.account_entry(login_content, "昵称", self.login_nickname_var, padx=0)
        login_password_entry = self.account_entry(login_content, "密码", self.login_password_var, show="*", padx=0)
        login_name_entry.bind("<Return>", lambda _event: login_password_entry.focus_set())
        login_password_entry.bind("<Return>", lambda _event: self.login_current_account())
        HoverButton(login_content, "登录", self.login_current_account, width=250, height=58, accent="#9ff2b2").pack(anchor="w", pady=(16, 0))

        register, register_content = make_account_card(max(520, scaled_int(480)), max(500, scaled_int(480)))
        register_row = 1 if stack_cards else 0
        register_column = 0 if stack_cards else 1
        register.grid(row=register_row, column=register_column, padx=18, pady=(0, 20), sticky="n")
        tk.Label(register_content, text="注册", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(register_content, text="新建账号后会拥有独立 record、成就、段位和设置。", fg="#9ca8c7", bg="#182033", wraplength=380, justify="left", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 16))
        self.register_nickname_var = tk.StringVar(value="")
        self.register_password_var = tk.StringVar(value="")
        self.register_confirm_var = tk.StringVar(value="")
        register_name_entry = self.account_entry(register_content, "昵称", self.register_nickname_var, padx=0)
        register_password_entry = self.account_entry(register_content, "密码", self.register_password_var, show="*", padx=0)
        register_confirm_entry = self.account_entry(register_content, "确认密码", self.register_confirm_var, show="*", padx=0)
        register_name_entry.bind("<Return>", lambda _event: register_password_entry.focus_set())
        register_password_entry.bind("<Return>", lambda _event: register_confirm_entry.focus_set())
        register_confirm_entry.bind("<Return>", lambda _event: self.register_account())
        HoverButton(register_content, "注册并进入", self.register_account, width=250, height=58, accent="#8fb6ff").pack(anchor="w", pady=(16, 0))
        self.reveal_background_surface(shell)
        self.after(80, login_name_entry.focus_set)

    def cancel_account_switch(self):
        account = self.switch_return_account or active_account()
        self.switch_return_account = None
        if account:
            self.activate_account(account)
            return
        self.show_login()

    def account_entry(self, parent, label, variable, show=None, padx=22):
        tk.Label(parent, text=label, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", padx=padx, pady=(8, 4))
        entry = tk.Entry(
            parent,
            textvariable=variable,
            show=show or "",
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        entry.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        entry.pack(fill="x", padx=padx, ipady=7)
        return entry

    def login_current_account(self):
        try:
            account = authenticate(self.login_nickname_var.get(), self.login_password_var.get())
        except AccountError as exc:
            messagebox.showerror("登录失败", str(exc))
            return
        self.activate_account(account)

    def register_account(self):
        nickname = self.register_nickname_var.get()
        password = self.register_password_var.get()
        confirm = self.register_confirm_var.get()
        if password != confirm:
            messagebox.showerror("注册失败", "两次输入的密码不一致。")
            return
        try:
            account = create_account(nickname, password)
            set_active_session(account["id"])
        except AccountError as exc:
            messagebox.showerror("注册失败", str(exc))
            return
        apply_account_context(account["id"])
        settings = dict(DEFAULT_PLAYER_SETTINGS)
        settings["nickname"] = account["nickname"]
        settings["tutorial_completed"] = False
        save_player_settings(settings)
        self.activate_account(account)

    def logout_account(self):
        if self.is_spectating():
            self.exit_spectator_mode()
            return
        clear_active_session()
        self.switch_return_account = None
        self.current_account = None
        self.player_settings = dict(DEFAULT_PLAYER_SETTINGS)
        self.apply_backdrop_theme()
        self.apply_audio_settings()
        self.show_login()

    def switch_account(self):
        if self.is_spectating():
            self.exit_spectator_mode()
            return
        self.spectator_admin_account = None
        self.spectated_account = None
        self.tutorial_active = False
        self.tutorial_manual = False
        self.tutorial_step = 0
        self.switch_return_account = self.current_account
        self.current_account = None
        self.player_settings = dict(DEFAULT_PLAYER_SETTINGS)
        self.apply_backdrop_theme()
        self.apply_audio_settings()
        self.show_login(allow_cancel=True)

    def show_change_password(self):
        if self.block_spectator_action("修改密码"):
            return
        if not self.current_account:
            self.show_login()
            return
        popup = tk.Toplevel(self)
        popup.title("修改密码")
        popup.configure(bg="#111725")
        popup.geometry("440x370")
        popup.minsize(420, 350)
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        panel = tk.Frame(popup, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(panel, text="修改密码", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w", padx=22, pady=(18, 10))
        old_var = tk.StringVar()
        new_var = tk.StringVar()
        confirm_var = tk.StringVar()
        self.account_entry(panel, "原密码", old_var, show="*")
        self.account_entry(panel, "新密码", new_var, show="*")
        self.account_entry(panel, "确认新密码", confirm_var, show="*")
        row = tk.Frame(panel, bg="#182033")
        row.pack(anchor="w", padx=22, pady=(16, 22))

        def submit():
            if new_var.get() != confirm_var.get():
                messagebox.showerror("修改失败", "两次输入的新密码不一致。", parent=popup)
                return
            try:
                change_password(self.current_account["id"], old_var.get(), new_var.get())
            except AccountError as exc:
                messagebox.showerror("修改失败", str(exc), parent=popup)
                return
            popup.destroy()
            messagebox.showinfo("修改成功", "密码已更新。")

        HoverButton(row, "确认修改", submit, width=150, height=52, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 10))
        HoverButton(row, "取消", popup.destroy, width=120, height=52, accent="#ff9b89").grid(row=0, column=1)
        self.apply_static_theme(popup)
