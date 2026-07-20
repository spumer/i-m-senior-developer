#!/usr/bin/env python3
"""Резолвер пакетов компетенций (DPF/LPF, FPF E.4.DPF) по уровням.

Уровни поиска (по приоритету, первый выигрывает при затенении):
  1. project  — $PWD/.claude/frameworks
  2. user     — ~/.claude/frameworks
  3. plugin   — пути построчно из ~/.claude/frameworks.paths (если файл есть;
                строки, начинающиеся с '#', и пустые строки пропускаются)

Пакет = каталог <root>/<ID>/ с файлом DPF.md внутри. Полный id вида
"plugin:<ID>" минует уровни project/user и ищет только среди plugin-путей.

Только stdlib. Никаких внешних YAML-парсеров — читаем YAML-frontmatter
DPF.md простым построчным разбором `key: value` (формат авторингового
конвейера dpf-authoring: все нужные поля однострочные).

CLI:
  resolve.py <id> [--json]
  resolve.py --list [--json]

Exit-коды (для одиночного <id>):
  0 — пакет найден и свеж (status=active, review_due не истёк)
  1 — пакет не найден ни на одном уровне
  2 — пакет найден, но протух (status!=active или review_due истёк/отсутствует
      или не парсится) — вывод содержит причину и владельца (owner) для
      эскалации; работа по протухшему своду запрещена (см. SKILL.md).

--list всегда завершается кодом 0 (информационный режим).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys


def build_levels() -> list[tuple[str, str]]:
    levels = [
        ("project", os.path.join(os.getcwd(), ".claude", "frameworks")),
        ("user", os.path.join(os.path.expanduser("~"), ".claude", "frameworks")),
    ]
    paths_file = os.path.join(os.path.expanduser("~"), ".claude", "frameworks.paths")
    if os.path.isfile(paths_file):
        with open(paths_file, encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                levels.append(("plugin", os.path.expanduser(line)))
    return levels


def parse_frontmatter(dpf_md_path: str) -> dict[str, str]:
    try:
        with open(dpf_md_path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError:
        return {}

    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.rstrip("\n")
        if stripped.strip() == "---":
            break
        if not stripped.strip() or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        fields[key] = value
    return fields


def parse_list_value(value: str) -> list[str] | str:
    """Скобочный frontmatter-список ("[\"a\", \"b\"]") -> настоящий список для --json."""
    if not (value.startswith("[") and value.endswith("]")):
        return value
    items = []
    for part in value[1:-1].split(","):
        item = part.strip()
        if item.startswith('"') and item.endswith('"') and len(item) >= 2:
            item = item[1:-1]
        elif item.startswith("'") and item.endswith("'") and len(item) >= 2:
            item = item[1:-1]
        if item:
            items.append(item)
    return items


def check_stale(status: str, review_due: str) -> tuple[bool, str | None]:
    reasons = []
    if status != "active":
        reasons.append(f'status={status or "?"} (не active)')
    if not review_due:
        reasons.append("review_due отсутствует")
    else:
        try:
            due = dt.date.fromisoformat(review_due)
        except ValueError:
            reasons.append(f"review_due={review_due} не парсится как YYYY-MM-DD")
        else:
            if due < dt.date.today():
                reasons.append(f"review_due={review_due} истёк")
    if reasons:
        return True, "; ".join(reasons)
    return False, None


def build_info(pkg_id: str, pkg_dir: str, level_name: str) -> dict:
    dpf_md = os.path.join(pkg_dir, "DPF.md")
    fm = parse_frontmatter(dpf_md)
    status = fm.get("status", "")
    review_due = fm.get("review_due", "")
    stale, reason = check_stale(status, review_due)
    executable = os.path.isfile(os.path.join(pkg_dir, "assets", "apply-prompt.md"))
    return {
        "id": fm.get("dpf_id", pkg_id),
        "path": pkg_dir,
        "level": level_name,
        "kind": fm.get("kind", ""),
        "owner": parse_list_value(fm.get("owner", "")),
        "status": status,
        "review_due": review_due,
        "date": fm.get("date", ""),
        "executable": executable,
        "stale": stale,
        "stale_reason": reason,
    }


def resolve_id(id_arg: str, levels: list[tuple[str, str]]) -> tuple[dict | None, list[str]]:
    if id_arg.startswith("plugin:"):
        bare_id = id_arg[len("plugin:") :]
        search_levels = [(lvl, root) for lvl, root in levels if lvl == "plugin"]
    else:
        bare_id = id_arg
        search_levels = levels

    searched = []
    for level_name, root in search_levels:
        searched.append(f"{level_name}:{root}")
        pkg_dir = os.path.join(root, bare_id)
        if os.path.isfile(os.path.join(pkg_dir, "DPF.md")):
            return build_info(bare_id, pkg_dir, level_name), searched
    return None, searched


def iter_packages(root: str):
    if not os.path.isdir(root):
        return
    for name in sorted(os.listdir(root)):
        pkg_dir = os.path.join(root, name)
        if os.path.isfile(os.path.join(pkg_dir, "DPF.md")):
            yield name, pkg_dir


def list_all(levels: list[tuple[str, str]]) -> list[dict]:
    seen: dict[str, str] = {}
    rows: list[dict] = []
    for level_name, root in levels:
        for pkg_id, pkg_dir in iter_packages(root):
            shadowed = pkg_id in seen
            info = build_info(pkg_id, pkg_dir, level_name)
            info["shadowed"] = shadowed
            if not shadowed:
                seen[pkg_id] = pkg_dir
            rows.append(info)
    return rows


def print_info_human(info: dict) -> None:
    print(info["id"])
    print(f'  path:        {info["path"]}')
    print(f'  level:       {info["level"]}')
    print(f'  kind:        {info["kind"] or "?"}')
    owner = info["owner"]
    owner_text = ", ".join(owner) if isinstance(owner, list) else owner
    print(f'  owner:       {owner_text or "?"}')
    print(f'  status:      {info["status"] or "?"}')
    print(f'  review_due:  {info["review_due"] or "?"}')
    executable_note = "assets/apply-prompt.md найден" if info["executable"] else "ground-only, assets/apply-prompt.md отсутствует"
    print(f'  executable:  {"да" if info["executable"] else "нет"} ({executable_note})')
    print(f'  fresh:       {"нет" if info["stale"] else "да"}')
    if info["stale"]:
        print(f'  stale_reason: {info["stale_reason"]}')


def print_list_human(rows: list[dict]) -> None:
    if not rows:
        print("(пакетов не найдено ни на одном уровне)")
        return
    for row in rows:
        shadow_note = " [shadowed]" if row["shadowed"] else ""
        stale_note = " [stale]" if row["stale"] else ""
        print(f'{row["id"]:<32} {row["level"]:<8} {row["kind"]:<28} {row["status"]:<10}{shadow_note}{stale_note}')


def main() -> int:
    parser = argparse.ArgumentParser(description="Резолвер пакетов компетенций (DPF/LPF).")
    parser.add_argument("id", nargs="?", help="id пакета, опц. с префиксом plugin:")
    parser.add_argument("--list", action="store_true", help="показать слитую карту по всем уровням")
    parser.add_argument("--json", action="store_true", help="вывод в JSON")
    args = parser.parse_args()

    levels = build_levels()

    if args.list:
        rows = list_all(levels)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print_list_human(rows)
        return 0

    if not args.id:
        parser.error("нужен <id> либо --list")

    info, searched = resolve_id(args.id, levels)

    if info is None:
        if args.json:
            print(json.dumps({"id": args.id, "found": False, "searched": searched}, ensure_ascii=False, indent=2))
        else:
            print(f"не найден: {args.id}", file=sys.stderr)
            print(f'  искали в: {", ".join(searched)}', file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print_info_human(info)

    return 2 if info["stale"] else 0


if __name__ == "__main__":
    sys.exit(main())
