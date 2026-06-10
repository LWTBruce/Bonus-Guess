from __future__ import annotations

from dataclasses import dataclass, field, replace
import random
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .term_library import normalize_term_initials


Cell = Tuple[int, int]
PlacedCell = Tuple[int, int, str]
MaskFunc = Callable[[Any], Optional[Sequence[int]]]


DIFFICULTY_SIZES = {
    "入门": 8,
    "新手": 8,
    "easy": 11,
    "简单": 11,
    "普通": 15,
    "normal": 15,
    "困难": 18,
    "hard": 18,
    "噩梦": 22,
    "nightmare": 22,
    "混合模式": 15,
}

DIFFICULTY_DENSITIES = {
    "入门": 0.60,
    "新手": 0.60,
    "easy": 0.60,
    "简单": 0.60,
    "normal": 0.65,
    "普通": 0.65,
    "hard": 0.70,
    "困难": 0.70,
    "nightmare": 0.75,
    "噩梦": 0.75,
    "混合模式": 0.68,
    "自定义": 0.65,
}

DIFFICULTY_AVERAGE_LENGTHS = {
    "入门": 3.4,
    "新手": 3.4,
    "easy": 3.8,
    "简单": 3.8,
    "normal": 4.6,
    "普通": 4.6,
    "hard": 5.5,
    "困难": 5.5,
    "nightmare": 6.4,
    "噩梦": 6.4,
    "混合模式": 4.8,
    "自定义": 4.8,
}

DIFFICULTY_WORD_COUNT_CAP_FACTORS = {
    "入门": 1.15,
    "新手": 1.15,
    "easy": 1.25,
    "简单": 1.25,
    "normal": 1.35,
    "普通": 1.35,
    "hard": 1.45,
    "困难": 1.45,
    "nightmare": 1.70,
    "噩梦": 1.70,
    "混合模式": 1.40,
    "自定义": 1.40,
}

NORMAL_SOURCE_WEIGHTS = {
    "quantum_mechanics_terms.csv": 0.42,
    "electrodynamics_terms.csv": 0.62,
    "theoretical_mechanics_terms.csv": 1.90,
    "thermo_stat_mech_terms.csv": 2.15,
}


@dataclass(frozen=True)
class CrosswordPlacement:
    id: int
    term: Any
    answer: str
    initials: str
    display_initials: Optional[str]
    row: int
    col: int
    direction: str
    cells: List[PlacedCell]
    intersections: int
    source_label: str
    mask_positions: Set[int] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "term": self.term,
            "answer": self.answer,
            "initials": self.initials,
            "display_initials": self.display_initials,
            "row": self.row,
            "col": self.col,
            "direction": self.direction,
            "cells": list(self.cells),
            "intersections": self.intersections,
            "source_label": self.source_label,
            "mask_positions": sorted(self.mask_positions),
        }


@dataclass(frozen=True)
class CrosswordPuzzle:
    width: int
    height: int
    placements: List[CrosswordPlacement]
    grid: Dict[Cell, str]
    rows: List[List[Optional[str]]]
    intersection_count: int
    isolated_count: int
    cell_shape: str = "square"

    @property
    def cells(self) -> Dict[Cell, str]:
        return self.grid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "placements": [placement.to_dict() for placement in self.placements],
            "grid": dict(self.grid),
            "rows": [list(row) for row in self.rows],
            "cells": dict(self.grid),
            "intersection_count": self.intersection_count,
            "isolated_count": self.isolated_count,
            "cell_shape": self.cell_shape,
        }


@dataclass(frozen=True)
class _Candidate:
    term: Any
    answer: str
    initials: str
    row: int
    col: int
    direction: str
    cells: List[PlacedCell]
    intersections: int
    score: float


@dataclass(frozen=True)
class _IsolationInfo:
    word_count: int
    component_sizes: Dict[int, int]
    cell_components: Dict[Cell, int]
    main_size: int
    detached_count: int


SQUARE_DIRECTIONS = ("across", "down")
TRIANGLE_DIRECTIONS = ("tri_horizontal", "tri_down", "tri_up")
HEX_DIRECTIONS = ("hex_vertical", "hex_down", "hex_up")


def _normalize_cell_shape(cell_shape: Any) -> str:
    shape = str(cell_shape or "square").strip().lower()
    return shape if shape in {"square", "triangle", "hex"} else "square"


def _directions_for_shape(cell_shape: Any) -> Tuple[str, ...]:
    shape = _normalize_cell_shape(cell_shape)
    if shape == "triangle":
        return TRIANGLE_DIRECTIONS
    if shape == "hex":
        return HEX_DIRECTIONS
    return SQUARE_DIRECTIONS


def _triangle_points_up(row: int, col: int) -> bool:
    return (row + col) % 2 == 0


def _next_cell(row: int, col: int, direction: str, cell_shape: Any = "square") -> Cell:
    shape = _normalize_cell_shape(cell_shape)
    if shape == "triangle":
        if direction == "tri_horizontal":
            return row, col + 1
        if direction == "tri_down":
            return (row + 1, col) if _triangle_points_up(row, col) else (row, col + 1)
        if direction == "tri_up":
            return (row, col + 1) if _triangle_points_up(row, col) else (row - 1, col)
    elif shape == "hex":
        if direction == "hex_vertical":
            return row + 1, col
        if direction == "hex_down":
            return (row, col + 1) if col % 2 == 0 else (row + 1, col + 1)
        if direction == "hex_up":
            return (row - 1, col + 1) if col % 2 == 0 else (row, col + 1)
    else:
        if direction == "across":
            return row, col + 1
        if direction == "down":
            return row + 1, col
    raise ValueError(f"invalid direction for {shape} crossword: {direction}")


