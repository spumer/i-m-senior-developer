"""Юнит-тесты сверки чисел отчёта с последним прогоном.

Детерминированный контракт: выбор результата по startedAt, коды выхода
0/1/2, разбор таблицы «Последний прогон», сообщение о расхождении с
именем поля, номером строки и обоими значениями, допуск даты одни
сутки, поля кейса и границы скана числовых зеркал.
"""

import io
import json
import textwrap
import tempfile
import unittest
from pathlib import Path

import check_report_numbers as crn

REPORT = textwrap.dedent("""\
    # Отчёт: planner

    ## Последний прогон

    | Параметр | Значение |
    |---|---|
    | Дата | 21.08.2026 |
    | Claude Code | `2.1.238` |
    | Версия плагина | `1.1.0` |
    | Модель | `opus`, судья `haiku` |
    | Порог | `1.0` (строгий) |
    | Стоимость | `$3.22` |
    | Длительность | 15 минут |
    | `partial` | `false` |

    | Кейс | Оценка | Успешных повторов |
    |---|---|---|
    | `baseline-provider-limits` | `1.00` | 3 из 3 |
    | `idea-routing` | `1.00` | 3 из 3 |
""")


def make_result(**overrides):
    case = {
        "name": "baseline-provider-limits",
        "runsPerCase": 3,
        "arms": {"with": [{"passed": True}, {"passed": True}, {"passed": True}]},
        "aggregates": {"score": 1.0, "passRate": 1.0},
    }
    case2 = {
        "name": "idea-routing",
        "runsPerCase": 3,
        "arms": {"with": [{"passed": True}, {"passed": True}, {"passed": True}]},
        "aggregates": {"score": 1.0, "passRate": 1.0},
    }
    document = {
        "schemaVersion": 1,
        "claudeVersion": "2.1.238",
        "startedAt": "2026-08-21T06:49:08.873Z",
        "durationSeconds": 900,
        "costUsd": 3.2199,
        "partial": False,
        "suite": {
            "root": "/x/plugins/planner",
            "ablation": "none",
            "modelOverride": "opus",
            "judgeModel": "haiku",
            "threshold": 1,
            "plugins": [{"name": "planner", "version": "1.1.0", "path": "/x"}],
        },
        "cases": [case, case2],
        "aggregates": {"casesTotal": 2, "casesPassed": 2},
    }
    for key, value in overrides.items():
        document[key] = value
    return document


class Harness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.results = self.root / "results"
        self.report = self.root / "report.md"
        self.err = io.StringIO()

    def tearDown(self):
        self._tmp.cleanup()

    def add_run(self, dirname, document, raw=None):
        run_dir = self.results / dirname
        run_dir.mkdir(parents=True)
        target = run_dir / "aggregate-result.json"
        target.write_text(raw if raw is not None else json.dumps(document))
        return target

    def add_report(self, text=REPORT):
        self.report.write_text(text)
        return self.report

    def run_check(self):
        return crn.main(
            ["--report", str(self.report), "--results", str(self.results)],
            out=self.err,
        )


class TestLatestSelection(unittest.TestCase):
    def test__latest_result__chosen_by_startedAt_not_dirname(self):
        """Позже начавшийся прогон выбирается даже при «раннем» имени каталога."""
        h = Harness()
        h.setUp()
        try:
            h.add_run(
                "run-00000001",
                make_result(
                    startedAt="2026-08-20T06:49:08.873Z", costUsd=9.99
                ),
            )
            h.add_run("run-ffffffff", make_result())  # позже по startedAt в JSON
            h.add_report()
            code = h.run_check()
            self.assertEqual(code, 0, h.err.getvalue())
        finally:
            h.tearDown()

    def test__latest_result__ignores_mtime_order(self):
        harness = Harness()
        harness.setUp()
        try:
            old = harness.results / "run-old"
            old.mkdir(parents=True)
            (old / "aggregate-result.json").write_text(json.dumps(make_result()))
            new = harness.results / "run-new"
            new.mkdir(parents=True)
            target = new / "aggregate-result.json"
            target.write_text(
                json.dumps(make_result(startedAt="2026-08-10T00:00:00.000Z"))
            )
            # mtime новой записи старше — выбор обязан идти по startedAt
            import os

            stamp = 1_000_000_000
            os.utime(target, (stamp, stamp))
            harness.add_report()
            # у «old» startedAt 21.08 — он и есть последний, отчёт совпадает с ним
            code = harness.run_check()
            self.assertEqual(code, 0, harness.err.getvalue())
        finally:
            harness.tearDown()


