import json
import random
import sys
import time
import unicodedata
import uuid
from datetime import datetime

from game_config import (
    ACHIEVEMENT_CATEGORIES,
    APP_VERSION,
    GAME_MECHANICS_FILE,
    HIDDEN_ACHIEVEMENT_IDS,
    HINT_COOLDOWN_SECONDS,
    RECORD_DIR,
    RESOURCE_DIR,
    TERM_CLUES_DIR,
    TITLE_CN,
    TITLE_EN,
    WORDS_DIR,
)

import tkinter as tk
from tkinter import messagebox

from avatars import AVATARS, draw_avatar
from backdrop import BackdropMixin
from clue_library import ClueLibrary
from cosmetics import (
    RATING_REWARDS,
    coerce_avatar_id,
    coerce_title_id,
    title_name,
    unlocked_avatar_ids,
    unlocked_title_options,
)
from markdown_view import render_inline_markdown, render_markdown, split_mechanics_sections
from player_profile import DEFAULT_PLAYER_SETTINGS, load_player_settings, save_player_settings
from rank_system import (
    RANK_CHALLENGES,
    coerce_rank_badge_id,
    draw_rank_badge,
    format_rank_time,
    mark_rank_passed,
    parse_rank_badge_id,
    rank_badge_id,
    rank_badge_name,
    rank_by_id,
    rank_hint_cooldown_seconds,
    rank_hint_limit,
    rank_kind_label,
    rank_pass_score,
    rank_progress_key,
    read_rank_progress,
    subject_label,
    unlocked_rank_badges,
)
from records import (
    ACHIEVEMENTS,
    apply_initial_mask,
    choose_daily_term_by_difficulty,
    format_duration,
    format_rating,
    format_score,
    is_abandoned_record,
    is_counted_record,
    load_record_entries,
    random_free_hint_quota,
    random_mask_positions,
    read_achievements,
    record_datetime,
    record_effective_difficulty,
    record_free_hint_count,
    record_hint_count,
    record_library_hint_count,
    record_mode,
    record_paid_hint_count,
    record_play_mode,
    record_score,
    record_single_rating,
    record_storage_dir,
    record_term_difficulty,
    record_weighted_score,
    score_weight_for_difficulty,
    summarize_records,
    write_achievements,
)
from term_library import TermLibrary
from widgets import HoverButton, WobblePanel