def _previous_cell(row: int, col: int, direction: str, cell_shape: Any = "square") -> Cell:
    shape = _normalize_cell_shape(cell_shape)
    if shape == "triangle":
        if direction == "tri_horizontal":
            return row, col - 1
        if direction == "tri_down":
            left = (row, col - 1)
            up = (row - 1, col)
            if not _triangle_points_up(*left):
                return left
            if _triangle_points_up(*up):
                return up
            return left
        if direction == "tri_up":
            left = (row, col - 1)
            down = (row + 1, col)
            if _triangle_points_up(*left):
                return left
            if not _triangle_points_up(*down):
                return down
            return left
    elif shape == "hex":
        if direction == "hex_vertical":
            return row - 1, col
        prev_col = col - 1
        if direction == "hex_down":
            return (row, prev_col) if prev_col % 2 == 0 else (row - 1, prev_col)
        if direction == "hex_up":
            return (row + 1, prev_col) if prev_col % 2 == 0 else (row, prev_col)
    else:
        if direction == "across":
            return row, col - 1
        if direction == "down":
            return row - 1, col
    raise ValueError(f"invalid direction for {shape} crossword: {direction}")


def _step_cell(row: int, col: int, direction: str, cell_shape: Any, steps: int) -> Cell:
    current = (row, col)
    stepper = _next_cell if steps >= 0 else _previous_cell
    for _ in range(abs(int(steps))):
        current = stepper(current[0], current[1], direction, cell_shape)
    return current


def _start_for_cell_at_index(row: int, col: int, index: int, direction: str, cell_shape: Any) -> Cell:
    return _step_cell(row, col, direction, cell_shape, -index)


def _side_neighbors(row: int, col: int, cell_shape: Any = "square") -> Tuple[Cell, ...]:
    shape = _normalize_cell_shape(cell_shape)
    if shape == "triangle":
        vertical = (row + 1, col) if _triangle_points_up(row, col) else (row - 1, col)
        return ((row, col - 1), (row, col + 1), vertical)
    if shape == "hex":
        return (
            _next_cell(row, col, "hex_vertical", shape),
            _previous_cell(row, col, "hex_vertical", shape),
            _next_cell(row, col, "hex_down", shape),
            _previous_cell(row, col, "hex_down", shape),
            _next_cell(row, col, "hex_up", shape),
            _previous_cell(row, col, "hex_up", shape),
        )
    return ((row, col - 1), (row, col + 1), (row - 1, col), (row + 1, col))


def _is_primary_direction(direction: str) -> bool:
    return direction in {"across", "tri_horizontal"}


def _is_down_direction(direction: str) -> bool:
    return direction in {"down", "hex_vertical"}


def size_for_difficulty(difficulty: Any) -> int:
    name = str(difficulty or "").strip()
    lowered = name.lower()
    if name in DIFFICULTY_SIZES:
        return DIFFICULTY_SIZES[name]
    if lowered in DIFFICULTY_SIZES:
        return DIFFICULTY_SIZES[lowered]
    if "入门" in name:
        return 8
    if "简单" in name or "easy" in lowered:
        return 11
    if "普通" in name or "normal" in lowered:
        return 15
    if "困难" in name or "hard" in lowered:
        return 18
    if "噩梦" in name or "nightmare" in lowered:
        return 22
    return 15


def _difficulty_key(difficulty: Any) -> str:
    name = str(difficulty or "").strip()
    lowered = name.lower()
    if name in DIFFICULTY_DENSITIES:
        return name
    if lowered in DIFFICULTY_DENSITIES:
        return lowered
    if "入门" in name:
        return "入门"
    if "简单" in name or "easy" in lowered:
        return "简单"
    if "普通" in name or "normal" in lowered:
        return "普通"
    if "困难" in name or "hard" in lowered:
        return "困难"
    if "噩梦" in name or "nightmare" in lowered:
        return "噩梦"
    if "混合" in name:
        return "混合模式"
    if "自定义" in name:
        return "自定义"
    return "普通"


def target_density_for_difficulty(difficulty: Any) -> float:
    return DIFFICULTY_DENSITIES.get(_difficulty_key(difficulty), DIFFICULTY_DENSITIES["普通"])


def target_average_word_length_for_difficulty(difficulty: Any) -> float:
    return DIFFICULTY_AVERAGE_LENGTHS.get(_difficulty_key(difficulty), DIFFICULTY_AVERAGE_LENGTHS["普通"])


def _word_count_cap_factor_for_difficulty(difficulty: Any) -> float:
    return DIFFICULTY_WORD_COUNT_CAP_FACTORS.get(_difficulty_key(difficulty), DIFFICULTY_WORD_COUNT_CAP_FACTORS["普通"])


def _size_dimensions(size: Any) -> Tuple[int, int]:
    if isinstance(size, (tuple, list)):
        return int(size[0]), int(size[1])
    value = int(size)
    return value, value


def target_word_count_for_size(size: Any, multiplier: float = 1.8, difficulty: Any = None, cell_shape: str = "square") -> int:
    width, height = _size_dimensions(size)
    density = target_density_for_difficulty(difficulty)
    average_length = target_average_word_length_for_difficulty(difficulty)
    effective_cells_per_word = max(2.0, average_length - 1.0)
    target_cells = max(width * height, 1) * density
    density_count = int(round(target_cells / effective_cells_per_word))
    side_count_cap = int(round(max(width, height) * multiplier * _word_count_cap_factor_for_difficulty(difficulty)))
    return max(5, min(density_count, max(5, side_count_cap)))


