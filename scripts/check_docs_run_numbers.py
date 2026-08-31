"""Запрет чисел наблюдённого прогона в документации.

Числа прогона — стоимость, длительность, оценки кейсов, счёт успешных
повторов — живут в его `aggregate-result.json`, который Git не отслеживает.
Перенесённые в `docs/` они устаревают молча: страница не знает, что прогон
повторили, и читатель верит числу, которого больше нет.

Страж ловит только машинно опознаваемые следы: денежную сумму вида $X.XX и
пару «N из M» рядом с оценкой. Смысловой пересказ он не ловит и правдивость
прозы не проверяет.

Коды выхода: 0 — чисто; 1 — найдено числовое зеркало; 64 — неверный вызов.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXIT_OK = 0
EXIT_MIRROR_FOUND = 1
EXIT_USAGE = 64

MONEY_RE = re.compile(r"\$\d+\.\d{2}")
SCORE_RE = re.compile(r"\b\d\.\d{2}\b")
REPEATS_RE = re.compile(r"(\d+)\s+из\s+(\d+)")


class GuardParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: ошибка: {message}\n")


def scan_docs(docs_root, out):
    found = []
    for path in sorted(docs_root.rglob("*.md")):
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            hits = list(MONEY_RE.finditer(line))
            if REPEATS_RE.search(line) and SCORE_RE.search(line):
                hits.append(None)
            for hit in hits:
                fragment = hit.group(0) if hit else "N из M рядом с оценкой"
                found.append(f"{path}, строка {number}: числовое зеркало {fragment}")
    if found:
        for line in found:
            print(line, file=out)
        return EXIT_MIRROR_FOUND
    return EXIT_OK


def build_parser():
    parser = GuardParser(
        description="Запрет чисел наблюдённого прогона в документации."
    )
    parser.add_argument("--docs-root", type=Path, help="корень docs/ для скана")
    return parser


def main(argv=None, out=sys.stderr):
    args = build_parser().parse_args(argv)
    docs_root = args.docs_root or REPO_ROOT / "docs"
    if not docs_root.is_dir():
        print(f"каталог документации не найден: {docs_root}", file=out)
        return EXIT_USAGE
    return scan_docs(docs_root, out)


if __name__ == "__main__":
    sys.exit(main())
