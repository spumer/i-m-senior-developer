import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, TypeAlias, cast
import unittest
from unittest import mock

import product_state


SCRIPT = Path(__file__).with_name("product_state.py")
_OMIT = object()


def body_hash(body: str) -> str:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode()).hexdigest()


def product_document(kind: str, **overrides: object) -> str:
    body = f"# {kind.title()}\n"
    metadata_by_kind: dict[str, dict[str, object]] = {
        "idea": {"stage": "exploring", "outcome": "open"},
        "epic": {
            "stage": "shaping",
            "origin": {
                "path": "../../ideas/IDEA-0001-provider-routing.md",
                "version": 1,
                "content_sha256": "2" * 64,
            },
        },
        "roadmap": {
            "state": "active",
            "epic": {
                "path": "./EPIC.md",
                "version": 1,
                "content_sha256": "2" * 64,
            },
        },
        "feature": {
            "readiness": "ready",
            "parent": {
                "path": "../../epics/EPIC-0001-provider-routing/EPIC.md",
                "version": 1,
                "content_sha256": "2" * 64,
            },
        },
    }
    metadata: dict[str, object] = {
        "plan_type": kind,
        "version": 1,
        "status": "current",
        "content_sha256": body_hash(body),
        **metadata_by_kind[kind],
    }
    for field, value in overrides.items():
        if value is _OMIT:
            metadata.pop(field, None)
        else:
            metadata[field] = value
    return product_state.render_document(metadata, body)


RowOverrides: TypeAlias = dict[str, dict[str, str]]
ExtraRows: TypeAlias = tuple[tuple[str, dict[str, str]], ...]


_CAPABILITY_HEADERS = (
    "Способность",
    "Нужна для",
    "Поставщик",
    "Источник",
    "Доступность",
    "Покрытие",
    "Основание",
    "Ограничения",
    "Приоритет",
)


def capability_row(
    provider: str,
    *,
    capability: str = "product_synthesis",
    required_for: str = "epic",
    availability: str = "available",
    coverage: str = "full",
    priority: str = "plugin",
    evidence: str = "discovery/provider.md",
    limitations: str = "—",
) -> dict[str, str]:
    return {
        "capability": capability,
        "required_for": required_for,
        "provider": provider,
        "source": "discovered component",
        "availability": availability,
        "coverage": coverage,
        "evidence": evidence,
        "limitations": limitations,
        "priority": priority,
    }


def capability_context(
    *,
    row_overrides: RowOverrides | None = None,
    extra_rows: ExtraRows = (),
    headers: tuple[str, ...] = _CAPABILITY_HEADERS,
) -> str:
    rows = [
        (
            "problem.external",
            {
                "capability": "problem_outcome_framing",
                "required_for": "idea, epic, feature",
                "provider": "product",
                "source": "project agent",
                "availability": "available",
                "coverage": "full",
                "evidence": ".claude/agents/product.md",
                "limitations": "—",
                "priority": "project",
            },
        ),
        (
            "problem.builtin",
            {
                "capability": "problem_outcome_framing",
                "required_for": "idea, epic, feature",
                "provider": "planner:product-baseline",
                "source": "planner plugin",
                "availability": "available",
                "coverage": "partial",
                "evidence": "plugins/planner/skills/product-baseline/SKILL.md",
                "limitations": "нет данных о пользователях",
                "priority": "builtin",
            },
        ),
        (
            "synthesis.external",
            {
                "capability": "product_synthesis",
                "required_for": "idea, epic, roadmap",
                "provider": "product",
                "source": "project agent",
                "availability": "available",
                "coverage": "full",
                "evidence": ".claude/agents/product.md",
                "limitations": "—",
                "priority": "project",
            },
        ),
        (
            "synthesis.builtin",
            {
                "capability": "product_synthesis",
                "required_for": "idea, epic, roadmap",
                "provider": "planner:product-baseline",
                "source": "planner plugin",
                "availability": "available",
                "coverage": "partial",
                "evidence": "plugins/planner/skills/product-baseline/SKILL.md",
                "limitations": "нет независимой многоролевой проверки",
                "priority": "builtin",
            },
        ),
        (
            "dialogue.external",
            {
                "capability": "decision_dialogue",
                "required_for": "idea, epic, roadmap, feature",
                "provider": "product",
                "source": "project agent",
                "availability": "available",
                "coverage": "full",
                "evidence": ".claude/agents/product.md",
                "limitations": "—",
                "priority": "project",
            },
        ),
        (
            "dialogue.builtin",
            {
                "capability": "decision_dialogue",
                "required_for": "idea, epic, roadmap, feature",
                "provider": "planner:product-baseline",
                "source": "planner plugin",
                "availability": "available",
                "coverage": "partial",
                "evidence": "plugins/planner/skills/product-baseline/SKILL.md",
                "limitations": "нет подтверждения гипотезы",
                "priority": "builtin",
            },
        ),
    ]
    overrides = row_overrides or {}
    rendered_rows: list[dict[str, str]] = []
    for name, original in (*rows, *extra_rows):
        row = dict(original)
        row.update(overrides.get(name, {}))
        rendered_rows.append(row)
    fields = (
        "capability",
        "required_for",
        "provider",
        "source",
        "availability",
        "coverage",
        "evidence",
        "limitations",
        "priority",
    )
    table = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join('---' for _ in headers)} |",
    ]
    table.extend(
        f"| {' | '.join(row[field] for field in fields)} |" for row in rendered_rows
    )
    return "\n".join(
        (
            "# Planner context",
            "",
            "## §9 Способности и поставщики",
            "",
            *table,
            "",
            "## §10 Следующий раздел",
            "",
        )
    )


def make_symbolic_link(node: Path, source: Path) -> None:
    source.write_text("# Draft\n")
    node.symlink_to(source)


def make_hard_link(node: Path, source: Path) -> None:
    source.write_text("# Draft\n")
    os.link(source, node)


def make_named_pipe(node: Path, source: Path) -> None:
    os.mkfifo(node)


def make_directory(node: Path, source: Path) -> None:
    node.mkdir()


_UNSUITABLE_FILE_NODES = (
    ("symbolic link", make_symbolic_link, "symbolic link"),
    ("hard link", make_hard_link, "hard link"),
    ("directory", make_directory, "regular file"),
    ("named pipe", make_named_pipe, "regular file"),
)


class ProductStateCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ideas = self.root / "ideas"
        self.epics = self.root / "epics"
        self.features = self.root / "features"
        self.ideas.mkdir()
        self.epics.mkdir()
        self.features.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def idea_path(self, slug: str = "provider-routing") -> Path:
        return self.ideas / f"IDEA-0001-{slug}.md"

    def product_path(self, kind: str) -> Path:
        paths = {
            "idea": self.idea_path(),
            "epic": self.epics / "EPIC-0001-provider-routing" / "EPIC.md",
            "roadmap": self.epics / "EPIC-0001-provider-routing" / "ROADMAP.md",
            "feature": product_state.allocation_target(
                "feature", self.features, 1, "provider-routing"
            )
            / "README.md",
        }
        path = paths[kind]
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def prepared_body(self, target: Path, body: str) -> Path:
        prepared = target.with_name(f"{target.name}.prepared")
        prepared.write_text(body)
        return prepared

    def sync_product(
        self,
        kind: str,
        path: Path,
        body: str,
        semantic_change: str = "yes",
        parent: Path | None = None,
        **fields: str,
    ) -> subprocess.CompletedProcess[str]:
        prepared = self.prepared_body(path, body)
        arguments = [
            "sync",
            kind,
            str(path),
            "--body-file",
            str(prepared),
            "--semantic-change",
            semantic_change,
        ]
        if parent is not None:
            arguments.extend(("--parent", str(parent)))
        for field, value in fields.items():
            arguments.extend((f"--{field.replace('_', '-')}", value))
        result = self.run_cli(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(prepared.exists())
        return result

    def sync_idea(
        self, body: str = "# Idea\n", semantic_change: str = "yes"
    ) -> subprocess.CompletedProcess[str]:
        return self.sync_product(
            "idea",
            self.idea_path(),
            body,
            semantic_change,
            stage="exploring",
            outcome="open",
        )

    def allocate_product(self, kind: str, root: Path, slug: str) -> Path:
        result = self.run_cli(
            "allocate", kind, "--root", str(root), "--slug", slug
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(json.loads(result.stdout)["path"])

    def inspect_product(self, path: Path) -> dict[str, Any]:
        result = self.run_cli("inspect", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        return cast(dict[str, Any], json.loads(result.stdout))

    def assert_product_document(
        self,
        path: Path,
        expected_metadata: dict[str, object],
        expected_body: str,
    ) -> product_state.ProductDocument:
        document = product_state.read_document(path)
        self.assertTrue(document.has_frontmatter)
        self.assertEqual(document.metadata, expected_metadata)
        self.assertEqual(document.body, expected_body)
        return document

    def response_draft(self, kind: str, **overrides: object) -> Path:
        draft: dict[str, object] = {
            "problem": "владелец теряет сохранённые элементы после массового удаления",
            "outcome": "удалённый элемент возвращается за один шаг",
            "actors": "владелец элемента",
            "scope_in": "возврат последнего удалённого элемента",
            "scope_out": "полная история версий",
            "assumptions": ["потеря происходит при массовом удалении"],
            "unknowns": ["как часто владелец замечает потерю"],
            "limitations": ["нет данных о пользователях"],
        }
        by_kind: dict[str, dict[str, object]] = {
            "idea": {"recommended_outcome": "feature"},
            "epic": {"candidate_slices": ["возврат последнего элемента"]},
            "roadmap": {"candidate_slices": ["возврат последнего элемента"]},
            "feature": {},
        }
        draft.update(by_kind.get(kind, {}))
        for field, value in overrides.items():
            if value is _OMIT:
                draft.pop(field, None)
            else:
                draft[field] = value
        path = self.root / "provider-response.json"
        path.write_text(json.dumps(draft, ensure_ascii=False))
        return path

    def check_response(
        self, kind: str, path: Path
    ) -> subprocess.CompletedProcess[str]:
        return self.run_cli("check-response", str(path), "--for", kind)

    def context_path(
        self,
        *,
        row_overrides: RowOverrides | None = None,
        extra_rows: ExtraRows = (),
        headers: tuple[str, ...] = _CAPABILITY_HEADERS,
    ) -> Path:
        path = self.root / "planner-context.md"
        path.write_text(
            capability_context(
                row_overrides=row_overrides, extra_rows=extra_rows, headers=headers
            )
        )
        return path

    def test__parse_capabilities__full_valid_matrix__returns_normalized_rows(
        self,
    ) -> None:
        context = self.context_path()

        result = self.run_cli("parse-capabilities", str(context))

        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            rows[0],
            {
                "availability": "available",
                "capability": "problem_outcome_framing",
                "coverage": "full",
                "evidence": ".claude/agents/product.md",
                "limitations": "—",
                "priority": "project",
                "provider": "product",
                "required_for": ["idea", "epic", "feature"],
                "source": "project agent",
            },
        )

    def test__parse_capabilities__empty_evidence__normalizes_coverage_to_unknown(
        self,
    ) -> None:
        context = self.context_path(
            row_overrides={"problem.external": {"evidence": ""}}
        )

        result = self.run_cli("parse-capabilities", str(context))

        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)[0]
        self.assertEqual(row["evidence"], "")
        self.assertEqual(row["coverage"], "unknown")

    def test__parse_capabilities__unknown_closed_value__returns_invalid_with_line(
        self,
    ) -> None:
        cases = (
            ("availability", {"availability": "sometimes"}, "sometimes"),
            ("coverage", {"coverage": "broad"}, "broad"),
            ("priority", {"priority": "workspace"}, "workspace"),
            (
                "required-for-kind",
                {"required_for": "idea, initiative"},
                "initiative",
            ),
        )

        for case_name, override, invalid_value in cases:
            with self.subTest(case=case_name):
                context = self.context_path(
                    row_overrides={"problem.external": override}
                )

                result = self.run_cli("parse-capabilities", str(context))

                self.assertEqual(result.returncode, 3)
                self.assertIn("line 7", result.stderr)
                self.assertIn(invalid_value, result.stderr)

    def test__parse_capabilities__wrong_column_order__returns_invalid(self) -> None:
        headers = (
            _CAPABILITY_HEADERS[1],
            _CAPABILITY_HEADERS[0],
            *_CAPABILITY_HEADERS[2:],
        )
        context = self.context_path(headers=headers)

        result = self.run_cli("parse-capabilities", str(context))

        self.assertEqual(result.returncode, 3)
        self.assertIn("line 5", result.stderr)
        self.assertIn("columns", result.stderr)

    def test__route__external_full_and_builtin_fallback__selects_external_with_trace(
        self,
    ) -> None:
        context = self.context_path()

        result = self.run_cli("route", str(context), "--for", "epic")

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(trace["for"], "epic")
        self.assertEqual(
            trace["required"],
            ["problem_outcome_framing", "product_synthesis", "decision_dialogue"],
        )
        self.assertEqual(trace["fallback_used"], False)
        self.assertEqual(trace["limitations"], [])
        self.assertEqual(trace["writer"], "planner")
        external = next(
            candidate
            for candidate in trace["candidates"]
            if candidate["capability"] == "product_synthesis"
            and candidate["provider"] == "product"
        )
        builtin = next(
            candidate
            for candidate in trace["candidates"]
            if candidate["capability"] == "product_synthesis"
            and candidate["provider"] == "planner:product-baseline"
        )
        self.assertEqual(
            external,
            {
                "availability": "available",
                "capability": "product_synthesis",
                "coverage": "full",
                "evidence": ".claude/agents/product.md",
                "priority": "project",
                "provider": "product",
                "rejected": None,
                "selected": True,
            },
        )
        self.assertEqual(
            builtin,
            {
                "availability": "available",
                "capability": "product_synthesis",
                "coverage": "partial",
                "evidence": "plugins/planner/skills/product-baseline/SKILL.md",
                "priority": "builtin",
                "provider": "planner:product-baseline",
                "rejected": "higher-priority-full-provider",
                "selected": False,
            },
        )

    def test__route__capability_evidence_date__returns_context_scan_date(self) -> None:
        cases: tuple[tuple[str, RowOverrides, str | None], ...] = (
            (
                "dated-evidence",
                {
                    "problem.external": {
                        "evidence": ".claude/agents/product.md "
                        "<!-- auto-added 2026-08-14 -->"
                    },
                    "synthesis.external": {
                        "evidence": ".claude/agents/product.md "
                        "<!-- stale, last seen 2026-08-16 -->"
                    },
                },
                "2026-08-16",
            ),
            ("undated-evidence", {}, None),
        )

        for case_name, overrides, expected_date in cases:
            with self.subTest(case=case_name):
                context = self.context_path(row_overrides=overrides)

                result = self.run_cli("route", str(context), "--for", "epic")

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(result.stdout)["context_scanned_at"], expected_date
                )

    def test__route__candidate_rank_data__uses_coverage_then_priority(self) -> None:
        cases: tuple[tuple[str, RowOverrides, ExtraRows, str, str], ...] = (
            (
                "project-full-over-configured-partial",
                {},
                (
                    (
                        "synthesis.configured",
                        capability_row(
                            "configured-product",
                            coverage="partial",
                            priority="configured",
                        ),
                    ),
                ),
                "product",
                "configured-product",
            ),
            (
                "plugin-full-over-project-partial",
                {"synthesis.external": {"coverage": "partial"}},
                (
                    (
                        "synthesis.plugin",
                        capability_row("plugin-product", priority="plugin"),
                    ),
                ),
                "plugin-product",
                "product",
            ),
            (
                "builtin-full-over-plugin-partial",
                {
                    "synthesis.external": {
                        "coverage": "partial",
                        "priority": "plugin",
                    },
                    "synthesis.builtin": {"coverage": "full"},
                },
                (),
                "planner:product-baseline",
                "product",
            ),
            (
                "same-priority-full-over-partial",
                {"synthesis.external": {"coverage": "partial"}},
                (
                    (
                        "synthesis.project-full",
                        capability_row("project-full", priority="project"),
                    ),
                ),
                "project-full",
                "product",
            ),
        )

        for (
            case_name,
            overrides,
            extra_rows,
            expected_provider,
            displaced_provider,
        ) in cases:
            with self.subTest(case=case_name):
                context = self.context_path(
                    row_overrides=overrides, extra_rows=extra_rows
                )

                result = self.run_cli("route", str(context), "--for", "epic")

                self.assertEqual(result.returncode, 0, result.stderr)
                trace = json.loads(result.stdout)
                selected = [
                    candidate
                    for candidate in trace["candidates"]
                    if candidate["capability"] == "product_synthesis"
                    and candidate["selected"]
                ]
                self.assertEqual(
                    [candidate["provider"] for candidate in selected],
                    [expected_provider],
                )
                self.assertEqual(
                    trace["fallback_used"],
                    expected_provider == "planner:product-baseline",
                )
                displaced = next(
                    candidate
                    for candidate in trace["candidates"]
                    if candidate["capability"] == "product_synthesis"
                    and candidate["provider"] == displaced_provider
                )
                self.assertEqual(displaced["rejected"], "higher-coverage-provider")

    def test__route__available_pinned_provider__selects_it_for_every_capability(
        self,
    ) -> None:
        context = self.context_path()

        result = self.run_cli(
            "route",
            str(context),
            "--for",
            "epic",
            "--pin",
            "planner:product-baseline",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        selected = [
            candidate for candidate in trace["candidates"] if candidate["selected"]
        ]
        self.assertEqual(
            {candidate["provider"] for candidate in selected},
            {"planner:product-baseline"},
        )
        self.assertEqual(
            {candidate["capability"] for candidate in selected}, set(trace["required"])
        )
        self.assertEqual(trace["fallback_used"], True)
        self.assertEqual(
            trace["limitations"],
            [
                "нет данных о пользователях",
                "нет независимой многоролевой проверки",
                "нет подтверждения гипотезы",
            ],
        )

    def test__route__pinned_provider_absent_or_unavailable__stops_without_fallback(
        self,
    ) -> None:
        cases: tuple[tuple[str, str, RowOverrides, str], ...] = (
            ("absent", "missing-provider", {}, "missing-provider"),
            (
                "stale",
                "product",
                {"synthesis.external": {"availability": "stale"}},
                "stale",
            ),
            (
                "error",
                "product",
                {"synthesis.external": {"availability": "error"}},
                "error",
            ),
            (
                "not-surfaced",
                "product",
                {"synthesis.external": {"availability": "not-surfaced"}},
                "not-surfaced",
            ),
        )

        for case_name, pin, overrides, expected_message in cases:
            with self.subTest(case=case_name):
                context = self.context_path(row_overrides=overrides)

                result = self.run_cli(
                    "route", str(context), "--for", "epic", "--pin", pin
                )

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(pin, result.stderr)
                self.assertIn(expected_message, result.stderr)

    def test__route__required_capability_not_covered__returns_invalid(self) -> None:
        cases = (
            ("availability-stale", "stale", "full", "discovery/provider.md"),
            ("availability-error", "error", "full", "discovery/provider.md"),
            (
                "availability-not-surfaced",
                "not-surfaced",
                "full",
                "discovery/provider.md",
            ),
            ("coverage-none", "available", "none", "discovery/provider.md"),
            ("coverage-unknown", "available", "unknown", "discovery/provider.md"),
            ("empty-evidence", "available", "full", ""),
        )

        for case_name, availability, coverage, evidence in cases:
            with self.subTest(case=case_name):
                context = self.context_path(
                    extra_rows=(
                        (
                            "uncovered",
                            capability_row(
                                "uncovered-provider",
                                capability="uncovered_capability",
                                availability=availability,
                                coverage=coverage,
                                evidence=evidence,
                            ),
                        ),
                    )
                )

                result = self.run_cli("route", str(context), "--for", "epic")

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn("uncovered_capability", result.stderr)
                self.assertIn("not covered", result.stderr)

    def test__route__missing_base_capability_row__returns_invalid(self) -> None:
        cases: tuple[tuple[str, RowOverrides, str], ...] = (
            (
                "idea",
                {
                    "problem.external": {"required_for": "epic, feature"},
                    "problem.builtin": {"required_for": "epic, feature"},
                },
                "problem_outcome_framing",
            ),
            (
                "epic",
                {
                    "synthesis.external": {"required_for": "idea, roadmap"},
                    "synthesis.builtin": {"required_for": "idea, roadmap"},
                },
                "product_synthesis",
            ),
            (
                "roadmap",
                {
                    "dialogue.external": {"required_for": "idea, epic, feature"},
                    "dialogue.builtin": {"required_for": "idea, epic, feature"},
                },
                "decision_dialogue",
            ),
            (
                "feature",
                {
                    "problem.external": {"required_for": "idea, epic"},
                    "problem.builtin": {"required_for": "idea, epic"},
                },
                "problem_outcome_framing",
            ),
        )

        for kind, overrides, missing_capability in cases:
            with self.subTest(kind=kind, capability=missing_capability):
                context = self.context_path(row_overrides=overrides)

                result = self.run_cli("route", str(context), "--for", kind)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(missing_capability, result.stderr)
                self.assertIn("not covered", result.stderr)

    def test__route__different_providers_cover_required_capabilities__composes_them(
        self,
    ) -> None:
        context = self.context_path(
            row_overrides={
                "synthesis.external": {
                    "provider": "strategy",
                    "evidence": ".claude/agents/strategy.md",
                    "limitations": "требуется проверка рыночных данных",
                }
            }
        )

        result = self.run_cli("route", str(context), "--for", "epic")

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        selected = {
            candidate["capability"]: candidate["provider"]
            for candidate in trace["candidates"]
            if candidate["selected"]
        }
        self.assertEqual(
            selected,
            {
                "problem_outcome_framing": "product",
                "product_synthesis": "strategy",
                "decision_dialogue": "product",
            },
        )
        self.assertEqual(trace["fallback_used"], False)
        self.assertEqual(trace["limitations"], ["требуется проверка рыночных данных"])

    def test__route__unknown_product_kind__returns_usage_error(self) -> None:
        context = self.context_path()

        result = self.run_cli("route", str(context), "--for", "initiative")

        self.assertEqual(result.returncode, 64)
        self.assertIn("invalid choice", result.stderr)
        self.assertEqual(result.stdout, "")

    def test__check_response__complete_draft_for_each_kind__accepts_with_limitations(
        self,
    ) -> None:
        for kind in ("idea", "epic", "roadmap", "feature"):
            with self.subTest(kind=kind):
                draft = self.response_draft(kind)

                result = self.check_response(kind, draft)

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["accepted"], True)
                self.assertEqual(payload["for"], kind)
                self.assertEqual(
                    payload["limitations"], ["нет данных о пользователях"]
                )

    def test__check_response__missing_or_empty_required_field__returns_invalid(
        self,
    ) -> None:
        cases = (
            ("problem absent", {"problem": _OMIT}, "problem"),
            ("problem blank", {"problem": "   "}, "problem"),
            ("outcome absent", {"outcome": _OMIT}, "outcome"),
            ("outcome blank", {"outcome": ""}, "outcome"),
            ("limitations absent", {"limitations": _OMIT}, "limitations"),
            ("limitations empty list", {"limitations": []}, "limitations"),
            ("limitations blank item", {"limitations": ["  "]}, "limitations"),
        )

        for name, overrides, expected_field in cases:
            with self.subTest(case=name):
                draft = self.response_draft("idea", **overrides)

                result = self.check_response("idea", draft)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(expected_field, result.stderr)

    def test__check_response__field_from_another_kind__returns_invalid(self) -> None:
        cases = (
            ("epic", {"recommended_outcome": "feature"}, "recommended_outcome"),
            ("roadmap", {"recommended_outcome": "epic"}, "recommended_outcome"),
            ("idea", {"candidate_slices": ["одна фича"]}, "candidate_slices"),
            ("feature", {"candidate_slices": ["одна фича"]}, "candidate_slices"),
        )

        for kind, overrides, unexpected_field in cases:
            with self.subTest(kind=kind, field=unexpected_field):
                draft = self.response_draft(kind, **overrides)

                result = self.check_response(kind, draft)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(unexpected_field, result.stderr)

    def test__check_response__unknown_field_or_wrong_type__returns_invalid(
        self,
    ) -> None:
        cases = (
            ("unknown field", {"confidence": "high"}, "confidence"),
            ("scalar as list", {"problem": ["две части"]}, "problem"),
            ("list as scalar", {"limitations": "одно ограничение"}, "limitations"),
            ("list item not text", {"unknowns": [42]}, "unknowns"),
        )

        for name, overrides, expected_field in cases:
            with self.subTest(case=name):
                draft = self.response_draft("idea", **overrides)

                result = self.check_response("idea", draft)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(expected_field, result.stderr)

    def test__check_response__unusable_input__returns_invalid(self) -> None:
        malformed = self.root / "malformed.json"
        malformed.write_text("problem: нет\n")
        sequence = self.root / "sequence.json"
        sequence.write_text(json.dumps(["problem"]))
        cases = (
            ("not json", malformed),
            ("json array", sequence),
            ("missing file", self.root / "absent.json"),
        )

        for name, path in cases:
            with self.subTest(case=name):
                result = self.check_response("idea", path)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertNotEqual(result.stderr, "")

    def test__check_response__unknown_product_kind__returns_usage_error(self) -> None:
        draft = self.response_draft("idea")

        result = self.check_response("initiative", draft)

        self.assertEqual(result.returncode, 64)
        self.assertIn("invalid choice", result.stderr)
        self.assertEqual(result.stdout, "")

    def test__inspect__valid_idea_frontmatter__returns_parsed_state(self) -> None:
        body = "# Idea\n"
        idea = self.idea_path()
        idea.write_text(
            "---\n"
            "plan_type: idea\n"
            "version: 2\n"
            "status: current\n"
            f"content_sha256: {body_hash(body)}\n"
            "stage: resolved\n"
            "outcome: research\n"
            "---\n"
            f"{body}"
        )

        result = self.run_cli("inspect", str(idea))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "content_sha256": body_hash(body),
                "outcome": "research",
                "path": str(idea.resolve()),
                "plan_type": "idea",
                "stage": "resolved",
                "status": "current",
                "version": 2,
            },
        )

    def test__inspect_and_check__document_without_frontmatter__returns_version_zero_without_mutation(
        self,
    ) -> None:
        body = "# Legacy idea\n\nNo supported frontmatter.\n"
        legacy = self.idea_path("legacy")
        legacy.write_text(body)
        original = legacy.read_bytes()
        expected = {
            "content_sha256": body_hash(body),
            "path": str(legacy.resolve()),
            "plan_type": None,
            "status": "current",
            "version": 0,
        }

        for command in ("inspect", "check"):
            with self.subTest(command=command):
                result = self.run_cli(command, str(legacy))

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), expected)
                self.assertEqual(legacy.read_bytes(), original)

    def test__inspect__unknown_frontmatter_field__returns_invalid(self) -> None:
        idea = self.idea_path()
        idea.write_text(
            "---\n"
            "plan_type: idea\n"
            "version: 1\n"
            "status: current\n"
            f"content_sha256: {'1' * 64}\n"
            "stage: exploring\n"
            "outcome: open\n"
            "invented: value\n"
            "---\n"
            "# Idea\n"
        )

        result = self.run_cli("inspect", str(idea))

        self.assertEqual(result.returncode, 3)
        self.assertIn("unsupported frontmatter fields", result.stderr)
        self.assertIn("invented", result.stderr)

    def test__inspect__unsupported_frontmatter_indentation__returns_invalid(
        self,
    ) -> None:
        epic = self.epics / "EPIC-0001-provider-routing" / "EPIC.md"
        epic.parent.mkdir()
        cases = (
            ("one-space", " "),
            ("tab", "\t"),
            ("four-spaces", "    "),
        )

        for case_name, indentation in cases:
            with self.subTest(case=case_name):
                epic.write_text(
                    "---\n"
                    "plan_type: epic\n"
                    "version: 1\n"
                    "status: current\n"
                    f"content_sha256: {'1' * 64}\n"
                    "stage: shaping\n"
                    "origin:\n"
                    f'{indentation}path: "../../ideas/IDEA-0001-provider-routing.md"\n'
                    "  version: 1\n"
                    f"  content_sha256: {'2' * 64}\n"
                    "---\n"
                    "# Epic\n"
                )

                result = self.run_cli("inspect", str(epic))

                self.assertEqual(result.returncode, 3)
                self.assertIn("two-space nesting", result.stderr)

    def test__inspect__invalid_value_or_relationship__returns_invalid(self) -> None:
        cases = (
            (
                "idea.stage.unknown",
                "idea",
                {"stage": "guessed"},
                "stage",
                "stage must be one of",
            ),
            (
                "idea.outcome.unknown",
                "idea",
                {"outcome": "guessed"},
                "outcome",
                "outcome must be one of",
            ),
            (
                "epic.stage.unknown",
                "epic",
                {"stage": "guessed"},
                "stage",
                "stage must be one of",
            ),
            (
                "roadmap.state.unknown",
                "roadmap",
                {"state": "guessed"},
                "state",
                "state must be one of",
            ),
            (
                "feature.readiness.unknown",
                "feature",
                {"readiness": "guessed"},
                "readiness",
                "readiness must be one of",
            ),
            (
                "idea.outcome.exploring-requires-open",
                "idea",
                {"outcome": "research"},
                "outcome",
                "exploring idea requires outcome open",
            ),
            (
                "idea.target.exploring-forbids-target",
                "idea",
                {"target": "../features/sample/README.md"},
                "target",
                "exploring idea must not have target",
            ),
            (
                "idea.outcome.resolved-forbids-open",
                "idea",
                {"stage": "resolved"},
                "outcome",
                "resolved idea cannot have outcome open",
            ),
            (
                "idea.target.feature-outcome-requires-target",
                "idea",
                {"stage": "resolved", "outcome": "feature"},
                "target",
                "outcome feature requires target",
            ),
            (
                "idea.target.epic-outcome-requires-target",
                "idea",
                {"stage": "resolved", "outcome": "epic"},
                "target",
                "outcome epic requires target",
            ),
            (
                "idea.target.duplicate-outcome-requires-target",
                "idea",
                {"stage": "resolved", "outcome": "duplicate"},
                "target",
                "outcome duplicate requires target",
            ),
            (
                "roadmap.epic.required",
                "roadmap",
                {"epic": _OMIT},
                "epic",
                "missing frontmatter fields",
            ),
        )

        for case_name, kind, overrides, field, expected_message in cases:
            with self.subTest(case=case_name):
                path = self.product_path(kind)
                path.write_text(product_document(kind, **overrides))

                result = self.run_cli("inspect", str(path))

                self.assertEqual(result.returncode, 3)
                self.assertIn(field, result.stderr)
                self.assertIn(expected_message, result.stderr)

    def test__allocate__idea_with_existing_numbers__creates_next_file_and_reports_duplicates(self) -> None:
        (self.ideas / "IDEA-0002-first.md").write_text("")
        (self.ideas / "IDEA-0002-second.md").write_text("")
        (self.ideas / "IDEA-0007-existing.md").write_text("")

        result = self.run_cli(
            "allocate",
            "idea",
            "--root",
            str(self.ideas),
            "--slug",
            "provider-routing",
            "--json",
        )

        target = self.ideas / "IDEA-0008-provider-routing.md"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "created": True,
                "duplicates": [2],
                "id": "IDEA-0008",
                "kind": "idea",
                "number": 8,
                "path": str(target.resolve()),
            },
        )
        self.assertTrue(target.is_file())

    def test__allocate__epic__creates_numbered_directory(self) -> None:
        result = self.run_cli(
            "allocate",
            "epic",
            "--root",
            str(self.epics),
            "--slug",
            "provider-routing",
        )

        target = self.epics / "EPIC-0001-provider-routing"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(target.is_dir())
        self.assertEqual(json.loads(result.stdout)["path"], str(target.resolve()))

    def test__allocate__feature__creates_directory_and_review_subdirectory(self) -> None:
        result = self.run_cli(
            "allocate",
            "feature",
            "--root",
            str(self.features),
            "--slug",
            "provider-routing",
        )

        target = self.features / "FEAT-0001-provider-routing"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(target.is_dir())
        self.assertTrue((target / "review-request-changes").is_dir())

    def test__allocate__feature_review_directory_conflict__returns_invalid_without_retry_or_orphan(
        self,
    ) -> None:
        original_mkdir = Path.mkdir
        mkdir_calls = 0

        def nested_directory_conflict(
            path: Path,
            mode: int = 0o777,
            parents: bool = False,
            exist_ok: bool = False,
        ) -> None:
            nonlocal mkdir_calls
            mkdir_calls += 1
            if mkdir_calls == 2:
                raise FileExistsError(path)
            original_mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)

        with mock.patch.object(
            Path, "mkdir", autospec=True, side_effect=nested_directory_conflict
        ):
            with self.assertRaisesRegex(
                product_state.ProductStateError, "review-request-changes"
            ):
                product_state.allocate_artifact(
                    "feature", self.features, "provider-routing"
                )

        self.assertEqual(mkdir_calls, 2)
        self.assertEqual(list(self.features.iterdir()), [])

    def test__allocate__exclusive_creation_conflict__retries_next_number(self) -> None:
        original_open = os.open
        attempts = 0

        def racing_open(path: Path, flags: int, mode: int = 0o777) -> int:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise FileExistsError(path)
            return original_open(path, flags, mode)

        with mock.patch.object(os, "open", side_effect=racing_open):
            payload = product_state.allocate_artifact(
                "idea", self.ideas, "provider-routing"
            )

        self.assertEqual(payload["number"], 2)
        self.assertTrue((self.ideas / "IDEA-0002-provider-routing.md").is_file())

    def test__allocate__roadmap__returns_invalid(self) -> None:
        result = self.run_cli(
            "allocate",
            "roadmap",
            "--root",
            str(self.epics),
            "--slug",
            "provider-routing",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("roadmap cannot be allocated", result.stderr)

    def test__validate_target__valid_name_and_directory_for_each_kind__returns_current(self) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        feature_directory = self.features / "FEAT-0001-provider-routing"
        epic_directory.mkdir()
        feature_directory.mkdir()
        epic_parent = epic_directory / "EPIC.md"
        epic_parent.write_text("# Epic\n")
        cases = (
            ("idea", self.idea_path(), self.ideas, None),
            ("epic", epic_parent, epic_directory, None),
            ("roadmap", epic_directory / "ROADMAP.md", epic_directory, epic_parent),
            ("feature", feature_directory / "README.md", feature_directory, None),
        )

        for kind, target, directory, parent in cases:
            with self.subTest(kind=kind):
                arguments = [
                    "validate-target",
                    kind,
                    str(target),
                    "--directory",
                    str(directory),
                ]
                if parent is not None:
                    arguments.extend(("--parent", str(parent)))
                result = self.run_cli(*arguments)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(result.stdout),
                    {
                        "kind": kind,
                        "path": str(target.resolve()),
                        "status": "current",
                    },
                )

    def test__validate_target__wrong_name_for_each_kind__returns_invalid(self) -> None:
        directory = self.root / "targets"
        directory.mkdir()
        cases = (
            ("idea", directory / "IDEA.md"),
            ("epic", directory / "EPIC-0001-provider-routing.md"),
            ("roadmap", directory / "ROADMAP-0001.md"),
            ("feature", directory / "FEATURE.md"),
        )

        for kind, target in cases:
            with self.subTest(kind=kind):
                arguments = [
                    "validate-target",
                    kind,
                    str(target),
                    "--directory",
                    str(directory),
                ]
                if kind == "roadmap":
                    parent = directory / "EPIC.md"
                    parent.write_text("# Epic\n")
                    arguments.extend(("--parent", str(parent)))
                result = self.run_cli(*arguments)

                self.assertEqual(result.returncode, 3)
                self.assertIn("target name", result.stderr)

    def test__validate_target__path_outside_directory__returns_invalid(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        target = outside / "IDEA-0001-provider-routing.md"

        result = self.run_cli(
            "validate-target",
            "idea",
            str(target),
            "--directory",
            str(self.ideas),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("target must stay inside", result.stderr)

    def test__validate_target__symbolic_link__returns_invalid(self) -> None:
        outside = self.root / "outside.md"
        outside.write_text("# Outside\n")
        target = self.idea_path()
        target.symlink_to(outside)

        result = self.run_cli(
            "validate-target",
            "idea",
            str(target),
            "--directory",
            str(self.ideas),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("symbolic link", result.stderr)

    def test__validate_target__hard_link__returns_invalid(self) -> None:
        source = self.root / "source.md"
        source.write_text("# Source\n")
        target = self.idea_path()
        os.link(source, target)

        result = self.run_cli(
            "validate-target",
            "idea",
            str(target),
            "--directory",
            str(self.ideas),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("hard link", result.stderr)

    def test__validate_target__nonregular_file__returns_invalid(self) -> None:
        target = self.idea_path()
        os.mkfifo(target)

        result = self.run_cli(
            "validate-target",
            "idea",
            str(target),
            "--directory",
            str(self.ideas),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("regular file", result.stderr)

    def test__validate_target__same_path_as_protected_parent__returns_invalid(self) -> None:
        feature_directory = self.features / "FEAT-0001-provider-routing"
        feature_directory.mkdir()
        target = feature_directory / "README.md"

        result = self.run_cli(
            "validate-target",
            "feature",
            str(target),
            "--directory",
            str(feature_directory),
            "--parent",
            str(target),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("different files", result.stderr)

    def test__consume_prepared_body__exact_neighbor__returns_body_and_deletes_file(self) -> None:
        target = self.idea_path()
        prepared = self.prepared_body(target, "# Prepared idea\n")

        body = product_state.consume_prepared_body(prepared, target)

        self.assertEqual(body, "# Prepared idea\n")
        self.assertFalse(prepared.exists())

    def test__consume_prepared_body__arbitrary_neighbor__returns_invalid_without_deleting_source(self) -> None:
        target = self.idea_path()
        source = self.ideas / "draft.md"
        source.write_text("# Draft\n")

        with self.assertRaisesRegex(
            product_state.ProductStateError, "IDEA-0001-provider-routing.md.prepared"
        ):
            product_state.consume_prepared_body(source, target)

        self.assertEqual(source.read_text(), "# Draft\n")

    def test__consume_prepared_body__unsuitable_file_node__returns_invalid(
        self,
    ) -> None:
        for case, make_node, expected in _UNSUITABLE_FILE_NODES:
            with self.subTest(case=case):
                target = self.ideas / f"IDEA-0001-{case.replace(' ', '-')}.md"
                prepared = target.with_name(f"{target.name}.prepared")
                make_node(prepared, self.ideas / f"source-{case[0]}.md")

                with self.assertRaisesRegex(
                    product_state.ProductStateError, expected
                ):
                    product_state.consume_prepared_body(prepared, target)

                self.assertTrue(prepared.exists() or prepared.is_symlink())
                self.assertFalse(target.exists())

    def test__sync__field_from_another_kind__returns_invalid_before_consuming_body(
        self,
    ) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        self.sync_product("epic", epic, "# Epic\n", stage="shaping")
        feature_directory = self.features / "FEAT-0001-provider-routing"
        feature_directory.mkdir()
        cases = (
            (
                "idea",
                self.idea_path(),
                ("--stage", "exploring", "--outcome", "open", "--readiness", "ready"),
                "readiness",
            ),
            (
                "epic",
                epic,
                ("--stage", "active", "--outcome", "open"),
                "outcome",
            ),
            (
                "roadmap",
                epic_directory / "ROADMAP.md",
                ("--parent", str(epic), "--state", "active", "--stage", "shaping"),
                "stage",
            ),
            (
                "feature",
                feature_directory / "README.md",
                ("--readiness", "ready", "--state", "active"),
                "state",
            ),
        )

        for kind, target, fields, unexpected_field in cases:
            with self.subTest(kind=kind, field=unexpected_field):
                previous = target.read_bytes() if target.exists() else None
                prepared = self.prepared_body(target, f"# Invalid {kind.title()}\n")

                result = self.run_cli(
                    "sync",
                    kind,
                    str(target),
                    "--body-file",
                    str(prepared),
                    "--semantic-change",
                    "yes",
                    *fields,
                )

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(unexpected_field, result.stderr)
                self.assertTrue(prepared.exists())
                if previous is None:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), previous)

    def test__sync__new_idea__writes_version_one(self) -> None:
        body = "# Idea\n"

        result = self.sync_idea(body)

        self.assertEqual(json.loads(result.stdout)["version"], 1)
        self.assert_product_document(
            self.idea_path(),
            {
                "plan_type": "idea",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(body),
                "stage": "exploring",
                "outcome": "open",
            },
            body,
        )

    def test__sync__semantic_body_change__increments_version(self) -> None:
        self.sync_idea("# Idea\n")
        changed_body = "# Changed idea\n"

        self.sync_idea(changed_body, semantic_change="yes")

        self.assertEqual(
            product_state.read_document(self.idea_path()).metadata["version"], 2
        )

    def test__sync__nonsemantic_body_change__preserves_version_and_updates_hash(self) -> None:
        self.sync_idea("# Idea\n")
        changed_body = "# Idea\n\n"

        self.sync_idea(changed_body, semantic_change="no")

        self.assert_product_document(
            self.idea_path(),
            {
                "plan_type": "idea",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(changed_body),
                "stage": "exploring",
                "outcome": "open",
            },
            changed_body,
        )

    def test__sync__epic_with_origin__records_parent_snapshot(self) -> None:
        idea_body = "# Idea\n"
        self.sync_idea(idea_body)
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        epic_body = "# Epic\n"

        self.sync_product(
            "epic",
            epic,
            epic_body,
            parent=self.idea_path(),
            stage="shaping",
        )

        self.assert_product_document(
            epic,
            {
                "plan_type": "epic",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(epic_body),
                "stage": "shaping",
                "origin": {
                    "path": "../../ideas/IDEA-0001-provider-routing.md",
                    "version": 1,
                    "content_sha256": body_hash(idea_body),
                },
            },
            epic_body,
        )

    def test__sync__roadmap__records_required_epic_snapshot(self) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        epic_body = "# Epic\n"
        self.sync_product("epic", epic, epic_body, stage="shaping")
        roadmap = epic_directory / "ROADMAP.md"
        roadmap_body = "# Roadmap\n"

        self.sync_product(
            "roadmap",
            roadmap,
            roadmap_body,
            parent=epic,
            state="active",
        )

        self.assert_product_document(
            roadmap,
            {
                "plan_type": "roadmap",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(roadmap_body),
                "state": "active",
                "epic": {
                    "path": "./EPIC.md",
                    "version": 1,
                    "content_sha256": body_hash(epic_body),
                },
            },
            roadmap_body,
        )

    def test__sync__roadmap_without_parent__rejects_before_reading_body(self) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        roadmap = epic_directory / "ROADMAP.md"
        prepared = self.prepared_body(roadmap, "# Roadmap\n")

        result = self.run_cli(
            "sync",
            "roadmap",
            str(roadmap),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
            "--state",
            "active",
        )

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("roadmap parent EPIC.md is required", result.stderr)
        self.assertTrue(prepared.exists())
        self.assertFalse(roadmap.exists())

    def test__sync__feature_with_parent__records_parent_snapshot(self) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        epic_body = "# Epic\n"
        self.sync_product("epic", epic, epic_body, stage="shaping")
        feature_directory = self.features / "FEAT-0001-provider-routing"
        feature_directory.mkdir()
        feature = feature_directory / "README.md"
        feature_body = "# Feature\n"

        self.sync_product(
            "feature",
            feature,
            feature_body,
            parent=epic,
            readiness="ready",
        )

        self.assert_product_document(
            feature,
            {
                "plan_type": "feature",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(feature_body),
                "readiness": "ready",
                "parent": {
                    "path": "../../epics/EPIC-0001-provider-routing/EPIC.md",
                    "version": 1,
                    "content_sha256": body_hash(epic_body),
                },
            },
            feature_body,
        )

    def test__sync__existing_linked_document_without_parent__preserves_parent_snapshot(
        self,
    ) -> None:
        self.sync_idea()
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        self.sync_product(
            "epic", epic, "# Epic\n", parent=self.idea_path(), stage="shaping"
        )
        roadmap = epic_directory / "ROADMAP.md"
        self.sync_product(
            "roadmap", roadmap, "# Roadmap\n", parent=epic, state="active"
        )
        feature_directory = self.features / "FEAT-0001-provider-routing"
        feature_directory.mkdir()
        feature = feature_directory / "README.md"
        self.sync_product(
            "feature", feature, "# Feature\n", parent=epic, readiness="ready"
        )
        cases = (
            ("epic", epic, "origin", "stage", "active"),
            ("roadmap", roadmap, "epic", "state", "paused"),
            ("feature", feature, "parent", "readiness", "draft"),
        )

        for kind, path, reference_field, value_field, value in cases:
            with self.subTest(kind=kind):
                reference_before = dict(
                    product_state.read_document(path).metadata[reference_field]
                )
                changed_body = f"# Changed {kind.title()}\n"
                prepared = self.prepared_body(path, changed_body)

                result = self.run_cli(
                    "sync",
                    kind,
                    str(path),
                    "--body-file",
                    str(prepared),
                    "--semantic-change",
                    "no",
                    f"--{value_field}",
                    value,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(prepared.exists())
                document = product_state.read_document(path)
                self.assertEqual(document.metadata[reference_field], reference_before)
                self.assertEqual(document.body, changed_body)

    def test__lifecycle__idea_to_epic_to_roadmap__links_and_versions_stay_consistent(
        self,
    ) -> None:
        idea = self.allocate_product("idea", self.ideas, "lifecycle")
        self.sync_product(
            "idea",
            idea,
            "# Exploring idea\n",
            stage="exploring",
            outcome="open",
        )
        resolved_body = "# Resolved idea\n"
        self.sync_product(
            "idea",
            idea,
            resolved_body,
            stage="resolved",
            outcome="epic",
            target="../epics/EPIC-0001-lifecycle/EPIC.md",
        )
        idea_before_children = self.inspect_product(idea)
        idea_bytes = idea.read_bytes()

        epic_directory = self.allocate_product("epic", self.epics, "lifecycle")
        epic = epic_directory / "EPIC.md"
        epic_body = "# Epic\n"
        self.sync_product(
            "epic", epic, epic_body, parent=idea, stage="shaping"
        )
        epic_before_roadmap = self.inspect_product(epic)
        epic_bytes = epic.read_bytes()
        roadmap = epic_directory / "ROADMAP.md"
        roadmap_body = "# Roadmap\n"
        self.sync_product(
            "roadmap", roadmap, roadmap_body, parent=epic, state="active"
        )

        idea_state = self.inspect_product(idea)
        epic_state = self.inspect_product(epic)
        roadmap_state = self.inspect_product(roadmap)
        self.assertEqual(idea_state, idea_before_children)
        self.assertEqual(idea.read_bytes(), idea_bytes)
        self.assertEqual(idea_state["version"], 2)
        self.assertEqual(idea_state["content_sha256"], body_hash(resolved_body))
        self.assertEqual(epic_state, epic_before_roadmap)
        self.assertEqual(epic.read_bytes(), epic_bytes)
        self.assertEqual(epic_state["version"], 1)
        self.assertEqual(epic_state["content_sha256"], body_hash(epic_body))
        self.assertEqual(
            epic_state["origin"],
            {
                "path": "../../ideas/IDEA-0001-lifecycle.md",
                "version": idea_state["version"],
                "content_sha256": idea_state["content_sha256"],
            },
        )
        self.assertEqual(roadmap_state["version"], 1)
        self.assertEqual(
            roadmap_state["content_sha256"], body_hash(roadmap_body)
        )
        self.assertEqual(
            roadmap_state["epic"],
            {
                "path": "./EPIC.md",
                "version": epic_state["version"],
                "content_sha256": epic_state["content_sha256"],
            },
        )
        self.assertEqual({path.name for path in self.ideas.iterdir()}, {idea.name})
        self.assertEqual(
            {path.name for path in self.epics.iterdir()}, {epic_directory.name}
        )
        self.assertEqual(
            {path.name for path in epic_directory.iterdir()}, {epic.name, roadmap.name}
        )
        self.assertEqual(list(self.features.iterdir()), [])

    def linked_pair(self, slug: str) -> tuple[Path, Path]:
        epic_directory = self.allocate_product("epic", self.epics, slug)
        epic = epic_directory / "EPIC.md"
        self.sync_product("epic", epic, "# Epic\n", stage="shaping")
        roadmap = epic_directory / "ROADMAP.md"
        self.sync_product(
            "roadmap", roadmap, "# Roadmap\n", parent=epic, state="active"
        )
        return epic, roadmap

    def test__check__non_current_document__names_the_reason(self) -> None:
        def break_parent_body(epic: Path, roadmap: Path) -> None:
            epic.write_text(epic.read_text() + "Правка мимо метаданных.\n")

        def raise_parent_version(epic: Path, roadmap: Path) -> None:
            epic.write_text(epic.read_text().replace("version: 1", "version: 2", 1))

        def rewrite_parent_body_without_meaning(epic: Path, roadmap: Path) -> None:
            self.sync_product(
                "epic", epic, "# Epic, иначе\n", semantic_change="no", stage="shaping"
            )

        def mark_child_stale(epic: Path, roadmap: Path) -> None:
            roadmap.write_text(
                roadmap.read_text().replace("status: current", "status: stale", 1)
            )

        cases = (
            ("parent body edited beside metadata", break_parent_body,
             "epic content hash does not match its body"),
            ("recorded version behind", raise_parent_version,
             "epic version mismatch"),
            ("recorded hash behind", rewrite_parent_body_without_meaning,
             "epic content hash mismatch"),
            ("child marked stale", mark_child_stale, "document status is stale"),
        )

        for index, (case, prepare, expected_reason) in enumerate(cases):
            with self.subTest(case=case):
                epic, roadmap = self.linked_pair(f"reason-{index}")
                prepare(epic, roadmap)

                result = self.run_cli("check", str(roadmap))

                self.assertEqual(result.returncode, 2, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["status"], "stale")
                self.assertEqual(payload["reason"], expected_reason)

    def test__check__own_body_changed_beside_metadata__returns_invalid(self) -> None:
        idea = self.allocate_product("idea", self.ideas, "own-hash")
        self.sync_product(
            "idea", idea, "# Idea\n", stage="exploring", outcome="open"
        )
        idea.write_text(idea.read_text() + "Правка мимо метаданных.\n")
        changed = idea.read_bytes()

        result = self.run_cli("check", str(idea))

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("content hash mismatch", result.stderr)
        self.assertEqual(idea.read_bytes(), changed)

    def test__sync__inconsistent_parent__rejects_and_writes_nothing(self) -> None:
        epic_directory = self.allocate_product("epic", self.epics, "broken-parent")
        epic = epic_directory / "EPIC.md"
        self.sync_product("epic", epic, "# Epic\n", stage="shaping")
        epic.write_text(epic.read_text() + "Правка мимо метаданных.\n")
        roadmap = epic_directory / "ROADMAP.md"
        prepared = self.prepared_body(roadmap, "# Roadmap\n")

        result = self.run_cli(
            "sync", "roadmap", str(roadmap),
            "--body-file", str(prepared),
            "--semantic-change", "yes",
            "--parent", str(epic),
            "--state", "active",
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("does not match its body", result.stderr)
        self.assertTrue(prepared.exists())
        self.assertFalse(roadmap.exists())

    def test__sync__roadmap_parent_not_epic_beside_target__returns_invalid(
        self,
    ) -> None:
        own_directory = self.allocate_product("epic", self.epics, "own-hypothesis")
        own_epic = own_directory / "EPIC.md"
        self.sync_product("epic", own_epic, "# Epic\n", stage="shaping")
        other_directory = self.allocate_product("epic", self.epics, "other-hypothesis")
        other_epic = other_directory / "EPIC.md"
        self.sync_product("epic", other_epic, "# Other epic\n", stage="shaping")
        misnamed = own_directory / "HYPOTHESIS.md"
        misnamed.write_text(own_epic.read_text())
        cases = (
            ("parent in another directory", other_epic),
            ("parent not named EPIC.md", misnamed),
        )

        for case, parent in cases:
            with self.subTest(case=case):
                roadmap = own_directory / "ROADMAP.md"
                prepared = self.prepared_body(roadmap, "# Roadmap\n")

                result = self.run_cli(
                    "sync", "roadmap", str(roadmap),
                    "--body-file", str(prepared),
                    "--semantic-change", "yes",
                    "--parent", str(parent),
                    "--state", "active",
                )

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn("same directory", result.stderr)
                self.assertTrue(prepared.exists())
                self.assertFalse(roadmap.exists())
                prepared.unlink()

    def test__lifecycle__epic_body_changes__roadmap_becomes_stale_and_keeps_body(
        self,
    ) -> None:
        epic_directory = self.allocate_product("epic", self.epics, "staleness")
        epic = epic_directory / "EPIC.md"
        self.sync_product("epic", epic, "# Epic\n", stage="shaping")
        roadmap = epic_directory / "ROADMAP.md"
        roadmap_body = "# Roadmap\nKeep this body.\n"
        self.sync_product(
            "roadmap", roadmap, roadmap_body, parent=epic, state="active"
        )
        roadmap_before = roadmap.read_bytes()
        roadmap_state_before = self.inspect_product(roadmap)

        changed_epic_body = "# Changed epic\n"
        self.sync_product(
            "epic", epic, changed_epic_body, stage="active"
        )
        first_check = self.run_cli("check", str(roadmap))

        self.assertEqual(first_check.returncode, 2, first_check.stderr)
        self.assertEqual(json.loads(first_check.stdout)["status"], "stale")
        self.assertEqual(roadmap.read_bytes(), roadmap_before)

        marked_check = self.run_cli("check", str(roadmap), "--mark-stale")

        self.assertEqual(marked_check.returncode, 2, marked_check.stderr)
        roadmap_document = product_state.read_document(roadmap)
        roadmap_state_after = self.inspect_product(roadmap)
        self.assertEqual(roadmap_document.body, roadmap_body)
        self.assertEqual(
            roadmap_state_after["version"], roadmap_state_before["version"]
        )
        self.assertEqual(
            roadmap_state_after["content_sha256"],
            roadmap_state_before["content_sha256"],
        )
        self.assertEqual(
            roadmap_state_after["epic"], roadmap_state_before["epic"]
        )
        self.assertEqual(roadmap_state_after["status"], "stale")
        self.assertEqual(
            roadmap.read_bytes(),
            roadmap_before.replace(b"status: current\n", b"status: stale\n", 1),
        )
        epic_state = self.inspect_product(epic)
        self.assertEqual(epic_state["version"], 2)
        self.assertEqual(
            epic_state["content_sha256"], body_hash(changed_epic_body)
        )
        self.assertEqual(
            {path.name for path in epic_directory.iterdir()}, {epic.name, roadmap.name}
        )
        self.assertEqual(list(self.ideas.iterdir()), [])
        self.assertEqual(list(self.features.iterdir()), [])

    def test__lifecycle__failed_sync__leaves_previous_document_and_removes_no_data(
        self,
    ) -> None:
        idea = self.allocate_product("idea", self.ideas, "atomic-sync")
        self.sync_product(
            "idea",
            idea,
            "# Stable idea\n",
            stage="exploring",
            outcome="open",
        )
        previous_bytes = idea.read_bytes()
        previous_state = self.inspect_product(idea)
        prepared = self.prepared_body(idea, "# Invalid replacement\n")

        result = self.run_cli(
            "sync",
            "idea",
            str(idea),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
            "--stage",
            "exploring",
            "--outcome",
            "research",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("outcome", result.stderr)
        self.assertIn("exploring idea requires outcome open", result.stderr)
        self.assertEqual(idea.read_bytes(), previous_bytes)
        self.assertEqual(self.inspect_product(idea), previous_state)
        self.assertFalse(prepared.exists())
        self.assertEqual({path.name for path in self.ideas.iterdir()}, {idea.name})
        self.assertEqual(list(self.epics.iterdir()), [])
        self.assertEqual(list(self.features.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
