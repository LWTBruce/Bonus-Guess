from __future__ import annotations

import importlib
import sys
from pathlib import Path


def alias_tool(current_name, target_name):
    root = Path(__file__).resolve().parents[1]
    tool_dir = root / "tools" / "word_pipeline"
    for path in (root, tool_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    module = importlib.import_module(target_name)
    sys._getframe(1).f_globals.update(module.__dict__)
    sys.modules[current_name] = module
    return module
