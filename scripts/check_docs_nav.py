"""Страж полноты навигации документации.

Сравнивает рекурсивный набор docs/**/*.md со списком project.nav из
zensical.toml. Код 0 — только при точном совпадении без повторов; код 1 —
пропуск, лишняя цель, повтор, недопустимый путь или неразбираемый вход;
код 64 — неверный вызов CLI.
"""

import argparse
import sys
import tomllib
from pathlib import Path, PurePosixPath
from typing import NoReturn

DIAGNOSTIC_PREFIX = "проверка полноты навигации:"
EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 64


def fail(message) -> NoReturn:
    print(f"{DIAGNOSTIC_PREFIX} {message}", file=sys.stderr)
    sys.exit(EXIT_MISMATCH)


def collect_pages(docs_dir):
    return {
        path.relative_to(docs_dir).as_posix()
        for path in sorted(docs_dir.rglob("*.md"))
        if path.is_file()
    }


def load_nav(root):
    config_path = root / "zensical.toml"
    if not config_path.is_file():
        fail(f"нет {config_path}")
    try:
        with open(config_path, "rb") as handle:
            config = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        fail(f"TOML не разобран: {error}")
    project = config.get("project")
    if not isinstance(project, dict):
        fail("нет таблицы [project]")
    nav = project.get("nav")
    if not isinstance(nav, list):
        fail("нет списка project.nav")
    seen = set()
    for item in nav:
        if not isinstance(item, str):
            fail(f"в project.nav нестроковый элемент: {item!r}")
        pure = PurePosixPath(item)
        if pure.is_absolute() or ".." in pure.parts:
            fail(f"недопустимый путь в project.nav: {item}")
        if pure.suffix != ".md":
            fail(f"цель project.nav не Markdown: {item}")
        normalized = pure.as_posix()
        if normalized in seen:
            fail(f"повтор в project.nav: {item}")
        seen.add(normalized)
    return seen


class GuardParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: ошибка: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def main(argv=None):
    parser = GuardParser(
        description="Проверка полноты навигации документации."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="корень репозитория с zensical.toml и docs/",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    docs_dir = root / "docs"
    if not root.is_dir():
        fail(f"нет каталога {root} с zensical.toml")
    if not docs_dir.is_dir():
        fail(f"нет каталога {docs_dir}")

    pages = collect_pages(docs_dir)
    nav = load_nav(root)

    missing = sorted(pages - nav)
    if missing:
        fail("нет в project.nav: " + ", ".join(missing))
    extra = sorted(nav - pages)
    if extra:
        fail("лишнее в project.nav: " + ", ".join(extra))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
