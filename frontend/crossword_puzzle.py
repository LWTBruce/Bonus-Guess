from __future__ import annotations

from dataclasses import dataclass, field, replace
import random
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from term_library import normalize_term_initials


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
    return 15


def target_word_count_for_size(size: Any, multiplier: float = 1.8) -> int:
    if isinstance(size, (tuple, list)):
        value = max(int(size[0]), int(size[1]))
    else:
        value = int(size)
    return max(5, int(round(value * multiplier)))


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
    width, height = _resolve_size(size, difficulty)
    if width <= 0 or height <= 0:
        raise ValueError("crossword size must be positive")

    pool = _prepare_terms(terms, width, height, rng, difficulty)
    if max_words is None:
        max_words = min(len(pool), target_word_count_for_size(max(width, height)))
    else:
        max_words = max(0, int(max_words))
    min_words = min(max_words, max(5, int(round(max_words * 0.88))))

    if not pool or max_words <= 0:
        rows = [[None for _ in range(width)] for _ in range(height)]
        return CrosswordPuzzle(width, height, [], {}, rows, 0, 0, cell_shape)

    attempts = _attempt_count(width, height, len(pool))
    best: Optional[CrosswordPuzzle] = None
    best_score = float("-inf")
    for _attempt in range(attempts):
        order = _randomized_pool(pool, rng, max_words, width, height, difficulty)
        puzzle = _generate_once(order, width, height, max_words, min_words, mask_func, rng, cell_shape)
        score = _puzzle_score(puzzle, max_words)
        if score > best_score:
            best = puzzle
            best_score = score
        if _has_full_line_coverage(puzzle) and len(puzzle.placements) >= max_words:
            break
    empty_rows = [[None for _ in range(width)] for _ in range(height)]
    return best or CrosswordPuzzle(width, height, [], {}, empty_rows, 0, 0, cell_shape)


def _generate_once(
    pool: List[Tuple[Any, str, str]],
    width: int,
    height: int,
    max_words: int,
    min_words: int,
    mask_func: Optional[MaskFunc],
    rng: random.Random,
    cell_shape: str,
) -> CrosswordPuzzle:
    grid: Dict[Cell, str] = {}
    cell_dirs: Dict[Cell, set] = {}
    placements: List[CrosswordPlacement] = []
    seen_answers = set()
    area = width * height
    target_density = _target_density(width, height)

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

        candidates = _crossing_candidates(term, answer, initials, grid, cell_dirs, placements, width, height, rng)
        should_fill_lines = _line_coverage_priority(grid, width, height) > 0
        isolated_ratio = sum(1 for placement in placements if placement.intersections == 0) / max(len(placements), 1)
        down_count = sum(1 for placement in placements if placement.direction == "down")
        down_ratio = down_count / max(len(placements), 1)
        if (
            placements
            and len(placements) < max_words
            and isolated_ratio < 0.42
            and (should_fill_lines or len(placements) < min_words or not candidates or down_ratio > 0.36)
        ):
            isolated_candidates = _isolated_candidates(term, answer, initials, grid, cell_dirs, placements, width, height, rng)
            if down_ratio > 0.36:
                isolated_candidates = [
                    replace(candidate, score=candidate.score + (150 if candidate.direction == "across" else -120))
                    for candidate in isolated_candidates
                ]
            candidates.extend(isolated_candidates)
        if not candidates and not placements:
            first = _center_candidate(term, answer, initials, width, height)
            candidates = [first] if first else []
        if not candidates and (not placements or should_fill_lines or (len(placements) < min_words and isolated_ratio < 0.34 and rng.random() < 0.24)):
            candidates = _isolated_candidates(term, answer, initials, grid, cell_dirs, placements, width, height, rng)
        if not candidates:
            continue

        best = max(candidates, key=lambda candidate: candidate.score)
        placement = _make_placement(len(placements) + 1, best, mask_func)
        placements.append(placement)
        seen_answers.add(answer)
        for r, c, char in placement.cells:
            grid[(r, c)] = char
            cell_dirs.setdefault((r, c), set()).add(placement.direction)

    placements = _refresh_intersections(placements)
    placements = _propagate_intersection_masks(placements)
    rows = [[grid.get((r, c)) for c in range(width)] for r in range(height)]
    intersection_count = sum(placement.intersections for placement in placements)
    isolated_count = sum(1 for placement in placements if placement.intersections == 0)
    return CrosswordPuzzle(width, height, placements, grid, rows, intersection_count, isolated_count, cell_shape)


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


