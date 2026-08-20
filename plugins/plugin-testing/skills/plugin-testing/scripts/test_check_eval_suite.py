#!/usr/bin/env python3
"""Тесты `check_eval_suite.py` — проверки состава набора кейсов.

Запуск:
  python3 test_check_eval_suite.py
  python3 -m unittest test_check_eval_suite

stdlib only (unittest) — pytest в окружении отсутствует.
"""

from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_eval_suite as checker  # noqa: E402


def write_case(
    evals_root: Path,
    name: str,
    *,
    allowed_tools: str = "[Read, Glob, Grep, Skill]",
    graders: dict[str, str] | None = None,
) -> None:
    case_dir = evals_root / name
    (case_dir / "graders").mkdir(parents=True)
    (case_dir / "prompt.md").write_text(
        textwrap.dedent(
            f"""\
            ---
            name: {name}
            runs: 3
            allowed_tools: {allowed_tools}
            plugins: ["../.."]
            ---

            Запрос человека.
            """
        )
    )
    for grader_name, body in (graders or {}).items():
        (case_dir / "graders" / f"{grader_name}.md").write_text(body)


TOOL_USED_SKILL = textwrap.dedent(
    """\
    ---
    type: tool_used
    name: uses-skill
    tool: Skill
    min: 1
    ---
    """
)

FORBID_WRITE = textwrap.dedent(
    """\
    ---
    type: tool_used
    name: writes-no-file
    tool: Write
    min: 0
    max: 0
    ---
    """
)

MAX_WITHOUT_MIN = textwrap.dedent(
    """\
    ---
    type: tool_used
    name: writes-no-file
    tool: Write
    max: 0
    ---
    """
)

UNKNOWN_TYPE = textwrap.dedent(
    """\
    ---
    type: vibes
    name: feels-right
    ---
    """
)


class SuiteDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.plugin = Path(self.temp.name) / "my-plugin"
        self.evals = self.plugin / "evals"
        self.evals.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_suite_has_no_findings(self) -> None:
        write_case(self.evals, "routing", graders={"uses-skill": TOOL_USED_SKILL})

        findings = checker.check_suite(self.plugin)

        self.assertEqual(findings, [])

    def test_missing_evals_directory_is_reported(self) -> None:
        findings = checker.check_suite(Path(self.temp.name) / "no-such-plugin")

        self.assertTrue(any("evals" in finding for finding in findings))

    def test_case_without_graders_is_reported(self) -> None:
        write_case(self.evals, "routing", graders={})

        findings = checker.check_suite(self.plugin)

        self.assertTrue(any("routing" in f and "критери" in f for f in findings))

    def test_forbidding_a_tool_the_case_never_requests_is_reported(self) -> None:
        write_case(
            self.evals,
            "limits",
            allowed_tools="[Read, Skill]",
            graders={"writes-no-file": FORBID_WRITE},
        )

        findings = checker.check_suite(self.plugin)

        self.assertTrue(any("Write" in f and "limits" in f for f in findings))

    def test_forbidding_a_requested_tool_is_accepted(self) -> None:
        write_case(
            self.evals,
            "limits",
            allowed_tools="[Read, Skill, Write]",
            graders={"writes-no-file": FORBID_WRITE},
        )

        findings = checker.check_suite(self.plugin)

        self.assertEqual(findings, [])

    def test_max_zero_without_min_zero_is_reported(self) -> None:
        write_case(
            self.evals,
            "limits",
            allowed_tools="[Read, Skill, Write]",
            graders={"writes-no-file": MAX_WITHOUT_MIN},
        )

        findings = checker.check_suite(self.plugin)

        self.assertTrue(any("min" in f for f in findings))

    def test_unknown_grader_type_is_reported(self) -> None:
        write_case(self.evals, "routing", graders={"feels-right": UNKNOWN_TYPE})

        findings = checker.check_suite(self.plugin)

        self.assertTrue(any("vibes" in f for f in findings))

    def test_duplicate_grader_names_are_reported(self) -> None:
        write_case(
            self.evals,
            "routing",
            graders={"a": TOOL_USED_SKILL, "b": TOOL_USED_SKILL},
        )

        findings = checker.check_suite(self.plugin)

        self.assertTrue(any("uses-skill" in f for f in findings))


class ExitCodeTests(unittest.TestCase):
    def test_clean_suite_exits_zero_and_broken_suite_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            plugin = Path(temp) / "plugin"
            evals = plugin / "evals"
            evals.mkdir(parents=True)
            write_case(evals, "routing", graders={"uses-skill": TOOL_USED_SKILL})
            self.assertEqual(checker.main([str(plugin)]), 0)

            write_case(evals, "empty", graders={})
            self.assertEqual(checker.main([str(plugin)]), 1)


if __name__ == "__main__":
    unittest.main()
