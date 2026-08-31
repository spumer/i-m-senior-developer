#!/usr/bin/env python3
"""Резолвер пакетов компетенций (DPF/LPF, FPF E.4.DPF) по уровням.

Уровни поиска (по приоритету, первый выигрывает при затенении):
  1. project  — $PWD/.claude/frameworks
  2. user     — ~/.claude/frameworks
  3. plugin   — пути построчно из ~/.claude/frameworks.paths, затем
                ~/.claude/frameworks.published (если файлы есть; строки,
                начинающиеся с '#', и пустые строки пропускаются)

Пакет = каталог <root>/<ID>/ с файлом DPF.md внутри. Полный id вида
"plugin:<ID>" минует уровни project/user и ищет только среди plugin-путей.

Только stdlib. Никаких внешних YAML-парсеров — читаем YAML-frontmatter
DPF.md простым построчным разбором `key: value` (формат авторингового
конвейера dpf-authoring: все нужные поля однострочные).

CLI:
  resolve.py <id> [--json]
  resolve.py --list [--json]
  resolve.py --sources [--json]

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


def read_source_paths(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    roots = []
    with open(path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line and not line.startswith("#"):
                roots.append(os.path.expanduser(line))
    return roots


def build_source_rows() -> list[tuple[str, str, str]]:
    home = os.path.expanduser("~")
    claude_dir = os.path.join(home, ".claude")
    rows = [
        ("project", "project", os.path.join(os.getcwd(), ".claude", "frameworks")),
        ("user", "user", os.path.join(claude_dir, "frameworks")),
    ]
    rows.extend(("plugin", "paths", root) for root in read_source_paths(os.path.join(claude_dir, "frameworks.paths")))
    rows.extend(("plugin", "published", root) for root in read_source_paths(os.path.join(claude_dir, "frameworks.published")))
    return rows


def published_roots() -> set[str]:
    """Корни, объявленные хуком публикации, а не человеком.

    Указатель на корень публикацией отдельного пакета не является, поэтому
    пакеты из такого корня проходят банковский допуск. Корень, названный
    человеком в `frameworks.paths`, остаётся вне допуска: ответственность за
    него взял человек, и тот же корень в списке публикации ничего не меняет.
    """
    published: set[str] = set()
    declared_by_human: set[str] = set()
    for _level, origin, root in build_source_rows():
        canonical = os.path.realpath(root)
        if origin == "published":
            if canonical not in declared_by_human:
                published.add(canonical)
        else:
            declared_by_human.add(canonical)
    return published


def build_levels() -> list[tuple[str, str]]:
    levels = []
    seen_roots = set()
    for level, _origin, root in build_source_rows():
        canonical_root = os.path.realpath(root)
        if canonical_root in seen_roots:
            continue
        seen_roots.add(canonical_root)
        levels.append((level, root))
    return levels


def parse_frontmatter(dpf_md_path: str) -> dict[str, str]:
    try:
        with open(dpf_md_path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeError) as exc:
        print(f"unreadable DPF.md: {dpf_md_path}: {exc}", file=sys.stderr)
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


KIND_ENUM = {"Domain Principle Framework", "Local Practice Framework"}
REQUIRED_FIELDS = ("dpf_id", "kind", "status", "review_due", "owner")

# Гейтящие проверки по области: local-авторинг пропускает свежесть/вердикт;
# bank fail-closed гейтит всё. Ключ используют и run_verify, и печать финала.
GATING = {
    "local": ("resolve", "structure", "kind"),
    "bank": ("resolve", "structure", "kind", "freshness", "conformance"),
}

_CONFORMANCE_MARKER = "E.4.DPF.DA:"
_ADMISSIBLE_TOKEN = "admissibleForDeclaredDPFUse"


def read_conformance_verdict(dpf_md_path: str) -> tuple[bool, str | None]:
    """Читает авторитетный вердикт E.4.DPF.DA из самого DPF.md.

    Источник истины — ПОСЛЕДНЯЯ строка '> conformance:', несущая маркер
    'E.4.DPF.DA:'; статус — токен сразу за маркером. references/ не сканируется:
    там несколько вердиктов разных раундов и токен встречается в отрицаниях
    (false-positive). admissible только если токен ровно admissibleForDeclaredDPFUse.
    """
    try:
        with open(dpf_md_path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeError) as exc:
        print(f"unreadable DPF.md: {dpf_md_path}: {exc}", file=sys.stderr)
        return False, None
    verdict_line = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> conformance:") and _CONFORMANCE_MARKER in stripped:
            verdict_line = stripped
    if verdict_line is None:
        return False, None
    after = verdict_line.split(_CONFORMANCE_MARKER, 1)[1].split()
    token = after[0] if after else ""
    return token == _ADMISSIBLE_TOKEN, token or None


def run_verify(id_arg: str, scope: str, levels: list[tuple[str, str]]) -> tuple[dict, int]:
    checks: list[dict] = []
    info, _ = resolve_id(id_arg, levels)
    checks.append({"name": "resolve", "ok": info is not None,
                   "reason": None if info is not None else f"not found: {id_arg}"})
    if info is None:
        return {"id": id_arg, "scope": scope, "checks": checks, "ok": False}, 1

    dpf_md = os.path.join(info["path"], "DPF.md")
    fm = parse_frontmatter(dpf_md)

    missing = next((name for name in REQUIRED_FIELDS if not fm.get(name, "").strip()), None)
    checks.append({"name": "structure", "ok": missing is None,
                   "reason": None if missing is None else f"missing field: {missing}"})

    kind = fm.get("kind", "").strip()
    kind_ok = kind in KIND_ENUM
    checks.append({"name": "kind", "ok": kind_ok,
                   "reason": None if kind_ok else f"kind not in enum: {kind}"})

    stale, stale_reason = check_stale(fm.get("status", "").strip(), fm.get("review_due", "").strip())
    checks.append({"name": "freshness", "ok": not stale, "reason": stale_reason})

    admissible, _token = read_conformance_verdict(dpf_md)
    checks.append({"name": "conformance", "ok": admissible,
                   "reason": None if admissible else "no admissible E.4.DPF.DA conformance line in DPF.md"})

    gating = GATING[scope]
    overall_ok = all(c["ok"] for c in checks if c["name"] in gating)
    return {"id": id_arg, "scope": scope, "checks": checks, "ok": overall_ok}, (0 if overall_ok else 2)


def build_info(
    pkg_id: str, pkg_dir: str, level_name: str, published: set[str] | None = None
) -> dict:
    dpf_md = os.path.join(pkg_dir, "DPF.md")
    fm = parse_frontmatter(dpf_md)
    status = fm.get("status", "")
    review_due = fm.get("review_due", "")
    stale, reason = check_stale(status, review_due)
    executable = os.path.isfile(os.path.join(pkg_dir, "assets", "apply-prompt.md"))
    # Набор считается сам, если его не передали: забытый аргумент обязан
    # приводить к допуску, а не к его обходу.
    roots = published_roots() if published is None else published
    from_published = os.path.realpath(os.path.dirname(pkg_dir)) in roots
    admissible = read_conformance_verdict(dpf_md)[0] if from_published else None
    return {
        "published": from_published,
        "admissible": admissible,
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
    roots = published_roots()
    for level_name, root in search_levels:
        searched.append(f"{level_name}:{root}")
        pkg_dir = os.path.join(root, bare_id)
        if os.path.isfile(os.path.join(pkg_dir, "DPF.md")):
            return build_info(bare_id, pkg_dir, level_name, roots), searched
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
    roots = published_roots()
    for level_name, root in levels:
        for pkg_id, pkg_dir in iter_packages(root):
            shadowed = pkg_id in seen
            info = build_info(pkg_id, pkg_dir, level_name, roots)
            info["shadowed"] = shadowed
            if not shadowed:
                seen[pkg_id] = pkg_dir
            rows.append(info)
    return rows


def list_sources() -> list[dict]:
    return [
        {
            "level": level,
            "origin": origin,
            "path": root,
            "exists": os.path.isdir(root),
        }
        for level, origin, root in build_source_rows()
    ]


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
    if info["published"]:
        print(f'  допуск:      {"подтверждён" if info["admissible"] else "не подтверждён"}')


def print_list_human(rows: list[dict]) -> None:
    if not rows:
        print("(пакетов не найдено ни на одном уровне)")
        return
    for row in rows:
        shadow_note = " [shadowed]" if row["shadowed"] else ""
        stale_note = " [stale]" if row["stale"] else ""
        admission_note = " [без допуска]" if row["published"] and not row["admissible"] else ""
        print(f'{row["id"]:<32} {row["level"]:<8} {row["kind"]:<28} {row["status"]:<10}{shadow_note}{stale_note}{admission_note}')


def print_sources_human(rows: list[dict]) -> None:
    for row in rows:
        exists = "yes" if row["exists"] else "no"
        print(f'{row["level"]:<8} {row["origin"]:<9} {row["path"]} exists={exists}')


def print_verify_human(result: dict) -> None:
    for c in result["checks"]:
        status = "PASS" if c["ok"] else "FAIL"
        suffix = f"  {c['reason']}" if c["reason"] else ""
        print(f"{status}  {c['name']}{suffix}")
    if result["ok"]:
        print(f'verify: PASS (scope={result["scope"]})')
    else:
        gating = GATING[result["scope"]]
        first = next(c["reason"] for c in result["checks"] if c["name"] in gating and not c["ok"])
        print(f"verify: FAIL — {first}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Резолвер пакетов компетенций (DPF/LPF).")
    parser.add_argument("id", nargs="?", help="id пакета, опц. с префиксом plugin:")
    parser.add_argument("--list", action="store_true", help="показать слитую карту по всем уровням")
    parser.add_argument("--sources", action="store_true", help="показать источники уровней")
    parser.add_argument("--verify", action="store_true", help="проверить пригодность пакета (гейт)")
    parser.add_argument("--scope", choices=["local", "bank"], default="local",
                        help="область гейта для --verify (дефолт local)")
    parser.add_argument("--json", action="store_true", help="вывод в JSON")
    args = parser.parse_args()

    levels = build_levels()

    if args.verify:
        if not args.id:
            parser.error("нужен <id> для --verify")
        result, code = run_verify(args.id, args.scope, levels)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_verify_human(result)
        return code

    if args.sources:
        rows = list_sources()
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print_sources_human(rows)
        return 0

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

    if info["published"] and not info["admissible"]:
        print(
            f'допуск не подтверждён: {info["id"]} лежит в опубликованном корне, '
            "но в его DPF.md нет строки допуска E.4.DPF.DA",
            file=sys.stderr,
        )
        return 2

    return 2 if info["stale"] else 0


if __name__ == "__main__":
    sys.exit(main())
