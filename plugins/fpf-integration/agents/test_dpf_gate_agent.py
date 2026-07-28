#!/usr/bin/env python3
"""Контракт агента-гейта `dpf-gate` (`fpf-integration:dpf-gate`).

Тест фиксирует, что обязано быть верно про `dpf-gate.md`, ДО того как сам
файл агента написан (FPF Evidence Graph, A.10: контракт первым, реализация —
за ним; см. `code-change-discipline`).

Запуск:
  python3 -m pytest plugins/fpf-integration/agents/test_dpf_gate_agent.py -v
  python3 plugins/fpf-integration/agents/test_dpf_gate_agent.py

stdlib only (unittest) — pytest в окружении может отсутствовать. Frontmatter
и markdown-таблица разбираются построчно `key: value` / `| cell | cell |`,
тем же приёмом, что уже используют `resolve.py` и `maturity.py` в этом
плагине — отдельный YAML-парсер не заводим (A.11, Ontological Parsimony).
"""

from __future__ import annotations

import os
import re
import unittest

AGENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dpf-gate.md")

# Несущая гарантия второго запрета (решение человека, не пересматривается):
# ровно эти инструменты чтения/диагностики, никакой записи.
ALLOWED_TOOLS = {"Read", "Grep", "Glob", "Bash"}

PLACEHOLDER_CELLS = {"...", "…", "todo", "tbd", ""}


def read_agent_text() -> str:
    with open(AGENT_PATH, encoding="utf-8") as handle:
        return handle.read()


