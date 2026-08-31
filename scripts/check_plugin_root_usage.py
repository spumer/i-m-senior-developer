#!/usr/bin/env python3
"""Страж способа получения корня плагина.

В текстах команд, скиллов и агентов путь к ресурсам плагина должен приходить
из подстановки ``${CLAUDE_PLUGIN_ROOT}``, а не из переменной окружения во
время работы. Каталоги hooks исключены: там переменная доступна. Документация
вне каталогов компонентов не сканируется, потому что модель не исполняет её
как инструкцию. Корень без каталога plugins — неверный вызов с кодом 64.
Успех — код 0 без вывода; нарушение — код 1 с путём и номером строки.

Запуск из корня репозитория::

    python3 scripts/check_plugin_root_usage.py

Для изолированной копии корень передаётся явно::

    python3 scripts/check_plugin_root_usage.py --root /путь/к/копии
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

VARIABLE_NAME = "CLAUDE_PLUGIN_ROOT"
SUBSTITUTION = "${CLAUDE_PLUGIN_ROOT}"
VARIABLE_PATTERN = re.compile(re.escape(VARIABLE_NAME))
EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_USAGE = 64


class GuardParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: ошибка: {message}\n")


def is_allowed_occurrence(line: str, start: int, end: int) -> bool:
    return line[start - 2 : end + 1] == SUBSTITUTION


def component_directory(path: Path) -> str | None:
    """Возвращает имя компонента в пути plugins/<плагин>/<компонент>/… ."""
    if len(path.parts) < 4 or path.parts[0] != "plugins":
        return None
    return path.parts[2]


def is_checked_component_path(path: Path) -> bool:
    return component_directory(path) in {"commands", "skills", "agents", "hooks"}


def is_hook_path(path: Path) -> bool:
    return component_directory(path) == "hooks"


def check_plugin_root_usage(root: Path) -> list[str]:
    """Возвращает нарушения; без plugins/ возбуждает FileNotFoundError."""
    plugins_dir = root / "plugins"
    if not plugins_dir.is_dir():
        raise FileNotFoundError(f"нет каталога {plugins_dir}")

    problems = []
    for path in sorted(plugins_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if (
            not is_checked_component_path(relative)
            or is_hook_path(relative)
            or "__pycache__" in relative.parts
        ):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        except OSError as error:
            problems.append(f"{relative}: не прочитан: {error}")
            continue
        for line_number, line in enumerate(lines, start=1):
            for match in VARIABLE_PATTERN.finditer(line):
                if is_allowed_occurrence(line, match.start(), match.end()):
                    continue
                problems.append(
                    f"{relative}:{line_number}: {VARIABLE_NAME} в команде, скилле "
                    f"или агенте должен быть записан как {SUBSTITUTION}"
                )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = GuardParser(description="Проверка способа получения корня плагина.")
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
    try:
        problems = check_plugin_root_usage(root.resolve())
    except FileNotFoundError as error:
        parser.error(str(error))
    for problem in problems:
        print(problem, file=sys.stderr)
    return EXIT_VIOLATION if problems else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
