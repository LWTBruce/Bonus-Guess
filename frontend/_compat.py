from __future__ import annotations

import importlib
import sys
from pathlib import Path


def ensure_project_root():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def alias_module(current_name, target_name):
    ensure_project_root()
    module = importlib.import_module(target_name)
    caller_globals = sys._getframe(1).f_globals
    caller_globals.update(module.__dict__)
    sys.modules[current_name] = module
    return module
