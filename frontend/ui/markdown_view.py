import math
import re
import tkinter as tk


def split_mechanics_sections(content):
    quick_title = "## 简单说明"
    detail_title = "## 详细规则"
    quick_start = content.find(quick_title)
    detail_start = content.find(detail_title)
    if quick_start == -1 or detail_start == -1:
        return content, content
    quick = content[quick_start + len(quick_title):detail_start].strip()
    detail = content[detail_start + len(detail_title):].strip()
    return quick, detail


def make_scroll_frame(parent, bg="#182033"):
    shell = tk.Frame(parent, bg=bg)
    shell.pack(fill="both", expand=True)
    canvas = tk.Canvas(shell, bg=bg, bd=0, highlightthickness=0)
    scrollbar = tk.Scrollbar(shell, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def on_mousewheel(event):
        if not canvas.winfo_exists():
            return "break"
        if getattr(event, "num", None) == 4:
            amount = -3
        elif getattr(event, "num", None) == 5:
            amount = 3
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return "break"
            amount = int(-delta / 120)
            if amount == 0:
                amount = -1 if delta > 0 else 1
        canvas.yview_scroll(amount, "units")
        return "break"

    events = ("<MouseWheel>", "<Button-4>", "<Button-5>")

    def bind_all(_event=None):
        for event_name in events:
            canvas.bind_all(event_name, on_mousewheel)

    def unbind_all(_event=None):
        for event_name in events:
            canvas.unbind_all(event_name)

    shell.bind("<Enter>", bind_all, add="+")
    shell.bind("<Leave>", unbind_all, add="+")
    for widget in (shell, canvas):
        for event_name in events:
            widget.bind(event_name, on_mousewheel, add="+")
    inner._scroll_canvas = canvas
    return inner


def render_markdown(parent, content, mode="detail"):
    bg = "#182033"
    fg = "#dce6ff"
    muted = "#9ca8c7"
    accent = "#8fb6ff"
    base_size = 15 if mode == "quick" else 13
    heading_scale = 1.45 if mode == "quick" else 1.35

    inner = make_scroll_frame(parent, bg)
    lines = content.splitlines()
    index = 0
    paragraph = []

    def flush_paragraph():
        nonlocal paragraph
        if not paragraph:
            return
        text = " ".join(line.strip() for line in paragraph).strip()
        if text:
            if mode == "quick":
                text = "　　" + text
            _render_text_block(inner, text, base_size, fg=fg, bg=bg, padx=28, pady=(3, 11))
        paragraph = []

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index].rstrip())
                index += 1
            _render_code(inner, "\n".join(code_lines), base_size)
            index += 1
            continue
        if _is_table_start(lines, index):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            _render_table(inner, table_lines, base_size)
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            size = max(base_size + 1, int(base_size * heading_scale) - (level - 1) * 2)
            color = "#fff2bd" if level <= 2 else accent
            tk.Label(
                inner,
                text=title,
                fg=color,
                bg=bg,
                font=("Microsoft YaHei UI", size, "bold"),
            ).pack(anchor="w", padx=28, pady=(16 if level <= 2 else 10, 6))
            index += 1
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            _render_text_block(inner, "• " + stripped[2:], base_size, fg=fg, bg=bg, padx=42, pady=4)
            index += 1
            continue
        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    tk.Label(inner, text="", fg=muted, bg=bg, font=("Microsoft YaHei UI", 2)).pack(pady=8)
    return inner


