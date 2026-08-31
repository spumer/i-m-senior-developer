#!/usr/bin/env python3
"""Страж соответствия встроенных поставщиков каталогу агентов.

Для каждой встроенной строки матрицы способностей поставляемого шаблона
проверяет, что поставщик ``<плагин>:<имя>`` имеет одноимённый файл агента с
совпадающим заголовочным ``name``. Форматом таблицы владеет только
``product_state.py parse-capabilities``; этот скрипт читает его JSON-результат.

Успех — код 0 без вывода. Нарушение договора — код 1 с диагностикой. Неверный
корень репозитория или отсутствие обязательных каталогов — код 64.

Для YAML-заголовка агента страж принимает закрытый ограничителями ``---``
верхнеуровневый скаляр ``name`` с простым, одинарно- или двойно-кавычным ключом
и значением, включая начальную UTF-8 BOM. После каждого разделителя допустимы
только ASCII-пробелы и табуляции. Комментарий после открывающего разделителя и
``...`` вместо закрывающего разделителя не поддерживаются: при проверенном вызове
``claude plugin validate <корень-плагина>/agents --strict`` валидатор в этих
формах не видит рамку и пропускает файл. В этом вызове валидатор принимает и
другие формы закрывающей границы (``---extra``, ``----`` и отступ перед ``---``),
но страж намеренно их не повторяет: для закрытого набора наших файлов точный отказ
дешевле ложного допуска.

Разделяющим считается только двоеточие, за которым идёт пробел, табуляция или
конец строки; строка с комментарием до такого двоеточия не объявляет поле. В
двойных кавычках допустимы JSON-совместимые экранирования, в одинарных —
удвоенная одинарная кавычка. Inline-комментарий начинается после пробела, в том
числе после закрывающей кавычки; ``#`` внутри кавычек остаётся значением. Общий
отступ рамки из ASCII-пробелов допускается: первая допустимая YAML-пара задаёт
базовый уровень, а более глубокий ``name`` остаётся вложенным; пара с меньшим
отступом рамку отвергает. Некавычное имя входит в это подмножество, только если
совпадает с ``[a-z][a-z0-9]*(?:-[a-z0-9]+)*`` и не является ``true``, ``false``
или ``null``; кавычное значение остаётся строкой без этого ограничения. Блочные
скаляры, якоря и поточные отображения для этого поля не входят в договор. Страж
намеренно строже хоста для некавычных имён вроде ``123abc`` и ``2026-08-25``, а
также для повтора верхнеуровневого ``name``: в закрытом наборе встроенных
поставщиков имена выбираются нами, поэтому явный отказ безопаснее догадки о
YAML-типе, а ровно одно непустое поле делает ожидаемое имя однозначным.

Страж удостоверяет только равенство объявленного имени ожидаемому; разбираемость
YAML-заголовка он не удостоверяет. Job ``manifests`` в
``.github/workflows/tests.yml`` выполняет тот же вызов хоста ``claude plugin
validate "$plugin/$components" --strict`` по тем же каталогам компонентов и тем
самым проверяет только принятие этих файлов валидатором. Диспетчеризацию агента по
имени во время работы не наблюдают ни job, ни страж.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn


EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_USAGE = 64
ASCII_WHITESPACE = " \t"
# Нечувствительность к регистру держит принимаемое подмножество одинаковым для
# значения в кавычках и без них: YAML отдаёт обычную строку в обоих видах, а
# разный регистр здесь — расхождение имени, о котором и надо сказать.
UNQUOTED_AGENT_NAME = re.compile(
    r"(?!(?:true|false|null)\Z)[a-z][a-z0-9]*(?:-[a-z0-9]+)*",
    re.IGNORECASE,
)
HELPER_PATH = Path("plugins/planner/skills/product-discovery/assets/product_state.py")
TEMPLATE_PATH = Path("plugins/planner/skills/planner/references/template-context.md")


class GuardParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: ошибка: {message}\n")


def relative_path(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def parse_capabilities(root: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    helper = root / HELPER_PATH
    template = root / TEMPLATE_PATH
    try:
        completed = subprocess.run(
            [sys.executable, str(helper), "parse-capabilities", str(template)],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        return None, f"не запущен разбор матрицы способностей: {error}"
    if completed.returncode != EXIT_OK:
        detail = completed.stderr.strip() or completed.stdout.strip()
        if not detail:
            detail = f"подкоманда завершилась с кодом {completed.returncode}"
        return None, f"не удалось разобрать матрицу способностей: {detail}"
    try:
        rows = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return None, f"подкоманда вернула не JSON: {error.msg}"
    if not isinstance(rows, list):
        return None, "подкоманда вернула не массив строк способностей"
    if not rows:
        return None, "подкоманда вернула пустую матрицу способностей"
    if not all(isinstance(row, dict) for row in rows):
        return None, "подкоманда вернула массив с некорректной строкой способностей"
    for row in rows:
        described = row_description(row)
        source = row.get("source")
        if described is None or not isinstance(source, str) or not source:
            return None, "подкоманда вернула некорректную строку способностей"
    return rows, None


def row_description(row: dict[str, Any]) -> tuple[str, str, int] | None:
    capability = row.get("capability")
    provider = row.get("provider")
    line = row.get("line")
    if (
        not isinstance(capability, str)
        or not capability
        or not isinstance(provider, str)
        or not provider
        or not isinstance(line, int)
        or isinstance(line, bool)
    ):
        return None
    return capability, provider, line


def provider_parts(provider: str) -> tuple[str, str] | None:
    parts = provider.split(":")
    if len(parts) != 2:
        return None
    plugin, agent_name = parts
    if not plugin or not agent_name:
        return None
    if any(part in {".", ".."} or "/" in part or "\\" in part for part in parts):
        return None
    return plugin, agent_name


def quoted_scalar_value(value: str) -> str | None:
    quote = value[0]
    if quote == '"':
        escaped = False
        end = None
        for index, character in enumerate(value[1:], start=1):
            if character == '"' and not escaped:
                end = index
                break
            escaped = character == "\\" and not escaped
            if character != "\\":
                escaped = False
        if end is None:
            return None
        try:
            declared = json.loads(value[: end + 1])
        except json.JSONDecodeError:
            return None
    else:
        characters: list[str] = []
        index = 1
        while index < len(value):
            character = value[index]
            if character != "'":
                characters.append(character)
                index += 1
                continue
            if index + 1 < len(value) and value[index + 1] == "'":
                characters.append("'")
                index += 2
                continue
            end = index
            declared = "".join(characters)
            break
        else:
            return None

    tail = value[end + 1 :]
    if tail.strip(ASCII_WHITESPACE):
        if (
            tail[:1] not in ASCII_WHITESPACE
            or not tail.lstrip(ASCII_WHITESPACE).startswith("#")
        ):
            return None
    return declared


def scalar_value(value: str) -> str | None:
    declared = value.strip(ASCII_WHITESPACE)
    if not declared:
        return ""
    if declared[0] in {"'", '"'}:
        return quoted_scalar_value(declared)
    for index, character in enumerate(declared):
        if character == "#" and (
            index == 0 or declared[index - 1] in ASCII_WHITESPACE
        ):
            declared = declared[:index].rstrip(ASCII_WHITESPACE)
            break
    return declared if UNQUOTED_AGENT_NAME.fullmatch(declared) else None


def is_name_key(key: str) -> bool:
    declared = key.strip(ASCII_WHITESPACE)
    if declared == "name":
        return True
    if len(declared) < 2 or declared[0] not in {"'", '"'}:
        return False
    return scalar_value(declared) == "name"


def frontmatter_pair(line: str) -> tuple[str, str] | None:
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(line):
        character = line[index]
        if quote == '"':
            if character == '"' and not escaped:
                quote = None
            escaped = character == "\\" and not escaped
            if character != "\\":
                escaped = False
            index += 1
            continue
        if quote == "'":
            if character == "'":
                if index + 1 < len(line) and line[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if character in {"'", '"'}:
            quote = character
        elif character == "#":
            return None
        elif character == ":" and (
            index + 1 == len(line) or line[index + 1] in ASCII_WHITESPACE
        ):
            return line[:index], line[index + 1 :]
        index += 1
    return None


def is_supported_frontmatter_delimiter(line: str) -> bool:
    return line.startswith("---") and not line[3:].strip(ASCII_WHITESPACE)


def agent_name_from_frontmatter(path: Path) -> tuple[str | None, str | None]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return None, "файл агента не удалось прочитать"
    if not lines or not is_supported_frontmatter_delimiter(lines[0]):
        return None, "рамка заголовка не в поддерживаемом виде"

    names: list[tuple[str, str | None]] = []
    base_indent: int | None = None
    for line in lines[1:]:
        if is_supported_frontmatter_delimiter(line):
            break
        pair = frontmatter_pair(line)
        if pair is None:
            continue
        key, value = pair
        indent = len(key) - len(key.lstrip(" "))
        if key[indent:][:1].isspace():
            continue
        if base_indent is None:
            base_indent = indent
        elif indent < base_indent:
            return None, "рамка заголовка не в поддерживаемом виде"
        if indent == base_indent and is_name_key(key[indent:]):
            names.append((value, scalar_value(value)))
    else:
        return None, "рамка заголовка не в поддерживаемом виде"

    if not names:
        return None, "поле «name» в рамке заголовка не объявлено"
    if len(names) > 1:
        return None, "поле «name» объявлено больше одного раза"

    value, declared_name = names[0]
    if not declared_name:
        written_value = value.strip(ASCII_WHITESPACE)
        return (
            None,
            "значение поля «name» вне принимаемого подмножества: "
            f"«{written_value}»",
        )
    return declared_name, None


def diagnostic_prefix(capability: str, provider: str, line: int) -> str:
    return f"способность «{capability}», поставщик «{provider}», строка {line}"


def check_builtin_providers(root: Path) -> list[str]:
    rows, parse_error = parse_capabilities(root)
    if parse_error is not None:
        return [parse_error]
    assert rows is not None

    problems = []
    for row in rows:
        if row.get("source") != "builtin":
            continue
        described = row_description(row)
        if described is None:
            problems.append("встроенная строка матрицы не содержит способность, поставщика или номер строки")
            continue
        capability, provider, line = described
        prefix = diagnostic_prefix(capability, provider, line)
        parts = provider_parts(provider)
        if parts is None:
            problems.append(f"{prefix}: некорректный адрес встроенного поставщика")
            continue
        plugin, agent_name = parts
        plugin_path = root / "plugins" / plugin
        agent_path = plugin_path / "agents" / f"{agent_name}.md"
        expected_path = relative_path(root, agent_path)
        if plugin not in {
            candidate.name for candidate in plugin_path.parent.iterdir() if candidate.is_dir()
        }:
            problems.append(
                f"{prefix}: нет плагина «{plugin}»; ожидался каталог "
                f"{relative_path(root, plugin_path)} (файл агента {expected_path})"
            )
            continue
        if not agent_path.is_file():
            problems.append(f"{prefix}: нет файла агента {expected_path}")
            continue
        declared_name, frontmatter_error = agent_name_from_frontmatter(agent_path)
        if frontmatter_error is not None:
            problems.append(f"{prefix}: файл агента {expected_path}: {frontmatter_error}")
        elif declared_name != agent_name:
            assert declared_name is not None
            problems.append(
                f"{prefix}: файл агента {expected_path}: ожидалось имя «{agent_name}», "
                f"указано «{declared_name}»"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = GuardParser(description="Проверка встроенных поставщиков матрицы способностей.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="корень репозитория с plugins/ (по умолчанию — родитель scripts/)",
    )
    options = parser.parse_args(argv)
    root = options.root.expanduser()
    if not root.is_dir():
        parser.error(f"нет каталога {root}")
    root = root.resolve()
    plugins = root / "plugins"
    if not plugins.is_dir():
        parser.error(f"нет каталога {plugins}")
    helper = root / HELPER_PATH
    if not helper.is_file():
        parser.error(f"нет помощника разбора {helper}")
    template = root / TEMPLATE_PATH
    if not template.is_file():
        parser.error(f"нет поставляемого шаблона {template}")

    problems = check_builtin_providers(root)
    for problem in problems:
        print(problem, file=sys.stderr)
    return EXIT_VIOLATION if problems else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
