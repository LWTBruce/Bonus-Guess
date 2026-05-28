import json
import math
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
    MASK_PROBABILITIES,
    APP_ICON_FILE,
    PROJECT_DIR,
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
from accounts import (
    AccountError,
    account_paths,
    active_account,
    apply_account_context,
    authenticate,
    change_password,
    clear_active_session,
    create_account,
    ensure_local_bruce_account,
    is_admin_account,
    list_public_accounts,
    rename_account,
    set_active_session,
)
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
from crossword_puzzle import generate_crossword, size_for_difficulty, target_word_count_for_size, validate_crossword
from markdown_view import render_inline_markdown, render_markdown, split_mechanics_sections
from player_profile import DEFAULT_PLAYER_SETTINGS, load_player_settings, save_player_settings
from rank_system import (
    RANK_CHALLENGES,
    coerce_rank_badge_id,
    draw_rank_badge,
    format_rank_time,
    mark_rank_passed,
    normalize_rank_kind,
    parse_rank_badge_id,
    rank_badge_id,
    rank_badge_name,
    rank_by_id,
    rank_hint_cooldown_seconds,
    rank_hint_limit,
    rank_highest_passed,
    rank_kind_label,
    rank_pass_score,
    rank_passed_ids,
    rank_progress_key,
    read_rank_progress,
    split_rank_progress_key,
    subject_label,
    unlocked_rank_badges,
)
from records import (
    ACHIEVEMENTS,
    apply_initial_mask,
    choose_daily_term_by_difficulty,
    choose_term_by_length,
    format_duration,
    format_rating,
    format_score,
    is_abandoned_record,
    is_counted_record,
    is_random_record,
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
from term_library import (
    TermLibrary,
    answers_differ_only_by_person_alias,
    answers_equivalent,
    normalize_term_initials,
    term_has_greek_letter,
    term_notice_text,
)
from widgets import HoverButton, WobblePanel, scaled_int, set_ui_scale


class BonusGuessApp(BackdropMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_account = ensure_local_bruce_account()
        if self.current_account:
            apply_account_context(self.current_account["id"])
        self.player_settings = load_player_settings() if self.current_account else dict(DEFAULT_PLAYER_SETTINGS)
        try:
            self.base_tk_scaling = float(self.tk.call("tk", "scaling"))
        except tk.TclError:
            self.base_tk_scaling = 1.0
        self.apply_ui_font_scale()
        self.title(f"{TITLE_CN} {APP_VERSION}")
        self.apply_window_icon()
        self.geometry(f"{self.player_settings['window_width']}x{self.player_settings['window_height']}")
        self.minsize(936, 598)
        self.configure(bg="#111725")
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        self.library = TermLibrary(WORDS_DIR)
        self.clue_library = ClueLibrary(TERM_CLUES_DIR)
        self.mode = None
        self.play_mode = "自由"
        self.true_random_mode = False
        self.random_group_mode = False
        self.selected_subject = "物理模式"
        self.selected_game_group = "普通"
        self.selected_rule_mode = "自由"
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
        self.initial_warning_until = 0.0
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
        self.admin_show_details = False
        self.spectator_admin_account = None
        self.spectated_account = None
        self.tutorial_active = False
        self.tutorial_manual = False
        self.tutorial_step = 0
        self.tutorial_overlay_widgets = []
        self.tutorial_confirm_button = None
        self.tutorial_question_panel = None
        self.tutorial_hint_button = None
        self.tutorial_library_hint_button = None
        self.switch_return_account = None
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
        self.settings_title_category_var = None
        self.settings_title_search_var = None
        self.settings_title_current_label = None
        self.settings_title_options_frame = None
        self.settings_title_cards = []
        self.login_nickname_var = None
        self.login_password_var = None
        self.register_nickname_var = None
        self.register_password_var = None
        self.register_confirm_var = None
        self.password_old_var = None
        self.password_new_var = None
        self.password_confirm_var = None
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
        self.custom_hint_cooldown_var = None
        self.custom_library_hint_var = None
        self.custom_mask_mode_var = None
        self.custom_mask_fixed_var = None
        self.custom_mask_probability_var = None
        self.custom_mask_max_var = None
        self.custom_clue_initial_var = None
        self.custom_clue_reveal_var = None
        self.custom_crossword_width_var = None
        self.custom_crossword_height_var = None
        self.custom_crossword_words_var = None
        self.custom_crossword_shape_var = None
        self.custom_crossword_triangle_var = None
        self.custom_crossword_hex_var = None
        self.custom_minutes_entries = []
        self.custom_challenge_entries = []
        self.custom_play_frames = {}
        self.custom_summary_label = None
        self.custom_file_listbox = None
        self.custom_session_id = ""
        self.crossword_random = False
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
        self.rank_answer_history = []
        self.crossword_mode = False
        self.crossword_puzzle = None
        self.crossword_canvas = None
        self.crossword_word_listbox = None
        self.crossword_answer_var = None
        self.crossword_feedback = None
        self.crossword_status_label = None
        self.crossword_score_label = None
        self.crossword_timer_label = None
        self.crossword_hint_box = None
        self.crossword_hint_button = None
        self.crossword_library_hint_button = None
        self.crossword_library_hint_label = None
        self.crossword_selected_id = None
        self.crossword_solved_ids = set()
        self.crossword_revealed_cells = set()
        self.crossword_filled_answers = {}
        self.crossword_cell_to_placements = {}
        self.crossword_attempts = []
        self.crossword_free_hint_quota = 0
        self.crossword_free_hint_count = 0
        self.crossword_paid_hint_count = 0
        self.crossword_library_hint_limit = 0
        self.crossword_library_hint_count = 0
        self.crossword_library_hint_texts = []
        self.crossword_hint_lines = []
        self.crossword_hint_penalties = []
        self.crossword_score_penalty = 0
        self.crossword_cheat_warnings = 0
        self.crossword_cheat_pending = False
        self.crossword_raw_initial_buffer = ""
        self.crossword_raw_initial_last_at = 0.0
        self.crossword_session_id = ""
        self.crossword_start_score = 0
        self.crossword_zoom = 1.0
        self.crossword_pan_x = 0.0
        self.crossword_pan_y = 0.0
        self.crossword_drag_start = None
        self.crossword_drag_pan_start = (0.0, 0.0)
        self.crossword_dragged = False
        self.crossword_last_clicked_cell = None
        self.crossword_click_cycle_index = 0
        self.crossword_rank_seconds = 0
        self.crossword_rank_word_count = 0
        self.crossword_rank_size = 0

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.container = tk.Frame(self, bg="#111725")
        self.container.pack(fill="both", expand=True)
        if self.current_account:
            self.complete_achievement("first_launch")
            self.refresh_achievements()
            if self.should_auto_start_tutorial():
                self.start_tutorial(auto=True)
            else:
                self.show_home()
        else:
            self.show_login()

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
        self.apply_ui_font_scale()
        self.achievements = read_achievements()
        self.show_admin_dashboard()

    def should_auto_start_tutorial(self):
        return bool(self.current_account) and not self.is_spectating() and not bool(self.player_settings.get("tutorial_completed", True))

    def save_tutorial_completed(self):
        settings = dict(self.player_settings or DEFAULT_PLAYER_SETTINGS)
        settings["tutorial_completed"] = True
        self.player_settings = save_player_settings(settings)

    def start_tutorial(self, auto=False):
        if self.is_spectating():
            return
        self.tutorial_manual = not auto
        self.tutorial_active = True
        self.tutorial_step = "home"
        self.selected_subject = "物理模式"
        self.selected_game_group = "普通"
        self.selected_rule_mode = "自由"
        self.selected_play_mode = "自由"
        self.mode = "物理模式"
        self.play_mode = "自由"
        self.true_random_mode = False
        self.random_group_mode = False
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

        def add_block(x, y, w, h, color="#070b13"):
            if w <= 0 or h <= 0:
                return
            block = tk.Frame(self.container, bg=color)
            block.place(x=x, y=y, width=w, height=h)
            self.tutorial_overlay_widgets.append(block)

        add_block(0, 0, width, top)
        add_block(0, bottom, width, height - bottom)
        add_block(0, top, left, bottom - top)
        add_block(right, top, width - right, bottom - top)
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
        callout = tk.Frame(self.container, bg="#182033", highlightbackground="#f6d36b", highlightthickness=1)
        self.tutorial_overlay_widgets.append(callout)
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
        callout.place(x=callout_x, y=callout_y, width=callout_width)
        for widget in self.tutorial_overlay_widgets:
            try:
                widget.lift()
            except tk.TclError:
                pass

    def show_tutorial_page(self):
        self.start_tutorial(auto=not self.tutorial_manual)

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
        self.selected_subject = "物理模式"
        self.selected_game_group = "普通"
        self.selected_rule_mode = "自由"
        self.selected_play_mode = "自由"
        self.mode = "物理模式"
        self.play_mode = "自由"
        self.true_random_mode = False
        self.random_group_mode = False
        self.start_game("入门")

    def render_tutorial_banner(self, parent, answer=None):
        if not self.tutorial_active:
            return
        box = tk.Frame(parent, bg="#101827", highlightbackground="#f6d36b", highlightthickness=1)
        box.pack(fill="x", padx=36, pady=(8, 0))
        text = "新手教程：跟着黄色高光操作。教程题会免费体验一次字词提示和一次词库提示。"
        if answer:
            text += f"  本题答案：{answer}"
        tk.Label(box, text=text, fg="#fff2bd", bg="#101827", justify="left", wraplength=1080, font=("Microsoft YaHei UI", 11, "bold")).pack(side="left", fill="x", expand=True, padx=16, pady=10)
        HoverButton(box, "跳过教程", self.skip_tutorial, width=132, height=44, accent="#ff9b89").pack(side="right", padx=12, pady=7)

    def render_tutorial_game_overlay(self):
        if not self.tutorial_active or not self.current:
            return
        answer = self.current.chinese
        if self.tutorial_step == "question":
            self.render_tutorial_overlay(
                self.tutorial_question_panel,
                "先看题面",
                "这里是真实答题页。左侧是题面、难度和规则；教程会先带你体验提示与词库提示，再正式输入答案。",
                next_text="试用提示",
                next_command=lambda: self.advance_tutorial_game_step("hint"),
            )
        elif self.tutorial_step == "hint":
            self.render_tutorial_overlay(
                self.tutorial_hint_button,
                "点击字词提示",
                "本教程题免费送一次字词提示。正式游戏中过多提示会扣分，提示把答案全部揭完还会让本题失败。",
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

    def advance_tutorial_game_step(self, step):
        if not self.tutorial_active:
            return
        self.tutorial_step = step
        self.render_tutorial_game_overlay()

    def show_tutorial_complete(self, elapsed, record_path):
        self.clear_tutorial_overlay()
        self.save_tutorial_completed()
        self.tutorial_active = False
        self.tutorial_step = "complete"
        self.clear()
        self._start_backdrop("constellation")
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.70, relheight=0.58)
        tk.Label(card, text="新手教程完成", fg="#9ff2b2", bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(58, 12))
        tk.Label(card, text=f"你完成了一道物理入门题，用时 {elapsed:.1f} 秒。", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 16, "bold")).pack(pady=5)
        tk.Label(card, text="教程题已保存为只读练习记录，不计入正式 Rating、成就或总积分。", fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(pady=5)
        if record_path:
            try:
                record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
            except ValueError:
                record_display = f"record/{record_path.name}"
            tk.Label(card, text=f"教程记录：{record_display}", fg="#7683a3", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(pady=(6, 16))
        HoverButton(card, "回到主页", self.show_home, width=190, height=62, accent="#9ff2b2").pack(pady=(10, 0))

    def show_login(self, allow_cancel=False):
        self.clear()
        self._start_backdrop("constellation")
        page = self.make_scroll_frame(self.container)
        if allow_cancel and self.switch_return_account:
            back = HoverButton(self.container, "返回", self.cancel_account_switch, width=110, height=48, accent="#8fb6ff")
            back.place(x=22, y=18)
        shell = tk.Frame(page, bg="#111725")
        shell.pack(fill="x", padx=32, pady=(10, 34))
        self.draw_home_title(shell, compact=True).pack(pady=(0, 14))
        cards = tk.Frame(shell, bg="#111725")
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

        self.draw_home_title(center).pack(pady=(0, 36))
        home_summary = summarize_records(load_record_entries())
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
        if self.tutorial_active and self.tutorial_step == "home" and start_button:
            self.render_tutorial_overlay(
                start_button,
                "第一步：从主页进入",
                "这里是正式主页。先点击高光的“开始游戏”，教程会带你进入一局物理入门题。",
            )

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
        avatar_id = coerce_avatar_id(self.player_settings.get("avatar_id", 0), summary.get("rating", 0))
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
        self._topbar("玩家档案（旁观）" if self.is_spectating() else "设置", self.show_home)
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
        current_title_category = self.title_category_for_title_id(current_title_id)
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
        self.settings_transitions_var = tk.BooleanVar(value=bool(self.player_settings.get("transitions_enabled", True)))
        self.settings_window_width_var = tk.StringVar(value=str(int(self.player_settings.get("window_width", 1274))))
        self.settings_window_height_var = tk.StringVar(value=str(int(self.player_settings.get("window_height", 806))))
        self.settings_speed_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_density_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_opacity_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
        self.settings_font_scale_label = tk.Label(right, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 12, "bold"))
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
            text=self.smart_wrap_text("速度、密度和透明度会影响所有动态背景。字号会影响后续打开的页面，保存后生效；页面过场可按偏好关闭。", 27),
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
        summary = summarize_records(load_record_entries())
        achievements_data = read_achievements()
        rank_progress = read_rank_progress()
        avatar_id = coerce_avatar_id(self.settings_avatar_var.get(), summary["rating"])
        title_id = coerce_title_id(self.settings_title_var.get() if self.settings_title_var else None, summary["rating"], achievements_data, rank_progress)
        rank_badge_id = coerce_rank_badge_id(self.rank_badge_var.get() if self.rank_badge_var else "", rank_progress)
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
            "transitions_enabled": self.settings_transitions_var.get(),
            "window_width": self.settings_window_width_var.get(),
            "window_height": self.settings_window_height_var.get(),
            "tutorial_completed": self.player_settings.get("tutorial_completed", True),
        })
        self.apply_ui_font_scale()
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
        self.show_settings()

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
        play_mode = BonusGuessApp.normalize_play_mode_choice(play_mode)
        random_base = BonusGuessApp.random_play_mode_base(play_mode)
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
                f"{subject_text}专属的正式限时首字母挑战，共 15 个段位。",
                "沿用旧首字母段位进度、通过总分、段位标识和称号。",
                "必须在总时限内全题答对；错误提交可以继续尝试。",
                "通过后会解锁可佩戴的段位标识和称号。",
            ]
        elif selected == "线索段位":
            title = "线索段位"
            lines = [
                f"{subject_text}专属的线索资格挑战，共 15 个段位。",
                "全部题目换成线索题，不显示首字母，只显示答案字数。",
                "每段由固定题组构成，必须全题答对并且未超时。",
                "通过后会解锁可佩戴的段位标识和称号。",
            ]
        elif selected == "字谜段位":
            title = "字谜段位"
            lines = [
                f"{subject_text}专属的字谜资格挑战，共 15 个段位。",
                "从 8 格左右逐步扩展到 25 格左右，每图词量和难度同步提升。",
                "在 10-25 分钟内完成整张字谜才算通过。",
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
                "初始只给一句描述，每次提示会多显示一条线索并扣分。",
                "普通和困难可能出现破碎线索，使本题总难度上升。",
            ]
            if random_scope:
                lines.append("线索的“真·随机”会读取入门到困难词库，暂不纳入噩梦。")
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
        self.custom_clue_initial_var = tk.StringVar(value="1")
        self.custom_clue_reveal_var = tk.StringVar(value="1")
        self.custom_minutes_var = tk.StringVar(value="5")
        self.custom_challenge_count_var = tk.StringVar(value="5")
        self.custom_crossword_width_var = tk.StringVar(value="15")
        self.custom_crossword_height_var = tk.StringVar(value="15")
        self.custom_crossword_words_var = tk.StringVar(value="27")
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
        self.custom_range_inputs(params, "初始线索数", self.custom_clue_initial_var, None, note="1-5")
        self.custom_range_inputs(params, "每次追加", self.custom_clue_reveal_var, None, note="1-5")

        tk.Label(params, text="字谜", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 4))
        self.custom_range_inputs(params, "网格宽高", self.custom_crossword_width_var, self.custom_crossword_height_var, note="5-30")
        self.custom_range_inputs(params, "目标词数", self.custom_crossword_words_var, None, note="5-80")
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
        crossword_words = self.parse_int_var(self.custom_crossword_words_var, target_word_count_for_size(max(crossword_width, crossword_height), 1.8), 5, 80)
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
            "clue_initial_lines": self.parse_int_var(self.custom_clue_initial_var, 1, 1, 5),
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

        left = tk.Frame(frame, bg="#111725", width=360)
        left.pack(side="left", fill="y", padx=(0, 24))
        left.pack_propagate(False)
        right = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="选择段位", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(6, 14))
        tk.Label(
            left,
            text="已通过的段位会带有菱形标记。\n段位进度按学科和玩法分别保存。",
            fg="#7f8caf",
            bg="#111725",
            justify="left",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor="w", fill="x", pady=(0, 12))
        button_height = 34
        for index, rank in enumerate(RANK_CHALLENGES):
            passed = rank["id"] in passed_ids
            accent = "#9ff2b2" if passed else "#9fb7ff"
            label = f"{'◆ ' if passed else ''}{rank['name']}"
            HoverButton(left, label, lambda rank_id=rank["id"]: self.start_rank_challenge(rank_id), width=332, height=button_height, accent=accent).pack(anchor="w", pady=2)

        header = tk.Frame(right, bg="#182033")
        header.pack(fill="x", padx=34, pady=(28, 16))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(header, text=f"{subject_label(self.mode)}{rank_label}", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 24, "bold")).grid(row=0, column=0, sticky="w")
        if rank_kind == "crossword":
            intro = "字谜整图挑战：边长、词量和难度随段位提升。"
        elif rank_kind == "timed":
            intro = "旧限时首字母挑战：保留历史轨道兼容。"
        elif rank_kind == "free":
            intro = "限时首字母挑战，沿用旧首字母段位进度和称号。"
        else:
            intro = "线索题挑战：不显示首字母，提示会逐步追加线索。"
        tk.Label(header, text=intro, fg="#dce6ff", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 11)).grid(row=1, column=0, sticky="w", pady=(8, 0))
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
        for index, rank in enumerate(RANK_CHALLENGES):
            self.render_rank_select_card(rank_grid, index, columns, rank, subject_info, passed_ids, wraplength)

    def render_rank_select_card(self, parent, index, columns, rank, subject_info, passed_ids, wraplength):
        passed = rank["id"] in passed_ids
        bg = "#182f2b" if passed else "#171f31"
        border = "#4cae82" if passed else "#30384e"
        title_color = "#b8ffd7" if passed else "#dce6ff"
        muted = "#8fa0c2" if not passed else "#a7dcc0"
        card = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1)
        card.grid(row=index // columns, column=index % columns, sticky="nsew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(card, bg=bg)
        title_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(13, 5))
        title_row.grid_columnconfigure(0, weight=1)
        tk.Label(title_row, text=rank["name"], fg=title_color, bg=bg, font=("Microsoft YaHei UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        score = rank_pass_score(subject_info, rank["id"])
        state = f"最高总分 {score}" if score is not None else ("已通过" if passed else "未通过")
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
                req_text = f"词条难度 {low}（{self.difficulty_label_for_value(low)}）；高段位靠掩码、交叉和限时提高有效难度"
            else:
                req_text = f"词条难度 {low}-{high}（{self.difficulty_label_for_value(low)}-{self.difficulty_label_for_value(high)}）；随段位平滑提高"
        else:
            req_text = "、".join(f"{difficulty}≥{target:g}" for difficulty, target in rank["requirements"])
        tk.Label(card, text=req_text, fg=muted, bg=bg, justify="left", anchor="w", wraplength=wraplength, font=("Microsoft YaHei UI", 9, "bold")).grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 14))

    def crossword_rank_size_for_id(self, rank_id):
        rank_id = max(1, min(15, int(rank_id or 1)))
        return int(round(8 + (rank_id - 1) * 17 / 14))

    def crossword_rank_word_count_for_id(self, rank_id):
        rank_id = max(1, min(15, int(rank_id or 1)))
        low = target_word_count_for_size(8, 1.8)
        high = int(round(target_word_count_for_size(18, 1.8) * 1.8))
        return int(round(low + (rank_id - 1) * (high - low) / 14))

    def crossword_rank_seconds_for_id(self, rank_id):
        rank_id = max(1, min(15, int(rank_id or 1)))
        return int(round(600 + (rank_id - 1) * 900 / 14))

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
        if difficulty <= 9:
            return "困难"
        return "噩梦"

    def crossword_rank_difficulty_window_for_id(self, rank_id):
        rank_id = max(1, min(15, int(rank_id or 1)))
        center = 1.5 + (rank_id - 1) * 8.5 / 14
        if rank_id == 1:
            return 1, 2, center
        if rank_id == 15:
            return 10, 10, 10.5
        low = max(1, int(center - 1.0))
        high = min(10, int(center + 1.0))
        return low, high, center

    def load_crossword_rank_terms(self, rank):
        all_terms, files = self.library.load(self.mode, "混合模式")
        low, high, center = self.crossword_rank_difficulty_window_for_id(rank["id"])
        target_words = self.crossword_rank_word_count_for_id(rank["id"])
        if int(rank["id"]) in {1, 15}:
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
        self.custom_mode = False
        self.crossword_mode = False
        self.rank_mode = True
        self.rank_kind = normalize_rank_kind(getattr(self, "rank_kind", "free"))
        if self.rank_kind == "crossword":
            self.start_crossword_rank_challenge(rank)
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

    def start_crossword_rank_challenge(self, rank):
        if self.block_spectator_action("开始字谜段位挑战"):
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
        if self.play_mode != "线索":
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
            mode_text = "不显示首字母，改用五句递进线索作答；每次追加线索都会按规则处理。线索暂不开放噩梦词库。"
        elif self.play_mode == "字谜":
            mode_text = "多词交叉填格：入门到噩梦约为 8/11/15/18/22 格。" + ("随机字谜会跨物理和数学同难度词库；真·随机会读取全部词库。" if random_scope else "")
        else:
            mode_text = "单题练习，答完后进入结算。" + ("随机模式会跨物理和数学同难度词库；真·随机会读取全部词库。" if random_scope else "")
        if random_scope and self.play_mode in {"限时", "线索"}:
            highest = "困难" if self.play_mode == "线索" else "噩梦"
            mode_text += f" 入门到{highest}只限定选词难度；真·随机会改为全库等权抽查。"
        tk.Label(parent, text="词库介绍", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=26, pady=(26, 12))
        tk.Label(parent, text=f"范围：{subject}", fg="#dce6ff", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=26, pady=5)
        tk.Label(parent, text=self.smart_wrap_text(mode_text, 30), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 12)).pack(anchor="w", padx=26, pady=5)
        tk.Label(parent, text="难度说明", fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=26, pady=(18, 8))
        descriptions = {
            "入门": "偏高中与基础词，低难高概率，免费提示更慷慨。",
            "简单": "偏核心基础概念，难度 3-4 高概率。",
            "普通": "偏大学基础和常见进阶概念，难度 5-6 高概率；首字母题可能出现 *，线索题可能出现破碎线索。",
            "困难": "偏高阶词库和更难想到的概念，难度 8-10 占比高，掩码或破碎线索概率更高。",
            "噩梦": "偏前沿和高度专门化词库，难度 10-12 占比最高；自由、限时和字谜的掩码、冷却与免费提示都比困难更严苛。",
            "混合模式": "读取当前学科下全部难度文件，词条难度均匀抽取。",
            "真·随机": "读取物理和数学的全部词库，按中文答案去重后抽取；线索玩法会排除暂未配套线索的噩梦词库。",
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
        if self.is_clue_mode():
            self.remove_nightmare_terms_from_clue_scope(difficulty)
        if not self.terms:
            raise ValueError("词库为空")

    def remove_nightmare_terms_from_clue_scope(self, difficulty):
        filtered_files = [
            file
            for file in self.library_files
            if not any(str(part).startswith("噩梦") for part in getattr(file, "parts", ()))
        ]
        if len(filtered_files) == len(self.library_files):
            return
        if not filtered_files:
            raise ValueError("线索模式暂不开放噩梦难度")
        self.terms, self.library_files = self.library.load_files(filtered_files)
        if self.is_true_random_mode() or difficulty == "真·随机":
            self.scope_text = f"全部物理和数学入门到困难线索词库：{self.library.scope_text(self.library_files)}"
        elif self.is_random_group_mode():
            self.scope_text = f"全部物理和数学{difficulty}线索词库：{self.library.scope_text(self.library_files)}"
        else:
            self.scope_text = self.library.scope_text(self.library_files)

    def crossword_mask_func(self, term):
        initials = getattr(term, "initials", "")
        if self.custom_mode:
            return self.custom_mask_positions_for_initials(initials)
        return self.crossword_random_mask_positions(initials, self.difficulty)

    @staticmethod
    def crossword_random_mask_positions(initials, gameplay_difficulty):
        table = MASK_PROBABILITIES.get(gameplay_difficulty)
        if not table:
            return []
        length = len(initials)
        if length >= 6:
            tier = 6
        elif length >= 5:
            tier = 5
        elif length >= 4:
            tier = 4
        else:
            return []
        count_probs = table.get(tier, {})
        if not count_probs:
            return []
        boosted = {count: min(1.0, probability + 0.05) for count, probability in count_probs.items()}
        counts = [0] + sorted(boosted)
        probabilities = [max(0.0, 1.0 - sum(boosted.values()))] + [boosted[count] for count in counts[1:]]
        mask_count = random.choices(counts, weights=probabilities, k=1)[0]
        if mask_count <= 0:
            return []
        return sorted(random.sample(range(length), min(mask_count, length)))

    def choose_crossword_cell_shape(self, difficulty):
        if self.custom_mode:
            shape = self.custom_config.get("crossword_shape", "随机")
            if shape == "方格":
                return "square"
            if shape == "三角":
                return "triangle"
            if shape == "六边":
                return "hex"
            try:
                triangle_probability = float(self.custom_config.get("crossword_triangle_probability", 15)) / 100
                hex_probability = float(self.custom_config.get("crossword_hex_probability", 15)) / 100
            except (TypeError, ValueError):
                triangle_probability, hex_probability = 0.15, 0.15
            roll = random.random()
            if roll < triangle_probability:
                return "triangle"
            if roll < triangle_probability + hex_probability:
                return "hex"
            return "square"
        if difficulty == "普通":
            roll = random.random()
            if roll < 0.15:
                return "triangle"
            if roll < 0.30:
                return "hex"
        if difficulty == "困难":
            roll = random.random()
            if roll < 0.20:
                return "triangle"
            if roll < 0.40:
                return "hex"
        if difficulty == "噩梦":
            roll = random.random()
            if roll < 0.25:
                return "triangle"
            if roll < 0.55:
                return "hex"
        return "square"

    @staticmethod
    def scaled_crossword_free_hint_quota(quota):
        try:
            value = int(quota or 0)
        except (TypeError, ValueError):
            value = 0
        return max(0, int(value * 0.75))

    def start_crossword_game(self, difficulty):
        self.crossword_mode = True
        is_crossword_rank = self.rank_mode and self.rank_kind == "crossword"
        if not is_crossword_rank:
            self.rank_mode = False
        self.current = None
        self.difficulty = difficulty
        if self.custom_mode:
            size = (
                int(self.custom_config.get("crossword_width") or 15),
                int(self.custom_config.get("crossword_height") or 15),
            )
            max_words = int(self.custom_config.get("crossword_words") or target_word_count_for_size(size, 1.8))
        else:
            size = self.crossword_rank_size if is_crossword_rank and self.crossword_rank_size else size_for_difficulty(difficulty)
            max_words = self.crossword_rank_word_count if is_crossword_rank and self.crossword_rank_word_count else target_word_count_for_size(size, 1.8)
        cell_shape = self.choose_crossword_cell_shape(difficulty)
        try:
            puzzle = generate_crossword(
                self.terms,
                difficulty,
                rng=random,
                max_words=max_words,
                size=size,
                mask_func=self.crossword_mask_func,
                cell_shape=cell_shape,
            )
            validate_crossword(puzzle)
        except Exception as exc:
            messagebox.showerror("字谜生成失败", str(exc))
            self.show_difficulty()
            return
        if not puzzle.placements:
            messagebox.showerror("字谜生成失败", "当前词库没有可用词条。")
            self.show_difficulty()
            return
        self.crossword_puzzle = puzzle
        self.crossword_session_id = uuid.uuid4().hex
        self.crossword_selected_id = puzzle.placements[0].id
        self.crossword_solved_ids = set()
        self.crossword_revealed_cells = set()
        self.crossword_filled_answers = {}
        self.crossword_cell_to_placements = {}
        for placement in puzzle.placements:
            for index, (row, col, _char) in enumerate(placement.cells):
                self.crossword_cell_to_placements.setdefault((row, col), []).append((placement, index))
        self.crossword_attempts = []
        self.crossword_hint_lines = []
        self.crossword_hint_penalties = []
        self.crossword_library_hint_texts = []
        self.crossword_score_penalty = 0
        self.crossword_zoom = 1.0
        self.crossword_pan_x = 0.0
        self.crossword_pan_y = 0.0
        self.crossword_drag_start = None
        self.crossword_drag_pan_start = (0.0, 0.0)
        self.crossword_dragged = False
        self.crossword_last_clicked_cell = None
        self.crossword_click_cycle_index = 0
        self.crossword_free_hint_count = 0
        self.crossword_paid_hint_count = 0
        self.crossword_library_hint_count = 0
        self.crossword_cheat_warnings = 0
        self.crossword_cheat_pending = False
        self.crossword_raw_initial_buffer = ""
        self.crossword_raw_initial_last_at = 0.0
        self.hint_cooldown_until = 0.0
        self.cheat_info = {}
        sample_count = max(1, (len(puzzle.placements) + 1) // 2)
        if self.custom_mode:
            setting = self.custom_config.get("free_hint", "自动")
            if setting == "自动":
                self.crossword_free_hint_quota = sum(
                    random_free_hint_quota(len(random.choice(puzzle.placements).answer), self.automatic_mask_difficulty())
                    for _ in range(sample_count)
                )
            else:
                try:
                    self.crossword_free_hint_quota = max(0, min(50, int(setting)))
                except (TypeError, ValueError):
                    self.crossword_free_hint_quota = 0
            self.crossword_free_hint_quota = self.scaled_crossword_free_hint_quota(self.crossword_free_hint_quota)
            library_setting = self.custom_config.get("library_hint_limit", "自动")
            self.crossword_library_hint_limit = sample_count if library_setting == "自动" else max(0, min(50, int(library_setting or 0)))
        else:
            self.crossword_free_hint_quota = sum(
                random_free_hint_quota(len(random.choice(puzzle.placements).answer), difficulty)
                for _ in range(sample_count)
            )
            self.crossword_free_hint_quota = self.scaled_crossword_free_hint_quota(self.crossword_free_hint_quota)
            self.crossword_library_hint_limit = sample_count
        self.crossword_start_score = 400 * len(puzzle.placements)
        difficulties = [max(1, int(getattr(placement.term, "difficulty", 5) or 5)) for placement in puzzle.placements]
        mask_total = sum(len(getattr(placement, "mask_positions", set()) or set()) for placement in puzzle.placements)
        word_total_difficulties = [
            difficulty + 0.5 * len(getattr(placement, "mask_positions", set()) or set())
            for placement, difficulty in zip(puzzle.placements, difficulties)
        ]
        average_difficulty = sum(word_total_difficulties) / max(len(word_total_difficulties), 1)
        shape_bonus = 0.5 if getattr(puzzle, "cell_shape", "square") in {"triangle", "hex"} else 0.0
        self.effective_difficulty = average_difficulty + shape_bonus
        if not self.custom_mode and any(len(placement.answer) == 1 for placement in puzzle.placements):
            self.complete_achievement("one_char_term")
        self.mark_greek_term_encounter((placement.answer for placement in puzzle.placements), crossword=True)
        self.start_time = time.perf_counter()
        self.timed_round_start = self.start_time
        if is_crossword_rank:
            self.timed_deadline = self.start_time + self.crossword_rank_seconds
        self.game_active = True
        self.record_saved = False
        self.show_crossword_game()

    def show_crossword_game(self, transition=True):
        self.clear(transition=transition)
        self._start_backdrop("wind")
        if self.rank_mode and self.rank_kind == "crossword":
            rank = rank_by_id(self.rank_id)
            title = f"{subject_label(self.rank_subject)}字谜段位 / {rank['name']}"
        elif self.custom_mode:
            title = f"自定义 / 字谜 / {self.custom_config.get('crossword_shape', '随机')}"
        else:
            title = "字谜模式 / 随机 / " + self.difficulty if self.is_crossword_random_scope() else f"{self.mode} / 字谜 / {self.difficulty}"
        self._topbar(title, self.abandon_crossword)
        root = tk.Frame(self.container, bg="#111725")
        root.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        root.grid_columnconfigure(0, weight=0, minsize=390)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        left = tk.Frame(root, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left.grid_columnconfigure(0, weight=1)
        right = tk.Frame(root, bg="#101827", highlightbackground="#3b4560", highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        tk.Label(left, text="字谜作答", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 21, "bold")).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 6))
        self.crossword_status_label = tk.Label(left, text="", fg="#c8d2ee", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11, "bold"))
        self.crossword_status_label.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        list_shell = tk.Frame(left, bg="#182033")
        list_shell.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))
        left.grid_rowconfigure(2, weight=1)
        self.crossword_word_listbox = tk.Listbox(
            list_shell,
            exportselection=False,
            fg="#dce6ff",
            bg="#101827",
            selectforeground="#101827",
            selectbackground="#9ff2b2",
            relief="flat",
            activestyle="none",
            height=10,
            font=("Consolas", 12, "bold"),
        )
        word_scrollbar = tk.Scrollbar(list_shell, orient="vertical", command=self.crossword_word_listbox.yview)
        self.crossword_word_listbox.configure(yscrollcommand=word_scrollbar.set)
        self.crossword_word_listbox.pack(side="left", fill="both", expand=True)
        word_scrollbar.pack(side="right", fill="y")
        self.crossword_word_listbox.bind("<<ListboxSelect>>", self.on_crossword_word_select)
        self.bind_scroll_wheel(list_shell, self.crossword_word_listbox)

        self.crossword_answer_var = tk.StringVar()
        validate_answer = (self.register(self.validate_crossword_answer_change), "%P")
        entry = tk.Entry(
            left,
            textvariable=self.crossword_answer_var,
            validate="key",
            validatecommand=validate_answer,
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Microsoft YaHei UI", 21, "bold"),
        )
        entry.grid(row=3, column=0, sticky="ew", padx=24, ipady=9)
        entry.bind("<KeyPress>", self.on_crossword_keypress)
        entry.bind("<KeyRelease>", self.on_crossword_keyrelease)
        entry.bind("<Return>", lambda _event: self.check_crossword_answer())
        self.answer_entry = entry
        self.crossword_answer_var.trace_add("write", self.on_crossword_answer_change)

        buttons = tk.Frame(left, bg="#182033")
        buttons.grid(row=4, column=0, pady=14)
        HoverButton(buttons, "确认", self.check_crossword_answer, width=118, height=52, accent="#9ff2b2").grid(row=0, column=0, padx=5)
        self.crossword_hint_button = HoverButton(buttons, "提示", self.show_crossword_hint, width=118, height=52, accent="#f6d36b")
        self.crossword_hint_button.grid(row=0, column=1, padx=5)
        self.crossword_library_hint_button = HoverButton(buttons, "词库", self.show_crossword_library_hint, width=118, height=52, accent="#ffbd7e")
        self.crossword_library_hint_button.grid(row=0, column=2, padx=5)
        self.hint_button = self.crossword_hint_button

        self.crossword_feedback = tk.Label(left, text="选择编号后输入中文答案。", fg="#9ca8c7", bg="#182033", justify="left", anchor="w", wraplength=340, font=("Microsoft YaHei UI", 12, "bold"))
        self.crossword_feedback.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 10))
        self.crossword_hint_box = tk.Text(left, height=5, wrap="char", fg="#dce6ff", bg="#111827", relief="flat", bd=0, highlightthickness=1, highlightbackground="#30384e", font=("Microsoft YaHei UI", 10))
        self.crossword_hint_box.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 10))
        self.crossword_hint_box.config(state="disabled")
        self.crossword_library_hint_label = tk.Label(left, text="", fg="#f6d36b", bg="#182033", justify="left", anchor="w", wraplength=340, font=("Microsoft YaHei UI", 10, "bold"))
        self.crossword_library_hint_label.grid(row=7, column=0, sticky="ew", padx=24, pady=(0, 18))

        self.crossword_canvas = tk.Canvas(right, bg="#050b1e", bd=0, highlightthickness=0)
        self.crossword_canvas.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self.crossword_canvas.bind("<Configure>", self.draw_crossword_canvas)
        self.crossword_canvas.bind("<ButtonPress-1>", self.on_crossword_canvas_press)
        self.crossword_canvas.bind("<B1-Motion>", self.on_crossword_canvas_drag)
        self.crossword_canvas.bind("<ButtonRelease-1>", self.on_crossword_canvas_release)
        for event_name in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.crossword_canvas.bind(event_name, self.on_crossword_canvas_wheel, add="+")

        self.refresh_crossword_word_list()
        self.update_crossword_status()
        self.update_crossword_hint_box()
        self.update_hint_cooldown_button()
        entry.focus_set()
        self.crossword_tick()

    def crossword_selected_placement(self):
        if not self.crossword_puzzle:
            return None
        for placement in self.crossword_puzzle.placements:
            if placement.id == self.crossword_selected_id:
                return placement
        return None

    def crossword_initials_for_placement(self, placement):
        initials = normalize_term_initials(placement.answer, placement.initials)
        mask_positions = getattr(placement, "mask_positions", set()) or set()
        display = placement.display_initials or initials
        if len(display) != len(placement.answer):
            display = apply_initial_mask(initials, mask_positions) if mask_positions else initials
        return display

    def refresh_crossword_word_list(self):
        if not self.crossword_word_listbox or not self.crossword_puzzle:
            return
        self.crossword_word_listbox.delete(0, tk.END)
        selected_index = 0
        for index, placement in enumerate(self.crossword_puzzle.placements):
            direction = "横" if placement.direction == "across" else "纵"
            status = "OK" if placement.id in self.crossword_solved_ids else "  "
            initials = self.crossword_initials_for_placement(placement)
            difficulty = int(getattr(placement.term, "difficulty", 5) or 5)
            difficulty_label = self.difficulty_label_for_value(difficulty)
            text = f"{status} {placement.id:02d} {direction} {len(placement.answer)}字  {difficulty_label} {difficulty}  {initials}"
            notice = term_notice_text(placement.answer, prefix="含有")
            if notice:
                text = f"{text}  | {notice}"
            self.crossword_word_listbox.insert(tk.END, text)
            if placement.id in self.crossword_solved_ids:
                self.crossword_word_listbox.itemconfig(index, foreground="#74d99f")
            elif placement.intersections == 0:
                self.crossword_word_listbox.itemconfig(index, foreground="#f6d36b")
            if placement.id == self.crossword_selected_id:
                selected_index = index
        self.crossword_word_listbox.selection_clear(0, tk.END)
        self.crossword_word_listbox.selection_set(selected_index)
        self.crossword_word_listbox.activate(selected_index)
        self.crossword_word_listbox.see(selected_index)

    def on_crossword_word_select(self, _event=None):
        if not self.crossword_word_listbox or not self.crossword_puzzle:
            return
        selection = self.crossword_word_listbox.curselection()
        if not selection:
            return
        index = int(selection[0])
        if 0 <= index < len(self.crossword_puzzle.placements):
            self.crossword_selected_id = self.crossword_puzzle.placements[index].id
            if self.crossword_answer_var:
                self.crossword_answer_var.set("")
            self.draw_crossword_canvas()

    def on_crossword_canvas_click(self, event):
        if not self.crossword_puzzle or not self.crossword_canvas:
            return
        cell = self.crossword_cell_at_point(event.x, event.y)
        if cell is None:
            return
        placements = self.crossword_cell_to_placements.get(cell, [])
        if not placements:
            return
        unsolved = [(placement, idx) for placement, idx in placements if placement.id not in self.crossword_solved_ids]
        candidates = unsolved or placements
        if len(candidates) == 1:
            chosen = candidates[0][0]
            self.crossword_click_cycle_index = 0
        else:
            current_index = next((i for i, (placement, _idx) in enumerate(candidates) if placement.id == self.crossword_selected_id), -1)
            if current_index >= 0 and self.crossword_last_clicked_cell != cell:
                chosen = candidates[current_index][0]
                self.crossword_click_cycle_index = current_index
            else:
                next_index = (current_index + 1) % len(candidates) if current_index >= 0 else 0
                chosen = candidates[next_index][0]
                self.crossword_click_cycle_index = next_index
        self.crossword_last_clicked_cell = cell
        self.crossword_selected_id = chosen.id
        self.refresh_crossword_word_list()
        self.draw_crossword_canvas()
        return "break"

    def on_crossword_canvas_press(self, event):
        self.crossword_drag_start = (event.x, event.y)
        self.crossword_drag_pan_start = (self.crossword_pan_x, self.crossword_pan_y)
        self.crossword_dragged = False
        return "break"

    def on_crossword_canvas_drag(self, event):
        if not self.crossword_drag_start:
            return "break"
        if self.crossword_zoom <= 1.0001:
            return "break"
        dx = event.x - self.crossword_drag_start[0]
        dy = event.y - self.crossword_drag_start[1]
        if abs(dx) + abs(dy) > 4:
            self.crossword_dragged = True
        if self.crossword_dragged:
            self.crossword_pan_x = self.crossword_drag_pan_start[0] + dx
            self.crossword_pan_y = self.crossword_drag_pan_start[1] + dy
            self.draw_crossword_canvas()
        return "break"

    def on_crossword_canvas_release(self, event):
        dragged = self.crossword_dragged
        self.crossword_drag_start = None
        self.crossword_dragged = False
        if not dragged:
            return self.on_crossword_canvas_click(event)
        return "break"

    def crossword_allows_zoom(self):
        return bool(self.crossword_puzzle)

    def on_crossword_canvas_wheel(self, event):
        if not self.crossword_allows_zoom():
            return None
        if getattr(event, "num", None) == 4:
            step = 1
        elif getattr(event, "num", None) == 5:
            step = -1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return "break"
            step = 1 if delta > 0 else -1
        factor = 1.10 if step > 0 else 1 / 1.10
        old_zoom = max(1.0, float(self.crossword_zoom or 1.0))
        new_zoom = max(1.0, min(3.25, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 0.001:
            return "break"
        width = max(self.crossword_canvas.winfo_width(), 1) if self.crossword_canvas else 1
        height = max(self.crossword_canvas.winfo_height(), 1) if self.crossword_canvas else 1
        focus_x = event.x - width / 2
        focus_y = event.y - height / 2
        scale = new_zoom / old_zoom
        self.crossword_pan_x = (self.crossword_pan_x - focus_x) * scale + focus_x
        self.crossword_pan_y = (self.crossword_pan_y - focus_y) * scale + focus_y
        self.crossword_zoom = new_zoom
        if self.crossword_zoom <= 1.0001:
            self.crossword_pan_x = 0.0
            self.crossword_pan_y = 0.0
        self.draw_crossword_canvas()
        self.update_crossword_status()
        return "break"

    def crossword_shape(self):
        return getattr(self.crossword_puzzle, "cell_shape", "square") if self.crossword_puzzle else "square"

    def crossword_canvas_padding(self):
        return 50

    def crossword_board_size_for_unit(self, unit, shape=None):
        if not self.crossword_puzzle:
            return 0.0, 0.0
        shape = shape or self.crossword_shape()
        cols = max(1, int(self.crossword_puzzle.width))
        rows = max(1, int(self.crossword_puzzle.height))
        if shape == "triangle":
            return (cols + 1) * unit / 2, rows * unit * math.sqrt(3) / 2
        if shape == "hex":
            hex_height = math.sqrt(3) * unit
            return 2 * unit + max(0, cols - 1) * 1.5 * unit, rows * hex_height + (hex_height / 2 if cols > 1 else 0)
        return cols * unit, rows * unit

    def crossword_fit_unit(self, width, height, pad=None):
        if not self.crossword_puzzle:
            return 0.0
        pad = self.crossword_canvas_padding() if pad is None else pad
        available_w = max(1.0, width - 2 * pad)
        available_h = max(1.0, height - 2 * pad)
        cols = max(1, int(self.crossword_puzzle.width))
        rows = max(1, int(self.crossword_puzzle.height))
        shape = self.crossword_shape()
        if shape == "triangle":
            width_units = (cols + 1) / 2
            height_units = rows * math.sqrt(3) / 2
        elif shape == "hex":
            width_units = 2 + max(0, cols - 1) * 1.5
            height_units = math.sqrt(3) * (rows + (0.5 if cols > 1 else 0))
        else:
            width_units = cols
            height_units = rows
        return max(1.0, min(available_w / width_units, available_h / height_units))

    def clamp_crossword_pan(self, width, height, board_width, board_height):
        if self.crossword_zoom <= 1.0001:
            self.crossword_pan_x = 0.0
            self.crossword_pan_y = 0.0
            return
        outer_pad = 34
        margin = 8
        base_origin_x = (width - board_width) / 2
        base_origin_y = (height - board_height) / 2
        outer_width = board_width + outer_pad * 2
        outer_height = board_height + outer_pad * 2
        if outer_width <= width - margin * 2:
            self.crossword_pan_x = 0.0
        else:
            min_pan = width - margin - (base_origin_x + board_width + outer_pad)
            max_pan = margin - (base_origin_x - outer_pad)
            self.crossword_pan_x = min(max(self.crossword_pan_x, min_pan), max_pan)
        if outer_height <= height - margin * 2:
            self.crossword_pan_y = 0.0
        else:
            min_pan = height - margin - (base_origin_y + board_height + outer_pad)
            max_pan = margin - (base_origin_y - outer_pad)
            self.crossword_pan_y = min(max(self.crossword_pan_y, min_pan), max_pan)

    def crossword_canvas_metrics(self):
        if not self.crossword_canvas or not self.crossword_puzzle:
            return 0, 0, 0
        width = max(self.crossword_canvas.winfo_width(), 1)
        height = max(self.crossword_canvas.winfo_height(), 1)
        base_unit = self.crossword_fit_unit(width, height)
        zoom = max(1.0, float(self.crossword_zoom or 1.0)) if self.crossword_allows_zoom() else 1.0
        self.crossword_zoom = zoom
        unit = base_unit * zoom
        board_width, board_height = self.crossword_board_size_for_unit(unit)
        self.clamp_crossword_pan(width, height, board_width, board_height)
        origin_x = (width - board_width) / 2 + self.crossword_pan_x
        origin_y = (height - board_height) / 2 + self.crossword_pan_y
        return unit, origin_x, origin_y

    def crossword_column_label(self, col):
        value = col + 1
        label = ""
        while value > 0:
            value, index = divmod(value - 1, 26)
            label = chr(ord("A") + index) + label
        return label

    def crossword_cell_coord(self, row, col):
        return f"{self.crossword_column_label(col)}{row + 1}"

    def crossword_cell_resolved(self, cell):
        if cell in self.crossword_revealed_cells:
            return True
        return any(placement.id in self.crossword_solved_ids for placement, _idx in self.crossword_cell_to_placements.get(cell, []))

    def crossword_cell_visible_char(self, cell):
        for placement, index in self.crossword_cell_to_placements.get(cell, []):
            filled = self.crossword_filled_answers.get(placement.id)
            if filled and index < len(filled):
                return filled[index]
        return self.crossword_puzzle.grid.get(cell, "") if self.crossword_puzzle else ""

    def crossword_cell_text(self, row, col):
        cell = (row, col)
        if self.crossword_cell_resolved(cell):
            char = self.crossword_cell_visible_char(cell)
            return char, "#e0fbff", ("Microsoft YaHei UI", 14, "bold")
        placements = self.crossword_cell_to_placements.get(cell, [])
        selected = next(((placement, idx) for placement, idx in placements if placement.id == self.crossword_selected_id), None)
        placement, index = selected or placements[0]
        initials = self.crossword_initials_for_placement(placement)
        text = initials[index] if index < len(initials) else normalize_term_initials(placement.answer, "")[index:index + 1]
        color = "#f0abfc" if text == "*" else "#bfdbfe"
        return text, color, ("Consolas", 12, "bold")

    def flat_points(self, points):
        return [coord for point in points for coord in point]

    def polygon_center(self, points):
        if not points:
            return 0.0, 0.0
        return sum(x for x, _y in points) / len(points), sum(y for _x, y in points) / len(points)

    def scaled_polygon(self, points, center, factor):
        cx, cy = center
        return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in points]

    def crossword_cell_polygon(self, row, col, unit, origin_x, origin_y, shape=None):
        shape = shape or self.crossword_shape()
        if shape == "triangle":
            side = unit
            height = side * math.sqrt(3) / 2
            x = origin_x + col * side / 2
            y = origin_y + row * height
            if (row + col) % 2 == 0:
                return [(x, y + height), (x + side / 2, y), (x + side, y + height)]
            return [(x, y), (x + side, y), (x + side / 2, y + height)]
        if shape == "hex":
            radius = unit
            hex_height = math.sqrt(3) * radius
            cx = origin_x + radius + col * 1.5 * radius
            cy = origin_y + hex_height / 2 + row * hex_height + (hex_height / 2 if col % 2 else 0)
            return [
                (cx + radius, cy),
                (cx + radius / 2, cy + hex_height / 2),
                (cx - radius / 2, cy + hex_height / 2),
                (cx - radius, cy),
                (cx - radius / 2, cy - hex_height / 2),
                (cx + radius / 2, cy - hex_height / 2),
            ]
        x1 = origin_x + col * unit
        y1 = origin_y + row * unit
        return [(x1, y1), (x1 + unit, y1), (x1 + unit, y1 + unit), (x1, y1 + unit)]

    def crossword_cell_center(self, row, col, unit, origin_x, origin_y, shape=None):
        return self.polygon_center(self.crossword_cell_polygon(row, col, unit, origin_x, origin_y, shape))

    def point_in_polygon(self, x, y, points):
        inside = False
        count = len(points)
        if count < 3:
            return False
        j = count - 1
        for i in range(count):
            xi, yi = points[i]
            xj, yj = points[j]
            if min(yi, yj) <= y <= max(yi, yj) and abs(yj - yi) < 1e-9 and min(xi, xj) <= x <= max(xi, xj):
                return True
            intersects = ((yi > y) != (yj > y)) and (x <= (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi)
            if intersects:
                inside = not inside
            j = i
        return inside

    def crossword_cell_at_point(self, x, y):
        if not self.crossword_puzzle:
            return None
        unit, origin_x, origin_y = self.crossword_canvas_metrics()
        if unit <= 0:
            return None
        shape = self.crossword_shape()
        for row, col in self.crossword_puzzle.grid:
            points = self.crossword_cell_polygon(row, col, unit, origin_x, origin_y, shape)
            xs = [px for px, _py in points]
            ys = [py for _px, py in points]
            if min(xs) - 1 <= x <= max(xs) + 1 and min(ys) - 1 <= y <= max(ys) + 1 and self.point_in_polygon(x, y, points):
                return (row, col)
        return None

    def polygon_corner_anchor(self, points, center, index):
        if not points:
            return center
        corner = points[index % len(points)]
        cx, cy = center
        return corner[0] * 0.78 + cx * 0.22, corner[1] * 0.78 + cy * 0.22

    def start_number_corner_order(self, points):
        cx, cy = self.polygon_center(points)
        scored = []
        for index, (x, y) in enumerate(points):
            angle = math.atan2(y - cy, x - cx)
            scored.append((angle, index))
        scored.sort()
        return [index for _angle, index in scored]

    def draw_crossword_start_numbers(self, canvas, points, placements, unit):
        if not placements:
            return
        center = self.polygon_center(points)
        ordered_corners = self.start_number_corner_order(points)
        placements = sorted(placements, key=lambda item: (0 if item.direction == "across" else 1, item.id))
        number_size = max(5, min(10, int(unit * 0.15)))
        radius_y = max(4.5, number_size * 0.60)
        for offset, placement in enumerate(placements):
            anchor = self.polygon_corner_anchor(points, center, ordered_corners[offset % len(ordered_corners)])
            text = str(placement.id)
            radius_x = max(6, int(number_size * (0.48 * len(text) + 0.55)))
            selected_start = placement.id == self.crossword_selected_id
            number_fill = "#e0f2fe" if selected_start else ("#67e8f9" if placement.id in self.crossword_solved_ids else "#93c5fd")
            outline = "#7dd3fc" if selected_start else "#1d4ed8"
            canvas.create_rectangle(
                anchor[0] - radius_x,
                anchor[1] - radius_y,
                anchor[0] + radius_x,
                anchor[1] + radius_y,
                fill="#061128",
                outline=outline,
                width=1,
            )
            canvas.create_text(anchor[0], anchor[1], text=text, fill=number_fill, font=("Consolas", number_size, "bold"))

    def draw_crossword_polygon(self, canvas, points, fill, outline="", width=1):
        canvas.create_polygon(self.flat_points(points), fill=fill, outline=outline, width=width)

    def draw_crossword_backdrop(self, canvas, width, height, origin_x, origin_y, board_width, board_height):
        canvas.create_rectangle(0, 0, width, height, fill="#050b1e", outline="")
        for i in range(95):
            x = (i * 83 + i * i * 19) % max(width, 1)
            y = (i * 47 + i * i * 11) % max(height, 1)
            size = 1 + (1 if i % 17 == 0 else 0)
            color = ("#1d4ed8", "#38bdf8", "#dbeafe")[i % 3]
            canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
        for i in range(0, max(width, 1), 92):
            y = (i * 37) % max(height, 1)
            canvas.create_line(i - 70, y, i + 36, y + 10, fill="#0e2f5a", width=1)
        x1 = origin_x - 34
        y1 = origin_y - 34
        x2 = origin_x + board_width + 34
        y2 = origin_y + board_height + 34
        canvas.create_rectangle(x1 - 8, y1 - 8, x2 + 8, y2 + 8, fill="#061128", outline="#0b2d5c", width=1)
        canvas.create_rectangle(x1 - 3, y1 - 3, x2 + 3, y2 + 3, outline="#1d4ed8", width=1)
        canvas.create_rectangle(x1, y1, x2, y2, outline="#38bdf8", width=1)

    def draw_crossword_axes(self, canvas, puzzle, unit, origin_x, origin_y, board_width, board_height):
        axis_size = max(8, min(14, int(unit * 0.28)))
        font = ("Consolas", axis_size, "bold")
        letter_y_top = origin_y - max(15, int(unit * 0.34))
        letter_y_bottom = origin_y + board_height + max(15, int(unit * 0.34))
        number_x_left = origin_x - max(13, int(unit * 0.28))
        number_x_right = origin_x + board_width + max(13, int(unit * 0.28))
        shape = self.crossword_shape()
        for col in range(puzzle.width):
            centers = [self.crossword_cell_center(row, col, unit, origin_x, origin_y, shape)[0] for row in range(puzzle.height)]
            x = sum(centers) / max(len(centers), 1)
            label = self.crossword_column_label(col)
            canvas.create_text(x, letter_y_top, text=label, fill="#93c5fd", font=font)
            canvas.create_text(x, letter_y_bottom, text=label, fill="#38bdf8", font=font)
        for row in range(puzzle.height):
            centers = [self.crossword_cell_center(row, col, unit, origin_x, origin_y, shape)[1] for col in range(puzzle.width)]
            y = sum(centers) / max(len(centers), 1)
            label = str(row + 1)
            canvas.create_text(number_x_left, y, text=label, fill="#93c5fd", anchor="e", font=font)
            canvas.create_text(number_x_right, y, text=label, fill="#38bdf8", anchor="w", font=font)

    def crossword_cell_shape_label(self):
        labels = {
            "triangle": "三角格",
            "hex": "六边格",
            "square": "方格",
        }
        shape = getattr(self.crossword_puzzle, "cell_shape", "square") if self.crossword_puzzle else "square"
        return labels.get(shape, "方格")

    def draw_crossword_canvas(self, _event=None):
        if not self.crossword_canvas or not self.crossword_puzzle:
            return
        canvas = self.crossword_canvas
        puzzle = self.crossword_puzzle
        canvas.delete("all")
        unit, origin_x, origin_y = self.crossword_canvas_metrics()
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        board_width, board_height = self.crossword_board_size_for_unit(unit)
        self.draw_crossword_backdrop(canvas, width, height, origin_x, origin_y, board_width, board_height)
        self.draw_crossword_axes(canvas, puzzle, unit, origin_x, origin_y, board_width, board_height)
        selected = self.crossword_selected_placement()
        selected_cells = {(row, col) for row, col, _char in selected.cells} if selected else set()
        shape = self.crossword_shape()
        for row in range(puzzle.height):
            for col in range(puzzle.width):
                cell = (row, col)
                points = self.crossword_cell_polygon(row, col, unit, origin_x, origin_y, shape)
                center = self.polygon_center(points)
                if cell not in puzzle.grid:
                    self.draw_crossword_polygon(canvas, points, fill="#071225", outline="#102642", width=1)
                    if (row + col) % 5 == 0:
                        cx, cy = center
                        mark = max(3, int(unit * 0.09))
                        canvas.create_line(cx - mark, cy, cx + mark, cy, fill="#123b6d", width=1)
                    continue
                resolved = self.crossword_cell_resolved(cell)
                highlighted = cell in selected_cells
                intersecting = len(self.crossword_cell_to_placements.get(cell, [])) > 1
                if highlighted:
                    glow, fill, inset, outline = "#0ea5e9", "#1d4ed8", "#1e3a8a", "#7dd3fc"
                elif resolved:
                    glow, fill, inset, outline = "#0891b2", "#0f3f61", "#155e75", "#67e8f9"
                else:
                    glow, fill, inset, outline = "#123b6d", "#0b1e38", "#102a4c", "#2563eb"
                self.draw_crossword_polygon(canvas, points, fill="#071225", outline="#102642", width=1)
                self.draw_crossword_polygon(canvas, self.scaled_polygon(points, center, 0.92), fill=glow, outline="")
                self.draw_crossword_polygon(canvas, self.scaled_polygon(points, center, 0.84), fill=fill, outline=outline, width=2 if highlighted else 1)
                if highlighted:
                    self.draw_crossword_polygon(canvas, self.scaled_polygon(points, center, 0.72), fill="", outline="#e0f2fe", width=2)
                self.draw_crossword_polygon(canvas, self.scaled_polygon(points, center, 0.58), fill=inset, outline="")
                if intersecting and not resolved:
                    marker = max(2, int(unit * 0.06))
                    corner = max(points, key=lambda item: item[0] - item[1])
                    mx = corner[0] * 0.70 + center[0] * 0.30
                    my = corner[1] * 0.70 + center[1] * 0.30
                    canvas.create_oval(mx - marker, my - marker, mx + marker, my + marker, fill="#22d3ee", outline="")
                text, color, font = self.crossword_cell_text(row, col)
                text_size = max(7, min(19, int(unit * (0.44 if shape != "triangle" else 0.38))))
                canvas.create_text(center[0], center[1] + max(1, int(unit * 0.03)), text=text, fill=color, font=(font[0], text_size, font[2]))
        starts_by_cell = {}
        for placement in puzzle.placements:
            row, col, _char = placement.cells[0]
            starts_by_cell.setdefault((row, col), []).append(placement)
        for (row, col), placements in starts_by_cell.items():
            points = self.crossword_cell_polygon(row, col, unit, origin_x, origin_y, shape)
            self.draw_crossword_start_numbers(canvas, points, placements, unit)

    def update_crossword_status(self):
        if not self.crossword_puzzle:
            return
        solved = len(self.crossword_solved_ids)
        total = len(self.crossword_puzzle.placements)
        elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        score = self.crossword_current_score(elapsed)
        time_label = f"计时 {elapsed:.1f} 秒"
        if self.rank_mode and self.rank_kind == "crossword" and self.timed_deadline:
            remaining = max(0.0, self.timed_deadline - time.perf_counter())
            time_label = f"剩余 {format_duration(remaining)}"
        shape_text = self.crossword_cell_shape_label()
        zoom_text = f"    缩放 {self.crossword_zoom:.0%}" if self.crossword_allows_zoom() else ""
        text = (
            f"进度 {solved}/{total} 词    交叉 {self.crossword_puzzle.intersection_count}    孤立 {self.crossword_puzzle.isolated_count}    {shape_text}{zoom_text}\n"
            f"{time_label}    积分 {score}    提示 {self.crossword_free_hint_count}/{self.crossword_free_hint_quota} 免费"
        )
        if self.crossword_status_label:
            self.crossword_status_label.config(text=text)

    def crossword_tick(self):
        if not self.game_active or self.record_saved or not self.crossword_mode:
            return
        if self.rank_mode and self.rank_kind == "crossword" and self.timed_deadline and time.perf_counter() >= self.timed_deadline:
            self.fail_crossword_game("时间到", "timeout")
            return
        self.update_crossword_status()
        self.timer_job = self.after(100, self.crossword_tick)

    def crossword_current_score(self, elapsed=None):
        if elapsed is None:
            elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        return self.crossword_start_score - int(elapsed) - self.crossword_score_penalty

    def crossword_score_weight(self):
        if self.custom_mode:
            return 0.0
        return score_weight_for_difficulty(self.difficulty)

    def crossword_penalty_factor(self):
        return 1.18 - 0.045 * max(1.0, min(12.0, float(self.effective_difficulty or 5)))

    def crossword_character_hint_cost(self, hint_number):
        average_length = sum(len(placement.answer) for placement in self.crossword_puzzle.placements) / max(len(self.crossword_puzzle.placements), 1)
        raw = max(80, round(440 / max(average_length, 2))) + 45 * (hint_number - 1)
        return max(55, round(raw * self.crossword_penalty_factor()))

    def crossword_library_hint_cost(self):
        return max(75, round(170 * self.crossword_penalty_factor()))

    def add_crossword_penalty(self, amount):
        self.crossword_score_penalty += int(amount)
        self.update_crossword_status()

    def update_crossword_hint_box(self):
        if not self.crossword_hint_box:
            return
        self.crossword_hint_box.config(state="normal")
        self.crossword_hint_box.delete("1.0", tk.END)
        if not self.crossword_hint_lines:
            self.crossword_hint_box.insert("1.0", f"字词提示会按 A2 坐标揭开一个未确定格子；本局免费 {self.crossword_free_hint_quota} 次。\n词库提示可用 {self.crossword_library_hint_limit} 次。")
        else:
            self.crossword_hint_box.insert("1.0", "\n".join(self.crossword_hint_lines[-8:]))
        self.crossword_hint_box.config(state="disabled")

    def clear_crossword_answer_input(self):
        if not self.crossword_answer_var:
            return
        self.suppress_answer_trace = True
        try:
            self.crossword_answer_var.set("")
            if self.answer_entry and self.answer_entry.winfo_exists():
                self.answer_entry.delete(0, tk.END)
        finally:
            self.suppress_answer_trace = False

    def crossword_locked_indices(self, placement):
        locked = {}
        for index, (row, col, char) in enumerate(placement.cells):
            cell = (row, col)
            if cell in self.crossword_revealed_cells or len(self.crossword_cell_to_placements.get(cell, [])) > 1:
                locked[index] = char
        return locked

    def crossword_answer_matches_placement(self, placement, answer, initials):
        if len(answer) != len(placement.answer):
            return False, "length"
        normalized_initials = self.normalize_initial_input(initials or "")
        if len(normalized_initials) != len(answer):
            return False, "initials"
        locked = self.crossword_locked_indices(placement)
        for index, char in locked.items():
            if answer[index] != char:
                return False, "locked_conflict"
        display = placement.display_initials or placement.initials
        for index, marker in enumerate(display):
            if index in locked:
                continue
            if marker == "*":
                continue
            if index >= len(normalized_initials) or normalized_initials[index] != marker:
                return False, "initials"
        return True, ""

    def crossword_terms_for_answer(self, answer):
        return [term for term in self.terms if answers_equivalent(term.chinese, answer)]

    def crossword_answer_candidates(self, placement):
        candidates = []
        seen = set()
        for term in self.terms:
            answer = term.chinese
            if answer in seen:
                continue
            allowed, _reason = self.crossword_answer_matches_placement(placement, answer, term.initials)
            if allowed:
                candidates.append(answer)
                seen.add(answer)
        if placement.answer not in seen:
            candidates.insert(0, placement.answer)
        return candidates

    def crossword_answer_status(self, placement, answer):
        terms = self.crossword_terms_for_answer(answer)
        if not terms:
            return False, "not_in_library", [], ""
        locked_conflict = False
        for term in terms:
            allowed, reason = self.crossword_answer_matches_placement(placement, term.chinese, term.initials)
            if allowed:
                status = "exact" if answers_equivalent(term.chinese, placement.answer) else "alternative"
                return True, status, self.crossword_answer_candidates(placement), term.chinese
            if reason == "locked_conflict":
                locked_conflict = True
        return False, "locked_conflict" if locked_conflict else "wrong", self.crossword_answer_candidates(placement), ""

    def check_crossword_answer(self):
        if not self.game_active or self.record_saved:
            return
        placement = self.crossword_selected_placement()
        if not placement:
            return
        if placement.id in self.crossword_solved_ids:
            if self.crossword_feedback:
                self.crossword_feedback.config(text="这个编号已经填好了，换一个未完成的词。", fg="#9ca8c7")
            return
        answer = (self.crossword_answer_var.get() if self.crossword_answer_var else "").strip()
        if not answer:
            if self.crossword_feedback:
                self.crossword_feedback.config(text="先写一个答案。", fg="#f6d36b")
            return
        elapsed = time.perf_counter() - self.start_time
        attempt = {
            "word_id": placement.id,
            "target": placement.answer,
            "answer": answer,
            "answer_initials": self._lookup_initials(answer) or "",
            "time_seconds": round(elapsed, 3),
        }
        allowed, reason, candidates, accepted_answer = self.crossword_answer_status(placement, answer)
        attempt["accepted_answers"] = candidates
        if allowed:
            attempt["result"] = "success"
            attempt["accepted_as"] = reason
            attempt["accepted_answer"] = accepted_answer or answer
            self.crossword_attempts.append(attempt)
            self.crossword_solved_ids.add(placement.id)
            filled_answer = accepted_answer or answer
            self.crossword_filled_answers[placement.id] = filled_answer
            self.clear_crossword_answer_input()
            if self.crossword_feedback:
                extra = "（多解已接受）" if reason == "alternative" else ""
                if filled_answer != answer and answers_differ_only_by_person_alias(answer, filled_answer):
                    extra = "（作答正确，但是填入默认翻译）"
                elif filled_answer != answer and answers_equivalent(filled_answer, answer):
                    extra = "（已按标准写法填入）"
                self.crossword_feedback.config(text=f"{placement.id:02d} 号已填入：{filled_answer}{extra}", fg="#9ff2b2")
            self.refresh_crossword_word_list()
            self.draw_crossword_canvas()
            self.update_crossword_status()
            if len(self.crossword_solved_ids) >= len(self.crossword_puzzle.placements):
                self.finish_crossword_game(True)
            return
        attempt["result"] = reason
        self.crossword_attempts.append(attempt)
        if self.crossword_feedback:
            if reason == "locked_conflict":
                self.crossword_feedback.config(text="这个词在本局词库里，但关键交叉/已揭晓字对不上；这些字不能换。", fg="#ff9b89")
            elif reason == "not_in_library":
                self.crossword_feedback.config(text="这个词不在本局词库里。", fg="#ff9b89")
            else:
                self.crossword_feedback.config(text="还不对；非交叉格可用同词库、同题面首字母/掩码且交叉字一致的多解。", fg="#ff9b89")

    def unresolved_crossword_cells(self):
        if not self.crossword_puzzle:
            return []
        return [
            cell
            for cell in self.crossword_puzzle.grid
            if not self.crossword_cell_resolved(cell)
        ]

    def show_crossword_hint(self):
        if not self.game_active or self.record_saved:
            return
        if self.hint_cooldown_remaining() > 0:
            self.update_hint_cooldown_button()
            return
        candidates = self.unresolved_crossword_cells()
        if not candidates:
            if self.crossword_feedback:
                self.crossword_feedback.config(text="所有格子都已经可见，剩下就靠填词了。", fg="#9ca8c7")
            return
        row, col = random.choice(candidates)
        char = self.crossword_puzzle.grid[(row, col)]
        self.crossword_revealed_cells.add((row, col))
        hint_number = self.crossword_free_hint_count + self.crossword_paid_hint_count + 1
        normal_cost = self.crossword_character_hint_cost(hint_number)
        if self.crossword_free_hint_count < self.crossword_free_hint_quota:
            self.crossword_free_hint_count += 1
            cost = 0
            label = f"免费提示 {self.crossword_free_hint_count}/{self.crossword_free_hint_quota}"
            penalty_type = "free_crossword_character"
        else:
            self.crossword_paid_hint_count += 1
            cost = normal_cost
            self.add_crossword_penalty(cost)
            label = f"付费提示 {self.crossword_paid_hint_count}"
            penalty_type = "crossword_character"
        coord = self.crossword_cell_coord(row, col)
        line = f"{label}：{coord} 是“{char}”" + (f"    -{cost} 分" if cost else "")
        self.crossword_hint_lines.append(line)
        self.crossword_hint_penalties.append({"type": penalty_type, "coordinate": coord, "row": row, "col": col, "char": char, "cost": cost, "normal_cost": normal_cost})
        self.update_crossword_hint_box()
        self.draw_crossword_canvas()
        self.update_crossword_status()
        self.start_hint_cooldown()

    def show_crossword_library_hint(self):
        if not self.game_active or self.record_saved or not self.crossword_puzzle:
            return
        if self.crossword_library_hint_count >= self.crossword_library_hint_limit:
            if self.crossword_library_hint_button:
                self.crossword_library_hint_button.disable("已用完")
            return
        hinted_ids = {item.get("word_id") for item in self.crossword_hint_penalties if item.get("type") == "crossword_library"}
        candidates = [
            placement for placement in self.crossword_puzzle.placements
            if placement.id not in self.crossword_solved_ids and placement.id not in hinted_ids
        ]
        if not candidates:
            candidates = [placement for placement in self.crossword_puzzle.placements if placement.id not in self.crossword_solved_ids]
        if not candidates:
            return
        placement = random.choice(candidates)
        self.crossword_library_hint_count += 1
        cost = self.crossword_library_hint_cost()
        self.add_crossword_penalty(cost)
        text = f"词库提示 {self.crossword_library_hint_count}/{self.crossword_library_hint_limit}：第 {placement.id:02d} 词属于：{placement.source_label}"
        self.crossword_library_hint_texts.append(text)
        self.crossword_hint_penalties.append({"type": "crossword_library", "word_id": placement.id, "source_label": placement.source_label, "cost": cost})
        if self.crossword_library_hint_label:
            self.crossword_library_hint_label.config(text=f"{text}\n-{cost} 分")
        if self.crossword_library_hint_count >= self.crossword_library_hint_limit and self.crossword_library_hint_button:
            self.crossword_library_hint_button.disable("已用完")
        self.update_crossword_status()

    def selected_crossword_initials(self):
        placement = self.crossword_selected_placement()
        return self.normalize_initial_input(placement.initials if placement else "")

    def crossword_contains_blocked_initials(self, normalized_answer):
        blocked = self.selected_crossword_initials()
        return bool(blocked and blocked in normalized_answer)

    def handle_crossword_blocked_initial_input(self, blocked_text, clear_now=True):
        if time.perf_counter() < self.initial_warning_until:
            return
        self.crossword_cheat_warnings += 1
        self.crossword_raw_initial_buffer = ""
        self.crossword_raw_initial_last_at = 0.0
        self.initial_warning_until = time.perf_counter() + 0.8
        if clear_now:
            self.clear_crossword_answer_input()
        else:
            self.after_idle(self.clear_crossword_answer_input)
        if self.crossword_cheat_warnings <= 2:
            if not self.custom_mode:
                self.complete_achievement("first_initial_block")
            if self.crossword_feedback:
                self.crossword_feedback.config(text=f"题面首字母已清空。警告 {self.crossword_cheat_warnings}/2；再来一次会触发隐藏彩蛋。", fg="#f6d36b")
            self.after_idle(lambda: messagebox.showwarning("字谜输入警告", "题面首字母不应直接进入输入框。\n本次已清空；两次警告后再次触发会进入隐藏彩蛋。"))
            return
        self.crossword_cheat_pending = True
        self.after_idle(lambda blocked=blocked_text: self.cheat_crossword_game(blocked))

    def validate_crossword_answer_change(self, proposed):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.crossword_cheat_pending:
            return True
        normalized = self.normalize_initial_input(proposed)
        if not self.crossword_contains_blocked_initials(normalized):
            return True
        self.handle_crossword_blocked_initial_input(proposed, clear_now=False)
        return False

    def on_crossword_answer_change(self, *_args):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.crossword_cheat_pending:
            return
        answer = self.crossword_answer_var.get().strip() if self.crossword_answer_var else ""
        normalized = self.normalize_initial_input(answer)
        if self.crossword_contains_blocked_initials(normalized):
            self.handle_crossword_blocked_initial_input(answer, clear_now=True)

    def on_crossword_keypress(self, event):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.crossword_cheat_pending:
            return None
        normalized_char = self.normalize_key_event(event)
        if not normalized_char:
            self.after(1, self.scan_crossword_answer_for_blocked_initials)
            return None
        now = time.perf_counter()
        if now - self.crossword_raw_initial_last_at > 2.5:
            self.crossword_raw_initial_buffer = ""
        self.crossword_raw_initial_last_at = now
        self.crossword_raw_initial_buffer = (self.crossword_raw_initial_buffer + normalized_char)[-32:]
        if not self.crossword_contains_blocked_initials(self.crossword_raw_initial_buffer):
            self.after(1, self.scan_crossword_answer_for_blocked_initials)
            return None
        blocked_text = self.crossword_answer_var.get().strip() or self.crossword_raw_initial_buffer
        self.handle_crossword_blocked_initial_input(blocked_text, clear_now=False)
        return "break"

    def on_crossword_keyrelease(self, _event):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.crossword_cheat_pending:
            return None
        self.after(1, self.scan_crossword_answer_for_blocked_initials)
        return None

    def scan_crossword_answer_for_blocked_initials(self):
        if self.suppress_answer_trace or not self.game_active or self.record_saved or self.crossword_cheat_pending:
            return
        values = []
        if self.crossword_answer_var:
            values.append(self.crossword_answer_var.get())
        if self.answer_entry and self.answer_entry.winfo_exists():
            try:
                values.append(self.answer_entry.get())
            except tk.TclError:
                pass
        ime_text = self.read_ime_composition_text()
        if ime_text:
            values.append(ime_text)
        for value in values:
            if self.crossword_contains_blocked_initials(self.normalize_initial_input(value)):
                self.handle_crossword_blocked_initial_input(value, clear_now=True)
                return

    def cheat_crossword_game(self, blocked_initials):
        if not self.game_active or self.record_saved:
            return
        self.crossword_cheat_pending = False
        elapsed = time.perf_counter() - self.start_time
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        normal_score = self.crossword_current_score(elapsed)
        self.cheat_info = {
            "trigger": "crossword_initials",
            "input_initials": blocked_initials,
            "warning_count": self.crossword_cheat_warnings,
            "normal_score": normal_score,
        }
        self.crossword_attempts.append({
            "word_id": self.crossword_selected_id,
            "answer": blocked_initials,
            "time_seconds": round(elapsed, 3),
            "result": "cheat",
            "cheat_warning_count": self.crossword_cheat_warnings,
        })
        if not self.custom_mode:
            self.complete_achievement("crossword_cheat")
        if self.rank_mode and self.rank_kind == "crossword":
            self.complete_achievement("rank_cheat")
        record_path = self.save_crossword_record(False, elapsed, "cheated", "再次输入题面首字母")
        self.game_active = False
        self.record_saved = True
        if self.rank_mode and self.rank_kind == "crossword":
            self.show_rank_result(False, reason="触发隐藏彩蛋", elapsed=elapsed, record_path=record_path, cheated=True)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason="触发隐藏彩蛋", elapsed=elapsed, record_path=record_path, cheated=True)
            return
        self.show_crossword_result(False, elapsed, record_path, failed_reason="再次输入题面首字母", cheated=True)

    def fail_crossword_game(self, reason, finished_by="timeout"):
        if not self.game_active or self.record_saved:
            return
        elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.crossword_attempts.append({
            "word_id": self.crossword_selected_id,
            "answer": "",
            "time_seconds": round(elapsed, 3),
            "result": finished_by,
        })
        record_path = self.save_crossword_record(False, elapsed, finished_by, reason)
        self.game_active = False
        self.record_saved = True
        if self.rank_mode and self.rank_kind == "crossword":
            self.show_rank_result(False, reason=reason, elapsed=elapsed, record_path=record_path)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason=reason, elapsed=elapsed, record_path=record_path)
            return
        self.show_crossword_result(False, elapsed, record_path, failed_reason=reason)

    def finish_crossword_game(self, success=True):
        elapsed = time.perf_counter() - self.start_time
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        record_path = self.save_crossword_record(success, elapsed, "answered")
        self.game_active = False
        self.record_saved = True
        if self.rank_mode and self.rank_kind == "crossword":
            if success:
                self.timed_correct = 1
                self.rank_session_score = self.crossword_current_score(elapsed)
                mark_rank_passed(self.rank_subject, self.rank_id, "crossword", score=self.rank_session_score)
                self.show_rank_result(True, elapsed=elapsed, record_path=record_path)
            else:
                self.show_rank_result(False, reason="字谜段位未完成", elapsed=elapsed, record_path=record_path)
            return
        if self.is_custom_challenge_mode():
            self.timed_correct = 1 if success else 0
            self.show_custom_challenge_result(success, reason="" if success else "字谜未完成", elapsed=elapsed, record_path=record_path)
            return
        self.show_crossword_result(success, elapsed, record_path)

    def abandon_crossword(self):
        record_path = None
        elapsed = None
        if self.game_active and not self.record_saved and self.start_time and self.crossword_mode:
            elapsed = time.perf_counter() - self.start_time
            record_path = self.save_crossword_record(False, elapsed, "abandoned", "中途退出")
            self.record_saved = True
        self.game_active = False
        if self.rank_mode and self.rank_kind == "crossword":
            self.show_rank_result(False, reason="中途退出", elapsed=elapsed, record_path=record_path)
            return
        if self.is_custom_challenge_mode():
            self.show_custom_challenge_result(False, reason="自定义挑战中断", elapsed=elapsed, record_path=record_path)
            return
        self.show_difficulty()

    def save_crossword_record(self, success, elapsed, finished_by="answered", failed_reason=""):
        now = datetime.now()
        storage_dir = record_storage_dir(now)
        storage_dir.mkdir(parents=True, exist_ok=True)
        final_score = self.crossword_current_score(elapsed)
        if finished_by == "cheated":
            final_score = -abs(final_score)
        elif not success and finished_by != "abandoned":
            final_score = 0
        score_weight = self.crossword_score_weight()
        is_rank = self.rank_mode and self.rank_kind == "crossword"
        is_custom = bool(self.custom_mode)
        if is_custom:
            subject_value = self.custom_config.get("subject", "自定义")
            mode_value = "自定义"
            play_value = "自定义字谜"
            score_weight = 0.0
        else:
            random_label = "真·随机" if self.is_true_random_mode() else "随机"
            subject_value = self.rank_subject if is_rank else (random_label if self.is_crossword_random_scope() else self.mode)
            mode_value = self.rank_subject if is_rank else subject_value
            play_value = "字谜段位" if is_rank else ("随机字谜" if self.is_crossword_random_scope() else "字谜")
        try:
            file_names = [path.name for path in self.library_files]
        except Exception:
            file_names = []
        placements = []
        accepted_by_placement = {}
        cell_count = 0
        mask_count = 0
        difficulty_sum = 0
        for placement in self.crossword_puzzle.placements:
            mask_positions = sorted(getattr(placement, "mask_positions", set()) or [])
            accepted_answers = self.crossword_answer_candidates(placement)
            accepted_by_placement[str(placement.id)] = accepted_answers
            notice_text = term_notice_text(placement.answer, prefix="含有")
            mask_count += len(mask_positions)
            cell_count += len(placement.answer)
            difficulty_sum += int(getattr(placement.term, "difficulty", 5) or 5) + 0.5 * len(mask_positions)
            placements.append({
                "id": placement.id,
                "answer": placement.answer,
                "filled_answer": self.crossword_filled_answers.get(placement.id, ""),
                "accepted_answers": accepted_answers,
                "initials": placement.initials,
                "display_initials": self.crossword_initials_for_placement(placement),
                "mask_positions": mask_positions,
                "row": placement.row,
                "col": placement.col,
                "direction": placement.direction,
                "cells": [(row, col) for row, col, _char in placement.cells],
                "intersections": placement.intersections,
                "source_label": placement.source_label,
                "difficulty": int(getattr(placement.term, "difficulty", 5) or 5),
                "solved": 1 if placement.id in self.crossword_solved_ids else 0,
                "notice": notice_text,
                "has_greek_letter": 1 if term_has_greek_letter(placement.answer) else 0,
            })
        base_difficulty = difficulty_sum / max(len(self.crossword_puzzle.placements), 1)
        shape_bonus = 0.5 if getattr(self.crossword_puzzle, "cell_shape", "square") in {"triangle", "hex"} else 0.0
        rank_target_difficulty = 0
        if is_rank:
            _low, rank_target_difficulty, _center = self.crossword_rank_difficulty_window_for_id(self.rank_id)
        record = {
            "version": APP_VERSION,
            "id": uuid.uuid4().hex,
            "created_at": now.isoformat(timespec="seconds"),
            "mode": mode_value,
            "subject": subject_value,
            "play_mode": play_value,
            "difficulty": self.difficulty,
            "custom_mode": 1 if is_custom else 0,
            "custom_config": self.custom_config if is_custom else {},
            "custom_play_kind": self.custom_config.get("play_kind", "") if is_custom else "",
            "custom_files": file_names if is_custom else [],
            "custom_session_id": self.custom_session_id if is_custom else "",
            "custom_timed_enabled": 1 if (is_custom and self.is_custom_timed_enabled()) else 0,
            "custom_challenge_enabled": 1 if (is_custom and self.is_custom_challenge_mode()) else 0,
            "custom_challenge_target": self.custom_challenge_target() if (is_custom and self.is_custom_challenge_mode()) else 0,
            "custom_challenge_progress": len(self.crossword_solved_ids) if is_custom else 0,
            "rank_mode": 1 if is_rank else 0,
            "exclude_from_stats": 1 if is_custom else 0,
            "rank_subject": self.rank_subject if is_rank else "",
            "rank_kind": "crossword" if is_rank else "",
            "rank_progress_key": rank_progress_key(self.rank_subject, "crossword") if is_rank else "",
            "rank_id": self.rank_id if is_rank else 0,
            "rank_question_index": len(self.rank_requirements) if (is_rank and success) else (1 if is_rank else 0),
            "rank_passed_session_id": self.rank_session_id if is_rank else "",
            "rank_target_difficulty": rank_target_difficulty if is_rank else 0,
            "rank_relaxed": 0,
            "rank_session_score": final_score if (is_rank and success) else 0,
            "rank_hint_used": (self.crossword_free_hint_count + self.crossword_paid_hint_count + self.crossword_library_hint_count) if is_rank else 0,
            "rank_hint_limit": (self.crossword_free_hint_quota + self.crossword_library_hint_limit) if is_rank else 0,
            "crossword_mode": 1,
            "crossword_session_id": self.crossword_session_id,
            "crossword_width": self.crossword_puzzle.width,
            "crossword_height": self.crossword_puzzle.height,
            "crossword_cell_shape": getattr(self.crossword_puzzle, "cell_shape", "square"),
            "crossword_rank_size": self.crossword_rank_size if is_rank else 0,
            "crossword_rank_word_count": self.crossword_rank_word_count if is_rank else 0,
            "crossword_rank_seconds": self.crossword_rank_seconds if is_rank else 0,
            "crossword_word_count": len(self.crossword_puzzle.placements),
            "crossword_solved_count": len(self.crossword_solved_ids),
            "crossword_cell_count": cell_count,
            "crossword_intersection_count": self.crossword_puzzle.intersection_count,
            "crossword_isolated_count": self.crossword_puzzle.isolated_count,
            "crossword_placements": placements,
            "question_initials": " / ".join(placement["display_initials"] for placement in placements),
            "displayed_initials": " / ".join(placement["display_initials"] for placement in placements),
            "mask_count": mask_count,
            "clue_mode": 0,
            "selected_answer": f"字谜{len(self.crossword_puzzle.placements)}词",
            "base_term_difficulty": round(base_difficulty, 3),
            "term_difficulty": round(base_difficulty, 3),
            "effective_difficulty": round(base_difficulty + shape_bonus, 3),
            "accepted_answers": sorted({answer for answers in accepted_by_placement.values() for answer in answers}),
            "crossword_accepted_answers": accepted_by_placement,
            "source_file": "",
            "source_label": self.scope_text,
            "library_files": file_names,
            "scope": self.scope_text,
            "all_answers": self.crossword_attempts,
            "success": success,
            "finished_by": finished_by,
            "failed_reason": failed_reason,
            "cheat_detected": 1 if finished_by == "cheated" else 0,
            "cheat_info": self.cheat_info if finished_by == "cheated" else {},
            "elapsed_seconds": round(elapsed, 3),
            "hint_count": self.crossword_free_hint_count + self.crossword_paid_hint_count,
            "hint_cooldown_seconds": self.hint_cooldown_seconds(),
            "free_hint_quota": self.crossword_free_hint_quota,
            "free_hint_count": self.crossword_free_hint_count,
            "paid_hint_count": self.crossword_paid_hint_count,
            "hints": self.crossword_hint_lines,
            "hint_penalties": self.crossword_hint_penalties,
            "used_library_hint": self.crossword_library_hint_count,
            "library_hint_text": "\n".join(self.crossword_library_hint_texts),
            "score_start": self.crossword_start_score,
            "score_time_cost": int(elapsed),
            "score_penalty": self.crossword_score_penalty,
            "score": final_score,
            "score_weight": score_weight,
            "weighted_score": round(final_score * score_weight, 3),
            "timed_session": 1 if is_rank else 0,
        }
        path = storage_dir / f"{now.strftime('%Y%m%d_%H%M%S')}_{record['id'][:8]}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        self.refresh_achievements()
        return path

    def crossword_answer_summary_text(self):
        parts = []
        for placement in self.crossword_puzzle.placements:
            filled = self.crossword_filled_answers.get(placement.id)
            candidates = self.crossword_answer_candidates(placement)
            if len(candidates) > 1:
                answer_text = " / ".join(candidates)
                if filled and filled != placement.answer:
                    parts.append(f"{placement.id:02d}.{filled}（可：{answer_text}）")
                else:
                    parts.append(f"{placement.id:02d}.{placement.answer}（可：{answer_text}）")
            elif filled and filled != placement.answer:
                parts.append(f"{placement.id:02d}.{filled}（原：{placement.answer}）")
            else:
                parts.append(f"{placement.id:02d}.{placement.answer}")
        return "、".join(parts)

    def show_crossword_result(self, success, elapsed, record_path, failed_reason="", cheated=False):
        self.clear(transition=False)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True)
        self._start_backdrop("constellation", frame)
        card = tk.Frame(frame, bg="#182033", highlightbackground="#4b5877", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.74, relheight=0.76)
        if cheated:
            final_score = -abs(int(self.cheat_info.get("normal_score", self.crossword_current_score(elapsed))))
            title = "字谜隐藏彩蛋"
            title_color = "#ff6b8a"
        else:
            final_score = self.crossword_current_score(elapsed) if success else 0
            title = "字谜完成" if success else "字谜结束"
            title_color = "#9ff2b2" if success else "#ff9b89"
        tk.Label(card, text=title, fg=title_color, bg="#182033", font=("Microsoft YaHei UI", 38, "bold")).pack(pady=(38, 8))
        if failed_reason:
            tk.Label(card, text=failed_reason, fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(pady=(0, 8))
        tk.Label(card, text=f"进度 {len(self.crossword_solved_ids)}/{len(self.crossword_puzzle.placements)} 词    用时 {elapsed:.1f} 秒", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 18, "bold")).pack(pady=4)
        tk.Label(card, text=f"积分 {final_score} 分", fg="#9ff2b2" if final_score >= 0 else "#ff9b89", bg="#182033", font=("Consolas", 24, "bold")).pack(pady=4)
        score_weight = self.crossword_score_weight()
        score_note = "自定义字谜不计总积分、Rating 和成就" if self.custom_mode else f"计入总积分 {format_score(final_score * score_weight)} 分（权重 {score_weight:g}）"
        tk.Label(card, text=score_note, fg="#9ca8c7", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(pady=2)
        detail = tk.Frame(card, bg="#182033")
        detail.pack(fill="x", padx=74, pady=(18, 8))
        tk.Label(detail, text=f"网格 {self.crossword_puzzle.width}×{self.crossword_puzzle.height}    交叉 {self.crossword_puzzle.intersection_count}    孤立 {self.crossword_puzzle.isolated_count}", fg="#c8d2ee", bg="#182033", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", pady=2)
        answers = self.crossword_answer_summary_text()
        tk.Label(detail, text=self.smart_wrap_text(f"答案：{answers}", 54), fg="#dce6ff", bg="#182033", justify="left", font=("Microsoft YaHei UI", 11)).pack(anchor="w", pady=(8, 4))
        try:
            record_display = record_path.relative_to(RECORD_DIR.parent).as_posix()
        except ValueError:
            record_display = f"record/{record_path.name}"
        tk.Label(detail, text=f"记录已保存：{record_display}", fg="#7683a3", bg="#182033", font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(6, 14))
        buttons = tk.Frame(card, bg="#182033")
        buttons.pack()
        if self.custom_mode:
            HoverButton(buttons, "再练一局", self.restart_custom_session, width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回配置", self.show_custom_config, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)
        else:
            HoverButton(buttons, "再来一局", lambda: self.start_game(self.difficulty), width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "返回模式", self.show_mode_select, width=180, height=62, accent="#9fb7ff").grid(row=0, column=1, padx=12)

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
        if self.custom_mode:
            try:
                visible = int(self.custom_config.get("clue_initial_lines") or 1)
            except (TypeError, ValueError):
                visible = 1
            self.clue_visible_count = max(1, min(len(self.clue_lines), visible))
        else:
            self.clue_visible_count = 1

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
        root = tk.Frame(self.container, bg="#111725")
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
        else:
            self.hint_box = tk.Frame(panel, bg="#182033")
            self.hint_box.pack(fill="x", padx=54, pady=22)
            self._render_hints()
        if self.rank_mode:
            self.start_hint_cooldown(initial=True)
        else:
            self.update_hint_cooldown_button()

        side = tk.Frame(root, bg="#111725", width=side_width)
        side.pack(side="left", fill="both", expand=True)
        side.pack_propagate(False)
        tk.Label(side, text="剩余" if self.is_timed_mode() else "计时", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        self.timer_label = tk.Label(side, text="0.0 秒", fg="#fff2bd", bg="#111725", font=("Consolas", 28, "bold"))
        self.timer_label.pack(anchor="w", pady=(4, 14))
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
            rule_text = "本题不显示首字母，但会显示答案字数。\n初始只显示第一句线索。\n第一次提示免费，之后从揭晓第三条线索开始扣分。\n共五条线索，普通/困难可能出现破碎线索。\n揭晓答案会记为未答出。"
        else:
            rule_text = "同首字母的词库内答案都算对。\n普通/困难/噩梦可能用 * 掩码首字母；* 处不限，只检查未掩码位置。\n当前模式总词库里、但不在本轮范围内的匹配词，才会提示超纲。\n提示揭开全部汉字或主动揭晓答案时，本题失败。"
        tk.Label(
            side,
            text=rule_text,
            justify="left",
            fg="#9ca8c7",
            bg="#111725",
            wraplength=side_text_width,
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", pady=(4, 18))
        tk.Label(side, text="范围", fg="#8fb6ff", bg="#111725", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        self.render_side_scope_text(side, self.scope_text, side_text_width)
        self.library_hint_button = HoverButton(side, "提示词库", self.show_library_hint, width=170, height=54, accent="#ffbd7e")
        self.library_hint_button.pack(anchor="w", pady=(0, 8))
        self.tutorial_library_hint_button = self.library_hint_button
        self.library_hint_label = tk.Label(
            side,
            text="",
            justify="left",
            fg="#f6d36b",
            bg="#111725",
            wraplength=side_text_width,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.library_hint_label.pack(anchor="w")
        self._tick()
        self.render_tutorial_game_overlay()

    def render_side_scope_text(self, parent, text, side_text_width):
        text = str(text or "")
        wrap_chars = max(16, min(46, int(side_text_width / 13)))
        estimated_lines = 0
        for line in text.splitlines() or [""]:
            estimated_lines += max(1, math.ceil(len(line) / wrap_chars))
        if estimated_lines <= 4:
            tk.Label(
                parent,
                text=text,
                justify="left",
                fg="#c8d2ee",
                bg="#111725",
                wraplength=side_text_width,
                font=("Microsoft YaHei UI", 11),
            ).pack(anchor="w", pady=(4, 18))
            return None

        visible_lines = 7
        box = tk.Frame(parent, bg="#101827", highlightbackground="#30384e", highlightthickness=1)
        box.pack(fill="x", pady=(4, 18))
        text_widget = tk.Text(
            box,
            height=visible_lines,
            wrap="word",
            fg="#c8d2ee",
            bg="#101827",
            bd=0,
            relief="flat",
            insertbackground="#fff8dc",
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

    def is_accepted_answer(self, answer):
        return any(answers_equivalent(answer, accepted) for accepted in self.accepted_answers)

    def current_term_notice_text(self):
        return term_notice_text(self.current.chinese) if self.current else ""

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
        return BonusGuessApp.record_greek_answers(record)

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
                self.feedback.config(text="题面首字母已清空。再试一次会触发隐藏彩蛋。", fg="#f6d36b")
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
        if self.tutorial_active:
            if self.free_hint_count + self.paid_hint_count <= 0:
                self.feedback.config(text="教程会先带你试用一次字词提示。点击“提示”后再作答。", fg="#f6d36b")
                self.advance_tutorial_game_step("hint")
                return
            if not self.library_hint_used:
                self.feedback.config(text="还要试用一次“提示词库”。教程中免费，正式局通常会扣分。", fg="#f6d36b")
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
                self.feedback.config(text=f"教程提示：本题答案是“{self.current.chinese}”，输入后点击确认即可完成。", fg="#f6d36b")
            else:
                self.feedback.config(text="还不对，顺着线索再想想。", fg="#ff9b89")
        elif self.initials_match_question(answer_initials):
            attempt["result"] = "out_of_scope"
            self.attempts.append(attempt)
            if self.tutorial_active:
                self.feedback.config(text=f"这个答案首字母匹配，但教程题要填写“{self.current.chinese}”。", fg="#f6d36b")
            else:
                self.feedback.config(text="超纲啦，再想想~", fg="#f6d36b")
        else:
            attempt["result"] = "wrong"
            self.attempts.append(attempt)
            if self.tutorial_active:
                self.feedback.config(text=f"教程提示：本题答案是“{self.current.chinese}”，再试一次。", fg="#f6d36b")
            else:
                self.feedback.config(text="还不对，换个词试试。", fg="#ff9b89")

    def current_score(self, elapsed=None):
        if elapsed is None:
            elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        return 1000 - int(elapsed) - self.score_penalty

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
        for term in self.terms:
            if answers_equivalent(term.chinese, answer):
                return term.initials
        lookup_mode = None if self.is_random_group_mode() or self.custom_mode else self.mode
        return self.library.lookup_initials(answer, lookup_mode)

    def show_clue_hint(self):
        if self.clue_visible_count >= len(self.clue_lines):
            if self.feedback:
                self.feedback.config(text="五条线索已经全部显示。", fg="#9ca8c7")
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
        if self.tutorial_active and self.tutorial_step in {"question", "hint"}:
            self.advance_tutorial_game_step("library")

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
        if self.tutorial_active:
            HoverButton(buttons, "再试教程题", self.start_tutorial_round, width=180, height=62, accent="#9ff2b2").grid(row=0, column=0, padx=12)
            HoverButton(buttons, "跳过教程", self.skip_tutorial, width=180, height=62, accent="#ff9b89").grid(row=0, column=1, padx=12)
        elif self.custom_mode:
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
        if self.rank_kind == "crossword":
            if not self.crossword_puzzle:
                return []
            lines = []
            for placement in self.crossword_puzzle.placements:
                direction = "横" if placement.direction == "across" else "纵"
                initials = self.crossword_initials_for_placement(placement)
                accepted = self.crossword_answer_candidates(placement)
                lines.append(f"{placement.id:02d} {direction} {len(placement.answer)}字 {initials}：{'、'.join(accepted)}")
            return lines
        entries = list(getattr(self, "rank_answer_history", []) or [])
        if not entries:
            current = self.current_rank_answer_entry()
            if current:
                entries = [current]
        lines = []
        for entry in entries:
            target = entry.get("target_difficulty")
            try:
                target_text = f"≥{float(target):g}"
            except (TypeError, ValueError):
                target_text = ""
            initials = entry.get("displayed_initials") or "线索题"
            accepted = entry.get("accepted_answers") or [entry.get("answer", "")]
            lines.append(
                f"{int(entry.get('index') or 0):02d} {entry.get('difficulty', '')}{target_text} "
                f"{initials}：{'、'.join(str(answer) for answer in accepted if answer)}"
            )
        return lines

    def render_rank_failure_answers(self, parent):
        if not self.rank_mode:
            return
        lines = self.rank_answer_summary_lines()
        if not lines:
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
            height=max(4, min(9, len(lines))),
            wrap="char",
            fg="#dce6ff",
            bg="#111827",
            insertbackground="#dce6ff",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#30384e",
            font=("Microsoft YaHei UI", 10),
        )
        scrollbar = tk.Scrollbar(shell, orient="vertical", command=answer_box.yview)
        answer_box.configure(yscrollcommand=scrollbar.set)
        answer_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        answer_box.insert("1.0", "\n".join(lines))
        answer_box.config(state="disabled")
        self.bind_scroll_wheel(shell, answer_box)

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
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.76, relheight=0.78)
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
            badge_canvas = tk.Canvas(card, width=badge_width, height=badge_height, bd=0, highlightthickness=0, bg="#182033")
            badge_canvas.pack(pady=(14, 8))
            draw_rank_badge(badge_canvas, badge_id, badge_width, badge_height, selected=True)
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
        elif not success and finished_by != "abandoned":
            final_score = 0
        score_weight = self.current_score_weight()
        subject_value = self.rank_subject if is_rank else (self.custom_config.get("subject", self.mode) if is_custom else self.mode)
        mode_value = self.rank_subject if is_rank else ("自定义" if is_custom else self.mode)
        play_value = rank_kind_label(self.rank_kind) if is_rank else ("自定义" if is_custom else self.play_mode)
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
            "clue_hint_count": max(0, self.clue_visible_count - 1) if self.is_clue_mode() else 0,
            "clue_penalty": sum(item.get("cost", 0) for item in self.hint_penalties if item.get("type") == "clue"),
            "selected_answer": self.current.chinese,
            "base_term_difficulty": self.current.difficulty,
            "term_difficulty": self.current.difficulty,
            "effective_difficulty": self.effective_difficulty,
            "accepted_answers": self.accepted_answers,
            "term_notice": self.current_term_notice_text(),
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
        self.refresh_achievements()
        return path

    def on_close(self):
        if self.tutorial_active:
            self.game_active = False
            self.record_saved = True
            self.destroy()
            return
        if self.game_active and not self.record_saved and self.start_time and self.crossword_mode and self.crossword_puzzle:
            elapsed = time.perf_counter() - self.start_time
            self.save_crossword_record(False, elapsed, "abandoned", "关闭窗口")
            self.record_saved = True
            self.destroy()
            return
        if self.game_active and not self.record_saved and self.start_time and self.current:
            elapsed = time.perf_counter() - self.start_time
            self.save_record(False, elapsed, "abandoned")
            self.record_saved = True
        self.destroy()

    def complete_achievement(self, achievement_id, when=None):
        if self.is_spectating() or self.tutorial_active:
            self.achievements = read_achievements()
            return
        self.achievements = read_achievements()
        completed = self.achievements.setdefault("completed", {})
        if achievement_id in completed:
            return
        completed[achievement_id] = (when or datetime.now()).isoformat(timespec="seconds")
        write_achievements(self.achievements)

    def refresh_achievements(self):
        if self.is_spectating() or self.tutorial_active:
            self.achievements = read_achievements()
            return
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
        total_clue_success = 0
        total_random_success = 0
        total_cheats = 0
        total_crossword_words = 0
        total_greek_success = 0
        rank_records = [record for record in all_records if record.get("rank_mode")]
        rank_records.sort(key=record_datetime)
        distinct_rank_passes = {}
        for record in rank_records:
            is_cheat = bool(record.get("cheat_detected")) or record.get("finished_by") == "cheated"
            if is_cheat:
                mark("rank_cheat", record)
            if not record.get("success"):
                continue
            try:
                rank_id = int(record.get("rank_id") or 0)
            except (TypeError, ValueError):
                continue
            if rank_id <= 0 or rank_id > len(RANK_CHALLENGES):
                continue
            try:
                progress_index = int(record.get("rank_question_index") or 0)
            except (TypeError, ValueError):
                progress_index = 0
            if progress_index < len(rank_by_id(rank_id)["requirements"]):
                continue
            rank_kind = normalize_rank_kind(record.get("rank_kind"))
            progress_key = record.get("rank_progress_key") or rank_progress_key(record.get("rank_subject") or record.get("subject"), rank_kind)
            distinct_rank_passes.setdefault((progress_key, rank_id), record)
            mark("first_rank_pass", record)
            if rank_kind == "clue":
                mark("first_clue_rank_pass", record)
            elif rank_kind == "timed":
                mark("first_timed_rank_pass", record)
            elif rank_kind == "crossword":
                mark("first_crossword_rank_pass", record)
            else:
                mark("first_free_rank_pass", record)
            if rank_id >= 5:
                mark("rank_class_5_pass", record)
            if rank_id >= 10:
                mark("rank_class_10_pass", record)
            if rank_id >= 15:
                mark("rank_class_15_pass", record)
            try:
                rank_hint_used = int(record.get("rank_hint_used") or 0)
            except (TypeError, ValueError):
                rank_hint_used = 0
            if rank_hint_used == 0:
                mark("rank_no_hint_pass", record)
            distinct_count = len(distinct_rank_passes)
            if distinct_count >= 5:
                mark("rank_distinct_5", record)
            if distinct_count >= 15:
                mark("rank_distinct_15", record)

        rank_progress = read_rank_progress()
        progress_passes = [
            (subject_key, rank_id)
            for subject_key, info in (rank_progress.get("subjects") or {}).items()
            for rank_id in rank_passed_ids(info)
        ]
        if progress_passes:
            mark("first_rank_pass")
        if any("::clue" in subject_key for subject_key, _rank_id in progress_passes):
            mark("first_clue_rank_pass")
        if any("::timed" in subject_key for subject_key, _rank_id in progress_passes):
            mark("first_timed_rank_pass")
        if any("::crossword" in subject_key for subject_key, _rank_id in progress_passes):
            mark("first_crossword_rank_pass")
        if any("::clue" not in subject_key and "::timed" not in subject_key and "::crossword" not in subject_key for subject_key, _rank_id in progress_passes):
            mark("first_free_rank_pass")
        if any(rank_id >= 5 for _subject_key, rank_id in progress_passes):
            mark("rank_class_5_pass")
        if any(rank_id >= 10 for _subject_key, rank_id in progress_passes):
            mark("rank_class_10_pass")
        if any(rank_id >= 15 for _subject_key, rank_id in progress_passes):
            mark("rank_class_15_pass")
        if len(set(progress_passes)) >= 5:
            mark("rank_distinct_5")
        if len(set(progress_passes)) >= 15:
            mark("rank_distinct_15")
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
            play_label = record_play_mode(record)
            is_timed = play_label in {"限时", "随机-限时"} or bool(record.get("timed_session"))
            is_clue = play_label in {"线索", "随机-线索"} or (bool(record.get("clue_mode")) and not bool(record.get("crossword_mode")))
            is_random = is_random_record(record)
            is_true_random = str(record.get("difficulty") or "") == "真·随机" or str(record.get("mode") or "") == "真·随机"
            is_cheat = bool(record.get("cheat_detected")) or record.get("finished_by") == "cheated"
            is_crossword = bool(record.get("crossword_mode"))
            crossword_placements = record.get("crossword_placements") if isinstance(record.get("crossword_placements"), list) else []
            greek_answers = self.record_greek_answers(record)
            if greek_answers:
                mark("first_greek_term", record)
                if is_crossword:
                    mark("crossword_greek_term", record)
            if len(str(record.get("selected_answer") or "")) == 1 or any(len(str(item.get("answer") or "")) == 1 for item in crossword_placements if isinstance(item, dict)):
                mark("one_char_term", record)
            if mask_count:
                mark("first_masked_round", record)
            if is_timed:
                total_timed_time += float(record.get("elapsed_seconds") or 0)
            if is_cheat:
                total_cheats += 1
                mark("first_cheat", record)
                if is_timed:
                    mark("timed_cheat", record)
                if is_crossword:
                    mark("crossword_cheat", record)

            if success:
                total_success += 1
                streak += 1
                mark("first_success", record)
                greek_success_answers = self.record_success_greek_answers(record)
                if greek_success_answers:
                    total_greek_success += len(greek_success_answers)
                    mark("first_greek_success", record)
                    if total_greek_success >= 10:
                        mark("greek_success_10", record)
                if play_label == "自由":
                    mark("first_free_success", record)
                if is_random:
                    total_random_success += 1
                    mark("first_random_success", record)
                    if total_random_success >= 20:
                        mark("random_success_20", record)
                if is_true_random:
                    mark("true_random_success", record)
                if is_crossword:
                    mark("first_crossword_success", record)
                    try:
                        crossword_words = int(record.get("crossword_solved_count") or record.get("crossword_word_count") or 0)
                    except (TypeError, ValueError):
                        crossword_words = 0
                    total_crossword_words += crossword_words
                    try:
                        intersection_count = int(record.get("crossword_intersection_count") or 0)
                    except (TypeError, ValueError):
                        intersection_count = 0
                    if intersection_count >= 10:
                        mark("crossword_crossings_10", record)
                    if char_hints == 0 and library_hints == 0:
                        mark("crossword_no_hint_success", record)
                    shape = record.get("crossword_cell_shape")
                    if shape == "triangle":
                        mark("crossword_triangle_success", record)
                    elif shape == "hex":
                        mark("crossword_hex_success", record)
                    if total_crossword_words >= 50:
                        mark("crossword_words_50", record)
                if mask_count:
                    total_masked_success += 1
                    mark("first_masked_success", record)
                    if mask_count >= 3:
                        mark("three_mask_success", record)
                if is_timed:
                    total_timed_success += 1
                    mark("first_timed_success", record)
                if is_clue:
                    total_clue_success += 1
                    mark("first_clue_success", record)
                    if char_hints == 0 and library_hints == 0:
                        mark("clue_no_hint_success", record)
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
            if total_clue_success >= 20:
                mark("clue_success_20", record)
            if total_clue_success >= 100:
                mark("clue_success_100", record)
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
            ("隐藏彩蛋", f"{summary['cheat_count']}"),
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
        term_parts = [f"{i}:{summary['difficulty_counts'].get(i, 0)}" for i in range(1, 13)]
        if summary["difficulty_counts"].get(0, 0):
            term_parts.append(f"未知:{summary['difficulty_counts'].get(0, 0)}")
        term_text = "  ".join(term_parts)
        mode_order = ["入门", "简单", "普通", "困难", "噩梦", "混合模式", "未知"]
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
        mode_order = ["入门", "简单", "普通", "困难", "噩梦", "混合模式", "未知"]
        score_parts = [
            f"{name}:{format_score(summary['mode_scores'].get(name, 0))}"
            for name in mode_order
            if summary["mode_scores"].get(name, 0) or summary["mode_counts"].get(name, 0)
        ]
        lines = [
            f"答对 {summary['success_count']} 题，未答对 {summary['wrong_count']} 题，中途退出 {summary['abandoned_count']} 次，正确率 {accuracy:.1f}%",
            f"平均用时 {summary['avg_time']:.1f} 秒，平均计入积分 {summary['avg_score']:.1f} 分，平均原始得分 {summary['avg_raw_score']:.1f} 分",
            f"Rating {format_rating(summary['rating'])}，去重B20均值 {format_rating(summary['rating_best_average'])}，R10均值 {format_rating(summary['rating_recent_average'])}",
            f"最终总积分按入门 0.1、简单 0.2、普通 0.3、困难 0.4、噩梦 0.5、混合模式/真·随机 0.25 加权；随机四玩法按所选难度同口径计分。原始总分 {summary['raw_total_score']} 分",
            f"字词/线索提示：免费字词 {summary['free_char_hints']}，付费字词或线索 {summary['paid_char_hints']}，总计 {summary['char_hints']}",
            f"各模式计入积分：{'  '.join(score_parts) if score_parts else '暂无'}",
            f"提交答案统计：正确 {result.get('success', 0)}，错误 {result.get('wrong', 0)}，超纲 {result.get('out_of_scope', 0)}",
        ]
        for line in lines:
            tk.Label(box, text=line, fg="#dce6ff", bg="#182033", justify="left", anchor="w", wraplength=1080, font=("Microsoft YaHei UI", 11)).pack(anchor="w", fill="x", padx=16, pady=3)

        dimensions = [
            ("按学科", summary.get("by_subject", {}), ["物理模式", "数学模式", "随机", "真·随机", "未知"]),
            ("按玩法", summary.get("by_play_mode", {}), ["自由", "限时", "线索", "字谜", "随机-自由", "随机-限时", "随机-线索", "随机字谜", "真·随机-自由", "真·随机-限时", "真·随机-线索", "真·随机", "未知"]),
            ("按选词难度", summary.get("by_difficulty", {}), ["入门", "简单", "普通", "困难", "噩梦", "混合模式", "真·随机", "未知"]),
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
            status = "隐藏彩蛋"
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

    def project_path_text(self, path):
        try:
            return path.relative_to(PROJECT_DIR).as_posix()
        except ValueError:
            return str(path)

    def admin_json_files(self, root, include_state_files=True):
        if not root.exists():
            return []
        files = sorted(root.rglob("*.json"), key=lambda item: item.as_posix())
        if include_state_files:
            return files
        state_names = {"achievements.json", "rank_progress.json"}
        return [path for path in files if path.name not in state_names]

    def account_admin_snapshot(self, account):
        paths = account_paths(account["id"])
        records = load_record_entries(paths["record_dir"])
        achievements_data = read_achievements(paths["achievements_file"])
        summary = summarize_records(records, achievements_data=achievements_data)
        record_files = self.admin_json_files(paths["record_dir"], include_state_files=False)
        profile_files = self.admin_json_files(paths["profile_dir"])
        return {
            "account": account,
            "paths": paths,
            "records": records,
            "summary": summary,
            "record_files": record_files,
            "profile_files": profile_files,
            "achievements": achievements_data,
        }

    def show_admin_dashboard(self):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以查看后台数据。")
            self.show_home()
            return
        self.clear()
        self._topbar("后台数据", self.show_settings)
        frame = tk.Frame(self.container, bg="#111725")
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self._start_backdrop("grid", frame)

        snapshots = [self.account_admin_snapshot(account) for account in list_public_accounts()]
        legacy_record_dir = PROJECT_DIR / "record"
        legacy_records = load_record_entries(legacy_record_dir)
        legacy_files = self.admin_json_files(legacy_record_dir, include_state_files=False)
        total_records = sum(len(item["records"]) for item in snapshots)
        total_record_files = sum(len(item["record_files"]) for item in snapshots)
        total_profile_files = sum(len(item["profile_files"]) for item in snapshots)

        top = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        top.pack(fill="x", pady=(0, 14))
        cards = [
            ("账号数", str(len(snapshots))),
            ("用户记录", str(total_records)),
            ("record 文件", str(total_record_files)),
            ("profile 文件", str(total_profile_files)),
            ("旧版 record", str(len(legacy_files))),
        ]
        for index, (name, value) in enumerate(cards):
            cell = tk.Frame(top, bg="#182033")
            cell.grid(row=0, column=index, sticky="ew", padx=18, pady=12)
            top.grid_columnconfigure(index, weight=1)
            tk.Label(cell, text=name, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
            tk.Label(cell, text=value, fg="#fff2bd", bg="#182033", font=("Consolas", 19, "bold")).pack(anchor="w", pady=(3, 0))

        detail_text = "收起文件" if self.admin_show_details else "展开文件"
        HoverButton(frame, detail_text, self.toggle_admin_details, width=140, height=46, accent="#8fb6ff").pack(anchor="w", pady=(0, 10))
        tk.Label(
            frame,
            text="选择一个账号进入旁观主页。旁观模式只读，可以查看该玩家的主页、历史记录、成就和玩家档案，不能开始游戏或修改数据。",
            fg="#c8d2ee",
            bg="#111725",
            justify="left",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        scroll = self.make_scroll_frame(frame)
        for snapshot in snapshots:
            self.render_admin_account_row(scroll, snapshot)
        self.render_legacy_record_row(scroll, legacy_record_dir, legacy_records, legacy_files)

    def toggle_admin_details(self):
        self.admin_show_details = not self.admin_show_details
        self.show_admin_dashboard()

    def render_admin_account_row(self, parent, snapshot):
        account = snapshot["account"]
        summary = snapshot["summary"]
        paths = snapshot["paths"]
        row = tk.Frame(parent, bg="#182033", highlightbackground="#30384e", highlightthickness=1)
        row.pack(fill="x", pady=6)
        title = f"{account.get('nickname', '')}    id={account.get('id', '')}"
        if account.get("is_admin"):
            title += "    管理员"
        tk.Label(row, text=title, fg="#fff2bd", bg="#182033", justify="left", anchor="w", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", fill="x", padx=14, pady=(10, 3))
        meta = (
            f"创建 {account.get('created_at') or '未知'}    "
            f"最近登录 {account.get('last_login_at') or '未记录'}    "
            f"Rating {format_rating(summary['rating'])}    "
            f"题数 {summary['total_count']}    "
            f"总积分 {format_score(summary['total_score'])}    "
            f"成就 {summary['achievement_count']}/{summary['achievement_total']}"
        )
        tk.Label(row, text=meta, fg="#c8d2ee", bg="#182033", wraplength=1080, justify="left", font=("Microsoft YaHei UI", 10)).pack(anchor="w", padx=14, pady=(0, 4))
        path_line = f"record: {self.project_path_text(paths['record_dir'])}    profile: {self.project_path_text(paths['profile_dir'])}"
        tk.Label(row, text=path_line, fg="#9ca8c7", bg="#182033", wraplength=1080, justify="left", font=("Consolas", 9)).pack(anchor="w", padx=14, pady=(0, 8))
        row_buttons = tk.Frame(row, bg="#182033")
        row_buttons.pack(anchor="w", padx=14, pady=(0, 10))
        HoverButton(row_buttons, "旁观主页", lambda account=account: self.enter_spectator_mode(account), width=132, height=46, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 8))
        HoverButton(row_buttons, "只看记录", lambda account=account: self.enter_spectator_history(account), width=132, height=46, accent="#8fb6ff").grid(row=0, column=1, padx=8)
        if not self.admin_show_details:
            return

        file_box = tk.Frame(row, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
        file_box.pack(fill="x", padx=14, pady=(0, 12))
        state_files = [
            paths["achievements_file"],
            paths["rank_progress_file"],
            paths["player_settings_file"],
            paths["daily_terms_file"],
        ]
        file_lines = [self.project_path_text(path) for path in state_files if path.exists()]
        file_lines.extend(self.project_path_text(path) for path in snapshot["record_files"])
        if not file_lines:
            file_lines = ["暂无 JSON 数据文件。"]
        tk.Label(file_box, text="\n".join(file_lines), fg="#dce6ff", bg="#111827", justify="left", anchor="w", wraplength=1060, font=("Consolas", 9)).pack(anchor="w", fill="x", padx=12, pady=10)

    def render_legacy_record_row(self, parent, legacy_record_dir, legacy_records, legacy_files):
        row = tk.Frame(parent, bg="#182033", highlightbackground="#30384e", highlightthickness=1)
        row.pack(fill="x", pady=6)
        tk.Label(row, text="旧版根 record 文件夹", fg="#f6d36b", bg="#182033", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=14, pady=(10, 3))
        tk.Label(
            row,
            text=f"{self.project_path_text(legacy_record_dir)}    记录 {len(legacy_records)}    JSON {len(legacy_files)}",
            fg="#c8d2ee",
            bg="#182033",
            wraplength=1080,
            justify="left",
            font=("Consolas", 10),
        ).pack(anchor="w", padx=14, pady=(0, 8))
        if not self.admin_show_details:
            return
        file_box = tk.Frame(row, bg="#111827", highlightbackground="#30384e", highlightthickness=1)
        file_box.pack(fill="x", padx=14, pady=(0, 12))
        file_lines = [self.project_path_text(path) for path in legacy_files]
        if not file_lines:
            file_lines = ["暂无旧版 record JSON 文件。"]
        tk.Label(file_box, text="\n".join(file_lines), fg="#dce6ff", bg="#111827", justify="left", anchor="w", wraplength=1060, font=("Consolas", 9)).pack(anchor="w", fill="x", padx=12, pady=10)

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
        bar.pack(fill="x", padx=22, pady=(14, 8))
        HoverButton(bar, "返回", back_command, width=110, height=48, accent="#8fb6ff").pack(side="left")
        tk.Label(bar, text=title, fg="#fff2bd", bg="#111725", font=("Microsoft YaHei UI", 19, "bold")).pack(side="left", padx=18)
        line = tk.Canvas(self.container, height=10, bg="#111725", bd=0, highlightthickness=0)
        line.pack(fill="x", padx=34, pady=(0, 12))
        line.create_line(0, 5, 1200, 5, fill="#1f4168", width=1)
        line.create_line(0, 6, 260, 6, fill="#2d78b7", width=2)

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



def main():
    app = BonusGuessApp()
    app.mainloop()
