import math


AVATARS = [
    {"name": "相空间", "bg": "#19243a", "accent": "#7ed6ff"},
    {"name": "光锥", "bg": "#201f3a", "accent": "#f6d36b"},
    {"name": "矩阵", "bg": "#172b2e", "accent": "#9ff2b2"},
    {"name": "波函数", "bg": "#241b32", "accent": "#f6a6ff"},
    {"name": "电磁场", "bg": "#162638", "accent": "#72d5ff"},
    {"name": "统计谱", "bg": "#2a2434", "accent": "#ffbd7e"},
    {"name": "群论环", "bg": "#1d2a25", "accent": "#7fd9c6"},
    {"name": "晶格", "bg": "#1c2438", "accent": "#9fb7ff"},
    {"name": "黑体谱", "bg": "#241f27", "accent": "#fff2bd"},
    {"name": "量子跃迁", "bg": "#172238", "accent": "#8fb6ff"},
    {"name": "泊松括号", "bg": "#20283a", "accent": "#f6d36b"},
    {"name": "希尔伯特", "bg": "#18263b", "accent": "#9ff2b2"},
    {"name": "费曼图", "bg": "#241d2f", "accent": "#ffbd7e"},
    {"name": "测地线", "bg": "#172937", "accent": "#7ed6ff"},
    {"name": "皇冠谱", "bg": "#24212e", "accent": "#fff2bd"},
]


def avatar_name(avatar_id):
    return AVATARS[avatar_id % len(AVATARS)]["name"]


