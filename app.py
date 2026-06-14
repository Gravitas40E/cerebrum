"""Cerebrum desktop application using the Wenrexa sci-fi UI pack."""
from __future__ import annotations

import ctypes
import datetime as dt
import sys
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    X,
    Y,
    Button,
    Entry,
    Frame,
    Label,
    Menu,
    Scrollbar,
    StringVar,
    Text,
    Tk,
    Toplevel,
    messagebox,
    simpledialog,
)

from PIL import Image, ImageTk

from database.manager import Database
from services.data_service import FolderService, NoteService

ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
PACK_DIR = ASSETS_DIR / "Assets Wenrexa UI Sci-Fi Minimalism #01"
ELEMENTS_DIR = PACK_DIR / "Elements"
GAME_DIR = PACK_DIR / "Main Game(Example)"
COMMON_DIR = next(
    (path for path in PACK_DIR.iterdir() if path.is_dir() and (path / "Background.jpg").exists()),
    PACK_DIR,
)
FONT_DIR = ASSETS_DIR / "XTypewriter_Font_0_96" / "TrueType (.ttf)"
FONT_PATHS = (
    FONT_DIR / "XTypewriter-Regular.ttf",
    FONT_DIR / "XTypewriter-Bold.ttf",
)

BG = "#081016"
PANEL = "#0b151d"
PANEL_ALT = "#101d26"
FIELD = "#071017"
BORDER = "#4a8491"
CYAN = "#7ad7df"
CYAN_BRIGHT = "#b8fbff"
MUTED = "#5d7a82"
WHITE = "#e5f9fa"
RED = "#ef7d7d"
FONT_FAMILY = "X Typewriter"


def register_font() -> str:
    """Register the X Typewriter faces privately on Windows."""
    available = [path for path in FONT_PATHS if path.exists()]
    if sys.platform == "win32" and available:
        try:
            for path in available:
                ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)
            return FONT_FAMILY
        except (AttributeError, OSError):
            pass
    return FONT_FAMILY if available else "Segoe UI"


class ImageLibrary:
    """Loads and resizes pack assets while retaining Tk image references."""

    def __init__(self):
        self._source: dict[Path, Image.Image] = {}
        self._tk: dict[tuple[Path, tuple[int, int]], ImageTk.PhotoImage] = {}

    def get(self, path: Path, size: tuple[int, int] | None = None) -> ImageTk.PhotoImage:
        if path not in self._source:
            self._source[path] = Image.open(path).convert("RGBA")
        source = self._source[path]
        target_size = size or source.size
        key = (path, target_size)
        if key not in self._tk:
            image = source if source.size == target_size else source.resize(target_size, Image.Resampling.LANCZOS)
            self._tk[key] = ImageTk.PhotoImage(image)
        return self._tk[key]


class ScrollFrame(Frame):
    def __init__(self, master, bg=PANEL, **kwargs):
        from tkinter import Canvas

        super().__init__(master, bg=bg, **kwargs)
        self.canvas = Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = Scrollbar(
            self, command=self.canvas.yview, width=9,
            bg=PANEL_ALT, troughcolor=FIELD, activebackground=CYAN,
        )
        self.inner = Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.inner.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.window, width=event.width),
        )
        self.canvas.bind_all("<MouseWheel>", self._wheel)

    def _wheel(self, event) -> None:
        pointer = self.winfo_containing(event.x_root, event.y_root)
        if pointer and str(pointer).startswith(str(self)):
            self.canvas.yview_scroll(int(-event.delta / 120), "units")


