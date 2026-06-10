from ._shared import *


class DataViewsMixin:
    def on_close(self):
        self.shutdown_audio()
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

    def refresh_achievements(self, force=False):
        if self.is_spectating() or self.tutorial_active:
            self.achievements = read_achievements()
            return
        self.achievements = read_achievements()
        all_records = load_record_entries()
        rank_progress = read_rank_progress()
        try:
            progress_signature = json.dumps(rank_progress.get("subjects", {}), sort_keys=True, ensure_ascii=False)
        except (TypeError, ValueError):
            progress_signature = ""
        refresh_signature = (record_entries_signature(), progress_signature)
        if not force and getattr(self, "_achievements_refresh_signature", None) == refresh_signature:
            return
        completed = self.achievements.setdefault("completed", {})
        changed = False

        def mark(achievement_id, record=None):
            nonlocal changed
            if achievement_id in completed:
                return
            when = record_datetime(record) if record else datetime.now()
            completed[achievement_id] = when.isoformat(timespec="seconds")
            changed = True

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
            try:
                progress_index = int(record.get("rank_question_index") or 0)
            except (TypeError, ValueError):
                progress_index = 0
            rank_kind = normalize_rank_kind(record.get("rank_kind"))
            if rank_id <= 0 or rank_id > rank_count_for_kind(rank_kind):
                continue
            if progress_index < len(rank_by_id(rank_id)["requirements"]):
                continue
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

        progress_passes = [
            (subject_key, rank_id)
            for subject_key, info in (rank_progress.get("subjects") or {}).items()
            for rank_id in rank_passed_ids(info)
            if rank_id <= rank_count_for_kind(split_rank_progress_key(subject_key)[1])
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
                if effective_difficulty >= 11:
                    mark("difficulty_eleven_success", record)
                if effective_difficulty >= 12:
                    mark("difficulty_twelve_success", record)
                if effective_difficulty >= 13:
                    mark("difficulty_thirteen_success", record)
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

        if changed:
            write_achievements(self.achievements)
        self._achievements_refresh_signature = refresh_signature

    def achievement_progress_snapshot(self):
        completed = (self.achievements or {}).get("completed", {})
        progress = {
            achievement_id: (1 if achievement_id in completed else 0, 1, "")
            for achievement_id, _title, _description in ACHIEVEMENTS
        }

        def set_progress(achievement_id, current, target=1, unit=""):
            try:
                target_value = float(target)
            except (TypeError, ValueError):
                target_value = 1.0
            target_value = max(target_value, 1.0)
            try:
                current_value = float(current)
            except (TypeError, ValueError):
                current_value = 0.0
            if achievement_id in completed:
                current_value = target_value
            else:
                current_value = max(0.0, min(current_value, target_value))
            progress[achievement_id] = (current_value, target_value, unit)

        all_records = load_record_entries()
        rank_progress = read_rank_progress()
        abandoned_records = [record for record in all_records if is_abandoned_record(record)]
        records = [record for record in all_records if is_counted_record(record)]
        records.sort(key=record_datetime)
        abandoned_records.sort(key=record_datetime)

        total_score = 0.0
        total_time = 0.0
        total_success = 0
        total_char_hints = 0
        total_library_hints = 0
        total_hard_success = 0
        total_difficulty_ten_success = 0
        total_effective_over_10_success = 0
        total_effective_over_11_success = 0
        total_masked_success = 0
        total_timed_success = 0
        total_timed_time = 0.0
        total_clue_success = 0
        total_random_success = 0
        total_cheats = 0
        total_crossword_words = 0
        total_greek_success = 0
        max_streak = 0
        streak = 0
        first_success = 0
        first_free_success = 0
        no_hint_success = 0
        quick_success = 0
        slow_success = 0
        score_guard = 0
        first_out_of_scope = 0
        negative_score = 0
        three_hints_one_round = 0
        first_masked_round = 0
        first_masked_success = 0
        three_mask_success = 0
        first_timed_success = 0
        first_clue_success = 0
        clue_no_hint_success = 0
        first_random_success = 0
        true_random_success = 0
        first_greek_term = 0
        first_greek_success = 0
        crossword_greek_term = 0
        first_cheat = 0
        timed_cheat = 0
        first_crossword_success = 0
        crossword_crossings_10 = 0
        crossword_no_hint_success = 0
        crossword_triangle_success = 0
        crossword_hex_success = 0
        one_char_term = 0
        crossword_cheat = 0
        difficulty_eleven_success = 0
        difficulty_twelve_success = 0
        difficulty_thirteen_success = 0

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
                first_greek_term = 1
                if is_crossword:
                    crossword_greek_term = 1
            if len(str(record.get("selected_answer") or "")) == 1 or any(len(str(item.get("answer") or "")) == 1 for item in crossword_placements if isinstance(item, dict)):
                one_char_term = 1
            if mask_count:
                first_masked_round = 1
            if is_timed:
                total_timed_time += float(record.get("elapsed_seconds") or 0)
            if is_cheat:
                total_cheats += 1
                first_cheat = 1
                if is_timed:
                    timed_cheat = 1
                if is_crossword:
                    crossword_cheat = 1

            if success:
                total_success += 1
                first_success = 1
                streak += 1
                max_streak = max(max_streak, streak)
                greek_success_answers = self.record_success_greek_answers(record)
                if greek_success_answers:
                    first_greek_success = 1
                    total_greek_success += len(greek_success_answers)
                if play_label == "自由":
                    first_free_success = 1
                if is_random:
                    first_random_success = 1
                    total_random_success += 1
                if is_true_random:
                    true_random_success = 1
                if is_crossword:
                    first_crossword_success = 1
                    try:
                        total_crossword_words += int(record.get("crossword_solved_count") or record.get("crossword_word_count") or 0)
                    except (TypeError, ValueError):
                        pass
                    try:
                        if int(record.get("crossword_intersection_count") or 0) >= 10:
                            crossword_crossings_10 = 1
                    except (TypeError, ValueError):
                        pass
                    if char_hints == 0 and library_hints == 0:
                        crossword_no_hint_success = 1
                    shape = record.get("crossword_cell_shape")
                    if shape == "triangle":
                        crossword_triangle_success = 1
                    elif shape == "hex":
                        crossword_hex_success = 1
                if mask_count:
                    total_masked_success += 1
                    first_masked_success = 1
                    if mask_count >= 3:
                        three_mask_success = 1
                if is_timed:
                    first_timed_success = 1
                    total_timed_success += 1
                if is_clue:
                    first_clue_success = 1
                    total_clue_success += 1
                    if char_hints == 0 and library_hints == 0:
                        clue_no_hint_success = 1
                if char_hints == 0 and library_hints == 0:
                    no_hint_success = 1
                if float(record.get("elapsed_seconds") or 0) <= 10:
                    quick_success = 1
                if float(record.get("elapsed_seconds") or 0) > 180:
                    slow_success = 1
                if effective_difficulty >= 8:
                    total_hard_success += 1
                if effective_difficulty >= 10:
                    total_difficulty_ten_success += 1
                if effective_difficulty >= 11:
                    difficulty_eleven_success = 1
                if effective_difficulty >= 12:
                    difficulty_twelve_success = 1
                if effective_difficulty >= 13:
                    difficulty_thirteen_success = 1
                if effective_difficulty > 10:
                    total_effective_over_10_success += 1
                if effective_difficulty > 11:
                    total_effective_over_11_success += 1
                if score >= 900:
                    score_guard = 1
            else:
                streak = 0

            if char_hints >= 3:
                three_hints_one_round = 1
            if score < 0:
                negative_score = 1
            if any((attempt.get("result") == "out_of_scope") for attempt in record.get("all_answers") or []):
                first_out_of_scope = 1

        rank_records = [record for record in all_records if record.get("rank_mode")]
        rank_pass_keys = set()
        rank_pass_kinds = set()
        rank_no_hint_pass = 0
        rank_cheat = 0

        for record in rank_records:
            if bool(record.get("cheat_detected")) or record.get("finished_by") == "cheated":
                rank_cheat = 1
            if not record.get("success"):
                continue
            try:
                rank_id = int(record.get("rank_id") or 0)
            except (TypeError, ValueError):
                continue
            rank_kind = normalize_rank_kind(record.get("rank_kind"))
            if rank_id <= 0 or rank_id > rank_count_for_kind(rank_kind):
                continue
            try:
                progress_index = int(record.get("rank_question_index") or 0)
            except (TypeError, ValueError):
                progress_index = 0
            if progress_index < len(rank_by_id(rank_id)["requirements"]):
                continue
            progress_key = record.get("rank_progress_key") or rank_progress_key(record.get("rank_subject") or record.get("subject"), rank_kind)
            rank_pass_keys.add((progress_key, rank_id))
            rank_pass_kinds.add(rank_kind)
            try:
                rank_hint_used = int(record.get("rank_hint_used") or 0)
            except (TypeError, ValueError):
                rank_hint_used = 0
            if rank_hint_used == 0:
                rank_no_hint_pass = 1

        for subject_key, info in (rank_progress.get("subjects") or {}).items():
            _subject, rank_kind = split_rank_progress_key(subject_key)
            for rank_id in rank_passed_ids(info):
                if rank_id <= rank_count_for_kind(rank_kind):
                    rank_pass_keys.add((subject_key, rank_id))
                    rank_pass_kinds.add(rank_kind)

        rank_distinct_count = len(rank_pass_keys)
        max_rank_class = max((rank_id for _subject_key, rank_id in rank_pass_keys), default=0)

        set_progress("first_success", first_success)
        set_progress("first_free_success", first_free_success)
        set_progress("three_hints_one_round", three_hints_one_round)
        set_progress("first_out_of_scope", first_out_of_scope)
        set_progress("negative_score", negative_score)
        set_progress("fifty_char_hints", total_char_hints, 50)
        set_progress("five_hundred_char_hints", total_char_hints, 500)
        set_progress("twenty_library_hints", total_library_hints, 20)
        set_progress("two_hundred_library_hints", total_library_hints, 200)
        set_progress("no_hint_success", no_hint_success)
        set_progress("quick_success", quick_success)
        set_progress("slow_success", slow_success)
        set_progress("hard_success", 1 if total_hard_success else 0)
        set_progress("difficulty_ten_success", 1 if total_difficulty_ten_success else 0)
        set_progress("difficulty_eleven_success", difficulty_eleven_success)
        set_progress("difficulty_twelve_success", difficulty_twelve_success)
        set_progress("difficulty_thirteen_success", difficulty_thirteen_success)
        set_progress("effective_over_10_success", 1 if total_effective_over_10_success else 0)
        set_progress("effective_over_11_success", 1 if total_effective_over_11_success else 0)
        set_progress("streak_five", max_streak, 5)
        set_progress("streak_ten", max_streak, 10)
        set_progress("score_guard", score_guard)
        set_progress("total_score_5000", total_score, 5000, "分")
        set_progress("total_score_20000", total_score, 20000, "分")
        set_progress("total_score_100000", total_score, 100000, "分")
        set_progress("total_score_500000", total_score, 500000, "分")
        set_progress("completed_50", len(records), 50)
        set_progress("completed_200", len(records), 200)
        set_progress("completed_500", len(records), 500)
        set_progress("completed_1000", len(records), 1000)
        set_progress("exit_ten", len(abandoned_records), 10)
        set_progress("exit_hundred", len(abandoned_records), 100)
        set_progress("play_time_10h", total_time / 3600, 10, "小时")
        set_progress("play_time_30h", total_time / 3600, 30, "小时")
        set_progress("play_time_100h", total_time / 3600, 100, "小时")
        set_progress("success_500", total_success, 500)
        set_progress("hard_success_100", total_hard_success, 100)
        set_progress("difficulty_ten_success_30", total_difficulty_ten_success, 30)
        set_progress("effective_over_10_success_20", total_effective_over_10_success, 20)
        set_progress("effective_over_11_success_5", total_effective_over_11_success, 5)
        set_progress("first_masked_round", first_masked_round)
        set_progress("first_masked_success", first_masked_success)
        set_progress("three_mask_success", three_mask_success)
        set_progress("masked_success_50", total_masked_success, 50)
        set_progress("masked_success_300", total_masked_success, 300)
        set_progress("first_timed_success", first_timed_success)
        set_progress("timed_success_20", total_timed_success, 20)
        set_progress("timed_success_100", total_timed_success, 100)
        set_progress("timed_success_500", total_timed_success, 500)
        set_progress("timed_time_5h", total_timed_time / 3600, 5, "小时")
        set_progress("timed_time_30h", total_timed_time / 3600, 30, "小时")
        set_progress("first_clue_success", first_clue_success)
        set_progress("clue_no_hint_success", clue_no_hint_success)
        set_progress("clue_success_20", total_clue_success, 20)
        set_progress("clue_success_100", total_clue_success, 100)
        set_progress("first_random_success", first_random_success)
        set_progress("random_success_20", total_random_success, 20)
        set_progress("true_random_success", true_random_success)
        set_progress("first_greek_term", first_greek_term)
        set_progress("first_greek_success", first_greek_success)
        set_progress("greek_success_10", total_greek_success, 10)
        set_progress("crossword_greek_term", crossword_greek_term)
        set_progress("first_cheat", first_cheat)
        set_progress("cheat_three", total_cheats, 3)
        set_progress("cheat_ten", total_cheats, 10)
        set_progress("timed_cheat", timed_cheat)
        set_progress("first_rank_pass", 1 if rank_pass_keys else 0)
        set_progress("first_free_rank_pass", 1 if any(kind not in {"timed", "clue", "crossword"} for kind in rank_pass_kinds) else 0)
        set_progress("first_timed_rank_pass", 1 if "timed" in rank_pass_kinds else 0)
        set_progress("first_clue_rank_pass", 1 if "clue" in rank_pass_kinds else 0)
        set_progress("first_crossword_rank_pass", 1 if "crossword" in rank_pass_kinds else 0)
        set_progress("rank_class_5_pass", 1 if max_rank_class >= 5 else 0)
        set_progress("rank_class_10_pass", 1 if max_rank_class >= 10 else 0)
        set_progress("rank_class_15_pass", 1 if max_rank_class >= 15 else 0)
        set_progress("rank_distinct_5", rank_distinct_count, 5)
        set_progress("rank_distinct_15", rank_distinct_count, 15)
        set_progress("rank_no_hint_pass", rank_no_hint_pass)
        set_progress("rank_cheat", rank_cheat)
        set_progress("first_crossword_success", first_crossword_success)
        set_progress("crossword_words_50", total_crossword_words, 50)
        set_progress("crossword_crossings_10", crossword_crossings_10)
        set_progress("crossword_no_hint_success", crossword_no_hint_success)
        set_progress("crossword_triangle_success", crossword_triangle_success)
        set_progress("crossword_hex_success", crossword_hex_success)
        set_progress("one_char_term", one_char_term)
        set_progress("crossword_cheat", crossword_cheat)

        return progress

    def achievement_progress_text(self, achievement_id, progress_snapshot):
        current, target, unit = progress_snapshot.get(achievement_id, (0, 1, ""))

        def fmt(value):
            if unit == "分":
                return format_score(value)
            if isinstance(value, float) and not value.is_integer():
                return f"{value:.1f}".rstrip("0").rstrip(".")
            return str(int(value))

        return f"进度 {fmt(current)}/{fmt(target)}{unit}"

    def show_history(self, transition=True, records=None, summary=None):
        self.play_music("archive")
        self.clear(transition=transition)
        self._topbar("历史记录", self.show_home)
        base_bg = self.theme_color("base")
        frame = tk.Frame(self.container, bg=base_bg)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self._start_backdrop("particles", frame)

        if records is None:
            records = load_record_entries()
        if summary is None:
            summary = load_record_summary()
        self._history_records = records
        self._history_summary = summary

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

        dist = tk.Frame(frame, bg=base_bg)
        dist.pack(fill="x", pady=(0, 12))
        term_parts = [f"{i}:{summary['difficulty_counts'].get(i, 0)}" for i in range(1, 13)]
        if summary["difficulty_counts"].get(0, 0):
            term_parts.append(f"未知:{summary['difficulty_counts'].get(0, 0)}")
        term_text = "  ".join(term_parts)
        mode_order = ["入门", "简单", "普通", "困难", "噩梦", "混合模式", "未知"]
        mode_text = "  ".join(f"{name}:{summary['mode_counts'].get(name, 0)}" for name in mode_order if summary["mode_counts"].get(name, 0) or name != "未知")
        tk.Label(dist, text=f"词条难度分布  {term_text}", fg="#c8d2ee", bg=base_bg, font=("Microsoft YaHei UI", 11)).pack(anchor="w")
        tk.Label(dist, text=f"选词难度分布  {mode_text}", fg="#c8d2ee", bg=base_bg, font=("Microsoft YaHei UI", 11)).pack(anchor="w", pady=(4, 0))

        HoverButton(frame, "详情", self.show_history_details_popup, width=130, height=46, accent="#8fb6ff").pack(anchor="w", pady=(0, 10))

        tk.Label(frame, text="记录列表", fg="#8fb6ff", bg=base_bg, font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", pady=(4, 8))
        scroll = self.make_scroll_frame(frame)
        if not records:
            tk.Label(scroll, text="还没有历史记录。", fg="#9ca8c7", bg=base_bg, font=("Microsoft YaHei UI", 13)).pack(anchor="w", pady=18)
        else:
            self.render_history_record_rows(scroll, records)
        self.reveal_background_surface(frame)

    def toggle_history_details(self):
        self.show_history_details_popup()

    def show_history_details_popup(self):
        summary = getattr(self, "_history_summary", None)
        if summary is None:
            summary = load_record_summary()
            self._history_summary = summary
        popup = tk.Toplevel(self)
        popup.title("历史详情")
        popup.configure(bg=self.theme_color("base"))
        popup.geometry("1040x720")
        popup.minsize(760, 520)
        popup.transient(self)

        panel = tk.Frame(popup, bg=self.theme_color("base"))
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        header = tk.Frame(panel, bg=self.theme_color("base"))
        header.pack(fill="x", pady=(0, 12))
        tk.Label(
            header,
            text="历史详情",
            fg=self.theme_color("title"),
            bg=self.theme_color("base"),
            font=("Microsoft YaHei UI", 22, "bold"),
        ).pack(side="left")
        HoverButton(header, "关闭", popup.destroy, width=104, height=44, accent="#ff9b89").pack(side="right")

        scroll = self.make_scroll_frame(panel, bg=self.theme_color("base"))
        self.render_history_details(scroll, summary)
        self.apply_static_theme(popup)

        def focus_popup():
            try:
                if popup.winfo_exists():
                    popup.focus_force()
            except tk.TclError:
                pass

        self.after(80, focus_popup)

    def render_history_record_rows(self, parent, records):
        self._history_render_token = getattr(self, "_history_render_token", 0) + 1
        token = self._history_render_token
        index = {"value": 0}

        def render_batch(limit):
            end = min(len(records), index["value"] + limit)
            while index["value"] < end:
                self.render_record_row(parent, records[index["value"]])
                index["value"] += 1

        render_batch(28)

        def render_more():
            if token != getattr(self, "_history_render_token", None):
                return
            try:
                if not parent.winfo_exists():
                    return
            except tk.TclError:
                return
            render_batch(42)
            if index["value"] < len(records):
                self._history_render_job = self.after(1, render_more)
            else:
                self._history_render_job = None

        if index["value"] < len(records):
            self._history_render_job = self.after_idle(render_more)

    def render_history_details(self, parent, summary):
        surface_bg = self.theme_color("button_bg", "#182033")
        panel_bg = self.theme_color("entry_bg", "#111827")
        border = self.theme_color("button_outline", "#30384e")
        text_fg = self.theme_color("text", "#dce6ff")
        muted_fg = self.theme_color("muted", "#64708f")
        accent_fg = self.theme_color("accent", "#8fb6ff")
        box = tk.Frame(parent, bg=surface_bg, highlightbackground=border, highlightthickness=1)
        box.pack(fill="x", pady=(0, 14))
        total = max(summary["total_count"], 1)
        accuracy = summary["success_count"] / total * 100
        result = summary["answer_results"]
        mode_order = ["入门", "简单", "普通", "困难", "噩梦", "混合模式", "未知"]
        scored_mode_order = ["入门", "简单", "普通", "困难", "噩梦", "混合模式"]
        score_parts = [
            f"{name}:{format_score(summary['mode_scores'].get(name, 0))}"
            for name in scored_mode_order
        ]
        if summary["mode_scores"].get("未知", 0) or summary["mode_counts"].get("未知", 0):
            score_parts.append(f"未知:{format_score(summary['mode_scores'].get('未知', 0))}")
        lines = [
            f"答对 {summary['success_count']} 题，未答对 {summary['wrong_count']} 题，中途退出 {summary['abandoned_count']} 次，正确率 {accuracy:.1f}%",
            f"平均用时 {summary['avg_time']:.1f} 秒，平均计入积分 {summary['avg_score']:.1f} 分，平均原始得分 {summary['avg_raw_score']:.1f} 分",
            f"Rating {format_rating(summary['rating'])}，去重B20均值 {format_rating(summary['rating_best_average'])}，R10均值 {format_rating(summary['rating_recent_average'])}",
            f"最终总积分按入门 0.1、简单 0.2、普通 0.3、困难 0.4、噩梦 0.6、混合模式/真·随机 0.3 加权；随机四玩法按所选难度同口径计分。原始总分 {summary['raw_total_score']} 分",
            f"字词/线索提示：免费字词 {summary['free_char_hints']}，付费字词或线索 {summary['paid_char_hints']}，总计 {summary['char_hints']}",
            f"各模式计入积分：{'  '.join(score_parts) if score_parts else '暂无'}",
            f"提交答案统计：正确 {result.get('success', 0)}，错误 {result.get('wrong', 0)}，超纲 {result.get('out_of_scope', 0)}",
        ]
        for line in lines:
            tk.Label(box, text=line, fg=text_fg, bg=surface_bg, justify="left", anchor="w", wraplength=1080, font=("Microsoft YaHei UI", 11)).pack(anchor="w", fill="x", padx=16, pady=3)

        dimensions = [
            ("按学科", summary.get("by_subject", {}), ["物理模式", "数学模式", "随机", "真·随机", "未知"]),
            ("按玩法", summary.get("by_play_mode", {}), ["自由", "限时", "线索", "字谜", "随机-自由", "随机-限时", "随机-线索", "随机字谜", "真·随机-自由", "真·随机-限时", "真·随机-线索", "真·随机", "未知"]),
            ("按选词难度", summary.get("by_difficulty", {}), ["入门", "简单", "普通", "困难", "噩梦", "混合模式", "真·随机", "未知"]),
        ]
        grid = tk.Frame(box, bg=surface_bg)
        grid.pack(fill="x", padx=12, pady=(10, 12))
        for column, (title, data, order) in enumerate(dimensions):
            panel = tk.Frame(grid, bg=panel_bg, highlightbackground=border, highlightthickness=1)
            panel.grid(row=0, column=column, sticky="nsew", padx=5)
            grid.grid_columnconfigure(column, weight=1)
            tk.Label(panel, text=title, fg=accent_fg, bg=panel_bg, font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
            if title == "按选词难度":
                keys = [key for key in order if key != "未知" or key in data]
            else:
                keys = [key for key in order if key in data]
            keys.extend(key for key in sorted(data, key=str) if key not in keys)
            if not keys:
                tk.Label(panel, text="暂无记录", fg=muted_fg, bg=panel_bg, font=("Microsoft YaHei UI", 10)).pack(anchor="w", padx=12, pady=(0, 10))
            for key in keys:
                item = data.get(key, {
                    "total_count": 0,
                    "success_count": 0,
                    "total_score": 0,
                    "abandoned_count": 0,
                })
                text = (
                    f"{key}｜{item['total_count']}题 / 对{item['success_count']}｜"
                    f"计入{format_score(item['total_score'])}｜退出{item['abandoned_count']}"
                )
                tk.Label(panel, text=text, fg=text_fg, bg=panel_bg, font=("Microsoft YaHei UI", 9), wraplength=330, justify="left").pack(anchor="w", padx=12, pady=2)

    @staticmethod
    def crossword_record_placements(record):
        placements = record.get("crossword_placements")
        if not isinstance(placements, list):
            return []
        return [item for item in placements if isinstance(item, dict)]

    def record_question_display(self, record):
        if record.get("crossword_mode"):
            parts = []
            for placement in self.crossword_record_placements(record):
                raw_id = placement.get("id")
                try:
                    label = f"{int(raw_id):02d}."
                except (TypeError, ValueError):
                    label = f"{raw_id}." if raw_id else ""
                initials = str(placement.get("display_initials") or placement.get("initials") or "").strip()
                if initials:
                    parts.append(f"{label}{initials}")
            if parts:
                return "；".join(parts)
        return str(record.get("displayed_initials") or record.get("question_initials") or "")

    def record_answer_display(self, record):
        if record.get("crossword_mode"):
            parts = []
            for placement in self.crossword_record_placements(record):
                raw_id = placement.get("id")
                try:
                    label = f"{int(raw_id):02d}."
                except (TypeError, ValueError):
                    label = f"{raw_id}." if raw_id else ""
                answer = str(placement.get("answer") or "").strip()
                filled = str(placement.get("filled_answer") or "").strip()
                if filled and answer and filled != answer:
                    parts.append(f"{label}{filled}→{answer}")
                elif answer:
                    parts.append(f"{label}{answer}")
                elif filled:
                    parts.append(f"{label}{filled}")
            if parts:
                return "；".join(parts)
        return str(record.get("selected_answer") or "")

    def render_record_row(self, parent, record):
        row_bg = self.theme_color("button_bg", "#182033")
        row_border = self.theme_color("button_outline", "#30384e")
        detail_fg = self.theme_color("text", "#c8d2ee")
        row = tk.Frame(parent, bg=row_bg, highlightbackground=row_border, highlightthickness=1)
        row.pack(fill="x", pady=5)
        if is_abandoned_record(record):
            status = "中途退出"
            status_color = self.theme_color("warning", "#f6d36b")
        elif record.get("cheat_detected"):
            status = "隐藏彩蛋"
            status_color = self.theme_color("danger", "#ff6b8a")
        elif record.get("finished_by") == "hint_failure":
            status = "提示失败"
            status_color = self.theme_color("danger", "#ff9b89")
        elif record.get("finished_by") == "revealed":
            status = "已揭晓"
            status_color = self.theme_color("warning", "#f6d36b")
        elif record.get("success"):
            status = "答对"
            status_color = self.theme_color("success", "#9ff2b2")
        else:
            status = "未答对"
            status_color = self.theme_color("danger", "#ff9b89")
        created = (record.get("created_at") or "")[:19].replace("T", " ")
        title = f"{created}    {record_mode(record)} / {record_play_mode(record)} / {record.get('difficulty', '未知')}    {status}"
        tk.Label(row, text=title, fg=status_color, bg=row_bg, justify="left", anchor="w", wraplength=1080, font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", fill="x", padx=14, pady=(9, 2))
        hint_label = "线索提示" if record.get("clue_mode") else "字词提示"
        question_text = self.record_question_display(record)
        answer_text = self.record_answer_display(record)
        detail = (
            f"题目 {question_text}    答案 {answer_text}    "
            f"基础难度 {record_term_difficulty(record) or '未知'} / 总难度 {record_effective_difficulty(record):g}    "
            f"掩码 {int(record.get('mask_count') or 0)}    用时 {float(record.get('elapsed_seconds') or 0):.1f} 秒    "
            f"得分 {record_score(record)} / 计入 {format_score(record_weighted_score(record))}    单局Rating {format_rating(record_single_rating(record))}    "
            f"{hint_label} {record_hint_count(record)}（免费 {record_free_hint_count(record)} / 付费 {record_paid_hint_count(record)}）    "
            f"提示词库 {record_library_hint_count(record)}"
        )
        if record.get("failed_reason"):
            detail += f"    原因 {record.get('failed_reason')}"
        tk.Label(row, text=detail, fg=detail_fg, bg=row_bg, font=("Microsoft YaHei UI", 10), wraplength=1060, justify="left").pack(anchor="w", padx=14, pady=(0, 9))

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
        summary = load_record_summary(paths["record_dir"], achievements_data=achievements_data)
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
        self.play_music("archive")
        self.clear()
        self._topbar("后台数据", self.show_settings)
        base_bg = self.theme_color("base")
        frame = tk.Frame(self.container, bg=base_bg)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self._start_backdrop("grid", frame)

        snapshots = [self.account_admin_snapshot(account) for account in list_public_accounts()]
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
            bg=base_bg,
            justify="left",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        scroll = self.make_scroll_frame(frame)
        for snapshot in snapshots:
            self.render_admin_account_row(scroll, snapshot)
        self.reveal_background_surface(frame)

    def show_feedback_admin(self, transition=True):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以查看玩家建议。")
            self.show_home()
            return
        self.play_music("archive")
        self.clear(transition=transition)
        self._topbar("玩家意见", self.show_settings)
        base_bg = self.theme_color("base")
        frame = tk.Frame(self.container, bg=base_bg)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self._start_backdrop("grid", frame)
        data = load_feedback()
        items = data.get("items", [])
        pending_count = sum(1 for item in items if item.get("status") == "pending")
        fixed_count = sum(1 for item in items if item.get("fixed"))
        header = tk.Frame(frame, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        header.pack(fill="x", pady=(0, 14))
        term_count = sum(1 for item in items if item.get("feedback_type") == "term")
        cards = [
            ("意见总数", str(len(items))),
            ("待处理", str(pending_count)),
            ("已处理", str(max(0, len(items) - pending_count))),
            ("词条反馈", str(term_count)),
            ("已改", str(fixed_count)),
        ]
        for index, (name, value) in enumerate(cards):
            cell = tk.Frame(header, bg="#182033")
            cell.grid(row=0, column=index, sticky="ew", padx=18, pady=12)
            header.grid_columnconfigure(index, weight=1)
            tk.Label(cell, text=name, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
            tk.Label(cell, text=value, fg="#fff2bd", bg="#182033", font=("Consolas", 19, "bold")).pack(anchor="w", pady=(3, 0))
        path_line = f"后台文件：{self.project_path_text(feedback_file_path())}"
        tk.Label(
            frame,
            text=path_line,
            fg="#9ca8c7",
            bg=base_bg,
            justify="left",
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        tk.Label(
            frame,
            text="后续修复完成后，可以在该文件里把对应条目的 fixed 改为 true，并补充 fixed_note；自动处理时也会优先读取这个文件。下方意见已按日期分类。",
            fg="#c8d2ee",
            bg=base_bg,
            wraplength=1180,
            justify="left",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 12))
        scroll = self.make_scroll_frame(frame)
        if not items:
            tk.Label(scroll, text="暂无玩家建议。", fg="#64708f", bg=base_bg, font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w", pady=18)
            self.reveal_background_surface(frame)
            return
        for date_label, group_items in self.feedback_items_by_date(items):
            tk.Label(
                scroll,
                text=date_label,
                fg="#fff2bd",
                bg=base_bg,
                font=("Microsoft YaHei UI", 16, "bold"),
            ).pack(anchor="w", pady=(18, 6))
            for item in group_items:
                self.render_feedback_admin_row(scroll, item)
        self.reveal_background_surface(frame)

    def feedback_items_by_date(self, items):
        groups = []
        grouped = {}
        for item in items:
            created = str(item.get("created_at") or "")
            date_label = created[:10] if len(created) >= 10 else "未知日期"
            if date_label not in grouped:
                grouped[date_label] = []
                groups.append(date_label)
            grouped[date_label].append(item)
        return [(date_label, grouped[date_label]) for date_label in groups]

    def feedback_player_display_name(self, item):
        return item.get("player_name") or item.get("player_nickname") or "未知玩家"

    def feedback_player_account(self, player_id):
        player_id = str(player_id or "").strip()
        if not player_id:
            return None
        return next((account for account in list_public_accounts() if account.get("id") == player_id), None)

    def render_feedback_admin_row(self, parent, item):
        row = tk.Frame(parent, bg="#182033", highlightbackground="#30384e", highlightthickness=1)
        row.pack(fill="x", pady=7)
        content = tk.Frame(row, bg="#182033")
        content.pack(side="left", fill="both", expand=True, padx=14, pady=12)
        actions = tk.Frame(row, bg="#182033")
        actions.pack(side="right", fill="y", padx=(8, 14), pady=12)
        status = item.get("status_label") or item.get("status") or "待处理"
        fixed = "是" if item.get("fixed") else "否"
        title_bar = tk.Frame(content, bg="#182033")
        title_bar.pack(anchor="w", fill="x")
        created_text = f"{item.get('created_at', '')}    来自玩家："
        tk.Label(
            title_bar,
            text=created_text,
            fg="#fff2bd",
            bg="#182033",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(side="left")
        player_id = item.get("player_id") or ""
        player_name = self.feedback_player_display_name(item)
        player_link = tk.Label(
            title_bar,
            text=player_name,
            fg="#8fb6ff",
            bg="#182033",
            cursor="hand2",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 12, "bold underline"),
        )
        player_link.pack(side="left")
        player_link.bind("<Button-1>", lambda _event, player_id=player_id, player_name=player_name: self.show_feedback_player_profile(player_id, player_name))
        player_link.bind("<Enter>", lambda _event: player_link.configure(fg="#fff2bd"))
        player_link.bind("<Leave>", lambda _event: player_link.configure(fg="#8fb6ff"))
        feedback_type = "词条反馈" if item.get("feedback_type") == "term" else "玩家建议"
        if item.get("feedback_type") == "term" and item.get("term_action_label"):
            feedback_type += f" / {item.get('term_action_label')}"
        tk.Label(
            title_bar,
            text=f"  ({player_id or '无账号ID'})    类型：{feedback_type}    采纳状态：{status}    是否已改：{fixed}",
            fg="#fff2bd",
            bg="#182033",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(side="left")
        tk.Label(
            content,
            text=item.get("suggestion") or "（空）",
            fg="#dce6ff",
            bg="#182033",
            justify="left",
            wraplength=930,
            font=("Microsoft YaHei UI", 11),
        ).pack(anchor="w", fill="x", pady=(8, 0))
        if item.get("feedback_type") == "term":
            detail_lines = [
                f"模式：{item.get('mode_context') or '未知'}",
                f"词库：{item.get('source_label') or '未知'}",
                f"词条：{item.get('term_name') or '未知'}",
                f"操作：{item.get('term_action_label') or item.get('term_action') or '未知'}",
            ]
            if item.get("proposed_change"):
                detail_lines.append(f"建议改为：{item.get('proposed_change')}")
            if item.get("source_file"):
                detail_lines.append(f"来源文件：{item.get('source_file')}")
            if item.get("record_path"):
                detail_lines.append(f"作答记录：{item.get('record_path')}")
            tk.Label(
                content,
                text="\n".join(detail_lines),
                fg="#9ca8c7",
                bg="#182033",
                justify="left",
                wraplength=930,
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(anchor="w", fill="x", pady=(8, 0))
        if item.get("modification"):
            tk.Label(
                content,
                text=f"修改建议：{item.get('modification')}",
                fg="#9ff2b2",
                bg="#182033",
                justify="left",
                wraplength=930,
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(anchor="w", fill="x", pady=(8, 0))
        if item.get("fixed_note"):
            tk.Label(
                content,
                text=f"修复备注：{item.get('fixed_note')}",
                fg="#8fb6ff",
                bg="#182033",
                justify="left",
                wraplength=930,
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(anchor="w", fill="x", pady=(6, 0))
        feedback_id = item.get("id")
        HoverButton(actions, "同意", lambda feedback_id=feedback_id: self.review_feedback(feedback_id, "accepted"), width=112, height=42, accent="#9ff2b2").pack(pady=(0, 7))
        HoverButton(actions, "拒绝", lambda feedback_id=feedback_id: self.review_feedback(feedback_id, "rejected"), width=112, height=42, accent="#ff9b89").pack(pady=7)
        HoverButton(actions, "修改", lambda item=item: self.show_feedback_modify_dialog(item), width=112, height=42, accent="#ffcf8f").pack(pady=7)

    def show_feedback_player_profile(self, player_id, fallback_name=""):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以查看玩家信息。")
            return
        account = self.feedback_player_account(player_id)
        if not account:
            messagebox.showinfo("玩家信息", f"找不到玩家账号：{fallback_name or player_id or '未知玩家'}")
            return
        snapshot = self.account_admin_snapshot(account)
        summary = snapshot["summary"]
        paths = snapshot["paths"]
        popup = tk.Toplevel(self)
        popup.title(f"玩家信息 - {account.get('nickname') or account.get('id')}")
        popup.configure(bg="#111725")
        popup.geometry("700x560")
        popup.minsize(600, 470)
        popup.transient(self)
        popup.grab_set()
        panel = tk.Frame(popup, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        title = f"{account.get('nickname') or '未知玩家'}"
        if account.get("is_admin"):
            title += "  管理员"
        tk.Label(panel, text=title, fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=24, pady=(20, 10))
        row = tk.Frame(panel, bg="#182033")
        row.pack(side="bottom", anchor="w", fill="x", padx=24, pady=(0, 20))
        lines = [
            f"账号 ID：{account.get('id') or '未知'}",
            f"创建时间：{account.get('created_at') or '未知'}",
            f"最近登录：{account.get('last_login_at') or '未记录'}",
            f"Rating：{format_rating(summary['rating'])}",
            f"答题记录：{summary['total_count']} 条",
            f"总积分：{format_score(summary['total_score'])}",
            f"成就：{summary['achievement_count']}/{summary['achievement_total']}",
            f"record：{self.project_path_text(paths['record_dir'])}",
            f"profile：{self.project_path_text(paths['profile_dir'])}",
        ]
        info_shell = tk.Frame(panel, bg="#182033")
        info_shell.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        info_text = tk.Text(
            info_shell,
            height=10,
            wrap="word",
            fg="#dce6ff",
            bg="#101827",
            relief="flat",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        info_text.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        info_scrollbar = tk.Scrollbar(info_shell, orient="vertical", command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        info_text.insert("1.0", "\n".join(lines))
        info_text.configure(state="disabled")
        info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar.pack(side="right", fill="y", padx=(8, 0))

        def spectate_home():
            popup.destroy()
            self.enter_spectator_mode(account)

        def spectate_history():
            popup.destroy()
            self.enter_spectator_history(account)

        HoverButton(row, "旁观主页", spectate_home, width=132, height=48, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 10))
        HoverButton(row, "只看记录", spectate_history, width=132, height=48, accent="#8fb6ff").grid(row=0, column=1, padx=10)
        HoverButton(row, "关闭", popup.destroy, width=112, height=48, accent="#ff9b89").grid(row=0, column=2, padx=10)
        self.apply_static_theme(popup)

    def review_feedback(self, feedback_id, status):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以处理玩家建议。")
            return
        try:
            update_feedback_status(feedback_id, status, admin_account)
        except ValueError as exc:
            messagebox.showerror("处理失败", str(exc))
            return
        self.show_feedback_admin(transition=False)

    def show_feedback_modify_dialog(self, item):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以处理玩家建议。")
            return
        popup = tk.Toplevel(self)
        popup.title("修改建议")
        popup.configure(bg="#111725")
        popup.geometry("700x540")
        popup.minsize(600, 460)
        popup.transient(self)
        popup.grab_set()
        panel = tk.Frame(popup, bg="#182033", highlightbackground="#3b4560", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(panel, text="填写修改建议", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 22, "bold")).pack(anchor="w", padx=22, pady=(18, 8))
        row = tk.Frame(panel, bg="#182033")
        row.pack(side="bottom", anchor="w", fill="x", padx=22, pady=(0, 18))
        preview_shell = tk.Frame(panel, bg="#182033")
        preview_shell.pack(fill="x", padx=22, pady=(0, 12))
        preview = tk.Text(
            preview_shell,
            height=4,
            wrap="word",
            fg="#c8d2ee",
            bg="#101827",
            relief="flat",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        preview.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        preview_scrollbar = tk.Scrollbar(preview_shell, orient="vertical", command=preview.yview)
        preview.configure(yscrollcommand=preview_scrollbar.set)
        preview.insert("1.0", item.get("suggestion") or "（空）")
        preview.configure(state="disabled")
        preview.pack(side="left", fill="x", expand=True)
        preview_scrollbar.pack(side="right", fill="y", padx=(8, 0))
        note_box = tk.Text(
            panel,
            height=9,
            wrap="word",
            fg="#fff8dc",
            bg="#101827",
            insertbackground="#fff8dc",
            relief="flat",
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        note_box.configure(highlightthickness=1, highlightbackground="#30384e", highlightcolor="#8fb6ff")
        note_box.pack(fill="both", expand=True, padx=22, pady=(0, 14))
        if item.get("modification"):
            note_box.insert("1.0", item.get("modification"))

        def submit():
            note = note_box.get("1.0", "end").strip()
            if not note:
                messagebox.showwarning("修改建议为空", "请输入管理员修改建议。", parent=popup)
                return
            try:
                update_feedback_status(item.get("id"), "modified", admin_account, modification=note)
            except ValueError as exc:
                messagebox.showerror("处理失败", str(exc), parent=popup)
                return
            popup.destroy()
            self.show_feedback_admin(transition=False)

        HoverButton(row, "保存修改", submit, width=150, height=52, accent="#9ff2b2").grid(row=0, column=0, padx=(0, 10))
        HoverButton(row, "取消", popup.destroy, width=118, height=52, accent="#ff9b89").grid(row=0, column=1)
        self.apply_static_theme(popup)
        self.after(80, note_box.focus_set)

    def admin_term_detail_text(self, term):
        clue = self.clue_library.get(term)
        lines = [
            f"词条：{term.chinese}",
            f"首字母：{term.initials}",
            f"英文：{term.english or '（未填写）'}",
            f"拼音：{term.pinyin or '（未填写）'}",
            f"难度：{term.difficulty}",
            f"词库：{term.source_label}",
            f"来源文件：{term.source}",
            "",
            "解释文段：",
            str(clue.get("explanation_markdown") or "（暂无解释文段）").strip(),
            "",
            "完整线索：",
        ]
        for index, line in enumerate(clue.get("complete") or [], 1):
            lines.append(f"{index}. {line}")
        if not clue.get("complete"):
            lines.append("（暂无完整线索）")
        lines.extend(["", "破碎线索："])
        for index, line in enumerate(clue.get("fragments") or [], 1):
            lines.append(f"{index}. {line}")
        if not clue.get("fragments"):
            lines.append("（暂无破碎线索）")
        source_links = clue.get("source_links") or []
        if source_links:
            lines.extend(["", "参考来源："])
            for source in source_links:
                title = source.get("title") or source.get("label") or "来源"
                lines.append(f"- {title}: {source.get('url')}")
        return "\n".join(lines)

    def admin_term_detail_markdown(self, term):
        clue = self.clue_library.get(term)
        lines = [
            f"## {term.chinese}",
            f"- 首字母：`{term.initials}`",
            f"- 英文：`{term.english or '未填写'}`",
            f"- 拼音：`{term.pinyin or '未填写'}`",
            f"- 难度：{term.difficulty}",
            f"- 词库：{term.source_label}",
            f"- 来源文件：`{term.source}`",
            "",
            "### 解释文段",
            str(clue.get("explanation_markdown") or "暂无解释文段。").strip(),
            "",
            "### 完整线索",
        ]
        complete = clue.get("complete") or []
        fragments = clue.get("fragments") or []
        for index, line in enumerate(complete, 1):
            lines.append(f"{index}. {line}")
        if not complete:
            lines.append("暂无完整线索。")
        lines.extend(["", "### 破碎线索"])
        for index, line in enumerate(fragments, 1):
            lines.append(f"{index}. {line}")
        if not fragments:
            lines.append("暂无破碎线索。")
        source_links = clue.get("source_links") or []
        if source_links:
            lines.extend(["", "### 参考来源"])
            for source in source_links:
                title = source.get("title") or source.get("label") or "来源"
                lines.append(f"- {title}: `{source.get('url')}`")
        return "\n".join(lines)

    def show_admin_term_browser(self):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以查看词库。")
            self.show_home()
            return
        self.play_music("archive")
        self.clear()
        self._topbar("查看词库", self.show_settings)
        base_bg = self.theme_color("base")
        frame = tk.Frame(self.container, bg=base_bg)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        self._start_backdrop("grid", frame)

        left = tk.Frame(frame, bg=base_bg, highlightbackground=self.theme_color("grid_a"), highlightthickness=1)
        left.pack(side="left", fill="both", padx=(0, 18), pady=0)
        right = tk.Frame(frame, bg=base_bg, highlightbackground=self.theme_color("grid_a"), highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)
        self.decorate_surface(left, "particles", opacity_scale=0.26)
        self.decorate_surface(right, "grid", opacity_scale=0.24)

        tk.Label(left, text="筛选词条", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 21, "bold")).pack(anchor="w", padx=22, pady=(20, 12))
        controls = tk.Frame(left, bg="#182033")
        controls.pack(fill="x", padx=22, pady=(0, 12))

        self.admin_browser_subject_var = tk.StringVar(value="物理模式")
        self.admin_browser_difficulty_var = tk.StringVar(value="入门")
        self.admin_browser_file_var = tk.StringVar(value="")
        state = {"files": [], "terms": [], "visible_terms": [], "file_display_to_name": {}}

        def style_option(option):
            option.configure(
                bg="#101827",
                fg="#dce6ff",
                activebackground="#22304a",
                activeforeground="#fff2bd",
                highlightthickness=1,
                highlightbackground="#30384e",
                relief="flat",
                font=("Microsoft YaHei UI", 10, "bold"),
            )
            option["menu"].configure(bg="#101827", fg="#dce6ff", activebackground="#22304a", activeforeground="#fff2bd")

        def reset_option_menu(option, variable, values):
            menu = option["menu"]
            menu.delete(0, "end")
            for value in values:
                menu.add_command(label=value, command=lambda item=value: variable.set(item))

        def add_selector(row, label, variable, values):
            tk.Label(controls, text=label, fg="#8fb6ff", bg="#182033", font=("Microsoft YaHei UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=5)
            option = tk.OptionMenu(controls, variable, *values)
            style_option(option)
            option.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
            controls.grid_columnconfigure(1, weight=1, minsize=260)
            return option

        subject_option = add_selector(0, "学科", self.admin_browser_subject_var, ["物理模式", "数学模式"])
        difficulty_option = add_selector(1, "难度", self.admin_browser_difficulty_var, TermLibrary.DIFFICULTIES)
        file_option = add_selector(2, "词库", self.admin_browser_file_var, [""])
        list_shell = tk.Frame(left, bg="#182033")
        list_shell.pack(fill="both", expand=True, padx=22, pady=(4, 22))
        term_list = tk.Listbox(
            list_shell,
            exportselection=False,
            fg="#dce6ff",
            bg="#101827",
            selectforeground="#101827",
            selectbackground="#9ff2b2",
            relief="flat",
            activestyle="none",
            font=("Microsoft YaHei UI", 11, "bold"),
            width=34,
        )
        term_scrollbar = tk.Scrollbar(list_shell, orient="vertical", command=term_list.yview)
        term_list.configure(yscrollcommand=term_scrollbar.set)
        term_list.pack(side="left", fill="both", expand=True)
        term_scrollbar.pack(side="right", fill="y")
        self.bind_scroll_wheel(list_shell, term_list)

        tk.Label(right, text="词条详情", fg="#fff2bd", bg="#182033", font=("Microsoft YaHei UI", 21, "bold")).pack(anchor="w", padx=22, pady=(20, 12))
        detail_shell = tk.Frame(right, bg="#182033")
        detail_shell.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        def set_detail(markdown_text):
            for child in detail_shell.winfo_children():
                child.destroy()
            render_markdown(detail_shell, markdown_text, mode="detail")
            self.reveal_background_surface(detail_shell)

        def selected_file_name():
            display = self.admin_browser_file_var.get()
            return state["file_display_to_name"].get(display, display)

        def render_selected_term(_event=None):
            selection = term_list.curselection()
            if not selection:
                set_detail("请选择左侧词条。")
                return
            index = int(selection[0])
            if index < 0 or index >= len(state["visible_terms"]):
                set_detail("请选择左侧词条。")
                return
            set_detail(self.admin_term_detail_markdown(state["visible_terms"][index]))

        def refresh_terms(*_args):
            file_name = selected_file_name()
            visible = [term for term in state["terms"] if term.source == file_name]
            state["visible_terms"] = visible
            term_list.delete(0, "end")
            for term in visible:
                term_list.insert(tk.END, f"{term.number}. {term.chinese}    {term.initials}    难度{term.difficulty}")
            if visible:
                term_list.selection_set(0)
                term_list.activate(0)
                render_selected_term()
            else:
                set_detail("当前词库没有可显示的词条。")

        def reload_files(*_args):
            try:
                terms, files = self.library.load(self.admin_browser_subject_var.get(), self.admin_browser_difficulty_var.get())
            except Exception as exc:
                state["files"] = []
                state["terms"] = []
                state["visible_terms"] = []
                state["file_display_to_name"] = {}
                reset_option_menu(file_option, self.admin_browser_file_var, [""])
                self.admin_browser_file_var.set("")
                term_list.delete(0, "end")
                set_detail(f"词库加载失败：{exc}")
                return
            state["files"] = files
            state["terms"] = terms
            displays = []
            display_map = {}
            for path in files:
                label = self.library.file_label(path)
                display = f"{label} ({path.name})"
                displays.append(display)
                display_map[display] = path.name
            state["file_display_to_name"] = display_map
            if not displays:
                displays = [""]
            reset_option_menu(file_option, self.admin_browser_file_var, displays)
            self.admin_browser_file_var.set(displays[0])
            refresh_terms()

        self.admin_browser_subject_var.trace_add("write", reload_files)
        self.admin_browser_difficulty_var.trace_add("write", reload_files)
        self.admin_browser_file_var.trace_add("write", refresh_terms)
        term_list.bind("<<ListboxSelect>>", render_selected_term)
        HoverButton(controls, "刷新", reload_files, width=112, height=42, accent="#8fb6ff").grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(8, 0))
        reload_files()
        self.reveal_background_surface(frame)

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
        admin_button = HoverButton(row_buttons, "设为管理员", lambda account=account: self.promote_account_to_admin(account), width=144, height=46, accent="#f6d36b")
        admin_button.grid(row=0, column=2, padx=8)
        if account.get("is_admin"):
            admin_button.disable("已是管理员")
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

    def promote_account_to_admin(self, account):
        admin_account = self.spectator_admin_account if self.is_spectating() else self.current_account
        if not is_admin_account(admin_account):
            messagebox.showerror("没有权限", "只有管理员账号可以设置管理员。")
            self.show_home()
            return
        nickname = account.get("nickname") or account.get("id") or "该账号"
        if not messagebox.askyesno("设置管理员", f"确认将 {nickname} 设置为管理员吗？"):
            return
        try:
            set_account_admin(account.get("id"), True)
        except AccountError as exc:
            messagebox.showerror("设置失败", str(exc))
            return
        if self.current_account and self.current_account.get("id") == account.get("id"):
            self.current_account = active_account()
        messagebox.showinfo("已设置", f"{nickname} 已成为管理员。")
        self.show_admin_dashboard()

    def show_achievements(self):
        self.refresh_achievements()
        self.clear()
        self._topbar("成就", self.show_home)
        base_bg = self.theme_color("base")
        frame = tk.Frame(self.container, bg=base_bg)
        frame.pack(fill="both", expand=True, padx=34, pady=(0, 24))
        self._start_backdrop("constellation", frame)
        completed = self.achievements.get("completed", {})
        progress_snapshot = self.achievement_progress_snapshot()
        completed_count = sum(1 for achievement_id, _title, _description in ACHIEVEMENTS if achievement_id in completed)
        tk.Label(
            frame,
            text=f"已完成 {completed_count} / {len(ACHIEVEMENTS)}",
            fg="#fff2bd",
            bg=base_bg,
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 14))
        scroll = self.make_scroll_frame(frame)
        achievement_lookup = {achievement_id: (title, description) for achievement_id, title, description in ACHIEVEMENTS}
        reveal_hidden = self.admin_reveal_hidden_enabled()
        used_ids = set()
        for category_title, achievement_ids in ACHIEVEMENT_CATEGORIES:
            visible_ids = [achievement_id for achievement_id in achievement_ids if achievement_id in achievement_lookup and achievement_id not in HIDDEN_ACHIEVEMENT_IDS]
            used_ids.update(visible_ids)
            self.render_achievement_category(scroll, category_title, visible_ids, achievement_lookup, completed, progress_snapshot, mysterious=False)

        remaining_ids = [
            achievement_id
            for achievement_id, _title, _description in ACHIEVEMENTS
            if achievement_id not in used_ids and achievement_id not in HIDDEN_ACHIEVEMENT_IDS
        ]
        if remaining_ids:
            self.render_achievement_category(scroll, "其他成就", remaining_ids, achievement_lookup, completed, progress_snapshot, mysterious=False)

        mystery_ids = [
            achievement_id
            for achievement_id, _title, _description in ACHIEVEMENTS
            if achievement_id in HIDDEN_ACHIEVEMENT_IDS
        ]
        self.render_achievement_category(scroll, "神秘成就", mystery_ids, achievement_lookup, completed, progress_snapshot, mysterious=not reveal_hidden)
        self.reveal_background_surface(frame)

    def render_achievement_category(self, parent, title, achievement_ids, achievement_lookup, completed, progress_snapshot, mysterious=False):
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
        elif title == "神秘成就" and self.admin_reveal_hidden_enabled():
            tk.Label(
                header,
                text="管理员隐藏已开启",
                fg="#f6d36b",
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
                progress_snapshot,
                hidden_until_complete=mysterious,
            )

    def render_achievement_card(self, parent, index, achievement_id, title, description, completed, progress_snapshot, hidden_until_complete=False):
        done = achievement_id in completed
        bg = "#1c2033" if hidden_until_complete and not done else "#182033"
        border = "#5b4775" if hidden_until_complete else "#30384e"
        row = tk.Frame(parent, bg=bg, highlightbackground=border, highlightthickness=1, width=350, height=132)
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
        progress_text = self.achievement_progress_text(achievement_id, progress_snapshot)
        right_text = f"{status_text}\n{progress_text}"
        if done:
            right_text = f"{right_text}\n{completed[achievement_id].replace('T', ' ')}"
        tk.Label(row, text=right_text, fg=status_color, bg=bg, justify="right", font=("Microsoft YaHei UI", 9, "bold")).pack(side="right", padx=(4, 10), pady=8)
