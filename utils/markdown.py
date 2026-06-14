"""Small, predictable Markdown helpers for the tkinter preview."""
from __future__ import annotations

import re
from tkinter import Text

INLINE_RE = re.compile(
    r"(\*\*(.+?)\*\*|~~(.+?)~~|`(.+?)`|\*([^*]+?)\*|\[([^\]]+)\]\(([^)]+)\))"
)


def strip_markdown(text: str) -> str:
    value = text
    value = re.sub(r"```.*?```", "", value, flags=re.DOTALL)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"(\*\*|__|~~|`)", "", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*", r"\1", value)
    value = re.sub(
        r"^[ \t]{0,3}(#{1,6}|>|[-*+]|\d+\.)[ \t]+",
        "",
        value,
        flags=re.MULTILINE,
    )
    value = re.sub(r"^[ \t]*---+[ \t]*$", "", value, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def parse_md(text: str) -> str:
    """Compatibility helper returning readable plain text."""
    return strip_markdown(text)


def configure_preview_tags(widget: Text, font_family: str) -> None:
    widget.tag_configure("h1", foreground="#ffb400", font=(font_family, 16, "bold"), spacing1=8, spacing3=5)
    widget.tag_configure("h2", foreground="#40e0ff", font=(font_family, 13, "bold"), spacing1=7, spacing3=4)
    widget.tag_configure("h3", foreground="#c084fc", font=(font_family, 11, "bold"), spacing1=6, spacing3=3)
    widget.tag_configure("bold", foreground="#c8ffc8", font=(font_family, 10, "bold"))
    widget.tag_configure("italic", foreground="#8fcf8f", font=(font_family, 10, "italic"))
    widget.tag_configure("strike", foreground="#6d9b6d", overstrike=True)
    widget.tag_configure("code", foreground="#40e0ff", background="#111111")
    widget.tag_configure("quote", foreground="#6d9b6d", lmargin1=14, lmargin2=14)
    widget.tag_configure("bullet", foreground="#ffb400", lmargin1=8, lmargin2=20)
    widget.tag_configure("link", foreground="#40e0ff", underline=True)
    widget.tag_configure("rule", foreground="#2d3d2d")


def render_markdown(widget: Text, text: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    in_code_block = False
    for raw in text.splitlines():
        if raw.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            widget.insert("end", raw + "\n", "code")
            continue
        if re.match(r"^\s*---+\s*$", raw):
            widget.insert("end", "-" * 36 + "\n", "rule")
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", raw)
        if heading:
            tag = "h1" if len(heading.group(1)) == 1 else "h2" if len(heading.group(1)) == 2 else "h3"
            _insert_inline(widget, heading.group(2), tag)
            widget.insert("end", "\n")
            continue
        quote = re.match(r"^>\s?(.*)$", raw)
        if quote:
            widget.insert("end", "| ", "quote")
            _insert_inline(widget, quote.group(1), "quote")
            widget.insert("end", "\n")
            continue
        bullet = re.match(r"^\s*[-*+]\s+(.+)$", raw)
        if bullet:
            widget.insert("end", "- ", "bullet")
            _insert_inline(widget, bullet.group(1))
            widget.insert("end", "\n")
            continue
        _insert_inline(widget, raw)
        widget.insert("end", "\n")
    widget.configure(state="disabled")


def _insert_inline(widget: Text, text: str, base_tag: str | None = None) -> None:
    cursor = 0
    for match in INLINE_RE.finditer(text):
        if match.start() > cursor:
            widget.insert("end", text[cursor:match.start()], base_tag or ())
        token = match.group(0)
        if token.startswith("**"):
            widget.insert("end", match.group(2), (base_tag, "bold") if base_tag else "bold")
        elif token.startswith("~~"):
            widget.insert("end", match.group(3), (base_tag, "strike") if base_tag else "strike")
        elif token.startswith("`"):
            widget.insert("end", match.group(4), (base_tag, "code") if base_tag else "code")
        elif token.startswith("*"):
            widget.insert("end", match.group(5), (base_tag, "italic") if base_tag else "italic")
        else:
            widget.insert("end", match.group(6), (base_tag, "link") if base_tag else "link")
        cursor = match.end()
    if cursor < len(text):
        widget.insert("end", text[cursor:], base_tag or ())
