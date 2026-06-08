import json
import math
import random
import sys
import time
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import messagebox

from backend.runtime.game_config import (
    ACHIEVEMENT_CATEGORIES,
    APP_VERSION,
    GAME_MECHANICS_FILE,
    HIDDEN_ACHIEVEMENT_IDS,
    HINT_COOLDOWN_SECONDS,
    MASK_PROBABILITIES,
    APP_ICON_FILE,
    ASSETS_DIR,
    PROJECT_DIR,
    RECORD_DIR,
    RESOURCE_DIR,
    TERM_CLUES_DIR,
    TITLE_CN,
    TITLE_EN,
    WORDS_DIR,
)
from frontend.ui.avatars import AVATARS, draw_avatar
from backend.runtime.accounts import (
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
    set_account_admin,
    set_active_session,
)
from backend.runtime.bug_feedback import (
    feedback_file_path,
    load_feedback,
    submit_feedback,
    submit_term_feedback,
    update_feedback_status,
)
from frontend.ui.backdrop import BackdropMixin
from backend.runtime.clue_library import ClueLibrary
from backend.runtime.cosmetics import (
    RATING_REWARDS,
    coerce_avatar_id,
    coerce_title_id,
    title_name,
    unlocked_avatar_ids,
    unlocked_title_options,
)
from backend.runtime.music_catalog import (
    HOME_MUSIC_OPTIONS,
    coerce_home_music_id,
    home_music_label,
    home_music_option,
    home_music_track,
    unlocked_home_music_ids,
)
from backend.runtime.sfx_catalog import (
    SFX_EVENT_OPTIONS,
    normalize_sfx_choices,
    sfx_event_label,
    sfx_sound_display,
    sfx_sound_display_options,
    sfx_sound_id_from_display,
)
from backend.runtime.crossword_puzzle import generate_crossword, size_for_difficulty, target_word_count_for_size, validate_crossword
from frontend.ui.markdown_view import render_inline_markdown, render_markdown, split_mechanics_sections
from backend.runtime.player_profile import DEFAULT_PLAYER_SETTINGS, load_player_settings, save_player_settings
from backend.runtime.rank_system import (
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
    rank_count_for_kind,
    rank_hint_cooldown_seconds,
    rank_hint_limit,
    rank_highest_passed,
    rank_is_unlocked,
    rank_kind_label,
    rank_pass_score,
    rank_passed_ids,
    rank_progress_key,
    rank_target_difficulty,
    read_rank_progress,
    split_rank_progress_key,
    subject_label,
    unlocked_rank_badges,
    visible_rank_challenges,
)
from backend.runtime.records import (
    ACHIEVEMENTS,
    EQUAL_DIFFICULTY_MODE_RANDOM,
    add_record_entry_to_cache,
    apply_initial_mask,
    balanced_terms_by_equal_difficulty_mode,
    choose_daily_term_by_difficulty,
    choose_term_by_length,
    format_duration,
    format_rating,
    format_score,
    is_abandoned_record,
    is_counted_record,
    is_random_record,
    load_record_entries,
    load_record_summary,
    record_entries_signature,
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
from backend.runtime.term_library import (
    TermLibrary,
    answers_differ_only_by_person_alias,
    answers_equivalent,
    canonical_answer_text,
    normalize_term_initials,
    person_name_answer_key,
    term_has_greek_letter,
    term_notice_tags,
    term_notice_text,
)
from frontend.ui.widgets import HoverButton, WobblePanel, scaled_int, set_button_sound_callback, set_ui_scale
