"""Knowledge graph queries based on tag co-occurrence."""
from __future__ import annotations

from typing import Any

from database.manager import Database


class GraphService:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def build_graph(self) -> dict[str, Any]:
        tag_rows = self.db.execute(
            "SELECT t.id, t.name, COUNT(nt.note_id) AS count "
            "FROM tags t LEFT JOIN note_tags nt ON nt.tag_id = t.id "
            "GROUP BY t.id ORDER BY count DESC, t.name COLLATE NOCASE"
        ).fetchall()
        edge_rows = self.db.execute(
            "SELECT a.tag_id AS source, b.tag_id AS target, COUNT(*) AS weight "
            "FROM note_tags a JOIN note_tags b "
            "ON a.note_id = b.note_id AND a.tag_id < b.tag_id "
            "GROUP BY a.tag_id, b.tag_id"
        ).fetchall()
        return {
            "nodes": [
                {"id": row["id"], "name": row["name"], "count": row["count"]}
                for row in tag_rows
            ],
            "edges": [dict(row) for row in edge_rows],
        }

    def get_related_tags(self, tag_id: int, limit: int = 20) -> list[dict]:
        rows = self.db.execute(
            "SELECT t.id AS tag_id, t.name, COUNT(*) AS weight "
            "FROM note_tags source "
            "JOIN note_tags related ON source.note_id = related.note_id "
            "JOIN tags t ON t.id = related.tag_id "
            "WHERE source.tag_id = ? AND related.tag_id != ? "
            "GROUP BY t.id ORDER BY weight DESC, t.name COLLATE NOCASE LIMIT ?",
            (tag_id, tag_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
