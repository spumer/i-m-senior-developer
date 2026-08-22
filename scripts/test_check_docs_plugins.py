"""Юнит-тесты стража соответствия docs/ манифестам плагинов.

Детерминированный контракт: чистое дерево — код 0 без вывода; строка с именем
плагина и неверным X.Y.Z в docs/**/*.md, колонка состава в каталоге, пропуск
или лишняя строка плагина — код 1 с диагностикой
«проверка соответствия документации манифестам:»; неверный вызов CLI,
включая несуществующий --root, — код 64. Тесты работают на минимальных
временных деревьях, а не на реальных страницах.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_docs_plugins.py")
PREFIX = "проверка соответствия документации манифестам:"

PLUGINS = {
    "alpha": "1.2.3",
    "beta": "0.4.0",
}


def run_guard(root):
    return subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


class TempTree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def make_plugins(self, plugins):
        for name, version in plugins.items():
            manifest_dir = self.root / "plugins" / name / ".claude-plugin"
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "plugin.json").write_text(
                json.dumps({"name": name, "version": version}),
                encoding="utf-8",
            )

    def write_docs(self, index_text, other_pages=None):
        docs = self.root / "docs"
        (docs / "plugins").mkdir(parents=True, exist_ok=True)
        (docs / "plugins" / "index.md").write_text(index_text, encoding="utf-8")
        for page, text in (other_pages or {}).items():
            path = docs / page
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


CLEAN_INDEX = """\
# Плагины

| Плагин | Что делает |
|---|---|
| [alpha](alpha.md) | планирование |
| [beta](beta.md) | ревью |

Версию показывает установка; состав каждого плагина перечислен на его
странице (см. [каталог](index.md)).
"""


class CleanTree(TempTree):
    def test_clean_tree_returns_zero_without_output(self):
        self.make_plugins(PLUGINS)
        self.write_docs(
            CLEAN_INDEX,
            {
                "plugins/alpha.md": "# alpha\n\nПлагин alpha поставляет команды.\n",
                "plugins/beta.md": "# beta\n",
            },
        )
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


class ForeignVersionSilence(TempTree):
    def test_foreign_product_version_next_to_plugin_name_gives_zero(self):
        self.make_plugins({"planner": "1.1.0"})
        self.write_docs(
            CLEAN_INDEX.replace(
                "| [alpha](alpha.md) | планирование |",
                "| [planner](planner.md) | планирование |",
            ).replace("| [beta](beta.md) | ревью |\n", ""),
            {
                "testing/reference.md": (
                    "# Справка\n\n"
                    "Для planner стоит ориентироваться минимум на "
                    "Claude Code `2.1.224`.\n"
                ),
                "plugins/planner.md": "# planner\n",
            },
        )
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")


class Refusals(TempTree):
    def assert_refusal(self, result, *fragments):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(PREFIX, result.stderr)
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def test_wrong_version_on_page(self):
        self.make_plugins(PLUGINS)
        self.write_docs(
            CLEAN_INDEX,
            {"plugins/alpha.md": "# alpha\n\nПлагин alpha версии 9.9.9 поставляет команды.\n"},
        )
        self.assert_refusal(
            run_guard(self.root),
            "docs/plugins/alpha.md:3:",
            "alpha",
            "версия",
            "9.9.9",
            "1.2.3",
        )

    def test_stale_version_in_catalog_row(self):
        self.make_plugins(PLUGINS)
        index = CLEAN_INDEX.replace(
            "| [alpha](alpha.md) | планирование |",
            "| [alpha](alpha.md) | 2.0.0 |",
        )
        self.write_docs(index)
        self.assert_refusal(
            run_guard(self.root),
            "docs/plugins/index.md:5:",
            "alpha",
            "версия",
            "2.0.0",
            "1.2.3",
        )

    def test_version_column_forbidden(self):
        self.make_plugins(PLUGINS)
        index = CLEAN_INDEX.replace(
            "| Плагин | Что делает |", "| Плагин | Версия | Что делает |"
        )
        self.write_docs(index)
        self.assert_refusal(run_guard(self.root), "Версия", "docs/plugins/index.md")

    def test_composition_columns_forbidden(self):
        self.make_plugins(PLUGINS)
        for column in ("Команды", "Скиллы", "Агенты", "Хуки"):
            with self.subTest(column=column):
                index = CLEAN_INDEX.replace(
                    "| Плагин | Что делает |", f"| Плагин | {column} | Что делает |"
                )
                self.write_docs(index)
                self.assert_refusal(run_guard(self.root), column)

    def test_missing_plugin_row(self):
        self.make_plugins(PLUGINS)
        index = CLEAN_INDEX.replace("| [beta](beta.md) | ревью |\n", "")
        self.write_docs(index)
        self.assert_refusal(run_guard(self.root), "beta")

    def test_extra_plugin_row(self):
        self.make_plugins(PLUGINS)
        index = CLEAN_INDEX.replace(
            "| [beta](beta.md) | ревью |",
            "| [beta](beta.md) | ревью |\n| [gamma](gamma.md) | лишний |",
        )
        self.write_docs(index)
        self.assert_refusal(run_guard(self.root), "gamma")


class Cli(unittest.TestCase):
    def test_unknown_argument_gives_64(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--nonsense"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 64)

    def test_missing_root_gives_64(self):
        result = run_guard(Path("/нет-такого-корня-для-проверки"))
        self.assertEqual(result.returncode, 64)
        self.assertIn(PREFIX, result.stderr)


if __name__ == "__main__":
    unittest.main()