def generate_crossword(
    terms: Iterable[Any],
    difficulty: Any,
    rng: Optional[random.Random] = None,
    max_words: Optional[int] = None,
    size: Optional[Any] = None,
    mask_func: Optional[MaskFunc] = None,
    cell_shape: str = "square",
) -> CrosswordPuzzle:
    rng = rng or random.Random()
    cell_shape = _normalize_cell_shape(cell_shape)
    width, height = _resolve_size(size, difficulty)
    if width <= 0 or height <= 0:
        raise ValueError("crossword size must be positive")

    pool = _prepare_terms(terms, width, height, rng, difficulty)
    if max_words is None:
        max_words = min(len(pool), target_word_count_for_size((width, height), difficulty=difficulty, cell_shape=cell_shape))
    else:
        max_words = max(0, int(max_words))
    min_words = min(max_words, max(5, int(round(max_words * 0.84))))
    target_density = target_density_for_difficulty(difficulty)
    target_average_length = target_average_word_length_for_difficulty(difficulty)

    if not pool or max_words <= 0:
        rows = [[None for _ in range(width)] for _ in range(height)]
        return CrosswordPuzzle(width, height, [], {}, rows, 0, 0, cell_shape)

    attempts = _attempt_count(width, height, len(pool))
    best: Optional[CrosswordPuzzle] = None
    best_connected: Optional[CrosswordPuzzle] = None
    best_score = float("-inf")
    best_connected_score = float("-inf")
    for _attempt in range(attempts):
        order = _randomized_pool(pool, rng, max_words, width, height, difficulty)
        puzzle = _generate_once(order, width, height, max_words, min_words, mask_func, rng, cell_shape, target_density)
        score = _puzzle_score(puzzle, max_words, target_density, target_average_length)
        connected_enough = _detached_within_limit(puzzle.placements)
        if score > best_score:
            best = puzzle
            best_score = score
        if connected_enough and score > best_connected_score:
            best_connected = puzzle
            best_connected_score = score
        if connected_enough and _has_full_line_coverage(puzzle) and len(puzzle.placements) >= max_words:
            break
    empty_rows = [[None for _ in range(width)] for _ in range(height)]
    return best_connected or best or CrosswordPuzzle(width, height, [], {}, empty_rows, 0, 0, cell_shape)


def _generate_once(
    pool: List[Tuple[Any, str, str]],
    width: int,
    height: int,
    max_words: int,
    min_words: int,
    mask_func: Optional[MaskFunc],
    rng: random.Random,
    cell_shape: str,
    target_density: float,
) -> CrosswordPuzzle:
    grid: Dict[Cell, str] = {}
    cell_dirs: Dict[Cell, set] = {}
    placements: List[CrosswordPlacement] = []
    seen_answers = set()
    area = width * height
    isolated_limit = 0.20
    fallback_isolated_limit = 0.20

    for item in pool:
        if len(placements) >= max_words:
            break
        if (
            placements
            and _line_coverage_priority(grid, width, height) == 0
            and len(placements) >= max(min_words, int(round(max_words * 0.96)))
            and len(grid) / max(area, 1) >= target_density
        ):
            break
        term, answer, initials = item
        if answer in seen_answers:
            continue

        candidates = _crossing_candidates(term, answer, initials, grid, cell_dirs, placements, width, height, rng, cell_shape)
        should_fill_lines = _line_coverage_priority(grid, width, height) > 0
        isolation_info = _placement_isolation_info(placements)
        isolated_ratio = isolation_info.detached_count / max(len(placements), 1)
        down_count = sum(1 for placement in placements if _is_down_direction(placement.direction))
        down_ratio = down_count / max(len(placements), 1)
        if (
            placements
            and len(placements) < max_words
            and isolated_ratio < isolated_limit
            and (should_fill_lines or len(placements) < min_words or not candidates or down_ratio > 0.36)
        ):
            isolated_candidates = _isolated_candidates(term, answer, initials, grid, cell_dirs, placements, width, height, rng, cell_shape)
            isolated_candidates = [
                candidate
                for candidate in isolated_candidates
                if _candidate_projected_detached_count(placements, candidate, isolation_info) <= _detached_limit(len(placements) + 1)
            ]
            if down_ratio > 0.36:
                isolated_candidates = [
                    replace(candidate, score=candidate.score + (150 if _is_primary_direction(candidate.direction) else -120))
                    for candidate in isolated_candidates
                ]
            candidates.extend(isolated_candidates)
        if not candidates and not placements:
            first = _center_candidate(term, answer, initials, width, height, cell_shape)
            candidates = [first] if first else []
        if not candidates and (not placements or should_fill_lines or (len(placements) < min_words and isolated_ratio < fallback_isolated_limit and rng.random() < 0.30)):
            candidates = _isolated_candidates(term, answer, initials, grid, cell_dirs, placements, width, height, rng, cell_shape)
        if not candidates:
            continue
        if placements:
            candidates = _connectivity_preferred_candidates(placements, candidates)
            if not candidates:
                continue

        best = max(candidates, key=lambda candidate: candidate.score)
        placement = _make_placement(len(placements) + 1, best, mask_func)
        placements.append(placement)
        seen_answers.add(answer)
        for r, c, char in placement.cells:
            grid[(r, c)] = char
            cell_dirs.setdefault((r, c), set()).add(placement.direction)

    return _puzzle_from_placements(width, height, placements, cell_shape)


