#!/usr/bin/env python3
"""Тесты чистых функций UserPromptSubmit-хука `prompt_competency_hint.py`.

Запуск:
  python3 test_prompt_competency_hint.py
  python3 -m unittest test_prompt_competency_hint

stdlib only (unittest) — pytest в окружении отсутствует.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import prompt_competency_hint as hint  # noqa: E402


def write_map(root: str, body: str) -> str:
    path = os.path.join(root, "competency-map.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


class ExtractIdCandidatesTests(unittest.TestCase):
    def test_finds_dpf_and_lpf_ids(self):
        prompt = "смотри DPF-COUPLING-GENERALIZATION и LPF-SIMPLIFICATION-REVIEW"
        candidates = hint.extract_id_candidates(prompt)
        self.assertEqual(candidates, ["DPF-COUPLING-GENERALIZATION", "LPF-SIMPLIFICATION-REVIEW"])

    def test_dedups_preserving_first_appearance_order(self):
        prompt = "DPF-X затем DPF-Y затем снова DPF-X"
        self.assertEqual(hint.extract_id_candidates(prompt), ["DPF-X", "DPF-Y"])

    def test_no_ids_returns_empty(self):
        self.assertEqual(hint.extract_id_candidates("надо ли обобщать этот код?"), [])

    def test_surrounding_cyrillic_text_does_not_break_match(self):
        prompt = "применить пакет DPF-COUPLING-GENERALIZATION к дублирующемуся коду"
        self.assertEqual(hint.extract_id_candidates(prompt), ["DPF-COUPLING-GENERALIZATION"])


class ParseCompetencyMapTests(unittest.TestCase):
    def test_well_formed_table(self):
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| DPF-A | foo; bar |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual(rows, [{"id": "DPF-A", "cues": ["foo", "bar"]}])

    def test_regression_id_in_backticks_is_stripped(self):
        """ISSUE-001: id-ячейка обёрнута в markdown-backticks в реальной карте."""
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| `DPF-COUPLING-GENERALIZATION` | обобщать; дублирующийся код |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "DPF-COUPLING-GENERALIZATION")
        self.assertNotIn("`", rows[0]["id"])

    def test_cues_in_backticks_are_also_stripped(self):
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| DPF-A | `foo`; `bar baz` |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual(rows[0]["cues"], ["foo", "bar baz"])

    def test_missing_file_returns_empty_list(self):
        self.assertEqual(hint.parse_competency_map("/no/such/path/competency-map.md"), [])

    def test_separator_row_is_skipped(self):
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| DPF-A | foo |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual(len(rows), 1)

    def test_row_with_wrong_cell_count_is_skipped(self):
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| DPF-A | foo | extra |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual(rows, [])

    def test_row_with_empty_id_is_skipped(self):
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "|  | foo |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual(rows, [])

    def test_table_stops_at_first_non_pipe_line_after_header(self):
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| DPF-A | foo |\n"
            "\n"
            "прочий текст, не таблица\n"
            "| DPF-B | bar |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        self.assertEqual([row["id"] for row in rows], ["DPF-A"])


class FindCueMatchesTests(unittest.TestCase):
    def test_word_boundary_case_insensitive_match(self):
        rows = [{"id": "DPF-A", "cues": ["coupling"]}]
        self.assertEqual(hint.find_cue_matches("нужен Coupling анализ", rows), ["DPF-A"])

    def test_no_match_returns_empty(self):
        rows = [{"id": "DPF-A", "cues": ["coupling"]}]
        self.assertEqual(hint.find_cue_matches("ничего похожего", rows), [])

    def test_dedup_by_id_first_row_wins(self):
        rows = [
            {"id": "DPF-A", "cues": ["foo"]},
            {"id": "DPF-A", "cues": ["bar"]},
        ]
        self.assertEqual(hint.find_cue_matches("foo bar", rows), ["DPF-A"])

    def test_cyrillic_cue_word_boundary(self):
        rows = [{"id": "DPF-A", "cues": ["обобщение"]}]
        self.assertEqual(
            hint.find_cue_matches("надо ли обобщение этого кода?", rows), ["DPF-A"]
        )
        self.assertEqual(
            hint.find_cue_matches("необобщениеподряд без границ", rows), []
        )

    def test_regression_backtick_stripped_map_yields_clean_id(self):
        """ISSUE-001 end-to-end: карта с backtick-id -> найденный id без бэктиков."""
        body = (
            "| id | cues |\n"
            "|----|------|\n"
            "| `DPF-COUPLING-GENERALIZATION` | дублирующийся код |\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = write_map(root, body)
            rows = hint.parse_competency_map(path)
        matches = hint.find_cue_matches("надо ли обобщать этот дублирующийся код?", rows)
        self.assertEqual(matches, ["DPF-COUPLING-GENERALIZATION"])


class BuildHintLinesTests(unittest.TestCase):
    def test_single_id_format(self):
        lines = hint.build_hint_lines(["DPF-A"])
        self.assertEqual(
            lines,
            [
                "свод `DPF-A` выглядит релевантным → /fpf-integration:dpf-apply DPF-A",
                "(применение требует declaredUse; гейт свежести не обходится)",
            ],
        )

    def test_empty_input_returns_empty(self):
        self.assertEqual(hint.build_hint_lines([]), [])

    def test_caps_at_max_n_with_remainder_pointer(self):
        lines = hint.build_hint_lines(["A", "B", "C", "D", "E"], max_n=3)
        self.assertEqual(lines[-1], "…+2, см. /fpf-integration:dpf-apply --list")
        self.assertEqual(len(lines), 3 * 2 + 1)

    def test_regression_slash_command_has_no_backticks(self):
        lines = hint.build_hint_lines(["DPF-COUPLING-GENERALIZATION"])
        self.assertIn(
            "/fpf-integration:dpf-apply DPF-COUPLING-GENERALIZATION", lines[0]
        )
        self.assertNotIn(
            "/fpf-integration:dpf-apply `DPF-COUPLING-GENERALIZATION`", lines[0]
        )


class ParsePromptPayloadTests(unittest.TestCase):
    def test_valid_payload_returns_prompt(self):
        raw = '{"prompt": "надо ли обобщать этот код?"}'
        self.assertEqual(hint.parse_prompt_payload(raw), "надо ли обобщать этот код?")

    def test_empty_raw_returns_empty_string(self):
        self.assertEqual(hint.parse_prompt_payload(""), "")
        self.assertEqual(hint.parse_prompt_payload("   \n"), "")

    def test_malformed_json_returns_empty_string(self):
        self.assertEqual(hint.parse_prompt_payload("{not json"), "")

    def test_non_dict_payload_returns_empty_string(self):
        self.assertEqual(hint.parse_prompt_payload("[1, 2, 3]"), "")

    def test_missing_prompt_field_returns_empty_string(self):
        self.assertEqual(hint.parse_prompt_payload("{}"), "")

    def test_non_string_prompt_field_returns_empty_string(self):
        self.assertEqual(hint.parse_prompt_payload('{"prompt": 42}'), "")


class ParseSessionIdTests(unittest.TestCase):
    def test_valid_payload_returns_session_id(self):
        raw = '{"prompt": "x", "session_id": "abc-123"}'
        self.assertEqual(hint.parse_session_id(raw), "abc-123")

    def test_missing_field_returns_empty(self):
        self.assertEqual(hint.parse_session_id('{"prompt": "x"}'), "")

    def test_malformed_json_returns_empty(self):
        self.assertEqual(hint.parse_session_id("{not json"), "")

    def test_non_dict_returns_empty(self):
        self.assertEqual(hint.parse_session_id("[1,2]"), "")

    def test_non_string_session_id_returns_empty(self):
        self.assertEqual(hint.parse_session_id('{"session_id": 42}'), "")


class SeenStorePathTests(unittest.TestCase):
    def test_empty_session_returns_none(self):
        self.assertIsNone(hint._seen_store_path(""))

    def test_traversal_chars_are_sanitized(self):
        path = hint._seen_store_path("../../etc/passwd")
        self.assertIsNotNone(path)
        # ни одного `..`-сегмента и никакого выхода за каталог стора
        self.assertNotIn("..", os.path.basename(path))
        self.assertEqual(
            os.path.dirname(path),
            os.path.join(tempfile.gettempdir(), "dpf-competency-hints"),
        )

    def test_normal_session_id_kept_as_safe_token(self):
        path = hint._seen_store_path("abc-123_XYZ")
        self.assertEqual(os.path.basename(path), "abc-123_XYZ")


class SeenStoreRoundtripTests(unittest.TestCase):
    SESSION = "unittest-session-DEDUP-fixture"

    def tearDown(self):
        path = hint._seen_store_path(self.SESSION)
        if path and os.path.exists(path):
            os.remove(path)

    def test_unknown_session_loads_empty(self):
        # гарантируем отсутствие стора
        self.tearDown()
        self.assertEqual(hint.load_seen(self.SESSION), set())

    def test_record_then_load_roundtrip(self):
        self.tearDown()
        hint.record_seen(self.SESSION, ["DPF-A", "DPF-B"])
        self.assertEqual(hint.load_seen(self.SESSION), {"DPF-A", "DPF-B"})

    def test_record_appends_across_calls(self):
        self.tearDown()
        hint.record_seen(self.SESSION, ["DPF-A"])
        hint.record_seen(self.SESSION, ["DPF-B"])
        self.assertEqual(hint.load_seen(self.SESSION), {"DPF-A", "DPF-B"})

    def test_record_empty_is_noop(self):
        self.tearDown()
        hint.record_seen(self.SESSION, [])
        self.assertEqual(hint.load_seen(self.SESSION), set())

    def test_no_session_id_load_is_empty_fail_open(self):
        # пустой session_id -> путь None -> load всегда set() (дедуп не применяется)
        self.assertEqual(hint.load_seen(""), set())
        hint.record_seen("", ["DPF-A"])  # не должно падать и ничего не писать


if __name__ == "__main__":
    unittest.main()
