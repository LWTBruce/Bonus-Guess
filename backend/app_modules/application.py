from ._shared import *
from .account_tutorial import AccountTutorialMixin
from .navigation_home import NavigationHomeMixin
from .settings import SettingsMixin
from .mode_flow import ModeFlowMixin
from .crossword import CrosswordMixin
from .round_play import RoundPlayMixin
from .data_views import DataViewsMixin
from .ui_helpers import UiHelpersMixin


def _run_daemon(target):
    import threading

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


class BonusGuessApp(
    AccountTutorialMixin,
    NavigationHomeMixin,
    SettingsMixin,
    ModeFlowMixin,
    CrosswordMixin,
    RoundPlayMixin,
    DataViewsMixin,
    UiHelpersMixin,
    BackdropMixin,
    tk.Tk,
):
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
        self.cache_warmup_started = False
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
        self.accepted_answer_keys = set()
        self.round_initial_lookup = {}
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
        self.hint_box = None
        self.hint_text_widget = None
        self.hint_scrollbar = None
        self.hint_box_rows = 4
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
            self.after(350, self.start_runtime_cache_warmup)
        else:
            self.show_login()

    def start_runtime_cache_warmup(self):
        if self.cache_warmup_started:
            return
        self.cache_warmup_started = True

        def warm():
            try:
                self.library.warm_initials_cache()
            except Exception:
                pass
            try:
                self.clue_library.load()
            except Exception:
                pass

        _run_daemon(warm)


def main():
    app = BonusGuessApp()
    app.mainloop()