def _refresh_intersections(placements: List[CrosswordPlacement]) -> List[CrosswordPlacement]:
    cell_usage: Dict[Cell, int] = {}
    for placement in placements:
        for row, col, _char in placement.cells:
            cell_usage[(row, col)] = cell_usage.get((row, col), 0) + 1
    return [
        replace(
            placement,
            intersections=sum(1 for row, col, _char in placement.cells if cell_usage.get((row, col), 0) > 1),
        )
        for placement in placements
    ]


def _propagate_intersection_masks(placements: List[CrosswordPlacement]) -> List[CrosswordPlacement]:
    cell_usage: Dict[Cell, List[Tuple[int, int]]] = {}
    for placement_index, placement in enumerate(placements):
        for char_index, (row, col, _char) in enumerate(placement.cells):
            cell_usage.setdefault((row, col), []).append((placement_index, char_index))
    propagated = [set(placement.mask_positions) for placement in placements]
    for usage in cell_usage.values():
        if len(usage) <= 1:
            continue
        if any(char_index in propagated[placement_index] for placement_index, char_index in usage):
            for placement_index, char_index in usage:
                propagated[placement_index].add(char_index)
    result = []
    for placement, mask_positions in zip(placements, propagated):
        display_initials = _apply_initial_mask(placement.initials, mask_positions) if mask_positions else None
        result.append(replace(placement, mask_positions=mask_positions, display_initials=display_initials))
    return result


def _puzzle_from_placements(width: int, height: int, placements: Sequence[CrosswordPlacement], cell_shape: str) -> CrosswordPuzzle:
    refreshed = _refresh_intersections(list(placements))
    if refreshed and not _detached_within_limit(refreshed):
        refreshed = _trim_detached_components(refreshed)
        refreshed = _refresh_intersections(refreshed)
    refreshed = _propagate_intersection_masks(refreshed)
    grid: Dict[Cell, str] = {}
    for placement in refreshed:
        for row, col, char in placement.cells:
            grid[(row, col)] = char
    rows = [[grid.get((r, c)) for c in range(width)] for r in range(height)]
    intersection_count = sum(placement.intersections for placement in refreshed)
    isolated_count = _detached_placement_count(refreshed)
    return CrosswordPuzzle(width, height, refreshed, grid, rows, intersection_count, isolated_count, cell_shape)


def _trim_detached_components(placements: Sequence[CrosswordPlacement]) -> List[CrosswordPlacement]:
    components = _placement_component_indices(placements)
    if len(components) <= 1:
        return list(placements)
    main = components[0]
    keep = set(main)
    detached_kept = 0
    for component in components[1:]:
        next_detached = detached_kept + len(component)
        next_total = len(main) + next_detached
        if next_detached <= _detached_limit(next_total):
            keep.update(component)
            detached_kept = next_detached
    trimmed = [placement for index, placement in enumerate(placements) if index in keep]
    return [replace(placement, id=index + 1) for index, placement in enumerate(trimmed)]


def validate_crossword(puzzle: CrosswordPuzzle) -> bool:
    grid: Dict[Cell, str] = {}
    seen_ids = set()
    seen_answers = set()
    cell_shape = _normalize_cell_shape(getattr(puzzle, "cell_shape", "square"))
    valid_directions = set(_directions_for_shape(cell_shape))
    for placement in puzzle.placements:
        if placement.id in seen_ids:
            raise ValueError(f"duplicate placement id: {placement.id}")
        seen_ids.add(placement.id)
        if placement.answer in seen_answers:
            raise ValueError(f"duplicate crossword answer: {placement.answer}")
        seen_answers.add(placement.answer)
        if placement.direction not in valid_directions:
            raise ValueError(f"invalid direction for placement {placement.id}: {placement.direction}")
        if len(placement.cells) != len(placement.answer):
            raise ValueError(f"cell count does not match answer length for placement {placement.id}")

        for index, (r, c, char) in enumerate(placement.cells):
            if not (0 <= r < puzzle.height and 0 <= c < puzzle.width):
                raise ValueError(f"placement {placement.id} is out of bounds at {(r, c)}")
            if char != placement.answer[index]:
                raise ValueError(f"placement {placement.id} cell text does not match answer")
            expected = _step_cell(placement.row, placement.col, placement.direction, cell_shape, index)
            if (r, c) != expected:
                raise ValueError(f"placement {placement.id} has non-contiguous cells")
            if index > 0 and (r, c) not in _side_neighbors(placement.cells[index - 1][0], placement.cells[index - 1][1], cell_shape):
                raise ValueError(f"placement {placement.id} has cells without a shared edge")
            existing = grid.get((r, c))
            if existing is not None and existing != char:
                raise ValueError(f"conflicting characters at {(r, c)}")
            grid[(r, c)] = char

    if dict(puzzle.grid) != grid:
        raise ValueError("puzzle grid does not match placement cells")
    for r, row in enumerate(puzzle.rows):
        if len(row) != puzzle.width:
            raise ValueError(f"row {r} has width {len(row)}, expected {puzzle.width}")
        for c, char in enumerate(row):
            if char != puzzle.grid.get((r, c)):
                raise ValueError(f"row/grid mismatch at {(r, c)}")
    cell_usage: Dict[Cell, int] = {}
    for placement in puzzle.placements:
        for row, col, _char in placement.cells:
            cell_usage[(row, col)] = cell_usage.get((row, col), 0) + 1
    intersection_count = 0
    for placement in puzzle.placements:
        actual_intersections = sum(
            1
            for row, col, _char in placement.cells
            if cell_usage.get((row, col), 0) > 1
        )
        if placement.intersections != actual_intersections:
            raise ValueError(f"placement {placement.id} intersections do not match placement cells")
        intersection_count += actual_intersections
    if puzzle.intersection_count != intersection_count:
        raise ValueError("puzzle intersection_count does not match placements")
    isolated_count = _detached_placement_count(list(puzzle.placements))
    if puzzle.isolated_count != isolated_count:
        raise ValueError("puzzle isolated_count does not match placements")
    return True


