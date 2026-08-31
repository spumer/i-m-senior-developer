#!/usr/bin/env python3
"""UserPromptSubmit-хук: подсказка на релевантные пакеты компетенций.

Два независимых канала:
  1. Точный id в промпте — регулярка `(?:DPF|LPF)-[\\w-]+` (unicode),
     каждый матч валидируется против набора id из `resolve.py --list --json`.
  2. Cue-совпадение — колонка `cues` в `competency-map.md` каждого уровня,
     word-boundary case-insensitive substring-матч. Смысловое сопоставление
     хук не делает — только выкладывает совпадения.

Дедуп по id, кап 3 подсказки на промпт. Ни id, ни cue не найдены -> молчит.
Дедуп в пределах сессии: уже подсказанный в этой сессии свод повторно не
всплывает (стор по `session_id` в temp; fail-open — проблема со стором не
глушит подсказки и не роняет хук).
Никогда не применяет пакет и никогда не блокирует промпт (exit 0 всегда).

Только stdlib.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

ID_PATTERN = re.compile(r"(?:DPF|LPF)-[\w-]+", re.UNICODE)
MAX_HINTS = 3


def resolve_script_path() -> str:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    return os.path.join(plugin_root, "skills", "dpf-apply", "scripts", "resolve.py")


def fetch_known_ids(resolve_path: str) -> set[str]:
    """Вызывает `resolve.py --list --json`, возвращает набор известных id. Любая проблема -> set()."""
    try:
        result = subprocess.run(
            ["python3", resolve_path, "--list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if result.returncode != 0:
        return set()
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, list):
        return set()
    return {
        row.get("id", "")
        for row in data
        if isinstance(row, dict) and row.get("id") and admitted(row)
    }


def admitted(row: dict) -> bool:
    """Пакет из опубликованного корня без подтверждённого допуска не подсказываем.

    Подсказка ведёт к применению, поэтому недопущенный пакет здесь молчит:
    предложить его — то же, что выдать. Строки без полей допуска приходят от
    прежней версии резолвера и остаются допущенными.
    """
    return not row.get("published") or bool(row.get("admissible"))


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


def build_levels() -> list[tuple[str, str]]:
    """Та же конвенция уровней, что `resolve.py.build_levels()`.

    Копия намеренна: хук читает опубликованный вывод резолвера, поэтому не
    зависит от его внутренностей и не импортирует их.
    """
    home = os.path.expanduser("~")
    claude_dir = os.path.join(home, ".claude")
    source_roots = [
        ("project", os.path.join(os.getcwd(), ".claude", "frameworks")),
        ("user", os.path.join(claude_dir, "frameworks")),
    ]
    source_roots.extend(
        ("plugin", root) for root in read_source_paths(os.path.join(claude_dir, "frameworks.paths"))
    )
    source_roots.extend(
        ("plugin", root) for root in read_source_paths(os.path.join(claude_dir, "frameworks.published"))
    )

    levels = []
    seen_roots = set()
    for level, root in source_roots:
        canonical_root = os.path.realpath(root)
        if canonical_root in seen_roots:
            continue
        seen_roots.add(canonical_root)
        levels.append((level, root))
    return levels


def parse_competency_map(path: str) -> list[dict]:
    """Парсит pipe-delimited таблицу `competency-map.md` -> [{"id","cues":[...]}]."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError:
        return []

    header: list[str] | None = None
    raw_rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header is not None:
                break  # таблица закончилась (напр. началась LPF non-use трансляция)
            continue
        cells = [cell.strip().strip("`").strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells if cell):
            continue  # строка-разделитель заголовка
        if len(cells) != len(header):
            continue
        raw_rows.append(cells)

    if header is None:
        return []

    result: list[dict] = []
    for cells in raw_rows:
        row = dict(zip(header, cells))
        pkg_id = row.get("id", "").strip()
        if not pkg_id:
            continue
        cues = [
            cue.strip().strip("`").strip()
            for cue in row.get("cues", "").split(";")
            if cue.strip()
        ]
        result.append({"id": pkg_id, "cues": cues})
    return result


def collect_competency_rows() -> list[dict]:
    rows: list[dict] = []
    for _level, root in build_levels():
        map_path = os.path.join(root, "competency-map.md")
        rows.extend(parse_competency_map(map_path))
    return rows


def extract_id_candidates(prompt: str) -> list[str]:
    """Все матчи id-регулярки в промпте, дедуп с сохранением порядка первого появления."""
    seen: set[str] = set()
    result: list[str] = []
    for match in ID_PATTERN.finditer(prompt):
        candidate = match.group(0)
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result