def _render_text_block(parent, text, base_size, fg="#dce6ff", bg="#182033", padx=22, pady=(2, 8), bold=False):
    widget = tk.Text(
        parent,
        height=1,
        width=1,
        wrap="word",
        fg=fg,
        bg=bg,
        relief="flat",
        bd=0,
        highlightthickness=0,
        insertbackground=fg,
        padx=0,
        pady=0,
        font=("Microsoft YaHei UI", base_size, "bold" if bold else "normal"),
        spacing1=0,
        spacing2=1,
        spacing3=2,
        cursor="arrow",
    )
    widget.pack(anchor="w", fill="x", padx=padx, pady=pady)
    widget.tag_configure("bold", font=("Microsoft YaHei UI", base_size, "bold"), foreground=fg)
    widget.tag_configure("code", font=("Consolas", max(11, base_size)), foreground="#9ff2b2", background="#101827")
    widget.tag_configure("math", font=("Microsoft YaHei UI", base_size, "bold" if bold else "normal"), foreground="#fff2bd", background=bg)
    widget.tag_configure("muted", foreground="#9ca8c7")
    _insert_inline_segments(widget, text)
    _tag_formula_like_spans(widget, _plain_inline_text(text))
    widget.configure(state="disabled")
    _bind_auto_text_height(widget)
    return widget


def _bind_auto_text_height(widget):
    def cancel_pending():
        pending = getattr(widget, "_auto_text_height_after", None)
        if pending:
            try:
                widget.after_cancel(pending)
            except tk.TclError:
                pass
            widget._auto_text_height_after = None

    def schedule(delay=None):
        try:
            if not widget.winfo_exists():
                return
        except tk.TclError:
            return
        cancel_pending()
        try:
            if delay is None:
                widget._auto_text_height_after = widget.after_idle(update_height)
            else:
                widget._auto_text_height_after = widget.after(delay, update_height)
        except tk.TclError:
            pass

    def update_height():
        widget._auto_text_height_after = None
        if not widget.winfo_exists():
            return
        if widget.winfo_width() <= 20:
            schedule(30)
            return
        try:
            count = widget.count("1.0", "end-1c", "displaylines")
        except tk.TclError:
            return
        if not count:
            return
        extra = 1 if count[0] > 1 else 0
        desired = max(1, int(count[0]) + extra)
        if str(widget.cget("height")) != str(desired):
            widget.configure(height=desired)

    def on_destroy(event):
        if event.widget is widget:
            cancel_pending()

    widget.bind("<Configure>", lambda _event: schedule(), add="+")
    widget.bind("<Destroy>", on_destroy, add="+")
    schedule()


def render_inline_markdown(
    parent,
    content,
    fg="#dce6ff",
    bg="#182033",
    base_size=12,
    bold=False,
    wrap_chars=58,
    padx=0,
    pady=0,
    fill="x",
):
    """Render a short Markdown-ish line with inline code/math styling."""
    text = str(content or "")
    plain = _plain_inline_text(text)
    height = max(1, min(6, math.ceil(_display_width(plain) / max(12, wrap_chars))))
    widget = tk.Text(
        parent,
        height=height,
        width=1,
        wrap="word",
        fg=fg,
        bg=bg,
        relief="flat",
        bd=0,
        highlightthickness=0,
        insertbackground=fg,
        padx=0,
        pady=0,
        font=("Microsoft YaHei UI", base_size, "bold" if bold else "normal"),
        spacing1=1,
        spacing2=1,
        spacing3=2,
    )
    widget.pack(anchor="w", fill=fill, padx=padx, pady=pady)
    widget.tag_configure("bold", font=("Microsoft YaHei UI", base_size, "bold"), foreground=fg)
    widget.tag_configure("code", font=("Consolas", max(9, base_size)), foreground="#9ff2b2", background="#101827")
    widget.tag_configure("math", font=("Microsoft YaHei UI", base_size, "bold" if bold else "normal"), foreground="#fff2bd", background=bg)
    widget.tag_configure("muted", foreground="#9ca8c7")
    _insert_inline_segments(widget, text)
    _tag_formula_like_spans(widget, plain)
    widget.configure(state="disabled", cursor="")
    _bind_auto_text_height(widget)
    return widget


def _inline_text(text):
    return text.replace("`", "").replace("**", "")


