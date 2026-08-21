#!/usr/bin/env python3
"""Страж манифестов плагинов.

Обходит plugins/*/.claude-plugin/plugin.json и отказывает (код 1), если
на верхнем уровне манифеста есть ключ ``hooks``: хуки плагина грузятся
из hooks/hooks.json автоматически, поле в манифесте не нужно и уже
однажды приводило к инциденту. Невалидный JSON — тоже отказ, а не
молчаливый успех.

Успех — код 0 без вывода.

Запуск из корня репозитория::

    python3 scripts/check_manifests.py

Для изолированной копии корень передаётся явно::

    python3 scripts/check_manifests.py --root /путь/к/копии
"""

import argparse
import json
import sys
from pathlib import Path

FORBIDDEN_KEY = "hooks"


def check_manifests(root: Path) -> list[str]:
    """Возвращает список диагностических строк; пустой список — успех."""
    problems = []
    manifests_dir = root / "plugins"
    for manifest in sorted(manifests_dir.glob("*/.claude-plugin/plugin.json")):
        text = manifest.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            relative = manifest.relative_to(root)
            problems.append(
                f"{relative}, строка {error.lineno}, позиция {error.colno}: "
                f"JSON не разобран: {error.msg}"
            )
            continue
        if isinstance(data, dict) and FORBIDDEN_KEY in data:
            relative = manifest.relative_to(root)
            line = find_key_line(text)
            problems.append(
                f"{relative}, строка {line}: "
                f"запрещённый ключ верхнего уровня «{FORBIDDEN_KEY}»"
            )
    return problems


def find_key_line(text: str) -> int:
    """Номер строки первого вхождения ключа как строки JSON-текста."""
    marker = f'"{FORBIDDEN_KEY}"'
    return text[: text.index(marker)].count("\n") + 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Страж манифестов плагинов.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="корень репозитория (по умолчанию — родитель scripts/)",
    )
    args = parser.parse_args(argv)
    problems = check_manifests(args.root)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
