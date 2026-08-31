"""Run and verify the complete planner plugin eval suite."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import uuid


MINIMUM_CLAUDE_VERSION = "2.1.234"
EXPECTED_CASES = frozenset(
    {
        "baseline-provider-limits",
        "idea-routing",
        "multi-step-input",
    }
)
PLUGIN_PATHS = (
    "plugins/planner",
    "plugins/planner/commands",
    "plugins/planner/skills",
    "plugins/planner/agents",
)


class RunnerError(RuntimeError):
    pass


def run_claude(
    claude_bin: str,
    arguments: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [claude_bin, *arguments],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise RunnerError(f"Claude CLI not found: {claude_bin}") from error


def command_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )


def version_key(version: str) -> tuple[int, ...]:
    parts = version.split(".")
    if not all(part.isdecimal() for part in parts):
        raise RunnerError(
            f"Claude Code version {version!r} could not be compared with the "
            f"required minimum {MINIMUM_CLAUDE_VERSION}: expected numbers "
            "separated by dots"
        )
    return tuple(int(part) for part in parts)


def require_claude_version(claude_bin: str, repo_root: Path) -> None:
    result = run_claude(claude_bin, ["--version"], repo_root)
    output = command_output(result)
    if result.returncode != 0:
        raise RunnerError(
            f"claude --version failed with code {result.returncode}: {output}"
        )
    actual = output.split(maxsplit=1)[0] if output else "<empty output>"
    if version_key(actual) < version_key(MINIMUM_CLAUDE_VERSION):
        raise RunnerError(
            "Claude Code is older than the eval contract allows: "
            f"needs {MINIMUM_CLAUDE_VERSION} or newer, got {actual}"
        )


def require_open_eval_gate(claude_bin: str) -> None:
    with tempfile.TemporaryDirectory(prefix="planner-eval-gate-") as directory:
        result = run_claude(claude_bin, ["plugin", "eval"], Path(directory))
    output = command_output(result)
    if result.returncode == 1 and "No eval cases found" in output:
        return
    raise RunnerError(
        "claude plugin eval gate probe failed: "
        f"expected code 1 with 'No eval cases found', got code "
        f"{result.returncode}: {output}"
    )


def validate_plugin(claude_bin: str, repo_root: Path) -> None:
    for path in PLUGIN_PATHS:
        result = run_claude(
            claude_bin,
            ["plugin", "validate", path, "--strict"],
            repo_root,
        )
        if result.returncode != 0:
            raise RunnerError(
                f"plugin validation failed for {path} with code "
                f"{result.returncode}: {command_output(result)}"
            )


def fresh_output_path(results_root: Path) -> Path:
    results_root.mkdir(parents=True, exist_ok=True)
    for _ in range(10):
        candidate = results_root / f"run-{uuid.uuid4().hex}"
        if not candidate.exists():
            return candidate
    raise RunnerError(f"could not allocate a fresh output path under {results_root}")


def eval_arguments(max_cost_usd: str, output_dir: Path) -> list[str]:
    return [
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
        max_cost_usd,
        "--output-dir",
        str(output_dir),
    ]


def run_eval(
    claude_bin: str,
    repo_root: Path,
    max_cost_usd: str,
    output_dir: Path,
) -> None:
    result = run_claude(
        claude_bin,
        eval_arguments(max_cost_usd, output_dir),
        repo_root,
    )
    if result.returncode != 0:
        raise RunnerError(
            f"claude plugin eval failed with code {result.returncode}: "
            f"{command_output(result)}"
        )


def require_mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunnerError(f"{location} must be a JSON object")
    return value


def require_list(value: object, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise RunnerError(f"{location} must be a JSON array")
    return value


def require_one(value: object, location: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != 1:
        raise RunnerError(f"{location} must equal 1, got {value!r}")


def require_top_level(result: dict[str, Any]) -> None:
    if type(result.get("schemaVersion")) is not int or result["schemaVersion"] != 1:
        raise RunnerError("schemaVersion must be integer 1")
    if result.get("partial") is not False:
        raise RunnerError("partial must be false")
    aggregates = require_mapping(result.get("aggregates"), "aggregates")
    expected_case_count = len(EXPECTED_CASES)
    if aggregates.get("casesTotal") != expected_case_count:
        raise RunnerError(
            f"aggregates.casesTotal must equal {expected_case_count}"
        )
    if aggregates.get("casesPassed") != expected_case_count:
        raise RunnerError(
            f"aggregates.casesPassed must equal {expected_case_count}"
        )
    require_one(aggregates.get("overallScore"), "aggregates.overallScore")


def indexed_cases(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = require_list(result.get("cases"), "cases")
    indexed: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(cases):
        case = require_mapping(value, f"cases[{index}]")
        name = case.get("name")
        if not isinstance(name, str):
            raise RunnerError(f"cases[{index}].name must be a string")
        if name in indexed:
            raise RunnerError(f"duplicate eval case: {name}")
        indexed[name] = case
    actual = set(indexed)
    if actual != EXPECTED_CASES:
        missing = ", ".join(sorted(EXPECTED_CASES - actual)) or "none"
        unexpected = ", ".join(sorted(actual - EXPECTED_CASES)) or "none"
        raise RunnerError(
            f"cases must match the expected set; missing: {missing}; "
            f"unexpected: {unexpected}"
        )
    return indexed


def require_run(run: object, location: str) -> None:
    value = require_mapping(run, location)
    if value.get("passed") is not True:
        raise RunnerError(f"{location}.passed must be true")
    require_one(value.get("score"), f"{location}.score")
    if value.get("skippedPaidGraders") is not False:
        raise RunnerError(f"{location}.skippedPaidGraders must be false")


def require_case(case: dict[str, Any], name: str) -> None:
    aggregates = require_mapping(case.get("aggregates"), f"case {name}.aggregates")
    require_one(aggregates.get("score"), f"case {name}.aggregates.score")
    arms = require_mapping(case.get("arms"), f"case {name}.arms")
    runs = require_list(arms.get("with"), f"case {name}.arms.with")
    if len(runs) != 3:
        raise RunnerError(
            f"case {name}.arms.with must contain exactly 3 runs, got {len(runs)}"
        )
    for index, run in enumerate(runs):
        require_run(run, f"case {name}.arms.with[{index}]")


def validate_result(result: object) -> tuple[object, int]:
    document = require_mapping(result, "aggregate-result.json")
    cases = indexed_cases(document)
    require_top_level(document)
    for name, case in cases.items():
        require_case(case, name)
    cost_usd = document.get("costUsd")
    if isinstance(cost_usd, bool) or not isinstance(cost_usd, (int, float)):
        raise RunnerError("costUsd must be a JSON number")
    return cost_usd, len(cases)


def load_result(output_dir: Path) -> object:
    aggregate_path = output_dir / "aggregate-result.json"
    report_path = output_dir / "report.html"
    if not aggregate_path.is_file():
        raise RunnerError(f"missing aggregate-result.json in {output_dir}")
    if not report_path.is_file():
        raise RunnerError(f"missing report.html in {output_dir}")
    try:
        return json.loads(aggregate_path.read_text())
    except json.JSONDecodeError as error:
        raise RunnerError(
            f"aggregate-result.json must contain valid JSON: {error}"
        ) from error


def main(arguments: list[str]) -> int:
    if arguments:
        raise RunnerError("this runner does not accept arguments")
    repo_root = Path(__file__).resolve().parents[3]
    claude_bin = os.environ.get("CLAUDE_BIN", "claude")
    results_root = Path(
        os.environ.get(
            "PLANNER_EVAL_RESULTS_ROOT",
            str(repo_root / "plugins/planner/evals/results"),
        )
    ).expanduser()
    max_cost_usd = os.environ.get("MAX_COST_USD", "6.00")

    require_claude_version(claude_bin, repo_root)
    require_open_eval_gate(claude_bin)
    validate_plugin(claude_bin, repo_root)
    output_dir = fresh_output_path(results_root)
    run_eval(claude_bin, repo_root, max_cost_usd, output_dir)
    cost_usd, case_count = validate_result(load_result(output_dir))
    print(f"OK: output={output_dir} costUsd={cost_usd} cases={case_count}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RunnerError as error:
        print(f"planner eval runner: {error}", file=sys.stderr)
        raise SystemExit(1)