def _plain_inline_text(text):
    text = str(text or "")
    result = []
    index = 0
    while index < len(text):
        marker = _next_inline_marker(text, index)
        if marker is None:
            result.append(_render_loose_latex_text(text[index:]))
            break
        start, end, tag, body = marker
        result.append(_render_loose_latex_text(text[index:start]))
        result.append(_render_latex_math(body) if tag == "math" else _render_inline_body(tag, body))
        index = end
    return "".join(result)


def _insert_inline_segments(widget, text):
    index = 0
    while index < len(text):
        marker = _next_inline_marker(text, index)
        if marker is None:
            widget.insert("end-1c", _render_loose_latex_text(text[index:]))
            break
        start, end, tag, body = marker
        if start > index:
            widget.insert("end-1c", _render_loose_latex_text(text[index:start]))
        widget.insert("end-1c", _render_latex_math(body) if tag == "math" else _render_inline_body(tag, body), (tag,))
        index = end


def _next_inline_marker(text, start_index):
    candidates = []
    for opener, closer, tag in (
        ("**", "**", "bold"),
        ("`", "`", "code"),
        ("\\(", "\\)", "math"),
        ("\\[", "\\]", "math"),
        ("$", "$", "math"),
    ):
        start = text.find(opener, start_index)
        if start == -1:
            continue
        body_start = start + len(opener)
        end = text.find(closer, body_start)
        if end == -1:
            continue
        body = text[body_start:end]
        if body:
            candidates.append((start, end + len(closer), tag, body))
    return min(candidates, key=lambda item: item[0]) if candidates else None


def _render_inline_body(tag, body):
    if tag == "code":
        return body
    return _render_loose_latex_text(body)


LATEX_SYMBOLS = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "varepsilon": "ε",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "vartheta": "ϑ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "varphi": "φ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "ell": "ℓ",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Xi": "Ξ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Phi": "Φ",
    "Psi": "Ψ",
    "Omega": "Ω",
    "nabla": "∇",
    "partial": "∂",
    "infty": "∞",
    "times": "×",
    "cdot": "·",
    "pm": "±",
    "mp": "∓",
    "le": "≤",
    "leq": "≤",
    "ge": "≥",
    "geq": "≥",
    "neq": "≠",
    "approx": "≈",
    "sim": "∼",
    "propto": "∝",
    "to": "→",
    "rightarrow": "→",
    "leftarrow": "←",
    "leftrightarrow": "↔",
    "Rightarrow": "⇒",
    "Leftarrow": "⇐",
    "int": "∫",
    "oint": "∮",
    "sum": "∑",
    "prod": "∏",
    "sqrt": "√",
    "langle": "⟨",
    "rangle": "⟩",
    "lvert": "|",
    "rvert": "|",
    "lVert": "‖",
    "rVert": "‖",
    "prime": "′",
    "forall": "∀",
    "exists": "∃",
    "in": "∈",
    "notin": "∉",
}

SUPERSCRIPT_MAP = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ",
    "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ",
    "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ", "A": "ᴬ", "B": "ᴮ", "D": "ᴰ", "E": "ᴱ", "G": "ᴳ",
    "H": "ᴴ", "I": "ᴵ", "J": "ᴶ", "K": "ᴷ", "L": "ᴸ", "M": "ᴹ", "N": "ᴺ", "O": "ᴼ", "P": "ᴾ", "R": "ᴿ",
    "T": "ᵀ", "U": "ᵁ", "V": "ⱽ", "W": "ᵂ",
})
SUBSCRIPT_MAP = str.maketrans({
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
    "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "x": "ₓ",
})


def _render_latex_math(expr):
    text = str(expr or "").strip()
    if not text:
        return ""
    text = _replace_common_latex(text)
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    text = _replace_scripts(text)
    text = text.replace("{", "").replace("}", "")
    return _normalize_math_spacing(text)


def _render_loose_latex_text(text):
    text = str(text or "")
    if "\\" not in text:
        return text
    rendered = _replace_common_latex(text)
    rendered = re.sub(r"\\([A-Za-z]+)", r"\1", rendered)
    rendered = _replace_scripts(rendered)
    rendered = rendered.replace("{", "").replace("}", "")
    return _normalize_math_spacing(rendered)


