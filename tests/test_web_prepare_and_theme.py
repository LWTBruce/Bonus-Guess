import inspect
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frontend"))

from backend.runtime.deploy_config import load_runtime_config  # noqa: E402
from backend.app_modules.navigation_home import NavigationHomeMixin  # noqa: E402
from backend.runtime.game_config import GAME_MECHANICS_FILE  # noqa: E402
from frontend.ui.backdrop import BackdropMixin  # noqa: E402
from frontend.ui.markdown_view import render_markdown, split_mechanics_sections  # noqa: E402
import rank_system  # noqa: E402


def _relative_luminance(color):
    value = str(color).lstrip("#")
    red, green, blue = (int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))

    def linear(channel):
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue)


def _contrast_ratio(foreground, background):
    fg_luminance = _relative_luminance(foreground)
    bg_luminance = _relative_luminance(background)
    lighter = max(fg_luminance, bg_luminance)
    darker = min(fg_luminance, bg_luminance)
    return (lighter + 0.05) / (darker + 0.05)


class DeployConfigTests(unittest.TestCase):
    def test_runtime_config_defaults_to_local_paths(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_runtime_config(Path("resources"), Path("data"))
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8765)
        self.assertFalse(config.enable_online)
        self.assertEqual(config.resource_dir, Path("resources").resolve())
        self.assertEqual(config.data_dir, Path("data").resolve())

    def test_runtime_config_env_overrides_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "web_runtime.json"
            config_path.write_text(
                '{"host":"0.0.0.0","port":9000,"resource_dir":"file_resources","data_dir":"file_data","enable_online":true}',
                encoding="utf-8",
            )
            env = {
                "BONUS_GUESS_WEB_CONFIG": str(config_path),
                "BONUS_GUESS_PORT": "7777",
                "BONUS_GUESS_DATA_DIR": "env_data",
                "BONUS_GUESS_ENABLE_ONLINE": "false",
            }
            with patch.dict(os.environ, env, clear=True):
                config = load_runtime_config(Path("resources"), Path("data"))
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 7777)
        self.assertEqual(config.resource_dir, Path("file_resources").resolve())
        self.assertEqual(config.data_dir, Path("env_data").resolve())
        self.assertFalse(config.enable_online)

    def test_requirements_include_runtime_pinyin_dependency(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        normalized = {line.strip().lower() for line in requirements if line.strip()}
        self.assertIn("pyinstaller", normalized)
        self.assertIn("pypinyin", normalized)


class RecordingCanvas:
    def __init__(self, bg="#FFA8CF"):
        self.bg = bg
        self.calls = []

    def delete(self, *_args):
        self.calls.append(("delete", {}, _args))

    def cget(self, option):
        if option == "bg":
            return self.bg
        raise KeyError(option)

    def create_rectangle(self, *args, **kwargs):
        self.calls.append(("rectangle", kwargs, args))

    def create_polygon(self, *args, **kwargs):
        self.calls.append(("polygon", kwargs, args))

    def create_text(self, *args, **kwargs):
        self.calls.append(("text", kwargs, args))

    def create_line(self, *args, **kwargs):
        self.calls.append(("line", kwargs, args))

    def create_oval(self, *args, **kwargs):
        self.calls.append(("oval", kwargs, args))

    def move(self, *args, **kwargs):
        self.calls.append(("move", kwargs, args))


class ThemeRenderingTests(unittest.TestCase):
    def test_transparent_rank_badge_avoids_legacy_black_fills(self):
        canvas = RecordingCanvas()
        badge_id = rank_system.rank_badge_id("物理模式", 7, "free")
        rank_system.draw_rank_badge(canvas, badge_id, 220, 34, selected=True, transparent=True, background="#FFA8CF")
        legacy_fills = {"#050507", "#111725", "#182033", "#020617", "#0b1020"}
        fills = {
            kwargs.get("fill")
            for name, kwargs, _args in canvas.calls
            if name in {"rectangle", "polygon"} and "fill" in kwargs
        }
        self.assertFalse(legacy_fills & fills)

    def test_title_animation_uses_smooth_timer(self):
        source = inspect.getsource(NavigationHomeMixin.draw_home_title)
        self.assertIn("time.perf_counter", source)
        self.assertIn("canvas.after(16, draw_frame)", source)
        self.assertNotIn("canvas.after(58, draw_frame)", source)
        self.assertNotIn("title_scale", source)
        self.assertNotIn("round(title_size", source)
        self.assertNotIn("growth_fonts", source)
        self.assertNotIn("math.floor(growth", source)

    def test_non_blue_theme_text_roles_have_readable_contrast(self):
        roles = {
            "title": 4.5,
            "text": 4.5,
            "muted": 4.5,
            "subtle": 3.0,
            "accent": 4.5,
            "success": 4.5,
            "warning": 4.5,
            "danger": 4.5,
            "special": 4.5,
            "button_disabled_fg": 3.0,
            "code_fg": 4.5,
            "link_fg": 4.5,
            "select_fg": 4.5,
        }
        surfaces = ("base", "panel", "button_bg", "entry_bg", "code_bg", "select_bg")
        for theme_id, theme in BackdropMixin.BACKDROP_THEMES.items():
            if theme_id == "blue":
                continue
            for surface in surfaces:
                for role, minimum in roles.items():
                    with self.subTest(theme=theme_id, surface=surface, role=role):
                        ratio = _contrast_ratio(theme[role], theme[surface])
                        self.assertGreaterEqual(ratio, minimum)

    def test_green_doodle_flowers_fall_and_rotate_from_stable_specs(self):
        specs_a = BackdropMixin._green_flower_specs(6)
        specs_b = BackdropMixin._green_flower_specs(6)
        self.assertEqual(specs_a, specs_b)
        first = specs_a[0]
        self.assertIn("base_angle", first)
        self.assertIn("spin_speed", first)
        self.assertNotEqual(first["base_angle"], 0)

        x0, y0, angle0 = BackdropMixin._green_flower_position(first, 1200, 760, 0)
        x1, y1, angle1 = BackdropMixin._green_flower_position(first, 1200, 760, 4)
        self.assertNotEqual(round(x0, 4), round(x1, 4))
        self.assertNotEqual(round(y0, 4), round(y1, 4))
        self.assertNotEqual(round(angle0, 4), round(angle1, 4))

    def test_red_heart_ribbons_rise_from_stable_specs(self):
        specs_a = BackdropMixin._red_float_specs(9)
        specs_b = BackdropMixin._red_float_specs(9)
        self.assertEqual(specs_a, specs_b)
        self.assertIn("heart", {spec["kind"] for spec in specs_a})
        self.assertIn("ribbon", {spec["kind"] for spec in specs_a})
        self.assertGreater(len({spec["color"] for spec in specs_a if spec["kind"] == "heart"}), 1)
        self.assertTrue(all(len(spec["colors"]) > 1 for spec in specs_a if spec["kind"] == "ribbon"))
        heart_specs = [spec for spec in specs_a if spec["kind"] == "heart"]
        self.assertNotEqual([spec["base_x"] for spec in heart_specs], sorted(spec["base_x"] for spec in heart_specs))
        self.assertNotEqual([spec["base_y"] for spec in heart_specs], sorted(spec["base_y"] for spec in heart_specs))
        ribbon_specs = [spec for spec in specs_a if spec["kind"] == "ribbon"]
        self.assertTrue(any(spec["base_angle"] > math.pi for spec in ribbon_specs))
        self.assertTrue(any(spec["coiled"] for spec in ribbon_specs))
        first = specs_a[0]

        x0, y0, angle0 = BackdropMixin._red_float_position(first, 1200, 760, 0)
        x1, y1, angle1 = BackdropMixin._red_float_position(first, 1200, 760, 1)
        self.assertNotEqual(round(x0, 4), round(x1, 4))
        self.assertLess(y1, y0)
        self.assertNotEqual(round(angle0, 4), round(angle1, 4))
        positions = [BackdropMixin._red_float_position(spec, 1200, 760, 0) for spec in specs_a]
        self.assertGreater(max(x for x, _y, _angle in positions) - min(x for x, _y, _angle in positions), 700)
        self.assertGreater(max(y for _x, y, _angle in positions) - min(y for _x, y, _angle in positions), 500)

        source = inspect.getsource(BackdropMixin._draw_red_heart_ribbons)
        self.assertIn("9 * 0.75", source)

    def test_red_ribbon_centerlines_can_be_long_or_coiled(self):
        length = 10 * 44.0
        regular = BackdropMixin._ribbon_centerline_points(10, length, 42, 0.7, False)
        regular_y_span = max(y for _x, y in regular) - min(y for _x, y in regular)
        self.assertGreater(regular_y_span, 400)

        coiled = BackdropMixin._ribbon_centerline_points(10, length, 42, 0.7, True, 1.1, 4.5, 0.2)
        loop = coiled[10:25]
        loop_x_span = max(x for x, _y in loop) - min(x for x, _y in loop)
        loop_y_span = max(y for _x, y in loop) - min(y for _x, y in loop)
        loop_average_y = sum(y for _x, y in loop) / len(loop)
        lead_y_span = coiled[10][1] - coiled[0][1]
        tail_y_span = coiled[-1][1] - coiled[24][1]
        self.assertGreater(loop_x_span, 60)
        self.assertLess(loop_y_span, 130)
        self.assertLess(abs(loop_average_y), 35)
        self.assertGreater(lead_y_span, 180)
        self.assertGreater(tail_y_span, 180)

    def test_markdown_scroll_canvas_is_theme_surface(self):
        try:
            import tkinter as tk
        except Exception as exc:
            self.skipTest(f"Tk import unavailable: {exc}")
            return

        class Harness(BackdropMixin, tk.Tk):
            def __init__(self):
                tk.Tk.__init__(self)
                self.player_settings = {"backdrop_theme": "pink"}

        try:
            root = Harness()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            inner = render_markdown(root, "正文\n\n```text\ncode\n```", mode="detail")
            root.apply_static_theme(root)
            root.update_idletasks()
            canvases = []

            def collect(widget):
                if isinstance(widget, tk.Canvas):
                    canvases.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(root)
            self.assertTrue(canvases)
            self.assertTrue(all(getattr(canvas, "_theme_surface", False) for canvas in canvases))
            self.assertNotIn("#182033", {canvas.cget("bg").lower() for canvas in canvases})
            self.assertTrue(getattr(inner, "_theme_surface", False))
        finally:
            root.destroy()

    def test_game_mechanics_markdown_wraps_at_multiple_window_widths(self):
        try:
            import tkinter as tk
        except Exception as exc:
            self.skipTest(f"Tk import unavailable: {exc}")
            return

        class Harness(BackdropMixin, tk.Tk):
            def __init__(self):
                tk.Tk.__init__(self)
                self.player_settings = {"backdrop_theme": "red"}

        _quick, detail = split_mechanics_sections(GAME_MECHANICS_FILE.read_text(encoding="utf-8"))
        for width in (420, 760, 1274, 1600):
            with self.subTest(width=width):
                try:
                    root = Harness()
                except tk.TclError as exc:
                    self.skipTest(f"Tk is unavailable: {exc}")
                    return
                try:
                    root.geometry(f"{width}x560+20+20")
                    frame = tk.Frame(root, bg=root.theme_color("base"), width=max(260, width - 40), height=520)
                    frame.pack(fill="both", expand=True)
                    inner = render_markdown(frame, detail, mode="detail")
                    root.apply_static_theme(root)
                    for _ in range(4):
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
                    canvas = inner._scroll_canvas
                    scrollregion = [int(float(value)) for value in canvas.cget("scrollregion").split()]
                    self.assertLessEqual(scrollregion[2] - scrollregion[0], canvas.winfo_width() + 1)

                    target = next(widget for widget in text_widgets if "选定物理或数学" in widget.get("1.0", "end-1c"))
                    self.assertEqual(target.cget("wrap"), "char")
                    end_bbox = target.bbox("end-2c")
                    self.assertIsNotNone(end_bbox)
                    self.assertLessEqual(end_bbox[0] + end_bbox[2], target.winfo_width())
                    if width <= 760:
                        self.assertGreater(int(target.cget("height")), 1)

                    tagged = next(widget for widget in text_widgets if "题目总难度" in widget.get("1.0", "end-1c"))
                    for tag in ("code", "math", "math_sup", "math_sub"):
                        if tagged.tag_ranges(tag):
                            self.assertEqual(tagged.tag_cget(tag, "background"), tagged.cget("background"))
                finally:
                    root.destroy()

    def test_game_mechanics_incremental_rendering_defers_later_blocks(self):
        try:
            import tkinter as tk
        except Exception as exc:
            self.skipTest(f"Tk import unavailable: {exc}")
            return

        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk is unavailable: {exc}")
            return
        try:
            root.geometry("760x560+20+20")
            _quick, detail = split_mechanics_sections(GAME_MECHANICS_FILE.read_text(encoding="utf-8"))
            inner = render_markdown(root, detail, mode="detail", incremental=True, first_batch=4, batch_size=5, batch_delay=1000)
            root.update_idletasks()
            root.update()
            text_widgets = []

            def collect(widget):
                if isinstance(widget, tk.Text):
                    text_widgets.append(widget)
                for child in widget.winfo_children():
                    collect(child)

            collect(inner)
            self.assertLess(len(text_widgets), 10)
            self.assertNotIn("选定物理或数学", "\n".join(widget.get("1.0", "end-1c") for widget in text_widgets))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