def extract_frontmatter(text: str) -> str:
    """Текст между первой и второй строкой `---` (YAML-frontmatter-блок).

    Построчно, без YAML-парсера — тот же приём, что `parse_frontmatter`
    в `resolve.py`/`maturity.py`.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return ""
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return ""


def extract_tools(frontmatter: str) -> list[str]:
    """Значение поля `tools: [...]` — bracket-список в одну строку.

    Ищем строку `tools:` без отступа (не строку внутри многострочного
    `description: |`) и разбираем её содержимое тем же приёмом, что
    `parse_list_value` в `resolve.py`.
    """
    m = re.search(r"^tools:\s*\[(.*?)\]\s*$", frontmatter, re.MULTILINE)
    if not m:
        return []
    items = []
    for part in m.group(1).split(","):
        item = part.strip()
        if item.startswith('"') and item.endswith('"') and len(item) >= 2:
            item = item[1:-1]
        elif item.startswith("'") and item.endswith("'") and len(item) >= 2:
            item = item[1:-1]
        if item:
            items.append(item)
    return items


def extract_section(text: str, heading: str) -> str:
    """Тело раздела `## <heading>` до следующего `## ` или конца файла."""
    lines = text.split("\n")
    pat = re.compile(rf"^##\s*{re.escape(heading)}\s*$")
    start = None
    for i, line in enumerate(lines):
        if pat.match(line.strip()):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^##\s", lines[j].strip()):
            end = j
            break
    return "\n".join(lines[start:end])


def split_table_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.match(r"^:?-{2,}:?$", c) for c in cells)


def extract_prohibition_rows(section_text: str) -> list[list[str]]:
    """Строки markdown-таблицы запретов: `[запрет, цена, гард]`.

    Пропускает строку заголовка (`Запрет | Цена нарушения | Гард`) и
    строку-разделитель (`|---|---|---|`) — данными считаются строки ПОСЛЕ
    разделителя.
    """
    rows: list[list[str]] = []
    header_seen = False
    for raw_line in section_text.split("\n"):
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = split_table_row(line)
        if is_separator_row(cells):
            header_seen = True
            continue
        if not header_seen:
            continue  # строка заголовка таблицы
        if len(cells) < 3:
            continue
        rows.append(cells)
    return rows


def strip_markdown_emphasis(text: str) -> str:
    stripped = text.strip()
    while stripped.startswith("**"):
        stripped = stripped[2:]
    return stripped.strip()


class ToolsAreReadOnlySubsetTests(unittest.TestCase):
    """Гард первого измерения второго запрета: у агента физически нет
    инструментов записи."""

    def test_agent_file_exists(self):
        self.assertTrue(
            os.path.isfile(AGENT_PATH),
            f"агент не найден: {AGENT_PATH} (контракт написан ДО агента — это ожидаемо, пока агента нет)",
        )

    def test_tools_field_present(self):
        frontmatter = extract_frontmatter(read_agent_text())
        tools = extract_tools(frontmatter)
        self.assertTrue(tools, "поле `tools:` не найдено или пусто во frontmatter")

    def test_tools_are_subset_of_read_only_set(self):
        frontmatter = extract_frontmatter(read_agent_text())
        tools = extract_tools(frontmatter)
        extra = set(tools) - ALLOWED_TOOLS
        self.assertFalse(
            extra,
            f"tools содержит инструменты вне {sorted(ALLOWED_TOOLS)}: {sorted(extra)}"
            " (Write/Edit/NotebookEdit/MCP запрещены агенту-гейту)",
        )


class ProhibitionsTableTests(unittest.TestCase):
    """Раздел `## Запреты` присутствует и цел: минимум 2 строки, у каждой
    непустые ячейки «цена» и «гард»."""

    def test_prohibitions_section_present(self):
        section = extract_section(read_agent_text(), "Запреты")
        self.assertTrue(section, "раздел `## Запреты` не найден в теле агента")

    def test_at_least_two_prohibition_rows(self):
        section = extract_section(read_agent_text(), "Запреты")
        rows = extract_prohibition_rows(section)
        self.assertGreaterEqual(len(rows), 2, "в таблице запретов должно быть минимум 2 строки")

    def test_price_and_guard_cells_are_non_empty_and_not_placeholder(self):
        section = extract_section(read_agent_text(), "Запреты")
        rows = extract_prohibition_rows(section)
        for i, row in enumerate(rows):
            price, guard = row[1], row[2]
            self.assertNotIn(
                price.strip().lower(),
                PLACEHOLDER_CELLS,
                f"строка {i}: ячейка «цена» пуста/пустышка: {price!r}",
            )
            self.assertNotIn(
                guard.strip().lower(),
                PLACEHOLDER_CELLS,
                f"строка {i}: ячейка «гард» пуста/пустышка: {guard!r}",
            )


class NegativeFormTests(unittest.TestCase):
    """Каждый запрет записан негативно — «Никогда не …», без смягчителей."""

    def test_every_prohibition_starts_with_nikogda_ne(self):
        section = extract_section(read_agent_text(), "Запреты")
        rows = extract_prohibition_rows(section)
        for i, row in enumerate(rows):
            prohibition_text = strip_markdown_emphasis(row[0])
            self.assertTrue(
                prohibition_text.startswith("Никогда не"),
                f"строка {i}: запрет не начинается с «Никогда не»: {row[0]!r}",
            )


class NamedProhibitionsTests(unittest.TestCase):
    """Оба ратифицированных запрета присутствуют поимённо. Тест ищет по
    двум заранее известным темам (из архитектурного плана), не гадает
    формулировку и не реконструирует её из текста."""

    def test_pipeline_authoring_prohibition_present(self):
        section = extract_section(read_agent_text(), "Запреты")
        rows = extract_prohibition_rows(section)
        found = any(
            re.search(r"конвейер|автор", " ".join(row), re.IGNORECASE)
            and re.search(r"подтвержд", " ".join(row), re.IGNORECASE)
            for row in rows
        )
        self.assertTrue(
            found,
            "не найден запрет про запуск конвейера авторинга без подтверждения "
            "человеком (состава компетенций)",
        )

    def test_dpf_editing_prohibition_present(self):
        section = extract_section(read_agent_text(), "Запреты")
        rows = extract_prohibition_rows(section)
        found = any("DPF.md" in " ".join(row) or "править свод" in " ".join(row) for row in rows)
        self.assertTrue(found, "не найден запрет про правку свода (DPF.md / «править свод»)")

    def test_bash_write_bypass_guard_names_write_profile(self):
        """Пятая проверка — закрывает найденный пробел, которого нет в плане.

        Ограничение `tools` (нет Write/Edit) — необходимое, но НЕ достаточное
        условие второго запрета: `Bash` умеет писать в обход прямых
        инструментов записи (shell-редирект `>`, `sed -i`, и главное —
        `maturity.py --write-profile`, который реально открывает файл на
        запись, см. `assets/maturity.py:930`). Без явного упоминания обоих
        слов в ячейке «гард» эта гарантия может со временем усохнуть до
        «нет Write/Edit» и дыра откроется заново, а тест этого не заметит.

        Проверка ищет именованные слова, а не перефразировки — однозначный
        разбор, не угадывание синонимов.
        """
        section = extract_section(read_agent_text(), "Запреты")
        rows = extract_prohibition_rows(section)
        dpf_editing_rows = [row for row in rows if "DPF.md" in " ".join(row) or "править свод" in " ".join(row)]
        self.assertTrue(
            dpf_editing_rows,
            "не найден запрет про правку свода — проверка 5 не может найти его ячейку «гард»",
        )
        for row in dpf_editing_rows:
            guard = row[2]
            self.assertIn(
                "Bash",
                guard,
                "ячейка «гард» запрета про правку свода не упоминает `Bash` — "
                "ограничение `tools` без этого выглядит достаточным, а это не так",
            )
            self.assertIn(
                "--write-profile",
                guard,
                "ячейка «гард» запрета про правку свода не упоминает `--write-profile` — "
                "`maturity.py` с этим флагом реально открывает файл на запись "
                "(`assets/maturity.py:930`), одного ограничения `tools` для этого недостаточно",
            )


if __name__ == "__main__":
    unittest.main()
