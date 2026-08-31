import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
from typing import TypedDict, cast
import unittest


RUNNER = Path(__file__).with_name("run.py")
REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_CASES = (
    "baseline-provider-limits",
    "idea-routing",
    "multi-step-input",
)


class ClaudeCall(TypedDict):
    argv: list[str]
    cwd: str


FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys


CASE_NAMES = $EXPECTED_CASES


def log_call(argv):
    log_path = Path(os.environ["FAKE_CLAUDE_LOG"])
    with log_path.open("a") as stream:
        stream.write(json.dumps({"argv": argv, "cwd": os.getcwd()}) + "\n")


def valid_result():
    cases = []
    for case_name in CASE_NAMES:
        runs = []
        for index in range(3):
            runs.append({
                "passed": True,
                "score": 1,
                "skippedPaidGraders": False,
                "error": (
                    "AskUserQuestion is unavailable in headless mode"
                    if case_name == "idea-routing" and index == 0
                    else None
                ),
            })
        cases.append({
            "name": case_name,
            "aggregates": {"score": 1},
            "arms": {"with": runs},
        })
    return {
        "schemaVersion": 1,
        "costUsd": 0.42,
        "partial": False,
        "cases": cases,
        "aggregates": {
            "casesTotal": len(CASE_NAMES),
            "casesPassed": len(CASE_NAMES),
            "overallScore": 1,
        },
    }


def write_fixture(output_dir, fixture):
    if output_dir.exists():
        print(f"output directory already exists: {output_dir}", file=sys.stderr)
        raise SystemExit(90)
    output_dir.mkdir(parents=True)
    result = valid_result()
    if fixture == "partial":
        result["partial"] = True
    elif fixture == "missing-case":
        result["cases"].pop()
        case_count = len(result["cases"])
        result["aggregates"]["casesTotal"] = case_count
        result["aggregates"]["casesPassed"] = case_count
    elif fixture == "two-runs":
        result["cases"][0]["arms"]["with"].pop()
    elif fixture == "skipped-paid-graders":
        result["cases"][0]["arms"]["with"][0]["skippedPaidGraders"] = True

    aggregate = output_dir / "aggregate-result.json"
    if fixture == "broken-json":
        aggregate.write_text("{broken")
    elif fixture != "missing-json":
        aggregate.write_text(json.dumps(result))
    if fixture != "missing-report":
        (output_dir / "report.html").write_text("<html>report</html>")


argv = sys.argv[1:]
log_call(argv)

if argv == ["--version"]:
    print(os.environ.get("FAKE_CLAUDE_VERSION", "2.1.234 (Claude Code)"))
    raise SystemExit(0)

if argv == ["plugin", "eval"]:
    gate = os.environ.get("FAKE_CLAUDE_GATE", "open")
    if gate == "open":
        print("No eval cases found", file=sys.stderr)
        raise SystemExit(1)
    if gate == "closed":
        print("`plugin eval` is currently in early access", file=sys.stderr)
        raise SystemExit(1)
    print("unexpected gate response", file=sys.stderr)
    raise SystemExit(0)

if len(argv) == 4 and argv[:2] == ["plugin", "validate"] and argv[3] == "--strict":
    raise SystemExit(0)

if argv[:3] == ["plugin", "eval", "plugins/planner"]:
    exit_code = int(os.environ.get("FAKE_CLAUDE_EVAL_EXIT", "0"))
    if exit_code:
        print(f"eval stopped with code {exit_code}", file=sys.stderr)
        raise SystemExit(exit_code)
    output_dir = Path(argv[argv.index("--output-dir") + 1])
    write_fixture(output_dir, os.environ.get("FAKE_CLAUDE_FIXTURE", "valid"))
    raise SystemExit(0)

