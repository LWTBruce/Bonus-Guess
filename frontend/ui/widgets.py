import tkinter as tk


UI_SCALE = 1.0
BUTTON_SOUND_CALLBACK = None


def set_ui_scale(scale):
    global UI_SCALE
    try:
        value = float(scale)
    except (TypeError, ValueError):
        value = 1.0
    UI_SCALE = max(0.8, min(2.0, value))


def scaled_int(value):
    return max(1, int(round(value * UI_SCALE)))


def set_button_sound_callback(callback):
    global BUTTON_SOUND_CALLBACK
    BUTTON_SOUND_CALLBACK = callback


class HoverButton(tk.Frame):
    def __init__(self, parent, text, command, width=260, height=76, accent="#f6d36b"):
        parent_bg = parent["bg"]
        theme_owner = self._theme_owner(parent)
        if theme_owner:
            parent_bg = theme_owner.theme_color("base", parent_bg)
            accent = theme_owner.theme_mapped_color(accent)
        self.command = command
        self.text = text
        self.accent = accent
        self.enabled = True
        self.normal_bg = theme_owner.theme_color("button_bg", "#20283a") if theme_owner else "#20283a"
        self.hover_bg = theme_owner.theme_color("button_hover", "#344262") if theme_owner else "#344262"
        self.normal_fg = theme_owner.theme_color("title", "#f5f0df") if theme_owner else "#f5f0df"
        self.hover_fg = theme_owner.theme_color("title", "#fff6b0") if theme_owner else "#fff6b0"
        self.disabled_bg = theme_owner.theme_color("button_disabled_bg", "#151b29") if theme_owner else "#151b29"
        self.disabled_outline = theme_owner.theme_color("button_outline", "#30384e") if theme_owner else "#30384e"
        self.disabled_fg = theme_owner.theme_color("button_disabled_fg", "#69738d") if theme_owner else "#69738d"
        self.base_outline = theme_owner.theme_color("button_outline", "#4a5268") if theme_owner else "#4a5268"
        super().__init__(parent, bg=parent_bg)
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
            bg=parent_bg,
            cursor="hand2",
        )
        self.canvas.pack()
        self.canvas.bind("<Enter>", self._enter)
        self.canvas.bind("<Leave>", self._leave)
        self.canvas.bind("<Button-1>", self._click)
        self._draw()

    def _click(self, _event):
        if self.enabled:
            if BUTTON_SOUND_CALLBACK:
                try:
                    BUTTON_SOUND_CALLBACK(self.text, self.accent)
                except Exception:
                    pass
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
                fill=self.disabled_bg,
                outline=self.disabled_outline,
                width=line_width,
            )
            self.canvas.create_text(
                self.width / 2,
                self.height / 2,
                text=self.text,
                fill=self.disabled_fg,
                font=("Microsoft YaHei UI", 18, "bold"),
            )
            return
        v = self.value
        pad = scaled_int(6) - scaled_int(4) * v
        bg = self._mix(self.normal_bg, self.hover_bg, v)
        fg = self._mix(self.normal_fg, self.hover_fg, v)
        outline = self._mix(self.base_outline, self.accent, v)
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

    @staticmethod
    def _theme_owner(widget):
        current = widget
        while current is not None:
            if hasattr(current, "theme_color") and hasattr(current, "theme_mapped_color"):
                return current
            current = getattr(current, "master", None)
        return None
