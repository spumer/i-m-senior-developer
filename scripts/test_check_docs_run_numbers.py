#!/usr/bin/env python3
"""Проверки стража чисел прогона в документации.

Запуск::

    python3 scripts/test_check_docs_run_numbers.py
"""

from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_docs_run_numbers.py")
SPEC = importlib.util.spec_from_file_location("check_docs_run_numbers", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class DocsRunNumbersTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.docs = Path(self._tmp.name) / "docs"
        self.err = io.StringIO()

    def write(self, relative: str, text: str) -> Path:
        target = self.docs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def scan(self) -> int:
        return GUARD.main(["--docs-root", str(self.docs)], out=self.err)

    def test__money_mirror__exits_1_with_path_and_line(self) -> None:
        path = self.write("testing/running.md", "Прогон стоит $3.06.\n")

        self.assertEqual(self.scan(), 1)

        message = self.err.getvalue()
        self.assertIn("$3.06", message)
        self.assertIn(str(path), message)
        self.assertIn("строка 1", message)

    def test__repeats_near_score__exits_1(self) -> None:
        self.write("plugins/planner.md", "Кейс `x` | `1.00` | 3 из 3\n")

        self.assertEqual(self.scan(), 1)

    def test__repeats_without_score_nearby__passes(self) -> None:
        self.write("plugins/planner.md", "Повторили 3 из 3 раз, без оценки.\n")

        self.assertEqual(self.scan(), 0)

    def test__clean_docs__exits_0(self) -> None:
        self.write("plugins/planner.md", "Ограничение названо словами, без чисел.\n")

        self.assertEqual(self.scan(), 0)

    def test__former_reports_path_is_no_longer_excluded(self) -> None:
        # Каталог отчётов снят, и прежнее исключение вместе с ним: число,
        # положенное по этому пути, теперь такое же нарушение, как любое другое.
        self.write("reports/planner.md", "| Стоимость | `$3.22` |\n")

        self.assertEqual(self.scan(), 1)

    def test__missing_docs_root__exits_64(self) -> None:
        self.assertEqual(self.scan(), 64)


if __name__ == "__main__":
    unittest.main()
