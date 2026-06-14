# Cerebrum

Cerebrum is a local-first personal knowledge archive for Windows. It combines structured note-taking, tagging, and lightweight knowledge-graph analysis in a desktop GUI built with Python, tkinter, Pillow, and SQLite. The interface uses the bundled Wenrexa Sci-Fi Minimalism UI pack and the X Typewriter font.

<img width="1919" height="1029" alt="image" src="https://github.com/user-attachments/assets/0a7ea601-aedd-4a89-8f5a-93e3d6d49094" />
<img width="1918" height="1032" alt="image" src="https://github.com/user-attachments/assets/b824866b-3fdd-49cb-8f15-bfac5a356768" />


## Capabilities

Core features
- Markdown notes with inline formatting, code blocks, links, block quotes, bullets, and headings
- Hierarchical folders with expand/collapse, subfolders, and right-click context actions
- Tagging system with exact `#tag` search syntax and many-to-many relationships
- Knowledge graph built from tag co-occurrence across notes
- Daily log mode with streak tracking and streak progression logic
- Special views: Dashboard, All Notes, Pinned, Favorites, Brain Vault, Archive
- Quick capture and daily-log shortcuts for fast entry
- Incremental search across titles and plain-text note bodies
- Pinning, favorites, and vault classification with dedicated views
- Context menus on folders for open, add subfolder, rename, collapse, delete
- Autosave with explicit Ctrl+S, word counts, save status indicator

Keyboard shortcuts
- Ctrl+N — new note
- Ctrl+F — focus search
- Ctrl+S — save immediately
- Ctrl+D — open today's daily log
- Ctrl+Q — quick capture

Requirements
- Python 3.11 or newer
- tkinter (bundled with standard Windows Python installs)
- Pillow

Install
```powershell
python -m pip install -r requirements.txt
```

Run
```powershell
python main.py
```

Optional CLI flags
- `--no-boot` — skip any boot animation/sequence and open directly

Configuration
- Database path: `CEREBRUM_DB_PATH` overrides the default location `~/.cerebrum/cerebrum.db`
- UI assets are loaded from `assets/` at runtime (Wenrexa UI pack and X Typewriter font)

Testing
```powershell
python -m unittest discover -s tests -v
```

Project structure
- `main.py` — CLI entry point; parses `--no-boot` and launches `app.main`
- `app.py` — MainApp: shell, background, nav, note list, editor, dashboard, shortcuts, and refresh flow
- `widgets.py` — Reusable Tkinter widgets such as GlowButton and ScrollFrame
- `models/schema.py` — Domain dataclasses for Note, Folder, Tag and default DB path resolution
- `services/data_service.py` — NoteService and FolderService for CRUD, tags, daily logs, streaks, activity, dashboard snapshots
- `services/graph_service.py` — GraphService for tag co-occurrence graph queries
- `database/manager.py` — Thread-safe SQLite wrapper; schema, indexes, transactions, and connection lifecycle
- `utils/markdown.py` — Markdown strip/parse helpers and Tkinter Text preview renderer
- `tests/test_services.py` — Service integration tests: notes, folders, tags, search, streaks, graph
- `tests/test_markdown.py` — Markdown utility tests
- `assets/` — Bundled UI assets: Wenrexa Sci-Fi Minimalism pack and X Typewriter font

Database schema highlights
- `folders`: id, name, parent_id, is_expanded, created_at
- `notes`: id, title, body, plain, folder_id, flags (pinned/archived/favorite/vault), daily_log_date, created_at, updated_at
- `tags`: id, name (unique, case-insensitive)
- `note_tags`: join table for many-to-many note/tag relationships
- `streaks`: single-row table tracking current and best streak
- `app_state`: key/value store if needed
- Indexes on folder, flags, daily_log_date, updated_at, and vault

Notes on design
- Local-first with SQLite in user profile; no external service or account required
- Thread-safe DB access via `threading.RLock` and context manager transactions
- Search uses escaped LIKE with backslash; exact tag matching with `#tag-name`
- Folder deletion reassigns notes to unfiled and orphans child folders by reparenting them up one level
