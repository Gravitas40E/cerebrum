# Cerebrum

**Your personal knowledge archive. Built for ideas worth keeping.**

Cerebrum is a local-first personal knowledge archive for Windows. It combines structured note-taking, tagging, daily journaling, and lightweight knowledge graph analysis in a desktop GUI built with Python, tkinter, Pillow, and SQLite.

Designed around a retro-futuristic sci-fi aesthetic, Cerebrum helps you capture ideas, organize knowledge, and connect thoughts without relying on cloud services, subscriptions, or accounts.

Free UI Minimalism SciFi: https://wenrexa.itch.io/kit-nesia2

font X Typewriter: https://ggbot.itch.io/x-typewriter-font?download

<img width="1919" height="1029" alt="image" src="https://github.com/user-attachments/assets/0a7ea601-aedd-4a89-8f5a-93e3d6d49094" />
<img width="1918" height="1032" alt="image" src="https://github.com/user-attachments/assets/b824866b-3fdd-49cb-8f15-bfac5a356768" />

---

## Features

### Knowledge Archive

* Create, edit, and organize notes
* Hierarchical folders with nested subfolders
* Pin important notes
* Favorites system
* Archive old notes
* Brain Vault for ideas, quotes, and reflections

### Dashboard

* Recent notes
* Pinned notes
* Daily streak tracking
* Knowledge statistics
* Random Brain Vault entries
* Recent activity feed

### Markdown Support

* Headings
* Lists
* Code blocks
* Blockquotes
* Links
* Checklists

### Knowledge Graph

Automatically builds relationships between notes through shared tags and displays connections across your archive.

### Daily Logs

* Automatic daily journal entries
* Writing streak tracking
* Historical log browsing

### Search

Search across:

* Titles
* Note content
* Tags
* Folders

Use exact tag searches:

```text
#fitness
#python
#ideas
```

### Quick Capture

Capture ideas instantly without leaving your workflow.

---

## Keyboard Shortcuts

| Shortcut | Action                 |
| -------- | ---------------------- |
| Ctrl + N | New Note               |
| Ctrl + F | Focus Search           |
| Ctrl + S | Save                   |
| Ctrl + D | Open Today's Daily Log |
| Ctrl + Q | Quick Capture          |

---

## Requirements

* Python 3.11+
* tkinter
* Pillow

---

## Installation

```powershell
python -m pip install -r requirements.txt
```

---

## Run

```powershell
python main.py
```

Optional:

```powershell
python main.py --no-boot
```

---

## Configuration

* `CEREBRUM_DB_PATH` overrides the default database location:
  `~/.cerebrum/cerebrum.db`
* UI assets are loaded from `assets/`

---

## Testing

```powershell
python -m unittest discover -s tests -v
```

---

## Project Structure

* `main.py` — Entry point and CLI options
* `app.py` — Main application shell and UI
* `widgets.py` — Reusable Tkinter widgets
* `models/schema.py` — Domain models
* `services/data_service.py` — Notes, folders, tags, streaks
* `services/graph_service.py` — Knowledge graph generation
* `database/manager.py` — SQLite management layer
* `utils/markdown.py` — Markdown utilities
* `tests/` — Integration and utility tests
* `assets/` — UI pack and fonts

---

## Design Philosophy

### Local First

Your data stays on your machine.

### Fast

Built with SQLite and native Python tooling for responsive performance on low-end systems.

### Focused

Cerebrum is designed to be a personal archive of knowledge, not another bloated productivity platform.

---

## Roadmap

* Wiki-style note links (`[[Note Name]]`)
* Command Palette (`Ctrl + P`)
* Interactive Knowledge Network
* Theme customization
* Export and backup tools
* Advanced graph analytics