def validate_crossword(puzzle: CrosswordPuzzle) -> bool:
    grid: Dict[Cell, str] = {}
    intersection_count = 0
    isolated_count = 0
    seen_ids = set()
    seen_answers = set()
    for placement in puzzle.placements:
        intersection_count += placement.intersections
        if placement.intersections == 0:
            isolated_count += 1
        if placement.id in seen_ids:
            raise ValueError(f"duplicate placement id: {placement.id}")
        seen_ids.add(placement.id)
        if placement.answer in seen_answers:
            raise ValueError(f"duplicate crossword answer: {placement.answer}")
        seen_answers.add(placement.answer)
        if placement.direction not in {"across", "down"}:
            raise ValueError(f"invalid direction for placement {placement.id}: {placement.direction}")
        if len(placement.cells) != len(placement.answer):
            raise ValueError(f"cell count does not match answer length for placement {placement.id}")

        for index, (r, c, char) in enumerate(placement.cells):
            if not (0 <= r < puzzle.height and 0 <= c < puzzle.width):
                raise ValueError(f"placement {placement.id} is out of bounds at {(r, c)}")
            if char != placement.answer[index]:
                raise ValueError(f"placement {placement.id} cell text does not match answer")
            expected = (placement.row, placement.col + index)
            if placement.direction == "down":
                expected = (placement.row + index, placement.col)
            if (r, c) != expected:
                raise ValueError(f"placement {placement.id} has non-contiguous cells")
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
    if puzzle.intersection_count != intersection_count:
        raise ValueError("puzzle intersection_count does not match placements")
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
        length_bonus = _crossword_length_bonus(len(answer))
        decorated.append((overlap * 5 + length_bonus - ascii_penalty + _source_weight_bonus(item[0], difficulty, 65.0) + rng.random(), item))
    decorated.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in decorated]


def _crossword_length_bonus(length: int) -> float:
    if length <= 1:
        return -14.0
    if length == 2:
        return -4.0
    if 3 <= length <= 6:
        return 15.0 - abs(length - 4.5) * 1.6
    return max(-5.0, 10.0 - (length - 6) * 1.9)


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
    base = 18 if max(width, height) <= 11 else 28
    return min(44, max(base, pool_size // 55))


def _randomized_pool(
    pool: List[Tuple[Any, str, str]],
    rng: random.Random,
    max_words: int,
    width: int,
    height: int,
    difficulty: Any,
) -> List[Tuple[Any, str, str]]:
    limit = min(len(pool), max(70, max_words * 8))
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
        length_bonus = _crossword_length_bonus(length) * 2.6
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


def _puzzle_score(puzzle: CrosswordPuzzle, max_words: int) -> float:
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
    target_density = _target_density(puzzle.width, puzzle.height)
    density_penalty = abs(density - target_density) * 760
    down_count = sum(1 for placement in puzzle.placements if placement.direction == "down")
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
        - puzzle.isolated_count * 92
        - density_penalty
        - down_penalty
    )


def _target_density(width: int, height: int) -> float:
    size = max(width, height)
    if size <= 8:
        return 0.36
    if size <= 11:
        return 0.33
    if size <= 15:
        return 0.30
    return 0.28


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
) -> List[_Candidate]:
    candidates: List[_Candidate] = []
    by_char: Dict[str, List[Cell]] = {}
    for cell, char in grid.items():
        by_char.setdefault(char, []).append(cell)

    for index, char in enumerate(answer):
        for r, c in by_char.get(char, []):
            for direction in ("across", "down"):
                row = r if direction == "across" else r - index
                col = c - index if direction == "across" else c
                candidate = _candidate(term, answer, initials, row, col, direction, grid, cell_dirs, width, height)
                if candidate and candidate.intersections > 0:
                    score = _candidate_score(candidate, grid, placements, width, height, rng)
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
) -> List[_Candidate]:
    candidates: List[_Candidate] = []
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
        candidate = _candidate(term, answer, initials, row, col, direction, grid, cell_dirs, width, height)
        if candidate and candidate.intersections == 0:
            score = _candidate_score(candidate, grid, placements, width, height, rng) - 65
            candidates.append(_Candidate(term, answer, initials, row, col, direction, candidate.cells, 0, score))
    return candidates


def _center_candidate(term: Any, answer: str, initials: str, width: int, height: int) -> Optional[_Candidate]:
    direction = "across" if len(answer) <= width else "down"
    if direction == "across":
        row = height // 2
        col = max(0, (width - len(answer)) // 2)
    else:
        row = max(0, (height - len(answer)) // 2)
        col = width // 2
    cells = _cells_for(answer, row, col, direction)
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
) -> Optional[_Candidate]:
    cells = _cells_for(answer, row, col, direction)
    intersections = 0
    occupied_cells = {(r, c) for r, c, _char in cells}
    if direction == "across":
        before = (row, col - 1)
        after = (row, col + len(answer))
    else:
        before = (row - 1, col)
        after = (row + len(answer), col)
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
        neighbors = ((r - 1, c), (r + 1, c)) if direction == "across" else ((r, c - 1), (r, c + 1))
        if any(neighbor in grid and neighbor not in occupied_cells for neighbor in neighbors):
            return None
    return _Candidate(term, answer, initials, row, col, direction, cells, intersections, 0)


def _cells_for(answer: str, row: int, col: int, direction: str) -> List[PlacedCell]:
    if direction == "across":
        return [(row, col + index, char) for index, char in enumerate(answer)]
    return [(row + index, col, char) for index, char in enumerate(answer)]


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
    down_count = sum(1 for placement in placements if placement.direction == "down")
    projected_down_ratio = (down_count + (1 if candidate.direction == "down" else 0)) / max(len(placements) + 1, 1)
    direction_adjust = 18 if candidate.direction == "across" else -24
    if projected_down_ratio > 0.35:
        direction_adjust -= (projected_down_ratio - 0.35) * 230
    if candidate.direction == "down" and candidate.intersections == 0:
        direction_adjust -= 48
    return (
        candidate.intersections * 92
        + len(candidate.answer) * 4
        + len(new_rows) * 35
        + len(new_cols) * 35
        + spread_area * 50
        + uncovered_bonus
        + direction_adjust
        - center_penalty * 2.5
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
