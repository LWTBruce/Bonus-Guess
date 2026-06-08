from ._shared import *


class NavigationHomeMixin:
    def clear(self, transition=True):
        self.clear_tutorial_overlay()
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        if self.backdrop_job:
            self.after_cancel(self.backdrop_job)
            self.backdrop_job = None
        if self.hint_cooldown_job:
            self.after_cancel(self.hint_cooldown_job)
            self.hint_cooldown_job = None
        if self.anti_cheat_poll_job:
            self.after_cancel(self.anti_cheat_poll_job)
            self.anti_cheat_poll_job = None
        if self.transition_job:
            self.after_cancel(self.transition_job)
            self.transition_job = None
        self.answer_entry = None
        self.crossword_canvas = None
        self.crossword_word_listbox = None
        self.crossword_hint_button = None
        self.crossword_library_hint_button = None
        self.hint_box = None
        self.hint_text_widget = None
        self.hint_scrollbar = None
        if self.transition_canvas and self.transition_canvas.winfo_exists():
            self.transition_canvas.destroy()
        self.transition_canvas = None
        self.backdrop_canvas = None
        self.answer_entry_frame = None
        self.tutorial_confirm_button = None
        self.tutorial_question_panel = None
        self.tutorial_hint_button = None
        self.tutorial_library_hint_button = None
        for child in self.container.winfo_children():
            child.destroy()
        self.transition_token += 1
        if transition and self.transitions_enabled():
            token = self.transition_token
            self.after_idle(lambda: self._start_page_transition(token))

    def transitions_enabled(self):
        return bool((self.player_settings or {}).get("transitions_enabled", True))

    def show_crossword_loading_screen(self, difficulty, is_crossword_rank=False, size=None, max_words=None):
        if not self.transitions_enabled():
            return
        self.play_music(self.rank_music_track() if is_crossword_rank else "crossword")
        self.clear(transition=False)
        self._start_backdrop("wind")
        self.update_idletasks()
        width = max(self.container.winfo_width(), self.winfo_width(), 900)
        height = max(self.container.winfo_height(), self.winfo_height(), 620)
        canvas = tk.Canvas(self.container, bg="#111725", bd=0, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.tk.call("raise", canvas._w)

        left = width * 0.24
        right = width * 0.76
        canvas.create_rectangle(0, 0, left, height, fill="#0d1321", outline="")
        canvas.create_rectangle(right, 0, width, height, fill="#0d1321", outline="")
        canvas.create_line(left, 0, left, height, fill="#2f70b7", width=2)
        canvas.create_line(right, 0, right, height, fill="#2f70b7", width=2)
        for index in range(9):
            y = height * (index + 1) / 10
            canvas.create_line(width * 0.12, y, width * 0.88, y, fill="#172f4d", width=1)
        for index, radius in enumerate((72, 108, 146)):
            canvas.create_oval(
                width / 2 - radius * 1.9,
                height / 2 - radius * 0.45,
                width / 2 + radius * 1.9,
                height / 2 + radius * 0.45,
                outline=("#2f70b7", "#58c7ff", "#f6d36b")[index],
                width=1,
            )
        canvas.create_text(
            width / 2,
            height / 2 - 42,
            text="字谜加载中",
            fill="#fff2bd",
            font=("Microsoft YaHei UI", 28, "bold"),
        )
        detail_parts = []
        if is_crossword_rank and self.rank_id:
            detail_parts.append(f"Class {int(self.rank_id):02d}")
        if size:
            if isinstance(size, tuple):
                detail_parts.append(f"{size[0]}×{size[1]}")
            else:
                detail_parts.append(f"{int(size)}×{int(size)}")
        if max_words:
            detail_parts.append(f"约 {int(max_words)} 词")
        detail = " / ".join(detail_parts) or str(difficulty or "")
        canvas.create_text(
            width / 2,
            height / 2 + 10,
            text=detail,
            fill="#9fb7ff",
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        canvas.create_text(
            width / 2,
            height / 2 + 56,
            text="正在生成棋盘与交叉位置...",
            fill="#8ee6ff",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        self.update_idletasks()
        try:
            self.update()
        except tk.TclError:
            pass

    @staticmethod
    def smart_wrap_text(text, limit=24):
        leading_punctuation = "，。、；：？！、）】》〉’”"
        wrapped = []
        for paragraph in str(text).split("\n"):
            line = ""
            for index, char in enumerate(paragraph):
                line += char
                next_char = paragraph[index + 1] if index + 1 < len(paragraph) else ""
                if len(line) >= limit and next_char not in leading_punctuation:
                    wrapped.append(line.rstrip())
                    line = ""
            if line:
                wrapped.append(line.rstrip())
        return "\n".join(wrapped)

    def _start_page_transition(self, token):
        if token != self.transition_token or not self.container.winfo_exists():
            return
        self.transition_canvas = tk.Canvas(self.container, bg="#111725", bd=0, highlightthickness=0)
        self.transition_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.transition_canvas.tk.call("raise", self.transition_canvas._w)
        self.transition_style = random.choice(["curtain", "iris", "stripes", "scanline", "diagonal"])
        self._draw_page_transition(token, 0)

    def _draw_page_transition(self, token, step):
        canvas = self.transition_canvas
        if token != self.transition_token or not canvas or not canvas.winfo_exists():
            return
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        progress = min(step / 18, 1.0)
        eased = 1 - (1 - progress) ** 3
        canvas.delete("all")
        style = self.transition_style
        if style == "curtain":
            curtain = (1 - eased) * width * 0.52
            if curtain <= 2:
                pass
            else:
                canvas.create_rectangle(0, 0, curtain, height, fill="#0d1321", outline="")
                canvas.create_rectangle(width - curtain, 0, width, height, fill="#0d1321", outline="")
                canvas.create_line(curtain, 0, curtain, height, fill="#263a58", width=2)
                canvas.create_line(width - curtain, 0, width - curtain, height, fill="#263a58", width=2)
        elif style == "iris":
            pad_x = width * eased / 2
            pad_y = height * eased / 2
            canvas.create_rectangle(0, 0, width, max(0, height / 2 - pad_y), fill="#0d1321", outline="")
            canvas.create_rectangle(0, min(height, height / 2 + pad_y), width, height, fill="#0d1321", outline="")
            canvas.create_rectangle(0, 0, max(0, width / 2 - pad_x), height, fill="#0d1321", outline="")
            canvas.create_rectangle(min(width, width / 2 + pad_x), 0, width, height, fill="#0d1321", outline="")
            canvas.create_rectangle(width / 2 - pad_x, height / 2 - pad_y, width / 2 + pad_x, height / 2 + pad_y, outline="#263a58", width=2)
        elif style == "stripes":
            stripe_count = 9
            stripe_h = height / stripe_count
            for index in range(stripe_count):
                offset = width * eased * (1.04 if index % 2 else 1.0)
                if index % 2:
                    canvas.create_rectangle(0, index * stripe_h, max(0, width - offset), (index + 1) * stripe_h + 1, fill="#0d1321", outline="")
                else:
                    canvas.create_rectangle(min(width, offset), index * stripe_h, width, (index + 1) * stripe_h + 1, fill="#0d1321", outline="")
        elif style == "scanline":
            band = max(1, (1 - eased) * height)
            canvas.create_rectangle(0, 0, width, band, fill="#0d1321", outline="")
            canvas.create_line(0, band, width, band, fill="#263a58", width=2)
            for index in range(0, int(band), 28):
                canvas.create_line(0, index, width, index, fill="#172238", width=1)
        else:
            shift = width * eased + height * 0.45
            points = [0, 0, max(0, shift - height * 0.45), 0, shift, height, 0, height]
            canvas.create_polygon(points, fill="#0d1321", outline="")
            canvas.create_line(max(0, shift - height * 0.45), 0, shift, height, fill="#263a58", width=2)
        if progress < 0.96:
            for index in range(7):
                y = (height * (index + 1) / 8 + step * 5) % height
                canvas.create_line(width * 0.08, y, width * 0.92, y, fill="#172238", width=1)
        if progress >= 1.0:
            canvas.destroy()
            self.transition_canvas = None
            self.transition_job = None
            return
        self.transition_job = self.after(22, lambda: self._draw_page_transition(token, step + 1))

    def show_home(self):
        self.play_music("home")
        self.clear()
        self._start_backdrop("grid")

        center = tk.Frame(self.container, bg="#111725")
        center.place(relx=0.5, rely=0.48, anchor="center")

        self.draw_home_title(center).pack(pady=(0, 36))
        home_summary = load_record_summary()
        self._profile_badge(home_summary)

        if self.is_spectating():
            tk.Label(
                center,
                text=f"旁观模式：{self.current_account.get('nickname', '')}",
                fg="#f6d36b",
                bg="#111725",
                font=("Microsoft YaHei UI", 16, "bold"),
            ).pack(pady=(0, 8))
            tk.Label(
                center,
                text="只能查看主页、历史记录、成就和玩家档案。",
                fg="#9ca8c7",
                bg="#111725",
                font=("Microsoft YaHei UI", 11, "bold"),
            ).pack(pady=(0, 22))
            start_button = None
        else:
            start_button = HoverButton(center, "开始游戏", self.show_mode_select, width=320, height=82)
            start_button.pack(pady=(0, 24))
        link_row = tk.Frame(center, bg="#111725")
        link_row.pack()
        HoverButton(link_row, "历史记录", self.show_history, width=156, height=56, accent="#8fb6ff").grid(row=0, column=0, padx=8)
        HoverButton(link_row, "成就", self.show_achievements, width=156, height=56, accent="#f6d36b").grid(row=0, column=1, padx=8)
        if self.is_spectating():
            HoverButton(link_row, "玩家档案", self.show_settings, width=156, height=56, accent="#f6a6ff").grid(row=0, column=2, padx=8)
            HoverButton(link_row, "退出旁观", self.exit_spectator_mode, width=156, height=56, accent="#ff9b89").grid(row=0, column=3, padx=8)
        else:
            HoverButton(link_row, "游戏机制", self.show_game_mechanics, width=156, height=56, accent="#7fd9c6").grid(row=0, column=2, padx=8)
            HoverButton(link_row, "漏洞反馈", self.show_feedback_dialog, width=156, height=56, accent="#ffcf8f").grid(row=0, column=3, padx=8)
            HoverButton(link_row, "设置", self.show_settings, width=156, height=56, accent="#f6a6ff").grid(row=0, column=4, padx=8)
        tk.Label(
            self.container,
            text="F11 全屏 / Esc 退出全屏",
            fg="#64708f",
            bg="#111725",
            font=("Microsoft YaHei UI", 10),
        ).place(relx=0.5, rely=0.965, anchor="center")
        tk.Label(
            self.container,
            text=f"v{APP_VERSION}",
            fg="#4f5a75",
            bg="#111725",
            font=("Consolas", 11, "bold"),
        ).place(relx=0.018, rely=0.965, anchor="sw")
        tk.Label(
            self.container,
            text="Made by Lω∇τ\nDedicated to all PHOers",
            fg="#4f5a75",
            bg="#111725",
            font=("Segoe UI", 10, "bold"),
            justify="right",
        ).place(relx=0.982, rely=0.965, anchor="se")
        if self.tutorial_active and self.tutorial_step == "home" and start_button:
            self.render_tutorial_overlay(
                start_button,
                "第一步：从主页进入",
                "这里是正式主页。先点击高光的“开始游戏”，教程会带你进入一局物理入门题。",
            )

    def show_feedback_dialog(self):
        if self.is_spectating():
            messagebox.showinfo("旁观模式", "旁观模式只能查看数据，不能提交反馈。")
            return
        if not self.current_account:
            self.show_login()
            return
        popup = tk.Toplevel(self)
        popup.title("漏洞反馈")
        popup.configure(bg="#111725")
        popup.geometry("700x560")
        popup.minsize(600, 480)
        popup.transient(self)
        popup.grab_set()
        panel = tk.Frame(popup, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(panel, text="漏洞反馈", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).pack(anchor="w", padx=24, pady=(20, 6))
        tk.Label(
            panel,
            text="把你遇到的问题、卡顿、排版异常，或者希望改进的地方写在这里。提交后会进入管理员后台文件，只有管理员能查看和处理。",
            fg="#c8d2ee",
            bg="#182033",
            wraplength=630,
            justify="left",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", padx=24, pady=(0, 14))
        row = tk.Frame(panel, bg="#182033")
        row.pack(side="bottom", anchor="w", fill="x", padx=24, pady=(0, 22))
        text_box = tk.Text(
            panel,
            height=12,
            wrap="word",
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        text_box.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        text_box.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        def submit():
            content = text_box.get("1.0", "end").strip()
            try:
                submit_feedback(self.current_account, content)
            except ValueError as exc:
                messagebox.showwarning("反馈为空", str(exc), parent=popup)
                return
            except Exception as exc:
                messagebox.showerror("提交失败", str(exc), parent=popup)
                return
            popup.destroy()
            messagebox.showinfo("已提交", "反馈已保存到管理员后台。谢谢你认真反馈。")

        HoverButton(row, "提交反馈", submit, width=150, height=54, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 10))
        HoverButton(row, "取消", popup.destroy, width=120, height=54, accent="#ff9b89").grid(row=0, column=1)
        self.after(80, text_box.focus_set)

    def draw_home_title(self, parent, compact=False):
        if compact:
            width = min(scaled_int(640), 760)
            height = min(scaled_int(126), 150)
            title_size = min(scaled_int(32), 40)
            subtitle_size = min(scaled_int(14), 18)
        else:
            width = scaled_int(760)
            height = scaled_int(156)
            title_size = scaled_int(38)
            subtitle_size = scaled_int(17)
        canvas = tk.Canvas(parent, width=width, height=height, bg="#111725", bd=0, highlightthickness=0)
        cx = width / 2
        for index, radius in enumerate((width * 0.42, width * 0.34, width * 0.26)):
            y = height * (0.46 + index * 0.035)
            canvas.create_oval(
                cx - radius,
                y - radius * 0.13,
                cx + radius,
                y + radius * 0.13,
                outline=["#1f4168", "#244f83", "#2c66a4"][index],
                width=1,
            )
        for x, y, size, color in (
            (width * 0.11, height * 0.20, 3, "#69d8ff"),
            (width * 0.86, height * 0.18, 2, "#f6d36b"),
            (width * 0.77, height * 0.70, 3, "#9ff2b2"),
            (width * 0.22, height * 0.77, 2, "#8fb6ff"),
        ):
            canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
        title_font = ("Microsoft YaHei UI", title_size, "bold")
        subtitle_font = ("Segoe UI", subtitle_size, "bold")
        for offset, color in ((5, "#172d4d"), (3, "#245a91"), (1, "#69d8ff")):
            canvas.create_text(cx + offset, height * 0.43 + offset, text=TITLE_CN, fill=color, font=title_font)
        canvas.create_text(cx, height * 0.43, text=TITLE_CN, fill="#fff2bd", font=title_font)
        canvas.create_line(width * 0.24, height * 0.66, width * 0.76, height * 0.66, fill="#2d78b7", width=2)
        canvas.create_text(cx, height * 0.82, text=TITLE_EN, fill="#8fb6ff", font=subtitle_font)
        return canvas

    def _profile_badge(self, summary):
        achievements_data = read_achievements()
        rank_progress = read_rank_progress()
        reveal_all = self.admin_reveal_hidden_enabled()
        avatar_id = coerce_avatar_id(self.player_settings.get("avatar_id", 0), summary.get("rating", 0), reveal_all=reveal_all)
        equipped_title = title_name(coerce_title_id(self.player_settings.get("title_id"), summary.get("rating", 0), achievements_data, rank_progress))
        rank_badge_id = coerce_rank_badge_id(self.player_settings.get("rank_badge_id", ""), rank_progress)
        badge = tk.Frame(self.container, bg="#182033", highlightbackground="#3b4560", highlightthickness=1, cursor="hand2")
        badge.place(relx=0.98, rely=0.035, anchor="ne")
        avatar_size = scaled_int(58)
        outer_pad = scaled_int(8)
        avatar_canvas = tk.Canvas(badge, width=avatar_size, height=avatar_size, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
        avatar_canvas.pack(side="left", padx=(scaled_int(10), scaled_int(8)), pady=outer_pad)
        draw_avatar(avatar_canvas, avatar_id, avatar_size)
        info = tk.Frame(badge, bg="#182033", cursor="hand2")
        info.pack(side="left", padx=(0, scaled_int(12)), pady=outer_pad)
        tk.Label(
            info,
            text=self.player_settings.get("nickname", "PHOer"),
            fg="#fff2bd",
            bg="#182033",
            font=("Microsoft YaHei UI", 11, "bold"),
            cursor="hand2",
        ).pack(anchor="w")
        tk.Label(
            info,
            text=equipped_title,
            fg="#8fb6ff",
            bg="#182033",
            font=("Microsoft YaHei UI", 9, "bold"),
            cursor="hand2",
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            info,
            text=f"Rating {format_rating(summary['rating'])}",
            fg="#9ff2b2",
            bg="#182033",
            font=("Consolas", 12, "bold"),
            cursor="hand2",
        ).pack(anchor="w", pady=(3, 0))
        widgets = [badge, avatar_canvas, info, *info.winfo_children()]
        if rank_badge_id:
            badge_width = scaled_int(190)
            badge_height = scaled_int(30)
            badge_canvas = tk.Canvas(info, width=badge_width, height=badge_height, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
            badge_canvas.pack(anchor="w", pady=(scaled_int(6), 0))
            draw_rank_badge(badge_canvas, rank_badge_id, badge_width, badge_height)
            widgets.append(badge_canvas)
        for widget in widgets:
            widget.bind("<Button-1>", lambda _event: self.show_settings())

    def show_game_mechanics(self, tab=None):
        self.play_music("archive")
        self.clear()
        self._topbar("游戏机制说明", self.show_home)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        self._start_backdrop("grid", frame)
        center = tk.Frame(frame, bg="#111725")
        center.place(relx=0.5, rely=0.47, anchor="center")
        tk.Label(center, text="选择阅读方式", fg="#fff2bd", bg="#111725", font=("Microsoft YaHei UI", 30, "bold")).pack(pady=(0, 22))
        tk.Label(
            center,
            text="快速上手先告诉你该看哪里；详细规则会说明模式、提示、计分、记录和称号。",
            fg="#c8d2ee",
            bg="#111725",
            font=("Microsoft YaHei UI", 13),
        ).pack(pady=(0, 34))
        row = tk.Frame(center, bg="#111725")
        row.pack()
        HoverButton(row, "快速上手", lambda: self.show_game_mechanics_page("quick"), width=250, height=86, accent="#9ff2b2").grid(row=0, column=0, padx=18)
        HoverButton(row, "详细规则", lambda: self.show_game_mechanics_page("detail"), width=250, height=86, accent="#9fb7ff").grid(row=0, column=1, padx=18)
