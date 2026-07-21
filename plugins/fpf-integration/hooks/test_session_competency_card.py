#!/usr/bin/env python3
"""Тесты чистых функций SessionStart-хука `session_competency_card.py`.

Запуск:
  python3 test_session_competency_card.py
  python3 -m unittest test_session_competency_card

stdlib only (unittest) — pytest в окружении отсутствует.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import session_competency_card as card  # noqa: E402


def row(pkg_id, level="project", kind="", stale=False, shadowed=False, path=""):
    return {
        "id": pkg_id,
        "path": path,
        "level": level,
        "kind": kind,
        "stale": stale,
        "shadowed": shadowed,
    }


def upper_purpose(row_):
    return f"purpose-{row_['id']}"


class BuildCardLinesTests(unittest.TestCase):
    def test_empty_rows_returns_empty(self):
        self.assertEqual(card.build_card_lines([], upper_purpose, max_n=40), [])

    def test_project_only_rows_grouped_under_project_title(self):
        rows = [row("DPF-A", level="project")]
        lines = card.build_card_lines(rows, upper_purpose, max_n=40)
        self.assertEqual(lines, ["Проект:", "DPF-A — purpose-DPF-A"])

    def test_level_headers_only_for_levels_with_rows(self):
        rows = [row("DPF-A", level="project"), row("DPF-B", level="plugin")]
        lines = card.build_card_lines(rows, upper_purpose, max_n=40)
        self.assertEqual(
            lines,
            [
                "Проект:",
                "DPF-A — purpose-DPF-A",
                "Плагины:",
                "DPF-B — purpose-DPF-B",
            ],
        )

    def test_level_order_is_project_user_plugin_regardless_of_input_order(self):
        rows = [
            row("DPF-C", level="plugin"),
            row("DPF-B", level="user"),
            row("DPF-A", level="project"),
        ]
        lines = card.build_card_lines(rows, upper_purpose, max_n=40)
        self.assertEqual(
            lines,
            [
                "Проект:",
                "DPF-A — purpose-DPF-A",
                "Пользователь:",
                "DPF-B — purpose-DPF-B",
                "Плагины:",
                "DPF-C — purpose-DPF-C",
            ],
        )

    def test_shadowed_rows_are_dropped_before_grouping(self):
        rows = [
            row("DPF-A", level="project", shadowed=False),
            row("DPF-A", level="user", shadowed=True),
        ]
        lines = card.build_card_lines(rows, upper_purpose, max_n=40)
        self.assertEqual(lines, ["Проект:", "DPF-A — purpose-DPF-A"])

    def test_stale_row_gets_suffix(self):
        rows = [row("DPF-A", stale=True)]
        lines = card.build_card_lines(rows, upper_purpose, max_n=40)
        self.assertEqual(lines, ["Проект:", "DPF-A — purpose-DPF-A · протух"])

    def test_truncation_shows_max_n_and_remainder_pointer(self):
        rows = [row(f"DPF-{i}", level="project") for i in range(5)]
        lines = card.build_card_lines(rows, upper_purpose, max_n=3)
        self.assertEqual(
            lines,
            [
                "Проект:",
                "DPF-0 — purpose-DPF-0",
                "DPF-1 — purpose-DPF-1",
                "DPF-2 — purpose-DPF-2",
                "…и ещё 2 — /fpf-integration:dpf-apply --list",
            ],
        )

    def test_no_truncation_when_exactly_at_max_n(self):
        rows = [row(f"DPF-{i}", level="project") for i in range(3)]
        lines = card.build_card_lines(rows, upper_purpose, max_n=3)
        self.assertNotIn("…", "\n".join(lines))


class ReadPurposeTests(unittest.TestCase):
    def test_name_field_quoted(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "DPF.md"), "w", encoding="utf-8") as fh:
                fh.write('---\nname: "человекочитаемое назначение"\n---\n')
            self.assertEqual(
                card.read_purpose(root, "kind-x", "DPF-A"), "человекочитаемое назначение"
            )

    def test_name_field_unquoted(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "DPF.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname: bare purpose\n---\n")
            self.assertEqual(card.read_purpose(root, "kind-x", "DPF-A"), "bare purpose")

    def test_fallback_to_kind_when_no_name_field(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "DPF.md"), "w", encoding="utf-8") as fh:
                fh.write("---\ndpf_id: DPF-A\n---\n")
            self.assertEqual(card.read_purpose(root, "kind-x", "DPF-A"), "kind-x")

    def test_fallback_to_empty_name_value_uses_kind(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "DPF.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname:\n---\n")
            self.assertEqual(card.read_purpose(root, "kind-x", "DPF-A"), "kind-x")

    def test_fallback_to_bare_id_when_no_name_and_no_kind(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "DPF.md"), "w", encoding="utf-8") as fh:
                fh.write("---\ndpf_id: DPF-A\n---\n")
            self.assertEqual(card.read_purpose(root, "", "DPF-A"), "DPF-A")

    def test_missing_file_falls_back_to_kind(self):
        purpose = card.read_purpose("/no/such/dir", "kind-x", "DPF-A")
        self.assertEqual(purpose, "kind-x")


if __name__ == "__main__":
    unittest.main()
