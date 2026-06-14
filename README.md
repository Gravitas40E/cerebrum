# Cerebrum

Cerebrum is a local-first personal knowledge archive built with Python,
tkinter, Pillow, and SQLite. Its interface uses the bundled Wenrexa Sci-Fi
Minimalism UI pack and X Typewriter.

<img width="1919" height="1031" alt="image" src="https://github.com/user-attachments/assets/285237da-0d73-47f4-a083-73e40860780c" />
<img width="1919" height="1032" alt="image" src="https://github.com/user-attachments/assets/41970ec7-d9cf-4c5d-a634-70bbce6b75ec" />


## Requirements

- Python 3.11 or newer
- tkinter (included with standard Windows Python installations)
- Pillow

## Run

```powershell
python -m pip install -r requirements.txt
python main.py
```

Data is stored in `~/.cerebrum/cerebrum.db`. Set `CEREBRUM_DB_PATH` to use a
different database file.

## Shortcuts

- `Ctrl+N`: new note
- `Ctrl+F`: focus search
- `Ctrl+S`: save immediately
- `Ctrl+D`: open today's daily log
- `Ctrl+Q`: quick capture

Search for ordinary text across titles and note bodies. Search for an exact
tag with `#tag-name`.

Right-click a folder to add a subfolder, rename it, collapse it, or delete it.
Deleting a folder keeps its notes and moves them to the unfiled collection.

## Test

```powershell
python -m unittest discover -s tests -v
```
