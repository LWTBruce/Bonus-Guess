from ._shared import *


class SettingsMixin:
    def show_game_mechanics_page(self, tab):
        self.play_music("archive")
        self.mechanics_tab = tab
        self.clear()
        title = "快速上手" if tab == "quick" else "详细规则"
        self._topbar(title, self.show_game_mechanics)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        self._start_backdrop("grid", frame)

        shell = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        shell.pack(fill="both", expand=True)
        try:
            content = GAME_MECHANICS_FILE.read_text(encoding="utf-8")
        except Exception:
            content = "暂时找不到 docs/game_mechanics.md。"
        quick, detail = split_mechanics_sections(content)
        render_markdown(shell, quick if tab == "quick" else detail, mode=tab)

    def show_settings(self):
        self.play_music("settings")
        self.clear()
        self._topbar("玩家档案（旁观）" if self.is_spectating() else "设置", self.show_home)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        self._start_backdrop("particles", frame)

        achievements_data = read_achievements()
        summary = load_record_summary(achievements_data=achievements_data)
        rank_progress = read_rank_progress()
        rating_value = summary["rating"]
        reveal_all = self.admin_reveal_hidden_enabled()
        self.available_avatar_ids = unlocked_avatar_ids(rating_value, reveal_all=reveal_all)
        self.available_title_options = unlocked_title_options(rating_value, achievements_data, rank_progress)
        self.available_home_music_ids = unlocked_home_music_ids(rating_value, reveal_all=reveal_all)
        current_avatar_id = coerce_avatar_id(self.player_settings.get("avatar_id", 0), rating_value, reveal_all=reveal_all)
        current_title_id = coerce_title_id(self.player_settings.get("title_id"), rating_value, achievements_data, rank_progress)
        current_title_category = self.title_category_for_title_id(current_title_id)
        current_rank_badge_id = coerce_rank_badge_id(self.player_settings.get("rank_badge_id", ""), rank_progress)
        current_home_music_id = coerce_home_music_id(
            self.player_settings.get("home_music_id"),
            rating_value,
            reveal_all=reveal_all,
        )
        shell = self.make_scroll_frame(frame, bg="#111725")
        left = tk.Frame(shell, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right = tk.Frame(shell, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        right.pack(side="right", fill="both", expand=True, padx=(14, 0))

        tk.Label(left, text="玩家档案", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", padx=28, pady=(26, 14))
        profile_row = tk.Frame(left, bg="#182033")
        profile_row.pack(fill="x", padx=28, pady=(0, 16))
        self.avatar_preview_canvas = tk.Canvas(profile_row, width=86, height=86, bg="#182033", bd=0, highlightthickness=0)
        self.avatar_preview_canvas.pack(side="left", padx=(0, 18))
        draw_avatar(self.avatar_preview_canvas, current_avatar_id, 86, selected=True)

        form = tk.Frame(profile_row, bg="#182033")
        form.pack(side="left", fill="x", expand=True)
        tk.Label(form, text="昵称", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
        self.settings_nickname_var = tk.StringVar(value=self.player_settings.get("nickname", "PHOer"))
        entry = tk.Entry(
            form,
            textvariable=self.settings_nickname_var,
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        entry.pack(fill="x", ipady=8, pady=(7, 10))
        if self.is_spectating():
            entry.configure(state="disabled", disabledforeground="#fff8dc", disabledbackground="#101827")
        tk.Label(form, text=f"当前 Rating {format_rating(rating_value)}", fg="#9ff2b2", bg="#182033", font=("Consolas", 14, "bold")).pack(anchor="w")
        rating_detail = f"作答 {format_rating(summary['play_rating'])}  +  成就 {summary['achievement_bonus']:.3f}"
        tk.Label(form, text=rating_detail, fg="#9ca8c7", bg="#182033", font=("Consolas", 10, "bold")).pack(anchor="w", pady=(3, 0))
        tk.Label(form, text=f"当前称号：{title_name(current_title_id)}", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(4, 0))

        tk.Label(left, text="头像", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(4, 8))
        avatar_grid = tk.Frame(left, bg="#182033")
        avatar_grid.pack(padx=24, pady=(0, 12))
        avatar_option_size = scaled_int(70)
        self.settings_avatar_var = tk.IntVar(value=current_avatar_id)
        self.avatar_option_canvases = []
        self.avatar_option_labels = []
        for index, avatar in enumerate(AVATARS):
            cell = tk.Frame(avatar_grid, bg="#182033")
            cell.grid(row=index // 5, column=index % 5, padx=8, pady=8)
            canvas = tk.Canvas(cell, width=avatar_option_size, height=avatar_option_size, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
            canvas.pack()
            canvas.bind("<Button-1>", lambda _event, avatar_id=index: self.select_avatar(avatar_id))
            label = tk.Label(cell, text=avatar["name"], fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 9))
            label.pack(pady=(2, 0))
            self.avatar_option_canvases.append(canvas)
            self.avatar_option_labels.append(label)
        self.refresh_avatar_choices()

        tk.Label(left, text="称号", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(2, 8))
        self.settings_title_var = tk.StringVar(value=current_title_id)
        self.settings_title_category_var = tk.StringVar(value=current_title_category)
        self.settings_title_search_var = tk.StringVar(value="")
        title_panel = tk.Frame(left, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
        title_panel.pack(fill="x", padx=26, pady=(0, 18))
        self.settings_title_current_label = tk.Label(
            title_panel,
            text=f"当前佩戴：{title_name(current_title_id)}",
            fg="#fff2bd",
            bg="#111827",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        self.settings_title_current_label.pack(anchor="w", padx=14, pady=(12, 6))
        search_row = tk.Frame(title_panel, bg="#111827")
        search_row.pack(fill="x", padx=14, pady=(0, 10))
        tk.Label(search_row, text="搜索", fg="#8fb6ff", bg="#111827", font=("Microsoft YaHei UI", 10, "bold")).pack(side="left", padx=(0, 8))
        title_search = tk.Entry(
            search_row,
            textvariable=self.settings_title_search_var,
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        title_search.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        title_search.pack(side="left", fill="x", expand=True, ipady=5)
        self.settings_title_search_var.trace_add("write", lambda *_args: self.render_settings_title_options())
        title_category_grid = tk.Frame(title_panel, bg="#111827")
        title_category_grid.pack(fill="x", padx=14, pady=(0, 10))
        title_categories = self.available_title_categories()
        if current_title_category not in title_categories:
            self.settings_title_category_var.set("全部")
        for index, category in enumerate(title_categories):
            rb = tk.Radiobutton(
                title_category_grid,
                text=f"{category} {self.title_category_count(category)}",
                value=category,
                variable=self.settings_title_category_var,
                command=self.render_settings_title_options,
                fg="#c8d2ee",
                bg="#111827",
                activeforeground="#fff2bd",
                activebackground="#20283a",
                selectcolor="#101827",
                font=("Microsoft YaHei UI", 10, "bold"),
                anchor="w",
                indicatoron=False,
                relief="flat",
                padx=8,
                pady=4,
            )
            rb.grid(row=index // 3, column=index % 3, sticky="ew", padx=(0, 8), pady=3)
        for column in range(3):
            title_category_grid.grid_columnconfigure(column, weight=1, uniform="title_category")
        self.settings_title_options_frame = tk.Frame(title_panel, bg="#111827")
        self.settings_title_options_frame.pack(fill="x", padx=14, pady=(0, 14))
        self.render_settings_title_options()

        tk.Label(left, text="段位标识", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(0, 8))
        badge_grid = tk.Frame(left, bg="#182033")
        badge_grid.pack(fill="x", padx=26, pady=(0, 16))
        rank_badge_width = scaled_int(220)
        rank_badge_height = scaled_int(34)
        self.rank_badge_var = tk.StringVar(value=current_rank_badge_id)
        self.rank_badge_canvases = []
        no_badge = tk.Radiobutton(
            badge_grid,
            text="不佩戴段位标识",
            value="",
            variable=self.rank_badge_var,
            fg="#dce6ff",
            bg="#182033",
            activeforeground="#fff2bd",
            activebackground="#182033",
            selectcolor="#101827",
            font=("Microsoft YaHei UI", 10, "bold"),
            anchor="w",
        )
        no_badge.grid(row=0, column=0, sticky="w", padx=(0, 12), pady=4)
        unlocked_badges = [(badge_id, rank_badge_name(badge_id)) for badge_id, _name in unlocked_rank_badges(rank_progress)]
        for index, (badge_id, _name) in enumerate(unlocked_badges, 1):
            cell = tk.Frame(badge_grid, bg="#182033")
            cell.grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 12), pady=4)
            radio = tk.Radiobutton(
                cell,
                text="",
                value=badge_id,
                variable=self.rank_badge_var,
                bg="#182033",
                activebackground="#182033",
                selectcolor="#101827",
            )
            radio.pack(side="left")
            canvas = tk.Canvas(cell, width=rank_badge_width, height=rank_badge_height, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
            canvas.pack(side="left")
            draw_rank_badge(canvas, badge_id, rank_badge_width, rank_badge_height, selected=badge_id == current_rank_badge_id)
            canvas.bind("<Button-1>", lambda _event, value=badge_id: self.select_rank_badge(value))
            self.rank_badge_canvases.append((canvas, badge_id))
        if not unlocked_badges:
            tk.Label(badge_grid, text="通过限时段位、线索段位或字谜段位后解锁。", fg="#64708f", bg="#182033", font=("Microsoft YaHei UI", 10)).grid(row=1, column=0, sticky="w", pady=3)

        tk.Label(right, text="显示与背景", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", padx=28, pady=(26, 14))
        self.settings_speed_var = tk.DoubleVar(value=float(self.player_settings.get("backdrop_speed", 1.0)))
        self.settings_density_var = tk.DoubleVar(value=float(self.player_settings.get("backdrop_density", 1.0)))
        self.settings_opacity_var = tk.DoubleVar(value=float(self.player_settings.get("backdrop_opacity", 1.0)))
        self.settings_font_scale_var = tk.DoubleVar(value=float(self.player_settings.get("font_scale", 1.0)))
        self.settings_music_volume_var = tk.DoubleVar(value=float(self.player_settings.get("music_volume", 0.55)))
        self.settings_sfx_volume_var = tk.DoubleVar(value=float(self.player_settings.get("sfx_volume", 0.75)))
        self.settings_home_music_var = tk.StringVar(value=current_home_music_id)
        current_sfx_choices = normalize_sfx_choices(self.player_settings.get("sfx_choices"))
        self.settings_sfx_choice_vars = {
            event_id: tk.StringVar(value=sfx_sound_display(current_sfx_choices[event_id]))
            for event_id, _label in SFX_EVENT_OPTIONS
        }
        self.settings_transitions_var = tk.BooleanVar(value=bool(self.player_settings.get("transitions_enabled", True)))
        self.settings_window_width_var = tk.StringVar(value=str(int(self.player_settings.get("window_width", 1274))))
        self.settings_window_height_var = tk.StringVar(value=str(int(self.player_settings.get("window_height", 806))))
        self.settings_admin_reveal_hidden_var = None
        self.settings_speed_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_density_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_opacity_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_font_scale_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_music_volume_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_sfx_volume_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_speed_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(right, self.settings_speed_var, self.update_setting_labels).pack(fill="x", padx=24, pady=(0, 18))
        self.settings_density_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(right, self.settings_density_var, self.update_setting_labels).pack(fill="x", padx=24, pady=(0, 18))
        self.settings_opacity_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(
            right,
            self.settings_opacity_var,
            self.update_setting_labels,
            from_=0.0,
            to=1.0,
            resolution=0.05,
        ).pack(fill="x", padx=24, pady=(0, 18))
        self.settings_font_scale_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(
            right,
            self.settings_font_scale_var,
            self.update_setting_labels,
            from_=0.8,
            to=2.0,
            resolution=0.05,
        ).pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(right, text="音乐与音效", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", padx=28, pady=(16, 14))
        self.settings_music_volume_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(
            right,
            self.settings_music_volume_var,
            self.update_setting_labels,
            from_=0.0,
            to=1.0,
            resolution=0.05,
        ).pack(fill="x", padx=24, pady=(0, 18))
        self.settings_sfx_volume_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(
            right,
            self.settings_sfx_volume_var,
            self.update_setting_labels,
            from_=0.0,
            to=1.0,
            resolution=0.05,
        ).pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(right, text="按键音效", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(2, 8))
        self.settings_sfx_options_frame = tk.Frame(right, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
        self.settings_sfx_options_frame.pack(fill="x", padx=26, pady=(0, 14))
        self.render_sfx_choice_options()
        tk.Label(right, text="主界面背景音乐", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(2, 8))
        self.settings_music_options_frame = tk.Frame(right, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
        self.settings_music_options_frame.pack(fill="x", padx=26, pady=(0, 14))
        self.render_home_music_options()
        tk.Label(right, text="默认窗口大小（像素）", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(2, 8))
        window_row = tk.Frame(right, bg="#182033")
        window_row.pack(anchor="w", padx=24, pady=(0, 14))
        self.make_pixel_entry(window_row, self.settings_window_width_var, 92).grid(row=0, column=0)
        tk.Label(window_row, text=" × ", fg="#9ca8c7", bg="#182033", font=("Consolas", 14, "bold")).grid(row=0, column=1, padx=4)
        self.make_pixel_entry(window_row, self.settings_window_height_var, 92).grid(row=0, column=2)
        tk.Label(window_row, text="  保存后生效", fg="#64708f", bg="#182033", font=("Microsoft YaHei UI", 10)).grid(row=0, column=3, padx=(10, 0))
        tk.Checkbutton(
            right,
            text="启用页面过场和字谜加载动画",
            variable=self.settings_transitions_var,
            fg="#c8d2ee",
            bg="#182033",
            activeforeground="#fff2bd",
            activebackground="#182033",
            selectcolor="#101827",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", padx=24, pady=(0, 18))
        if is_admin_account(self.current_account) and not self.is_spectating():
            self.settings_admin_reveal_hidden_var = tk.BooleanVar(value=bool(self.player_settings.get("admin_reveal_hidden", False)))
            tk.Checkbutton(
                right,
                text="打开所有隐藏",
                variable=self.settings_admin_reveal_hidden_var,
                command=self.refresh_admin_reveal_settings_choices,
                fg="#f6d36b",
                bg="#182033",
                activeforeground="#fff2bd",
                activebackground="#182033",
                selectcolor="#101827",
                font=("Microsoft YaHei UI", 12, "bold"),
            ).pack(anchor="w", padx=24, pady=(0, 8))
            tk.Label(
                right,
                text=self.smart_wrap_text("管理员专用：显示隐藏成就提示，临时开放锁定段位、头像和主页音乐。关闭后恢复普通显示，已经保存的段位成绩仍会保留。", 27),
                fg="#9ca8c7",
                bg="#182033",
                justify="left",
                font=("Microsoft YaHei UI", 10),
            ).pack(anchor="w", padx=28, pady=(0, 18))
        self.update_setting_labels()

        tk.Label(
            right,
            text=self.smart_wrap_text("速度、密度和透明度会影响所有动态背景。音乐和音效音量会实时预览，保存后随账号保留；字号会影响后续打开的页面，保存后生效。", 27),
            fg="#9ca8c7",
            bg="#182033",
            justify="left",
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", padx=28, pady=(0, 26))
        buttons = tk.Frame(right, bg="#182033")
        buttons.pack(anchor="w", padx=28, pady=(0, 22))
        if self.is_spectating():
            tk.Label(
                buttons,
                text="旁观模式为只读：不能保存设置、改密码或切换此玩家账号。",
                fg="#f6d36b",
                bg="#182033",
                justify="left",
                font=("Microsoft YaHei UI", 11, "bold"),
            ).grid(row=0, column=0, sticky="w")
        else:
            HoverButton(buttons, "保存设置", self.save_settings, width=170, height=58, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 12))
            HoverButton(buttons, "恢复默认", self.reset_settings, width=170, height=58, accent="#ff9b89").grid(row=0, column=1, padx=12)

        account_box = tk.Frame(right, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
        account_box.pack(fill="x", padx=28, pady=(0, 26))
        tk.Label(account_box, text="账号", fg="#8fb6ff", bg="#111827", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        account_text = "未登录"
        if self.current_account:
            account_text = f"{self.current_account.get('nickname', '')}  /  {self.current_account.get('id', '')}"
            if is_admin_account(self.current_account):
                account_text += "  /  管理员"
            if self.is_spectating():
                account_text = f"正在旁观：{account_text}"
        tk.Label(account_box, text=account_text, fg="#dce6ff", bg="#111827", wraplength=420, justify="left", font=("Consolas", 11, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        account_buttons = tk.Frame(account_box, bg="#111827")
        account_buttons.pack(anchor="w", padx=16, pady=(0, 16))
        if self.is_spectating():
            HoverButton(account_buttons, "退出旁观", self.exit_spectator_mode, width=132, height=48, accent="#ff9b89").grid(row=0, column=0, padx=(0, 8), pady=4)
            HoverButton(account_buttons, "历史记录", self.show_history, width=132, height=48, accent="#8fb6ff").grid(row=0, column=1, padx=8, pady=4)
        else:
            HoverButton(account_buttons, "修改密码", self.show_change_password, width=132, height=48, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 8), pady=4)
            HoverButton(account_buttons, "切换账号", self.switch_account, width=132, height=48, accent="#8fb6ff").grid(row=0, column=1, padx=8, pady=4)
            HoverButton(account_buttons, "退出登录", self.logout_account, width=132, height=48, accent="#ff9b89").grid(row=0, column=2, padx=8, pady=4)
            HoverButton(account_buttons, "重温教程", lambda: self.start_tutorial(auto=False), width=132, height=48, accent="#7fd9c6").grid(row=1, column=0, padx=(0, 8), pady=4)
            if is_admin_account(self.current_account):
                HoverButton(account_buttons, "后台数据", self.show_admin_dashboard, width=132, height=48, accent="#f6d36b").grid(row=1, column=1, padx=8, pady=4)
                HoverButton(account_buttons, "查看建议", self.show_feedback_admin, width=132, height=48, accent="#ffcf8f").grid(row=1, column=2, padx=8, pady=4)

    def make_setting_scale(self, parent, variable, command, from_=0.4, to=10.0, resolution=0.1):
        scale = tk.Scale(
            parent,
            from_=from_,
            to=to,
            resolution=resolution,
            orient="horizontal",
            variable=variable,
            command=lambda _value: command(),
            bg="#182033",
            fg="#c8d2ee",
            troughcolor="#101827",
            activebackground="#8fb6ff",
            highlightthickness=0,
            length=420,
            font=("Consolas", 10, "bold"),
        )
        return scale

    def make_pixel_entry(self, parent, variable, _width):
        entry = tk.Entry(
            parent,
            textvariable=variable,
            width=7,
            justify="center",
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Consolas", 13, "bold"),
        )
        entry.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        return entry

    def update_setting_labels(self):
        if hasattr(self, "settings_speed_label"):
            self.settings_speed_label.config(text=f"背景速度  {self.settings_speed_var.get():.1f}x")
        if hasattr(self, "settings_density_label"):
            self.settings_density_label.config(text=f"背景密度  {self.settings_density_var.get():.1f}x")
        if hasattr(self, "settings_opacity_label"):
            self.settings_opacity_label.config(text=f"粒子透明度  {self.settings_opacity_var.get() * 100:.0f}%")
        if hasattr(self, "settings_font_scale_label"):
            self.settings_font_scale_label.config(text=f"界面字号  {self.settings_font_scale_var.get() * 100:.0f}%")
        if hasattr(self, "settings_music_volume_label"):
            self.settings_music_volume_label.config(text=f"背景音乐  {self.settings_music_volume_var.get() * 100:.0f}%")
        if hasattr(self, "settings_sfx_volume_label"):
            self.settings_sfx_volume_label.config(text=f"按钮音效  {self.settings_sfx_volume_var.get() * 100:.0f}%")
        if getattr(self, "audio", None):
            self.audio.set_volumes(self.settings_music_volume_var.get(), self.settings_sfx_volume_var.get())

    def title_category_for_option(self, option):
        title_id, _title_text, source = option
        if str(title_id or "").startswith("rank_title:"):
            badge_id = str(title_id).split(":", 1)[1]
            subject_key, _rank_id = parse_rank_badge_id(badge_id)
            _subject, rank_kind = split_rank_progress_key(subject_key)
            return rank_kind_label(rank_kind)
        source_text = str(source or "")
        if source_text.startswith("Rating"):
            return "Rating"
        if source_text == "成就":
            return "成就"
        return source_text or "其他"

    def title_category_for_title_id(self, title_id):
        for option in self.available_title_options:
            if option[0] == title_id:
                return self.title_category_for_option(option)
        return "全部"

    def available_title_categories(self):
        order = [
            "全部",
            "Rating",
            "通用入门",
            "自由与常规",
            "线索与高难",
            "提示与词库",
            "掩码首字母",
            "限时模式",
            "随机模式",
            "字谜模式",
            "长期积累",
            "系统与退出",
            "段位挑战",
            "限时段位",
            "线索段位",
            "字谜段位",
            "旧限时段位",
        ]
        present = {self.title_category_for_option(option) for option in self.available_title_options}
        categories = ["全部"]
        categories.extend(category for category in order[1:] if category in present)
        categories.extend(sorted(category for category in present if category not in set(order)))
        return categories

    def title_category_count(self, category):
        return f"({len(self.filtered_title_options(category))})"

    def filtered_title_options(self, category=None):
        category = category or (self.settings_title_category_var.get() if self.settings_title_category_var else "全部")
        if category == "全部":
            options = list(self.available_title_options)
        else:
            options = [
                option for option in self.available_title_options
                if self.title_category_for_option(option) == category
            ]
        query = ""
        if self.settings_title_search_var:
            query = self.settings_title_search_var.get().strip().casefold()
        if not query:
            return options
        return [
            option for option in options
            if query in option[1].casefold() or query in option[2].casefold() or query in str(option[0]).casefold()
        ]

    def render_settings_title_options(self):
        frame = self.settings_title_options_frame
        if not frame or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            child.destroy()
        self.settings_title_cards = []
        for column in range(2):
            frame.grid_columnconfigure(column, weight=1)
        options = self.filtered_title_options()
        if not options:
            tk.Label(frame, text="没有匹配的称号", fg="#64708f", bg="#111827", font=("Microsoft YaHei UI", 10)).grid(row=0, column=0, sticky="w", pady=8)
            return
        visible_ids = {option[0] for option in options}
        current_id = self.settings_title_var.get() if self.settings_title_var else ""
        if current_id and current_id not in visible_ids:
            current_name = title_name(current_id)
            tk.Label(
                frame,
                text=f"当前佩戴：{current_name}（在其他分类）",
                fg="#8fb6ff",
                bg="#111827",
                font=("Microsoft YaHei UI", 10, "bold"),
            ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
            offset = 1
        else:
            offset = 0
        for index, (title_id, title_text, source) in enumerate(options):
            selected = title_id == current_id
            card = tk.Frame(
                frame,
                bg="#20283a" if selected else "#151d2c",
                highlightbackground="#f6d36b" if selected else "#30384e",
                highlightthickness=1,
                cursor="hand2",
            )
            card.grid(row=offset + index // 2, column=index % 2, sticky="ew", padx=(0, 10), pady=5)
            marker = tk.Label(
                card,
                text="●" if selected else "○",
                fg="#f6d36b" if selected else "#64708f",
                bg=card["bg"],
                font=("Microsoft YaHei UI", 11, "bold"),
                cursor="hand2",
            )
            marker.pack(side="left", padx=(10, 6), pady=10)
            text_box = tk.Frame(card, bg=card["bg"], cursor="hand2")
            text_box.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)
            title_label = tk.Label(text_box, text=title_text, fg="#fff2bd" if selected else "#dce6ff", bg=card["bg"], anchor="w", font=("Microsoft YaHei UI", 10, "bold"), cursor="hand2")
            title_label.pack(anchor="w", fill="x")
            source_label = tk.Label(text_box, text=source, fg="#8fb6ff", bg=card["bg"], anchor="w", font=("Microsoft YaHei UI", 9, "bold"), cursor="hand2")
            source_label.pack(anchor="w", fill="x", pady=(2, 0))
            for widget in (card, marker, text_box, title_label, source_label):
                widget.bind("<Button-1>", lambda _event, value=title_id: self.select_title(value))
            self.settings_title_cards.append((card, title_id))

    def render_sfx_choice_options(self):
        frame = self.settings_sfx_options_frame
        if not frame or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            child.destroy()
        options = sfx_sound_display_options()
        for column in range(2):
            frame.grid_columnconfigure(column, weight=1, uniform="sfx_choice")
        for index, (event_id, event_label) in enumerate(SFX_EVENT_OPTIONS):
            row = tk.Frame(frame, bg="#151d2c", highlightbackground="#30384e", highlightthickness=1)
            row.grid(row=index // 2, column=index % 2, sticky="ew", padx=8, pady=7)
            row.grid_columnconfigure(1, weight=1)
            tk.Label(
                row,
                text=event_label,
                fg="#dce6ff",
                bg="#151d2c",
                anchor="w",
                font=("Microsoft YaHei UI", 9, "bold"),
            ).grid(row=0, column=0, sticky="w", padx=(10, 8), pady=9)
            variable = self.settings_sfx_choice_vars[event_id]
            menu = tk.OptionMenu(
                row,
                variable,
                *options,
                command=lambda _value, value=event_id: self.preview_selected_sfx(value),
            )
            menu.configure(
                fg="#fff8dc",
                bg="#101827",
                activeforeground="#fff2bd",
                activebackground="#20283a",
                highlightthickness=1,
                highlightbackground="#30384e",
                relief="flat",
                font=("Microsoft YaHei UI", 9, "bold"),
                width=13,
            )
            try:
                menu["menu"].configure(
                    fg="#dce6ff",
                    bg="#101827",
                    activeforeground="#fff2bd",
                    activebackground="#20283a",
                    font=("Microsoft YaHei UI", 9, "bold"),
                )
            except tk.TclError:
                pass
            menu.grid(row=0, column=1, sticky="ew", pady=7)
            preview = tk.Label(
                row,
                text="试听",
                fg="#8fb6ff",
                bg="#151d2c",
                cursor="hand2",
                font=("Microsoft YaHei UI", 9, "bold underline"),
            )
            preview.grid(row=0, column=2, sticky="e", padx=(8, 10), pady=9)
            preview.bind("<Button-1>", lambda _event, value=event_id: self.preview_selected_sfx(value))
            preview.bind("<Enter>", lambda _event, widget=preview: widget.configure(fg="#fff2bd"))
            preview.bind("<Leave>", lambda _event, widget=preview: widget.configure(fg="#8fb6ff"))

    def preview_selected_sfx(self, event_id):
        if event_id not in self.settings_sfx_choice_vars:
            return
        sound_id = sfx_sound_id_from_display(self.settings_sfx_choice_vars[event_id].get())
        self.preview_sfx_choice(sound_id)

    def selected_sfx_choices_from_settings(self):
        choices = {}
        for event_id, _label in SFX_EVENT_OPTIONS:
            variable = self.settings_sfx_choice_vars.get(event_id)
            choices[event_id] = sfx_sound_id_from_display(variable.get() if variable else event_id)
        return normalize_sfx_choices(choices)

    def render_home_music_options(self):
        frame = self.settings_music_options_frame
        if not frame or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            child.destroy()
        self.settings_music_cards = []
        for column in range(2):
            frame.grid_columnconfigure(column, weight=1, uniform="home_music")
        current_id = self.settings_home_music_var.get() if self.settings_home_music_var else ""
        if self.settings_admin_reveal_hidden_var and is_admin_account(self.current_account):
            reveal_all = bool(self.settings_admin_reveal_hidden_var.get())
        else:
            reveal_all = self.admin_reveal_hidden_enabled()
        for index, option in enumerate(HOME_MUSIC_OPTIONS):
            music_id = option["id"]
            selected = music_id == current_id
            unlocked = music_id in self.available_home_music_ids
            bg = "#20283a" if selected else ("#151d2c" if unlocked else "#121827")
            border = "#f6d36b" if selected else ("#30384e" if unlocked else "#252d40")
            card = tk.Frame(frame, bg=bg, highlightbackground=border, highlightthickness=1, cursor="hand2" if unlocked else "arrow")
            card.grid(row=index // 2, column=index % 2, sticky="ew", padx=8, pady=7)
            marker = tk.Label(
                card,
                text="●" if selected else ("○" if unlocked else "锁"),
                fg="#f6d36b" if selected else ("#64708f" if unlocked else "#7f8caf"),
                bg=bg,
                font=("Microsoft YaHei UI", 11, "bold"),
                cursor="hand2" if unlocked else "arrow",
            )
            marker.pack(side="left", padx=(10, 7), pady=10)
            text_box = tk.Frame(card, bg=bg, cursor="hand2" if unlocked else "arrow")
            text_box.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)
            title_color = "#fff2bd" if unlocked else "#8d96ad"
            tk.Label(
                text_box,
                text=option["title"],
                fg=title_color,
                bg=bg,
                anchor="w",
                justify="left",
                wraplength=180,
                font=("Microsoft YaHei UI", 10, "bold"),
                cursor="hand2" if unlocked else "arrow",
            ).pack(anchor="w", fill="x")
            tk.Label(
                text_box,
                text=option["author"],
                fg="#8fb6ff" if unlocked else "#64708f",
                bg=bg,
                anchor="w",
                justify="left",
                wraplength=180,
                font=("Microsoft YaHei UI", 9, "bold"),
                cursor="hand2" if unlocked else "arrow",
            ).pack(anchor="w", fill="x", pady=(2, 0))
            unlock_label = self.home_music_unlock_label(option, unlocked, reveal_all)
            tk.Label(
                text_box,
                text=unlock_label,
                fg="#9ff2b2" if unlocked else "#69738d",
                bg=bg,
                anchor="w",
                font=("Microsoft YaHei UI", 8, "bold"),
                cursor="hand2" if unlocked else "arrow",
            ).pack(anchor="w", fill="x", pady=(2, 0))
            if unlocked:
                for widget in (card, marker, text_box, *text_box.winfo_children()):
                    widget.bind("<Button-1>", lambda _event, value=music_id: self.select_home_music(value))
            self.settings_music_cards.append((card, music_id))

    def home_music_unlock_label(self, option, unlocked, reveal_all=False):
        threshold = float(option.get("unlock_rating") or 0.0)
        if reveal_all and threshold > 0:
            return f"管理员开启 / 原需 R{threshold:g}"
        if threshold <= 0:
            return "默认可用"
        return f"Rating {threshold:g}" if unlocked else f"需 Rating {threshold:g}"

    def select_home_music(self, music_id):
        if music_id not in self.available_home_music_ids:
            option = home_music_option(music_id)
            threshold = float(option.get("unlock_rating") or 0.0)
            messagebox.showinfo("尚未解锁", f"这首音乐需要 Rating {threshold:g}。")
            return
        if self.settings_home_music_var:
            self.settings_home_music_var.set(music_id)
        self.render_home_music_options()
        self.preview_home_music(music_id)

    def refresh_admin_reveal_settings_choices(self):
        if not is_admin_account(self.current_account):
            return
        achievements_data = read_achievements()
        summary = load_record_summary(achievements_data=achievements_data)
        reveal_all = bool(self.settings_admin_reveal_hidden_var and self.settings_admin_reveal_hidden_var.get())
        self.available_avatar_ids = unlocked_avatar_ids(summary["rating"], reveal_all=reveal_all)
        self.available_home_music_ids = unlocked_home_music_ids(summary["rating"], reveal_all=reveal_all)
        if self.settings_avatar_var and int(self.settings_avatar_var.get()) not in self.available_avatar_ids:
            self.settings_avatar_var.set(0)
        if self.settings_home_music_var and self.settings_home_music_var.get() not in self.available_home_music_ids:
            self.settings_home_music_var.set(DEFAULT_PLAYER_SETTINGS["home_music_id"])
        self.refresh_avatar_choices()
        self.render_home_music_options()

    def select_title(self, title_id):
        if self.settings_title_var:
            self.settings_title_var.set(title_id)
        if self.settings_title_current_label and self.settings_title_current_label.winfo_exists():
            self.settings_title_current_label.config(text=f"当前佩戴：{title_name(title_id)}")
        self.render_settings_title_options()

    def select_avatar(self, avatar_id):
        if avatar_id not in self.available_avatar_ids:
            messagebox.showinfo("尚未解锁", "这个头像需要更高 Rating。")
            return
        self.settings_avatar_var.set(avatar_id)
        if self.avatar_preview_canvas:
            draw_avatar(self.avatar_preview_canvas, avatar_id, 86, selected=True)
        self.refresh_avatar_choices()

    def refresh_avatar_choices(self):
        current = int(self.settings_avatar_var.get())
        for index, canvas in enumerate(self.avatar_option_canvases):
            size = int(canvas.cget("width"))
            draw_avatar(canvas, index, size, selected=index == current)
            locked = index not in self.available_avatar_ids
            if locked:
                pad = max(3, int(size * 0.06))
                canvas.create_rectangle(pad, pad, size - pad, size - pad, fill="#111725", stipple="gray50", outline="#3b4560")
                canvas.create_text(size / 2, size / 2, text="锁", fill="#9ca8c7", font=("Microsoft YaHei UI", 15, "bold"))
            canvas.configure(cursor="hand2" if not locked else "arrow")
            if index < len(self.avatar_option_labels):
                unlock_text = self.avatar_unlock_label(index)
                label = self.avatar_option_labels[index]
                label.config(
                    text=unlock_text,
                    fg="#9ca8c7" if not locked else "#64708f",
                )

    def avatar_unlock_label(self, avatar_id):
        for threshold, _reward_id, _title, reward_avatar_id in RATING_REWARDS:
            if reward_avatar_id == avatar_id:
                if threshold <= 0:
                    return AVATARS[avatar_id]["name"]
                return f"{AVATARS[avatar_id]['name']}  R{threshold:g}"
        return AVATARS[avatar_id]["name"]

    def select_rank_badge(self, badge_id):
        if self.rank_badge_var:
            self.rank_badge_var.set(badge_id)
        for canvas, item_id in self.rank_badge_canvases:
            width = int(canvas.cget("width"))
            height = int(canvas.cget("height"))
            draw_rank_badge(canvas, item_id, width, height, selected=item_id == badge_id)

    def save_settings(self):
        if self.block_spectator_action("保存设置"):
            return
        achievements_data = read_achievements()
        summary = load_record_summary(achievements_data=achievements_data)
        rank_progress = read_rank_progress()
        reveal_all = bool(self.settings_admin_reveal_hidden_var.get()) if (self.settings_admin_reveal_hidden_var and is_admin_account(self.current_account)) else False
        avatar_id = coerce_avatar_id(self.settings_avatar_var.get(), summary["rating"], reveal_all=reveal_all)
        title_id = coerce_title_id(self.settings_title_var.get() if self.settings_title_var else None, summary["rating"], achievements_data, rank_progress)
        rank_badge_id = coerce_rank_badge_id(self.rank_badge_var.get() if self.rank_badge_var else "", rank_progress)
        home_music_id = coerce_home_music_id(
            self.settings_home_music_var.get() if self.settings_home_music_var else None,
            summary["rating"],
            reveal_all=reveal_all,
        )
        nickname = self.settings_nickname_var.get()
        if self.current_account:
            try:
                self.current_account = rename_account(self.current_account["id"], nickname)
                nickname = self.current_account["nickname"]
            except AccountError as exc:
                messagebox.showerror("保存失败", str(exc))
                return
        self.player_settings = save_player_settings({
            "nickname": nickname,
            "avatar_id": avatar_id,
            "title_id": title_id,
            "rank_badge_id": rank_badge_id,
            "backdrop_speed": self.settings_speed_var.get(),
            "backdrop_density": self.settings_density_var.get(),
            "backdrop_opacity": self.settings_opacity_var.get(),
            "font_scale": self.settings_font_scale_var.get(),
            "music_volume": self.settings_music_volume_var.get(),
            "sfx_volume": self.settings_sfx_volume_var.get(),
            "home_music_id": home_music_id,
            "sfx_choices": self.selected_sfx_choices_from_settings(),
            "transitions_enabled": self.settings_transitions_var.get(),
            "window_width": self.settings_window_width_var.get(),
            "window_height": self.settings_window_height_var.get(),
            "tutorial_completed": self.player_settings.get("tutorial_completed", True),
            "admin_reveal_hidden": reveal_all,
        })
        self.apply_ui_font_scale()
        self.apply_audio_settings()
        if not self.fullscreen:
            self.geometry(f"{self.player_settings['window_width']}x{self.player_settings['window_height']}")
        if self.player_settings["backdrop_speed"] >= 9.95 and self.player_settings["backdrop_density"] >= 9.95:
            self.complete_achievement("backdrop_overdrive")
        messagebox.showinfo("设置已保存", f"欢迎回来，{self.player_settings['nickname']}。")
        self.show_home()

    def ui_font_scale(self):
        try:
            return float((self.player_settings or {}).get("font_scale", 1.0))
        except (TypeError, ValueError):
            return 1.0

    def apply_ui_font_scale(self):
        scale = max(0.8, min(2.0, self.ui_font_scale()))
        set_ui_scale(scale)
        try:
            self.tk.call("tk", "scaling", self.base_tk_scaling * scale)
        except tk.TclError:
            pass

    def apply_window_icon(self):
        if not APP_ICON_FILE.exists():
            return
        try:
            self.iconbitmap(str(APP_ICON_FILE))
        except tk.TclError:
            pass

    def reset_settings(self):
        if self.block_spectator_action("恢复默认设置"):
            return
        self.player_settings = save_player_settings(DEFAULT_PLAYER_SETTINGS)
        self.apply_ui_font_scale()
        self.apply_audio_settings()
        self.show_settings()