def _resolve_size(size: Optional[Any], difficulty: Any) -> Tuple[int, int]:
    if size is None:
        value = size_for_difficulty(difficulty)
        return value, value
    if isinstance(size, (tuple, list)):
        if len(size) != 2:
            raise ValueError("crossword size tuple must be (width, height)")
        return int(size[0]), int(size[1])
    value = int(size)
    return value, value


def _prepare_terms(terms: Iterable[Any], width: int, height: int, rng: random.Random, difficulty: Any) -> List[Tuple[Any, str, str]]:
    seen = set()
    prepared: List[Tuple[Any, str, str]] = []
    board_size = max(width, height)
    limit = min(board_size, max(5, int(round(board_size * 0.48))))
    for term in terms:
        answer = str(getattr(term, "chinese", "") or "").strip()
        initials = normalize_term_initials(answer, getattr(term, "initials", ""))
        if not answer or answer in seen or len(answer) > limit or len(initials) != len(answer):
            continue
        seen.add(answer)
        prepared.append((term, answer, initials))

    char_counts: Dict[str, int] = {}
    for _, answer, _ in prepared:
        for char in set(answer):
            char_counts[char] = char_counts.get(char, 0) + 1

    decorated = []
    for item in prepared:
        _, answer, _ = item
        overlap = sum(char_counts.get(char, 0) - 1 for char in set(answer))
        ascii_penalty = sum(1 for char in answer if char.isascii() and char.isalpha()) * 3.2
        length_bonus = _crossword_length_bonus(len(answer), target_average_word_length_for_difficulty(difficulty))
        decorated.append((overlap * 5 + length_bonus - ascii_penalty + _source_weight_bonus(item[0], difficulty, 65.0) + rng.random(), item))
    decorated.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in decorated]


def _crossword_length_bonus(length: int, target_average_length: float = 4.6) -> float:
    if length <= 1:
        return -22.0
    if length == 2:
        return -8.0
    if length == 3 and target_average_length >= 4.8:
        return 1.5
    return max(-8.0, 18.0 - abs(length - target_average_length) * 2.25)


def _is_normal_difficulty(difficulty: Any) -> bool:
    text = str(difficulty or "").strip().lower()
    return text in {"普通", "normal"} or "普通" in text


def _source_weight_bonus(term: Any, difficulty: Any, scale: float) -> float:
    if not _is_normal_difficulty(difficulty):
        return 0.0
    source = str(getattr(term, "source", "") or "").lower()
    weight = NORMAL_SOURCE_WEIGHTS.get(source, 1.0)
    return (weight - 1.0) * scale