def find_cue_matches(prompt: str, competency_rows: list[dict]) -> list[str]:
    """Cue word-boundary case-insensitive матч; дедуп по id (первое вхождение)."""
    seen: set[str] = set()
    result: list[str] = []
    for row in competency_rows:
        pkg_id = row["id"]
        if pkg_id in seen:
            continue
        for cue in row["cues"]:
            pattern = re.compile(r"\b" + re.escape(cue) + r"\b", re.IGNORECASE | re.UNICODE)
            if pattern.search(prompt):
                seen.add(pkg_id)
                result.append(pkg_id)
                break
    return result


def build_hint_lines(matched_ids: list[str], max_n: int = MAX_HINTS) -> list[str]:
    """Формат строки — буквально по Q6. Кап max_n, дальше — указатель на --list."""
    total = len(matched_ids)
    shown = matched_ids[:max_n]
    lines: list[str] = []
    for pkg_id in shown:
        lines.append(f"свод `{pkg_id}` выглядит релевантным → /fpf-integration:dpf-apply {pkg_id}")
        lines.append("(применение требует declaredUse; гейт свежести не обходится)")
    if total > max_n:
        remaining = total - max_n
        lines.append(f"…+{remaining}, см. /fpf-integration:dpf-apply --list")
    return lines


def parse_prompt_payload(raw: str) -> str:
    """Достаёт поле промпта из JSON payload UserPromptSubmit. Битый JSON -> ''."""
    if not raw.strip():
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    prompt = payload.get("prompt", "")
    return prompt if isinstance(prompt, str) else ""


def parse_session_id(raw: str) -> str:
    """Достаёт `session_id` из payload UserPromptSubmit. Нет поля/битый JSON -> ''."""
    if not raw.strip():
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    session_id = payload.get("session_id", "")
    return session_id if isinstance(session_id, str) else ""


def _seen_store_path(session_id: str) -> str | None:
    """Путь файла-стора «уже подсказано в этой сессии».

    session_id санитизируется до безопасного токена (защита от path traversal в
    имени файла). Пустой/несанируемый session_id -> None (сессионный дедуп не
    применяется)."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:128]
    if not safe:
        return None
    return os.path.join(tempfile.gettempdir(), "dpf-competency-hints", safe)


def load_seen(session_id: str) -> set[str]:
    """id, уже подсказанные в этой сессии. Любая проблема -> set() (fail-open: подскажем)."""
    path = _seen_store_path(session_id)
    if not path:
        return set()
    try:
        with open(path, encoding="utf-8") as handle:
            return {line.strip() for line in handle if line.strip()}
    except OSError:
        return set()


def record_seen(session_id: str, shown_ids: list[str]) -> None:
    """Дописать показанные id в стор сессии. Любая проблема -> молча пропустить (fail-open)."""
    if not shown_ids:
        return
    path = _seen_store_path(session_id)
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            for pkg_id in shown_ids:
                handle.write(pkg_id + "\n")
    except OSError:
        return


def main() -> int:
    try:
        raw_stdin = sys.stdin.read()
    except Exception:
        return 0
    prompt = parse_prompt_payload(raw_stdin)
    if not prompt:
        return 0

    known_ids = fetch_known_ids(resolve_script_path())
    id_candidates = extract_id_candidates(prompt)
    channel1_ids = [pkg_id for pkg_id in id_candidates if pkg_id in known_ids]

    competency_rows = collect_competency_rows()
    channel2_ids = find_cue_matches(prompt, competency_rows)

    merged: list[str] = []
    seen: set[str] = set()
    for pkg_id in channel1_ids + channel2_ids:
        if pkg_id not in seen:
            seen.add(pkg_id)
            merged.append(pkg_id)

    # Сессионный дедуп: убрать своды, уже подсказанные в этой сессии. Без
    # session_id (или при проблеме со стором) — fail-open: подсказываем как есть.
    session_id = parse_session_id(raw_stdin)
    if session_id:
        already_seen = load_seen(session_id)
        merged = [pkg_id for pkg_id in merged if pkg_id not in already_seen]

    lines = build_hint_lines(merged)
    if lines:
        print("\n".join(lines))
    # Записать в стор ровно показанные (merged[:MAX_HINTS]) — не-показанный «хвост»
    # сможет всплыть в следующем промпте.
    if session_id:
        record_seen(session_id, merged[:MAX_HINTS])
    return 0


if __name__ == "__main__":
    sys.exit(main())
