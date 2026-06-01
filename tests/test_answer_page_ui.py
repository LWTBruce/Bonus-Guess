import time
import tkinter as tk
import unittest

from backend.app_modules.round_play import RoundPlayMixin
from frontend.ui.markdown_view import render_inline_markdown


class FakeHintButton:
    def __init__(self):
        self.disabled_texts = []
        self.enabled_texts = []

    def disable(self, text=None):
        self.disabled_texts.append(text)

    def enable(self, text=None):
        self.enabled_texts.append(text)


class CooldownHarness(RoundPlayMixin):
    def __init__(self):
        self.game_active = True
        self.hint_button = FakeHintButton()
        self.hint_cooldown_job = "old-job"
        self.hint_cooldown_until = time.perf_counter() + 59.8
        self.clue_visible_count = 0
        self.clue_lines = []
        self.cancelled_jobs = []
        self.scheduled = []

    def after_cancel(self, job):
        self.cancelled_jobs.append(job)

    def after(self, delay, callback):
        self.scheduled.append(delay)
        return "new-job"

    def can_take_hint(self):
        return True

    def is_clue_mode(self):
        return False


class SideTextHarness(tk.Tk, RoundPlayMixin):
    pass


class HintRenderHarness(tk.Tk, RoundPlayMixin):
    def hint_cooldown_seconds(self):
        return 45


class AnswerPageUiTests(unittest.TestCase):
    def test_hint_cooldown_refreshes_on_second_boundaries(self):
        harness = CooldownHarness()
        harness.update_hint_cooldown_button()

        self.assertEqual(harness.cancelled_jobs, ["old-job"])
        self.assertEqual(harness.hint_button.disabled_texts, ["60"])
        self.assertTrue(harness.scheduled)
        self.assertGreaterEqual(harness.scheduled[-1], 500)
        self.assertLessEqual(harness.scheduled[-1], 1000)

    def test_side_text_block_reflows_with_parent_width(self):
        try:
            root = SideTextHarness()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("520x260+20+20")
            frame = tk.Frame(root, bg="#111725", width=420, height=150)
            frame.pack()
            frame.pack_propagate(False)
            text = "同首字母的词库内答案都算对。普通、困难、噩梦可能使用掩码首字母；当前模式总词库里的匹配词会提示超纲。"
            widget = root.render_side_text_block(frame, text)
            root.update_idletasks()
            root.update()
            wide_height = int(widget.cget("height"))

            frame.configure(width=220)
            root.update_idletasks()
            root.update()
            narrow_height = int(widget.cget("height"))

            self.assertGreaterEqual(narrow_height, wide_height)
            self.assertGreaterEqual(widget.winfo_width(), 180)
        finally:
            root.destroy()

    def test_inline_hint_markdown_fills_available_width(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("520x180+20+20")
            frame = tk.Frame(root, bg="#182033", width=420, height=90)
            frame.pack()
            frame.pack_propagate(False)
            widget = render_inline_markdown(
                frame,
                "付费提示 1：第 2 个字是“动”    ＿动    -132 分",
                fg="#dce6ff",
                bg="#182033",
                base_size=12,
            )
            root.update_idletasks()
            root.update()

            self.assertEqual(str(widget.cget("width")), "1")
            self.assertGreaterEqual(widget.winfo_width(), 360)
            self.assertIn("提示", widget.get("1.0", "end-1c"))
        finally:
            root.destroy()

    def test_round_hint_box_renders_actual_hint_line(self):
        try:
            root = HintRenderHarness()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("620x220+20+20")
            root.hint_box = tk.Frame(root, bg="#182033", width=500, height=100)
            root.hint_box.pack()
            root.hint_box.pack_propagate(False)
            root.hint_lines = ["免费提示 1/1：第 2 个字是“动”    ＿动"]
            root.free_hint_quota = 1
            root._render_hints()
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect_text_widgets(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect_text_widgets(child)

            collect_text_widgets(root.hint_box)

            self.assertEqual(len(text_widgets), 1)
            hint_text = text_widgets[0].get("1.0", "end-1c")
            self.assertIn("免费提示", hint_text)
            self.assertIn("动", hint_text)
            self.assertGreaterEqual(text_widgets[0].winfo_width(), 420)
        finally:
            root.destroy()

    def test_live_answer_page_shows_character_hint_text(self):
        try:
            from backend.app_modules.application import BonusGuessApp

            app = BonusGuessApp()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            simple = "\u7b80\u5355"
            physics = "\u7269\u7406\u6a21\u5f0f"
            free = "\u81ea\u7531"
            common = "\u666e\u901a"
            app.geometry("1274x806+20+20")
            app.update_idletasks()
            app.update()
            app.mode = physics
            app.play_mode = free
            app.selected_subject = physics
            app.selected_game_group = common
            app.selected_rule_mode = free
            app.selected_play_mode = free
            app.difficulty = simple
            app.load_terms_for_current_selection(simple)
            app.terms = [next(term for term in app.terms if len(term.chinese) >= 2)]
            app.start_round(transition=False)
            app.update_idletasks()
            app.update()

            app.show_hint()
            app.update_idletasks()
            app.update()

            hint_text = app.hint_text_widget.get("1.0", "end-1c")
            self.assertTrue(app.hint_lines)
            self.assertIn("\u63d0\u793a", hint_text)
            self.assertIn(app.hint_lines[-1], hint_text)
            self.assertGreaterEqual(app.hint_box.winfo_height(), 110)
            self.assertIsNotNone(app.hint_scrollbar)
            self.assertTrue(app.hint_scrollbar.winfo_ismapped())
            self.assertGreater(app.hint_box.winfo_y(), app.answer_entry_frame.winfo_y())
            self.assertLess(
                app.hint_box.winfo_y() + app.hint_box.winfo_height(),
                app.tutorial_question_panel.winfo_height(),
            )
        finally:
            app.game_active = False
            app.clear(transition=False)
            app.destroy()


if __name__ == "__main__":
    unittest.main()