def _replace_common_latex(text):
    text = str(text or "").replace("\\\\", "\\")
    text = _replace_latex_groups(text, "frac", lambda parts: f"({parts[0]})/({parts[1]})", arg_count=2)
    text = _replace_latex_groups(text, "sqrt", lambda parts: f"√({parts[0]})", arg_count=1)
    text = _replace_latex_groups(text, "hat", lambda parts: f"{parts[0]}̂", arg_count=1)
    text = _replace_latex_groups(text, "bar", lambda parts: f"{parts[0]}̄", arg_count=1)
    text = _replace_latex_groups(text, "vec", lambda parts: f"{parts[0]}⃗", arg_count=1)
    for command in ("mathbf", "mathrm", "mathit", "mathcal", "mathbb", "operatorname", "text", "boldsymbol"):
        text = _replace_latex_groups(text, command, lambda parts: parts[0], arg_count=1)
        text = re.sub(rf"\\{command}\s*\\([A-Za-z]+)", r"\\\1", text)
        text = re.sub(rf"\\{command}\s+([A-Za-zΑ-ω]+)", r"\1", text)
    text = _replace_latex_over(text)
    text = re.sub(r"\\rm\s+([A-Za-zΑ-ω]+)", r"\1", text)
    for command in ("left", "right"):
        text = text.replace(f"\\{command}", "")
    text = text.replace("\\,", " ").replace("\\;", " ").replace("\\:", " ").replace("\\!", "")
    text = text.replace("\\quad", " ").replace("\\qquad", "  ")
    return _replace_latex_symbols(text)


def _replace_latex_symbols(text):
    commands = sorted(LATEX_SYMBOLS, key=len, reverse=True)
    result = []
    index = 0
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text) and text[index + 1].isalpha():
            end = index + 1
            while end < len(text) and text[end].isalpha():
                end += 1
            command = text[index + 1:end]
            matched = next((name for name in commands if command.startswith(name)), None)
            if matched:
                result.append(LATEX_SYMBOLS[matched])
                result.append(command[len(matched):])
            else:
                result.append(command)
            index = end
            continue
        result.append(text[index])
        index += 1
    return "".join(result)


def _replace_latex_over(text):
    pattern = re.compile(r"\{([^{}]+?)\\over([^{}]+?)\}")
    while True:
        text, count = pattern.subn(
            lambda match: f"({_render_latex_math(match.group(1))})/({_render_latex_math(match.group(2))})",
            text,
        )
        if not count:
            return text


def _normalize_math_spacing(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(r"\s*([=+\-*/<>×·≈∼≤≥≠→←↔⇒⇐∝])\s*", r"\1", text)
    return text


def _replace_latex_groups(text, command, formatter, arg_count=1):
    pattern = f"\\{command}"
    index = 0
    result = []
    while True:
        start = text.find(pattern, index)
        if start == -1:
            result.append(text[index:])
            break
        result.append(text[index:start])
        pos = start + len(pattern)
        parts = []
        ok = True
        for _ in range(arg_count):
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text) or text[pos] != "{":
                ok = False
                break
            body, pos = _read_braced_group(text, pos)
            if body is None:
                ok = False
                break
            parts.append(_render_latex_math(body))
        if ok:
            result.append(formatter(parts))
            index = pos
        else:
            result.append(text[start:pos])
            index = pos
    return "".join(result)


def _read_braced_group(text, start):
    if start >= len(text) or text[start] != "{":
        return None, start
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
    return None, start


def _replace_scripts(text):
    result = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in {"^", "_"} and index + 1 < len(text):
            marker = char
            index += 1
            if text[index] == "{":
                body, new_index = _read_braced_group(text, index)
                if body is None:
                    result.append(marker)
                    continue
                index = new_index
            else:
                body = text[index]
                index += 1
            rendered = _render_latex_math(body)
            translated = _translate_script(rendered, SUPERSCRIPT_MAP if marker == "^" else SUBSCRIPT_MAP)
            if translated is None:
                result.append(f"{marker}({rendered})")
            else:
                result.append(translated)
            continue
        result.append(char)
        index += 1
    return "".join(result)


