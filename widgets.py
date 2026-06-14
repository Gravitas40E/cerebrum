"""Reusable tkinter widgets."""
from __future__ import annotations

from tkinter import Button, Canvas, Frame, Scrollbar


class GlowButton(Button):
    def __init__(self, master, glow_color="#ffb400", hover_bg="#111111", **kwargs):
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("bd", 0)
        super().__init__(master, **kwargs)
        self._normal_fg = self.cget("fg")
        self._normal_bg = self.cget("bg")
        self._glow_color = glow_color
        self._hover_bg = hover_bg
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")

    def _enter(self, _event) -> None:
        self.configure(fg=self._glow_color, bg=self._hover_bg)

    def _leave(self, _event) -> None:
        self.configure(fg=self._normal_fg, bg=self._normal_bg)


class ScrollFrame(Frame):
    def __init__(self, master, bg="#0d0d0d", **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self.canvas = Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = Scrollbar(self, command=self.canvas.yview)
        self.inner = Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self._window, width=event.width),
        )