def draw_avatar(canvas, avatar_id, size=64, selected=False):
    canvas.delete("all")
    avatar = AVATARS[avatar_id % len(AVATARS)]
    bg = avatar["bg"]
    accent = avatar["accent"]

    def sx(value):
        return size * value / 100

    def line(*coords, fill=None, width=2, smooth=False):
        canvas.create_line(*[sx(v) for v in coords], fill=fill or accent, width=max(1, int(width * size / 64)), smooth=smooth)

    pad = sx(7)
    outline = "#fff2bd" if selected else "#4b5877"
    canvas.create_oval(pad, pad, size - pad, size - pad, fill=bg, outline=outline, width=3 if selected else 2)
    canvas.create_oval(sx(15), sx(15), sx(85), sx(85), outline="#2f3a56", width=1)

    kind = avatar_id % len(AVATARS)
    if kind == 0:
        canvas.create_oval(sx(45), sx(45), sx(55), sx(55), fill=accent, outline="")
        canvas.create_oval(sx(23), sx(39), sx(77), sx(61), outline=accent, width=2)
        canvas.create_oval(sx(39), sx(23), sx(61), sx(77), outline="#f6a6ff", width=2)
        line(28, 72, 72, 28, fill="#9ff2b2", width=1)
    elif kind == 1:
        canvas.create_polygon(sx(50), sx(18), sx(24), sx(78), sx(76), sx(78), outline=accent, fill="", width=2)
        canvas.create_polygon(sx(50), sx(82), sx(24), sx(22), sx(76), sx(22), outline="#8fb6ff", fill="", width=2)
        line(50, 12, 50, 88, fill="#fff2bd", width=1)
        line(20, 50, 80, 50, fill="#4e5d7d", width=1)
    elif kind == 2:
        line(26, 22, 18, 22, 18, 78, 26, 78, fill="#dce6ff", width=2)
        line(74, 22, 82, 22, 82, 78, 74, 78, fill="#dce6ff", width=2)
        for row in range(3):
            for col in range(3):
                x = sx(36 + col * 14)
                y = sx(34 + row * 14)
                canvas.create_oval(x - sx(3), y - sx(3), x + sx(3), y + sx(3), fill=accent if (row + col) % 2 else "#fff2bd", outline="")
    elif kind == 3:
        points = []
        for i in range(49):
            x = 18 + i * 64 / 48
            y = 50 + math.sin(i / 48 * math.pi * 4) * 17
            points.extend([sx(x), sx(y)])
        canvas.create_line(points, fill=accent, width=3, smooth=True)
        line(17, 50, 83, 50, fill="#43506e", width=1)
        line(50, 20, 50, 80, fill="#43506e", width=1)
    elif kind == 4:
        for offset in (28, 50, 72):
            line(18, offset, 82, 100 - offset, fill="#2f8ed8", width=1, smooth=True)
            line(18, 100 - offset, 82, offset, fill="#2f8ed8", width=1, smooth=True)
        canvas.create_text(sx(36), sx(42), text="+", fill="#ff9b89", font=("Consolas", max(11, size // 4), "bold"))
        canvas.create_text(sx(64), sx(58), text="-", fill="#9ff2b2", font=("Consolas", max(11, size // 4), "bold"))
    elif kind == 5:
        bars = [20, 34, 58, 46, 28]
        for i, height in enumerate(bars):
            x1 = sx(24 + i * 11)
            canvas.create_rectangle(x1, sx(78 - height), x1 + sx(7), sx(78), fill="#ffbd7e", outline="")
        points = []
        for i in range(34):
            x = 20 + i * 60 / 33
            y = 78 - 42 * math.exp(-((x - 50) ** 2) / 280)
            points.extend([sx(x), sx(y)])
        canvas.create_line(points, fill=accent, width=2, smooth=True)
    elif kind == 6:
        nodes = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            x = 50 + math.cos(angle) * 27
            y = 50 + math.sin(angle) * 27
            nodes.append((x, y))
        for i, (x, y) in enumerate(nodes):
            nx, ny = nodes[(i + 2) % len(nodes)]
            line(x, y, nx, ny, fill="#3c786f", width=1)
        for x, y in nodes:
            canvas.create_oval(sx(x - 5), sx(y - 5), sx(x + 5), sx(y + 5), fill=accent, outline="")
    elif kind == 7:
        for row in range(3):
            for col in range(4):
                x = 28 + col * 15 + (row % 2) * 7
                y = 32 + row * 14
                canvas.create_polygon(
                    sx(x), sx(y - 7), sx(x + 6), sx(y - 3), sx(x + 6), sx(y + 4),
                    sx(x), sx(y + 8), sx(x - 6), sx(y + 4), sx(x - 6), sx(y - 3),
                    outline=accent, fill="", width=1,
                )
    elif kind == 8:
        colors = ["#6ea8ff", "#7fd9c6", "#fff2bd", "#ffbd7e", "#ff9b89"]
        for i, color in enumerate(colors):
            canvas.create_rectangle(sx(22 + i * 11), sx(67 - i * 7), sx(30 + i * 11), sx(78), fill=color, outline="")
        points = []
        for i in range(32):
            x = 18 + i * 64 / 31
            y = 72 - 46 * (i / 31) ** 2 * math.exp(2 - 2 * i / 31)
            points.extend([sx(x), sx(y)])
        canvas.create_line(points, fill=accent, width=2, smooth=True)
    elif kind == 9:
        for y in (30, 48, 68):
            line(24, y, 76, y, fill="#6c7899", width=2)
        line(38, 66, 62, 32, fill=accent, width=3)
        canvas.create_polygon(sx(62), sx(32), sx(58), sx(42), sx(68), sx(39), fill=accent, outline="")
        canvas.create_oval(sx(34), sx(62), sx(42), sx(70), fill="#fff2bd", outline="")
    elif kind == 10:
        line(22, 50, 78, 50, fill="#6c7899", width=1)
        line(50, 22, 50, 78, fill="#6c7899", width=1)
        canvas.create_text(sx(38), sx(40), text="q", fill=accent, font=("Consolas", max(10, size // 4), "bold"))
        canvas.create_text(sx(62), sx(62), text="p", fill="#9ff2b2", font=("Consolas", max(10, size // 4), "bold"))
        canvas.create_arc(sx(24), sx(28), sx(78), sx(82), start=35, extent=255, outline="#fff2bd", width=2, style="arc")
    elif kind == 11:
        for radius, color in ((34, "#3d4a69"), (24, accent), (14, "#9ff2b2")):
            canvas.create_oval(sx(50 - radius), sx(50 - radius), sx(50 + radius), sx(50 + radius), outline=color, width=2)
        line(26, 74, 74, 26, fill="#fff2bd", width=1)
        canvas.create_text(sx(50), sx(50), text="H", fill="#fff2bd", font=("Consolas", max(14, size // 3), "bold"))
    elif kind == 12:
        nodes = [(24, 30), (50, 50), (76, 30), (33, 76), (67, 76)]
        for a, b in ((0, 1), (1, 2), (1, 3), (1, 4), (3, 4)):
            line(*nodes[a], *nodes[b], fill=accent if a == 1 or b == 1 else "#6c7899", width=2)
        for index, (x, y) in enumerate(nodes):
            color = "#fff2bd" if index == 1 else ("#9ff2b2" if index % 2 else "#ff9b89")
            canvas.create_oval(sx(x - 4), sx(y - 4), sx(x + 4), sx(y + 4), fill=color, outline="")
    elif kind == 13:
        points = []
        for i in range(46):
            t = i / 45
            x = 22 + 56 * t
            y = 78 - 52 * (t ** 0.72)
            points.extend([sx(x), sx(y)])
        canvas.create_line(points, fill=accent, width=3, smooth=True)
        line(22, 78, 78, 78, fill="#5a6684", width=1)
        line(22, 78, 22, 22, fill="#5a6684", width=1)
        canvas.create_oval(sx(68), sx(26), sx(76), sx(34), fill="#fff2bd", outline="")
    else:
        crown = [(28, 68), (28, 42), (40, 54), (50, 30), (60, 54), (72, 42), (72, 68)]
        canvas.create_polygon(*[sx(v) for point in crown for v in point], outline=accent, fill="", width=2)
        for x, y in ((40, 54), (50, 30), (60, 54)):
            canvas.create_oval(sx(x - 4), sx(y - 4), sx(x + 4), sx(y + 4), fill="#fff2bd", outline="")
        line(30, 68, 70, 68, fill="#9ff2b2", width=3)
        canvas.create_text(sx(50), sx(78), text="20", fill="#fff2bd", font=("Consolas", max(10, size // 5), "bold"))

    if selected:
        canvas.create_text(sx(50), sx(92), text="✓", fill="#fff2bd", font=("Microsoft YaHei UI", max(9, size // 6), "bold"))
