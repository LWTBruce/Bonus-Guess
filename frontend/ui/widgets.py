import math
import tkinter as tk


UI_SCALE = 1.0


def set_ui_scale(scale):
    global UI_SCALE
    try:
        value = float(scale)
    except (TypeError, ValueError):
        value = 1.0
    UI_SCALE = max(0.8, min(2.0, value))


def scaled_int(value):
    return max(1, int(round(value * UI_SCALE)))


class HoverButton(tk.Frame):
    def __init__(self, parent, text, command, width=260, height=76, accent="#f6d36b"):
        super().__init__(parent, bg=parent["bg"])
        self.command = command
        self.text = text
        self.accent = accent
        self.enabled = True
        self.normal_bg = "#20283a"
        self.hover_bg = "#344262"
        self.normal_fg = "#f5f0df"
        self.hover_fg = "#fff6b0"
        self.target = 0.0
        self.value = 0.0
        self.animation_job = None
        self.base_width = width
        self.base_height = height
        self.width = scaled_int(width)
        self.height = scaled_int(height)
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bd=0,
            highlightthickness=0,
            bg=parent["bg"],
            cursor="hand2",
        )
        self.canvas.pack()
        self.canvas.bind("<Enter>", self._enter)
        self.canvas.bind("<Leave>", self._leave)
        self.canvas.bind("<Button-1>", self._click)
        self._draw()

    def _click(self, _event):
        if self.enabled:
            self.command()

    def disable(self, text=None):
        next_text = self.text if text is None else text
        if not self.enabled and self.text == next_text and self.target == 0.0:
            return
        self.enabled = False
        self.text = next_text
        self.target = 0.0
        self._cancel_animation()
        self.canvas.config(cursor="arrow")
        self._draw()

    def enable(self, text=None):
        next_text = self.text if text is None else text
        if self.enabled and self.text == next_text:
            return
        self.enabled = True
        self.text = next_text
        self.canvas.config(cursor="hand2")
        self._draw()

    def _enter(self, _event):
        if not self.enabled:
            return
        self.target = 1.0
        self._ensure_animation()

    def _leave(self, _event):
        if not self.enabled:
            return
        self.target = 0.0
        self._ensure_animation()

    def _cancel_animation(self):
        if self.animation_job:
            try:
                self.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            self.animation_job = None

    def _ensure_animation(self):
        if not self.animation_job:
            self._animate()

    def _animate(self):
        self.animation_job = None
        if not self.winfo_exists():
            return
        diff = self.target - self.value
        if abs(diff) < 0.01:
            self.value = self.target
            self._draw()
            return
        self.value += diff * 0.22
        self._draw()
        self.animation_job = self.after(16, self._animate)

    def destroy(self):
        self._cancel_animation()
        super().destroy()

    def _draw(self):
        self.canvas.delete("all")
        edge = scaled_int(6)
        line_width = max(1, scaled_int(2))
        if not self.enabled:
            self.canvas.create_rectangle(
                edge,
                edge,
                self.width - edge,
                self.height - edge,
                fill="#151b29",
                outline="#30384e",
                width=line_width,
            )
            self.canvas.create_text(
                self.width / 2,
                self.height / 2,
                text=self.text,
                fill="#69738d",
                font=("Microsoft YaHei UI", 18, "bold"),
            )
            return
        v = self.value
        pad = scaled_int(6) - scaled_int(4) * v
        bg = self._mix(self.normal_bg, self.hover_bg, v)
        fg = self._mix(self.normal_fg, self.hover_fg, v)
        outline = self._mix("#4a5268", self.accent, v)
        font_size = int(18 + 3 * v)
        self.canvas.create_rectangle(
            pad,
            pad,
            self.width - pad,
            self.height - pad,
            fill=bg,
            outline=outline,
            width=line_width,
        )
        self.canvas.create_text(
            self.width / 2,
            self.height / 2,
            text=self.text,
            fill=fg,
            font=("Microsoft YaHei UI", font_size, "bold"),
        )

    @staticmethod
    def _mix(a, b, t):
        def h(x):
            x = x.lstrip("#")
            return tuple(int(x[i:i + 2], 16) for i in (0, 2, 4))

        ar, ag, ab = h(a)
        br, bg, bb = h(b)
        return "#{:02x}{:02x}{:02x}".format(
            int(ar + (br - ar) * t),
            int(ag + (bg - ag) * t),
            int(ab + (bb - ab) * t),
        )


class WobblePanel(tk.Frame):
    def __init__(self, parent, panel_bg="#182033", outline="#3b4560", bg="#111725"):
        super().__init__(parent, bg=bg)
        self.panel_bg = panel_bg
        self.outline = outline
        self.phase = 0.0
        self.job = None
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.content = tk.Frame(self.canvas, bg=panel_bg)
        self.window_id = self.canvas.create_window(24, 24, window=self.content, anchor="nw")
        self.canvas.bind("<Configure>", self._on_configure)
        self._animate()

    def destroy(self):
        if self.job:
            try:
                self.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None
        super().destroy()

    def _on_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=max(1, event.width - 48), height=max(1, event.height - 48))
        self._draw(event.width, event.height)

    def _animate(self):
        if not self.winfo_exists():
            return
        self.phase += 0.08
        self._draw(max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1))
        self.job = self.after(50, self._animate)

    def _draw(self, width, height):
        if width <= 2 or height <= 2:
            return
        self.canvas.delete("panel")
        angle = math.sin(self.phase) * 0.010
        nudge_x = math.sin(self.phase) * 2.0
        nudge_y = math.cos(self.phase * 0.9) * 1.1
        self.canvas.coords(self.window_id, 24 + nudge_x, 24 + nudge_y)
        points = self._rotated_box(width, height, 16 + nudge_x, 16 + nudge_y, angle)
        shadow = self._rotated_box(width, height, 20 + nudge_x, 20 + nudge_y, angle)
        self.canvas.create_polygon(shadow, fill="#0d1321", outline="", tags="panel")
        self.canvas.create_polygon(points, fill=self.panel_bg, outline=self.outline, width=1, tags="panel")
        cx = width / 2 + nudge_x
        cy = 16 + nudge_y
        needle_len = min(52, max(22, width * 0.055))
        needle_angle = angle * 9
        x1 = cx - math.cos(needle_angle) * needle_len
        y1 = cy - math.sin(needle_angle) * needle_len
        x2 = cx + math.cos(needle_angle) * needle_len
        y2 = cy + math.sin(needle_angle) * needle_len
        self.canvas.create_line(x1, y1, x2, y2, fill="#314668", width=1, tags="panel")
        self.canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill="#8fb6ff", outline="", tags="panel")
        self.canvas.tag_lower("panel")

    @staticmethod
    def _rotated_box(width, height, left, top, angle):
        right = width - left
        bottom = height - top
        cx = width / 2
        cy = height / 2
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        result = []
        for x, y in ((left, top), (right, top), (right, bottom), (left, bottom)):
            dx = x - cx
            dy = y - cy
            result.extend((cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))
        return result
