import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.runtime.crossword_puzzle import (  # noqa: E402
    CrosswordPlacement,
    CrosswordPuzzle,
    _cells_for,
    _detached_limit,
    _directions_for_shape,
    _detached_placement_count,
    _next_cell,
    _side_neighbors,
    _start_for_cell_at_index,
    generate_crossword,
    size_for_difficulty,
    target_word_count_for_size,
    validate_crossword,
)
from backend.runtime.term_library import TermLibrary  # noqa: E402


def _term(answer, initials="ABCD"):
    return SimpleNamespace(
        chinese=answer,
        initials=initials[:len(answer)],
        difficulty=5,
        source="geometry_terms.csv",
        source_label="几何测试",
    )


def _single_word_puzzle(shape, direction, start, answer="甲乙丙丁"):
    row, col = start
    cells = _cells_for(answer, row, col, direction, shape)
    grid = {(r, c): char for r, c, char in cells}
    rows = [[grid.get((r, c)) for c in range(7)] for r in range(7)]
    placement = CrosswordPlacement(
        id=1,
        term=_term(answer),
        answer=answer,
        initials="ABCD",
        display_initials=None,
        row=row,
        col=col,
        direction=direction,
        cells=cells,
        intersections=0,
        source_label="几何测试",
    )
    return CrosswordPuzzle(7, 7, [placement], grid, rows, 0, 0, shape)


