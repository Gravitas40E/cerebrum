"""Domain models and application data location."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def _default_db_path() -> Path:
    override = os.environ.get("CEREBRUM_DB_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cerebrum" / "cerebrum.db"


DB_PATH = _default_db_path()


@dataclass
class Note:
    id: int | None = None
    title: str = ""
    body: str = ""
    plain: str = ""
    folder_id: int | None = None
    is_pinned: bool = False
    is_archived: bool = False
    is_favorite: bool = False
    is_brain_vault: bool = False
    daily_log_date: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Folder:
    id: int | None = None
    name: str = ""
    parent_id: int | None = None
    is_expanded: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Tag:
    id: int | None = None
    name: str = ""
