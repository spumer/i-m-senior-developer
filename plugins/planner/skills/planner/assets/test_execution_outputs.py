import unittest

from execution_outputs import extract_outputs


class ExtractOutputsTest(unittest.TestCase):
    def test_field_labels_and_inline_value(self) -> None:
        body = "\n".join(
            [
                "## Фаза 1",
                "",
                "- **Выход:** `plugins/planner/references/x.md`",
                "- **Outputs:** `docs/plugins/planner.md`",
                "- **Output:** `plugins/a/b.py`",
                "- **Выходы:** `plugins/c/d.md`",
                "- **Allowed outputs:** `plugins/e/f.md`",
                "- **Допустимые выходы:** `plugins/g/h.md`",
            ]
        )
        result = extract_outputs(body)
        self.assertEqual(
            result["paths"],
            [
                "plugins/planner/references/x.md",
                "docs/plugins/planner.md",
                "plugins/a/b.py",
                "plugins/c/d.md",
                "plugins/e/f.md",
                "plugins/g/h.md",
            ],
        )
        self.assertEqual(result["rejected"], {"bare_path": 0, "absolute_path": 0, "placeholder": 0})

    def test_nested_list_and_termination(self) -> None:
        body = "\n".join(
            [
                "## Фаза 1",
                "",
                "Выходы:",
                "",
                "- `plugins/one.md`",
                "- `plugins/two.md`",
                "",
                "## Фаза 2",
                "",
                "- **Вход:** `docs/input.md`",
                "- **Outputs:** `plugins/three.md`",
            ]
        )
        result = extract_outputs(body)
        self.assertEqual(result["paths"], ["plugins/one.md", "plugins/two.md", "plugins/three.md"])

    def test_root_file_and_directory_forms(self) -> None:
        body = "\n".join(
            [
                "## Фаза 1",
                "",
                "- **Outputs:**",
                "  - `./README.md`",
                "  - `plugins/planner/`",
            ]
        )
        result = extract_outputs(body)
        self.assertEqual(result["paths"], ["README.md", "plugins/planner/"])

    def test_deduplication_keeps_first_order(self) -> None:
        body = "\n".join(
            [
                "## Фаза 1",
                "",
                "- **Outputs:** `plugins/a.md`, `plugins/b.md`",
                "",
                "## Фаза 2",
                "",
                "- **Outputs:** `plugins/b.md`, `./plugins/a.md`",
            ]
        )
        result = extract_outputs(body)
        self.assertEqual(result["paths"], ["plugins/a.md", "plugins/b.md"])

    def test_garbage_candidates_rejected_without_paths(self) -> None:
        body = "\n".join(
            [
                "## Фаза 1",
                "",
                "- **Outputs:**",
                "  - `ARCHITECTURE.md`",
                "  - `plugin.json`",
                "  - `SKILL.md`",
                "  - `/Users/alice/tasks/some-task.md`",
                "  - `~/notes/file.md`",
                "  - `../../other/file.md`",
                "  - `plugins/*/wild.md`",
                "  - `<выход>`",
            ]
        )
        result = extract_outputs(body)
        self.assertEqual(result["paths"], [])
        self.assertEqual(result["rejected"], {"bare_path": 3, "absolute_path": 2, "placeholder": 3})

    def test_non_output_context_is_ignored(self) -> None:
        body = "\n".join(
            [
                "## Фаза 1",
                "",
                "- **Вход:** `docs/plan.md`",
                "- **Проверка:** `python3 plugins/run.py`",
                "",
                "Проза с путём `plugins/mentioned/in-prose.md` игнорируется.",
                "",
                "### Заголовок",
                "",
                "- **Outputs:** `plugins/real.md`",
            ]
        )
        result = extract_outputs(body)
        self.assertEqual(result["paths"], ["plugins/real.md"])

    def test_empty_body(self) -> None:
        result = extract_outputs("# План\n\nТекст без полей.\n")
        self.assertEqual(result["paths"], [])
        self.assertEqual(result["rejected"], {"bare_path": 0, "absolute_path": 0, "placeholder": 0})


if __name__ == "__main__":
    unittest.main()
