"""Юнит-тесты стража полноты навигации docs/.

Детерминированный контракт: точное совпадение docs/**/*.md и project.nav
даёт код 0 без вывода; пропуск страницы, лишняя цель, повтор, недопустимый
путь, нестроковый элемент и неразбираемый вход дают код 1 с диагностикой
«проверка полноты навигации:»; неверный CLI-вызов даёт код 64. Тесты
работают на минимальных временных деревьях, а не на реальных страницах.
"""

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_docs_nav.py")
PREFIX = "проверка полноты навигации:"


def run_guard(root, *args):
    return subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


class TempTree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def make_tree(self, pages, nav):
        """Создать docs/ с файлами pages и zensical.toml с nav."""
        docs = self.root / "docs"
        docs.mkdir()
        for page in pages:
            path = docs / page
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# страница\n", encoding="utf-8")
        nav_lines = "\n".join(f'  "{item}",' for item in nav)
        (self.root / "zensical.toml").write_text(
            textwrap.dedent(f"""\
                [project]
                site_name = "проверка"
                docs_dir = "docs"

                nav = [
                {nav_lines}
                ]
            """),
            encoding="utf-8",
        )


class ExactMatch(TempTree):
    def test_match_returns_zero_without_output(self):
        self.make_tree(
            ["index.md", "plugins/planner.md"],
            ["index.md", "plugins/planner.md"],
        )
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


class Refusals(TempTree):
    def assert_refusal(self, result, *fragments):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(PREFIX, result.stderr)
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def test_missing_page(self):
        self.make_tree(["index.md", "plugins/planner.md"], ["index.md"])
        self.assert_refusal(run_guard(self.root), "plugins/planner.md")

    def test_extra_target(self):
        self.make_tree(["index.md"], ["index.md", "plugins/planner.md"])
        self.assert_refusal(run_guard(self.root), "plugins/planner.md")

    def test_duplicate_target(self):
        self.make_tree(["index.md"], ["index.md", "index.md"])
        self.assert_refusal(run_guard(self.root), "index.md")

    def test_absolute_path_rejected(self):
        self.make_tree(["index.md"], ["/etc/passwd"])
        self.assert_refusal(run_guard(self.root), "/etc/passwd")

    def test_escape_outside_docs_rejected(self):
        self.make_tree(["index.md"], ["../secrets.md"])
        self.assert_refusal(run_guard(self.root), "../secrets.md")

    def test_non_markdown_target_rejected(self):
        self.make_tree(["index.md"], ["image.png"])
        self.assert_refusal(run_guard(self.root), "image.png")

    def test_non_string_item_rejected(self):
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("#\n", encoding="utf-8")
        (self.root / "zensical.toml").write_text(
            "[project]\nnav = [1]\n", encoding="utf-8"
        )
        self.assert_refusal(run_guard(self.root), "nav")

    def test_missing_nav_rejected(self):
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("#\n", encoding="utf-8")
        (self.root / "zensical.toml").write_text(
            '[project]\nsite_name = "x"\n', encoding="utf-8"
        )
        self.assert_refusal(run_guard(self.root), "nav")

    def test_unparseable_toml_rejected(self):
        (self.root / "docs").mkdir()
        (self.root / "zensical.toml").write_text(
            "[project\nnav = ", encoding="utf-8"
        )
        self.assert_refusal(run_guard(self.root), "TOML")

    def test_missing_root_rejected(self):
        self.assert_refusal(
            run_guard(self.root / "нет-такого"), "zensical.toml"
        )


class Cli(unittest.TestCase):
    def test_unknown_argument_gives_64(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--nonsense"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 64)


if __name__ == "__main__":
    unittest.main()