class CrosswordGeometryTests(unittest.TestCase):
    def test_triangle_and_hex_steps_are_reversible(self):
        for shape in ("triangle", "hex"):
            for direction in _directions_for_shape(shape):
                for row in range(1, 5):
                    for col in range(1, 5):
                        following = _next_cell(row, col, direction, shape)
                        self.assertEqual((row, col), _start_for_cell_at_index(following[0], following[1], 1, direction, shape))

    def test_triangle_directions_are_straight_edge_paths(self):
        starts = {
            "tri_horizontal": (2, 0),
            "tri_down": (0, 0),
            "tri_up": (3, 0),
        }
        signatures = set()
        for direction in _directions_for_shape("triangle"):
            puzzle = _single_word_puzzle("triangle", direction, starts[direction])
            validate_crossword(puzzle)
            cells = [(r, c) for r, c, _char in puzzle.placements[0].cells]
            signatures.add(tuple((r - cells[0][0], c - cells[0][1]) for r, c in cells))
            for index, cell in enumerate(cells):
                self.assertEqual(starts[direction], _start_for_cell_at_index(cell[0], cell[1], index, direction, "triangle"))
            for current, following in zip(cells, cells[1:]):
                self.assertEqual(following, _next_cell(current[0], current[1], direction, "triangle"))
                self.assertIn(following, _side_neighbors(current[0], current[1], "triangle"))
        self.assertEqual(len(signatures), 3)

    def test_hex_directions_are_straight_edge_paths(self):
        starts = {
            "hex_vertical": (0, 2),
            "hex_down": (0, 0),
            "hex_up": (3, 0),
        }
        signatures = set()
        for direction in _directions_for_shape("hex"):
            puzzle = _single_word_puzzle("hex", direction, starts[direction])
            validate_crossword(puzzle)
            cells = [(r, c) for r, c, _char in puzzle.placements[0].cells]
            signatures.add(tuple((r - cells[0][0], c - cells[0][1]) for r, c in cells))
            for index, cell in enumerate(cells):
                self.assertEqual(starts[direction], _start_for_cell_at_index(cell[0], cell[1], index, direction, "hex"))
            for current, following in zip(cells, cells[1:]):
                self.assertEqual(following, _next_cell(current[0], current[1], direction, "hex"))
                self.assertIn(following, _side_neighbors(current[0], current[1], "hex"))
        self.assertEqual(len(signatures), 3)

    def test_generated_triangle_and_hex_puzzles_validate_geometry(self):
        words = ["甲乙丙丁", "丙戊己庚", "乙辛壬癸", "丁子丑寅", "庚卯辰巳", "壬午未申", "寅酉戌亥"]
        terms = [_term(word) for word in words]
        for shape in ("triangle", "hex"):
            puzzle = generate_crossword(terms, "普通", rng=random.Random(4), max_words=5, size=(8, 8), cell_shape=shape)
            self.assertTrue(puzzle.placements)
            validate_crossword(puzzle)
            self.assertLessEqual({placement.direction for placement in puzzle.placements}, set(_directions_for_shape(shape)))
            for placement in puzzle.placements:
                cells = [(r, c) for r, c, _char in placement.cells]
                for current, following in zip(cells, cells[1:]):
                    self.assertEqual(following, _next_cell(current[0], current[1], placement.direction, shape))
                    self.assertIn(following, _side_neighbors(current[0], current[1], shape))

    def test_isolated_count_uses_disconnected_components_not_zero_crossings(self):
        placements = [
            CrosswordPlacement(1, _term("甲乙丙"), "甲乙丙", "ABC", None, 1, 0, "across", _cells_for("甲乙丙", 1, 0, "across"), 1, "几何测试"),
            CrosswordPlacement(2, _term("丁乙戊"), "丁乙戊", "DEF", None, 0, 1, "down", _cells_for("丁乙戊", 0, 1, "down"), 1, "几何测试"),
            CrosswordPlacement(3, _term("己庚辛"), "己庚辛", "GHI", None, 5, 4, "across", _cells_for("己庚辛", 5, 4, "across"), 1, "几何测试"),
            CrosswordPlacement(4, _term("壬庚癸"), "壬庚癸", "JKL", None, 4, 5, "down", _cells_for("壬庚癸", 4, 5, "down"), 1, "几何测试"),
        ]
        grid = {}
        for placement in placements:
            for row, col, char in placement.cells:
                grid[(row, col)] = char
        rows = [[grid.get((row, col)) for col in range(8)] for row in range(8)]
        puzzle = CrosswordPuzzle(8, 8, placements, grid, rows, 4, 2, "square")
        self.assertEqual(_detached_placement_count(placements), 2)
        self.assertTrue(validate_crossword(puzzle))

        stale_report = CrosswordPuzzle(8, 8, placements, grid, rows, 4, 0, "square")
        with self.assertRaisesRegex(ValueError, "isolated_count"):
            validate_crossword(stale_report)

    def test_isolated_count_counts_words_outside_largest_component(self):
        placements = [
            CrosswordPlacement(1, _term("甲乙丙"), "甲乙丙", "ABC", None, 1, 0, "across", _cells_for("甲乙丙", 1, 0, "across"), 1, "几何测试"),
            CrosswordPlacement(2, _term("丁乙戊"), "丁乙戊", "DEF", None, 0, 1, "down", _cells_for("丁乙戊", 0, 1, "down"), 1, "几何测试"),
            CrosswordPlacement(3, _term("己庚辛"), "己庚辛", "GHI", None, 5, 0, "across", _cells_for("己庚辛", 5, 0, "across"), 0, "几何测试"),
            CrosswordPlacement(4, _term("壬癸子"), "壬癸子", "JKL", None, 6, 4, "across", _cells_for("壬癸子", 6, 4, "across"), 0, "几何测试"),
        ]
        grid = {}
        for placement in placements:
            for row, col, char in placement.cells:
                grid[(row, col)] = char
        rows = [[grid.get((row, col)) for col in range(8)] for row in range(8)]
        puzzle = CrosswordPuzzle(8, 8, placements, grid, rows, 2, 2, "square")
        self.assertEqual(_detached_placement_count(placements), 2)
        self.assertTrue(validate_crossword(puzzle))

    def test_generated_crosswords_keep_detached_words_under_twenty_percent(self):
        words = [
            "甲乙丙丁", "丙戊己庚", "丁辛壬癸", "乙子丑寅", "庚卯辰巳",
            "壬午未申", "寅酉戌亥", "甲申辰午", "戊辛酉子", "丑卯未亥",
            "己壬寅巳", "癸丙庚申", "子辰戊壬", "卯丁己辛", "未甲癸酉",
            "辰庚子申", "辛丑午酉", "乙己壬卯", "丙癸未戌", "丁庚亥寅",
        ]
        terms = [_term(word) for word in words]
        for shape in ("square", "triangle", "hex"):
            for seed in range(2):
                with self.subTest(shape=shape, seed=seed):
                    puzzle = generate_crossword(terms, "普通", rng=random.Random(seed), max_words=10, size=(12, 12), cell_shape=shape)
                    validate_crossword(puzzle)
                    self.assertLessEqual(puzzle.isolated_count, _detached_limit(len(puzzle.placements)))

    def test_real_crossword_generation_limits_detached_words(self):
        library = TermLibrary(ROOT / "words")
        terms, _files = library.load("物理模式", "普通")
        size = size_for_difficulty("普通")
        max_words = target_word_count_for_size(size, difficulty="普通")
        puzzle = generate_crossword(terms, "普通", rng=random.Random(0), max_words=max_words, size=size, cell_shape="square")

        self.assertTrue(validate_crossword(puzzle))
        self.assertLessEqual(puzzle.isolated_count, _detached_limit(len(puzzle.placements)))
