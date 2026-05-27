import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = FRONTEND_DIR.parent
LOG_FILE = PROJECT_DIR / "profile" / "launch.log"


def write_log(message):
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n")
    except Exception:
        pass


def main():
    os.chdir(FRONTEND_DIR)
    local_tcl = FRONTEND_DIR / "tcl"
    if local_tcl.exists():
        os.environ.setdefault("TCL_LIBRARY", str(local_tcl / "tcl8.6"))
        os.environ.setdefault("TK_LIBRARY", str(local_tcl / "tk8.6"))
    if str(FRONTEND_DIR) not in sys.path:
        sys.path.insert(0, str(FRONTEND_DIR))
    write_log(f"Launching with {sys.executable}")
    try:
        from bonus_guess import main as run_game

        run_game()
    except Exception:
        detail = traceback.format_exc()
        write_log("Launch failed:\n" + detail)
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动失败", f"游戏启动失败，详情已写入：\n{LOG_FILE}")
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