def _attempt_count(width: int, height: int, pool_size: int) -> int:
    base = 8
    return min(12, max(base, pool_size // 260))


def _randomized_pool(
    pool: List[Tuple[Any, str, str]],
    rng: random.Random,
    max_words: int,
    width: int,
    height: int,
    difficulty: Any,
) -> List[Tuple[Any, str, str]]:
    limit = min(len(pool), max(60, max_words * 5))
    ranked = list(pool[:limit])
    rng.shuffle(ranked)
    char_counts: Dict[str, int] = {}
    for _term, answer, _initials in ranked:
        for char in set(answer):
            char_counts[char] = char_counts.get(char, 0) + 1

    def score(item: Tuple[Any, str, str]) -> float:
        term, answer, _initials = item
        overlap = sum(char_counts.get(char, 0) - 1 for char in set(answer))
        length = len(answer)
        length_bonus = _crossword_length_bonus(length, target_average_word_length_for_difficulty(difficulty)) * 2.6
        ascii_penalty = sum(1 for char in answer if char.isascii() and char.isalpha()) * 5.0
        return overlap * 7.0 + length_bonus - ascii_penalty + _source_weight_bonus(term, difficulty, 90.0) + rng.random() * 28.0

    ranked.sort(key=score, reverse=True)
    return ranked


def _coverage_sets(grid: Dict[Cell, str]) -> Tuple[Set[int], Set[int]]:
    rows = {row for row, _col in grid}
    cols = {col for _row, col in grid}
    return rows, cols


def _line_coverage_priority(grid: Dict[Cell, str], width: int, height: int) -> int:
    rows, cols = _coverage_sets(grid)
    return (height - len(rows)) + (width - len(cols))


def _has_full_line_coverage(puzzle: CrosswordPuzzle) -> bool:
    if not puzzle.grid:
        return False
    rows, cols = _coverage_sets(puzzle.grid)
    return len(rows) >= puzzle.height and len(cols) >= puzzle.width


def _detached_limit(word_count: int) -> int:
    return max(0, int(word_count * 0.20))


def _detached_within_limit(placements: Sequence[Any]) -> bool:
    if not placements:
        return True
    return _detached_placement_count(placements, single_isolated=False) <= _detached_limit(len(placements))


def _connectivity_preferred_candidates(placements: Sequence[CrosswordPlacement], candidates: Sequence[_Candidate]) -> List[_Candidate]:
    if not candidates:
        return []
    info = _placement_isolation_info(placements)
    projected = [
        (candidate, _candidate_projected_detached_count(placements, candidate, info))
        for candidate in candidates
    ]
    limit = _detached_limit(len(placements) + 1)
    within_limit = [candidate for candidate, detached_count in projected if detached_count <= limit]
    if within_limit:
        return within_limit
    improving = [candidate for candidate, detached_count in projected if detached_count < info.detached_count]
    if improving:
        return improving
    if info.detached_count > _detached_limit(len(placements)):
        stable = [candidate for candidate, detached_count in projected if detached_count <= info.detached_count]
        return stable
    return list(candidates)


def _detached_placement_count(placements: Sequence[Any], single_isolated: bool = False) -> int:
    if len(placements) <= 1 and single_isolated:
        return len(placements)
    return _placement_isolation_info(placements).detached_count


def _candidate_projected_detached_count(
    placements: Sequence[CrosswordPlacement],
    candidate: _Candidate,
    isolation_info: Optional[_IsolationInfo] = None,
) -> int:
    info = isolation_info or _placement_isolation_info(placements)
    if info.word_count <= 0:
        return 0
    touched_components = {
        info.cell_components[(row, col)]
        for row, col, _char in candidate.cells
        if (row, col) in info.cell_components
    }
    projected_count = info.word_count + 1
    if not touched_components:
        return projected_count - max(info.main_size, 1)
    merged_size = 1 + sum(info.component_sizes[component] for component in touched_components)
    largest = merged_size
    for component, size in info.component_sizes.items():
        if component not in touched_components and size > largest:
            largest = size
    return projected_count - largest


def _placement_isolation_info(placements: Sequence[Any]) -> _IsolationInfo:
    cell_lists = [list(getattr(placement, "cells", placement)) for placement in placements]
    count = len(cell_lists)
    if count <= 1:
        cell_components: Dict[Cell, int] = {}
        if count == 1:
            for row, col, _char in cell_lists[0]:
                cell_components[(row, col)] = 0
        return _IsolationInfo(count, ({0: 1} if count == 1 else {}), cell_components, count, 0)

    parents = list(range(count))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    cell_usage: Dict[Cell, List[int]] = {}
    for placement_index, cells in enumerate(cell_lists):
        for row, col, _char in cells:
            cell_usage.setdefault((row, col), []).append(placement_index)
    for usage in cell_usage.values():
        if len(usage) <= 1:
            continue
        first = usage[0]
        for placement_index in usage[1:]:
            union(first, placement_index)

    component_sizes: Dict[int, int] = {}
    component_by_index: List[int] = []
    for placement_index in range(count):
        root = find(placement_index)
        component_by_index.append(root)
        component_sizes[root] = component_sizes.get(root, 0) + 1
    cell_components: Dict[Cell, int] = {}
    for placement_index, cells in enumerate(cell_lists):
        root = component_by_index[placement_index]
        for row, col, _char in cells:
            cell_components[(row, col)] = root
    main_size = max(component_sizes.values(), default=0)
    return _IsolationInfo(count, component_sizes, cell_components, main_size, count - main_size)


def _placement_component_indices(placements: Sequence[Any]) -> List[List[int]]:
    cell_lists = [list(getattr(placement, "cells", placement)) for placement in placements]
    count = len(cell_lists)
    if count == 0:
        return []
    if count == 1:
        return [[0]]
    parents = list(range(count))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    cell_usage: Dict[Cell, List[int]] = {}
    for placement_index, cells in enumerate(cell_lists):
        for row, col, _char in cells:
            cell_usage.setdefault((row, col), []).append(placement_index)
    for usage in cell_usage.values():
        if len(usage) <= 1:
            continue
        first = usage[0]
        for placement_index in usage[1:]:
            union(first, placement_index)

    groups: Dict[int, List[int]] = {}
    for placement_index in range(count):
        groups.setdefault(find(placement_index), []).append(placement_index)
    return sorted(groups.values(), key=lambda group: (-len(group), group[0]))


def _puzzle_score(puzzle: CrosswordPuzzle, max_words: int, target_density: Optional[float] = None, target_average_length: Optional[float] = None) -> float:
    if not puzzle.placements:
        return float("-inf")
    rows, cols = _coverage_sets(puzzle.grid)
    empty_rows = puzzle.height - len(rows)
    empty_cols = puzzle.width - len(cols)
    filled = len(puzzle.grid)
    area = puzzle.width * puzzle.height
    density = filled / max(area, 1)
    min_r = min(rows)
    max_r = max(rows)
    min_c = min(cols)
    max_c = max(cols)
    spread_area = ((max_r - min_r + 1) * (max_c - min_c + 1)) / max(area, 1)
    if target_density is None:
        target_density = _target_density(puzzle.width, puzzle.height)
    if target_average_length is None:
        target_average_length = 4.6
    density_penalty = abs(density - target_density) * 760
    lengths = [len(placement.answer) for placement in puzzle.placements]
    average_length = sum(lengths) / max(len(lengths), 1)
    short_ratio = sum(1 for length in lengths if length <= 3) / max(len(lengths), 1)
    average_length_penalty = abs(average_length - target_average_length) * len(puzzle.placements) * 8
    short_penalty = max(0.0, short_ratio - 0.25) * len(puzzle.placements) * 180
    down_count = sum(1 for placement in puzzle.placements if _is_down_direction(placement.direction))
    down_ratio = down_count / max(len(puzzle.placements), 1)
    down_penalty = max(0.0, down_ratio - 0.35) * len(puzzle.placements) * 210
    return (
        len(puzzle.placements) * 82
        + min(len(puzzle.placements), max_words) * 10
        + puzzle.intersection_count * 55
        + len(rows) * 28
        + len(cols) * 28
        + spread_area * 95
        - empty_rows * 760
        - empty_cols * 760
        - puzzle.isolated_count * 540
        - max(0, puzzle.isolated_count - _detached_limit(len(puzzle.placements))) * 920
        - density_penalty
        - average_length_penalty
        - short_penalty
        - down_penalty
    )


def _target_density(width: int, height: int) -> float:
    size = max(width, height)
    if size <= 11:
        return 0.60
    if size <= 15:
        return 0.65
    if size <= 18:
        return 0.70
    return 0.75


def _crossing_candidates(
    term: Any,
    answer: str,
    initials: str,
    grid: Dict[Cell, str],
    cell_dirs: Dict[Cell, set],
    placements: List[CrosswordPlacement],
    width: int,
    height: int,
    rng: random.Random,
    cell_shape: str,
) -> List[_Candidate]:
    candidates: List[_Candidate] = []
    component_info = _placement_isolation_info(placements)
    by_char: Dict[str, List[Cell]] = {}
    for cell, char in grid.items():
        by_char.setdefault(char, []).append(cell)

    for index, char in enumerate(answer):
        for r, c in by_char.get(char, []):
            for direction in _directions_for_shape(cell_shape):
                row, col = _start_for_cell_at_index(r, c, index, direction, cell_shape)
                candidate = _candidate(term, answer, initials, row, col, direction, grid, cell_dirs, width, height, cell_shape)
                if candidate and candidate.intersections > 0:
                    score = _candidate_score(candidate, grid, placements, width, height, rng, component_info)
                    candidates.append(_Candidate(term, answer, initials, row, col, direction, candidate.cells, candidate.intersections, score))
                    if len(candidates) >= 96:
                        return candidates
    return candidates


def _isolated_candidates(
    term: Any,
    answer: str,
    initials: str,
    grid: Dict[Cell, str],
    cell_dirs: Dict[Cell, set],
    placements: List[CrosswordPlacement],
    width: int,
    height: int,
    rng: random.Random,
    cell_shape: str,
) -> List[_Candidate]:
    candidates: List[_Candidate] = []
    shape = _normalize_cell_shape(cell_shape)
    component_info = _placement_isolation_info(placements)
    if shape != "square":
        starts = []
        for direction in _directions_for_shape(shape):
            for row in range(height):
                for col in range(width):
                    cells = _cells_for(answer, row, col, direction, shape)
                    if all(0 <= r < height and 0 <= c < width for r, c, _char in cells):
                        starts.append((row, col, direction))
        rows, cols = _coverage_sets(grid)
        priority = [
            start
            for start in starts
            if any(r not in rows or c not in cols for r, c, _char in _cells_for(answer, start[0], start[1], start[2], shape))
        ]
        priority_set = set(priority)
        rest = [start for start in starts if start not in priority_set]
        rng.shuffle(priority)
        rng.shuffle(rest)
        for row, col, direction in (priority + rest)[: min(len(starts), 520)]:
            candidate = _candidate(term, answer, initials, row, col, direction, grid, cell_dirs, width, height, shape)
            if candidate and candidate.intersections == 0:
                score = _candidate_score(candidate, grid, placements, width, height, rng, component_info) - 65
                candidates.append(_Candidate(term, answer, initials, row, col, direction, candidate.cells, 0, score))
        return candidates

    starts = []
    used_starts = set()
    rows, cols = _coverage_sets(grid)
    empty_rows = [row for row in range(height) if row not in rows]
    empty_cols = [col for col in range(width) if col not in cols]
    for row in empty_rows:
        for col in range(max(0, width - len(answer) + 1)):
            starts.append((row, col, "across"))
            used_starts.add((row, col, "across"))
    for col in empty_cols:
        for row in range(max(0, height - len(answer) + 1)):
            starts.append((row, col, "down"))
            used_starts.add((row, col, "down"))
    for direction in ("across", "down"):
        row_limit = height if direction == "across" else height - len(answer) + 1
        col_limit = width - len(answer) + 1 if direction == "across" else width
        for row in range(max(0, row_limit)):
            for col in range(max(0, col_limit)):
                start = (row, col, direction)
                if start not in used_starts:
                    starts.append(start)
    priority = starts[: len(empty_rows) * max(0, width - len(answer) + 1) + len(empty_cols) * max(0, height - len(answer) + 1)]
    rest = starts[len(priority):]
    rng.shuffle(priority)
    rng.shuffle(rest)
    starts = priority + rest
    for row, col, direction in starts[: min(len(starts), 520)]:
        candidate = _candidate(term, answer, initials, row, col, direction, grid, cell_dirs, width, height, shape)
        if candidate and candidate.intersections == 0:
            score = _candidate_score(candidate, grid, placements, width, height, rng, component_info) - 65
            candidates.append(_Candidate(term, answer, initials, row, col, direction, candidate.cells, 0, score))
    return candidates


def _center_candidate(term: Any, answer: str, initials: str, width: int, height: int, cell_shape: str) -> Optional[_Candidate]:
    shape = _normalize_cell_shape(cell_shape)
    if shape != "square":
        best: Optional[_Candidate] = None
        best_penalty = float("inf")
        for direction in _directions_for_shape(shape):
            for row in range(height):
                for col in range(width):
                    cells = _cells_for(answer, row, col, direction, shape)
                    if any(r < 0 or r >= height or c < 0 or c >= width for r, c, _ in cells):
                        continue
                    penalty = _center_penalty(cells, width, height)
                    if penalty < best_penalty:
                        best_penalty = penalty
                        best = _Candidate(term, answer, initials, row, col, direction, cells, 0, 0)
        return best

    direction = "across" if len(answer) <= width else "down"
    if direction == "across":
        row = height // 2
        col = max(0, (width - len(answer)) // 2)
    else:
        row = max(0, (height - len(answer)) // 2)
        col = width // 2
    cells = _cells_for(answer, row, col, direction, shape)
    if any(r < 0 or r >= height or c < 0 or c >= width for r, c, _ in cells):
        return None
    return _Candidate(term, answer, initials, row, col, direction, cells, 0, 0)


def _candidate(
    term: Any,
    answer: str,
    initials: str,
    row: int,
    col: int,
    direction: str,
    grid: Dict[Cell, str],
    cell_dirs: Dict[Cell, set],
    width: int,
    height: int,
    cell_shape: str,
) -> Optional[_Candidate]:
    shape = _normalize_cell_shape(cell_shape)
    cells = _cells_for(answer, row, col, direction, shape)
    intersections = 0
    before = _previous_cell(row, col, direction, shape)
    after = _step_cell(row, col, direction, shape, len(answer))
    if before in grid or after in grid:
        return None
    for r, c, char in cells:
        if not (0 <= r < height and 0 <= c < width):
            return None
        existing = grid.get((r, c))
        if existing is not None:
            if existing != char or direction in cell_dirs.get((r, c), set()):
                return None
            intersections += 1
            continue
    return _Candidate(term, answer, initials, row, col, direction, cells, intersections, 0)


def _cells_for(answer: str, row: int, col: int, direction: str, cell_shape: Any = "square") -> List[PlacedCell]:
    cells: List[PlacedCell] = []
    current_row, current_col = row, col
    for char in answer:
        cells.append((current_row, current_col, char))
        current_row, current_col = _next_cell(current_row, current_col, direction, cell_shape)
    return cells


def _center_penalty(cells: List[PlacedCell], width: int, height: int) -> float:
    center_r = (height - 1) / 2
    center_c = (width - 1) / 2
    return min(abs(r - center_r) + abs(c - center_c) for r, c, _ in cells)


def _candidate_score(
    candidate: _Candidate,
    grid: Dict[Cell, str],
    placements: List[CrosswordPlacement],
    width: int,
    height: int,
    rng: random.Random,
    component_info: Optional[_IsolationInfo] = None,
) -> float:
    old_rows, old_cols = _coverage_sets(grid)
    candidate_cells = {(r, c) for r, c, _char in candidate.cells}
    new_rows = {r for r, _c in candidate_cells} - old_rows
    new_cols = {c for _r, c in candidate_cells} - old_cols
    merged = dict(grid)
    for r, c, char in candidate.cells:
        merged[(r, c)] = char
    merged_rows, merged_cols = _coverage_sets(merged)
    min_r = min(merged_rows)
    max_r = max(merged_rows)
    min_c = min(merged_cols)
    max_c = max(merged_cols)
    spread_area = ((max_r - min_r + 1) * (max_c - min_c + 1)) / max(width * height, 1)
    center_penalty = _center_penalty(candidate.cells, width, height)
    uncovered_bonus = _line_coverage_priority(grid, width, height) * 2
    down_count = sum(1 for placement in placements if _is_down_direction(placement.direction))
    projected_down_ratio = (down_count + (1 if _is_down_direction(candidate.direction) else 0)) / max(len(placements) + 1, 1)
    direction_adjust = 18 if _is_primary_direction(candidate.direction) else -24
    if projected_down_ratio > 0.35:
        direction_adjust -= (projected_down_ratio - 0.35) * 230
    if _is_down_direction(candidate.direction) and candidate.intersections == 0:
        direction_adjust -= 48
    info = component_info or _placement_isolation_info(placements)
    current_detached = info.detached_count
    projected_detached = _candidate_projected_detached_count(placements, candidate, info)
    detached_limit = _detached_limit(len(placements) + 1)
    detached_delta = projected_detached - current_detached
    detached_penalty = projected_detached * 90 + max(0, detached_delta) * 280
    if projected_detached > detached_limit:
        detached_penalty += (projected_detached - detached_limit) * 520
    return (
        candidate.intersections * 92
        + len(candidate.answer) * 4
        + len(new_rows) * 35
        + len(new_cols) * 35
        + spread_area * 50
        + uncovered_bonus
        + direction_adjust
        - center_penalty * 2.5
        - detached_penalty
        + rng.random() * 5
    )


def _make_placement(placement_id: int, candidate: _Candidate, mask_func: Optional[MaskFunc]) -> CrosswordPlacement:
    display_initials = None
    mask_positions: Set[int] = set()
    if mask_func is not None:
        positions = mask_func(candidate.term)
        if positions is not None:
            mask_positions = {int(position) for position in positions if 0 <= int(position) < len(candidate.initials)}
            display_initials = _apply_initial_mask(candidate.initials, mask_positions)
    return CrosswordPlacement(
        id=placement_id,
        term=candidate.term,
        answer=candidate.answer,
        initials=candidate.initials,
        display_initials=display_initials,
        row=candidate.row,
        col=candidate.col,
        direction=candidate.direction,
        cells=candidate.cells,
        intersections=candidate.intersections,
        source_label=str(getattr(candidate.term, "source_label", "") or ""),
        mask_positions=mask_positions,
    )


def _apply_initial_mask(initials: str, positions: Sequence[int]) -> str:
    chars = list(initials)
    for position in positions:
        if 0 <= int(position) < len(chars):
            chars[int(position)] = "*"
    return "".join(chars)
