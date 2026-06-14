"""Optional decorative scanline canvas."""
from __future__ import annotations

from tkinter import Canvas


class ScanlineCanvas(Canvas):
    def __init__(self, master, line_color="#101810", spacing=4, **kwargs):
        super().__init__(master, highlightthickness=0, **kwargs)
        self.line_color = line_color
        self.spacing = spacing
        self._after_id = None
        self.bind("<Configure>", self.redraw)

    def redraw(self, _event=None) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(50, self._render)

    def _render(self) -> None:
        self.delete("scanline")
        for y in range(0, self.winfo_height(), self.spacing):
            self.create_line(0, y, self.winfo_width(), y, fill=self.line_color, tags="scanline")