class TestExitCodes(Harness):
    def test__matching_report__exit_0(self):
        self.add_run("run-a", make_result())
        self.add_report()
        self.assertEqual(self.run_check(), 0)

    def test__cost_mismatch__exit_1_with_field_values_and_line(self):
        self.add_run("run-a", make_result(costUsd=3.06))
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        message = self.err.getvalue()
        self.assertIn("Стоимость", message)
        self.assertIn("3.22", message)
        self.assertIn("3.06", message)
        self.assertIn(str(self.report), message)
        self.assertIn("строка 12", message)

    def test__missing_cost__exit_1_names_missing_field(self):
        self.add_run("run-a", make_result())
        self.add_report(REPORT.replace("| Стоимость | `$3.22` |\n", ""))
        code = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("Стоимость", self.err.getvalue())

    def test__no_results__exit_2_with_explicit_message(self):
        self.results.mkdir()
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn("сверка не выполнялась", self.err.getvalue())

    def test__missing_results_dir__exit_2(self):
        self.add_report()
        self.assertEqual(self.run_check(), 2)

    def test__unparseable_json__exit_1_with_path_and_error(self):
        self.add_run("run-a", None, raw="{broken")
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        message = self.err.getvalue()
        self.assertIn(str(self.results / "run-a" / "aggregate-result.json"), message)


class TestFieldComparison(Harness):
    def test__date_within_one_day__passes(self):
        # startedAt 21.08 UTC, отчёт 22.08 — местная шкала, допуск одни сутки
        self.add_run("run-a", make_result())
        self.add_report(REPORT.replace("| Дата | 21.08.2026 |", "| Дата | 22.08.2026 |"))
        self.assertEqual(self.run_check(), 0)

    def test__date_beyond_one_day__exit_1(self):
        self.add_run("run-a", make_result())
        self.add_report(REPORT.replace("| Дата | 21.08.2026 |", "| Дата | 23.08.2026 |"))
        self.assertEqual(self.run_check(), 1)

    def test__claude_version_mismatch(self):
        self.add_run("run-a", make_result(claudeVersion="2.1.234"))
        self.add_report()
        self.assertEqual(self.run_check(), 1)

    def test__plugin_version_mismatch(self):
        document = make_result()
        document["suite"]["plugins"][0]["version"] = "1.0.9"
        self.add_run("run-a", document)
        self.add_report()
        self.assertEqual(self.run_check(), 1)

    def test__model_and_judge_mismatch(self):
        document = make_result()
        document["suite"]["judgeModel"] = "sonnet"
        self.add_run("run-a", document)
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("судья", self.err.getvalue())

    def test__threshold_mismatch(self):
        document = make_result()
        document["suite"]["threshold"] = 0.8
        self.add_run("run-a", document)
        self.add_report()
        self.assertEqual(self.run_check(), 1)

    def test__duration_mismatch(self):
        self.add_run("run-a", make_result(durationSeconds=600))
        self.add_report()
        self.assertEqual(self.run_check(), 1)

    def test__partial_mismatch(self):
        self.add_run("run-a", make_result(partial=True))
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("partial", self.err.getvalue())


class TestCaseRows(Harness):
    def test__case_score_mismatch(self):
        document = make_result()
        document["cases"][0]["aggregates"]["score"] = 0.6666666666666666
        self.add_run("run-a", document)
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("baseline-provider-limits", self.err.getvalue())

    def test__case_passed_arms_mismatch(self):
        document = make_result()
        document["cases"][0]["arms"]["with"][2]["passed"] = False
        self.add_run("run-a", document)
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        message = self.err.getvalue()
        self.assertIn("повтор", message.lower())

    def test__case_missing_from_report__exit_1(self):
        document = make_result()
        document["cases"].append(
            {
                "name": "multi-step-input",
                "runsPerCase": 3,
                "arms": {"with": [{"passed": True}] * 3},
                "aggregates": {"score": 1.0},
            }
        )
        self.add_run("run-a", document)
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("multi-step-input", self.err.getvalue())

    def test__case_extra_in_report__exit_1(self):
        document = make_result()
        document["cases"] = document["cases"][:1]
        self.add_run("run-a", document)
        self.add_report()
        code = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("idea-routing", self.err.getvalue())


class TestMirrorScan(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self._tmp.name) / "docs"
        self.err = io.StringIO()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, relative, text):
        target = self.docs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def scan(self):
        return crn.main(["--scan-mirrors", "--docs-root", str(self.docs)], out=self.err)

    def test__money_mirror__exit_1(self):
        path = self.write("testing/running.md", "Прогон стоит $3.06.\n")
        self.assertEqual(self.scan(), 1)
        message = self.err.getvalue()
        self.assertIn("$3.06", message)
        self.assertIn(str(path), message)
        self.assertIn("строка 1", message)

    def test__repeats_near_score__exit_1(self):
        self.write("plugins/planner.md", "Кейс `x` | `1.00` | 3 из 3\n")
        self.assertEqual(self.scan(), 1)

    def test__repeats_without_score_nearby__pass(self):
        self.write("plugins/planner.md", "Повторили 3 из 3 раз, без оценки.\n")
        self.assertEqual(self.scan(), 0)

    def test__reports_dir_excluded(self):
        self.write("reports/planner.md", "| Стоимость | `$3.22` |\n| Кейс | `1.00` | 3 из 3 |\n")
        self.assertEqual(self.scan(), 0)

    def test__clean_docs__exit_0(self):
        self.write("plugins/planner.md", "Стоимость — в отчёте, повторы — там же.\n")
        self.assertEqual(self.scan(), 0)


if __name__ == "__main__":
    unittest.main()