class BonusGuessApp(BackdropMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.player_settings = load_player_settings()
        self.title(f"{TITLE_CN} {APP_VERSION}")
        self.geometry(f"{self.player_settings['window_width']}x{self.player_settings['window_height']}")
        self.minsize(936, 598)
        self.configure(bg="#111725")
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        self.library = TermLibrary(WORDS_DIR)
        self.clue_library = ClueLibrary(TERM_CLUES_DIR)
        self.mode = None
        self.play_mode = "自由"
        self.selected_subject = "物理模式"
        self.selected_play_mode = "自由"
        self.difficulty = None
        self.terms = []
        self.library_files = []
        self.current = None
        self.accepted_answers = []
        self.display_initials = ""
        self.clue_entry = {}
        self.clue_lines = []
        self.clue_line_types = []
        self.clue_visible_count = 0
        self.clue_fragment_count = 0
        self.clue_box = None
        self.mask_positions = []
        self.mask_count = 0
        self.effective_difficulty = 0.0
        self.revealed_positions = set()
        self.hint_lines = []
        self.hint_penalties = []
        self.free_hint_quota = 0
        self.free_hint_count = 0
        self.paid_hint_count = 0
        self.attempts = []
        self.start_time = None
        self.timer_job = None
        self.fullscreen = False
        self.game_active = False
        self.record_saved = False
        self.score_penalty = 0
        self.score_label = None
        self.library_hint_used = False
        self.library_hint_text = ""
        self.library_hint_label = None
        self.library_hint_button = None
        self.hint_button = None
        self.hint_cooldown_until = 0.0
        self.hint_cooldown_job = None
        self.answer_entry = None
        self.answer_entry_frame = None
        self.anti_cheat_poll_job = None
        self.initial_input_warnings = 0
        self.blocked_initial_input = ""
        self.raw_initial_buffer = ""
        self.raw_initial_last_at = 0.0
        self.suppress_answer_trace = False
        self.cheat_pending = False
        self.cheat_info = {}
        self.scope_text = ""
        self.backdrop_canvas = None
        self.backdrop_job = None
        self.backdrop_phase = 0.0
        self.backdrop_style = "grid"
        self.transition_canvas = None
        self.transition_job = None
        self.transition_token = 0
        self.transition_style = "curtain"
        self.history_show_details = False
        self.mechanics_tab = "quick"
        self.timed_deadline = None
        self.timed_correct = 0
        self.timed_score = 0
        self.timed_round_start = None
        self.timed_status_label = None
        self.achievements = read_achievements()
        self.avatar_option_canvases = []
        self.avatar_option_labels = []
        self.avatar_preview_canvas = None
        self.available_avatar_ids = {0}
        self.available_title_options = []
        self.settings_title_var = None
        self.rank_badge_var = None
        self.rank_badge_canvases = []
        self.custom_mode = False
        self.custom_config = {}
        self.custom_file_paths = []
        self.custom_subject_var = None
        self.custom_play_var = None
        self.custom_timing_var = None
        self.custom_challenge_var = None
        self.custom_challenge_count_var = None
        self.custom_minutes_entries = []
        self.custom_challenge_entries = []
        self.custom_file_listbox = None
        self.custom_session_id = ""
        self.rank_mode = False
        self.rank_subject = ""
        self.rank_id = 0
        self.rank_kind = "free"
        self.rank_requirements = []
        self.rank_question_index = 0
        self.rank_session_id = ""
        self.rank_relaxed = False
        self.rank_target_difficulty = 0.0
        self.rank_hint_used = 0
        self.rank_session_score = 0

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.container = tk.Frame(self, bg="#111725")
        self.container.pack(fill="both", expand=True)
        self.complete_achievement("first_launch")
        self.refresh_achievements()
        self.show_home()

    def clear(self, transition=True):
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
        if self.transition_canvas and self.transition_canvas.winfo_exists():
            self.transition_canvas.destroy()
        self.transition_canvas = None
        self.backdrop_canvas = None
        self.answer_entry_frame = None
        for child in self.container.winfo_children():
            child.destroy()
        self.transition_token += 1
        if transition and self.transitions_enabled():
            token = self.transition_token
            self.after_idle(lambda: self._start_page_transition(token))

    def transitions_enabled(self):
        return bool((self.player_settings or {}).get("transitions_enabled", True))

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
        self.clear()
        self._start_backdrop("grid")

        center = tk.Frame(self.container, bg="#111725")
        center.place(relx=0.5, rely=0.48, anchor="center")

        tk.Label(
            center,
            text=TITLE_CN,
            fg="#fff2bd",
            bg="#111725",
            font=("Microsoft YaHei UI", 42, "bold"),
        ).pack(pady=(0, 8))
        tk.Label(
            center,
            text=TITLE_EN,
            fg="#8fb6ff",
            bg="#111725",
            font=("Segoe UI", 21, "bold"),
        ).pack(pady=(0, 42))
        home_summary = summarize_records(load_record_entries())
        self._profile_badge(home_summary)

        HoverButton(center, "开始游戏", self.show_mode_select, width=320, height=82).pack(pady=(0, 24))
        link_row = tk.Frame(center, bg="#111725")
        link_row.pack()
        HoverButton(link_row, "历史记录", self.show_history, width=156, height=56, accent="#8fb6ff").grid(row=0, column=0, padx=8)
        HoverButton(link_row, "成就", self.show_achievements, width=156, height=56, accent="#f6d36b").grid(row=0, column=1, padx=8)
        HoverButton(link_row, "游戏机制", self.show_game_mechanics, width=156, height=56, accent="#7fd9c6").grid(row=0, column=2, padx=8)
        HoverButton(link_row, "设置", self.show_settings, width=156, height=56, accent="#f6a6ff").grid(row=0, column=3, padx=8)
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

    def _profile_badge(self, summary):
        achievements_data = read_achievements()
        rank_progress = read_rank_progress()
        avatar_id = coerce_avatar_id(self.player_settings.get("avatar_id", 0), summary.get("rating", 0))
        equipped_title = title_name(coerce_title_id(self.player_settings.get("title_id"), summary.get("rating", 0), achievements_data, rank_progress))
        rank_badge_id = coerce_rank_badge_id(self.player_settings.get("rank_badge_id", ""), rank_progress)
        badge = tk.Frame(self.container, bg="#182033", highlightbackground="#3b4560", highlightthickness=1, cursor="hand2")
        badge.place(relx=0.98, rely=0.035, anchor="ne")
        avatar_canvas = tk.Canvas(badge, width=58, height=58, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
        avatar_canvas.pack(side="left", padx=(10, 8), pady=8)
        draw_avatar(avatar_canvas, avatar_id, 58)
        info = tk.Frame(badge, bg="#182033", cursor="hand2")
        info.pack(side="left", padx=(0, 12), pady=8)
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
            badge_canvas = tk.Canvas(info, width=155, height=30, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
            badge_canvas.pack(anchor="w", pady=(6, 0))
            draw_rank_badge(badge_canvas, rank_badge_id, 155, 30)
            widgets.append(badge_canvas)
        for widget in widgets:
            widget.bind("<Button-1>", lambda _event: self.show_settings())

    def show_game_mechanics(self, tab=None):
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
            text="快速上手适合先玩起来，详细规则会列出概率、计分和 Rating 参数。",
            fg="#c8d2ee",
            bg="#111725",
            font=("Microsoft YaHei UI", 13),
        ).pack(pady=(0, 34))
        row = tk.Frame(center, bg="#111725")
        row.pack()
        HoverButton(row, "快速上手", lambda: self.show_game_mechanics_page("quick"), width=250, height=86, accent="#9ff2b2").grid(row=0, column=0, padx=18)
        HoverButton(row, "详细规则", lambda: self.show_game_mechanics_page("detail"), width=250, height=86, accent="#9fb7ff").grid(row=0, column=1, padx=18)

    def show_game_mechanics_page(self, tab):
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
        self.clear()
        self._topbar("设置", self.show_home)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        self._start_backdrop("particles", frame)

        summary = summarize_records(load_record_entries())
        achievements_data = read_achievements()
        rank_progress = read_rank_progress()
        rating_value = summary["rating"]
        self.available_avatar_ids = unlocked_avatar_ids(rating_value)
        self.available_title_options = unlocked_title_options(rating_value, achievements_data, rank_progress)
        current_avatar_id = coerce_avatar_id(self.player_settings.get("avatar_id", 0), rating_value)
        current_title_id = coerce_title_id(self.player_settings.get("title_id"), rating_value, achievements_data, rank_progress)
        current_rank_badge_id = coerce_rank_badge_id(self.player_settings.get("rank_badge_id", ""), rank_progress)
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
        tk.Label(form, text=f"当前 Rating {format_rating(rating_value)}", fg="#9ff2b2", bg="#182033", font=("Consolas", 14, "bold")).pack(anchor="w")
        rating_detail = f"作答 {format_rating(summary['play_rating'])}  +  成就 {summary['achievement_bonus']:.3f}"
        tk.Label(form, text=rating_detail, fg="#9ca8c7", bg="#182033", font=("Consolas", 10, "bold")).pack(anchor="w", pady=(3, 0))
        tk.Label(form, text=f"当前称号：{title_name(current_title_id)}", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(4, 0))

        tk.Label(left, text="头像", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(4, 8))
        avatar_grid = tk.Frame(left, bg="#182033")
        avatar_grid.pack(padx=24, pady=(0, 12))
        self.settings_avatar_var = tk.IntVar(value=current_avatar_id)
        self.avatar_option_canvases = []
        self.avatar_option_labels = []
        for index, avatar in enumerate(AVATARS):
            cell = tk.Frame(avatar_grid, bg="#182033")
            cell.grid(row=index // 5, column=index % 5, padx=8, pady=8)
            canvas = tk.Canvas(cell, width=70, height=70, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
            canvas.pack()
            canvas.bind("<Button-1>", lambda _event, avatar_id=index: self.select_avatar(avatar_id))
            label = tk.Label(cell, text=avatar["name"], fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 9))
            label.pack(pady=(2, 0))
            self.avatar_option_canvases.append(canvas)
            self.avatar_option_labels.append(label)
        self.refresh_avatar_choices()

        tk.Label(left, text="称号", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(2, 8))
        title_grid = tk.Frame(left, bg="#182033")
        title_grid.pack(fill="x", padx=26, pady=(0, 18))
        self.settings_title_var = tk.StringVar(value=current_title_id)
        for column in range(3):
            title_grid.grid_columnconfigure(column, weight=1)
        for index, (title_id, title_text, source) in enumerate(self.available_title_options):
            rb = tk.Radiobutton(
                title_grid,
                text=f"{title_text}  ·  {source}",
                value=title_id,
                variable=self.settings_title_var,
                fg="#dce6ff",
                bg="#182033",
                activeforeground="#fff2bd",
                activebackground="#182033",
                selectcolor="#101827",
                font=("Microsoft YaHei UI", 10, "bold"),
                anchor="w",
                justify="left",
            )
            rb.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 12), pady=3)
        if not self.available_title_options:
            tk.Label(title_grid, text="暂无可佩戴称号", fg="#64708f", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(anchor="w")

        tk.Label(left, text="段位标识", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(0, 8))
        badge_grid = tk.Frame(left, bg="#182033")
        badge_grid.pack(fill="x", padx=26, pady=(0, 16))
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
            canvas = tk.Canvas(cell, width=176, height=34, bg="#182033", bd=0, highlightthickness=0, cursor="hand2")
            canvas.pack(side="left")
            draw_rank_badge(canvas, badge_id, 176, 34, selected=badge_id == current_rank_badge_id)
            canvas.bind("<Button-1>", lambda _event, value=badge_id: self.select_rank_badge(value))
            self.rank_badge_canvases.append((canvas, badge_id))
        if not unlocked_badges:
            tk.Label(badge_grid, text="通过自由段位或线索段位后解锁。", fg="#64708f", bg="#182033", font=("Microsoft YaHei UI", 10)).grid(row=1, column=0, sticky="w", pady=3)

        tk.Label(right, text="背景", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", padx=28, pady=(26, 14))
        self.settings_speed_var = tk.DoubleVar(value=float(self.player_settings.get("backdrop_speed", 1.0)))
        self.settings_density_var = tk.DoubleVar(value=float(self.player_settings.get("backdrop_density", 1.0)))
        self.settings_transitions_var = tk.BooleanVar(value=bool(self.player_settings.get("transitions_enabled", True)))
        self.settings_window_width_var = tk.StringVar(value=str(int(self.player_settings.get("window_width", 1274))))
        self.settings_window_height_var = tk.StringVar(value=str(int(self.player_settings.get("window_height", 806))))
        self.settings_speed_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_density_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_speed_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(right, self.settings_speed_var, self.update_setting_labels).pack(fill="x", padx=24, pady=(0, 18))
        self.settings_density_label.pack(anchor="w", padx=28, pady=(2, 4))
        self.make_setting_scale(right, self.settings_density_var, self.update_setting_labels).pack(fill="x", padx=24, pady=(0, 14))
        tk.Label(right, text="默认窗口大小（像素）", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=28, pady=(2, 8))
        window_row = tk.Frame(right, bg="#182033")
        window_row.pack(anchor="w", padx=24, pady=(0, 14))
        self.make_pixel_entry(window_row, self.settings_window_width_var, 92).grid(row=0, column=0)
        tk.Label(window_row, text=" × ", fg="#9ca8c7", bg="#182033", font=("Consolas", 14, "bold")).grid(row=0, column=1, padx=4)
        self.make_pixel_entry(window_row, self.settings_window_height_var, 92).grid(row=0, column=2)
        tk.Label(window_row, text="  保存后生效", fg="#64708f", bg="#182033", font=("Microsoft YaHei UI", 10)).grid(row=0, column=3, padx=(10, 0))
        tk.Checkbutton(
            right,
            text="启用页面过场动画",
            variable=self.settings_transitions_var,
            fg="#c8d2ee",
            bg="#182033",
            activeforeground="#fff2bd",
            activebackground="#182033",
            selectcolor="#101827",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", padx=24, pady=(0, 18))
        self.update_setting_labels()

        tk.Label(
            right,
            text=self.smart_wrap_text("速度和密度会影响所有动态背景。数值越高，背景越活跃；数值越低，界面越安静。页面过场可按偏好关闭。", 27),
            fg="#9ca8c7",
            bg="#182033",
            justify="left",
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", padx=28, pady=(0, 26))
        buttons = tk.Frame(right, bg="#182033")
        buttons.pack(anchor="w", padx=28, pady=(0, 22))
        HoverButton(buttons, "保存设置", self.save_settings, width=170, height=58, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 12))
        HoverButton(buttons, "恢复默认", self.reset_settings, width=170, height=58, accent="#ff9b89").grid(row=0, column=1, padx=12)

    def make_setting_scale(self, parent, variable, command):
        scale = tk.Scale(
            parent,
            from_=0.4,
            to=10.0,
            resolution=0.1,
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
            draw_avatar(canvas, index, 70, selected=index == current)
            locked = index not in self.available_avatar_ids
            if locked:
                canvas.create_rectangle(4, 4, 66, 66, fill="#111725", stipple="gray50", outline="#3b4560")
                canvas.create_text(35, 35, text="锁", fill="#9ca8c7", font=("Microsoft YaHei UI", 15, "bold"))
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
            draw_rank_badge(canvas, item_id, 176, 34, selected=item_id == badge_id)

    def save_settings(self):
        summary = summarize_records(load_record_entries())
        achievements_data = read_achievements()
        rank_progress = read_rank_progress()
        avatar_id = coerce_avatar_id(self.settings_avatar_var.get(), summary["rating"])
        title_id = coerce_title_id(self.settings_title_var.get() if self.settings_title_var else None, summary["rating"], achievements_data, rank_progress)
        rank_badge_id = coerce_rank_badge_id(self.rank_badge_var.get() if self.rank_badge_var else "", rank_progress)
        self.player_settings = save_player_settings({
            "nickname": self.settings_nickname_var.get(),
            "avatar_id": avatar_id,
            "title_id": title_id,
            "rank_badge_id": rank_badge_id,
            "backdrop_speed": self.settings_speed_var.get(),
            "backdrop_density": self.settings_density_var.get(),
            "transitions_enabled": self.settings_transitions_var.get(),
            "window_width": self.settings_window_width_var.get(),
            "window_height": self.settings_window_height_var.get(),
        })
        if not self.fullscreen:
            self.geometry(f"{self.player_settings['window_width']}x{self.player_settings['window_height']}")
        if self.player_settings["backdrop_speed"] >= 9.95 and self.player_settings["backdrop_density"] >= 9.95:
            self.complete_achievement("backdrop_overdrive")
        messagebox.showinfo("设置已保存", f"欢迎回来，{self.player_settings['nickname']}。")
        self.show_home()

    def reset_settings(self):
        self.player_settings = save_player_settings(DEFAULT_PLAYER_SETTINGS)
        self.show_settings()

    @staticmethod
    def normalize_play_mode_choice(play_mode):
        return "自由段位" if play_mode == "段位" else play_mode

    def show_mode_select(self, transition=True):
        self.clear(transition=transition)
        self._start_backdrop("lines")
        self._topbar("选择模式", self.show_home)
        self.selected_play_mode = self.normalize_play_mode_choice(self.selected_play_mode)

        left = tk.Frame(self.container, bg="#111725")
        left.place(x=52, y=128)
        right_panel = WobblePanel(self.container)
        right_panel.place(relx=0.55, rely=0.13, relwidth=0.41, relheight=0.80)
        right = right_panel.content

        tk.Label(left, text="学科选择", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(0, 12))
        subject_row = tk.Frame(left, bg="#111725")
        subject_row.pack(anchor="w", pady=(0, 34))
        self.choice_button(subject_row, "物理", self.selected_subject == "物理模式", lambda: self.set_mode_choice(subject="物理模式")).grid(row=0, column=0, padx=(0, 14))
        self.choice_button(subject_row, "数学", self.selected_subject == "数学模式", lambda: self.set_mode_choice(subject="数学模式")).grid(row=0, column=1, padx=14)

        tk.Label(left, text="游戏模式", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(0, 10))

        groups = [
            ("普通模式", [("自由", "#9ff2b2"), ("线索", "#7ed6ff"), ("限时", "#f6d36b"), ("真·随机", "#f6a6ff")]),
            ("段位模式", [("自由段位", "#9fb7ff"), ("线索段位", "#67e8f9")]),
            ("自定义模式", [("自定义", "#ffbd7e")]),
        ]
        for group_title, play_options in groups:
            tk.Label(left, text=group_title, fg="#9ca8c7", bg="#111725", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(8, 2))
            play_grid = tk.Frame(left, bg="#111725")
            play_grid.pack(anchor="w")
            for index, (name, accent) in enumerate(play_options):
                self.choice_button(
                    play_grid,
                    name,
                    self.selected_play_mode == name,
                    lambda value=name: self.set_mode_choice(play_mode=value),
                    accent=accent,
                    width=158,
                    height=48,
                ).grid(row=index // 2, column=index % 2, padx=(0, 12), pady=5, sticky="w")
        HoverButton(left, "下一步", self.confirm_mode_choice, width=250, height=60, accent="#8fb6ff").pack(anchor="w", pady=(22, 0))

        self.render_mode_explanation(right)

    def choice_button(self, parent, text, selected, command, accent="#8fb6ff", width=220, height=62):
        button = HoverButton(parent, f"{'◆ ' if selected else ''}{text}", command, width=width, height=height, accent=accent if selected else "#4b5877")
        return button

    def set_mode_choice(self, subject=None, play_mode=None):
        if subject:
            self.selected_subject = subject
        if play_mode:
            self.selected_play_mode = self.normalize_play_mode_choice(play_mode)
        self.show_mode_select(transition=False)

    def confirm_mode_choice(self):
        self.custom_mode = False
        self.rank_mode = False
        self.custom_config = {}
        self.play_mode = self.normalize_play_mode_choice(self.selected_play_mode)
        if self.play_mode == "自定义":
            self.show_custom_config()
            return
        if self.play_mode in {"自由段位", "线索段位"}:
            self.mode = self.selected_subject
            self.rank_kind = "clue" if self.play_mode == "线索段位" else "free"
            self.show_rank_select()
            return
        self.mode = "真·随机" if self.play_mode == "真·随机" else self.selected_subject
        self.show_difficulty()

    def render_mode_explanation(self, parent):
        for child in parent.winfo_children():
            child.destroy()
        subject_text = "物理词库" if self.selected_subject == "物理模式" else "数学词库"
        selected = self.normalize_play_mode_choice(self.selected_play_mode)
        group_name = "普通模式"
        if selected in {"自由段位", "线索段位"}:
            group_name = "段位模式"
        elif selected == "自定义":
            group_name = "自定义模式"
        if selected == "自由":
            title = "自由模式"
            lines = [
                f"从{subject_text}中按难度抽取单题。",
                "答对后立即结算，适合练习和熟悉词库。",
                "混合模式会读取该学科下全部词库。",
            ]
        elif selected == "限时":
            title = "限时模式"
            lines = [
                f"从{subject_text}中连续出题，限时 5 分钟。",
                "答对后立刻进入下一题。",
                "最终看答对题数、原始积分和计入总积分。",
            ]
        elif selected == "线索":
            title = "线索模式"
            lines = [
                f"从{subject_text}中抽取词条，但不显示首字母。",
                "初始只给一句描述，每次提示会多显示一条线索并扣分。",
                "普通和困难可能出现破碎线索，使本题总难度上升。",
            ]
        elif selected == "真·随机":
            title = "真·随机"
            lines = [
                "从物理和数学全部词库中抽题。",
                "不再区分学科选择，下一页只保留入门到困难四档难度。",
                "适合检验跨学科反应和真实词库覆盖。",
            ]
        elif selected == "自定义":
            title = "自定义模式"
            lines = [
                "自由配置出题形式、词库、词长、难度、免费提示、掩码和破碎线索。",
                "限时和自定义挑战题数是独立开关，可以组合成四种练习。",
                "记录会保存，但不计总积分、Rating、成就和正式段位。",
            ]
        elif selected == "自由段位":
            title = "自由段位"
            lines = [
                f"{subject_text}专属的限时资格挑战，共 15 个段位。",
                "全部题目为首字母题，普通和困难会沿用掩码机制。",
                "每段由固定题组构成，必须全题答对并且未超时。",
                "通过后会解锁可佩戴的段位标识和称号。",
            ]
        else:
            title = "线索段位"
            lines = [
                f"{subject_text}专属的线索资格挑战，共 15 个段位。",
                "全部题目换成线索题，不显示首字母，只显示答案字数。",
                "每段由固定题组构成，必须全题答对并且未超时。",
                "通过后会解锁可佩戴的段位标识和称号。",
            ]
        tk.Label(parent, text=group_name, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=26, pady=(24, 4))
        tk.Label(parent, text=title, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=26, pady=(0, 14))
        for line in lines:
            tk.Label(parent, text=self.smart_wrap_text(line, 24), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 13)).pack(anchor="w", padx=26, pady=6)
        if selected == "自定义":
            footer = "下一步进入自定义配置页。"
        elif selected in {"自由段位", "线索段位"}:
            footer = "下一步选择段位。自由段位和线索段位都不计总积分和 Rating；两种段位进度互相独立。"
        else:
            footer = "下一步选择选词难度。难度会影响词条难度分布、提示代价、掩码或破碎线索概率和最终 Rating。"
        tk.Label(parent, text=self.smart_wrap_text(footer, 23), fg="#9ca8c7", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11)).pack(anchor="w", padx=26, pady=(18, 0))

    def show_custom_config(self):
        self.clear()
        self._start_backdrop("grid")
        self._topbar("自定义模式", self.show_mode_select)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=5, minsize=520)
        frame.grid_columnconfigure(1, weight=3, minsize=320)

        left_panel = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        right = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        left = self.make_scroll_frame(left_panel, bg="#182033")

        tk.Label(left, text="自定义参数", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=30, pady=(26, 16))
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
        self.custom_fragment_var = tk.StringVar(value="25")
        self.custom_minutes_var = tk.StringVar(value="5")
        self.custom_challenge_count_var = tk.StringVar(value="5")

        self.custom_option_group(left, "学科", self.custom_subject_var, ["物理模式", "数学模式", "全部"], self.refresh_custom_file_list)
        self.custom_option_group(left, "出题形式", self.custom_play_var, ["首字母", "线索"], None)
        self.custom_range_inputs(left, "基础难度", self.custom_diff_min_var, self.custom_diff_max_var)
        self.custom_range_inputs(left, "中文词长", self.custom_len_min_var, self.custom_len_max_var)
        self.custom_option_group(left, "免费提示", self.custom_free_hint_var, ["自动", "0", "1", "2", "3", "4", "5"], None)
        self.custom_option_group(left, "掩码数量", self.custom_mask_var, ["自动", "0", "1", "2", "3"], None)
        self.custom_option_group(left, "破碎线索", self.custom_fragment_var, ["0", "25", "40", "100"], None)
        self.custom_option_group(left, "限时", self.custom_timing_var, ["不限时", "限时"], self.update_custom_option_states)
        self.custom_minutes_entries = self.custom_range_inputs(left, "限时时长（分钟）", self.custom_minutes_var, None, note="范围 1-30")
        self.custom_option_group(left, "段位模式", self.custom_challenge_var, ["不开启", "开启"], self.update_custom_option_states)
        self.custom_challenge_entries = self.custom_range_inputs(left, "挑战题数", self.custom_challenge_count_var, None, note="建议 1-50，默认 5")
        self.update_custom_option_states()
        HoverButton(left, "开始自定义", self.start_custom_game, width=230, height=64, accent="#ffbd7e").pack(anchor="w", padx=30, pady=(20, 28))

        tk.Label(right, text="词库多选", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(right, text="默认选中当前范围全部词库。按住 Ctrl 可以增减选择。", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(anchor="w", padx=24)
        list_shell = tk.Frame(right, bg="#182033")
        list_shell.pack(fill="both", expand=True, padx=24, pady=16)
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
        self.bind_scroll_wheel(list_shell, self.custom_file_listbox)
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
        timed_enabled = self.custom_timing_var is not None and self.custom_timing_var.get() == "限时"
        challenge_enabled = self.custom_challenge_var is not None and self.custom_challenge_var.get() == "开启"
        for entry in self.custom_minutes_entries:
            entry.configure(state="normal" if timed_enabled else "disabled", disabledforeground="#64708f")
        for entry in self.custom_challenge_entries:
            entry.configure(state="normal" if challenge_enabled else "disabled", disabledforeground="#64708f")

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

    @staticmethod
    def parse_int_var(variable, default, low, high):
        try:
            value = int(float(variable.get()))
        except (TypeError, ValueError, tk.TclError):
            value = default
        return max(low, min(high, value))

    def start_custom_game(self):
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
        diff_min = self.parse_int_var(self.custom_diff_min_var, 1, 1, 10)
        diff_max = self.parse_int_var(self.custom_diff_max_var, 10, 1, 10)
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
        timed_enabled = self.custom_timing_var is not None and self.custom_timing_var.get() == "限时"
        challenge_enabled = self.custom_challenge_var is not None and self.custom_challenge_var.get() == "开启"
        challenge_target = self.parse_int_var(self.custom_challenge_count_var, 5, 1, 50)
        self.custom_mode = True
        self.rank_mode = False
        self.custom_session_id = uuid.uuid4().hex
        self.custom_config = {
            "subject": self.custom_subject_var.get(),
            "play_kind": self.custom_play_var.get(),
            "timed_enabled": 1 if timed_enabled else 0,
            "free_hint": self.custom_free_hint_var.get(),
            "mask": self.custom_mask_var.get(),
            "fragment_probability": int(self.custom_fragment_var.get()) / 100,
            "minutes": self.parse_int_var(self.custom_minutes_var, 5, 1, 30),
            "challenge_enabled": 1 if challenge_enabled else 0,
            "challenge_target": challenge_target,
            "difficulty_min": diff_min,
            "difficulty_max": diff_max,
            "length_min": len_min,
            "length_max": len_max,
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
        self.start_round()

    def show_rank_select(self):
        self.clear()
        self._start_backdrop("lines")
        rank_kind = getattr(self, "rank_kind", "free")
        rank_label = rank_kind_label(rank_kind)
        progress_key = rank_progress_key(self.mode, rank_kind)
        self._topbar(f"{subject_label(self.mode)}{rank_label}挑战", self.show_mode_select)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 26))
        progress = read_rank_progress()
        subject_info = (progress.get("subjects") or {}).get(progress_key, {})
        highest = int(subject_info.get("highest") or 0)

        left = tk.Frame(frame, bg="#111725")
        left.pack(side="left", fill="y", padx=(0, 18))
        right = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="选择段位", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(6, 12))
        for index, rank in enumerate(RANK_CHALLENGES):
            passed = rank["id"] <= highest
            accent = "#9ff2b2" if passed else "#9fb7ff"
            label = f"{'◆ ' if passed else ''}{rank['name']}"
            HoverButton(left, label, lambda rank_id=rank["id"]: self.start_rank_challenge(rank_id), width=270, height=28, accent=accent).pack(anchor="w", pady=1)

        tk.Label(right, text=f"{subject_label(self.mode)}{rank_label}", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).pack(anchor="w", padx=30, pady=(26, 10))
        intro = "首字母题挑战，普通/困难可能带掩码。" if rank_kind == "free" else "线索题挑战：不显示首字母，提示会逐步追加线索。"
        tk.Label(right, text=intro, fg="#dce6ff", bg="#182033", justify="left", anchor="w", wraplength=760, font=("Microsoft YaHei UI", 11)).pack(anchor="w", fill="x", padx=30, pady=(0, 8))
        tk.Label(right, text=f"当前最高段位：Class {highest:02d}" if highest else "当前还没有通过段位。", fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=30, pady=(0, 18))
        for rank in RANK_CHALLENGES:
            req_text = "、".join(f"{difficulty}≥{target:g}" for difficulty, target in rank["requirements"])
            score = rank_pass_score(subject_info, rank["id"])
            state = f"已通过｜最高总分 {score}" if score is not None else ("已通过" if rank["id"] <= highest else "未通过")
            color = "#9ff2b2" if rank["id"] <= highest else "#9ca8c7"
            hint_text = f"提示冷却 {rank_hint_cooldown_seconds(rank['id'])} 秒｜最多 {rank_hint_limit(rank['id'])} 次"
            line = f"{rank['name']}    {format_rank_time(rank['seconds'])}    {len(rank['requirements'])} 题    {state}    {hint_text}\n{req_text}"
            tk.Label(right, text=line, fg=color, bg="#182033", justify="left", anchor="w", wraplength=820, font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", fill="x", padx=30, pady=3)

    def start_rank_challenge(self, rank_id):
        rank = rank_by_id(rank_id)
        self.custom_mode = False
        self.rank_mode = True
        self.rank_kind = "clue" if getattr(self, "rank_kind", "free") == "clue" else "free"
        self.rank_subject = self.mode
        self.rank_id = rank["id"]
        self.rank_requirements = list(rank["requirements"])
        self.rank_question_index = 0
        self.rank_session_id = uuid.uuid4().hex
        self.rank_relaxed = False
        self.rank_target_difficulty = 0.0
        self.rank_hint_used = 0
        self.rank_session_score = 0
        self.play_mode = "线索段位" if self.rank_kind == "clue" else "自由段位"
        self.difficulty = self.rank_requirements[0][0]
        self.timed_deadline = time.perf_counter() + rank["seconds"]
        self.timed_correct = 0
        self.timed_score = 0
        self.start_round()

    def show_difficulty(self):
        self.clear()
        self._start_backdrop("particles")
        title = f"{self.mode} / {self.play_mode}" if self.play_mode != "真·随机" else "真·随机"
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
        if self.play_mode != "真·随机":
            options.append(("混合模式", "#9fb7ff"))
        for text, accent in options:
            HoverButton(
                left,
                text,
                lambda d=text: self.start_game(d),
                width=250,
                height=66,
                accent=accent,
            ).pack(anchor="w", pady=9)
        self.render_difficulty_explanation(right, options)

    def render_difficulty_explanation(self, parent, options):
        subject = "全部物理和数学词库" if self.play_mode == "真·随机" else ("物理词库" if self.mode == "物理模式" else "数学词库")
        if self.play_mode == "限时":
            mode_text = "限时 5 分钟，答对后自动换题。"
        elif self.play_mode == "线索":
            mode_text = "不显示首字母，改用五句递进线索作答；每次追加线索都会按规则处理。"
        elif self.play_mode == "真·随机":
            mode_text = "从所有现有词库中抽题，不提供混合难度按钮。"
        else:
            mode_text = "单题练习，答完后进入结算。"
        tk.Label(parent, text="词库介绍", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=26, pady=(26, 12))
        tk.Label(parent, text=f"范围：{subject}", fg="#dce6ff", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=26, pady=5)
        tk.Label(parent, text=self.smart_wrap_text(mode_text, 30), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 12)).pack(anchor="w", padx=26, pady=5)
        tk.Label(parent, text="难度说明", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 8))
        descriptions = {
            "入门": "偏高中与基础词，低难高概率，免费提示更慷慨。",
            "简单": "偏核心基础概念，难度 3-4 高概率。",
            "普通": "偏大学基础和常见进阶概念，难度 5-6 高概率；首字母题可能出现 *，线索题可能出现破碎线索。",
            "困难": "偏高阶词库和更难想到的概念，难度 8-10 占比高，掩码或破碎线索概率更高。",
            "混合模式": "读取当前学科下全部难度文件，词条难度均匀抽取。",
        }
        for text, _accent in options:
            tk.Label(parent, text=self.smart_wrap_text(f"{text}：{descriptions[text]}", 32), fg="#c8d2ee", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11)).pack(anchor="w", padx=26, pady=4)

    def start_game(self, difficulty):
        self.custom_mode = False
        self.rank_mode = False
        self.custom_config = {}
        self.difficulty = difficulty
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
        self.complete_achievement("entered_game")
        self.start_round()

    def load_terms_for_current_selection(self, difficulty):
        if self.play_mode == "真·随机":
            self.terms, self.library_files = self.library.load_all()
            self.scope_text = f"全部物理和数学词库：{self.library.scope_text(self.library_files)}"
        else:
            self.terms, self.library_files = self.library.load(self.mode, difficulty)
            self.scope_text = self.library.scope_text(self.library_files)
        if not self.terms:
            raise ValueError("词库为空")

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
        return bool(self.custom_config.get("timed_enabled")) or self.custom_config.get("play_kind") == "限时首字母"

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
        if self.difficulty == "困难":
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
        self.clue_visible_count = 1

    def automatic_mask_difficulty(self):
        if self.current and self.current.difficulty >= 8:
            return "困难"
        if self.current and self.current.difficulty >= 5:
            return "普通"
        return "入门"

    def custom_mask_positions(self):
        setting = self.custom_config.get("mask", "自动")
        if setting == "自动":
            return random_mask_positions(self.current.initials, self.automatic_mask_difficulty())
        try:
            count = int(setting)
        except (TypeError, ValueError):
            count = 0
        count = max(0, min(3, count, len(self.current.initials)))
        if count <= 0:
            return []
        return sorted(random.sample(range(len(self.current.initials)), count))

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
        if difficulty not in {"普通", "困难"}:
            return 0
        return min(3, len(term.initials))

    def max_rank_extra_count(self, term, difficulty):
        if self.rank_kind == "clue":
            return 5 if difficulty in {"普通", "困难"} else 0
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
            self.current = random.choice(self.terms)
        else:
            self.current = choose_daily_term_by_difficulty(self.terms, self.difficulty, self.daily_term_bucket_key())
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
        self.revealed_positions = set()
        self.hint_lines = []
        self.hint_penalties = []
        if self.is_clue_mode():
            self.free_hint_quota = 0
        elif self.custom_mode:
            self.free_hint_quota = self.custom_free_hint_quota()
        else:
            self.free_hint_quota = random_free_hint_quota(len(self.current.chinese), self.difficulty)
        self.free_hint_count = 0
        self.paid_hint_count = 0
        self.attempts = []
        self.score_penalty = 0
        self.library_hint_used = False
        self.library_hint_text = ""
        self.hint_button = None
        self.clue_box = None
        self.hint_cooldown_until = 0.0
        self.initial_input_warnings = 0
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
        elif self.play_mode == "真·随机":
            title = f"真·随机 / {self.difficulty}"
        else:
            title = f"{self.mode} / {self.difficulty}"
        if self.rank_mode:
            back_command = lambda: self.abandon_game(self.show_rank_select)
        elif self.custom_mode:
            back_command = lambda: self.abandon_game(self.show_custom_config)
        else:
            back_command = lambda: self.abandon_game(self.show_difficulty_for_current_mode)
        self._topbar(title, back_command)
        root = tk.Frame(self.container, bg="#111725")
        root.pack(fill="both", expand=True, padx=36, pady=24)
        self._start_backdrop("wind", root)

        if self.is_clue_mode():
            panel_width = min(880, max(640, int(self.winfo_width() * 0.62)))
        else:
            panel_width = min(760, max(560, int(self.winfo_width() * 0.56)))
        panel = tk.Frame(root, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(side="left", fill="both", expand=False, padx=(0, 22))
        panel.configure(width=panel_width)
        panel.pack_propagate(False)

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
                text=f"基础难度 {self.current.difficulty} / 10    本题总难度 {self.effective_difficulty:g}",
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
                text=f"基础难度 {self.current.difficulty} / 10    本题总难度 {self.effective_difficulty:g}",
                fg="#f6d36b",
                bg="#182033",
                font=("Microsoft YaHei UI", 14, "bold"),
            ).pack(anchor="w", padx=48, pady=(0, 18))
            tk.Label(
                panel,
                text=f"本局前 {self.free_hint_quota} 次字词提示免费，提示冷却 {self.hint_cooldown_seconds()} 秒",
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
        self.feedback.pack(fill="x", padx=54, pady=18)

        buttons = tk.Frame(panel, bg="#182033")
        buttons.pack(pady=6)
        button_width = 150 if self.can_reveal_answer() else 170
        HoverButton(buttons, "确认", self.check_answer, width=button_width, height=58, accent="#9ff2b2").grid(row=0, column=0, padx=10)
        self.hint_button = HoverButton(buttons, "提示", self.show_hint, width=button_width, height=58, accent="#f6d36b")
        self.hint_button.grid(row=0, column=1, padx=10)
        if self.can_reveal_answer():
            HoverButton(buttons, "揭晓答案", self.reveal_answer, width=button_width, height=58, accent="#ff9b89").grid(row=0, column=2, padx=10)

        if self.is_clue_mode():
            if self.clue_visible_count >= len(self.clue_lines):
                self.hint_button.disable("无")
        else:
            self.hint_box = tk.Frame(panel, bg="#182033")
            self.hint_box.pack(fill="x", padx=54, pady=22)
            self._render_hints()
        self.start_hint_cooldown()

        side = tk.Frame(root, bg="#111725")
        side.pack(side="left", fill="y")
        tk.Label(side, text="剩余" if self.is_timed_mode() else "计时", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        self.timer_label = tk.Label(side, text="0.0 秒", fg="#fff2bd", bg="#111725", font=("Consolas", 28, "bold"))
        self.timer_label.pack(anchor="w", pady=(4, 14))
        if self.is_timed_mode() or self.is_custom_challenge_mode():
            if self.rank_mode:
                label = "线索段位题" if self.rank_kind == "clue" else "自由段位题"
                status_text = (
                    f"{label} {self.rank_question_index + 1}/{len(self.rank_requirements)}\n"
                    f"已答对 {self.timed_correct} 题\n"
                    f"总分 {self.rank_session_score}｜提示 {self.rank_hint_used}/{rank_hint_limit(self.rank_id)}"
                )
            elif self.custom_mode:
                status_text = self.custom_status_text()
            else:
                status_text = f"已答对 {self.timed_correct} 题\n计入 {format_score(self.timed_score)} 分"
            self.timed_status_label = tk.Label(
                side,
                text=status_text,
                fg="#c8d2ee",
                bg="#111725",
                justify="left",
                font=("Microsoft YaHei UI", 11, "bold"),
            )
            self.timed_status_label.pack(anchor="w", pady=(0, 18))
        tk.Label(side, text="积分", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        self.score_label = tk.Label(side, text="1000 分", fg="#9ff2b2", bg="#111725", font=("Consolas", 24, "bold"))
        self.score_label.pack(anchor="w", pady=(4, 20))
        tk.Label(side, text="词库", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        tk.Label(
            side,
            text=f"{len(self.terms)} 个词条\n{len(self.library_files)} 个文件",
            justify="left",
            fg="#c8d2ee",
            bg="#111725",
            font=("Microsoft YaHei UI", 12),
        ).pack(anchor="w", pady=(4, 24))
        tk.Label(side, text="规则", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        if self.rank_mode:
            if self.rank_kind == "clue":
                rule_text = "线索段位必须在限时内全题答对。\n普通错误提交不会立刻失败，可以继续作答。\n提示会追加线索；主动揭晓、时间到、中途退出或作弊都会导致挑战失败。\n线索段位题不计总积分和 Rating。"
            else:
                rule_text = "自由段位必须在限时内全题答对。\n普通错误提交不会立刻失败，可以继续作答。\n时间到、揭晓、提示揭完、中途退出或作弊都会导致挑战失败。\n自由段位题不计总积分和 Rating。"
        elif self.custom_mode:
            if self.is_custom_challenge_mode():
                rule_text = (
                    f"自定义挑战需连续完成 {self.custom_challenge_target()} 题。\n"
                    "普通错误提交不会立刻失败，可以继续作答。\n"
                    "揭晓、提示揭完、作弊、中途退出或限时结束都会导致挑战失败。\n"
                    "记录会保存，但不计总积分、Rating、成就和正式段位。"
                )
            elif self.is_custom_timed_enabled():
                rule_text = "自定义限时连续练习。\n答对后自动换题，时间结束后看答对题数。\n记录会保存，但不计总积分、Rating 和成就。"
            else:
                rule_text = "自定义模式是练习沙盒。\n记录会保存，但不计总积分、Rating 和成就。\n你可以在配置页调节词库、词长、提示和掩码。"
        elif self.is_clue_mode():
            rule_text = "本题不显示首字母，但会显示答案字数。\n初始只显示第一句线索。\n第一次提示免费，之后从揭晓第三条线索开始扣分。\n共五条线索，普通/困难可能出现破碎线索。\n揭晓答案会记为未答出。"
        else:
            rule_text = "同首字母的词库内答案都算对。\n普通/困难可能用 * 掩码首字母；* 处不限，只检查未掩码位置。\n输入框若出现完整题面首字母串会被清空并记录。\n当前模式总词库里、但不在本轮范围内的匹配词，才会提示超纲。\n提示揭开全部汉字或主动揭晓答案时，本题失败。"
        tk.Label(
            side,
            text=rule_text,
            justify="left",
            fg="#9ca8c7",
            bg="#111725",
            wraplength=230,
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", pady=(4, 18))
        tk.Label(side, text="范围", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        tk.Label(
            side,
            text=self.scope_text,
            justify="left",
            fg="#c8d2ee",
            bg="#111725",
            wraplength=250,
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", pady=(4, 18))
        self.library_hint_button = HoverButton(side, "提示词库", self.show_library_hint, width=170, height=54, accent="#ffbd7e")
        self.library_hint_button.pack(anchor="w", pady=(0, 8))
        self.library_hint_label = tk.Label(
            side,
            text="",
            justify="left",
            fg="#f6d36b",
            bg="#111725",
            wraplength=250,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.library_hint_label.pack(anchor="w")
        self._tick()

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

    def contains_blocked_initials(self, normalized_answer):
        blocked = self.blocked_initial_sequence()
        return bool(blocked and blocked in normalized_answer)

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
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
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
        self.initial_input_warnings += 1
        self.blocked_initial_input = blocked_text
        self.raw_initial_buffer = ""
        self.raw_initial_last_at = 0.0
        if clear_now:
            self.clear_answer_input(rebuild=True)
        else:
            self.after_idle(lambda: self.clear_answer_input(rebuild=True))
        if self.initial_input_warnings == 1:
            self.complete_achievement("first_initial_block")
            if self.feedback:
                self.feedback.config(text="题面首字母已清空。再试一次就判作弊。", fg="#f6d36b")
            self.after_idle(lambda: messagebox.showwarning("输入已拦截", "不要把题面首字母喂给输入法。\n已为你清空；再尝试一次，本题直接判作弊。"))
            return
        self.cheat_pending = True
        self.after_idle(lambda blocked=blocked_text: self.cheat_game(blocked))

    @staticmethod
    def normalize_key_event(event):
        char = getattr(event, "char", "") or ""
        normalized = BonusGuessApp.normalize_initial_input(char)
        if normalized:
            return normalized
        keysym = str(getattr(event, "keysym", "") or "")
        if len(keysym) == 1:
            normalized = BonusGuessApp.normalize_initial_input(keysym)
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
        self.anti_cheat_poll_job = self.after(45, self.poll_anti_cheat_input)

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
            self.feedback.config(text="先写一个答案吧。", fg="#f6d36b")
            return

        answer_initials = self._lookup_initials(answer)
        attempt = {
            "answer": answer,
            "answer_initials": answer_initials,
            "time_seconds": round(time.perf_counter() - self.start_time, 3),
        }

        if answer in self.accepted_answers:
            attempt["result"] = "success"
            self.attempts.append(attempt)
            self.finish_game(True)
        elif self.is_clue_mode():
            attempt["result"] = "wrong"
            self.attempts.append(attempt)
            self.feedback.config(text="还不对，顺着线索再想想。", fg="#ff9b89")
        elif self.initials_match_question(answer_initials):
            attempt["result"] = "out_of_scope"
            self.attempts.append(attempt)
            self.feedback.config(text="超纲啦，再想想~", fg="#f6d36b")
        else:
            attempt["result"] = "wrong"
            self.attempts.append(attempt)
            self.feedback.config(text="还不对，换个词试试。", fg="#ff9b89")

    def current_score(self, elapsed=None):
        if elapsed is None:
            elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        return 1000 - int(elapsed) - self.score_penalty

    def current_score_weight(self):
        if self.custom_mode or self.rank_mode:
            return 0.0
        if self.play_mode == "真·随机":
            return 0.25
        return score_weight_for_difficulty(self.difficulty)

    def difficulty_penalty_factor(self):
        difficulty = self.effective_difficulty if self.current else 5
        return 1.18 - 0.045 * difficulty

    def library_hint_cost(self):
        return max(90, round(210 * self.difficulty_penalty_factor()))

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
            "混合模式": 230,
        }.get(self.difficulty or "", 230)
        difficulty_bonus = max(0, self.effective_difficulty - 1) * 18
        paid_order = hint_number - 1
        return round(mode_base + difficulty_bonus + 70 * max(0, paid_order - 1))

    def hint_cooldown_seconds(self):
        if self.rank_mode:
            return rank_hint_cooldown_seconds(self.rank_id)
        return HINT_COOLDOWN_SECONDS.get(self.difficulty or "", HINT_COOLDOWN_SECONDS["混合模式"])

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

    def start_hint_cooldown(self):
        seconds = self.hint_cooldown_seconds()
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
        remaining = self.hint_cooldown_remaining()
        if remaining > 0:
            self.hint_button.disable(str(remaining))
            self.hint_cooldown_job = self.after(250, self.update_hint_cooldown_button)
        else:
            self.hint_button.enable("提示")

    def add_score_penalty(self, amount):
        self.score_penalty += amount
        self.update_score_label()

    def update_score_label(self):
        if self.score_label:
            score = self.current_score()
            color = "#ff9b89" if score < 0 else "#9ff2b2"
            self.score_label.config(text=f"{score} 分", fg=color)

    def show_library_hint(self):
        if self.library_hint_used:
            return
        self.library_hint_used = True
        self.library_hint_text = f"这个词属于：{self.current.source_label}"
        cost = self.library_hint_cost()
        self.add_score_penalty(cost)
        self.hint_penalties.append({"type": "library", "cost": cost})
        if self.library_hint_button:
            self.library_hint_button.disable("已提示")
        if self.library_hint_label:
            self.library_hint_label.config(text=f"{self.library_hint_text}\n-{cost} 分")

    def _lookup_initials(self, answer):
        for term in self.terms:
            if term.chinese == answer:
                return term.initials
        lookup_mode = None if self.play_mode == "真·随机" or self.custom_mode else self.mode
        return self.library.lookup_initials(answer, lookup_mode)

    def show_clue_hint(self):
        if self.clue_visible_count >= len(self.clue_lines):
            if self.feedback:
                self.feedback.config(text="五条线索已经全部显示。", fg="#9ca8c7")
            if self.hint_button:
                self.hint_button.disable("无")
            return False
        hint_number = self.clue_visible_count
        self.clue_visible_count += 1
        cost = self.clue_hint_cost(hint_number)
        if cost > 0:
            self.add_score_penalty(cost)
            self.paid_hint_count += 1
        else:
            self.free_hint_count += 1
        line = self.clue_lines[self.clue_visible_count - 1]
        line_type = self.clue_line_types[self.clue_visible_count - 1] if self.clue_visible_count - 1 < len(self.clue_line_types) else "complete"
        cost_text = f"-{cost} 分" if cost > 0 else "免费"
        self.hint_lines.append(f"线索提示 {hint_number}：{line}    {cost_text}")
        self.hint_penalties.append({
            "type": "clue" if cost > 0 else "free_clue",
            "line_index": self.clue_visible_count,
            "line_type": line_type,
            "cost": cost,
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
                self.feedback.config(text="本段位的提示次数已经用完。", fg="#f6d36b")
            self.update_hint_cooldown_button()
            return
        if self.is_clue_mode():
            if self.show_clue_hint():
                self.note_hint_used()
                self.start_hint_cooldown()
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

    def _render_hints(self):
        for child in self.hint_box.winfo_children():
            child.destroy()
        if not self.hint_lines:
            text = "提示会出现在这里。"
            if self.free_hint_quota:
                text = f"提示会出现在这里。本局前 {self.free_hint_quota} 次字词提示免费；每次提示后冷却 {self.hint_cooldown_seconds()} 秒。"
            tk.Label(self.hint_box, text=text, fg="#64708f", bg="#182033", font=("Microsoft YaHei UI", 11)).pack(anchor="w")
            return
        for line in self.hint_lines:
            render_inline_markdown(
                self.hint_box,
                line,
                fg="#dce6ff",
                bg="#182033",
                base_size=12,
                wrap_chars=74,
                pady=3,
            )

    def _render_clues(self):
        if not self.clue_box:
            return
        for child in self.clue_box.winfo_children():
            child.destroy()
        for index, line in enumerate(self.clue_lines[:self.clue_visible_count], 1):
            line_type = self.clue_line_types[index - 1] if index - 1 < len(self.clue_line_types) else "complete"
            prefix = "破碎" if line_type == "fragment" else "线索"
            fg = "#f6d36b" if line_type == "fragment" else "#dce6ff"
            render_inline_markdown(
                self.clue_box,
                fg=fg,
                bg="#182033",
                content=f"{index}. **{prefix}**：{line}",
                base_size=13,
                bold=line_type == "fragment",
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
                fg="#9ca8c7",
                bg="#182033",
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
        final_score = self.current_score(elapsed) if success else 0
        weighted_score = final_score * self.current_score_weight()
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
            self.show_rank_result(False, reason="自由段位题未答出" if self.rank_kind == "free" else "线索段位题未答出", elapsed=elapsed, record_path=record_path)
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
        self.feedback.config(text=f"答对啦！用时 {elapsed:.1f} 秒", fg="#9ff2b2")
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
            self.show_rank_result(False, reason="你作弊了", elapsed=elapsed, record_path=record_path, cheated=True)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason="你作弊了", elapsed=elapsed, record_path=record_path, cheated=True)
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
            record_path = self.save_record(False, elapsed, "abandoned")
            self.record_saved = True
            if self.is_custom_challenge_mode():
                self.game_active = False
                self.show_custom_challenge_result(False, reason="自定义挑战中断", elapsed=elapsed, record_path=record_path)
                return
        self.game_active = False
        next_screen()

    def show_result(self, elapsed, record_path, success=True, failed_reason="", cheated=False):
        self.clear(transition=False)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.74, relheight=0.76)
        if cheated:
            final_score = -abs(int(self.cheat_info.get("normal_score", self.current_score(elapsed))))
        else:
            final_score = self.current_score(elapsed) if success else 0
        score_weight = self.current_score_weight()
        weighted_score = final_score * score_weight
        score_color = "#ff9b89" if final_score < 0 else "#9ff2b2"
        if cheated:
            title = "你作弊了"
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
        tk.Label(detail_frame, text=f"本轮答案：{self.current.chinese}", fg="#c8d2ee", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 14)).pack(anchor="w", fill="x", pady=4)
        if self.is_clue_mode():
            tk.Label(detail_frame, text="本轮线索", fg="#8fb6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", pady=(8, 3))
            for index, line in enumerate(self.clue_lines[:self.clue_visible_count], 1):
                line_type = self.clue_line_types[index - 1] if index - 1 < len(self.clue_line_types) else "complete"
                prefix = "破碎" if line_type == "fragment" else "线索"
                fg = "#f6d36b" if line_type == "fragment" else "#dce6ff"
                render_inline_markdown(
                    detail_frame,
                    f"{index}. **{prefix}**：{line}",
                    fg=fg,
                    bg="#182033",
                    base_size=10,
                    bold=line_type == "fragment",
                    wrap_chars=82,
                    pady=(0, 3),
                )
        else:
            answer_title = "本词库同首字母可接受解"
            if self.mask_count:
                answer_title = "本词库匹配当前掩码的可接受解"
            tk.Label(detail_frame, text=answer_title, fg="#8fb6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", pady=(10, 3))
            answer_box = tk.Text(
                detail_frame,
                height=3,
                wrap="char",
                fg="#dce6ff",
                bg="#111827",
                insertbackground="#dce6ff",
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground="#30384e",
                font=("Microsoft YaHei UI", 11),
            )
            answer_box.pack(fill="x", pady=(0, 8))
            answer_box.insert("1.0", "、".join(self.accepted_answers))
            answer_box.config(state="disabled")
        try:
            record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
        except ValueError:
            record_display = f"record/{record_path.name}"
        tk.Label(detail_frame, text=f"记录已保存：{record_display}", fg="#7683a3", bg="#182033", justify="left", anchor="w", wraplength=760, font=("Microsoft YaHei UI", 10)).pack(anchor="w", fill="x", pady=(4, 18))
        buttons = tk.Frame(card, bg="#182033")
        buttons.pack()
        if self.custom_mode:
            HoverButton(buttons, "再练一局", self.restart_custom_session, width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回配置", self.show_custom_config, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)
        else:
            HoverButton(buttons, "再来一局", lambda: self.start_game(self.difficulty), width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回模式", self.show_mode_select, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)

    def show_custom_challenge_result(self, passed, reason="", elapsed=None, record_path=None, cheated=False):
        self.clear(transition=False)
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.66)
        if cheated:
            title = "你作弊了"
            title_color = "#ff6b8a"
        else:
            title = "自定义挑战成功" if passed else "自定义挑战失败"
            title_color = "#9ff2b2" if passed else "#ff9b89"
        target = self.custom_challenge_target()
        tk.Label(card, text=title, fg=title_color, bg="#182033", font=("Microsoft YaHei UI", 36, "bold")).pack(pady=(48, 10))
        tk.Label(card, text=f"进度 {self.timed_correct}/{target} 题", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).pack(pady=6)
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

    def show_timed_result(self):
        self.clear()
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.68, relheight=0.62)
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
        self.start_round()

    def show_rank_result(self, passed, reason="", elapsed=None, record_path=None, cheated=False):
        self.clear(transition=False)
        self.game_active = False
        self.record_saved = True
        self.start_time = None
        rank = rank_by_id(self.rank_id)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.68)
        if cheated:
            title = "你作弊了"
            title_color = "#ff6b8a"
        else:
            label = "线索段位" if self.rank_kind == "clue" else "自由段位"
            title = f"{label}通过" if passed else f"{label}失败"
            title_color = "#9ff2b2" if passed else "#ff9b89"
        tk.Label(card, text=title, fg=title_color, bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(40, 8))
        tk.Label(card, text=f"{subject_label(self.rank_subject)}{rank_kind_label(self.rank_kind)} / {rank['name']}", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 19, "bold")).pack(pady=4)
        if reason:
            tk.Label(card, text=reason, fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(2, 8))
        tk.Label(
            card,
            text=f"进度 {self.timed_correct}/{len(self.rank_requirements)} 题    总分 {self.rank_session_score}    时限 {format_rank_time(rank['seconds'])}",
            fg="#c8d2ee",
            bg="#182033",
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(pady=6)
        if elapsed is not None:
            tk.Label(card, text=f"本题用时 {elapsed:.1f} 秒", fg="#9ca8c7", bg="#182033", font=("Consolas", 14, "bold")).pack(pady=2)
        if passed:
            badge_id = rank_badge_id(self.rank_subject, self.rank_id, self.rank_kind)
            badge_canvas = tk.Canvas(card, width=230, height=46, bd=0, highlightthickness=0, bg="#182033")
            badge_canvas.pack(pady=(14, 8))
            draw_rank_badge(badge_canvas, badge_id, 230, 46, selected=True)
            tk.Label(card, text=f"已解锁：{rank_badge_name(badge_id)}", fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(pady=(0, 10))
        else:
            req_text = "、".join(f"{difficulty}≥{target:g}" for difficulty, target in self.rank_requirements)
            tk.Label(card, text=f"本段题组：{req_text}", fg="#9ca8c7", bg="#182033", wraplength=760, justify="left", font=("Microsoft YaHei UI", 11)).pack(padx=64, pady=(12, 10))
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

    def save_record(self, success, elapsed, finished_by="answered", failed_reason=""):
        now = datetime.now()
        storage_dir = record_storage_dir(now)
        storage_dir.mkdir(parents=True, exist_ok=True)
        is_custom = bool(self.custom_mode)
        is_rank = bool(self.rank_mode)
        final_score = self.current_score(elapsed)
        if finished_by == "cheated":
            final_score = -abs(final_score)
        elif not success and finished_by != "abandoned":
            final_score = 0
        score_weight = self.current_score_weight()
        subject_value = self.rank_subject if is_rank else (self.custom_config.get("subject", self.mode) if is_custom else self.mode)
        mode_value = self.rank_subject if is_rank else ("自定义" if is_custom else self.mode)
        play_value = ("线索段位" if self.rank_kind == "clue" else "自由段位") if is_rank else ("自定义" if is_custom else self.play_mode)
        try:
            custom_files = [path.relative_to(WORDS_DIR).as_posix() for path in self.library_files]
        except ValueError:
            custom_files = [path.name for path in self.library_files]
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
            "exclude_from_stats": 1 if (is_custom or is_rank) else 0,
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
            "clue_hint_count": max(0, self.clue_visible_count - 1) if self.is_clue_mode() else 0,
            "clue_penalty": sum(item.get("cost", 0) for item in self.hint_penalties if item.get("type") == "clue"),
            "selected_answer": self.current.chinese,
            "base_term_difficulty": self.current.difficulty,
            "term_difficulty": self.current.difficulty,
            "effective_difficulty": self.effective_difficulty,
            "accepted_answers": self.accepted_answers,
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
        path = storage_dir / f"{now.strftime('%Y%m%d_%H%M%S')}_{record['id'][:8]}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        self.refresh_achievements()
        return path

    def on_close(self):
        if self.game_active and not self.record_saved and self.start_time and self.current:
            elapsed = time.perf_counter() - self.start_time
            self.save_record(False, elapsed, "abandoned")
            self.record_saved = True
        self.destroy()

    def complete_achievement(self, achievement_id, when=None):
        self.achievements = read_achievements()
        completed = self.achievements.setdefault("completed", {})
        if achievement_id in completed:
            return
        completed[achievement_id] = (when or datetime.now()).isoformat(timespec="seconds")
        write_achievements(self.achievements)

    def refresh_achievements(self):
        self.achievements = read_achievements()
        completed = self.achievements.setdefault("completed", {})

        def mark(achievement_id, record=None):
            if achievement_id in completed:
                return
            when = record_datetime(record) if record else datetime.now()
            completed[achievement_id] = when.isoformat(timespec="seconds")

        all_records = load_record_entries()
        abandoned_records = [record for record in all_records if is_abandoned_record(record)]
        records = [record for record in all_records if is_counted_record(record)]
        records.sort(key=record_datetime)
        abandoned_records.sort(key=record_datetime)
        streak = 0
        total_score = 0
        total_time = 0
        total_success = 0
        total_char_hints = 0
        total_library_hints = 0
        total_hard_success = 0
        total_difficulty_ten_success = 0
        total_effective_over_10_success = 0
        total_effective_over_11_success = 0
        total_masked_success = 0
        total_timed_success = 0
        total_timed_time = 0
        total_cheats = 0
        if len(abandoned_records) >= 10:
            mark("exit_ten", abandoned_records[9])
        if len(abandoned_records) >= 100:
            mark("exit_hundred", abandoned_records[99])
        for index, record in enumerate(records, 1):
            success = bool(record.get("success"))
            score = record_score(record)
            char_hints = record_hint_count(record)
            library_hints = record_library_hint_count(record)
            total_score += record_weighted_score(record)
            total_time += float(record.get("elapsed_seconds") or 0)
            total_char_hints += char_hints
            total_library_hints += library_hints
            mask_count = int(record.get("mask_count") or 0)
            effective_difficulty = record_effective_difficulty(record)
            is_timed = record_play_mode(record) == "限时" or bool(record.get("timed_session"))
            is_cheat = bool(record.get("cheat_detected")) or record.get("finished_by") == "cheated"
            if mask_count:
                mark("first_masked_round", record)
            if is_timed:
                total_timed_time += float(record.get("elapsed_seconds") or 0)
            if is_cheat:
                total_cheats += 1
                mark("first_cheat", record)
                if is_timed:
                    mark("timed_cheat", record)

            if success:
                total_success += 1
                streak += 1
                mark("first_success", record)
                if mask_count:
                    total_masked_success += 1
                    mark("first_masked_success", record)
                    if mask_count >= 3:
                        mark("three_mask_success", record)
                if is_timed:
                    total_timed_success += 1
                    mark("first_timed_success", record)
                if char_hints == 0 and library_hints == 0:
                    mark("no_hint_success", record)
                if float(record.get("elapsed_seconds") or 0) <= 10:
                    mark("quick_success", record)
                if float(record.get("elapsed_seconds") or 0) > 180:
                    mark("slow_success", record)
                if effective_difficulty >= 8:
                    total_hard_success += 1
                    mark("hard_success", record)
                if effective_difficulty >= 10:
                    total_difficulty_ten_success += 1
                    mark("difficulty_ten_success", record)
                if effective_difficulty > 10:
                    total_effective_over_10_success += 1
                    mark("effective_over_10_success", record)
                if effective_difficulty > 11:
                    total_effective_over_11_success += 1
                    mark("effective_over_11_success", record)
                if score >= 900:
                    mark("score_guard", record)
            else:
                streak = 0

            if char_hints >= 3:
                mark("three_hints_one_round", record)
            if score < 0:
                mark("negative_score", record)
            if any((attempt.get("result") == "out_of_scope") for attempt in record.get("all_answers") or []):
                mark("first_out_of_scope", record)
            if streak >= 5:
                mark("streak_five", record)
            if streak >= 10:
                mark("streak_ten", record)
            if total_score >= 5000:
                mark("total_score_5000", record)
            if total_score >= 20000:
                mark("total_score_20000", record)
            if total_score >= 100000:
                mark("total_score_100000", record)
            if total_score >= 500000:
                mark("total_score_500000", record)
            if total_char_hints >= 50:
                mark("fifty_char_hints", record)
            if total_char_hints >= 500:
                mark("five_hundred_char_hints", record)
            if total_library_hints >= 20:
                mark("twenty_library_hints", record)
            if total_library_hints >= 200:
                mark("two_hundred_library_hints", record)
            if total_time >= 10 * 3600:
                mark("play_time_10h", record)
            if total_time >= 30 * 3600:
                mark("play_time_30h", record)
            if total_time >= 100 * 3600:
                mark("play_time_100h", record)
            if total_success >= 500:
                mark("success_500", record)
            if total_hard_success >= 100:
                mark("hard_success_100", record)
            if total_difficulty_ten_success >= 30:
                mark("difficulty_ten_success_30", record)
            if total_effective_over_10_success >= 20:
                mark("effective_over_10_success_20", record)
            if total_effective_over_11_success >= 5:
                mark("effective_over_11_success_5", record)
            if total_masked_success >= 50:
                mark("masked_success_50", record)
            if total_masked_success >= 300:
                mark("masked_success_300", record)
            if total_timed_success >= 20:
                mark("timed_success_20", record)
            if total_timed_success >= 100:
                mark("timed_success_100", record)
            if total_timed_success >= 500:
                mark("timed_success_500", record)
            if total_timed_time >= 5 * 3600:
                mark("timed_time_5h", record)
            if total_timed_time >= 30 * 3600:
                mark("timed_time_30h", record)
            if total_cheats >= 3:
                mark("cheat_three", record)
            if total_cheats >= 10:
                mark("cheat_ten", record)
            if index >= 50:
                mark("completed_50", record)
            if index >= 200:
                mark("completed_200", record)
            if index >= 500:
                mark("completed_500", record)
            if index >= 1000:
                mark("completed_1000", record)

        write_achievements(self.achievements)

    def show_history(self):
        self.clear()
        self._topbar("历史记录", self.show_home)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self._start_backdrop("particles", frame)

        records = load_record_entries()
        summary = summarize_records(records)
        counted = summary["records"]

        top = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        top.pack(fill="x", pady=(0, 16))
        cards = [
            ("Rating", format_rating(summary["rating"])),
            ("作答Rating", format_rating(summary["play_rating"])),
            ("成就奖励", f"+{summary['achievement_bonus']:.3f}"),
            ("总做题数", f"{summary['total_count']}"),
            ("总用时", format_duration(summary["total_time"])),
            ("总积分", format_score(summary["total_score"])),
            ("中途退出", f"{summary['abandoned_count']}"),
            ("作弊判定", f"{summary['cheat_count']}"),
            ("字词/线索提示", f"{summary['char_hints']}"),
            ("提示词库", f"{summary['library_hints']}"),
        ]
        for index, (name, value) in enumerate(cards):
            cell = tk.Frame(top, bg="#182033")
            row = index // 4
            column = index % 4
            cell.grid(row=row, column=column, sticky="ew", padx=18, pady=10)
            top.grid_columnconfigure(column, weight=1)
            tk.Label(cell, text=name, fg="#8fb6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", fill="x")
            tk.Label(cell, text=value, fg="#fff2bd", bg="#182033", justify="left", anchor="w", font=("Consolas", 18, "bold")).pack(anchor="w", fill="x", pady=(3, 0))

        dist = tk.Frame(frame, bg="#111725")
        dist.pack(fill="x", pady=(0, 12))
        term_parts = [f"{i}:{summary['difficulty_counts'].get(i, 0)}" for i in range(1, 11)]
        if summary["difficulty_counts"].get(0, 0):
            term_parts.append(f"未知:{summary['difficulty_counts'].get(0, 0)}")
        term_text = "  ".join(term_parts)
        mode_order = ["入门", "简单", "普通", "困难", "混合模式", "未知"]
        mode_text = "  ".join(f"{name}:{summary['mode_counts'].get(name, 0)}" for name in mode_order if summary["mode_counts"].get(name, 0) or name != "未知")
        tk.Label(dist, text=f"词条难度分布  {term_text}", fg="#c8d2ee", bg="#111725", font=("Microsoft YaHei UI", 11)).pack(anchor="w")
        tk.Label(dist, text=f"选词难度分布  {mode_text}", fg="#c8d2ee", bg="#111725", font=("Microsoft YaHei UI", 11)).pack(anchor="w", pady=(4, 0))

        detail_button_text = "收起详情" if self.history_show_details else "详情"
        HoverButton(frame, detail_button_text, self.toggle_history_details, width=130, height=46, accent="#8fb6ff").pack(anchor="w", pady=(0, 10))
        if self.history_show_details:
            self.render_history_details(frame, summary)

        tk.Label(frame, text="记录列表", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", pady=(4, 8))
        scroll = self.make_scroll_frame(frame)
        if not records:
            tk.Label(scroll, text="还没有历史记录。", fg="#9ca8c7", bg="#111725", font=("Microsoft YaHei UI", 13)).pack(anchor="w", pady=18)
        for record in records:
            self.render_record_row(scroll, record)

    def toggle_history_details(self):
        self.history_show_details = not self.history_show_details
        self.show_history()

    def render_history_details(self, parent, summary):
        box = tk.Frame(parent, bg="#182033", highlightbackground="#30384e", highlightthickness=1)
        box.pack(fill="x", pady=(0, 14))
        total = max(summary["total_count"], 1)
        accuracy = summary["success_count"] / total * 100
        result = summary["answer_results"]
        mode_order = ["入门", "简单", "普通", "困难", "混合模式", "未知"]
        score_parts = [
            f"{name}:{format_score(summary['mode_scores'].get(name, 0))}"
            for name in mode_order
            if summary["mode_scores"].get(name, 0) or summary["mode_counts"].get(name, 0)
        ]
        lines = [
            f"答对 {summary['success_count']} 题，未答对 {summary['wrong_count']} 题，中途退出 {summary['abandoned_count']} 次，正确率 {accuracy:.1f}%",
            f"平均用时 {summary['avg_time']:.1f} 秒，平均计入积分 {summary['avg_score']:.1f} 分，平均原始得分 {summary['avg_raw_score']:.1f} 分",
            f"Rating {format_rating(summary['rating'])}，去重B20均值 {format_rating(summary['rating_best_average'])}，R10均值 {format_rating(summary['rating_recent_average'])}",
            f"最终总积分按入门 0.1、简单 0.2、普通 0.3、困难 0.4、混合模式/真·随机 0.25 加权。原始总分 {summary['raw_total_score']} 分",
            f"字词/线索提示：免费字词 {summary['free_char_hints']}，付费字词或线索 {summary['paid_char_hints']}，总计 {summary['char_hints']}",
            f"各模式计入积分：{'  '.join(score_parts) if score_parts else '暂无'}",
            f"提交答案统计：正确 {result.get('success', 0)}，错误 {result.get('wrong', 0)}，超纲 {result.get('out_of_scope', 0)}",
        ]
        for line in lines:
            tk.Label(box, text=line, fg="#dce6ff", bg="#182033", justify="left", anchor="w", wraplength=1080, font=("Microsoft YaHei UI", 11)).pack(anchor="w", fill="x", padx=16, pady=3)

        dimensions = [
            ("按学科", summary.get("by_subject", {}), ["物理模式", "数学模式", "真·随机", "未知"]),
            ("按玩法", summary.get("by_play_mode", {}), ["自由", "限时", "真·随机", "未知"]),
            ("按选词难度", summary.get("by_difficulty", {}), ["入门", "简单", "普通", "困难", "混合模式", "未知"]),
        ]
        grid = tk.Frame(box, bg="#182033")
        grid.pack(fill="x", padx=12, pady=(10, 12))
        for column, (title, data, order) in enumerate(dimensions):
            panel = tk.Frame(grid, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
            panel.grid(row=0, column=column, sticky="nsew", padx=5)
            grid.grid_columnconfigure(column, weight=1)
            tk.Label(panel, text=title, fg="#8fb6ff", bg="#111827", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
            keys = [key for key in order if key in data]
            keys.extend(key for key in sorted(data, key=str) if key not in keys)
            if not keys:
                tk.Label(panel, text="暂无记录", fg="#64708f", bg="#111827", font=("Microsoft YaHei UI", 10)).pack(anchor="w", padx=12, pady=(0, 10))
            for key in keys:
                item = data[key]
                text = (
                    f"{key}｜{item['total_count']}题 / 对{item['success_count']}｜"
                    f"计入{format_score(item['total_score'])}｜退出{item['abandoned_count']}"
                )
                tk.Label(panel, text=text, fg="#dce6ff", bg="#111827", font=("Microsoft YaHei UI", 9), wraplength=330, justify="left").pack(anchor="w", padx=12, pady=2)

    def render_record_row(self, parent, record):
        row = tk.Frame(parent, bg="#182033", highlightbackground="#30384e", highlightthickness=1)
        row.pack(fill="x", pady=5)
        if is_abandoned_record(record):
            status = "中途退出"
            status_color = "#f6d36b"
        elif record.get("cheat_detected"):
            status = "你作弊了"
            status_color = "#ff6b8a"
        elif record.get("finished_by") == "hint_failure":
            status = "提示失败"
            status_color = "#ff9b89"
        elif record.get("finished_by") == "revealed":
            status = "已揭晓"
            status_color = "#f6d36b"
        elif record.get("success"):
            status = "答对"
            status_color = "#9ff2b2"
        else:
            status = "未答对"
            status_color = "#ff9b89"
        created = (record.get("created_at") or "")[:19].replace("T", " ")
        title = f"{created}    {record_mode(record)} / {record_play_mode(record)} / {record.get('difficulty', '未知')}    {status}"
        tk.Label(row, text=title, fg=status_color, bg="#182033", justify="left", anchor="w", wraplength=1080, font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", padx=14, pady=(9, 2))
        hint_label = "线索提示" if record.get("clue_mode") else "字词提示"
        detail = (
            f"题目 {record.get('displayed_initials') or record.get('question_initials', '')}    答案 {record.get('selected_answer', '')}    "
            f"基础难度 {record_term_difficulty(record) or '未知'} / 总难度 {record_effective_difficulty(record):g}    "
            f"掩码 {int(record.get('mask_count') or 0)}    用时 {float(record.get('elapsed_seconds') or 0):.1f} 秒    "
            f"得分 {record_score(record)} / 计入 {format_score(record_weighted_score(record))}    单局Rating {format_rating(record_single_rating(record))}    "
            f"{hint_label} {record_hint_count(record)}（免费 {record_free_hint_count(record)} / 付费 {record_paid_hint_count(record)}）    "
            f"提示词库 {record_library_hint_count(record)}"
        )
        if record.get("failed_reason"):
            detail += f"    原因 {record.get('failed_reason')}"
        tk.Label(row, text=detail, fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 10), wraplength=1060, justify="left").pack(anchor="w", padx=14, pady=(0, 9))

    def show_achievements(self):
        self.refresh_achievements()
        self.clear()
        self._topbar("成就", self.show_home)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 24))
        self._start_backdrop("constellation", frame)
        completed = self.achievements.get("completed", {})
        completed_count = sum(1 for achievement_id, _title, _description in ACHIEVEMENTS if achievement_id in completed)
        tk.Label(
            frame,
            text=f"已完成 {completed_count} / {len(ACHIEVEMENTS)}",
            fg="#fff2bd",
            bg="#111725",
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 14))
        scroll = self.make_scroll_frame(frame)
        achievement_lookup = {achievement_id: (title, description) for achievement_id, title, description in ACHIEVEMENTS}
        used_ids = set()
        for category_title, achievement_ids in ACHIEVEMENT_CATEGORIES:
            visible_ids = [achievement_id for achievement_id in achievement_ids if achievement_id in achievement_lookup and achievement_id not in HIDDEN_ACHIEVEMENT_IDS]
            used_ids.update(visible_ids)
            self.render_achievement_category(scroll, category_title, visible_ids, achievement_lookup, completed, mysterious=False)

        remaining_ids = [
            achievement_id
            for achievement_id, _title, _description in ACHIEVEMENTS
            if achievement_id not in used_ids and achievement_id not in HIDDEN_ACHIEVEMENT_IDS
        ]
        if remaining_ids:
            self.render_achievement_category(scroll, "其他成就", remaining_ids, achievement_lookup, completed, mysterious=False)

        mystery_ids = [
            achievement_id
            for achievement_id, _title, _description in ACHIEVEMENTS
            if achievement_id in HIDDEN_ACHIEVEMENT_IDS
        ]
        self.render_achievement_category(scroll, "神秘成就", mystery_ids, achievement_lookup, completed, mysterious=True)

    def render_achievement_category(self, parent, title, achievement_ids, achievement_lookup, completed, mysterious=False):
        if not achievement_ids:
            return
        done_count = sum(1 for achievement_id in achievement_ids if achievement_id in completed)
        header = tk.Frame(parent, bg="#111725")
        header.pack(fill="x", pady=(16, 6))
        accent = "#f6a6ff" if mysterious else "#8fb6ff"
        tk.Label(
            header,
            text=f"{title}  {done_count}/{len(achievement_ids)}",
            fg=accent,
            bg="#111725",
            font=("Microsoft YaHei UI", 15, "bold"),
        ).pack(side="left")
        if mysterious:
            tk.Label(
                header,
                text="未完成前不会显示条件",
                fg="#69738d",
                bg="#111725",
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(side="left", padx=14)

        grid = tk.Frame(parent, bg="#111725")
        grid.pack(fill="x")
        for column in range(3):
            grid.grid_columnconfigure(column, weight=1, uniform=f"achievement_{title}")
        for index, achievement_id in enumerate(achievement_ids):
            achievement_title, description = achievement_lookup[achievement_id]
            self.render_achievement_card(
                grid,
                index,
                achievement_id,
                achievement_title,
                description,
                completed,
                hidden_until_complete=mysterious,
            )

    def render_achievement_card(self, parent, index, achievement_id, title, description, completed, hidden_until_complete=False):
        done = achievement_id in completed
        bg = "#1c2033" if hidden_until_complete and not done else "#182033"
        border = "#5b4775" if hidden_until_complete else "#30384e"
        row = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1, width=350, height=116)
        row.grid(row=index // 3, column=index % 3, sticky="nsew", padx=7, pady=7)
        row.grid_propagate(False)
        left = tk.Frame(row, bg=bg)
        left.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=9)
        title_color = "#f6a6ff" if hidden_until_complete and not done else "#fff2bd"
        tk.Label(left, text=title, fg=title_color, bg=bg, font=("Microsoft YaHei UI", 13, "bold"), anchor="w").pack(anchor="w", fill="x")
        detail_text = "？？？" if hidden_until_complete and not done else description
        tk.Label(left, text=detail_text, fg="#9ca8c7", bg=bg, font=("Microsoft YaHei UI", 9), wraplength=210, justify="left").pack(anchor="w", pady=(4, 0))
        status_text = "已完成" if done else "未完成"
        status_color = "#9ff2b2" if done else "#69738d"
        right_text = status_text if not done else f"{status_text}\n{completed[achievement_id].replace('T', ' ')}"
        tk.Label(row, text=right_text, fg=status_color, bg=bg, justify="right", font=("Microsoft YaHei UI", 9, "bold")).pack(side="right", padx=(4, 10), pady=8)

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

    def make_scroll_frame(self, parent, bg="#111725"):
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
        bar = tk.Frame(self.container, bg="#111725")
        bar.pack(fill="x", padx=22, pady=16)
        HoverButton(bar, "返回", back_command, width=110, height=48, accent="#8fb6ff").pack(side="left")
        tk.Label(bar, text=title, fg="#fff2bd", bg="#111725", font=("Microsoft YaHei UI", 19, "bold")).pack(side="left", padx=18)

    def _tick(self):
        if not self.start_time:
            return
        now = time.perf_counter()
        if self.is_timed_mode() and self.timed_deadline:
            remaining = max(0, self.timed_deadline - now)
            self.timer_label.config(text=f"{remaining:.1f} 秒")
            if self.timed_status_label:
                if self.rank_mode:
                    label = "线索段位题" if self.rank_kind == "clue" else "自由段位题"
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



def main():
    app = BonusGuessApp()
    app.mainloop()
