#!/usr/bin/env python3
"""Профиль зрелости компетенции (DPF/LPF) — детерминированный слой поверх критика.

Читает (только на чтение, ничего не меняет в исходниках свода):
  - `DPF.md` — заголовки канон-скелета (§4/§5/§10/§11) + frontmatter.
  - последний `references/package-adequacy-<date>.md` — таблица координат
    D1-D11 + статус-токен + строка `> maturity-critic:`.
  - листинг `references/` — файловый признак support-maps.

Вычисляет уровень L0-L4 (min-based D-ось + компонентная полнота, БЕЗ
усреднения — CC-DPFDA.4), kind-развилку DPF/LPF, чек-лист компонентов,
список «доработать next», рендер раздела `## Профиль зрелости`.

Не судит содержание — presence и арифметика (script), не substance
(critic). Финальный уровень L3/L4 требует строки `> maturity-critic:`
(её отсутствие капит structural L3+ до L2 — fail-closed).

CLI:
  maturity.py <package-dir> [--json] [--write-profile]

Exit-коды:
  0 — профиль построен (adequacy найден и распарсен, либо не найден и это
      отражено пометкой — human/json вывод в обоих случаях).
  2 — package-adequacy отсутствует: уровень посчитан только по компонентам
      DPF.md (не выше L0), в выводе явная пометка.
  1 — каталог свода или DPF.md не найден.

stdlib-only, без сети, без LLM. Парсинг frontmatter/conformance-строки
повторяет формат `resolve.py` (однострочные ключи) — независимая реализация,
`resolve.py` не импортируется и не меняется.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from collections.abc import Mapping

# --------------------------------------------------------------------------
# Низкоуровневое чтение файлов
# --------------------------------------------------------------------------


def read_text(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeError) as exc:
        print(f"unreadable: {path}: {exc}", file=sys.stderr)
        return None


# --------------------------------------------------------------------------
# Frontmatter (тот же однострочный формат, что у resolve.py; независимая
# реализация — DPF.md читаем только на чтение, resolve.py не трогаем)
# --------------------------------------------------------------------------


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.split("\n")
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


# --------------------------------------------------------------------------
# Извлечение секций канон-скелета (## N. Заголовок ... до следующего ## )
# --------------------------------------------------------------------------


def extract_section(text: str, heading_num: int) -> str | None:
    lines = text.split("\n")
    start_pat = re.compile(rf"^##\s*{heading_num}\.")
    start = None
    for i, line in enumerate(lines):
        if start_pat.match(line.strip()):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^##\s", lines[j].strip()):
            end = j
            break
    return "\n".join(lines[start:end])


# --------------------------------------------------------------------------
# canon-patterns (§4) + conformance-строка (admissible) в DPF.md
# --------------------------------------------------------------------------


def count_canon_patterns(dpf_text: str) -> tuple[int, bool]:
    """Возвращает (число тел паттернов в §4, найдена ли секция §4)."""
    section4 = extract_section(dpf_text, 4)
    if section4 is None:
        return 0, False
    matches = re.findall(r"^###\s*Паттерн\s+\d+", section4, re.MULTILINE)
    return len(matches), True


def dpf_md_admissible(dpf_text: str) -> bool:
    """Последняя строка `> conformance:` с маркером E.4.DPF.DA несёт
    admissibleForDeclaredDPFUse (тот же принцип "последняя строка выигрывает",
    что у resolve.py — независимая реализация)."""
    last_token = None
    for raw_line in dpf_text.split("\n"):
        line = raw_line.strip()
        if line.startswith("> conformance:") and "E.4.DPF.DA:" in line:
            after = line.split("E.4.DPF.DA:", 1)[1].split()
            last_token = after[0] if after else None
    return last_token == "admissibleForDeclaredDPFUse"


# --------------------------------------------------------------------------
# PFR-network — §5 (таблица связей) ИЛИ per-pattern "Связи:" внутри §4
# --------------------------------------------------------------------------

_BUCKET_PATTERNS = [
    ("requires_specialization", re.compile(r"require|specializ", re.I)),
    ("composes_source_reuse", re.compile(r"composition|compose|source-reuse|reuse", re.I)),
    ("conflicts", re.compile(r"conflict", re.I)),
    ("evaluation", re.compile(r"evaluat", re.I)),
    ("teaching", re.compile(r"teach", re.I)),
    ("ethics", re.compile(r"ethic", re.I)),
    ("generated_carrier", re.compile(r"generated|carrier", re.I)),
]


def _bucket_of(token: str) -> str | None:
    for name, pat in _BUCKET_PATTERNS:
        if pat.search(token):
            return name
    return None


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.match(r"^:?-{2,}:?$", c) for c in cells)


def extract_relation_edges(dpf_text: str) -> tuple[int, set[str], bool]:
    """Считает связи из §5-таблицы И per-pattern "Связи:"-буллетов в §4
    (оба источника принимаются — эталон ailev держит связи per-pattern, наш
    канон-скелет — отдельной секцией §5; оба легитимны, Q2/§3).

    Возвращает (число рёбер, множество распознанных типов-бакетов,
    найдена ли хотя бы одна из секций §4/§5)."""
    edges = 0
    buckets: set[str] = set()
    section_found = False

    section5 = extract_section(dpf_text, 5)
    if section5 is not None:
        section_found = True
        for raw_line in section5.split("\n"):
            line = raw_line.strip()
            if not line.startswith("|"):
                continue
            cells = _split_row(line)
            if len(cells) < 2 or _is_table_separator(cells):
                continue
            if "тип" in cells[1].lower() or "type" in cells[1].lower():
                continue  # header row
            tokens = re.findall(r"`([A-Za-z][\w-]*)`", cells[1])
            if not tokens:
                continue
            edges += 1
            for tok in tokens:
                bucket = _bucket_of(tok)
                if bucket:
                    buckets.add(bucket)

    section4 = extract_section(dpf_text, 4)
    if section4 is not None:
        section_found = True
        for m in re.finditer(r"-\s*\*\*Связи:\*\*\s*(.+)", section4):
            tokens = re.findall(r"`([A-Za-z][\w-]*)`", m.group(1))
            if not tokens:
                continue
            edges += 1
            for tok in tokens:
                bucket = _bucket_of(tok)
                if bucket:
                    buckets.add(bucket)

    return edges, buckets, section_found


# --------------------------------------------------------------------------
# refresh-route — §11 "Refresh triggers:" + frontmatter review_due
# --------------------------------------------------------------------------


def count_refresh_triggers(dpf_text: str) -> tuple[int, bool]:
    section11 = extract_section(dpf_text, 11)
    if section11 is None:
        return 0, False
    m = re.search(r"\*\*Refresh triggers:\*\*\s*(.+)", section11, re.DOTALL)
    if not m:
        return 0, True
    rest = m.group(1)
    stop = re.search(r"\n-\s*\*\*", rest)
    trigger_text = rest[: stop.start()] if stop else rest
    parts = [p.strip() for p in trigger_text.split(";") if p.strip()]
    return len(parts), True


def review_due_present(frontmatter: dict[str, str]) -> bool:
    value = frontmatter.get("review_due", "").strip()
    if not value:
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


# --------------------------------------------------------------------------
# acceptance-cases — §10 "Случай X" / "HC-N", не pending/гипотетичен
# --------------------------------------------------------------------------

_PENDING_RE = re.compile(r"worked-evidence pending|гипотетичен|не evidence|not evidence", re.I)


def extract_acceptance_cases(dpf_text: str) -> tuple[int, int, bool]:
    """Возвращает (всего кейсов, не-pending кейсов, найдена ли секция §10)."""
    section10 = extract_section(dpf_text, 10)
    if section10 is None:
        return 0, 0, False
    starts = sorted(
        {m.start() for m in re.finditer(r"\*\*Случай\s+\S+", section10)}
        | {m.start() for m in re.finditer(r"\bHC-\d+\b", section10)}
    )
    if not starts:
        return 0, 0, True
    total = len(starts)
    nonpending = 0
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(section10)
        block = section10[s:e]
        if not _PENDING_RE.search(block):
            nonpending += 1
    return total, nonpending, True


# --------------------------------------------------------------------------
# support-maps — файловый признак references/*map*.md | *bridge*.md
# --------------------------------------------------------------------------


def count_support_maps(references_dir: str) -> int:
    if not os.path.isdir(references_dir):
        return 0
    count = 0
    for name in os.listdir(references_dir):
        low = name.lower()
        if low.startswith("package-adequacy"):
            continue
        if low.endswith(".md") and ("map" in low or "bridge" in low):
            count += 1
    return count


# --------------------------------------------------------------------------
# executable-sync (LPF only) — assets/apply-prompt.md присутствует
# --------------------------------------------------------------------------


def executable_sync_present(package_dir: str) -> bool:
    return os.path.isfile(os.path.join(package_dir, "assets", "apply-prompt.md"))


# --------------------------------------------------------------------------
# package-adequacy: последний dated-файл
# --------------------------------------------------------------------------

_ADEQUACY_RE = re.compile(r"^package-adequacy-(\d{4}-\d{2}-\d{2})\.md$")


def find_latest_adequacy(references_dir: str) -> str | None:
    if not os.path.isdir(references_dir):
        return None
    candidates = []
    for name in os.listdir(references_dir):
        m = _ADEQUACY_RE.match(name)
        if m:
            candidates.append((m.group(1), name))
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1][1]


# --------------------------------------------------------------------------
# статус-токен package-adequacy — последнее вхождение по файлу
# --------------------------------------------------------------------------

_STATUS_TOKEN_ALT = r"admissibleForDeclaredDPFUse|repairBeforeDPFUse|seedOnly|refreshNeeded|holdFor\w*"
# Приоритетный сигнал — строка-ДЕКЛАРАЦИЯ статуса: bold-спан, заканчивающийся
# backtick-обёрнутым токеном ("**TOKEN**" / "**Статус (...): `TOKEN`**" — обе
# реальные формы package-adequacy держат токен как ПОСЛЕДНИЙ backtick-элемент
# bold-спана, необязательно вплотную после "**"). Отличает вердикт от
# прозаических упоминаний истории («круг 1 (`repairBeforeDPFUse`, §1-§8)
# сохранён дословно выше») — те НЕ лежат внутри bold-спана, только в
# одиночных backtick без обрамляющего "**...**".
_STATUS_DECL_RE = re.compile(rf"\*\*[^`\n]*`({_STATUS_TOKEN_ALT})`\.?\*\*")
_STATUS_BARE_RE = re.compile(rf"\b({_STATUS_TOKEN_ALT})\b")


def extract_status_token(adequacy_text: str) -> str | None:
    decl_matches = _STATUS_DECL_RE.findall(adequacy_text)
    if decl_matches:
        return decl_matches[-1]
    bare_matches = _STATUS_BARE_RE.findall(adequacy_text)
    return bare_matches[-1] if bare_matches else None


# --------------------------------------------------------------------------
# критик-потолок — последняя строка `> maturity-critic: L<n> ...`
# --------------------------------------------------------------------------

_CRITIC_RE = re.compile(
    r"^>\s*maturity-critic:\s*L(\d+)\s+confirmed[^\n]*?weak-components:\s*\[([^\]]*)\]",
    re.MULTILINE,
)
_CRITIC_PREFIX_RE = re.compile(r"^>\s*maturity-critic:", re.MULTILINE)
_PROFILE_HEADING_RE = re.compile(r"^##\s*Профиль зрелости\s*$", re.MULTILINE)


def _source_region(adequacy_text: str) -> str:
    """Область файла ДО раздела '## Профиль зрелости'. Критик-строка читается
    только отсюда: рендер профиля сам эхо-повторяет критик-строку ВНУТРИ
    раздела (в машинно-похожем формате), и без этой границы `_CRITIC_RE`
    на повторном прогоне матчил бы своё же эхо вместо исходной строки —
    затирая исходный `(guardian, <date>)` и копя `repr()`-артефакты в
    weak-components. Инвариант: подлинная критик-строка обязана предшествовать
    разделу профиля (см. `write_profile` — там же fail-fast, если это не так)."""
    m = _PROFILE_HEADING_RE.search(adequacy_text)
    return adequacy_text if m is None else adequacy_text[: m.start()]


def extract_critic_ceiling(adequacy_text: str) -> tuple[int | None, list[str], bool]:
    """Возвращает (уровень|None, weak-components, malformed).

    `malformed=True` — строка `> maturity-critic:` присутствует в
    исходной области (до раздела профиля), но не разобралась целиком
    (например нет `weak-components: [...]`) — отличается от «строки
    попросту нет», чтобы диагностика не врала (MINOR1)."""
    region = _source_region(adequacy_text)
    matches = list(_CRITIC_RE.finditer(region))
    if matches:
        last = matches[-1]
        level = int(last.group(1))
        weak_raw = last.group(2).strip()
        weak = [w.strip() for w in weak_raw.split(",") if w.strip()]
        return level, weak, False
    malformed = bool(_CRITIC_PREFIX_RE.search(region))
    return None, [], malformed


# --------------------------------------------------------------------------
# D1-D11: комбинирует ВСЕ координатные таблицы документа в порядке чтения
# (полноформатные Coord|V|.../Repair И delta-формата Координата|Круг1|Круг2|...
# — второй круг переоценки переопределяет значения первого; см. plan §7).
# --------------------------------------------------------------------------


def parse_d_scores(adequacy_text: str) -> tuple[dict[int, int], dict[int, str | None], bool]:
    values: dict[int, int] = {}
    repair: dict[int, str | None] = {}
    any_table = False
    lines = adequacy_text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < n:
            header_cells = _split_row(line)
            sep_cells = _split_row(lines[i + 1].strip())
            if _is_table_separator(sep_cells):
                j = i + 2
                data_rows = []
                while j < n and lines[j].strip().startswith("|"):
                    data_rows.append(lines[j].strip())
                    j += 1
                if _handle_d_table(header_cells, data_rows, values, repair):
                    any_table = True
                i = j
                continue
        i += 1
    return values, repair, any_table


def _handle_d_table(
    header_cells: list[str],
    data_rows: list[str],
    values: dict[int, int],
    repair: dict[int, str | None],
) -> bool:
    if not header_cells:
        return False
    id_header = header_cells[0].lower()
    if "coord" not in id_header and "координат" not in id_header:
        return False

    value_idx = None
    circle_indices = []
    for idx, h in enumerate(header_cells):
        hl = h.lower()
        if hl in ("v", "значение"):
            value_idx = idx
        if re.match(r"круг\s*\d+", hl):
            circle_indices.append(idx)
    if circle_indices:
        value_idx = circle_indices[-1]
    if value_idx is None:
        return False

    repair_idx = None
    for idx, h in enumerate(header_cells):
        if "repair" in h.lower():
            repair_idx = idx
            break

    handled_any = False
    for row in data_rows:
        cells = _split_row(row)
        if not cells or _is_table_separator(cells):
            continue
        id_cell = cells[0]
        ids = [int(x) for x in re.findall(r"D(\d{1,2})\b", id_cell)]
        if not ids:
            continue
        value_cell = cells[value_idx] if value_idx < len(cells) else ""
        digit_match = re.search(r"\d", value_cell)
        if not digit_match:
            continue
        value = int(digit_match.group(0))
        repair_cell = None
        if repair_idx is not None and repair_idx < len(cells):
            repair_cell = cells[repair_idx]
        for d_id in ids:
            values[d_id] = value
            repair[d_id] = repair_cell
        handled_any = True
    return handled_any


def d_scores_complete(values: dict[int, int]) -> bool:
    return set(values.keys()) == set(range(1, 12))


def compute_floor_fragile(values: Mapping[int, int], repair: Mapping[int, str | None]) -> set[int]:
    fragile = set()
    for d_id, v in values.items():
        if v != 4:
            continue
        rep = repair.get(d_id)
        if rep is None:
            # Нет колонки Repair у источника (delta-таблица круга переоценки) —
            # это отчёт "после ремонта", трактуем как разрешённый концерн.
            continue
        rep_stripped = rep.strip()
        if rep_stripped in ("—", "-", ""):
            continue
        if re.match(r"(?i)^no-proposal", rep_stripped):
            continue
        fragile.add(d_id)
    return fragile


# --------------------------------------------------------------------------
# Вычисление уровня (fail-closed вниз)
# --------------------------------------------------------------------------

LEVEL_NAMES = {0: "seed", 1: "admissible", 2: "grounded", 3: "exercised", 4: "exemplar"}

LEVEL_DEFINITIONS = {
    0: "seed (package-adequacy отсутствует, статус не admissible, или min(D)<4)",
    1: "admissible (статус admissible; все D≥4; canon-patterns присутствуют)",
    2: "grounded (admissible + PFR-сеть + refresh route + нет floor-fragile координаты)",
    3: (
        "exercised (grounded + ≥2 не-pending приёмочных кейса + ≥1 support-map"
        " + критик-подтверждение L≥3)"
    ),
    4: (
        "exemplar (exercised + полный набор паттернов + ~4 приёмочных кейса"
        " + полное семейство support-карт + богатая PFR-сеть ≥6 типов"
        " + выделенный refresh route + критик-подтверждение L4)"
    ),
}


def compute_level(ctx: dict) -> dict:
    """ctx — собранные сигналы (см. analyze()). Возвращает dict с
    structural_level, final_level, notes на каждый уровень."""
    notes: list[str] = []

    if not ctx["adequacy_present"]:
        return {"structural_level": 0, "final_level": 0, "notes": ["package-adequacy отсутствует"]}

    if ctx["status_token"] != "admissibleForDeclaredDPFUse":
        notes.append(
            f"статус пакета: {ctx['status_token'] or '(не распознан)'}"
            " (ожидался admissibleForDeclaredDPFUse)"
        )
        return {"structural_level": 0, "final_level": 0, "notes": notes}

    if not ctx["d_complete"]:
        notes.append("D-таблица не распарсена/неполна (не все D1-D11 найдены)")
        return {"structural_level": 0, "final_level": 0, "notes": notes}

    if ctx["min_d"] < 4:
        notes.append(f"min(D)={ctx['min_d']} < 4 (пол не удержан)")
        return {"structural_level": 0, "final_level": 0, "notes": notes}

    # L1
    l1_ok = ctx["canon_patterns_count"] >= 4 and ctx["dpf_conformance_admissible"]
    if not l1_ok:
        notes.append("L1 не достигнут: canon-patterns<4 или нет admissible conformance-строки в DPF.md")
        return {"structural_level": 0, "final_level": 0, "notes": notes}

    # L2
    no_fragile = not ctx["floor_fragile"]
    pfr_ok = ctx["pfr_edges"] >= 3 and len(ctx["pfr_types"]) >= 2
    refresh_ok = ctx["refresh_triggers"] >= 2 and ctx["review_due_present"]
    if not (no_fragile and pfr_ok and refresh_ok):
        if not no_fragile:
            notes.append(f"L2 не достигнут: floor-fragile координаты {sorted(ctx['floor_fragile'])}")
        if not pfr_ok:
            notes.append("L2 не достигнут: PFR-network < порога (нужно ≥3 связей, ≥2 типа)")
        if not refresh_ok:
            notes.append("L2 не достигнут: refresh-route < порога (нужно ≥2 триггера + review_due)")
        return {"structural_level": 1, "final_level": 1, "notes": notes}

    # L3
    acceptance_ok = ctx["acceptance_nonpending"] >= 2
    support_ok = ctx["support_maps"] >= 1
    executable_ok = True
    if ctx["is_lpf"]:
        executable_ok = ctx["executable_sync"]
    structural_l3 = acceptance_ok and support_ok and executable_ok
    if not structural_l3:
        if not acceptance_ok:
            notes.append("L3 не достигнут: acceptance-cases < 2 не-pending")
        if not support_ok:
            notes.append("L3 не достигнут: support-maps отсутствуют (файловый признак references/*map*.md|*bridge*.md)")
        if ctx["is_lpf"] and not executable_ok:
            notes.append("L3 не достигнут (LPF): executable-sync — assets/apply-prompt.md отсутствует")
        return {"structural_level": 2, "final_level": 2, "notes": notes}

    # L4 (best-effort — за пределами покрытия текущих seed-сводов)
    full_patterns = ctx["canon_patterns_count"] >= 8 if not ctx["is_lpf"] else True
    l4_structural = (
        full_patterns
        and ctx["acceptance_nonpending"] >= 4
        and ctx["support_maps"] >= 5
        and len(ctx["pfr_types"]) >= 6
        and ctx["refresh_triggers"] >= 2
    )
    structural_level = 4 if l4_structural else 3

    # critic-ceiling: обязателен для L3/L4 (fail-closed при отсутствии строки)
    critic_level = ctx["critic_level"]
    if critic_level is None:
        if ctx.get("critic_line_malformed"):
            notes.append(
                "critic-ceiling: строка `> maturity-critic:` присутствует, но не разобрана"
                " (проверьте формат `L<n> confirmed ...; weak-components: [...]`)"
                " — L3/L4 капается до L2"
            )
        else:
            notes.append("critic-ceiling отсутствует (`> maturity-critic:` не найдена) — L3/L4 капается до L2")
        return {"structural_level": structural_level, "final_level": 2, "notes": notes}

    final_level = min(structural_level, critic_level)
    if final_level < structural_level:
        notes.append(f"critic-ceiling L{critic_level} понижает structural L{structural_level} до L{final_level}")
    return {"structural_level": structural_level, "final_level": final_level, "notes": notes}


# --------------------------------------------------------------------------
# Чек-лист компонентов + «доработать next»
# --------------------------------------------------------------------------

PHASE_HINTS = {
    "canon-patterns": "authoring §4 «Паттерны» — дополнить E.8-тела паттернов (нужно ≥4)",
    "conformance": "критик-фаза — получить admissible-вердикт (E.4.DPF.DA) в DPF.md",
    "floor-fragile": "фаза Repair/Ремонт — снять открытые repair-предложения по floor-координатам",
    "pfr-network": "authoring §5 «Связи паттернов» — добавить/расширить связи (≥3 связей, ≥2 типа)",
    "refresh-route": "authoring §11 «Quality & refresh route» — добавить именованные refresh-триггеры (≥2) + review_due",
    "acceptance-cases": "authoring §10 «Разнородные приёмочные случаи» — добавить/подтвердить ≥2 не-pending кейса",
    "support-maps": "фаза Assemble/Source-pack `dpf-authoring` (режим доавторинга) — добавить substantive support/bridge-карту",
    "executable-sync": "провести паттерн в executable-носители (`assets/apply-prompt.md`) — режим доавторинга LPF",
    "critic-ceiling": "критик-фаза (режим B) — получить строку `> maturity-critic: L<n> confirmed`",
}


def build_components(ctx: dict, weak_components: list[str]) -> list[dict]:
    weak_set = {w.lower() for w in weak_components}

    def status_for(component_id: str, present: bool, section_found: bool, locus: str) -> dict:
        if not section_found:
            return {
                "id": component_id,
                "status": "missing",
                "locus": f"✗ (секция не найдена — свод вне канон-скелета?)",
            }
        if not present:
            return {"id": component_id, "status": "missing", "locus": locus}
        if component_id in weak_set:
            return {"id": component_id, "status": "weak", "locus": locus}
        return {"id": component_id, "status": "ok", "locus": locus}

    components = [
        status_for(
            "canon-patterns",
            ctx["canon_patterns_count"] >= 4,
            ctx["section4_found"],
            f"DPF.md §4 ({ctx['canon_patterns_count']} тел)",
        ),
        status_for(
            "pfr-network",
            ctx["pfr_edges"] >= 3 and len(ctx["pfr_types"]) >= 2,
            ctx["pfr_section_found"],
            f"DPF.md §5/пер-паттерн ({ctx['pfr_edges']} связей, {len(ctx['pfr_types'])} типов)",
        ),
        status_for(
            "refresh-route",
            ctx["refresh_triggers"] >= 2 and ctx["review_due_present"],
            ctx["section11_found"],
            f"DPF.md §11 ({ctx['refresh_triggers']} триггеров) + review_due",
        ),
        status_for(
            "acceptance-cases",
            ctx["acceptance_nonpending"] >= 2,
            ctx["section10_found"],
            f"DPF.md §10 ({ctx['acceptance_nonpending']}/{ctx['acceptance_total']} не-pending)",
        ),
        status_for(
            "support-maps",
            ctx["support_maps"] >= 1,
            True,
            f"references/ ({ctx['support_maps']} карт)" if ctx["support_maps"] else "нет отдельной map/bridge-карты",
        ),
    ]
    if ctx["is_lpf"]:
        components.append(
            status_for(
                "executable-sync",
                ctx["executable_sync"],
                True,
                "assets/apply-prompt.md" if ctx["executable_sync"] else "assets/apply-prompt.md отсутствует",
            )
        )
    return components


def build_next_steps(level_result: dict, components: list[dict], ctx: dict) -> list[str]:
    steps: list[str] = []
    for comp in components:
        if comp["status"] in ("missing", "weak"):
            hint = PHASE_HINTS.get(comp["id"], "authoring — уточнить фазу")
            steps.append(f"{comp['id']} — {hint}")
    if ctx["floor_fragile"]:
        steps.append(f"floor-fragile — {PHASE_HINTS['floor-fragile']}")
    if level_result["structural_level"] >= 3 and ctx["critic_level"] is None:
        steps.append(f"critic-ceiling — {PHASE_HINTS['critic-ceiling']}")
    return steps


# --------------------------------------------------------------------------
# Главный анализ
# --------------------------------------------------------------------------


def analyze(package_dir: str) -> dict:
    dpf_md_path = os.path.join(package_dir, "DPF.md")
    dpf_text = read_text(dpf_md_path)
    if dpf_text is None:
        return {"error": "unreadable", "code": 1}

    frontmatter = parse_frontmatter(dpf_text)
    kind = frontmatter.get("kind", "").strip()
    is_lpf = kind == "Local Practice Framework"
    dpf_id = frontmatter.get("dpf_id", "").strip() or os.path.basename(package_dir.rstrip(os.sep))

    canon_patterns_count, section4_found = count_canon_patterns(dpf_text)
    dpf_conformance_admissible = dpf_md_admissible(dpf_text)
    pfr_edges, pfr_types, pfr_section_found = extract_relation_edges(dpf_text)
    refresh_triggers, section11_found = count_refresh_triggers(dpf_text)
    acceptance_total, acceptance_nonpending, section10_found = extract_acceptance_cases(dpf_text)

    references_dir = os.path.join(package_dir, "references")
    support_maps = count_support_maps(references_dir)
    executable_sync = executable_sync_present(package_dir) if is_lpf else None

    adequacy_name = find_latest_adequacy(references_dir)
    adequacy_present = adequacy_name is not None
    status_token = None
    values: dict[int, int] = {}
    repair: dict[int, str | None] = {}
    d_complete = False
    min_d = None
    floor_fragile: set[int] = set()
    critic_level = None
    weak_components: list[str] = []
    critic_line_malformed = False

    if adequacy_name is not None:
        adequacy_text = read_text(os.path.join(references_dir, adequacy_name))
        if adequacy_text is not None:
            status_token = extract_status_token(adequacy_text)
            values, repair, _ = parse_d_scores(adequacy_text)
            d_complete = d_scores_complete(values)
            if d_complete:
                min_d = min(values.values())
                floor_fragile = compute_floor_fragile(values, repair)
            critic_level, weak_components, critic_line_malformed = extract_critic_ceiling(adequacy_text)
        else:
            adequacy_present = False  # нечитаем — трактуем как отсутствующий

    ctx = {
        "dpf_id": dpf_id,
        "kind": kind,
        "is_lpf": is_lpf,
        "canon_patterns_count": canon_patterns_count,
        "section4_found": section4_found,
        "dpf_conformance_admissible": dpf_conformance_admissible,
        "pfr_edges": pfr_edges,
        "pfr_types": pfr_types,
        "pfr_section_found": pfr_section_found,
        "refresh_triggers": refresh_triggers,
        "section11_found": section11_found,
        "review_due_present": review_due_present(frontmatter),
        "acceptance_total": acceptance_total,
        "acceptance_nonpending": acceptance_nonpending,
        "section10_found": section10_found,
        "support_maps": support_maps,
        "executable_sync": executable_sync,
        "adequacy_present": adequacy_present,
        "adequacy_name": adequacy_name,
        "status_token": status_token,
        "d_values": values,
        "d_repair": repair,
        "d_complete": d_complete,
        "min_d": min_d,
        "floor_fragile": floor_fragile,
        "critic_level": critic_level,
        "weak_components": weak_components,
        "critic_line_malformed": critic_line_malformed,
    }

    level_result = compute_level(ctx)
    components = build_components(ctx, weak_components)
    next_steps = build_next_steps(level_result, components, ctx)

    return {
        "error": None,
        "code": 0 if adequacy_present else 2,
        "ctx": ctx,
        "level_result": level_result,
        "components": components,
        "next_steps": next_steps,
    }


# --------------------------------------------------------------------------
# Рендер
# --------------------------------------------------------------------------


def _status_symbol(status: str) -> str:
    return {"ok": "✓", "missing": "✗", "weak": "✓ presence / критик: слабый"}[status]


def render_profile_section(result: dict) -> str:
    ctx = result["ctx"]
    lr = result["level_result"]
    n = lr["final_level"]
    lines = ["## Профиль зрелости", ""]
    lines.append(f"- **Уровень: L{n} — {LEVEL_NAMES[n]}** ({LEVEL_DEFINITIONS[n]}).")
    if ctx["d_complete"]:
        fragile = sorted(ctx["floor_fragile"]) or []
        lines.append(
            f"- **D-ось (референс, не копия):** таблица D1-D11 — см. package-adequacy выше."
            f" Сводка: min={ctx['min_d']}; floor-fragile={fragile}."
        )
    else:
        lines.append("- **D-ось:** ✗ D-scores (D-таблица не распарсена/неполна — package-adequacy вне канон-формата?)")
    lines.append("- **Компоненты:**")
    lines.append("  | Компонент | Статус | Сигнал-локус |")
    lines.append("  |---|---|---|")
    for comp in result["components"]:
        lines.append(f"  | {comp['id']} | {_status_symbol(comp['status'])} | {comp['locus']} |")
    if result["next_steps"]:
        lines.append(f"- **Доработать next (до L{min(n + 1, 4)}):**")
        for i, step in enumerate(result["next_steps"], 1):
            lines.append(f"  {i}. {step}")
    else:
        lines.append("- **Доработать next:** нет открытых пунктов на этом уровне.")
    lines.append(
        '- **Различение:** «✗» = компонента нет; «✓ presence / критик: слабый»'
        ' = скрипт видит компонент, критик пометил его слабым (weak-components).'
    )
    if lr["notes"]:
        lines.append("- **Диагностика уровня:**")
        for note in lr["notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    if ctx["critic_level"] is not None:
        weak_str = "[" + ", ".join(ctx["weak_components"]) + "]"
        # Немашинночитаемый маркер (НЕ "> maturity-critic:") — это ЭХО, не
        # источник; `_CRITIC_RE`/`_source_region` его игнорируют (см. фикс
        # округления критик-потолка выше), поэтому повторный прогон читает
        # исходную строку package-adequacy, а не собственное отражение.
        lines.append(
            f"(эхо источника: maturity-critic L{ctx['critic_level']} confirmed;"
            f" weak-components: {weak_str})"
        )
    elif ctx.get("critic_line_malformed"):
        lines.append("(эхо источника: строка `> maturity-critic:` присутствует, но не разобрана)")
    else:
        lines.append("(эхо источника: строка `> maturity-critic:` отсутствует в package-adequacy)")
    return "\n".join(lines) + "\n"


def render_human(result: dict) -> str:
    ctx = result["ctx"]
    lr = result["level_result"]
    n = lr["final_level"]
    out = []
    out.append(f"{ctx['dpf_id']} ({ctx['kind'] or '?'})")
    out.append(f"  уровень: L{n} — {LEVEL_NAMES[n]}")
    if not result["ctx"]["adequacy_present"]:
        out.append("  package-adequacy: отсутствует — уровень посчитан только по компонентам (не выше L0)")
    else:
        out.append(f"  package-adequacy: {ctx['adequacy_name']} (статус: {ctx['status_token'] or '?'})")
    out.append("  компоненты:")
    for comp in result["components"]:
        out.append(f"    {_status_symbol(comp['status']):<28} {comp['id']:<18} {comp['locus']}")
    if lr["notes"]:
        out.append("  диагностика:")
        for note in lr["notes"]:
            out.append(f"    - {note}")
    if result["next_steps"]:
        out.append("  доработать next:")
        for i, step in enumerate(result["next_steps"], 1):
            out.append(f"    {i}. {step}")
    map_id = ctx["dpf_id"]
    out.append(f"  предлагаемая правка карты: {map_id} maturity_level: ? → L{n}")
    return "\n".join(out)


# Инвариант, на который опирается и `write_profile`, и `_source_region`:
# подлинная критик-строка ("> maturity-critic: L<n> confirmed (guardian,
# <date>); weak-components: [...]") обязана лежать ДО '## Профиль зрелости'.
# Наше собственное эхо этот маркер-префикс больше не использует (см.
# `render_profile_section`) — если он всё же встретился внутри диапазона,
# который эта функция собирается заменить/удалить, это подлинная строка,
# случайно оказавшаяся ПОСЛЕ заголовка профиля (напр. поздний re-run критика
# дописал её в конец файла). Молча терять её нельзя (rule: не убирать
# информацию) — fail-fast с диагностикой, а не тихий пропуск.
_GENUINE_CRITIC_LINE_RE = re.compile(r"^>\s*maturity-critic:\s*L\d+\s+confirmed\s*\(guardian", re.MULTILINE)


def write_profile(adequacy_path: str, section_text: str) -> None:
    text = read_text(adequacy_path)
    if text is None:
        raise SystemExit(1)
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Профиль зрелости":
            start = i
            break
    new_section = section_text.rstrip("\n")
    if start is None:
        if text and not text.endswith("\n"):
            text += "\n"
        new_text = text.rstrip("\n") + "\n\n" + new_section + "\n"
    else:
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if re.match(r"^##\s", lines[j].strip()):
                end = j
                break
        old_section = "\n".join(lines[start:end])
        if _GENUINE_CRITIC_LINE_RE.search(old_section):
            raise SystemExit(
                "отказ: похоже на исходную критик-строку "
                "('> maturity-critic: L<n> confirmed (guardian, ...)') внутри диапазона "
                "'## Профиль зрелости' -> следующий заголовок, который --write-profile "
                "заменяет целиком. Инвариант: критик-строка обязана предшествовать разделу "
                "профиля — переместите её ПЕРЕД '## Профиль зрелости' в package-adequacy, "
                "иначе она будет молча потеряна при перезаписи."
            )
        new_lines = lines[:start] + new_section.split("\n") + lines[end:]
        new_text = "\n".join(new_lines)
        if not new_text.endswith("\n"):
            new_text += "\n"
    with open(adequacy_path, "w", encoding="utf-8") as handle:
        handle.write(new_text)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Профиль зрелости компетенции (DPF/LPF).")
    parser.add_argument("package_dir", help="каталог свода (содержит DPF.md)")
    parser.add_argument("--json", action="store_true", help="вывод в JSON")
    parser.add_argument(
        "--write-profile",
        action="store_true",
        help="перезаписать раздел '## Профиль зрелости' в последнем package-adequacy",
    )
    args = parser.parse_args(argv)

    package_dir = args.package_dir
    if not os.path.isdir(package_dir):
        print(f"каталог не найден: {package_dir}", file=sys.stderr)
        return 1
    dpf_md_path = os.path.join(package_dir, "DPF.md")
    if not os.path.isfile(dpf_md_path):
        print(f"DPF.md не найден: {dpf_md_path}", file=sys.stderr)
        return 1

    result = analyze(package_dir)
    if result["error"] == "unreadable":
        return 1

    if args.write_profile:
        if not result["ctx"]["adequacy_present"]:
            print(
                "нельзя записать профиль — package-adequacy отсутствует"
                " (новый носитель не заводится, A.11)",
                file=sys.stderr,
            )
        else:
            adequacy_path = os.path.join(package_dir, "references", result["ctx"]["adequacy_name"])
            section_text = render_profile_section(result)
            write_profile(adequacy_path, section_text)
            print(f"профиль записан: {adequacy_path}")

    if args.json:
        out = {
            "id": result["ctx"]["dpf_id"],
            "kind": result["ctx"]["kind"],
            "level": f"L{result['level_result']['final_level']}",
            "level_number": result["level_result"]["final_level"],
            "structural_level": result["level_result"]["structural_level"],
            "definition": LEVEL_DEFINITIONS[result["level_result"]["final_level"]],
            "d_axis": {
                "min": result["ctx"]["min_d"],
                "complete": result["ctx"]["d_complete"],
                "floor_fragile": sorted(result["ctx"]["floor_fragile"]),
                "values": {f"D{k}": v for k, v in sorted(result["ctx"]["d_values"].items())},
            },
            "components": result["components"],
            "next_steps": result["next_steps"],
            "notes": result["level_result"]["notes"],
            "critic_ceiling": {
                "level": result["ctx"]["critic_level"],
                "weak_components": result["ctx"]["weak_components"],
            },
            "status_token": result["ctx"]["status_token"],
            "adequacy_file": result["ctx"]["adequacy_name"],
            "adequacy_present": result["ctx"]["adequacy_present"],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))

    return result["code"]


if __name__ == "__main__":
    sys.exit(main())
