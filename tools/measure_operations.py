from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.runtime.accounts import active_account, apply_account_context  # noqa: E402
from backend.runtime.clue_library import ClueLibrary  # noqa: E402
from backend.runtime.crossword_puzzle import generate_crossword  # noqa: E402
from backend.runtime.game_config import TERM_CLUES_DIR, WORDS_DIR  # noqa: E402
from backend.runtime.rank_system import read_rank_progress  # noqa: E402
from backend.runtime.records import (  # noqa: E402
    clear_record_caches,
    load_record_entries,
    load_record_summary,
    read_achievements,
)
from backend.runtime.term_library import TermLibrary  # noqa: E402


def time_call(func):
    started = time.perf_counter()
    result = func()
    return (time.perf_counter() - started) * 1000.0, result


def measure(label, func, runs):
    samples = []
    last_result = None
    for _index in range(max(1, runs)):
        elapsed_ms, last_result = time_call(func)
        samples.append(elapsed_ms)
    return {
        "label": label,
        "runs": len(samples),
        "min": min(samples),
        "median": statistics.median(samples),
        "max": max(samples),
        "result": describe_result(last_result),
    }


def describe_result(result):
    if isinstance(result, tuple):
        return " / ".join(describe_result(item) for item in result)
    if isinstance(result, list):
        return f"{len(result)} items"
    if isinstance(result, dict):
        if "total_count" in result and "rating" in result:
            return f"{result['total_count']} records, rating {result['rating']:.3f}"
        completed = result.get("completed")
        if isinstance(completed, dict):
            return f"{len(completed)} completed"
        return f"{len(result)} keys"
    if hasattr(result, "placements"):
        return f"{len(result.placements)} words"
    return str(result)


def print_table(rows):
    print("Operation".ljust(32), "runs".rjust(4), "min".rjust(9), "median".rjust(9), "max".rjust(9), "result")
    print("-" * 92)
    for row in rows:
        print(
            row["label"].ljust(32),
            str(row["runs"]).rjust(4),
            f"{row['min']:.2f}ms".rjust(9),
            f"{row['median']:.2f}ms".rjust(9),
            f"{row['max']:.2f}ms".rjust(9),
            row["result"],
        )


def main():
    parser = argparse.ArgumentParser(description="Measure Bonus Guess data-operation timings.")
    parser.add_argument("--runs", type=int, default=5, help="runs per warm operation")
    parser.add_argument("--include-crossword", action="store_true", help="also measure one small crossword generation")
    args = parser.parse_args()

    account = active_account()
    if account:
        apply_account_context(account["id"])

    library = TermLibrary(WORDS_DIR)
    clue_library = ClueLibrary(TERM_CLUES_DIR)

    def cold_records():
        clear_record_caches()
        return load_record_entries()

    def cold_summary():
        clear_record_caches()
        return load_record_summary()

    operations = [
        ("records cold load", cold_records, 1),
        ("records warm load", load_record_entries, args.runs),
        ("summary cold build", cold_summary, 1),
        ("summary warm read", load_record_summary, args.runs),
        ("achievements read", read_achievements, args.runs),
        ("rank progress read", read_rank_progress, args.runs),
        ("physics normal terms", lambda: library.load("物理模式", "普通"), 1),
        ("math normal terms", lambda: library.load("数学模式", "普通"), 1),
        ("initials cache warmup", library.warm_initials_cache, 1),
        ("clue library load", clue_library.load, 1),
    ]
    if args.include_crossword:
        terms, _files = library.load("物理模式", "入门")
        operations.append(("crossword generation", lambda: generate_crossword(terms, "入门", max_words=5, size=(8, 8)), 1))

    rows = [measure(label, func, runs) for label, func, runs in operations]
    print_table(rows)


if __name__ == "__main__":
    main()
