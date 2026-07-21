#!/usr/bin/env python3
"""SessionStart-хук: компактная карта банков компетенций по уровням резолва.

Источник данных: `resolve.py --list --json` (не переоткрывает резолв,
не расширяет его контракт). `purpose` дочитывается из `DPF.md` пакета
(поле `name:`, fallback `kind`, fallback голый id).

Молчит (пустой stdout) при пустом наборе. Всегда завершается exit 0 —
хук non-blocking по контракту SessionStart.

Только stdlib.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

LEVEL_TITLES = {
    "project": "Проект:",
    "user": "Пользователь:",
    "plugin": "Плагины:",
}
LEVEL_ORDER = ["project", "user", "plugin"]

DEFAULT_MAX = 40


def resolve_script_path() -> str:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    return os.path.join(plugin_root, "skills", "dpf-apply", "scripts", "resolve.py")


def fetch_rows(resolve_path: str) -> list[dict]:
    """Вызывает `resolve.py --list --json`. Любая проблема -> []."""
    try:
        result = subprocess.run(
            ["python3", resolve_path, "--list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data


def read_purpose(path: str, kind: str, pkg_id: str) -> str:
    """`name:` из `<path>/DPF.md`; fallback `kind`; fallback голый id."""
    dpf_md = os.path.join(path, "DPF.md")
    try:
        with open(dpf_md, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("name:"):
                    value = stripped[len("name:") :].strip()
                    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
                        value = value[1:-1]
                    if value:
                        return value
                    break
    except OSError:
        pass
    return kind or pkg_id


def build_card_lines(rows: list[dict], purpose_fn, max_n: int) -> list[str]:
    """Чистая функция: строит текст карты по контракту Q5.

    purpose_fn(row) -> str. Затенённые строки пропускаются перед
    группировкой/усечением (id не показывается дважды).
    """
    visible = [row for row in rows if not row.get("shadowed")]

    by_level: dict[str, list[dict]] = {"project": [], "user": [], "plugin": []}
    for row in visible:
        level = row.get("level")
        if level in by_level:
            by_level[level].append(row)

    ordered: list[dict] = []
    for level in LEVEL_ORDER:
        ordered.extend(by_level[level])

    total = len(ordered)
    truncated = total > max_n
    shown = ordered[:max_n] if truncated else ordered

    shown_by_level: dict[str, list[dict]] = {"project": [], "user": [], "plugin": []}
    for row in shown:
        shown_by_level[row["level"]].append(row)

    lines: list[str] = []
    for level in LEVEL_ORDER:
        level_rows = shown_by_level[level]
        if not level_rows:
            continue
        lines.append(LEVEL_TITLES[level])
        for row in level_rows:
            purpose = purpose_fn(row)
            stale_suffix = " · протух" if row.get("stale") else ""
            lines.append(f'{row["id"]} — {purpose}{stale_suffix}')

    if truncated:
        remaining = total - max_n
        lines.append(f"…и ещё {remaining} — /fpf-integration:dpf-apply --list")

    return lines


def main() -> int:
    resolve_path = resolve_script_path()
    rows = fetch_rows(resolve_path)
    if not rows:
        return 0

    try:
        max_n = int(os.environ.get("DPF_SESSION_CARD_MAX", str(DEFAULT_MAX)))
    except ValueError:
        max_n = DEFAULT_MAX

    def purpose_fn(row: dict) -> str:
        return read_purpose(row.get("path", ""), row.get("kind", ""), row.get("id", ""))

    lines = build_card_lines(rows, purpose_fn, max_n)
    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
