#!/usr/bin/env python3
"""Страж манифестов плагинов.

Обходит plugins/*/.claude-plugin/plugin.json и отказывает (код 1), если
на верхнем уровне манифеста есть ключ ``hooks``: хуки плагина грузятся
из hooks/hooks.json автоматически, поле в манифесте не нужно и уже
однажды приводило к инциденту. Невалидный JSON — тоже отказ, а не
молчаливый успех.

Второй отказ — расхождение описания плагина с его карточкой в
.claude-plugin/marketplace.json. Карточку читает тот, кто выбирает плагин
в списке маркетплейса, а манифест — тот, кто уже поставил его; разошлись
описания однажды, и в карточке остались снятые утверждения.

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
    descriptions = {}
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
        if not isinstance(data, dict):
            continue
        if FORBIDDEN_KEY in data:
            relative = manifest.relative_to(root)
            line = find_key_line(text)
            problems.append(
                f"{relative}, строка {line}: "
                f"запрещённый ключ верхнего уровня «{FORBIDDEN_KEY}»"
            )
        name = data.get("name") or manifest.parent.parent.name
        descriptions[name] = (manifest.relative_to(root), data.get("description"))
    problems.extend(check_marketplace_mirror(root, descriptions))
    return problems


def check_marketplace_mirror(root: Path, descriptions: dict) -> list[str]:
    """Сверяет описания карточек маркетплейса с описаниями манифестов.

    Плагин без карточки пропускается: наличие карточки — предмет другой
    проверки. Отсутствующий или неразбираемый marketplace.json тоже не
    отказ этой проверки — сверять нечего.
    """
    marketplace = root / ".claude-plugin" / "marketplace.json"
    if not marketplace.is_file():
        return []
    try:
        data = json.loads(marketplace.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [
            f"{marketplace.relative_to(root)}, строка {error.lineno}, "
            f"позиция {error.colno}: JSON не разобран: {error.msg}"
        ]
    cards = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(cards, list):
        return []

    problems = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        name = card.get("name")
        if name not in descriptions:
            continue
        manifest_path, manifest_description = descriptions[name]
        if card.get("description") == manifest_description:
            continue
        problems.append(
            f"{marketplace.relative_to(root)}: описание плагина «{name}» "
            f"расходится с {manifest_path}"
        )
    return problems


def find_key_line(text: str) -> int:
    """Номер строки ключа в верхнем объекте JSON."""
    depth = 0
    string_start = None
    escaped = False
    for index, character in enumerate(text):
        if string_start is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                following = text[index + 1 :].lstrip()
                key = json.loads(text[string_start : index + 1])
                if depth == 1 and following.startswith(":") and key == FORBIDDEN_KEY:
                    return text[:string_start].count("\n") + 1
                string_start = None
            continue
        if character == '"':
            string_start = index
        elif character in "[{":
            depth += 1
        elif character in "]}":
            depth -= 1
    raise ValueError(f"ключ верхнего уровня «{FORBIDDEN_KEY}» не найден")


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
