"""Data services for notes, folders, tags, and activity."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from database.manager import Database
from models.schema import Folder, Note, Tag
from utils.markdown import strip_markdown

ALLOWED_ORDER = {
    "updated_at DESC",
    "updated_at ASC",
    "created_at DESC",
    "created_at ASC",
    "title COLLATE NOCASE ASC",
    "title COLLATE NOCASE DESC",
}


class NoteService:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def create_note(self, **kwargs) -> int:
        allowed = set(Note.__dataclass_fields__) - {"id"}
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(f"Unknown note fields: {', '.join(sorted(unknown))}")

        now = datetime.now().isoformat()
        body = str(kwargs.get("body", ""))
        kwargs.setdefault("title", "Untitled")
        kwargs.setdefault("body", body)
        kwargs.setdefault("plain", strip_markdown(body))
        kwargs.setdefault("created_at", now)
        kwargs.setdefault("updated_at", now)
        kwargs.setdefault("is_pinned", 0)
        kwargs.setdefault("is_archived", 0)
        kwargs.setdefault("is_favorite", 0)
        kwargs.setdefault("is_brain_vault", 0)

        fields = list(kwargs)
        placeholders = ",".join("?" for _ in fields)
        sql = f"INSERT INTO notes ({','.join(fields)}) VALUES ({placeholders})"
        cur = self.db.execute(sql, tuple(kwargs[field] for field in fields))
        self.db.commit()
        return int(cur.lastrowid)

    def get_note(self, note_id: int | None) -> Note | None:
        if note_id is None:
            return None
        row = self.db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return Note(**dict(row)) if row else None

    def get_notes(
        self,
        folder_id: int | None = None,
        pinned: bool | None = None,
        archived: bool | None = False,
        favorite: bool | None = None,
        vault: bool | None = None,
        search: str = "",
        tag_ids: list[int] | None = None,
        daily_month: str | None = None,
        limit: int = 200,
        offset: int = 0,
        order: str = "updated_at DESC",
    ) -> list[Note]:
        query = "SELECT * FROM notes WHERE 1=1"
        params: list[Any] = []

        if folder_id is not None:
            folder_ids = [folder_id, *self._get_all_subfolder_ids(folder_id)]
            placeholders = ",".join("?" for _ in folder_ids)
            query += f" AND folder_id IN ({placeholders})"
            params.extend(folder_ids)
        if pinned is not None:
            query += " AND is_pinned = ?"
            params.append(int(pinned))
        if archived is not None:
            query += " AND is_archived = ?"
            params.append(int(archived))
        if favorite is not None:
            query += " AND is_favorite = ?"
            params.append(int(favorite))
        if vault is not None:
            query += " AND is_brain_vault = ?"
            params.append(int(vault))
        if daily_month:
            query += " AND daily_log_date LIKE ?"
            params.append(f"{daily_month}%")
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            wildcard = f"%{escaped}%"
            query += " AND (title LIKE ? ESCAPE '\\' OR plain LIKE ? ESCAPE '\\')"
            params.extend([wildcard, wildcard])
        if tag_ids:
            placeholders = ",".join("?" for _ in tag_ids)
            query += (
                " AND id IN (SELECT note_id FROM note_tags "
                f"WHERE tag_id IN ({placeholders}) GROUP BY note_id "
                "HAVING COUNT(DISTINCT tag_id) = ?)"
            )
            params.extend(tag_ids)
            params.append(len(set(tag_ids)))

        safe_order = order if order in ALLOWED_ORDER else "updated_at DESC"
        query += f" ORDER BY {safe_order} LIMIT ? OFFSET ?"
        params.extend([max(1, limit), max(0, offset)])
        rows = self.db.execute(query, tuple(params)).fetchall()
        return [Note(**dict(row)) for row in rows]

    def get_notes_count(self, **filters) -> int:
        filters.pop("limit", None)
        filters.pop("offset", None)
        return len(self.get_notes(limit=1_000_000, **filters))

    def get_dashboard_snapshot(
        self,
        day: str | None = None,
        recent_limit: int = 6,
        pinned_limit: int = 6,
    ) -> dict[str, Any]:
        target_day = day or date.today().isoformat()
        streak = self.get_streak()
        recent = self.get_notes(limit=recent_limit) if recent_limit > 0 else []
        pinned = self.get_notes(pinned=True, limit=pinned_limit) if pinned_limit > 0 else []
        return {
            "target_day": target_day,
            "total_notes": self.get_notes_count(archived=None),
            "current_streak": streak["current"],
            "best_streak": streak["best"],
            "recent_notes": recent,
            "pinned_notes": pinned,
            "today_daily_log": self.get_daily_log(target_day),
            "random_brain_vault": self.get_random_brain_vault(),
        }

    def update_note(self, note_id: int | None, **kwargs) -> bool:
        if note_id is None or not kwargs:
            return False
        allowed = set(Note.__dataclass_fields__) - {"id", "created_at"}
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(f"Unknown note fields: {', '.join(sorted(unknown))}")
        if "body" in kwargs and "plain" not in kwargs:
            kwargs["plain"] = strip_markdown(str(kwargs["body"]))
        kwargs["updated_at"] = datetime.now().isoformat()
        assignments = ", ".join(f"{field} = ?" for field in kwargs)
        values = [kwargs[field] for field in kwargs]
        cur = self.db.execute(
            f"UPDATE notes SET {assignments} WHERE id = ?",
            (*values, note_id),
        )
        self.db.commit()
        return cur.rowcount > 0

    def delete_note(self, note_id: int | None) -> bool:
        if note_id is None:
            return False
        cur = self.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.db.commit()
        return cur.rowcount > 0

    def get_tags_for_note(self, note_id: int | None) -> list[Tag]:
        if note_id is None:
            return []
        rows = self.db.execute(
            "SELECT t.* FROM tags t JOIN note_tags nt ON t.id = nt.tag_id "
            "WHERE nt.note_id = ? ORDER BY t.name COLLATE NOCASE",
            (note_id,),
        ).fetchall()
        return [Tag(**dict(row)) for row in rows]

    def get_or_create_tag(self, name: str) -> Tag:
        clean = name.strip().lstrip("#")
        if not clean:
            raise ValueError("Tag name cannot be empty")
        with self.db.transaction():
            self.db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (clean,))
            row = self.db.execute(
                "SELECT * FROM tags WHERE name = ? COLLATE NOCASE", (clean,)
            ).fetchone()
        return Tag(**dict(row))

    def set_note_tag_names(self, note_id: int | None, names: list[str]) -> None:
        if note_id is None:
            return
        clean_names = list(dict.fromkeys(
            name.strip().lstrip("#") for name in names if name.strip().lstrip("#")
        ))
        tag_ids = [self.get_or_create_tag(name).id for name in clean_names]
        with self.db.transaction():
            self.db.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
            self.db.executemany(
                "INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                [(note_id, tag_id) for tag_id in tag_ids if tag_id is not None],
            )
            self.db.execute(
                "DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM note_tags)"
            )

    def get_all_tags(self) -> list[Tag]:
        rows = self.db.execute("SELECT * FROM tags ORDER BY name COLLATE NOCASE").fetchall()
        return [Tag(**dict(row)) for row in rows]

    def get_notes_by_tag(self, tag_id: int) -> list[Note]:
        return self.get_notes(tag_ids=[tag_id])

    def get_note_count_for_tag(self, tag_id: int) -> int:
        row = self.db.execute(
            "SELECT COUNT(*) FROM note_tags WHERE tag_id = ?", (tag_id,)
        ).fetchone()
        return int(row[0]) if row else 0

    def get_daily_log(self, day: str | None = None) -> Note | None:
        day = day or date.today().isoformat()
        row = self.db.execute(
            "SELECT * FROM notes WHERE daily_log_date = ?", (day,)
        ).fetchone()
        return Note(**dict(row)) if row else None

    def get_or_create_daily_log(self, day: str | None = None) -> Note:
        target = day or date.today().isoformat()
        note = self.get_daily_log(target)
        if note:
            return note
        note_id = self.create_note(
            title=target,
            body=f"# {target}\n\n",
            daily_log_date=target,
        )
        return self.get_note(note_id)  # type: ignore[return-value]

    def get_random_brain_vault(self) -> Note | None:
        row = self.db.execute(
            "SELECT * FROM notes WHERE is_brain_vault = 1 AND is_archived = 0 "
            "ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        return Note(**dict(row)) if row else None

    def get_random_favorite(self) -> Note | None:
        row = self.db.execute(
            "SELECT * FROM notes WHERE is_favorite = 1 AND is_archived = 0 "
            "ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        return Note(**dict(row)) if row else None

    def update_streak(self, day: date | None = None) -> tuple[int, int]:
        today = day or date.today()
        row = self.db.execute("SELECT * FROM streaks WHERE id = 1").fetchone()
        if not row:
            self.db.execute(
                "INSERT INTO streaks (id, current, best, last_date) VALUES (1, 1, 1, ?)",
                (today.isoformat(),),
            )
            self.db.commit()
            return 1, 1

        last = date.fromisoformat(row["last_date"]) if row["last_date"] else None
        current = int(row["current"] or 0)
        best = int(row["best"] or 0)
        if last == today:
            return current, best
        current = current + 1 if last and (today - last).days == 1 else 1
        best = max(best, current)
        self.db.execute(
            "UPDATE streaks SET current = ?, best = ?, last_date = ? WHERE id = 1",
            (current, best, today.isoformat()),
        )
        self.db.commit()
        return current, best

    def get_streak(self) -> dict[str, int]:
        row = self.db.execute("SELECT * FROM streaks WHERE id = 1").fetchone()
        return {
            "current": int(row["current"] or 0) if row else 0,
            "best": int(row["best"] or 0) if row else 0,
        }

    def get_activity(self, days: int = 42) -> dict[str, int]:
        rows = self.db.execute(
            "SELECT substr(updated_at, 1, 10) AS day, COUNT(*) AS count "
            "FROM notes WHERE is_archived = 0 GROUP BY day"
        ).fetchall()
        return {row["day"]: int(row["count"]) for row in rows}

    def _get_all_subfolder_ids(self, folder_id: int) -> list[int]:
        rows = self.db.execute(
            "WITH RECURSIVE descendants(id) AS ("
            " SELECT id FROM folders WHERE parent_id = ?"
            " UNION ALL"
            " SELECT f.id FROM folders f JOIN descendants d ON f.parent_id = d.id"
            ") SELECT id FROM descendants",
            (folder_id,),
        ).fetchall()
        return [int(row["id"]) for row in rows]


class FolderService:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def create_folder(self, name: str, parent_id: int | None = None) -> int:
        clean = name.strip() or "New Folder"
        cur = self.db.execute(
            "INSERT INTO folders (name, parent_id, created_at) VALUES (?, ?, ?)",
            (clean, parent_id, datetime.now().isoformat()),
        )
        self.db.commit()
        return int(cur.lastrowid)

    def get_all_folders(self, parent_id: int | None = None) -> list[Folder]:
        rows = self.db.execute(
            "SELECT * FROM folders WHERE parent_id IS ? ORDER BY name COLLATE NOCASE",
            (parent_id,),
        ).fetchall()
        return [Folder(**dict(row)) for row in rows]

    def get_all_folders_flat(self) -> list[Folder]:
        rows = self.db.execute(
            "SELECT * FROM folders ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [Folder(**dict(row)) for row in rows]

    def get_folder(self, folder_id: int) -> Folder | None:
        row = self.db.execute(
            "SELECT * FROM folders WHERE id = ?", (folder_id,)
        ).fetchone()
        return Folder(**dict(row)) if row else None

    def rename_folder(self, folder_id: int, name: str) -> None:
        clean = name.strip()
        if not clean:
            raise ValueError("Folder name cannot be empty")
        self.db.execute("UPDATE folders SET name = ? WHERE id = ?", (clean, folder_id))
        self.db.commit()

    def delete_folder(self, folder_id: int) -> None:
        parent = self.db.execute(
            "SELECT parent_id FROM folders WHERE id = ?", (folder_id,)
        ).fetchone()
        parent_id = parent["parent_id"] if parent else None
        with self.db.transaction():
            self.db.execute(
                "UPDATE folders SET parent_id = ? WHERE parent_id = ?",
                (parent_id, folder_id),
            )
            self.db.execute(
                "UPDATE notes SET folder_id = NULL WHERE folder_id = ?", (folder_id,)
            )
            self.db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))

    def toggle_expand(self, folder_id: int, expanded: bool) -> None:
        self.db.execute(
            "UPDATE folders SET is_expanded = ? WHERE id = ?",
            (int(expanded), folder_id),
        )
        self.db.commit()

    def get_note_count(self, folder_id: int) -> int:
        row = self.db.execute(
            "WITH RECURSIVE descendants(id) AS ("
            " SELECT ? UNION ALL"
            " SELECT f.id FROM folders f JOIN descendants d ON f.parent_id = d.id"
            ") SELECT COUNT(*) FROM notes WHERE folder_id IN (SELECT id FROM descendants)"
            " AND is_archived = 0",
            (folder_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def move_note(self, note_id: int, folder_id: int | None) -> None:
        self.db.execute(
            "UPDATE notes SET folder_id = ?, updated_at = ? WHERE id = ?",
            (folder_id, datetime.now().isoformat(), note_id),
        )
        self.db.commit()
