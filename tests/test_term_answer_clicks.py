import tkinter as tk
from tkinter import font as tkfont
import unittest

from backend.app_modules.round_play import RoundPlayMixin
from frontend.ui.markdown_view import render_markdown


class ClickableAnswerHarness(tk.Tk, RoundPlayMixin):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry("520x180+20+20")
        self.opened_terms = []

    def term_explanation_for_answer(self, answer, terms=None):
        return f"{answer} 的解释"

    def show_term_explanation_dialog(self, answer, explanation=None, sources=None):
        self.opened_terms.append((answer, explanation))


class TermAnswerClickTests(unittest.TestCase):
    def test_clickable_answer_text_has_real_tag_range_and_opens_dialog(self):
        try:
            root = ClickableAnswerHarness()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            box = root.render_clickable_answers(root, ["变压器"], height=3)
            box.pack(fill="x")
            root.update_idletasks()
            root.update()

            ranges = box.tag_ranges("term_1")
            self.assertEqual(str(ranges[0]), "1.0")
            self.assertEqual(str(ranges[1]), "1.3")

            bbox = box.bbox("1.1")
            if bbox is None:
                self.skipTest("Tk did not lay out the Text widget")
            x, y, _width, _height = bbox
            box.event_generate("<Button-1>", x=x + 1, y=y + 1)
            root.update()

            self.assertEqual(root.opened_terms, [("变压器", "变压器 的解释")])
        finally:
            root.destroy()

    def test_term_markdown_renders_styled_reading_text(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("640x320+20+20")
            inner = render_markdown(root, "散射振幅可写成 $\\psi\\sim e^{ikz}+f(\\theta)e^{ikr}/r$，这是 **远区** 关系。", mode="detail")
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            paragraph = text_widgets[0]
            self.assertGreaterEqual(int(paragraph.cget("height")), 1)
            self.assertTrue(paragraph.tag_ranges("math"))
            self.assertTrue(paragraph.tag_ranges("bold"))
            self.assertGreaterEqual(tkfont.Font(font=paragraph.cget("font")).cget("size"), 13)
            rendered = paragraph.get("1.0", "end-1c")
            self.assertIn("ψ∼eⁱᵏᶻ+f(θ)eⁱᵏʳ/r", rendered)
            self.assertNotIn("\\", rendered)
            self.assertNotIn("{", rendered)
            self.assertNotIn("}", rendered)
        finally:
            root.destroy()

    def test_term_markdown_renders_loose_latex_commands(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("640x320+20+20")
            inner = render_markdown(
                root,
                "常见条件写成 \\varepsilon>0，背景测度记作 \\mu；也可写为 \\(\\frac{\\mu_0}{4\\pi}\\)。",
                mode="detail",
            )
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            rendered = text_widgets[0].get("1.0", "end-1c")
            self.assertIn("ε>0", rendered)
            self.assertIn("μ", rendered)
            self.assertIn("μ₀∕4π", rendered)
            self.assertNotIn("\\", rendered)
            self.assertNotIn("{", rendered)
            self.assertNotIn("}", rendered)
        finally:
            root.destroy()

    def test_term_markdown_renders_loose_greek_subscripts(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("640x320+20+20")
            inner = render_markdown(
                root,
                "吉布斯相律常用 $G=H-TS$ 连接自由能；平衡时 μ_α=μ_β，而普通变量名 APP_VERSION 不应被改写。",
                mode="detail",
            )
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            rendered = text_widgets[0].get("1.0", "end-1c")
            self.assertIn("μₐ=μᵦ", rendered)
            self.assertNotIn("μ_α", rendered)
            self.assertIn("APP_VERSION", rendered)
        finally:
            root.destroy()

    def test_term_markdown_renders_ampere_law_formula_without_black_math_block(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("900x420+20+20")
            inner = render_markdown(
                root,
                "安培定律常写为 $\\oint\\mathbf B\\cdot d\\boldsymbol\\ell=\\mu_0 I_{\\rm in}$，"
                "其中 $\\mu_0$ 是真空磁导率。Legendre 方程里也常见 $y\\prime\\prime+\\ell y=0$。",
                mode="detail",
            )
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            paragraph = text_widgets[0]
            rendered = paragraph.get("1.0", "end-1c")
            self.assertIn("∮B·dℓ=μ₀ Iᵢₙ", rendered)
            self.assertIn("y′′+ℓ y=0", rendered)
            self.assertNotIn("oint", rendered)
            self.assertNotIn("boldsymbol", rendered)
            self.assertNotIn("prime", rendered)
            self.assertEqual(paragraph.tag_cget("math", "background"), paragraph.cget("background"))
            self.assertEqual(paragraph.tag_cget("math", "foreground"), paragraph.cget("foreground"))
            self.assertTrue(paragraph.tag_ranges("math_sub"))
            body_font = tkfont.Font(font=paragraph.cget("font"))
            math_font = tkfont.Font(font=paragraph.tag_cget("math", "font"))
            self.assertEqual(math_font.cget("family"), body_font.cget("family"))
            self.assertEqual(math_font.cget("size"), body_font.cget("size"))
            self.assertLessEqual(int(paragraph.cget("spacing2")), 1)
        finally:
            root.destroy()

    def test_term_markdown_formula_line_keeps_normal_paragraph_height(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("760x320+20+20")
            inner = render_markdown(
                root,
                "负电荷是电荷符号约定中取负号的一类源，电子是最常见的负电荷载体。"
                "量子化关系可写成 $q=-ne$，其中 $q$ 是负电荷量，$n$ 是正整数，$e$ 是元电荷大小。",
                mode="detail",
            )
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            paragraph = text_widgets[0]
            display_lines = paragraph.count("1.0", "end-1c", "displaylines")[0]
            self.assertLessEqual(int(paragraph.cget("height")), display_lines + 1)
            self.assertLessEqual(int(paragraph.cget("spacing2")), 1)
            self.assertIn("q=-ne", paragraph.get("1.0", "end-1c"))
        finally:
            root.destroy()

    def test_term_markdown_long_formula_wraps_at_boundary(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("360x260+20+20")
            inner = render_markdown(
                root,
                "长公式 $ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ$ 应该在边界处回行。",
                mode="detail",
            )
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            paragraph = text_widgets[0]
            display_lines = paragraph.count("1.0", "end-1c", "displaylines")[0]
            self.assertEqual(paragraph.cget("wrap"), "char")
            self.assertGreater(display_lines, 1)
            self.assertEqual(paragraph.tag_cget("math", "background"), paragraph.cget("background"))
        finally:
            root.destroy()

    def test_markdown_copy_restores_original_latex(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("760x260+20+20")
            source = "正则系综中 $F=-k_BT\\ln Z$，这是 **自由能** 的写法。"
            inner = render_markdown(root, source, mode="detail")
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertTrue(text_widgets)
            paragraph = text_widgets[0]
            paragraph.tag_add("sel", "1.0", "end-1c")
            paragraph.event_generate("<<Copy>>")
            root.update()
            self.assertEqual(root.clipboard_get(), source)
            rendered = paragraph.get("1.0", "end-1c")
            self.assertIn("F=-kᵦT ln Z", rendered)
            self.assertNotIn("$", rendered)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
