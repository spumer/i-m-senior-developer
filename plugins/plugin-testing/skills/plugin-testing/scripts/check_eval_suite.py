#!/usr/bin/env python3
"""Проверка состава набора eval-кейсов плагина без расхода токенов.

Находит то, что незаметно превращает проверку в декорацию: кейс без критериев,
запрет инструмента, который кейсу не выдан, границу `max: 0` без `min: 0`,
неизвестный тип критерия, совпадающие имена критериев в одном кейсе.

Разбор frontmatter намеренно простой: только плоские ключи `key: value`, которых
достаточно для этих проверок. Полную схему кейса проверяет сам CLI при прогоне.

Использование:
  python3 check_eval_suite.py <plugin-dir>

Коды выхода: 0 — замечаний нет, 1 — есть замечания, 64 — ошибка вызова.

Только stdlib.
"""

from __future__ import annotations

import sys
from pathlib import Path

KNOWN_GRADER_TYPES = frozenset(
    {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}
)

# Инструменты, которые кейс не может выдать себе сам: их отдельно разрешает оператор.
OPERATOR_GRANTED_TOOLS = frozenset({"Bash", "Write", "Edit", "WebFetch", "WebSearch"})


def parse_frontmatter(text: str) -> dict[str, str]:
    """Плоские ключи frontmatter. Без frontmatter -> пустой словарь."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        if line[0] in " \t":
            continue  # вложенное значение — этим проверкам не нужно
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def parse_tool_list(raw: str) -> set[str]:
    """`[Read, Skill, Write]` -> {'Read', 'Skill', 'Write'}."""
    trimmed = raw.strip().strip("[]")
    return {item.strip().strip("\"'") for item in trimmed.split(",") if item.strip()}


def grader_files(case_dir: Path) -> list[Path]:
    graders_dir = case_dir / "graders"
    if not graders_dir.is_dir():
        return []
    return sorted(path for path in graders_dir.glob("*.md") if path.is_file())


def case_directories(evals_root: Path) -> list[Path]:
    return sorted(
        path
        for path in evals_root.iterdir()
        if path.is_dir() and (path / "prompt.md").is_file()
    )


def check_grader(
    fields: dict[str, str],
    case_name: str,
    grader_path: Path,
    requested_tools: set[str],
) -> list[str]:
    findings: list[str] = []
    grader_type = fields.get("type", "")
    if grader_type not in KNOWN_GRADER_TYPES:
        findings.append(
            f"{case_name}/{grader_path.name}: неизвестный тип критерия {grader_type!r}"
        )
        return findings

    if grader_type != "tool_used":
        return findings

    tool = fields.get("tool", "")
    if fields.get("max") == "0" and fields.get("min") != "0":
        findings.append(
            f"{case_name}/{grader_path.name}: `max: 0` без `min: 0` не запрещает вызов, "
            "потому что `min` по умолчанию равен 1"
        )
    forbids_call = fields.get("min") == "0" and fields.get("max") == "0"
    if forbids_call and tool in OPERATOR_GRANTED_TOOLS and tool not in requested_tools:
        findings.append(
            f"{case_name}/{grader_path.name}: запрет инструмента {tool} ничего не "
            f"доказывает — кейс не запрашивает его в allowed_tools"
        )
    return findings


def check_case(case_dir: Path) -> list[str]:
    case_name = case_dir.name
    prompt_fields = parse_frontmatter((case_dir / "prompt.md").read_text())
    requested_tools = parse_tool_list(prompt_fields.get("allowed_tools", ""))

    graders = grader_files(case_dir)
    if not graders:
        return [f"{case_name}: нет критериев — кейс ничего не проверяет"]

    findings: list[str] = []
    seen_names: dict[str, str] = {}
    for grader_path in graders:
        fields = parse_frontmatter(grader_path.read_text())
        findings.extend(check_grader(fields, case_name, grader_path, requested_tools))
        name = fields.get("name", grader_path.stem)
        if name in seen_names:
            findings.append(
                f"{case_name}: имя критерия {name!r} повторяется "
                f"({seen_names[name]} и {grader_path.name})"
            )
        else:
            seen_names[name] = grader_path.name
    return findings


def check_suite(plugin_dir: Path) -> list[str]:
    """Замечания по набору. Пустой список означает отсутствие замечаний."""
    evals_root = plugin_dir / "evals"
    if not evals_root.is_dir():
        return [f"{plugin_dir}: нет каталога evals"]

    cases = case_directories(evals_root)
    if not cases:
        return [f"{evals_root}: нет кейсов с prompt.md"]

    findings: list[str] = []
    for case_dir in cases:
        findings.extend(check_case(case_dir))
    return findings


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print("использование: check_eval_suite.py <plugin-dir>", file=sys.stderr)
        return 64
    findings = check_suite(Path(arguments[0]))
    if not findings:
        print("состав набора: замечаний нет")
        return 0
    for finding in findings:
        print(finding, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
