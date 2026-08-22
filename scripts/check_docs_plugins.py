"""Страж соответствия документации манифестам плагинов.

Запрещает документации держать второй экземпляр сведений из plugin.json и
дерева плагинов: литерал X.Y.Z в docs/**/*.md, чьё ближайшее предшествующее
имя на строке — имя плагина (а не чужой продукт вроде Claude Code), обязан
равняться версии манифеста; колонки состава в каталоге плагинов
запрещены; строки каталога обязаны совпадать с множеством плагинов.
Код 0 — только при полном совпадении; код 1 — расхождение или нарушение
запрета, диагностика называет файл, строку, плагин и поле; код 64 —
неверный вызов CLI.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NoReturn

DIAGNOSTIC_PREFIX = "проверка соответствия документации манифестам:"
EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 64

VERSION_RE = re.compile(r"\b\d+\.\d+\.\d+\b")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
FORBIDDEN_COLUMNS = ("Версия", "Команды", "Скиллы", "Агенты", "Хуки")
FOREIGN_PRODUCTS = ("Claude Code", "Zensical", "Python")
CATALOG_PAGE = Path("docs") / "plugins" / "index.md"


def fail(message) -> NoReturn:
    print(f"{DIAGNOSTIC_PREFIX} {message}", file=sys.stderr)
    sys.exit(EXIT_MISMATCH)


def usage_error(parser, message) -> NoReturn:
    print(f"{DIAGNOSTIC_PREFIX} {message}", file=sys.stderr)
    parser.print_usage(sys.stderr)
    print(f"{parser.prog}: ошибка: {message}", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def load_plugin_versions(root):
    """Вернуть {имя каталога: version} по plugins/*/.claude-plugin/plugin.json."""
    versions = {}
    plugins_dir = root / "plugins"
    if not plugins_dir.is_dir():
        return versions
    for manifest in sorted(plugins_dir.glob("*/.claude-plugin/plugin.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            fail(f"не прочитан {manifest}: {error}")
        version = data.get("version")
        if not isinstance(version, str):
            fail(f"нет строки version в {manifest}")
        versions[manifest.parents[1].name] = version
    return versions


def nearest_owner(line, position, versions):
    """Ближайшее имя до position в строке: плагин, чужой продукт или None."""
    best_name, best_pos = None, -1
    for name in list(versions) + list(FOREIGN_PRODUCTS):
        pos = line.rfind(name, 0, position)
        if pos > best_pos:
            best_name, best_pos = name, pos
    return best_name


def check_versions(docs_dir, versions):
    """X.Y.Z, чьё ближайшее предшествующее имя на строке — плагин,
    равен версии манифеста этого плагина."""
    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir.parent)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in VERSION_RE.finditer(line):
                name = nearest_owner(line, match.start(), versions)
                if name not in versions:
                    continue
                expected = versions[name]
                found = match.group(0)
                if found != expected:
                    fail(
                        f"{rel}:{lineno}: плагин {name}, поле «версия»: "
                        f"в тексте {found}, в манифесте {expected}"
                    )


def catalog_table_lines(catalog_path):
    rel = catalog_path.relative_to(catalog_path.parents[2])
    for lineno, line in enumerate(
        catalog_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if line.lstrip().startswith("|"):
            yield rel, lineno, line


def check_columns(catalog_path):
    for rel, lineno, line in catalog_table_lines(catalog_path):
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        for column in FORBIDDEN_COLUMNS:
            if column in cells:
                fail(
                    f"{rel}:{lineno}: колонка «{column}» запрещена: "
                    "состав и версии показывает страница плагина, не каталог"
                )


def check_completeness(catalog_path, versions):
    links = set()
    for _, _, line in catalog_table_lines(catalog_path):
        for text, target in LINK_RE.findall(line):
            if text == Path(target).stem:
                links.add(text)
    missing = sorted(versions.keys() - links)
    if missing:
        fail("нет строки плагина в каталоге: " + ", ".join(missing))
    extra = sorted(links - versions.keys())
    if extra:
        fail("лишняя строка плагина в каталоге: " + ", ".join(extra))


class GuardParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: ошибка: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def main(argv=None):
    parser = GuardParser(
        description="Проверка соответствия документации манифестам плагинов."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="корень репозитория с plugins/ и docs/",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    docs_dir = root / "docs"
    if not root.is_dir():
        usage_error(parser, f"нет каталога {root}")
    if not docs_dir.is_dir():
        usage_error(parser, f"нет каталога {docs_dir}")

    versions = load_plugin_versions(root)
    catalog_path = root / CATALOG_PAGE
    if not catalog_path.is_file():
        fail(f"нет страницы каталога {root / CATALOG_PAGE}")

    check_versions(docs_dir, versions)
    check_columns(catalog_path)
    check_completeness(catalog_path, versions)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