class MainApp:
    def __init__(self, root: Tk | None = None, db: Database | None = None):
        self.font = register_font()
        self.root = root or Tk()
        self.db = db or Database()
        self.notes = NoteService(self.db)
        self.folders = FolderService(self.db)
        self.images = ImageLibrary()

        self.note_id: int | None = None
        self.current_view: str | int = "all"
        self.save_job: str | None = None
        self.loading_note = False
        self.background_job: str | None = None

        self.root.title("CEREBRUM")
        self.root.geometry("1440x860")
        self.root.minsize(1050, 650)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_background()
        self._build_shell()
        self._bind_shortcuts()

    def _build_background(self) -> None:
        self.background = Label(self.root, bd=0)
        self.background.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.bind("<Configure>", self._schedule_background)

    def _schedule_background(self, _event=None) -> None:
        if self.background_job:
            self.root.after_cancel(self.background_job)
        self.background_job = self.root.after(80, self._render_background)

    def _render_background(self) -> None:
        width = max(self.root.winfo_width(), 1050)
        height = max(self.root.winfo_height(), 650)
        image = self.images.get(COMMON_DIR / "Background.jpg", (width, height))
        self.background.configure(image=image)
        self.background.lower()

    def _build_shell(self) -> None:
        shell = Frame(self.root, bg=BG, highlightthickness=1, highlightbackground="#19323d")
        shell.place(relx=0.025, rely=0.035, relwidth=0.95, relheight=0.93)
        shell.grid_rowconfigure(1, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        self._build_topbar(shell)
        body = Frame(shell, bg=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(2, weight=1)

        self._build_navigation(body)
        self._build_note_list(body)
        self._build_editor(body)

    def _build_topbar(self, master) -> None:
        top = Frame(master, bg=BG, height=86)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        menu_image = self.images.get(COMMON_DIR / "TopMenu.png", (880, 82))
        menu = Label(top, image=menu_image, bg=BG, bd=0)
        menu.place(relx=0.5, rely=0, anchor="n")

        logo_image = self.images.get(GAME_DIR / "Logo.png", (70, 74))
        Label(top, image=logo_image, bg=BG, bd=0).pack(side=LEFT, padx=(18, 4))
        title = Frame(top, bg=BG)
        title.pack(side=LEFT, pady=13)
        Label(
            title, text="CEREBRUM", bg=BG, fg=CYAN_BRIGHT,
            font=(self.font, 23),
        ).pack(anchor="w")
        Label(
            title, text="KNOWLEDGE ARCHIVE", bg=BG, fg=MUTED,
            font=(self.font, 9),
        ).pack(anchor="w")

        actions = Frame(top, bg=BG)
        actions.pack(side=RIGHT, padx=18, pady=18)
        self._image_button(actions, "NEW NOTE", self.new_note, 1).pack(side=LEFT, padx=3)
        self._image_button(actions, "DAILY LOG", self.open_daily_log, 2).pack(side=LEFT, padx=3)
        self._image_button(actions, "CAPTURE", self.quick_capture, 3).pack(side=LEFT, padx=3)

    def _build_navigation(self, master) -> None:
        nav = Frame(
            master, bg=PANEL, width=235,
            highlightthickness=1, highlightbackground=BORDER,
        )
        nav.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        nav.grid_propagate(False)
        nav.grid_rowconfigure(5, weight=1)
        nav.grid_columnconfigure(0, weight=1)

        self._panel_heading(nav, "ARCHIVES").grid(row=0, column=0, sticky="ew", padx=7, pady=(7, 8))

        self.search_var = StringVar()
        self.search_entry = Entry(
            nav, textvariable=self.search_var, bg=FIELD, fg=WHITE,
            insertbackground=CYAN, relief="flat", font=(self.font, 10),
            highlightthickness=1, highlightbackground="#2c5964",
            highlightcolor=CYAN,
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=10, ipady=7)
        self.search_var.trace_add("write", lambda *_args: self.search())

        primary = Frame(nav, bg=PANEL)
        primary.grid(row=2, column=0, sticky="ew", padx=7, pady=8)
        for label, view in (
            ("ALL NOTES", "all"),
            ("PINNED", "pinned"),
            ("FAVORITES", "favorites"),
            ("BRAIN VAULT", "vault"),
            ("ARCHIVE", "archive"),
        ):
            self._nav_button(primary, label, lambda key=view: self.set_view(key)).pack(fill=X, pady=2)

        folder_head = Frame(nav, bg=PANEL)
        folder_head.grid(row=3, column=0, sticky="ew", padx=10, pady=(8, 2))
        Label(
            folder_head, text="FOLDERS", bg=PANEL, fg=CYAN,
            font=(self.font, 11),
        ).pack(side=LEFT)
        self._small_button(folder_head, "+", self.add_folder).pack(side=RIGHT)

        self.folder_frame = ScrollFrame(nav, bg=PANEL)
        self.folder_frame.grid(row=5, column=0, sticky="nsew", padx=6, pady=(0, 8))

        self.status_label = Label(
            nav, text="", bg=PANEL, fg=MUTED, anchor="w",
            font=(self.font, 8),
        )
        self.status_label.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 8))

    def _build_note_list(self, master) -> None:
        panel = Frame(
            master, bg=PANEL, width=320,
            highlightthickness=1, highlightbackground=BORDER,
        )
        panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=(0, 10))
        panel.grid_propagate(False)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        self.list_title = self._panel_heading(panel, "ALL NOTES")
        self.list_title.grid(row=0, column=0, sticky="ew", padx=7, pady=7)
        self.note_list = ScrollFrame(panel, bg=PANEL)
        self.note_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

    def _build_editor(self, master) -> None:
        editor_panel = Frame(
            master, bg=PANEL,
            highlightthickness=1, highlightbackground=BORDER,
        )
        editor_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=(0, 10))
        editor_panel.grid_rowconfigure(3, weight=1)
        editor_panel.grid_columnconfigure(0, weight=1)

        header = Frame(editor_panel, bg=PANEL, height=72)
        header.grid(row=0, column=0, sticky="ew", padx=7, pady=(7, 0))
        header.grid_propagate(False)
        header_image = self.images.get(ELEMENTS_DIR / "BlockInformation.png", (1000, 70))
        Label(header, image=header_image, bg=PANEL, bd=0).place(relx=0, rely=0, relwidth=1, relheight=1)

        self.title_var = StringVar()
        self.title_var.trace_add("write", lambda *_args: self.schedule_save())
        self.title_entry = Entry(
            header, textvariable=self.title_var, bg="#0c151c", fg=CYAN_BRIGHT,
            insertbackground=CYAN, relief="flat", font=(self.font, 19),
            highlightthickness=0,
        )
        self.title_entry.place(relx=0.035, rely=0.17, relwidth=0.68, relheight=0.55)

        self.save_label = Label(
            header, text="", bg="#0c151c", fg=CYAN,
            font=(self.font, 9),
        )
        self.save_label.place(relx=0.75, rely=0.30, relwidth=0.12)
        self.word_label = Label(
            header, text="0 WORDS", bg="#0c151c", fg=MUTED,
            font=(self.font, 9),
        )
        self.word_label.place(relx=0.87, rely=0.30, relwidth=0.1)

        tools = Frame(editor_panel, bg=PANEL)
        tools.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        for icon, label, callback in (
            (4, "PIN", self.toggle_pin),
            (5, "FAVORITE", self.toggle_favorite),
            (6, "VAULT", self.toggle_vault),
            (7, "MOVE", self.move_note),
            (8, "ARCHIVE", self.toggle_archive),
            (9, "DELETE", self.delete_note),
        ):
            self._tool_button(tools, icon, label, callback).pack(side=LEFT, padx=(0, 5))

        tag_row = Frame(editor_panel, bg=PANEL)
        tag_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 5))
        Label(
            tag_row, text="TAGS", bg=PANEL, fg=CYAN,
            font=(self.font, 9),
        ).pack(side=LEFT, padx=(0, 8))
        self.tags_var = StringVar()
        self.tags_var.trace_add("write", lambda *_args: self.schedule_save())
        self.tags_entry = Entry(
            tag_row, textvariable=self.tags_var, bg=FIELD, fg=WHITE,
            insertbackground=CYAN, relief="flat", font=(self.font, 9),
            highlightthickness=1, highlightbackground="#2c5964",
        )
        self.tags_entry.pack(side=LEFT, fill=X, expand=True, ipady=5)

        text_shell = Frame(
            editor_panel, bg=FIELD,
            highlightthickness=1, highlightbackground="#2c5964",
        )
        text_shell.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        text_shell.grid_rowconfigure(0, weight=1)
        text_shell.grid_columnconfigure(0, weight=1)

        self.editor = Text(
            text_shell, bg=FIELD, fg=WHITE, insertbackground=CYAN_BRIGHT,
            selectbackground="#276372", selectforeground=WHITE,
            relief="flat", wrap="word", undo=True,
            font=(self.font, 12), padx=18, pady=16, spacing1=2, spacing3=2,
        )
        self.editor.grid(row=0, column=0, sticky="nsew")
        scrollbar = Scrollbar(
            text_shell, command=self.editor.yview, width=10,
            bg=PANEL_ALT, troughcolor=FIELD, activebackground=CYAN,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.editor.configure(yscrollcommand=scrollbar.set)
        self.editor.bind("<KeyRelease>", lambda _event: self.editor_changed())
        self.editor.bind("<Tab>", self.insert_spaces)

    def _panel_heading(self, master, text: str) -> Label:
        image = self.images.get(ELEMENTS_DIR / "PanelTitleSettings.png", (500, 38))
        return Label(
            master, text=text, image=image, compound="center",
            bg=PANEL, fg=CYAN_BRIGHT, font=(self.font, 11), bd=0,
        )

    def _image_button(self, master, text: str, command, variant: int = 1) -> Button:
        path = GAME_DIR / f"Btn{max(1, min(6, variant)):02d}.png"
        image = self.images.get(path, (146, 40))
        return Button(
            master, text=text, image=image, compound="center", command=command,
            bg=BG, activebackground=BG, fg=CYAN_BRIGHT,
            activeforeground=WHITE, font=(self.font, 9),
            relief="flat", bd=0, cursor="hand2",
        )

    def _nav_button(self, master, text: str, command) -> Button:
        image = self.images.get(COMMON_DIR / "BtnDefault.png", (205, 43))
        return Button(
            master, text=text, image=image, compound="center", command=command,
            bg=PANEL, activebackground=PANEL, fg=CYAN,
            activeforeground=WHITE, font=(self.font, 10),
            relief="flat", bd=0, cursor="hand2",
        )

    def _small_button(self, master, text: str, command) -> Button:
        return Button(
            master, text=text, command=command, bg=PANEL_ALT, fg=CYAN,
            activebackground="#17303a", activeforeground=WHITE,
            font=(self.font, 12), relief="flat", bd=0, width=3, cursor="hand2",
        )

    def _tool_button(self, master, icon_number: int, text: str, command) -> Button:
        image = self.images.get(ELEMENTS_DIR / f"IconD{icon_number:02d}.png", (52, 39))
        return Button(
            master, text=text, image=image, compound="left", command=command,
            bg=PANEL, activebackground=PANEL, fg=CYAN,
            activeforeground=WHITE, font=(self.font, 8),
            relief="flat", bd=0, cursor="hand2", padx=2,
        )

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-n>", lambda _event: self.new_note())
        self.root.bind("<Control-f>", lambda _event: self.search_entry.focus_set())
        self.root.bind("<Control-s>", lambda _event: self.force_save())
        self.root.bind("<Control-d>", lambda _event: self.open_daily_log())
        self.root.bind("<Control-q>", lambda _event: self.quick_capture())

    def start(self, show_boot: bool = True) -> None:
        del show_boot  # The supplied UI pack replaces the old boot sequence.
        self.notes.update_streak()
        self._render_background()
        self.refresh_all()
        visible = self.notes.get_notes(limit=1)
        if visible:
            self.open_note(visible[0].id)
        else:
            self.new_note()
        self.root.mainloop()

    def refresh_all(self) -> None:
        self.refresh_folders()
        self.refresh_note_list()
        self.refresh_status()

    def refresh_status(self) -> None:
        total = self.notes.get_notes_count(archived=None)
        streak = self.notes.get_streak()
        self.status_label.configure(
            text=f"{total} NOTES  /  {streak['current']} DAY STREAK"
        )

    def refresh_folders(self) -> None:
        for widget in self.folder_frame.inner.winfo_children():
            widget.destroy()

        def add_level(parent_id: int | None, depth: int) -> None:
            for folder in self.folders.get_all_folders(parent_id):
                marker = "-" if folder.is_expanded else "+"
                text = f"{'  ' * depth}{marker} {folder.name}"
                button = Button(
                    self.folder_frame.inner, text=text,
                    command=lambda folder_id=folder.id: self.set_view(folder_id),
                    bg=PANEL_ALT if self.current_view == folder.id else PANEL,
                    fg=CYAN_BRIGHT if self.current_view == folder.id else MUTED,
                    activebackground=PANEL_ALT, activeforeground=WHITE,
                    font=(self.font, 9), anchor="w", relief="flat", bd=0,
                    cursor="hand2", padx=8, pady=5,
                )
                button.pack(fill=X, pady=1)
                button.bind(
                    "<Button-3>",
                    lambda event, folder_id=folder.id: self.folder_context(event, folder_id),
                )
                if folder.is_expanded:
                    add_level(folder.id, depth + 1)

        add_level(None, 0)

    def folder_context(self, event, folder_id: int) -> None:
        menu = Menu(
            self.root, tearoff=False, bg=PANEL, fg=WHITE,
            activebackground="#245463", activeforeground=WHITE,
            font=(self.font, 9),
        )
        menu.add_command(label="Open", command=lambda: self.set_view(folder_id))
        menu.add_command(label="Add subfolder", command=lambda: self.add_folder(folder_id))
        menu.add_command(label="Rename", command=lambda: self.rename_folder(folder_id))
        folder = self.folders.get_folder(folder_id)
        if folder:
            menu.add_command(
                label="Collapse" if folder.is_expanded else "Expand",
                command=lambda: self.toggle_folder(folder_id),
            )
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self.delete_folder(folder_id))
        menu.tk_popup(event.x_root, event.y_root)

    def set_view(self, view: str | int) -> None:
        self.force_save()
        self.current_view = view
        labels = {
            "all": "ALL NOTES",
            "pinned": "PINNED",
            "favorites": "FAVORITES",
            "archive": "ARCHIVE",
            "vault": "BRAIN VAULT",
        }
        if isinstance(view, int):
            folder = self.folders.get_folder(view)
            title = folder.name if folder else "FOLDER"
        else:
            title = labels.get(view, str(view))
        self.list_title.configure(text=title.upper())
        self.search_var.set("")
        self.refresh_folders()
        self.refresh_note_list()

    def visible_notes(self, search: str = ""):
        common = {"search": search, "limit": 500}
        if self.current_view == "pinned":
            return self.notes.get_notes(pinned=True, **common)
        if self.current_view == "favorites":
            return self.notes.get_notes(favorite=True, **common)
        if self.current_view == "archive":
            return self.notes.get_notes(archived=True, **common)
        if self.current_view == "vault":
            return self.notes.get_notes(vault=True, **common)
        if isinstance(self.current_view, int):
            return self.notes.get_notes(folder_id=self.current_view, **common)
        return self.notes.get_notes(**common)

    def refresh_note_list(self, note_set=None) -> None:
        notes = note_set if note_set is not None else self.visible_notes(self.search_var.get().strip())
        for widget in self.note_list.inner.winfo_children():
            widget.destroy()

        if not notes:
            Label(
                self.note_list.inner, text="NO NOTES FOUND",
                bg=PANEL, fg=MUTED, font=(self.font, 10),
            ).pack(pady=30)
            return

        disabled = COMMON_DIR / "ItemDisable.png"
        enabled = COMMON_DIR / "ItemEnable.png"
        for note in notes:
            selected = note.id == self.note_id
            image = self.images.get(enabled if selected else disabled, (292, 54))
            flags = []
            if note.is_pinned:
                flags.append("PIN")
            if note.is_favorite:
                flags.append("FAV")
            if note.is_brain_vault:
                flags.append("VAULT")
            suffix = f"  / {' '.join(flags)}" if flags else ""
            button = Button(
                self.note_list.inner,
                text=f"{note.title or 'Untitled'}{suffix}"[:48],
                image=image, compound="center",
                command=lambda note_id=note.id: self.open_note(note_id),
                bg=PANEL, activebackground=PANEL,
                fg=CYAN_BRIGHT if selected else CYAN,
                activeforeground=WHITE, font=(self.font, 9),
                relief="flat", bd=0, cursor="hand2",
            )
            button.pack(fill=X, pady=2)

    def search(self) -> None:
        if not hasattr(self, "note_list"):
            return
        query = self.search_var.get().strip()
        if query.startswith("#"):
            name = query[1:].strip().casefold()
            tag = next((item for item in self.notes.get_all_tags() if item.name.casefold() == name), None)
            result = self.notes.get_notes_by_tag(tag.id) if tag and tag.id else []
        else:
            result = self.visible_notes(query)
        self.refresh_note_list(result)

    def new_note(self) -> None:
        self.force_save()
        folder_id = self.current_view if isinstance(self.current_view, int) else None
        note_id = self.notes.create_note(title="New Note", body="", folder_id=folder_id)
        self.open_note(note_id)
        self.title_entry.select_range(0, END)
        self.title_entry.focus_set()
        self.refresh_all()

    def open_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        if self.note_id != note_id:
            self.force_save()
        note = self.notes.get_note(note_id)
        if not note:
            return
        self.loading_note = True
        self.note_id = note_id
        self.title_var.set(note.title)
        self.editor.delete("1.0", END)
        self.editor.insert("1.0", note.body)
        self.tags_var.set(", ".join(tag.name for tag in self.notes.get_tags_for_note(note_id)))
        self.loading_note = False
        self.update_word_count()
        self.refresh_note_list()
        self.editor.focus_set()

    def schedule_save(self) -> None:
        if self.loading_note or not self.note_id:
            return
        if self.save_job:
            self.root.after_cancel(self.save_job)
        self.save_label.configure(text="EDITED")
        self.save_job = self.root.after(650, self.force_save)

    def force_save(self) -> None:
        if self.save_job:
            self.root.after_cancel(self.save_job)
            self.save_job = None
        if self.loading_note or not self.note_id or not hasattr(self, "editor"):
            return
        title = self.title_var.get().strip() or "Untitled"
        body = self.editor.get("1.0", "end-1c")
        self.notes.update_note(self.note_id, title=title, body=body)
        self.notes.set_note_tag_names(
            self.note_id,
            [value.strip() for value in self.tags_var.get().split(",")],
        )
        self.save_label.configure(text="SAVED")
        self.root.after(1000, lambda: self.save_label.configure(text=""))
        self.refresh_note_list()
        self.refresh_status()

    def editor_changed(self) -> None:
        self.update_word_count()
        self.schedule_save()

    def update_word_count(self) -> None:
        count = len(self.editor.get("1.0", "end-1c").split())
        self.word_label.configure(text=f"{count} WORD{'S' if count != 1 else ''}")

    def insert_spaces(self, _event):
        self.editor.insert("insert", "    ")
        return "break"

    def current_note(self):
        return self.notes.get_note(self.note_id)

    def toggle(self, field: str) -> None:
        note = self.current_note()
        if not note:
            return
        self.notes.update_note(note.id, **{field: int(not bool(getattr(note, field)))})
        self.refresh_all()

    def toggle_pin(self) -> None:
        self.toggle("is_pinned")

    def toggle_favorite(self) -> None:
        self.toggle("is_favorite")

    def toggle_archive(self) -> None:
        self.toggle("is_archived")

    def toggle_vault(self) -> None:
        self.toggle("is_brain_vault")

    def delete_note(self) -> None:
        note = self.current_note()
        if not note:
            return
        if not messagebox.askyesno("Delete note", f'Delete "{note.title}" permanently?', parent=self.root):
            return
        self.notes.delete_note(note.id)
        self.note_id = None
        remaining = self.visible_notes()
        if remaining:
            self.open_note(remaining[0].id)
        else:
            self.new_note()
        self.refresh_all()

    def move_note(self) -> None:
        if not self.current_note():
            return
        dialog = Toplevel(self.root)
        dialog.title("Move note")
        dialog.geometry("380x470")
        dialog.configure(bg=PANEL)
        dialog.transient(self.root)
        Label(
            dialog, text="SELECT DESTINATION", bg=PANEL, fg=CYAN_BRIGHT,
            font=(self.font, 14),
        ).pack(anchor="w", padx=16, pady=14)
        frame = ScrollFrame(dialog, bg=PANEL)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        choices = [(None, "UNFILED")] + [
            (folder.id, folder.name.upper()) for folder in self.folders.get_all_folders_flat()
        ]
        for folder_id, name in choices:
            self._nav_button(
                frame.inner, name,
                lambda target=folder_id: self.finish_move(dialog, target),
            ).pack(fill=X, pady=2)

    def finish_move(self, dialog: Toplevel, folder_id: int | None) -> None:
        if self.note_id:
            self.folders.move_note(self.note_id, folder_id)
        dialog.destroy()
        self.refresh_all()

    def quick_capture(self) -> None:
        dialog = Toplevel(self.root)
        dialog.title("Quick Capture")
        dialog.geometry("650x330")
        dialog.configure(bg=PANEL)
        dialog.transient(self.root)
        Label(
            dialog, text="QUICK CAPTURE  /  CTRL+ENTER TO SAVE",
            bg=PANEL, fg=CYAN_BRIGHT, font=(self.font, 13),
        ).pack(anchor="w", padx=16, pady=14)
        field = Text(
            dialog, bg=FIELD, fg=WHITE, insertbackground=CYAN,
            font=(self.font, 11), relief="flat", wrap="word", padx=12, pady=12,
            highlightthickness=1, highlightbackground=BORDER,
        )
        field.pack(fill=BOTH, expand=True, padx=16, pady=(0, 16))

        def save(_event=None):
            body = field.get("1.0", "end-1c").strip()
            if body:
                title = next((line.strip() for line in body.splitlines() if line.strip()), "Captured note")[:80]
                folder_id = self.current_view if isinstance(self.current_view, int) else None
                note_id = self.notes.create_note(title=title, body=body, folder_id=folder_id)
                dialog.destroy()
                self.open_note(note_id)
                self.refresh_all()
            return "break"

        field.bind("<Control-Return>", save)
        field.bind("<Escape>", lambda _event: dialog.destroy())
        field.focus_set()

    def open_daily_log(self, day: str | None = None) -> None:
        self.force_save()
        note = self.notes.get_or_create_daily_log(day or dt.date.today().isoformat())
        self.set_view("all")
        self.open_note(note.id)
        self.refresh_all()

    def add_folder(self, parent_id: int | None = None) -> None:
        name = simpledialog.askstring("New folder", "Folder name:", parent=self.root)
        if name and name.strip():
            folder_id = self.folders.create_folder(name, parent_id)
            self.set_view(folder_id)

    def rename_folder(self, folder_id: int) -> None:
        folder = self.folders.get_folder(folder_id)
        if not folder:
            return
        name = simpledialog.askstring(
            "Rename folder", "Folder name:", initialvalue=folder.name, parent=self.root
        )
        if name and name.strip():
            self.folders.rename_folder(folder_id, name)
            self.refresh_folders()
            if self.current_view == folder_id:
                self.list_title.configure(text=name.strip().upper())

    def toggle_folder(self, folder_id: int) -> None:
        folder = self.folders.get_folder(folder_id)
        if folder:
            self.folders.toggle_expand(folder_id, not folder.is_expanded)
            self.refresh_folders()

    def delete_folder(self, folder_id: int) -> None:
        folder = self.folders.get_folder(folder_id)
        if not folder:
            return
        if messagebox.askyesno(
            "Delete folder",
            f'Delete "{folder.name}"? Notes will become unfiled.',
            parent=self.root,
        ):
            self.folders.delete_folder(folder_id)
            if self.current_view == folder_id:
                self.set_view("all")
            self.refresh_all()

    def close(self) -> None:
        self.force_save()
        self.db.close()
        if sys.platform == "win32":
            try:
                for path in FONT_PATHS:
                    if path.exists():
                        ctypes.windll.gdi32.RemoveFontResourceExW(str(path), 0x10, 0)
            except (AttributeError, OSError):
                pass
        self.root.destroy()


def main(show_boot: bool = True) -> None:
    MainApp().start(show_boot=show_boot)


if __name__ == "__main__":
    main()
