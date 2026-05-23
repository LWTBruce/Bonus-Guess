import math
import random
import tkinter as tk


class BackdropMixin:
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

    def _start_backdrop(self, style, parent=None):
        if parent is None:
            parent = self.container
        self.backdrop_style = style
        self.backdrop_phase = random.random() * 100
        self.backdrop_canvas = tk.Canvas(
            parent,
            bd=0,
            highlightthickness=0,
            bg="#111725",
        )
        self.backdrop_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.backdrop_canvas.tk.call("lower", self.backdrop_canvas._w)
        self._animate_backdrop()

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
        self.backdrop_phase += 0.024 * self._backdrop_speed()
        self.backdrop_job = self.after(70, self._animate_backdrop)

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
            canvas.create_line(x1, y1, x2, y2, fill="#1d2a40", width=1)
            x3, y3 = rotate(cx + offset, cy - extent)
            x4, y4 = rotate(cx + offset, cy + extent)
            canvas.create_line(x3, y3, x4, y4, fill="#1a2639", width=1)

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
                fill="#22324c",
                width=1 + index % 2,
            )

    def _draw_soft_particles(self, canvas, width, height):
        count = max(20, int(max(68, int(width / 16)) * self._backdrop_density()))
        for index in range(count):
            seed = index * 91.7
            x = (seed * 11 + math.sin(self.backdrop_phase + index) * 38) % (width + 100) - 50
            y = (seed * 7 + self.backdrop_phase * (12 + index % 5)) % (height + 120) - 60
            size = 2 + index % 4
            color = "#243451" if index % 3 else "#2b3150"
            canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
            if index % 8 == 0:
                canvas.create_line(x - 7, y, x + 7, y, fill="#263a58")
                canvas.create_line(x, y - 7, x, y + 7, fill="#263a58")

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
                canvas.create_line(x, y, x + length, y, fill="#1d2c44", width=1)
                if seed % 7 == 0:
                    canvas.create_line(x + length + 8, y, x + length + 22, y, fill="#233754", width=1)

    def _draw_constellation(self, canvas, width, height):
        points = []
        count = max(20, int(max(56, int(width / 19)) * self._backdrop_density()))
        for index in range(count):
            seed = index * 44.3
            x = (seed * 13 + math.sin(self.backdrop_phase * 0.9 + index) * 18) % width
            y = (seed * 17 + math.cos(self.backdrop_phase * 0.7 + index) * 22) % height
            points.append((x, y))
            canvas.create_rectangle(x, y, x + 3, y + 3, fill="#273756", outline="")
        for index in range(0, len(points) - 1, 3):
            x1, y1 = points[index]
            x2, y2 = points[index + 1]
            if abs(x1 - x2) + abs(y1 - y2) < 260:
                canvas.create_line(x1, y1, x2, y2, fill="#1e2c45", width=1)
