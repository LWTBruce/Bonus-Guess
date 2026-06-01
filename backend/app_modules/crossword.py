from ._shared import *


class CrosswordMixin:
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

    @staticmethod
    def crossword_source_table_key(term):
        source = str(getattr(term, "source", "") or "").strip()
        label = str(getattr(term, "source_label", "") or "").strip()
        return source, label

    @classmethod
    def balanced_crossword_terms_by_source_table(cls, terms, max_words=None, rng=None):
        source_terms = list(terms)
        if not source_terms:
            return []
        rng = rng or random
        buckets = {}
        for term in source_terms:
            buckets.setdefault(cls.crossword_source_table_key(term), []).append(term)
        table_keys = list(buckets)
        rng.shuffle(table_keys)
        selected_count = max(1, (len(table_keys) + 1) // 2)
        selected_keys = table_keys[:selected_count]
        target_pool = max(70, int(max_words or 0) * 8)
        per_table = max(1, (target_pool + selected_count - 1) // selected_count)
        balanced = []
        for key in selected_keys:
            bucket = list(buckets[key])
            rng.shuffle(bucket)
            balanced.extend(bucket[:per_table])
        rng.shuffle(balanced)
        return balanced or source_terms

    def crossword_terms_for_generation(self, difficulty, max_words):
        return self.balanced_crossword_terms_by_source_table(self.terms, max_words=max_words, rng=random)

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
        self.show_crossword_loading_screen(difficulty, is_crossword_rank=is_crossword_rank, size=size, max_words=max_words)
        try:
            terms_for_generation = self.crossword_terms_for_generation(difficulty, max_words)
            puzzle = generate_crossword(
                terms_for_generation,
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
        self.crossword_hint_box = tk.Text(left, height=5, width=1, wrap="char", fg="#dce6ff", bg="#111827", relief="flat", bd=0, highlightthickness=1, highlightbackground="#30384e", font=("Microsoft YaHei UI", 10))
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

    def crossword_direction_label(self, direction):
        labels = {
            "across": "横",
            "down": "纵",
            "tri_horizontal": "横",
            "tri_down": "右下",
            "tri_up": "右上",
            "hex_vertical": "竖",
            "hex_down": "右下",
            "hex_up": "右上",
        }
        return labels.get(direction, "线")

    def refresh_crossword_word_list(self):
        if not self.crossword_word_listbox or not self.crossword_puzzle:
            return
        self.crossword_word_listbox.delete(0, tk.END)
        selected_index = 0
        for index, placement in enumerate(self.crossword_puzzle.placements):
            direction = self.crossword_direction_label(placement.direction)
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

    def crossword_blocked_initials_are_unavoidable_pinyin_input(self, normalized_answer):
        placement = self.crossword_selected_placement()
        if not placement:
            return False
        answer = str(getattr(placement, "answer", "") or "")
        if len(answer) <= 1:
            return True
        pinyin = self.normalize_initial_input(getattr(getattr(placement, "term", None), "pinyin", ""))
        return bool(pinyin and (normalized_answer in pinyin or pinyin in normalized_answer))

    def crossword_contains_blocked_initials(self, normalized_answer):
        blocked = self.selected_crossword_initials()
        if not (blocked and blocked in normalized_answer):
            return False
        return not self.crossword_blocked_initials_are_unavoidable_pinyin_input(normalized_answer)

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
        add_record_entry_to_cache(record, path)
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
        tk.Label(
            detail,
            text="本张字谜全部认可答案",
            fg="#8fb6ff",
            bg="#182033",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", fill="x", pady=(8, 4))
        answer_entries = []
        for placement in self.crossword_puzzle.placements:
            direction = self.crossword_direction_label(placement.direction)
            answer_entries.append({
                "prefix": f"{placement.id:02d} {direction} {self.crossword_initials_for_placement(placement)}：",
                "answers": self.crossword_answer_candidates(placement),
            })
        answer_box = self.render_clickable_answer_entries(
            detail,
            answer_entries,
            height=max(4, min(8, len(answer_entries))),
            base_size=10,
        )
        answer_box.pack(fill="x", pady=(0, 8))
        self.bind_scroll_wheel(detail, answer_box)
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
