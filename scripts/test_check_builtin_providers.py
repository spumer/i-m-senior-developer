"""Проверки стража встроенных поставщиков матрицы способностей.

Каждый сценарий собирает минимальную временную копию с поставляемым
`product_state.py`. Поэтому проверяются код возврата и диагностика CLI, включая
вызов единственного владельца формата матрицы.
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).with_name("check_builtin_providers.py")
GUARD_SPEC = importlib.util.spec_from_file_location("check_builtin_providers", SCRIPT)
assert GUARD_SPEC is not None and GUARD_SPEC.loader is not None
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_SPEC.loader.exec_module(GUARD_MODULE)
PRODUCT_STATE_SOURCE = (
    REPOSITORY_ROOT
    / "plugins/planner/skills/product-discovery/assets/product_state.py"
)
PRODUCT_STATE_PATH = Path(
    "plugins/planner/skills/product-discovery/assets/product_state.py"
)
TEMPLATE_PATH = Path("plugins/planner/skills/planner/references/template-context.md")
CAPABILITY_HEADER = (
    "| Способность | Нужна для | Поставщик | Источник | Доступность | "
    "Покрытие | Основание | Ограничения | Приоритет |"
)
CAPABILITY_SEPARATOR = "|---|---|---|---|---|---|---|---|---|"


def capability_row(capability: str, provider: str, source: str) -> str:
    return (
        f"| {capability} | feature | {provider} | {source} | available | full | "
        "evidence.md | — | builtin |"
    )


def run_guard(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


class BuiltinProviderGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name)

    def make_root(self, rows: list[str], header: str = CAPABILITY_HEADER) -> None:
        helper = self.root / PRODUCT_STATE_PATH
        helper.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PRODUCT_STATE_SOURCE, helper)
        template = self.root / TEMPLATE_PATH
        template.parent.mkdir(parents=True, exist_ok=True)
        template.write_text(
            "\n".join(
                (
                    "## §9 Способности и поставщики",
                    "",
                    header,
                    CAPABILITY_SEPARATOR,
                    *rows,
                    "",
                )
            ),
            encoding="utf-8",
        )

    def add_agent(self, plugin: str, filename: str, declared_name: str) -> None:
        self.add_agent_frontmatter(plugin, filename, f"name: {declared_name}")

    def add_agent_frontmatter(self, plugin: str, filename: str, frontmatter: str) -> None:
        agent = self.root / "plugins" / plugin / "agents" / f"{filename}.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text(
            f"---\n{frontmatter}\n---\n",
            encoding="utf-8",
        )

    def replace_helper_output(self, output: str) -> None:
        self.replace_helper_source(f"print({output!r})\n")

    def replace_helper_source(self, source: str) -> None:
        helper = self.root / PRODUCT_STATE_PATH
        helper.write_text(source, encoding="utf-8")

    def test__invalid_helper_result__exits_1_instead_of_succeeding_silently(
        self,
    ) -> None:
        for output, diagnostic in (
            ("[]", "пустую матрицу способностей"),
            (
                '[{"capability": "problem_outcome_framing", '
                '"provider": "planner:product-baseline", "line": 5}]',
                "некорректную строку",
            ),
        ):
            with self.subTest(output=output):
                self.make_root([])
                self.replace_helper_output(output)

                result = run_guard(self.root)

                self.assertEqual(result.returncode, 1)
                self.assertIn(diagnostic, result.stderr)

    def test__helper__empty_stdout__exits_1_with_non_json_diagnostic(self) -> None:
        self.make_root([])
        self.replace_helper_source("")

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("подкоманда вернула не JSON", result.stderr)

    def test__main__missing_required_path__exits_64_with_path_diagnostic(self) -> None:
        for missing_path, diagnostic in (
            (PRODUCT_STATE_PATH, "нет помощника разбора"),
            (TEMPLATE_PATH, "нет поставляемого шаблона"),
        ):
            with self.subTest(missing_path=missing_path):
                self.make_root([])
                (self.root / missing_path).unlink()

                result = run_guard(self.root)

                self.assertEqual(result.returncode, 64)
                self.assertIn(diagnostic, result.stderr)
                self.assertIn(str(self.root / missing_path), result.stderr)

    def test__agent_frontmatter__accepted_name_notations__exit_0_without_output(self) -> None:
        for frontmatter, agent_name in (
            ('name: "product-baseline"', "product-baseline"),
            ("name: 'product-baseline'", "product-baseline"),
            ("name: product-baseline # comment", "product-baseline"),
            ('name: "product-baseline" # comment', "product-baseline"),
            ("name: 'product-baseline' # comment", "product-baseline"),
            ('"name": product-baseline', "product-baseline"),
            ("'name': product-baseline", "product-baseline"),
            ('name: "product-baseline#literal"', "product-baseline#literal"),
            ("name: 'product-baseline#literal'", "product-baseline#literal"),
        ):
            with self.subTest(frontmatter=frontmatter):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            f"planner:{agent_name}",
                            "builtin",
                        )
                    ]
                )
                self.add_agent_frontmatter("planner", agent_name, frontmatter)

                result = run_guard(self.root)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test__agent_frontmatter__unquoted_value_types__return_expected_exit_code(
        self,
    ) -> None:
        for case, agent_name, frontmatter, expected_code in (
            ("boolean", "true", "name: true", 1),
            ("number", "123", "name: 123", 1),
            ("flow_collection", "[product-baseline]", "name: [product-baseline]", 1),
            ("quoted_boolean", "true", "name: 'true'", 0),
            ("yaml12_string_yes", "yes", "name: yes", 0),
            ("yaml12_string_no", "no", "name: no", 0),
            ("yaml12_string_on", "on", "name: on", 0),
            ("yaml12_string_off", "off", "name: off", 0),
            ("boolean_prefix_name", "true-agent", "name: true-agent", 0),
        ):
            with self.subTest(case=case):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            f"planner:{agent_name}",
                            "builtin",
                        )
                    ]
                )
                self.add_agent_frontmatter("planner", agent_name, frontmatter)

                result = run_guard(self.root)

                self.assertEqual(result.returncode, expected_code, result.stderr)

    def test__agent_frontmatter__base_indent__returns_expected_exit_code(
        self,
    ) -> None:
        for case, agent_source, expected_code in (
            (
                "uniformly_indented_root",
                "---\n description: test\n name: product-baseline\n---\n",
                0,
            ),
            (
                "only_name_indented",
                "---\ndescription: test\n name: product-baseline\n---\n",
                1,
            ),
            (
                "only_name_indented_before_unindented_root",
                "---\n name: product-baseline\ndescription: test\n---\n",
                1,
            ),
            (
                "nested_metadata_name",
                "---\nmetadata:\n  name: product-baseline\n---\n",
                1,
            ),
            (
                "nested_metadata_name_below_indented_root",
                "---\n metadata:\n  name: product-baseline\n---\n",
                1,
            ),
        ):
            with self.subTest(case=case):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            "planner:product-baseline",
                            "builtin",
                        )
                    ]
                )
                agent = self.root / "plugins/planner/agents/product-baseline.md"
                agent.parent.mkdir(parents=True, exist_ok=True)
                agent.write_text(agent_source, encoding="utf-8")

                result = run_guard(self.root)

                self.assertEqual(result.returncode, expected_code, result.stderr)

    def test__agent_frontmatter__separator_and_bom_cases__returns_expected_exit_code(
        self,
    ) -> None:
        for case, agent_source, expected_code in (
            ("opening_separator_trailing_space", "--- \nname: product-baseline\n---\n", 0),
            ("opening_separator_trailing_tab", "---\t\nname: product-baseline\n---\n", 0),
            ("closing_separator_trailing_space", "---\nname: product-baseline\n--- \n", 0),
            ("closing_separator_trailing_tab", "---\nname: product-baseline\n---\t\n", 0),
            ("plain_key_without_separator_space", "---\nname:product-baseline\n---\n", 1),
            (
                "quoted_key_without_separator_space",
                '---\n"name":product-baseline\n---\n',
                1,
            ),
            (
                "double_quoted_key_with_comment_before_separator",
                '---\n"name" # comment: product-baseline\n---\n',
                1,
            ),
            (
                "single_quoted_key_with_comment_before_separator",
                "---\n'name' # comment: product-baseline\n---\n",
                1,
            ),
            (
                "utf8_bom_before_frontmatter",
                "﻿---\nname: product-baseline\n---\n",
                0,
            ),
            (
                "space_after_separator",
                "---\nname: product-baseline\n---\n",
                0,
            ),
            (
                "tab_after_separator",
                "---\nname:\tproduct-baseline\n---\n",
                0,
            ),
            ("no_break_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("ogham_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("en_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("em_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("figure_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("narrow_no_break_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("medium_mathematical_space_after_separator", "---\nname: product-baseline\n---\n", 1),
            ("ideographic_space_after_separator", "---\nname:　product-baseline\n---\n", 1),
            ("no_break_space_before_separator", "---\nname : product-baseline\n---\n", 1),
            ("no_break_space_before_plain_value", "---\nname:  product-baseline\n---\n", 1),
            ("no_break_space_before_inline_comment", "---\nname: product-baseline # comment\n---\n", 1),
            ("no_break_space_before_spaced_inline_comment", "---\nname: product-baseline  # comment\n---\n", 1),
            ("em_space_before_spaced_inline_comment", "---\nname: product-baseline  # comment\n---\n", 1),
            ("no_break_space_after_quoted_value", '---\nname: "product-baseline" \n---\n', 1),
        ):
            with self.subTest(case=case):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            "planner:product-baseline",
                            "builtin",
                        )
                    ]
                )
                agent = self.root / "plugins/planner/agents/product-baseline.md"
                agent.parent.mkdir(parents=True, exist_ok=True)
                agent.write_text(agent_source, encoding="utf-8")

                result = run_guard(self.root)

                self.assertEqual(result.returncode, expected_code, result.stderr)

    def test__frontmatter_pair__unicode_separator__returns_none(self) -> None:
        for case, whitespace in (
            ("no_break_space", " "),
            ("ogham_space", " "),
            ("en_space", " "),
            ("em_space", " "),
            ("figure_space", " "),
            ("narrow_no_break_space", " "),
            ("medium_mathematical_space", " "),
            ("ideographic_space", "　"),
        ):
            with self.subTest(case=case):
                self.assertIsNone(
                    GUARD_MODULE.frontmatter_pair(f"name:{whitespace}product-baseline")
                )

    def test__agent_frontmatter__reports_rejection_reason(self) -> None:
        for case, agent_source, diagnostic in (
            (
                "unsupported_opening_frame",
                "--- # comment\nname: product-baseline\n---\n",
                "рамка заголовка не в поддерживаемом виде",
            ),
            (
                "unsupported_closing_frame",
                "---\nname: product-baseline\n...\n",
                "рамка заголовка не в поддерживаемом виде",
            ),
            (
                "unsupported_closing_suffix",
                "---\nname: product-baseline\n---extra\n",
                "рамка заголовка не в поддерживаемом виде",
            ),
            (
                "unsupported_closing_dash",
                "---\nname: product-baseline\n----\n",
                "рамка заголовка не в поддерживаемом виде",
            ),
            (
                "unsupported_indented_closing",
                "---\nname: product-baseline\n ---\n",
                "рамка заголовка не в поддерживаемом виде",
            ),
            (
                "missing_name",
                "---\ndescription: test\n---\n",
                "поле «name» в рамке заголовка не объявлено",
            ),
            (
                "boolean_name_value",
                "---\nname: true\n---\n",
                "значение поля «name» вне принимаемого подмножества: «true»",
            ),
            (
                "numeric_name_value",
                "---\nname: 123\n---\n",
                "значение поля «name» вне принимаемого подмножества: «123»",
            ),
            (
                "repeated_name",
                "---\nname: product-baseline\nname: product-baseline\n---\n",
                "поле «name» объявлено больше одного раза",
            ),
            (
                "mismatched_name",
                "---\nname: another-name\n---\n",
                "ожидалось имя «product-baseline», указано «another-name»",
            ),
        ):
            with self.subTest(case=case):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            "planner:product-baseline",
                            "builtin",
                        )
                    ]
                )
                agent = self.root / "plugins/planner/agents/product-baseline.md"
                agent.parent.mkdir(parents=True, exist_ok=True)
                agent.write_text(agent_source, encoding="utf-8")

                result = run_guard(self.root)

                self.assertEqual(result.returncode, 1)
                self.assertIn(diagnostic, result.stderr)
                self.assertNotIn("указано не указано", result.stderr)

    def test__agent_name_case__reads_the_same_quoted_and_unquoted(self) -> None:
        for case, frontmatter, diagnostic in (
            (
                "mixed_case_unquoted",
                "name: Product-Baseline",
                "ожидалось имя «product-baseline», указано «Product-Baseline»",
            ),
            (
                "mixed_case_quoted",
                'name: "Product-Baseline"',
                "ожидалось имя «product-baseline», указано «Product-Baseline»",
            ),
            (
                "uppercase_boolean_unquoted",
                "name: TRUE",
                "значение поля «name» вне принимаемого подмножества: «TRUE»",
            ),
            (
                "capitalized_null_unquoted",
                "name: Null",
                "значение поля «name» вне принимаемого подмножества: «Null»",
            ),
        ):
            with self.subTest(case=case):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            "planner:product-baseline",
                            "builtin",
                        )
                    ]
                )
                self.add_agent_frontmatter("planner", "product-baseline", frontmatter)

                result = run_guard(self.root)

                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(diagnostic, result.stderr)

    def test__builtin_provider_plugin_case__returns_expected_cli_result(self) -> None:
        for provider_plugin, expected_code, diagnostic in (
            ("planner", 0, None),
            ("Planner", 1, "нет плагина «Planner»"),
        ):
            with self.subTest(provider_plugin=provider_plugin):
                self.make_root(
                    [
                        capability_row(
                            "problem_outcome_framing",
                            f"{provider_plugin}:product-baseline",
                            "builtin",
                        )
                    ]
                )
                self.add_agent("planner", "product-baseline", "product-baseline")

                result = run_guard(self.root)

                self.assertEqual(result.returncode, expected_code, result.stderr)
                if diagnostic is None:
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(result.stderr, "")
                else:
                    self.assertIn(diagnostic, result.stderr)
                    self.assertNotIn("нет файла агента", result.stderr)

    def test__missing_builtin_agent__exits_1_with_capability_provider_line_and_path(
        self,
    ) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")]
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("способность «problem_outcome_framing»", result.stderr)
        self.assertIn("поставщик «planner:product-baseline»", result.stderr)
        self.assertIn("строка 5", result.stderr)
        self.assertIn("plugins/planner/agents/product-baseline.md", result.stderr)
        self.assertIn("нет файла агента", result.stderr)

    def test__mismatched_agent_name__exits_1_with_expected_and_actual_names(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")]
        )
        self.add_agent("planner", "product-baseline", "another-name")

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("ожидалось имя «product-baseline»", result.stderr)
        self.assertIn("указано «another-name»", result.stderr)

    def test__nested_name_without_top_level_name__exits_1(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")]
        )
        agent = self.root / "plugins/planner/agents/product-baseline.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text(
            "---\ndescription: |\n  name: product-baseline\nmodel: sonnet\n---\n",
            encoding="utf-8",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("поле «name» в рамке заголовка не объявлено", result.stderr)

    def test__nested_name_with_top_level_name__exits_0_without_output(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")]
        )
        agent = self.root / "plugins/planner/agents/product-baseline.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text(
            "---\nname: product-baseline\ndescription: |\n  name: another-name\n"
            "model: sonnet\n---\n",
            encoding="utf-8",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test__block_scalar_delimiter__exits_0_without_output(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")]
        )
        agent = self.root / "plugins/planner/agents/product-baseline.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text(
            "---\nname: product-baseline\ndescription: |\n  --- вот так\n---\n",
            encoding="utf-8",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test__unclosed_frontmatter__reports_unsupported_frame(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")]
        )
        agent = self.root / "plugins/planner/agents/product-baseline.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text("---\nname: product-baseline\n", encoding="utf-8")

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("рамка заголовка не в поддерживаемом виде", result.stderr)

    def test__missing_plugin__exits_1_and_names_plugin_not_agent_file(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "missing-plugin:product-baseline", "builtin")]
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("нет плагина «missing-plugin»", result.stderr)
        self.assertNotIn("нет файла агента", result.stderr)
        self.assertIn(
            "plugins/missing-plugin/agents/product-baseline.md",
            result.stderr,
        )

    def test__external_provider_without_agent__exits_0_without_output(self) -> None:
        for source in ("project", "plugin"):
            with self.subTest(source=source):
                self.make_root(
                    [capability_row("problem_outcome_framing", "outside:provider", source)]
                )

                result = run_guard(self.root)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test__invalid_capability_table__exits_1_instead_of_succeeding_silently(
        self,
    ) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner:product-baseline", "builtin")],
            header="| Несовместимый заголовок |",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("не удалось разобрать матрицу способностей", result.stderr)
        self.assertIn("capability table columns", result.stderr)

    def test__invalid_root__exits_64_and_names_missing_plugins_directory(self) -> None:
        result = run_guard(self.root)

        self.assertEqual(result.returncode, 64)
        self.assertEqual(result.stdout, "")
        self.assertIn("нет каталога", result.stderr)
        self.assertIn(str(self.root / "plugins"), result.stderr)

    def test__malformed_builtin_provider__exits_1_with_address_diagnostic(self) -> None:
        self.make_root(
            [capability_row("problem_outcome_framing", "planner-product-baseline", "builtin")]
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("некорректный адрес", result.stderr)
        self.assertIn("planner-product-baseline", result.stderr)


if __name__ == "__main__":
    unittest.main()
