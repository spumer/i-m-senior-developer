"""Сверка таблицы «Последний прогон» отчёта с последним результатом прогона.

Локальный предрелизный страж: читает docs/reports/<plugin>.md и
plugins/<plugin>/evals/results/run-*/aggregate-result.json, выбирает
самый поздний результат по полю startedAt внутри файла и сверяет
фиксированный машинный контракт ячеек таблицы.

Коды выхода: 0 — совпадение; 1 — расхождение или ошибка разбора;
2 — результатов нет («сверка не выполнялась»).

Режим --scan-mirrors проверяет только числовые зеркала прогона
($X.XX и «N из N» рядом с оценкой) в docs/ вне docs/reports/; он
пригоден для CI, где результатов нет, и не является проверкой
правдивости прозы.
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

LAST_RUN_HEADING = "## Последний прогон"
MONEY_RE = re.compile(r"\$\d+\.\d{2}")
SCORE_RE = re.compile(r"\b\d\.\d{2}\b")
REPEATS_RE = re.compile(r"(\d+)\s+из\s+(\d+)")


def strip_marks(value):
    return value.strip().strip("`").strip()


def parse_report(text):
    """Разобрать именованные ячейки таблиц раздела «Последний прогон».

    Возвращает (params: dict имя -> (значение, номер строки),
    cases: dict имя кейса -> (оценка, повторы, номер строки)).
    """
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == LAST_RUN_HEADING)
    except StopIteration:
        raise ValueError(f"раздел «{LAST_RUN_HEADING}» не найден") from None
    params = {}
    cases = {}
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("#"):
            break
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] not in ("Параметр", "---"):
            params[cells[0]] = (cells[1], index + 1)
        if len(cells) == 3:
            name = cells[0].strip("`")
            if name in ("Кейс", "---"):
                continue
            cases[name] = (cells[1], cells[2], index + 1)
    return params, cases


def parse_date(cell):
    day, month, year = cell.split(".")
    return date(int(year), int(month), int(day))


def extract_model(cell):
    model = re.search(r"`([^`]+)`", cell)
    judge = re.search(r"судья `([^`]+)`", cell)
    return (model.group(1) if model else None, judge.group(1) if judge else None)


def expected_params(document):
    """Фактические значения полей из результата прогона."""
    suite = document["suite"]
    return {
        "Дата": parse_iso_date(document["startedAt"]),
        "Claude Code": document["claudeVersion"],
        "Версия плагина": suite["plugins"][0]["version"],
        "Модель": (suite.get("modelOverride"), suite.get("judgeModel")),
        "Порог": suite["threshold"],
        "Стоимость": round(document["costUsd"], 2),
        "Длительность": round(document["durationSeconds"] / 60),
        "`partial`": document["partial"],
    }


def parse_iso_date(started_at):
    moment = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    return moment.astimezone(timezone.utc).date()


def load_latest(results_dir):
    """Самый поздний результат по startedAt; (None, None), если каталог пуст.

    Неразбираемый JSON — ошибка разбора с путём, а не «нет результатов».
    """
    paths = sorted(results_dir.glob("run-*/aggregate-result.json"))
    if not paths:
        return None, None
    latest = None
    for path in paths:
        try:
            document = json.loads(path.read_text())
            started = parse_iso_date(document["startedAt"])
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
            raise ValueError(f"не читается {path}: {error}") from None
        key = (started, document["startedAt"])
        if latest is None or key > latest[0]:
            latest = (key, document)
    return latest[1], latest[1]["startedAt"]


def compare_params(params, document):
    """Список строк-расхождений по ячейкам таблицы параметров."""
    expected = expected_params(document)
    mismatches = []

    def fail(field, report_value, actual, line):
        mismatches.append(
            f"расхождение: {field}: в отчёте {report_value!r}, в результате {actual!r}"
            f" ({line})"
        )

    for field, (cell, line) in params.items():
        where = f"строка {line}"
        if field == "Дата":
            report_date = parse_date(strip_marks(cell))
            if abs((report_date - expected[field]).days) > 1:
                fail(field, cell, expected[field].isoformat(), where)
        elif field == "Модель":
            model, judge = extract_model(cell)
            actual_model, actual_judge = expected[field]
            if model != actual_model:
                fail("Модель", cell, actual_model, where)
            if judge != actual_judge:
                fail("судья", cell, actual_judge, where)
        elif field == "Порог":
            report_value = float(strip_marks(cell.split()[0]))
            if report_value != float(expected[field]):
                fail(field, cell, expected[field], where)
        elif field == "Стоимость":
            report_value = round(float(strip_marks(cell).lstrip("$")), 2)
            if report_value != expected[field]:
                fail(field, cell, expected[field], where)
        elif field == "Длительность":
            report_value = int(strip_marks(cell).split()[0])
            if report_value != expected[field]:
                fail(field, cell, expected[field], where)
        else:
            report_value = strip_marks(cell)
            actual = expected[field]
            if isinstance(actual, bool):
                if report_value != str(actual).lower():
                    fail(field, cell, actual, where)
            elif report_value != str(actual):
                fail(field, cell, actual, where)
    return mismatches


def compare_cases(cases, document):
    """Список строк-расхождений по строкам таблицы кейсов."""
    mismatches = []
    result_cases = {case["name"]: case for case in document["cases"]}
    for name, (score_cell, repeats_cell, line) in cases.items():
        case = result_cases.get(name)
        if case is None:
            mismatches.append(
                f"расхождение: кейс {name}: есть в отчёте, отсутствует в результате"
                f" (строка {line})"
            )
            continue
        report_score = round(float(strip_marks(score_cell)), 2)
        actual_score = round(case["aggregates"]["score"], 2)
        if report_score != actual_score:
            mismatches.append(
                f"расхождение: кейс {name}, оценка: в отчёте {score_cell},"
                f" в результате {actual_score} (строка {line})"
            )
        passed = sum(1 for run in case["arms"].get("with", []) if run.get("passed"))
        repeats = REPEATS_RE.search(repeats_cell)
        if not repeats:
            mismatches.append(
                f"расхождение: кейс {name}, успешные повторы: ячейка"
                f" {repeats_cell!r} не вида «N из M» (строка {line})"
            )
        else:
            report_passed, report_total = (int(g) for g in repeats.groups())
            if (report_passed, report_total) != (passed, case["runsPerCase"]):
                mismatches.append(
                    f"расхождение: кейс {name}, успешные повторы: в отчёте"
                    f" {repeats_cell}, в результате {passed} из"
                    f" {case['runsPerCase']} (строка {line})"
                )
    for name in result_cases:
        if name not in cases:
            mismatches.append(
                f"расхождение: кейс {name}: есть в результате, отсутствует в отчёте"
            )
    return mismatches


def check_report(report_path, results_dir, out):
    try:
        params, cases = parse_report(report_path.read_text())
    except (OSError, ValueError) as error:
        print(f"ошибка разбора отчёта {report_path}: {error}", file=out)
        return 1
    try:
        document, started_at = load_latest(results_dir)
    except ValueError as error:
        print(error, file=out)
        return 1
    if document is None:
        print(f"сверка не выполнялась: в «{results_dir}» нет ни одного результата прогона", file=out)
        return 2
    mismatches = compare_params(params, document) + compare_cases(cases, document)
    if mismatches:
        for line in mismatches:
            print(f"{report_path}: {line}", file=out)
        return 1
    print(f"сверка пройдена: отчёт соответствует прогону {started_at}", file=out)
    return 0


def scan_mirrors(docs_root, out):
    """Числовые зеркала прогона в docs/ вне docs/reports/.

    Ловит только денежную сумму $X.XX и пару «N из M» рядом с оценкой;
    смысловой пересказ не ловит и не проверяет.
    """
    found = []
    for path in sorted(docs_root.rglob("*.md")):
        if "reports" in path.relative_to(docs_root).parts:
            continue
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
        return 1
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plugin", nargs="?", help="имя плагина для обычной сверки")
    parser.add_argument("--report", type=Path, help="явный путь к отчёту")
    parser.add_argument("--results", type=Path, help="явный каталог результатов")
    parser.add_argument(
        "--scan-mirrors",
        action="store_true",
        help="только скан числовых зеркал в docs/ (режим CI)",
    )
    parser.add_argument("--docs-root", type=Path, help="корень docs/ для скана зеркал")
    return parser


def main(argv=None, out=sys.stderr):
    args = build_parser().parse_args(argv)
    if args.scan_mirrors:
        docs_root = args.docs_root or REPO_ROOT / "docs"
        return scan_mirrors(docs_root, out)
    report = args.report or REPO_ROOT / "docs" / "reports" / f"{args.plugin}.md"
    results = args.results or REPO_ROOT / "plugins" / args.plugin / "evals" / "results"
    code = check_report(report, results, out)
    if code == 0 and not args.report and not args.results:
        # обычный предрелизный вызов сканирует и зеркала; изолированный
        # вызов с явными путями проверяет только таблицу
        code = scan_mirrors(REPO_ROOT / "docs", out)
    return code


if __name__ == "__main__":
    sys.exit(main())
