import math
import random
import tkinter as tk


class BackdropMixin:
    BACKDROP_THEMES = {
        "blue": {
            "label": "蓝色",
            "base": "#101826",
            "deep": "#0b1220",
            "panel": "#162033",
            "button_bg": "#1f2a44",
            "button_hover": "#33415f",
            "button_outline": "#5b6b8d",
            "entry_bg": "#0d1524",
            "grid_a": "#236191",
            "grid_b": "#1b496f",
            "orbit": "#2f6fa3",
            "line": "#3b82c4",
            "line_alt": "#7dd3fc",
            "particle": "#38bdf8",
            "particle_alt": "#818cf8",
            "spark": "#bae6fd",
            "title": "#fff4c2",
            "text": "#dbeafe",
            "muted": "#aab8d6",
            "subtle": "#7583a5",
            "accent": "#93c5fd",
            "success": "#a7f3d0",
            "warning": "#fde68a",
            "danger": "#fca5a5",
            "special": "#d8b4fe",
            "button_disabled_bg": "#151b29",
            "button_disabled_fg": "#69738d",
            "code_bg": "#101827",
            "code_fg": "#9ff2b2",
            "link_fg": "#8fb6ff",
            "select_bg": "#9ff2b2",
            "select_fg": "#101827",
        },
        "green": {
            "label": "浅绿色",
            "base": "#7DFF7D",
            "deep": "#42CF61",
            "panel": "#D9FFD9",
            "button_bg": "#ECFFEC",
            "button_hover": "#D2FBD5",
            "button_outline": "#087238",
            "entry_bg": "#F3FFF2",
            "grid_a": "#168A3E",
            "grid_b": "#2DBB59",
            "orbit": "#0A7643",
            "line": "#0A7249",
            "line_alt": "#075F61",
            "particle": "#0C7E4C",
            "particle_alt": "#145F9C",
            "spark": "#052B1F",
            "title": "#062414",
            "text": "#10341C",
            "muted": "#245433",
            "subtle": "#3B6B47",
            "accent": "#004F3D",
            "success": "#004619",
            "warning": "#5B3A00",
            "danger": "#7D1515",
            "special": "#40206F",
            "button_disabled_bg": "#52D46C",
            "button_disabled_fg": "#31543B",
            "code_bg": "#C7F5CC",
            "code_fg": "#062414",
            "link_fg": "#064D70",
            "select_bg": "#B5F3BD",
            "select_fg": "#062414",
        },
        "red": {
            "label": "浅红色",
            "base": "#FF695E",
            "deep": "#E6504A",
            "panel": "#FFE1DD",
            "button_bg": "#FFECE8",
            "button_hover": "#FFD5CF",
            "button_outline": "#8E1E27",
            "entry_bg": "#FFF3F0",
            "grid_a": "#87202A",
            "grid_b": "#BD3838",
            "orbit": "#7A1B27",
            "line": "#711923",
            "line_alt": "#5B2038",
            "particle": "#7A1A23",
            "particle_alt": "#642A97",
            "spark": "#3A080B",
            "title": "#2A0708",
            "text": "#3D0F10",
            "muted": "#5A1A1A",
            "subtle": "#7A302C",
            "accent": "#4A101C",
            "success": "#00351A",
            "warning": "#3A2600",
            "danger": "#4D0A12",
            "special": "#35155E",
            "button_disabled_bg": "#EE7770",
            "button_disabled_fg": "#6F2B2A",
            "code_bg": "#F9CBC7",
            "code_fg": "#2A0708",
            "link_fg": "#2C1B66",
            "select_bg": "#F8B7B2",
            "select_fg": "#2A0708",
        },
        "yellow": {
            "label": "黄色",
            "base": "#FFFF7D",
            "deep": "#D7CC4A",
            "panel": "#FFFBD0",
            "button_bg": "#FFF9C2",
            "button_hover": "#F9ED9B",
            "button_outline": "#806300",
            "entry_bg": "#FFFDE5",
            "grid_a": "#8C7000",
            "grid_b": "#B09418",
            "orbit": "#806100",
            "line": "#806500",
            "line_alt": "#9A4D00",
            "particle": "#8B6A00",
            "particle_alt": "#8E4D00",
            "spark": "#332400",
            "title": "#241900",
            "text": "#352800",
            "muted": "#5F4C00",
            "subtle": "#776300",
            "accent": "#624900",
            "success": "#075F31",
            "warning": "#674300",
            "danger": "#7C1D1A",
            "special": "#4B2F85",
            "button_disabled_bg": "#E8DC67",
            "button_disabled_fg": "#6C5B00",
            "code_bg": "#F1ECA8",
            "code_fg": "#241900",
            "link_fg": "#334C8C",
            "select_bg": "#E7D96A",
            "select_fg": "#241900",
        },
        "pink": {
            "label": "粉色",
            "base": "#FFA8CF",
            "deep": "#E876A9",
            "panel": "#FFE4F0",
            "button_bg": "#FFF0F6",
            "button_hover": "#FFD8E9",
            "button_outline": "#9C2E68",
            "entry_bg": "#FFF6FA",
            "grid_a": "#98265F",
            "grid_b": "#C94F88",
            "orbit": "#862157",
            "line": "#7B2054",
            "line_alt": "#5B2A7E",
            "particle": "#8B245C",
            "particle_alt": "#4E4FA4",
            "spark": "#321027",
            "title": "#2A0D1E",
            "text": "#3D1730",
            "muted": "#66304F",
            "subtle": "#854769",
            "accent": "#70204F",
            "success": "#00481F",
            "warning": "#4A2E00",
            "danger": "#77182D",
            "special": "#4E2E8C",
            "button_disabled_bg": "#F09BBC",
            "button_disabled_fg": "#763F5A",
            "code_bg": "#FAD1E3",
            "code_fg": "#2A0D1E",
            "link_fg": "#1D367F",
            "select_bg": "#F2B6D3",
            "select_fg": "#2A0D1E",
        },
        "purple": {
            "label": "紫色",
            "base": "#C391FF",
            "deep": "#A779E8",
            "panel": "#EFE1FF",
            "button_bg": "#F5EBFF",
            "button_hover": "#E7D3FF",
            "button_outline": "#56308F",
            "entry_bg": "#FAF5FF",
            "grid_a": "#542A87",
            "grid_b": "#7748B3",
            "orbit": "#4C247D",
            "line": "#432070",
            "line_alt": "#29478F",
            "particle": "#512981",
            "particle_alt": "#087080",
            "spark": "#211039",
            "title": "#1D0D33",
            "text": "#2B1745",
            "muted": "#43265E",
            "subtle": "#5E4678",
            "accent": "#45227E",
            "success": "#00381B",
            "warning": "#3D2900",
            "danger": "#71172A",
            "special": "#4A0C62",
            "button_disabled_bg": "#B894EC",
            "button_disabled_fg": "#61477D",
            "code_bg": "#DFCCF7",
            "code_fg": "#1D0D33",
            "link_fg": "#12366F",
            "select_bg": "#D2B2F6",
            "select_fg": "#1D0D33",
        },
    }

    def backdrop_theme_id(self):
        settings = getattr(self, "player_settings", {}) or {}
        theme_id = str(settings.get("backdrop_theme") or "blue").strip()
        return theme_id if theme_id in self.BACKDROP_THEMES else "blue"

    def backdrop_theme(self):
        return self.BACKDROP_THEMES[self.backdrop_theme_id()]

    def theme_color(self, key, fallback="#111725"):
        return self.backdrop_theme().get(key, fallback)

    def theme_role_for_color(self, color):
        normalized = str(color or "").lower()
        role_map = {
            "#fff2bd": "title",
            "#fff8dc": "title",
            "#f5f0df": "title",
            "#fff6b0": "title",
            "#dce6ff": "text",
            "#c8d2ee": "text",
            "#9ca8c7": "muted",
            "#7f8caf": "muted",
            "#7683a3": "muted",
            "#69738d": "subtle",
            "#64708f": "subtle",
            "#4f5a75": "subtle",
            "#8fb6ff": "accent",
            "#9fb7ff": "accent",
            "#7ed6ff": "accent",
            "#b7f6ff": "accent",
            "#9ff2b2": "success",
            "#7fd9c6": "success",
            "#f6d36b": "warning",
            "#ffcf8f": "warning",
            "#ffbd7e": "warning",
            "#ff9b89": "danger",
            "#ff6b8a": "danger",
            "#f6a6ff": "special",
            "#c084fc": "special",
            "#c4b5fd": "special",
        }
        return role_map.get(normalized)

    def theme_mapped_color(self, color):
        role = self.theme_role_for_color(color)
        return self.theme_color(role, color) if role else color

    def themed_legacy_color(self, color, option="bg"):
        if self.backdrop_theme_id() == "blue":
            return color
        normalized = str(color or "").lower()
        surface_map = {
            "#111725": "base",
            "#182033": "base",
            "#162033": "base",
            "#050507": "base",
            "#020617": "base",
            "#0b1020": "base",
            "#0b1220": "deep",
            "#0d1524": "deep",
            "#101827": "deep",
            "#111827": "deep",
            "#121827": "deep",
            "#151d2c": "deep",
            "#1f2a44": "button_bg",
            "#20283a": "button_hover",
            "#233049": "button_bg",
            "#26344f": "button_hover",
            "#22304a": "button_hover",
            "#061128": "deep",
            "#071225": "panel",
            "#0b1e38": "button_bg",
            "#102a4c": "entry_bg",
            "#0f3f61": "button_bg",
            "#155e75": "entry_bg",
            "#1c2033": "button_bg",
        }
        border_map = {
            "#30384e": "button_outline",
            "#3b4560": "button_outline",
            "#4b5877": "button_outline",
            "#252d40": "button_outline",
            "#0b2d5c": "button_outline",
            "#102642": "grid_a",
            "#123b6d": "grid_a",
            "#1d4ed8": "line",
            "#2563eb": "line",
            "#0e2f5a": "grid_b",
            "#7dd3fc": "accent",
        }
        role = None
        if option == "selectbackground":
            role = "select_bg"
        elif option == "selectforeground":
            role = "select_fg"
        elif option == "disabledbackground":
            role = "button_disabled_bg"
        elif option == "disabledforeground":
            role = self.theme_role_for_color(normalized) or "button_disabled_fg"
        elif option in {"fg", "activeforeground", "insertbackground", "disabledforeground", "selectforeground"}:
            role = self.theme_role_for_color(normalized)
        elif option in {"highlightbackground", "highlightcolor", "outline", "border"}:
            role = border_map.get(normalized) or surface_map.get(normalized)
        else:
            role = surface_map.get(normalized)
        return self.theme_color(role, color) if role else color

    def apply_static_theme(self, root):
        if self.backdrop_theme_id() == "blue" or not root:
            return

        def configure_widget(widget):
            try:
                widget_class = widget.winfo_class()
            except tk.TclError:
                return
            theme_surface = bool(getattr(widget, "_theme_surface", False))
            if widget_class != "Canvas" or theme_surface:
                for option in (
                    "bg",
                    "background",
                    "activebackground",
                    "selectcolor",
                    "troughcolor",
                    "disabledbackground",
                    "selectbackground",
                ):
                    try:
                        current = widget.cget(option)
                        mapped = self.themed_legacy_color(current, option)
                        if mapped != current:
                            widget.configure(**{option: mapped})
                    except tk.TclError:
                        pass
                for option in ("highlightbackground", "highlightcolor"):
                    try:
                        current = widget.cget(option)
                        mapped = self.themed_legacy_color(current, option)
                        if mapped != current:
                            widget.configure(**{option: mapped})
                    except tk.TclError:
                        pass
                for option in ("fg", "foreground", "activeforeground", "insertbackground", "disabledforeground", "selectforeground"):
                    try:
                        current = widget.cget(option)
                        mapped = self.themed_legacy_color(current, option)
                        if mapped != current:
                            widget.configure(**{option: mapped})
                    except tk.TclError:
                        pass
                if hasattr(widget, "tag_configure"):
                    try:
                        widget_bg = widget.cget("bg")
                        widget.tag_configure("code", background=widget_bg, foreground=self.theme_color("code_fg"))
                        widget.tag_configure("math", background=widget_bg, foreground=self.theme_color("text"))
                        widget.tag_configure("math_sup", background=widget_bg, foreground=self.theme_color("text"))
                        widget.tag_configure("math_sub", background=widget_bg, foreground=self.theme_color("text"))
                        widget.tag_configure("bold", foreground=self.theme_color("text"))
                        widget.tag_configure("italic", foreground=self.theme_color("text"))
                        widget.tag_configure("muted", foreground=self.theme_color("muted"))
                    except tk.TclError:
                        pass
                try:
                    menu = widget["menu"]
                    if menu:
                        menu.configure(
                            bg=self.theme_color("deep"),
                            fg=self.theme_color("title"),
                            activebackground=self.theme_color("button_hover"),
                            activeforeground=self.theme_color("title"),
                        )
                except tk.TclError:
                    pass
                except Exception:
                    pass
            try:
                children = widget.winfo_children()
            except tk.TclError:
                children = []
            for child in children:
                configure_widget(child)

        configure_widget(root)

    def apply_backdrop_theme(self):
        base = self.theme_color("base")
        try:
            self.configure(bg=base)
        except tk.TclError:
            pass
        container = getattr(self, "container", None)
        try:
            if container and container.winfo_exists():
                container.configure(bg=base)
        except tk.TclError:
            pass

    def _backdrop_speed(self):
        settings = getattr(self, "player_settings", {}) or {}
        try:
            return max(0.4, min(10.0, float(settings.get("backdrop_speed", 1.0))))
        except (TypeError, ValueError):
            return 1.0

    def _backdrop_density(self):
        settings = getattr(self, "player_settings", {}) or {}
        try:
            return max(0.4, min(10.0, float(settings.get("backdrop_density", 1.0))))
        except (TypeError, ValueError):
            return 1.0

    def _backdrop_opacity(self):
        settings = getattr(self, "player_settings", {}) or {}
        try:
            return max(0.0, min(1.0, float(settings.get("backdrop_opacity", 1.0))))
        except (TypeError, ValueError):
            return 1.0

    @staticmethod
    def _hex_to_rgb(color):
        color = str(color or "#111725").lstrip("#")
        return tuple(int(color[index:index + 2], 16) for index in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb):
        return "#" + "".join(f"{max(0, min(255, int(value))):02x}" for value in rgb)

    def _fade_color(self, color, opacity_scale=1.0):
        opacity = self._backdrop_opacity() * opacity_scale
        if opacity <= 0:
            return self.theme_color("base")
        bg = self._hex_to_rgb(self.theme_color("base"))
        fg = self._hex_to_rgb(color)
        mixed = [bg[i] + (fg[i] - bg[i]) * opacity for i in range(3)]
        return self._rgb_to_hex(mixed)

    def _start_backdrop(self, style, parent=None):
        if parent is None:
            parent = self.container
        self.backdrop_style = style
        self.backdrop_phase = random.random() * 100
        self.backdrop_panels = []
        self.backdrop_canvas = tk.Canvas(
            parent,
            bd=0,
            highlightthickness=0,
            bg=self.theme_color("base"),
        )
        self.backdrop_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.backdrop_canvas.tk.call("lower", self.backdrop_canvas._w)
        self._animate_backdrop()

    def add_backdrop_panel(self, relx, rely, relwidth, relheight, pad=22, content=None):
        panels = getattr(self, "backdrop_panels", None)
        if panels is None:
            self.backdrop_panels = []
            panels = self.backdrop_panels
        panel = {
            "relx": float(relx),
            "rely": float(rely),
            "relwidth": float(relwidth),
            "relheight": float(relheight),
            "pad": int(pad),
            "content": list(content or []),
        }
        panels.append(panel)
        return panel

    def set_backdrop_panel_content(self, content, panel_index=-1):
        panels = getattr(self, "backdrop_panels", []) or []
        if not panels:
            return
        panels[panel_index]["content"] = list(content or [])

    def decorate_surface(self, parent, style="grid", opacity_scale=0.55):
        canvas = tk.Canvas(parent, bd=0, highlightthickness=0, bg=self.theme_color("base"))
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            canvas.tk.call("lower", canvas._w)
        except tk.TclError:
            pass
        phase_state = {"value": random.random() * 100}
        job_state = {"id": None}

        def cancel_job(_event=None):
            job = job_state.get("id")
            if job:
                try:
                    canvas.after_cancel(job)
                except tk.TclError:
                    pass
                job_state["id"] = None

        def redraw(_event=None, animate=False):
            try:
                if not canvas.winfo_exists():
                    return
            except tk.TclError:
                return
            width = max(canvas.winfo_width(), 1)
            height = max(canvas.winfo_height(), 1)
            canvas.delete("all")
            canvas.create_rectangle(0, 0, width, height, fill=self._fade_color(self.theme_color("base"), 1.0), outline="")
            phase = phase_state["value"]
            step = max(20, int(42 / math.sqrt(self._backdrop_density())))
            if style in {"grid", "particles"}:
                for x in range(-step, width + step, step):
                    offset = math.sin(phase * 0.8 + x * 0.01) * step * 0.18
                    canvas.create_line(x + offset, 0, x + step * 0.20 - offset, height, fill=self._fade_color(self.theme_color("grid_b"), opacity_scale * 0.62), width=1)
                for y in range(-step, height + step, step):
                    offset = math.cos(phase * 0.7 + y * 0.01) * step * 0.16
                    canvas.create_line(0, y + offset, width, y + step * 0.14 - offset, fill=self._fade_color(self.theme_color("grid_a"), opacity_scale * 0.58), width=1)
            if style in {"lines", "wind", "particles", "constellation"}:
                count = max(8, int(width / 85))
                for index in range(count):
                    seed = phase + index * 29.7
                    x = (seed * 13) % max(width, 1)
                    y = (seed * 19) % max(height, 1)
                    length = 20 + (index % 5) * 14
                    canvas.create_line(x, y, min(width, x + length), y, fill=self._fade_color(self.theme_color("line"), opacity_scale * 0.62), width=1)
            for index in range(max(3, int(width / 220))):
                seed = phase + index * 43.1
                x = (seed * 17) % max(width, 1)
                y = (seed * 11) % max(height, 1)
                size = 2 + index % 3
                canvas.create_rectangle(x, y, x + size, y + size, fill=self._fade_color(self.theme_color("spark"), opacity_scale * 0.85), outline="")
            if animate:
                phase_state["value"] += 0.018 * self._backdrop_speed()
                try:
                    cancel_job()
                    job_state["id"] = canvas.after(50, lambda: redraw(animate=True))
                except tk.TclError:
                    pass

        parent.bind("<Configure>", redraw, add="+")
        canvas.bind("<Destroy>", cancel_job, add="+")
        canvas.after_idle(lambda: redraw(animate=True))
        return canvas

    def reveal_background_surface(self, parent, bg=None):
        bg = bg or self.theme_color("base")
        border = self.theme_color("grid_a")
        skip_classes = {"Canvas", "Entry", "Text", "Listbox", "Scrollbar", "Scale", "TCombobox"}
        surface_colors = {"#111725", "#182033"}
        border_colors = {"#30384e", "#3b4560", "#4b5877"}

        def normalize(widget):
            try:
                widget_class = widget.winfo_class()
            except tk.TclError:
                return
            if widget_class not in skip_classes:
                try:
                    if str(widget.cget("bg")).lower() in surface_colors:
                        widget.configure(bg=bg)
                except tk.TclError:
                    pass
                try:
                    if str(widget.cget("highlightbackground")).lower() in border_colors:
                        widget.configure(highlightbackground=border)
                except tk.TclError:
                    pass
                try:
                    mapped = self.theme_mapped_color(widget.cget("fg"))
                    if mapped != widget.cget("fg"):
                        widget.configure(fg=mapped)
                except tk.TclError:
                    pass
                try:
                    mapped = self.theme_mapped_color(widget.cget("activeforeground"))
                    if mapped != widget.cget("activeforeground"):
                        widget.configure(activeforeground=mapped)
                except tk.TclError:
                    pass
            try:
                children = widget.winfo_children()
            except tk.TclError:
                children = []
            for child in children:
                normalize(child)

        normalize(parent)
        self.apply_static_theme(parent)

    def _animate_backdrop(self):
        canvas = self.backdrop_canvas
        if not canvas:
            return
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        canvas.delete("all")
        if self.backdrop_style == "grid":
            self._draw_rotating_grid(canvas, width, height)
        elif self.backdrop_style == "lines":
            self._draw_drifting_lines(canvas, width, height)
        elif self.backdrop_style == "particles":
            self._draw_soft_particles(canvas, width, height)
        elif self.backdrop_style == "wind":
            self._draw_wind_field(canvas, width, height)
        else:
            self._draw_constellation(canvas, width, height)
        self._draw_green_doodle_flowers(canvas, width, height)
        self._draw_red_heart_ribbons(canvas, width, height)
        self._draw_backdrop_panels(canvas, width, height)
        self.backdrop_phase += 0.024 * self._backdrop_speed()
        self.backdrop_job = self.after(70, self._animate_backdrop)

    def _draw_green_doodle_flowers(self, canvas, width, height):
        if self.backdrop_theme_id() != "green":
            return
        density = math.sqrt(self._backdrop_density())
        count = max(6, int(8 * density))
        for spec in self._green_flower_specs(count):
            x, y, angle = self._green_flower_position(spec, width, height, self.backdrop_phase)
            self._draw_doodle_flower(canvas, x, y, spec["size"], angle, spec["color"])

    @staticmethod
    def _green_flower_specs(count):
        flower_colors = ("#ff77b7", "#fff176", "#7edcff", "#ffb36b", "#c391ff", "#ffffff")
        specs = []
        for index in range(count):
            rng = random.Random(index * 92821 + 617)
            specs.append({
                "base_x": rng.random(),
                "base_y": rng.random(),
                "base_angle": rng.uniform(0, math.tau),
                "fall_speed": rng.uniform(10.0, 18.0),
                "drift_amp": rng.uniform(12.0, 36.0),
                "drift_speed": rng.uniform(0.34, 0.62),
                "spin_speed": rng.choice((-1, 1)) * rng.uniform(0.18, 0.42),
                "size": rng.uniform(5.0, 9.0),
                "color": flower_colors[index % len(flower_colors)],
                "phase": rng.uniform(0, math.tau),
            })
        return specs

    @staticmethod
    def _green_flower_position(spec, width, height, phase):
        margin = 54 + spec["size"] * 3
        x = spec["base_x"] * max(width, 1)
        x += math.sin(phase * spec["drift_speed"] + spec["phase"]) * spec["drift_amp"]
        x = (x + margin) % (width + margin * 2) - margin
        y = (spec["base_y"] * max(height, 1) + phase * spec["fall_speed"]) % (height + margin * 2) - margin
        angle = spec["base_angle"] + phase * spec["spin_speed"]
        return x, y, angle

    def _draw_doodle_flower(self, canvas, x, y, radius, angle, petal):
        outline = self._fade_color("#0b6d36", 0.56)
        petal_radius = radius * 0.48
        for petal_index in range(5):
            petal_angle = angle + math.tau * petal_index / 5
            px = x + math.cos(petal_angle) * radius
            py = y + math.sin(petal_angle) * radius
            canvas.create_oval(
                px - petal_radius,
                py - petal_radius,
                px + petal_radius,
                py + petal_radius,
                fill=self._fade_color(petal, 0.62),
                outline=outline,
                width=1,
            )
        canvas.create_oval(
            x - radius * 0.34,
            y - radius * 0.34,
            x + radius * 0.34,
            y + radius * 0.34,
            fill=self._fade_color("#ffe66d", 0.78),
            outline=outline,
        )
        stem_len = radius * 1.7
        stem_angle = angle + math.pi / 2
        canvas.create_line(
            x + math.cos(stem_angle) * radius * 0.55,
            y + math.sin(stem_angle) * radius * 0.55,
            x + math.cos(stem_angle) * (radius * 0.55 + stem_len),
            y + math.sin(stem_angle) * (radius * 0.55 + stem_len),
            fill=self._fade_color("#178f42", 0.52),
            width=1,
        )

    def _draw_red_heart_ribbons(self, canvas, width, height):
        if self.backdrop_theme_id() != "red":
            return
        density = math.sqrt(self._backdrop_density())
        count = max(5, int(round(9 * 0.75 * density)))
        for spec in self._red_float_specs(count):
            x, y, angle = self._red_float_position(spec, width, height, self.backdrop_phase)
            if spec["kind"] == "ribbon":
                self._draw_doodle_ribbon(
                    canvas,
                    x,
                    y,
                    spec["size"],
                    angle,
                    spec["color"],
                    self.backdrop_phase + spec["phase"],
                    spec["colors"],
                    coiled=spec.get("coiled", False),
                    coil_turns=spec.get("coil_turns", 1.1),
                    coil_radius=spec.get("coil_radius", 4.2),
                    coil_phase=spec.get("coil_phase", 0.0),
                )
            else:
                self._draw_doodle_heart(canvas, x, y, spec["size"], angle, spec["color"])

    @staticmethod
    def _red_float_specs(count):
        heart_colors = ("#fff3ef", "#ffd1d9", "#ff8fab", "#ffe066", "#c391ff", "#7edcff")
        ribbon_palettes = (
            ("#fff3ef", "#ffd166", "#ff8fab", "#c391ff"),
            ("#ffe0bd", "#ffb36b", "#fff3ef", "#7edcff"),
            ("#ffd1d9", "#ff5f7e", "#fff8f3", "#ffe066"),
            ("#f6d7ff", "#c391ff", "#fff3ef", "#ffb36b"),
        )
        specs = []
        for index in range(count):
            rng = random.Random(index * 73129 + 241)
            kind = "ribbon" if index % 3 == 1 else "heart"
            ribbon_palette = ribbon_palettes[index % len(ribbon_palettes)]
            heart_color = heart_colors[index % len(heart_colors)]
            is_ribbon = kind == "ribbon"
            is_coiled = is_ribbon and rng.random() < 0.55
            if is_ribbon:
                x_slot = (index + 0.5 + rng.uniform(-0.30, 0.30)) / max(1, count)
                y_slot = ((index * 5) % max(1, count) + 0.5 + rng.uniform(-0.30, 0.30)) / max(1, count)
            else:
                x_slot = rng.random()
                y_slot = rng.random()
            specs.append({
                "base_x": x_slot % 1.0,
                "base_y": y_slot % 1.0,
                "base_angle": rng.uniform(0, math.tau) if is_ribbon else rng.uniform(-0.42, 0.42),
                "rise_speed": rng.uniform(8.0, 15.0) if is_ribbon else rng.uniform(10.0, 18.0),
                "drift_amp": rng.uniform(22.0, 58.0) if is_ribbon else rng.uniform(14.0, 42.0),
                "drift_speed": rng.uniform(0.32, 0.58),
                "spin_speed": rng.choice((-1, 1)) * rng.uniform(0.10, 0.26),
                "size": rng.uniform(9.5, 15.5) if is_ribbon else rng.uniform(8.0, 15.0),
                "color": ribbon_palette[0] if is_ribbon else heart_color,
                "colors": ribbon_palette if is_ribbon else (heart_color,),
                "phase": rng.uniform(0, math.tau),
                "coiled": is_coiled,
                "coil_turns": rng.uniform(0.92, 1.28) if is_coiled else 0.0,
                "coil_radius": rng.uniform(3.7, 5.2) if is_coiled else 0.0,
                "coil_phase": rng.uniform(0, math.tau) if is_coiled else 0.0,
                "kind": kind,
            })
        return specs

    @staticmethod
    def _red_float_position(spec, width, height, phase):
        side_margin = 80 + spec["size"] * 2
        vertical_margin = 80 + spec["size"] * 2.5
        x = spec["base_x"] * max(width, 1)
        x += math.sin(phase * spec["drift_speed"] + spec["phase"]) * spec["drift_amp"]
        x = (x + side_margin) % (max(width, 1) + side_margin * 2) - side_margin
        travel = max(height, 1) + vertical_margin * 2
        y = (spec["base_y"] * travel - phase * spec["rise_speed"]) % travel - vertical_margin
        angle = spec["base_angle"] + math.sin(phase * spec["spin_speed"] + spec["phase"]) * 0.55
        return x, y, angle

    def _draw_doodle_heart(self, canvas, x, y, radius, angle, fill):
        scale = radius / 18.0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        points = []
        for step in range(32):
            t = math.tau * step / 32
            local_x = 16 * math.sin(t) ** 3 * scale
            local_y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * scale
            points.extend((
                x + local_x * cos_a - local_y * sin_a,
                y + local_x * sin_a + local_y * cos_a,
            ))
        canvas.create_polygon(
            points,
            fill=self._fade_color(fill, 0.74),
            outline=self._fade_color("#7a1a23", 0.56),
            width=1,
            smooth=True,
            splinesteps=18,
        )
        highlight_x = x - math.cos(angle) * radius * 0.20 + math.sin(angle) * radius * 0.24
        highlight_y = y - math.sin(angle) * radius * 0.20 - math.cos(angle) * radius * 0.24
        canvas.create_oval(
            highlight_x - radius * 0.10,
            highlight_y - radius * 0.08,
            highlight_x + radius * 0.10,
            highlight_y + radius * 0.08,
            fill=self._fade_color("#ffffff", 0.42),
            outline="",
        )

    def _draw_doodle_ribbon(
        self,
        canvas,
        x,
        y,
        radius,
        angle,
        fill,
        phase,
        palette=None,
        coiled=False,
        coil_turns=1.1,
        coil_radius=4.2,
        coil_phase=0.0,
    ):
        colors = tuple(palette or (fill,))
        length = radius * 44.0
        segments = 42
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        left_edge = []
        right_edge = []
        centerline = []

        def transform(local_x, local_y):
            return (
                x + local_x * cos_a - local_y * sin_a,
                y + local_x * sin_a + local_y * cos_a,
            )

        centers = self._ribbon_centerline_points(radius, length, segments, phase, coiled, coil_turns, coil_radius, coil_phase)
        samples = []
        for index in range(segments + 1):
            t = index / segments
            curve, local_y = centers[index]
            prev_x, prev_y = centers[max(0, index - 1)]
            next_x, next_y = centers[min(segments, index + 1)]
            tangent_x = next_x - prev_x
            tangent_y = next_y - prev_y
            tangent_len = max(1.0, math.hypot(tangent_x, tangent_y))
            normal_x = -tangent_y / tangent_len
            normal_y = tangent_x / tangent_len
            twist = math.sin(t * math.tau * 2.72 + phase * 1.18)
            visible_width = radius * (0.22 + 0.58 * abs(math.cos(t * math.tau * 2.72 + phase * 1.18)))
            taper = 0.58 + 0.42 * math.sin(t * math.pi)
            half_width = max(2.4, visible_width * taper)
            samples.append({
                "center": (curve, local_y),
                "left": (curve + normal_x * half_width, local_y + normal_y * half_width),
                "right": (curve - normal_x * half_width, local_y - normal_y * half_width),
                "twist": twist,
            })
            cx, cy = transform(curve, local_y)
            lx, ly = transform(*samples[-1]["left"])
            rx, ry = transform(*samples[-1]["right"])
            centerline.extend((cx, cy))
            left_edge.extend((lx, ly))
            right_edge.extend((rx, ry))

        canvas.create_line(
            centerline,
            fill=self._fade_color("#7a1a23", 0.20),
            width=max(2, int(radius * 0.82)),
            smooth=True,
            splinesteps=20,
            capstyle="round",
            joinstyle="round",
        )

        for index in range(segments):
            current = samples[index]
            following = samples[index + 1]
            points = []
            for point in (current["left"], following["left"], following["right"], current["right"]):
                points.extend(transform(*point))
            base_color = colors[index % len(colors)]
            shade_target = "#ffffff" if (current["twist"] + following["twist"]) >= 0 else "#7a1a23"
            shade_amount = 0.18 if shade_target == "#ffffff" else 0.12
            band_color = self._mix_hex_colors(base_color, shade_target, shade_amount)
            canvas.create_polygon(
                points,
                fill=self._fade_color(band_color, 0.64),
                outline=self._fade_color("#7a1a23", 0.16),
                width=1,
            )
            if index % 3 == 1:
                inner_a = current["center"]
                inner_b = following["center"]
                canvas.create_line(
                    *transform(*inner_a),
                    *transform(*inner_b),
                    fill=self._fade_color("#fffaf7", 0.32),
                    width=1,
                    smooth=True,
                    splinesteps=8,
                )

        canvas.create_line(left_edge, fill=self._fade_color("#fffaf7", 0.36), width=1, smooth=True, splinesteps=20)
        canvas.create_line(right_edge, fill=self._fade_color("#7a1a23", 0.28), width=1, smooth=True, splinesteps=20)

    @staticmethod
    def _ribbon_centerline_points(radius, length, segments, phase, coiled=False, coil_turns=1.1, coil_radius=4.2, coil_phase=0.0):
        points = []
        if not coiled:
            for index in range(segments + 1):
                t = index / segments
                curve = (
                    math.sin(t * math.tau * 1.16 + phase) * radius * 1.22
                    + math.sin(t * math.tau * 2.38 + phase * 0.72) * radius * 0.42
                )
                points.append((curve, (t - 0.5) * length))
            return points

        lead_end = 0.24
        loop_end = 0.58
        loop_center_y = 0.0
        loop_radius = radius * coil_radius
        loop_phase = coil_phase + phase * 0.10

        def loop_point(u):
            theta = loop_phase + u * math.tau * coil_turns
            radial = loop_radius * (1.05 - 0.12 * u)
            return (
                math.cos(theta) * radial,
                loop_center_y + math.sin(theta) * radial,
            )

        loop_start_x, loop_start_y = loop_point(0.0)
        loop_end_x, loop_end_y = loop_point(1.0)
        for index in range(segments + 1):
            t = index / segments
            if t < lead_end:
                v = t / lead_end
                entry_x = -radius * 3.4 + math.sin(phase + v * math.pi) * radius * 0.8
                entry_y = -length * 0.50 + v * (loop_start_y + length * 0.50)
                entry_x += v * (loop_start_x + radius * 3.4)
                points.append((entry_x, entry_y))
                continue
            if t <= loop_end:
                points.append(loop_point((t - lead_end) / (loop_end - lead_end)))
                continue
            v = (t - loop_end) / (1.0 - loop_end)
            tail_x = (
                loop_end_x
                + math.sin(v * math.tau * 1.25 + phase) * radius * 2.3
                + math.sin(v * math.tau * 2.4 + phase * 0.6) * radius * 0.8
                + v * radius * 4.4
            )
            tail_y = loop_end_y + v * (length * 0.50 - loop_end_y)
            points.append((tail_x, tail_y))
        return points

    def _mix_hex_colors(self, first, second, amount):
        amount = max(0.0, min(1.0, float(amount)))
        first_rgb = self._hex_to_rgb(first)
        second_rgb = self._hex_to_rgb(second)
        return self._rgb_to_hex(first_rgb[index] + (second_rgb[index] - first_rgb[index]) * amount for index in range(3))

    def _draw_backdrop_panels(self, canvas, width, height):
        for panel in getattr(self, "backdrop_panels", []) or []:
            panel_width = width * panel["relwidth"]
            panel_height = height * panel["relheight"]
            cx = width * panel["relx"]
            cy = height * panel["rely"]
            left = cx - panel_width / 2
            top = cy - panel_height / 2
            right = cx + panel_width / 2
            bottom = cy + panel_height / 2
            pad = panel.get("pad", 22)
            angle = math.sin(self.backdrop_phase * 1.15) * 0.012
            nudge_x = math.sin(self.backdrop_phase * 1.35) * 3.0
            nudge_y = math.cos(self.backdrop_phase * 1.05) * 1.8
            points = self._rotated_panel_points(left + pad + nudge_x, top + pad + nudge_y, right - pad + nudge_x, bottom - pad + nudge_y, angle)
            shadow = self._rotated_panel_points(left + pad + 6 + nudge_x, top + pad + 7 + nudge_y, right - pad + 6 + nudge_x, bottom - pad + 7 + nudge_y, angle)
            canvas.create_polygon(shadow, fill="", outline=self._fade_color(self.theme_color("deep"), 0.92), width=2)
            canvas.create_polygon(points, fill="", outline=self._fade_color(self.theme_color("grid_a"), 0.95), width=1)
            inset = 7
            inner = self._rotated_panel_points(left + pad + inset + nudge_x, top + pad + inset + nudge_y, right - pad - inset + nudge_x, bottom - pad - inset + nudge_y, angle)
            canvas.create_polygon(inner, fill="", outline=self._fade_color(self.theme_color("grid_b"), 0.54), width=1)
            needle_len = min(78, max(34, panel_width * 0.08))
            needle_angle = angle * 9
            nx = (left + right) / 2 + nudge_x
            ny = top + pad + nudge_y
            x1 = nx - math.cos(needle_angle) * needle_len
            y1 = ny - math.sin(needle_angle) * needle_len
            x2 = nx + math.cos(needle_angle) * needle_len
            y2 = ny + math.sin(needle_angle) * needle_len
            canvas.create_line(x1, y1, x2, y2, fill=self._fade_color(self.theme_color("line"), 0.88), width=1)
            canvas.create_oval(nx - 3, ny - 3, nx + 3, ny + 3, fill=self._fade_color(self.theme_color("spark"), 0.96), outline="")
            for corner in ((left + pad, top + pad), (right - pad, top + pad), (left + pad, bottom - pad), (right - pad, bottom - pad)):
                x, y = corner
                size = 18
                canvas.create_line(x + nudge_x, y + nudge_y, x + nudge_x + (size if x < cx else -size), y + nudge_y, fill=self._fade_color(self.theme_color("line_alt"), 0.58), width=1)
                canvas.create_line(x + nudge_x, y + nudge_y, x + nudge_x, y + nudge_y + (size if y < cy else -size), fill=self._fade_color(self.theme_color("line_alt"), 0.58), width=1)
            self._draw_backdrop_panel_content(canvas, panel, left, top, right, bottom, pad, nudge_x, nudge_y, angle)

    def _draw_backdrop_panel_content(self, canvas, panel, left, top, right, bottom, pad, nudge_x, nudge_y, angle):
        content = panel.get("content") or []
        if not content:
            return
        center_x = (left + right) / 2 + nudge_x
        center_y = (top + bottom) / 2 + nudge_y
        content_left = left + pad + panel.get("content_pad_x", 58) + nudge_x
        content_top = top + pad + panel.get("content_pad_y", 34) + nudge_y
        content_width = max(180, right - left - pad * 2 - panel.get("content_pad_x", 58) - panel.get("content_pad_right", 40))
        for item in content:
            text = str(item.get("text") or "")
            if not text:
                continue
            x = content_left + float(item.get("x", 0))
            y = content_top + float(item.get("y", 0))
            x, y = self._rotated_point(x, y, center_x, center_y, angle)
            role = item.get("role")
            fill = self.theme_color(role, item.get("fill", self.theme_color("text"))) if role else item.get("fill", self.theme_color("text"))
            font = tuple(item.get("font", ("Microsoft YaHei UI", 12)))
            anchor = item.get("anchor", "nw")
            try:
                width = float(item.get("width", content_width))
            except (TypeError, ValueError):
                width = content_width
            width = max(80, min(width, content_width))
            canvas.create_text(
                x,
                y,
                text=text,
                fill=fill,
                font=font,
                anchor=anchor,
                justify=item.get("justify", "left"),
                width=width,
            )

    def _rotated_panel_points(self, left, top, right, bottom, angle):
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        result = []
        for x, y in ((left, top), (right, top), (right, bottom), (left, bottom)):
            dx = x - cx
            dy = y - cy
            result.extend((cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))
        return result

    @staticmethod
    def _rotated_point(x, y, cx, cy, angle):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        dx = x - cx
        dy = y - cy
        return cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a

    def _draw_rotating_grid(self, canvas, width, height):
        cx = width / 2
        cy = height / 2
        angle = math.sin(self.backdrop_phase * 0.45) * 0.08
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        extent = int(max(width, height) * 1.4)
        step = max(14, int(32 / math.sqrt(self._backdrop_density())))

        def rotate(x, y):
            dx = x - cx
            dy = y - cy
            return cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a

        for offset in range(-extent, extent + step, step):
            x1, y1 = rotate(cx - extent, cy + offset)
            x2, y2 = rotate(cx + extent, cy + offset)
            canvas.create_line(x1, y1, x2, y2, fill=self._fade_color(self.theme_color("grid_a"), 0.78), width=1)
            x3, y3 = rotate(cx + offset, cy - extent)
            x4, y4 = rotate(cx + offset, cy + extent)
            canvas.create_line(x3, y3, x4, y4, fill=self._fade_color(self.theme_color("grid_b"), 0.72), width=1)
        for radius in (min(width, height) * 0.28, min(width, height) * 0.46):
            canvas.create_oval(
                cx - radius,
                cy - radius * 0.38,
                cx + radius,
                cy + radius * 0.38,
                outline=self._fade_color(self.theme_color("orbit"), 0.34),
                width=1,
            )

    def _draw_drifting_lines(self, canvas, width, height):
        count = max(16, int(max(48, int(width / 21)) * self._backdrop_density()))
        for index in range(count):
            seed = index * 37.17
            y = (seed * 19 + self.backdrop_phase * 34) % (height + 160) - 80
            x = (seed * 53 + self.backdrop_phase * 78) % (width + 240) - 120
            length = 28 + (index % 7) * 13
            sway = math.sin(self.backdrop_phase * 2 + index) * 10
            canvas.create_line(
                x,
                y,
                x + length,
                y + 10 + sway * 0.15,
                fill=self._fade_color(self.theme_color("line"), 0.76),
                width=1 + index % 2,
            )

    def _draw_soft_particles(self, canvas, width, height):
        count = max(20, int(max(68, int(width / 16)) * self._backdrop_density()))
        for index in range(count):
            seed = index * 91.7
            x = (seed * 11 + math.sin(self.backdrop_phase + index) * 38) % (width + 100) - 50
            y = (seed * 7 + self.backdrop_phase * (12 + index % 5)) % (height + 120) - 60
            size = 2 + index % 4
            color = self._fade_color(self.theme_color("particle") if index % 3 else self.theme_color("particle_alt"), 0.74)
            canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
            if index % 8 == 0:
                cross = self._fade_color(self.theme_color("spark"), 0.60)
                canvas.create_line(x - 7, y, x + 7, y, fill=cross)
                canvas.create_line(x, y - 7, x, y + 7, fill=cross)
        for index in range(6):
            seed = index * 23.4
            x = (seed * 41 + math.sin(self.backdrop_phase * 0.35 + index) * 80) % width
            y = (seed * 67 + math.cos(self.backdrop_phase * 0.28 + index) * 54) % height
            radius = 16 + (index % 3) * 8
            canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline=self._fade_color(self.theme_color("orbit"), 0.28),
                width=1,
            )

    def _draw_wind_field(self, canvas, width, height):
        density = math.sqrt(self._backdrop_density())
        rows = max(5, int(max(8, int(height / 92)) * density))
        cols = max(12, int(max(24, int(width / 48)) * density))
        for row in range(rows):
            for col in range(cols):
                seed = row * 17 + col * 31
                x = (col * 96 + seed * 3 + self.backdrop_phase * 54) % (width + 140) - 70
                y = row * max(height / rows, 1) + 32 + math.sin(self.backdrop_phase * 1.4 + seed) * 16
                length = 18 + (seed % 5) * 12
                canvas.create_line(x, y, x + length, y, fill=self._fade_color(self.theme_color("line"), 0.68), width=1)
                if seed % 7 == 0:
                    canvas.create_line(x + length + 8, y, x + length + 22, y, fill=self._fade_color(self.theme_color("line_alt"), 0.54), width=1)

    def _draw_constellation(self, canvas, width, height):
        points = []
        count = max(20, int(max(56, int(width / 19)) * self._backdrop_density()))
        for index in range(count):
            seed = index * 44.3
            x = (seed * 13 + math.sin(self.backdrop_phase * 0.9 + index) * 18) % width
            y = (seed * 17 + math.cos(self.backdrop_phase * 0.7 + index) * 22) % height
            points.append((x, y))
            size = 2 + (index % 3 == 0)
            color = self._fade_color(self.theme_color("spark") if index % 11 == 0 else self.theme_color("line"), 0.78)
            canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="")
        for index in range(0, len(points) - 1, 3):
            x1, y1 = points[index]
            x2, y2 = points[index + 1]
            if abs(x1 - x2) + abs(y1 - y2) < 260:
                canvas.create_line(x1, y1, x2, y2, fill=self._fade_color(self.theme_color("grid_a"), 0.50), width=1)