print(f"unsupported fake invocation: {argv}", file=sys.stderr)
raise SystemExit(91)
'''.replace("$EXPECTED_CASES", repr(EXPECTED_CASES))


class PlannerEvalRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.foreign_cwd = self.root / "foreign-cwd"
        self.foreign_cwd.mkdir()
        self.results_root = self.root / "results"
        self.log_path = self.root / "claude-calls.jsonl"
        self.fake_claude = self.root / "fake-claude"
        self.fake_claude.write_text(textwrap.dedent(FAKE_CLAUDE))
        self.fake_claude.chmod(0o755)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_runner(
        self,
        *args: str,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CLAUDE_BIN": str(self.fake_claude),
                "FAKE_CLAUDE_LOG": str(self.log_path),
                "PLANNER_EVAL_RESULTS_ROOT": str(self.results_root),
            }
        )
        env.pop("MAX_COST_USD", None)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(RUNNER), *args],
            cwd=self.foreign_cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def calls(self) -> list[ClaudeCall]:
        if not self.log_path.exists():
            return []
        return [
            cast(ClaudeCall, json.loads(line))
            for line in self.log_path.read_text().splitlines()
        ]

    def actual_eval_call(self) -> ClaudeCall:
        return next(
            call
            for call in self.calls()
            if call["argv"][:3] == ["plugin", "eval", "plugins/planner"]
        )

    def test__runner__valid_eval__runs_preflight_and_reports_success(self) -> None:
        result = self.run_runner()

        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(calls[0]["argv"], ["--version"])
        self.assertEqual(calls[1]["argv"], ["plugin", "eval"])
        self.assertNotEqual(calls[1]["cwd"], str(self.foreign_cwd))

        expected_validations = [
            ["plugin", "validate", path, "--strict"]
            for path in (
                "plugins/planner",
                "plugins/planner/commands",
                "plugins/planner/skills",
                "plugins/planner/agents",
            )
        ]
        validations = [
            call for call in calls if call["argv"][:2] == ["plugin", "validate"]
        ]
        self.assertEqual(
            [call["argv"] for call in validations], expected_validations
        )
        self.assertEqual(
            {call["cwd"] for call in validations}, {str(REPO_ROOT)}
        )

        actual_eval = self.actual_eval_call()
        argv = actual_eval["argv"]
        output_dir = Path(argv[-1])
        self.assertEqual(
            argv,
            [
                "plugin",
                "eval",
                "plugins/planner",
                "--ablation",
                "none",
                "--runs",
                "3",
                "--allow-tools",
                "Write",
                "--no-scaffold",
                "--no-publish",
                "--threshold",
                "1.0",
                "--model",
                "opus",
                "--judge-model",
                "haiku",
                "--max-cost-usd",
                "6.00",
                "--output-dir",
                str(output_dir),
            ],
        )
        self.assertEqual(actual_eval["cwd"], str(REPO_ROOT))
        self.assertEqual(output_dir.parent, self.results_root)
        self.assertTrue((output_dir / "aggregate-result.json").is_file())
        self.assertTrue((output_dir / "report.html").is_file())
        self.assertIn(str(output_dir), result.stdout)
        self.assertIn("costUsd=0.42", result.stdout)
        self.assertIn(f"cases={len(EXPECTED_CASES)}", result.stdout)
        self.assertEqual(result.stderr, "")

    def test__runner__invalid_result_fixture__fails_with_reason(self) -> None:
        cases = (
            ("partial", "partial"),
            # Фикстура снимает последний случай, поэтому ожидание берётся из
            # состава: при правке набора имя не должно отставать молча.
            ("missing-case", EXPECTED_CASES[-1]),
            ("two-runs", "exactly 3"),
            ("skipped-paid-graders", "skippedPaidGraders"),
            ("broken-json", "valid JSON"),
            ("missing-json", "aggregate-result.json"),
            ("missing-report", "report.html"),
        )

        for fixture, expected_error in cases:
            with self.subTest(fixture=fixture):
                self.log_path.unlink(missing_ok=True)

                result = self.run_runner(
                    extra_env={"FAKE_CLAUDE_FIXTURE": fixture}
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr)

    def test__runner__version_at_or_above_minimum__runs_the_eval(self) -> None:
        for version in ("2.1.234", "2.1.238", "2.1.1000", "2.2.0", "3.0.0"):
            with self.subTest(version=version):
                self.log_path.unlink(missing_ok=True)

                result = self.run_runner(
                    extra_env={"FAKE_CLAUDE_VERSION": f"{version} (Claude Code)"}
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.actual_eval_call()["cwd"], str(REPO_ROOT))

    def test__runner__version_below_minimum__fails_before_gate(self) -> None:
        for version in ("2.1.233", "2.1.99", "2.1", "2.0.999", "1.9.9"):
            with self.subTest(version=version):
                self.log_path.unlink(missing_ok=True)

                result = self.run_runner(
                    extra_env={"FAKE_CLAUDE_VERSION": f"{version} (Claude Code)"}
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("2.1.234", result.stderr)
                self.assertIn(version, result.stderr)
                self.assertEqual(
                    [call["argv"] for call in self.calls()],
                    [["--version"]],
                )
                self.assertEqual(list(self.results_root.glob("*")), [])

    def test__runner__uncomparable_version__fails_before_gate(self) -> None:
        for version in ("nonsense", "2.1.x", "2.1.4-beta.1", ""):
            with self.subTest(version=version):
                self.log_path.unlink(missing_ok=True)

                result = self.run_runner(
                    extra_env={"FAKE_CLAUDE_VERSION": version}
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("could not be compared", result.stderr)
                self.assertEqual(
                    [call["argv"] for call in self.calls()],
                    [["--version"]],
                )
                self.assertEqual(list(self.results_root.glob("*")), [])

    def test__runner__closed_gate__fails_before_validation(self) -> None:
        result = self.run_runner(extra_env={"FAKE_CLAUDE_GATE": "closed"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("early access", result.stderr)
        self.assertEqual(
            [call["argv"] for call in self.calls()],
            [["--version"], ["plugin", "eval"]],
        )

    def test__runner__nonzero_eval_exit__fails_for_every_exit_code(self) -> None:
        for exit_code in (1, 2, 130):
            with self.subTest(exit_code=exit_code):
                self.log_path.unlink(missing_ok=True)

                result = self.run_runner(
                    extra_env={"FAKE_CLAUDE_EVAL_EXIT": str(exit_code)}
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"code {exit_code}", result.stderr)
                self.assertEqual(list(self.results_root.glob("*")), [])

    def test__runner__positional_argument__fails_before_claude(self) -> None:
        result = self.run_runner("unexpected")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not accept arguments", result.stderr)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
