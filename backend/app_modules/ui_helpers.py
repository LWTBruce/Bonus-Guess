from ._shared import *


class UiHelpersMixin:
    def bind_scroll_wheel(self, shell, target, units=3):
        def on_mousewheel(event):
            if not target.winfo_exists():
                return "break"
            if getattr(event, "num", None) == 4:
                amount = -units
            elif getattr(event, "num", None) == 5:
                amount = units
            else:
                delta = getattr(event, "delta", 0)
                if not delta:
                    return "break"
                amount = int(-delta / 120)
                if amount == 0:
                    amount = -1 if delta > 0 else 1
            target.yview_scroll(amount, "units")
            return "break"

        events = ("<MouseWheel>", "<Button-4>", "<Button-5>")

        def bind_all(_event=None):
            for event_name in events:
                target.bind_all(event_name, on_mousewheel)

        def unbind_all(_event=None):
            for event_name in events:
                target.unbind_all(event_name)

        shell.bind("<Enter>", bind_all, add="+")
        shell.bind("<Leave>", unbind_all, add="+")
        for widget in (shell, target):
            for event_name in events:
                widget.bind(event_name, on_mousewheel, add="+")

    def make_scroll_frame(self, parent, bg=None):
        if bg is None:
            bg = self.theme_color("base")
        shell = tk.Frame(parent, bg=bg)
        shell.pack(fill="both", expand=True)
        canvas = tk.Canvas(shell, bg=bg, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=bg)
        inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_scroll_wheel(shell, canvas)
        return inner

    def _topbar(self, title, back_command):
        base_bg = self.theme_color("base")
        bar = tk.Frame(self.container, bg=base_bg)
        bar.pack(fill="x", padx=22, pady=(14, 8))
        HoverButton(bar, "返回", back_command, width=110, height=48, accent="#8fb6ff").pack(side="left")
        tk.Label(bar, text=title, fg=self.theme_color("title"), bg=base_bg, font=("Microsoft YaHei UI", 19, "bold")).pack(side="left", padx=18)
        line = tk.Canvas(self.container, height=10, bg=base_bg, bd=0, highlightthickness=0)
        line.pack(fill="x", padx=34, pady=(0, 12))
        line.create_line(0, 5, 1200, 5, fill=self.theme_color("grid_a"), width=1)
        line.create_line(0, 6, 260, 6, fill=self.theme_color("line"), width=2)

    def _tick(self):
        if not self.start_time:
            return
        now = time.perf_counter()
        if self.is_timed_mode() and self.timed_deadline:
            remaining = max(0, self.timed_deadline - now)
            self.timer_label.config(text=f"{remaining:.1f} 秒")
            if self.timed_status_label:
                if self.rank_mode:
                    label = f"{rank_kind_label(self.rank_kind)}题"
                    self.timed_status_label.config(
                        text=(
                            f"{label} {self.rank_question_index + 1}/{len(self.rank_requirements)}\n"
                            f"已答对 {self.timed_correct} 题\n"
                            f"总分 {self.rank_session_score}｜提示 {self.rank_hint_used}/{rank_hint_limit(self.rank_id)}"
                        )
                    )
                elif self.custom_mode:
                    self.timed_status_label.config(text=self.custom_status_text())
                else:
                    self.timed_status_label.config(text=f"已答对 {self.timed_correct} 题\n计入 {format_score(self.timed_score)} 分")
            if remaining <= 0:
                if self.rank_mode:
                    self.fail_rank_challenge("时间到")
                elif self.is_custom_challenge_mode():
                    self.fail_custom_challenge("限时结束")
                else:
                    self.show_timed_result()
                return
        else:
            self.timer_label.config(text=f"{now - self.start_time:.1f} 秒")
        self.update_score_label()
        self.timer_job = self.after(100, self._tick)

    def toggle_fullscreen(self, _event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self, _event=None):
        self.fullscreen = False
        self.attributes("-fullscreen", False)