def _translate_script(text, table):
    translated = text.translate(table)
    if any(original == converted and not original.isspace() for original, converted in zip(text, translated)):
        return None
    return translated


_FORMULA_TOKEN_RE = re.compile(
    r"[A-Za-z0-9Α-ω_{}()<>|.,+\-*/=^²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉∮∫∇∂ΣΔδωΩψΨχΧφΦθΘλΛνμρπΠαβγδεε₀·×≈∼≤≥≠∞∝→←↔⇒⇐±∓√]+"
)
_FORMULA_MARKERS = set("=<>^_+-*/·×≈∼≤≥≠∞∝→←↔⇒⇐±∓√∮∫∇∂ΣΔδωΩψΨχΧφΦθΘλΛνμρπΠαβγδεε₀²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉|")


def _tag_formula_like_spans(widget, plain):
    for match in _FORMULA_TOKEN_RE.finditer(plain):
        token = match.group(0).strip(".,")
        if len(token) < 2:
            continue
        if not any(char in _FORMULA_MARKERS for char in token):
            continue
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        widget.tag_add("math", start, end)


def _display_width(text):
    width = 0
    for char in str(text or ""):
        width += 2 if "\u4e00" <= char <= "\u9fff" else 1
    return width


def _is_table_start(lines, index):
    if index + 1 >= len(lines):
        return False
    current = lines[index].strip()
    next_line = lines[index + 1].strip()
    return current.startswith("|") and next_line.startswith("|") and "---" in next_line


def _parse_table_line(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells):
    return all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells)


def _render_table(parent, table_lines, base_size):
    rows = []
    for line in table_lines:
        cells = _parse_table_line(line)
        if _is_separator_row(cells):
            continue
        rows.append(cells)
    if not rows:
        return
    table = tk.Frame(parent, bg="#233049", highlightbackground="#3b4560", highlightthickness=1)
    table.pack(anchor="w", fill="x", padx=28, pady=(4, 12))
    max_cols = max(len(row) for row in rows)
    col_weights = []
    for col in range(max_cols):
        max_width = max((_display_width(row[col]) if col < len(row) else 0) for row in rows)
        col_weights.append(max(8, min(48, max_width)))
        table.grid_columnconfigure(col, weight=col_weights[-1], uniform="")
    cells = []
    for row_index, row in enumerate(rows):
        for col_index in range(max_cols):
            text = row[col_index] if col_index < len(row) else ""
            is_header = row_index == 0
            label = tk.Label(
                table,
                text=_inline_text(text),
                fg="#fff2bd" if is_header else "#dce6ff",
                bg="#26344f" if is_header else "#182033",
                font=("Microsoft YaHei UI", max(8, base_size - 1), "bold" if is_header else "normal"),
                wraplength=260,
                justify="center",
                anchor="center",
                padx=8,
                pady=6,
                highlightbackground="#30384e",
                highlightthickness=1,
            )
            label.grid(row=row_index, column=col_index, sticky="nsew")
            cells.append((label, col_index))

    def update_wraps(_event=None):
        for label, col_index in cells:
            width = max(72, table.grid_bbox(col_index, 0)[2] - 18)
            label.configure(wraplength=width)

    table.bind("<Configure>", update_wraps)
    table.after_idle(update_wraps)


def _render_code(parent, code, base_size):
    block = tk.Label(
        parent,
        text=code,
        fg="#9ff2b2",
        bg="#101827",
        justify="left",
        anchor="w",
        font=("Consolas", max(11, base_size - 1)),
        padx=14,
        pady=10,
        wraplength=900,
    )
    block.pack(anchor="w", fill="x", padx=28, pady=(4, 12))
    block.bind("<Configure>", lambda event: block.configure(wraplength=max(260, event.width - 28)))
