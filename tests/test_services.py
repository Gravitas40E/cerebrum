from __future__ import annotations

import unittest
from datetime import date, timedelta

from database.manager import Database
from services.data_service import FolderService, NoteService
from services.graph_service import GraphService


class ServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Database(":memory:")
        self.notes = NoteService(self.db)
        self.folders = FolderService(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def test_note_crud_and_markdown_plain_text(self) -> None:
        note_id = self.notes.create_note(title="Alpha", body="# Hello\n**world**")
        note = self.notes.get_note(note_id)
        self.assertEqual(note.plain, "Hello\nworld")

        self.assertTrue(self.notes.update_note(note_id, body="Updated `code`"))
        self.assertEqual(self.notes.get_note(note_id).plain, "Updated code")
        self.assertTrue(self.notes.delete_note(note_id))
        self.assertIsNone(self.notes.get_note(note_id))

    def test_folder_filter_does_not_include_unfiled_notes(self) -> None:
        parent = self.folders.create_folder("Parent")
        child = self.folders.create_folder("Child", parent)
        parent_note = self.notes.create_note(title="Parent note", folder_id=parent)
        child_note = self.notes.create_note(title="Child note", folder_id=child)
        self.notes.create_note(title="Unfiled")

        result = {note.id for note in self.notes.get_notes(folder_id=parent)}
        self.assertEqual(result, {parent_note, child_note})
        self.assertEqual(self.folders.get_note_count(parent), 2)

    def test_tag_updates_are_atomic_and_remove_unused_tags(self) -> None:
        note_id = self.notes.create_note(title="Tagged")
        self.notes.set_note_tag_names(note_id, ["Python", "ideas", "Python"])
        self.assertEqual(
            [tag.name for tag in self.notes.get_tags_for_note(note_id)],
            ["ideas", "Python"],
        )

        self.notes.set_note_tag_names(note_id, ["ideas"])
        self.assertEqual([tag.name for tag in self.notes.get_all_tags()], ["ideas"])

    def test_tag_filter_requires_all_selected_tags(self) -> None:
        both = self.notes.create_note(title="Both")
        one = self.notes.create_note(title="One")
        self.notes.set_note_tag_names(both, ["a", "b"])
        self.notes.set_note_tag_names(one, ["a"])
        tags = {tag.name: tag.id for tag in self.notes.get_all_tags()}

        result = self.notes.get_notes(tag_ids=[tags["a"], tags["b"]])
        self.assertEqual([note.id for note in result], [both])

    def test_daily_log_is_unique_per_day(self) -> None:
        first = self.notes.get_or_create_daily_log("2026-06-14")
        second = self.notes.get_or_create_daily_log("2026-06-14")
        self.assertEqual(first.id, second.id)

    def test_dashboard_snapshot_contains_expected_sections(self) -> None:
        regular_id = self.notes.create_note(title="Regular note")
        pinned_id = self.notes.create_note(title="Pinned note", is_pinned=1)
        archived_id = self.notes.create_note(title="Archived note", is_archived=1)
        vault_id = self.notes.create_note(title="Vault note", is_brain_vault=1)
        daily = self.notes.get_or_create_daily_log("2026-06-14")
        self.notes.update_streak(date(2026, 6, 14))

        snapshot = self.notes.get_dashboard_snapshot(day="2026-06-14", recent_limit=5, pinned_limit=5)
        self.assertEqual(snapshot["target_day"], "2026-06-14")
        self.assertEqual(snapshot["total_notes"], 5)
        self.assertEqual(snapshot["current_streak"], 1)
        self.assertEqual(snapshot["today_daily_log"].id, daily.id)
        self.assertEqual(snapshot["random_brain_vault"].id, vault_id)
        self.assertEqual([note.id for note in snapshot["pinned_notes"]], [pinned_id])
        self.assertNotIn(archived_id, [note.id for note in snapshot["recent_notes"]])
        self.assertIn(regular_id, [note.id for note in snapshot["recent_notes"]])

    def test_streak_progression(self) -> None:
        start = date(2026, 6, 10)
        self.assertEqual(self.notes.update_streak(start), (1, 1))
        self.assertEqual(self.notes.update_streak(start), (1, 1))
        self.assertEqual(self.notes.update_streak(start + timedelta(days=1)), (2, 2))
        self.assertEqual(self.notes.update_streak(start + timedelta(days=3)), (1, 2))

    def test_search_escapes_sql_wildcards(self) -> None:
        literal = self.notes.create_note(title="100% complete")
        self.notes.create_note(title="1000 complete")
        result = self.notes.get_notes(search="100%")
        self.assertEqual([note.id for note in result], [literal])

    def test_graph_counts_tag_cooccurrence(self) -> None:
        first = self.notes.create_note(title="First")
        second = self.notes.create_note(title="Second")
        self.notes.set_note_tag_names(first, ["a", "b"])
        self.notes.set_note_tag_names(second, ["a", "b"])

        graph = GraphService(self.db).build_graph()
        self.assertEqual(len(graph["nodes"]), 2)
        self.assertEqual(graph["edges"][0]["weight"], 2)


if __name__ == "__main__":
    unittest.main()
