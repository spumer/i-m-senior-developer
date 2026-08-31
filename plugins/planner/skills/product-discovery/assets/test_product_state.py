import hashlib
import json
import os
from pathlib import Path
import shutil
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


def evidence_record(
    identifier: str = "a1",
    record_type: str = "наблюдение",
    claim: str = "владелец теряет элементы при массовом удалении",
    carrier: str = "реплика владельца в обсуждении",
) -> dict[str, object]:
    return {
        "id": identifier,
        "type": record_type,
        "claim": claim,
        "carrier": carrier,
    }


def complete_body(kind: str, body: str, stage: str | None = None) -> str:
    if "```yaml evidence-registry" in body:
        return body
    registry = (
        "```yaml evidence-registry\n"
        "- id: E1\n"
        "  type: наблюдение\n"
        "  claim: владелец теряет элементы при массовом удалении\n"
        "  carrier: реплика владельца в обсуждении\n"
        "```\n\n"
    )
    duty = ""
    if kind == "roadmap":
        duty = "## Основание порядка\nПорядок опирается на [E1].\n"
    elif kind == "feature":
        duty = (
            "## Договор взаимодействия\n"
            "Актор вызывает действие и видит результат [E1].\n"
        )
    elif kind == "idea" and stage == "resolved":
        duty = "## Решение\nИсход: decision\nОснование: [E1].\n"
    return f"{body}{registry}{duty}"


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
        analysis_by: str = "planner:product-baseline",
        **fields: str,
    ) -> subprocess.CompletedProcess[str]:
        prepared = self.prepared_body(
            path, complete_body(kind, body, fields.get("stage"))
        )
        arguments = [
            "sync",
            kind,
            str(path),
            "--body-file",
            str(prepared),
            "--semantic-change",
            semantic_change,
            "--analysis-by",
            analysis_by,
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
        self, body: str = "# Idea\n", semantic_change: str = "yes", **fields: str
    ) -> subprocess.CompletedProcess[str]:
        return self.sync_product(
            "idea",
            self.idea_path(),
            body,
            semantic_change,
            stage="exploring",
            outcome="open",
            **fields,
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

    def reserve_lease(self) -> Path:
        result = self.run_cli("reserve-response-draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        lease = Path(json.loads(result.stdout)["path"])
        # аренда живёт в системном временном каталоге, а не в self.root,
        # поэтому её не забирает общая уборка теста
        self.addCleanup(shutil.rmtree, lease.parent, ignore_errors=True)
        return lease

    def lease_draft(self, lease: Path, *, valid: bool = True) -> None:
        draft: dict[str, object] = {
            "problem": "владелец теряет сохранённые элементы после массового удаления",
            "outcome": "удалённый элемент возвращается за один шаг",
            "actors": "владелец элемента",
            "scope_in": "возврат последнего удалённого элемента",
            "scope_out": "полная история версий",
            "assumptions": ["потеря происходит при массовом удалении"],
            "unknowns": ["как часто владелец замечает потерю"],
            "limitations": ["нет данных о пользователях"],
            "recommended_outcome": "feature",
        }
        if not valid:
            draft["confidence"] = "high"
        lease.write_text(json.dumps(draft, ensure_ascii=False))

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
                "line": 7,
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

    def test__parse_capabilities__dash_or_comment_only_evidence__normalizes_coverage_to_unknown(
        self,
    ) -> None:
        cases = (
            ("dash-only", "—"),
            ("html-comment-only", "<!-- auto-added 2026-08-14 -->"),
        )

        for case_name, evidence in cases:
            with self.subTest(case=case_name):
                context = self.context_path(
                    row_overrides={"problem.external": {"evidence": evidence}}
                )

                result = self.run_cli("parse-capabilities", str(context))

                self.assertEqual(result.returncode, 0, result.stderr)
                row = json.loads(result.stdout)[0]
                self.assertEqual(row["evidence"], evidence)
                self.assertEqual(row["coverage"], "unknown")

    def test__parse_capabilities__path_with_html_comment_evidence__keeps_recorded_coverage(
        self,
    ) -> None:
        evidence = ".claude/agents/product.md <!-- auto-added 2026-08-14 -->"

        context = self.context_path(
            row_overrides={"problem.external": {"evidence": evidence}}
        )

        result = self.run_cli("parse-capabilities", str(context))

        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)[0]
        self.assertEqual(row["evidence"], evidence)
        self.assertEqual(row["coverage"], "full")

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
                "line": 9,
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
                "line": 10,
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

    def test__route__trace_names_line_and_reason_for_every_candidate(self) -> None:
        context = self.context_path(
            extra_rows=(
                (
                    "synthesis.dash-evidence",
                    capability_row(
                        "dash-provider", capability="product_synthesis", evidence="—"
                    ),
                ),
            )
        )

        result = self.run_cli("route", str(context), "--for", "epic")

        self.assertEqual(result.returncode, 0, result.stderr)
        trace = json.loads(result.stdout)
        self.assertEqual(len(trace["candidates"]), 7)
        for candidate in trace["candidates"]:
            with self.subTest(provider=candidate["provider"]):
                self.assertIsInstance(candidate["line"], int)
                if candidate["selected"]:
                    self.assertIsNone(candidate["rejected"])
                else:
                    self.assertIsNotNone(candidate["rejected"])
        dash = next(
            candidate
            for candidate in trace["candidates"]
            if candidate["provider"] == "dash-provider"
        )
        self.assertEqual(dash["line"], 13)
        self.assertEqual(dash["coverage"], "unknown")
        self.assertEqual(dash["rejected"], "no-substantive-evidence")

    def test__route__uncovered_capability__stderr_lists_rejected_rows(self) -> None:
        context = self.context_path(
            extra_rows=(
                (
                    "uncovered.dash",
                    capability_row(
                        "dash-provider",
                        capability="uncovered_capability",
                        evidence="—",
                    ),
                ),
                (
                    "uncovered.stale",
                    capability_row(
                        "stale-provider",
                        capability="uncovered_capability",
                        availability="stale",
                    ),
                ),
                (
                    "uncovered.none",
                    capability_row(
                        "none-provider",
                        capability="uncovered_capability",
                        coverage="none",
                    ),
                ),
            )
        )

        result = self.run_cli("route", str(context), "--for", "epic")

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("uncovered_capability", result.stderr)
        self.assertIn("not covered", result.stderr)
        self.assertIn(
            "line 13: provider dash-provider: no-substantive-evidence", result.stderr
        )
        self.assertIn(
            "line 14: provider stale-provider: availability-stale", result.stderr
        )
        self.assertIn("line 15: provider none-provider: coverage-none", result.stderr)

    def test__route__pinned_provider_without_evidence__stderr_lists_rejected_rows(
        self,
    ) -> None:
        context = self.context_path(
            row_overrides={"problem.external": {"evidence": "—"}}
        )

        result = self.run_cli(
            "route", str(context), "--for", "feature", "--pin", "product"
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("problem_outcome_framing", result.stderr)
        self.assertIn(
            "line 7: provider product: no-substantive-evidence", result.stderr
        )
        self.assertIn(
            "line 8: provider planner:product-baseline: not-pinned-provider",
            result.stderr,
        )

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

    def test__reserve_response_draft__unique_temp_directory_with_exact_file_name(
        self,
    ) -> None:
        first = self.reserve_lease()
        second = self.reserve_lease()

        self.assertEqual(first.name, "provider-response.json")
        self.assertEqual(second.name, "provider-response.json")
        self.assertNotEqual(first.parent, second.parent)
        self.assertTrue(first.parent.is_dir())
        self.assertTrue(
            first.parent.is_relative_to(Path(tempfile.gettempdir())),
            str(first.parent),
        )

    def test__check_response__consume_accepted_draft__removes_file_and_directory(
        self,
    ) -> None:
        lease = self.reserve_lease()
        self.lease_draft(lease)

        result = self.run_cli(
            "check-response", str(lease), "--for", "idea", "--consume"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["accepted"], True)
        self.assertEqual(payload["draft_removed"], True)
        self.assertFalse(lease.exists())
        self.assertFalse(lease.parent.exists())

    def test__check_response__consume_rejected_draft__still_removes_file_and_directory(
        self,
    ) -> None:
        lease = self.reserve_lease()
        self.lease_draft(lease, valid=False)

        result = self.run_cli(
            "check-response", str(lease), "--for", "idea", "--consume"
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("confidence", result.stderr)
        self.assertFalse(lease.exists())
        self.assertFalse(lease.parent.exists())

    def test__check_response__consume_wrong_file_name__returns_invalid_without_deletion(
        self,
    ) -> None:
        draft = self.root / "provider-draft.json"
        draft.write_text("{}\n")

        result = self.run_cli(
            "check-response", str(draft), "--for", "idea", "--consume"
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("provider-response.json", result.stderr)
        self.assertTrue(draft.exists())

    def test__check_response__consume_foreign_correct_file_name__rejects_without_reading_or_deletion(
        self,
    ) -> None:
        foreign_directory = self.root / "foreign-response-draft"
        foreign_directory.mkdir()
        draft = foreign_directory / product_state.LEASE_FILE_NAME
        draft.write_text("this is not JSON\n")

        result = self.run_cli(
            "check-response", str(draft), "--for", "idea", "--consume"
        )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn(str(draft.resolve()), result.stderr)
        self.assertIn("product-response-", result.stderr)
        self.assertNotIn("not valid JSON", result.stderr)
        self.assertTrue(draft.exists())
        self.assertTrue(foreign_directory.exists())

    def test__check_response__consume_deletion_failure__error_is_not_masked(
        self,
    ) -> None:
        for valid in (True, False):
            with self.subTest(valid=valid):
                lease = self.reserve_lease()
                self.lease_draft(lease, valid=valid)
                os.chmod(lease.parent, 0o500)
                try:
                    result = self.run_cli(
                        "check-response", str(lease), "--for", "idea", "--consume"
                    )
                finally:
                    os.chmod(lease.parent, 0o700)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn("draft cleanup failed", result.stderr)
                if not valid:
                    self.assertIn("confidence", result.stderr)
                self.assertTrue(lease.exists())

    def test__release_response_draft__existing_file__removes_file_and_directory(
        self,
    ) -> None:
        lease = self.reserve_lease()
        self.lease_draft(lease)

        result = self.run_cli("release-response-draft", str(lease))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {"draft_existed": True, "path": str(lease.resolve()), "removed": True},
        )
        self.assertFalse(lease.exists())
        self.assertFalse(lease.parent.exists())

    def test__release_response_draft__absent_file__reports_nothing_to_remove(
        self,
    ) -> None:
        lease = self.reserve_lease()

        result = self.run_cli("release-response-draft", str(lease))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {"draft_existed": False, "path": str(lease.resolve()), "removed": False},
        )
        self.assertFalse(lease.parent.exists())

    def test__release_response_draft__wrong_file_name__returns_invalid(self) -> None:
        draft = self.root / "provider-draft.json"
        draft.write_text("{}\n")

        result = self.run_cli("release-response-draft", str(draft))

        self.assertEqual(result.returncode, 3)
        self.assertIn("provider-response.json", result.stderr)
        self.assertTrue(draft.exists())

    def test__release_response_draft__foreign_correct_file_name__rejects_without_deletion(
        self,
    ) -> None:
        foreign_directory = self.root / "foreign-response-draft"
        foreign_directory.mkdir()
        draft = foreign_directory / product_state.LEASE_FILE_NAME
        draft.write_text("{}\n")

        result = self.run_cli("release-response-draft", str(draft))

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn(str(draft.resolve()), result.stderr)
        self.assertIn("product-response-", result.stderr)
        self.assertTrue(draft.exists())
        self.assertTrue(foreign_directory.exists())

    def test__inspect__document_without_analysis_by__remains_valid(self) -> None:
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

    def test__inspect__empty_analysis_by__returns_invalid(self) -> None:
        for kind in ("idea", "epic", "roadmap", "feature"):
            with self.subTest(kind=kind):
                path = self.product_path(kind)
                path.write_text(product_document(kind, analysis_by="  "))

                result = self.run_cli("inspect", str(path))

                self.assertEqual(result.returncode, 3)
                self.assertIn("analysis_by must be a non-empty string", result.stderr)

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

    def test__validate_evidence_records__records_of_every_type__returns_them(
        self,
    ) -> None:
        records = [
            evidence_record("a1", "наблюдение"),
            evidence_record("a2", "внешний источник"),
            evidence_record("a3", "допущение"),
            evidence_record("a4", "POV-гипотеза"),
            evidence_record("a5", "неизвестное"),
            evidence_record("a6", "не перенесено"),
        ]

        validated = product_state.validate_evidence_records(
            records, self.ideas / "evidence-registry.yaml"
        )

        self.assertEqual(validated, records)

    def test__validate_evidence_records__record_not_an_object__names_record_number(
        self,
    ) -> None:
        records = [evidence_record("a1"), 42]

        with self.assertRaisesRegex(
            product_state.ProductStateError, r"record 2 must be an object"
        ):
            product_state.validate_evidence_records(
                records, self.ideas / "evidence-registry.yaml"
            )

    def test__validate_evidence_records__missing_required_field__names_record_and_field(
        self,
    ) -> None:
        for field in ("id", "type", "claim", "carrier"):
            with self.subTest(field=field):
                second = evidence_record("a2")
                del second[field]

                with self.assertRaisesRegex(
                    product_state.ProductStateError,
                    rf"record 2 field {field} is missing",
                ):
                    product_state.validate_evidence_records(
                        [evidence_record("a1"), second],
                        self.ideas / "evidence-registry.yaml",
                    )

    def test__validate_evidence_records__unknown_type__names_record_field_and_allowed_values(
        self,
    ) -> None:
        records = [
            evidence_record("a1"),
            evidence_record("a2", record_type="мнение"),
        ]

        with self.assertRaisesRegex(
            product_state.ProductStateError, r"record 2 field type"
        ) as caught:
            product_state.validate_evidence_records(
                records, self.ideas / "evidence-registry.yaml"
            )

        message = str(caught.exception)
        for allowed in product_state._EVIDENCE_TYPES:
            self.assertIn(allowed, message)

    def test__validate_evidence_records__empty_carrier__names_record_and_field(
        self,
    ) -> None:
        for carrier in ("", "   "):
            with self.subTest(carrier=carrier):
                records = [
                    evidence_record("a1"),
                    evidence_record("a2"),
                    evidence_record("a3", carrier=carrier),
                ]

                with self.assertRaisesRegex(
                    product_state.ProductStateError, r"record 3 field carrier"
                ):
                    product_state.validate_evidence_records(
                        records, self.ideas / "evidence-registry.yaml"
                    )

    def test__validate_evidence_records__repeated_id__names_repeated_record(
        self,
    ) -> None:
        records = [
            evidence_record("a1"),
            evidence_record("a2"),
            evidence_record("a1"),
            evidence_record("a2"),
        ]

        with self.assertRaisesRegex(
            product_state.ProductStateError, r"record 3 field id"
        ):
            product_state.validate_evidence_records(
                records, self.ideas / "evidence-registry.yaml"
            )

    def test__parse_evidence_registry__valid_block__returns_literal_scalar_content(
        self,
    ) -> None:
        body = "\n".join(
            (
                "# Документ",
                "```yaml evidence-registry",
                "- id: E1",
                "  type: наблюдение",
                "  claim: |",
                "    Труба |, двоеточие: кавычки \"\" и решётка # остаются.",
                "",
                "    Закрывающий забор ``` остаётся содержимым.",
                "  carrier: |",
                "    Носитель с обратными кавычками ```.",
                "```",
            )
        )

        records = product_state.parse_evidence_registry(
            body, self.ideas / "registry.md"
        )

        self.assertEqual(
            records,
            [
                {
                    "id": "E1",
                    "type": "наблюдение",
                    "claim": (
                        "Труба |, двоеточие: кавычки \"\" и решётка # остаются."
                        "\n\nЗакрывающий забор ``` остаётся содержимым."
                    ),
                    "carrier": "Носитель с обратными кавычками ```.",
                }
            ],
        )

    def test__parse_evidence_registry__invalid_block_boundary__names_physical_line(
        self,
    ) -> None:
        cases = (
            ("missing", "# Документ\n", r"line 1.*evidence-registry"),
            (
                "duplicate",
                "```yaml evidence-registry\n```\n```yaml evidence-registry\n```\n",
                r"line 3.*second",
            ),
            (
                "unclosed",
                "```yaml evidence-registry\n- id: E1\n",
                r"line 1.*closing",
            ),
        )

        for name, body, expected in cases:
            with self.subTest(case=name):
                with self.assertRaisesRegex(product_state.ProductStateError, expected):
                    product_state.parse_evidence_registry(
                        body, self.ideas / "registry.md"
                    )

    def test__parse_evidence_registry__invalid_yaml_subset__names_physical_line(
        self,
    ) -> None:
        cases = (
            ("tab", "- id: E1\n\ttype: наблюдение", r"line 4.*tab"),
            ("indent", "- id: E1\n   type: наблюдение", r"line 4.*indent"),
            ("record-indent", " - id: E1", r"line 3.*indent"),
            ("outside", "  type: наблюдение", r"line 3.*outside record"),
            ("empty", "- id: E1\n  type:", r"line 4.*without a value"),
            ("duplicate", "- id: E1\n  id: E2", r"line 4.*record 1.*id"),
            ("junk", "- id: E1\nplain: text", r"line 4.*expected"),
            ("flow-map", "- id: { E1 }", r"line 3.*unsupported"),
            ("flow-list", "- id: [E1]", r"line 3.*unsupported"),
            ("anchor", "- id: &first E1", r"line 3.*unsupported"),
            ("alias", "- id: *first", r"line 3.*unsupported"),
            ("tag", "- id: !identifier E1", r"line 3.*unsupported"),
            ("nested-list", "- id: E1\n  - type: наблюдение", r"line 4.*field"),
            ("comment", "- id: E1\n# пояснение", r"line 4.*expected"),
            ("unknown", "- id: E1\n  extra: text", r"line 4.*unsupported field"),
        )

        for name, registry, expected in cases:
            with self.subTest(case=name):
                body = f"# Документ\n```yaml evidence-registry\n{registry}\n```\n"
                with self.assertRaisesRegex(product_state.ProductStateError, expected):
                    product_state.parse_evidence_registry(
                        body, self.ideas / "registry.md"
                    )

    def test__parse_evidence_registry__unsupported_block_scalar_indicator__names_indicator_and_allowed_value(
        self,
    ) -> None:
        indicators = (">", "|-", "|+", ">-")
        for indicator in indicators:
            for continued in (False, True):
                with self.subTest(indicator=indicator, continued=continued):
                    continuation = (
                        "\n    Текст утверждения автора." if continued else ""
                    )
                    body = (
                        "# Документ\n"
                        "```yaml evidence-registry\n"
                        "- id: E1\n"
                        "  type: наблюдение\n"
                        f"  claim: {indicator}{continuation}\n"
                        "  carrier: носитель\n"
                        "```\n"
                    )

                    with self.assertRaises(product_state.ProductStateError) as caught:
                        product_state.parse_evidence_registry(
                            body, self.ideas / "registry.md"
                        )

                    message = str(caught.exception)
                    self.assertIn("line 5", message)
                    self.assertIn(indicator, message)
                    self.assertIn("allowed indicator '|'", message)

    def test__parse_evidence_registry__ordinary_value_starting_with_indicator_symbols__preserves_value(
        self,
    ) -> None:
        cases = ("> 5 попыток подряд", "|зачёркнутое| название")
        for claim in cases:
            with self.subTest(claim=claim):
                body = (
                    "# Документ\n"
                    "```yaml evidence-registry\n"
                    "- id: E1\n"
                    "  type: наблюдение\n"
                    f"  claim: {claim}\n"
                    "  carrier: носитель\n"
                    "```\n"
                )

                records = product_state.parse_evidence_registry(
                    body, self.ideas / "registry.md"
                )

                self.assertEqual(records[0]["claim"], claim)

    def test__parse_evidence_registry__invalid_record_composition__names_record_field_and_line(
        self,
    ) -> None:
        cases = (
            (
                "missing-id",
                "- type: наблюдение\n  claim: утверждение\n  carrier: носитель",
                r"line 3.*record 1 field id is missing",
            ),
            (
                "missing-type",
                "- id: E1\n  claim: утверждение\n  carrier: носитель",
                r"line 3.*record 1 field type is missing",
            ),
            (
                "missing-claim",
                "- id: E1\n  type: наблюдение\n  carrier: носитель",
                r"line 3.*record 1 field claim is missing",
            ),
            (
                "missing-carrier",
                "- id: E1\n  type: наблюдение\n  claim: утверждение",
                r"line 3.*record 1 field carrier is missing",
            ),
            (
                "unknown-type",
                "- id: E1\n  type: мнение\n  claim: утверждение\n  carrier: носитель",
                r"line 4.*record 1 field type",
            ),
            (
                "empty-id",
                "- id:   \n  type: наблюдение\n  claim: утверждение\n  carrier: носитель",
                r"line 3.*without a value",
            ),
            (
                "invalid-id",
                "- id: 1E\n  type: наблюдение\n  claim: утверждение\n  carrier: носитель",
                r"line 3.*record 1 field id.*form",
            ),
            (
                "empty-claim",
                "- id: E1\n  type: наблюдение\n  claim: |\n  carrier: носитель",
                r"line 5.*record 1 field claim.*non-empty",
            ),
            (
                "empty-carrier",
                "- id: E1\n  type: наблюдение\n  claim: утверждение\n  carrier: |",
                r"line 6.*record 1 field carrier.*non-empty",
            ),
        )

        for name, registry, expected in cases:
            with self.subTest(case=name):
                body = f"# Документ\n```yaml evidence-registry\n{registry}\n```\n"
                with self.assertRaisesRegex(product_state.ProductStateError, expected):
                    product_state.parse_evidence_registry(
                        body, self.ideas / "registry.md"
                    )

    def test__parse_evidence_registry__repeated_id__names_both_id_lines_and_first_record(
        self,
    ) -> None:
        body = "\n".join(
            (
                "# Документ",
                "```yaml evidence-registry",
                "- id: E1",
                "  type: наблюдение",
                "  claim: первое",
                "  carrier: первый носитель",
                "- id: E1",
                "  type: допущение",
                "  claim: второе",
                "  carrier: второй носитель",
                "```",
            )
        )

        with self.assertRaisesRegex(
            product_state.ProductStateError, r"line 7.*record 1.*line 3"
        ):
            product_state.parse_evidence_registry(body, self.ideas / "registry.md")

    def test__validate_evidence_records__id_claim_and_carrier_require_strings_and_content(
        self,
    ) -> None:
        cases = (
            ("id-type", evidence_record(identifier=cast(str, 1)), "field id"),
            ("type-type", evidence_record(record_type=cast(str, 1)), "field type"),
            ("id-form", evidence_record(identifier="1E"), "field id"),
            ("claim-type", evidence_record(claim=cast(str, 1)), "field claim"),
            ("claim-empty", evidence_record(claim="  "), "field claim"),
            ("carrier-type", evidence_record(carrier=cast(str, 1)), "field carrier"),
        )

        for name, record, expected in cases:
            with self.subTest(case=name):
                with self.assertRaisesRegex(product_state.ProductStateError, expected):
                    product_state.validate_evidence_records(
                        [record], self.ideas / "registry.md"
                    )

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
                    "--analysis-by",
                    "planner:product-baseline",
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

    def test__sync__without_analysis_by__argparse_rejects_and_keeps_body(self) -> None:
        idea = self.idea_path()
        prepared = self.prepared_body(idea, "# Idea\n")

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
            "open",
        )

        self.assertEqual(result.returncode, product_state.EXIT_USAGE)
        self.assertIn("--analysis-by", result.stderr)
        self.assertTrue(prepared.exists())
        self.assertFalse(idea.exists())

    def test__sync__empty_analysis_by__rejects_before_consuming_body(self) -> None:
        for analysis_by in ("", "   "):
            with self.subTest(analysis_by=repr(analysis_by)):
                idea = self.idea_path(f"empty-analysis-{len(analysis_by)}")
                prepared = self.prepared_body(idea, "# Idea\n")

                result = self.run_cli(
                    "sync",
                    "idea",
                    str(idea),
                    "--body-file",
                    str(prepared),
                    "--semantic-change",
                    "yes",
                    "--analysis-by",
                    analysis_by,
                    "--stage",
                    "exploring",
                    "--outcome",
                    "open",
                )

                self.assertEqual(result.returncode, 3)
                self.assertIn("analysis_by must be a non-empty string", result.stderr)
                self.assertTrue(prepared.exists())
                self.assertFalse(idea.exists())
                prepared.unlink()

    def test__sync__invalid_kind_field_value__rejects_before_consuming_body(
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
                "idea stage",
                "idea",
                self.idea_path(),
                {"stage": "guessed", "outcome": "open"},
                "stage must be one of",
            ),
            (
                "idea outcome",
                "idea",
                self.idea_path(),
                {"stage": "exploring", "outcome": "guessed"},
                "outcome must be one of",
            ),
            (
                "epic stage",
                "epic",
                epic,
                {"stage": "guessed"},
                "stage must be one of",
            ),
            (
                "roadmap state",
                "roadmap",
                epic_directory / "ROADMAP.md",
                {"parent": epic, "state": "guessed"},
                "state must be one of",
            ),
            (
                "feature readiness",
                "feature",
                feature_directory / "README.md",
                {"readiness": "guessed"},
                "readiness must be one of",
            ),
        )

        for name, kind, target, fields, expected in cases:
            with self.subTest(case=name):
                body = complete_body(kind, f"# {kind.title()}\n")
                previous = target.read_bytes() if target.exists() else None

                result, prepared = self.sync_prepared(kind, target, body, **fields)

                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn(expected, result.stderr)
                self.assertTrue(prepared.exists())
                self.assertEqual(prepared.read_text(), body)
                if previous is None:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), previous)
                prepared.unlink()

    def test__validate_kind_fields__multiline_values__return_invalid(self) -> None:
        cases = (
            ("idea", "stage"),
            ("idea", "outcome"),
            ("epic", "stage"),
            ("roadmap", "state"),
            ("feature", "readiness"),
        )
        injected = "current\nstatus: stale"

        for kind, field in cases:
            with self.subTest(kind=kind, field=field):
                path = self.product_path(kind)
                path.write_text(product_document(kind))
                metadata = product_state.read_document(path).metadata
                metadata[field] = injected

                with self.assertRaisesRegex(
                    product_state.ProductStateError, f"{field} must be one of"
                ):
                    product_state._VALIDATORS[kind](metadata, path)

    def test__sync__multiline_analysis_by__injects_no_field_and_reads_back(self) -> None:
        hostile = 'planner:product-baseline\nstatus: stale'
        body = complete_body("idea", "# Idea\n")
        prepared = self.prepared_body(self.idea_path(), body)

        result = self.run_cli(
            "sync",
            "idea",
            str(self.idea_path()),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
            "--analysis-by",
            hostile,
            "--stage",
            "exploring",
            "--outcome",
            "open",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(prepared.exists())
        document = product_state.read_document(self.idea_path())
        self.assertEqual(document.metadata["analysis_by"], hostile)
        self.assertNotIn("duplicate frontmatter field", result.stderr)
        self.assertNotIn("\nstatus: stale\n", document.source)

    def test__sync__simple_analysis_by__round_trips_unquoted(self) -> None:
        body = "# Idea\n"

        self.sync_idea(body, analysis_by="planner:product-baseline")

        document = product_state.read_document(self.idea_path())
        self.assertIn("analysis_by: planner:product-baseline\n", document.source)
        self.assertEqual(document.metadata["analysis_by"], "planner:product-baseline")

    def test__sync__quoted_analysis_by__reads_back_identically(self) -> None:
        idea = self.idea_path("quoted")
        body = complete_body("idea", "# Idea\n")
        prepared = self.prepared_body(idea, body)

        result = self.run_cli(
            "sync",
            "idea",
            str(idea),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
            "--analysis-by",
            '  spaced provider  ',
            "--stage",
            "exploring",
            "--outcome",
            "open",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        document = product_state.read_document(idea)
        self.assertIn(
            'analysis_by: "  spaced provider  "\n', document.source
        )
        self.assertEqual(document.metadata["analysis_by"], "  spaced provider  ")

    def registry_body(self, duty: str = "") -> str:
        return (
            "```yaml evidence-registry\n"
            "- id: E1\n"
            "  type: наблюдение\n"
            "  claim: владелец теряет элементы при массовом удалении\n"
            "  carrier: реплика владельца в обсуждении\n"
            "```\n\n"
            f"{duty}"
        )

    def sync_prepared(
        self,
        kind: str,
        target: Path,
        body: str,
        **fields: str | Path,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        prepared = self.prepared_body(target, body)
        arguments = [
            "sync",
            kind,
            str(target),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
            "--analysis-by",
            "planner:product-baseline",
        ]
        if "parent" in fields:
            arguments.extend(("--parent", str(fields.pop("parent"))))
        for field, value in fields.items():
            arguments.extend((f"--{field.replace('_', '-')}", str(value)))
        return self.run_cli(*arguments), prepared

    def test__sync__prepared_body_replaced_after_validation__writes_verified_body(
        self,
    ) -> None:
        cases = (
            ("idea", self.idea_path(), {"stage": "exploring", "outcome": "open"}),
            (
                "epic",
                self.epics / "EPIC-0001-provider-routing" / "EPIC.md",
                {"stage": "active"},
            ),
        )
        swapped_body = "# Body swapped after validation\n"

        for kind, target, fields in cases:
            with self.subTest(kind=kind):
                target.parent.mkdir(parents=True, exist_ok=True)
                verified_body = complete_body(kind, f"# {kind.title()}\n")
                prepared = self.prepared_body(target, verified_body)
                original_prevalidation = product_state.prevalidate_prepared_body

                def validate_and_replace(*args: object) -> str:
                    body = original_prevalidation(*args)
                    prepared.write_text(swapped_body)
                    return body

                with mock.patch.object(
                    product_state,
                    "prevalidate_prepared_body",
                    side_effect=validate_and_replace,
                ) as prevalidation:
                    if kind == "idea":
                        result = product_state.sync_idea_document(
                            target,
                            prepared,
                            True,
                            "planner:product-baseline",
                            fields["stage"],
                            fields["outcome"],
                            None,
                        )
                    else:
                        result = product_state.sync_linked_document(
                            kind,
                            target,
                            prepared,
                            True,
                            "planner:product-baseline",
                            None,
                            fields["stage"],
                        )

                self.assertEqual(result, 0)
                prevalidation.assert_called_once()
                self.assertFalse(prepared.exists())
                self.assertEqual(product_state.read_document(target).body, verified_body)

    def duty_cases(
        self,
    ) -> tuple[tuple[str, Path, dict[str, str | Path], str], ...]:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        self.sync_product("epic", epic, "# Epic\n", stage="shaping")
        feature_directory = self.features / "FEAT-0001-provider-routing"
        feature_directory.mkdir()
        return (
            (
                "idea",
                self.idea_path(),
                {"stage": "resolved", "outcome": "decision"},
                "## Решение\nИсход: decision\nОснование: [E1].\n",
            ),
            (
                "epic",
                epic,
                {"stage": "active"},
                "## Принятые решения\n"
                "| Вопрос | Выбрано | Отклонено | Основание | Обратимость |\n"
                "|---|---|---|---|---|\n"
                "| Срез | один | два | [E1] | обратимо |\n",
            ),
            (
                "roadmap",
                epic_directory / "ROADMAP.md",
                {"parent": epic, "state": "active"},
                "## Основание порядка\nПорядок опирается на [E1].\n",
            ),
            (
                "feature",
                feature_directory / "README.md",
                {"readiness": "ready"},
                "## Договор взаимодействия\n"
                "Актор вызывает действие и видит результат [E1].\n",
            ),
        )

    def test__sync__template_layout__registry_before_sections__accepted_for_every_kind(
        self,
    ) -> None:
        for kind, target, fields, duty in self.duty_cases():
            with self.subTest(kind=kind):
                body = f"# {kind.title()}\n\n{self.registry_body(duty)}"

                self.sync_product(kind, target, body, **fields)

                document = product_state.read_document(target)
                self.assertEqual(document.body, body)

    def test__sync__reversed_layout__sections_before_registry__accepted_for_every_kind(
        self,
    ) -> None:
        for kind, target, fields, duty in self.duty_cases():
            with self.subTest(kind=kind):
                body = f"# {kind.title()}\n\n{duty}\n{self.registry_body()}"

                self.sync_product(kind, target, body, **fields)

                document = product_state.read_document(target)
                self.assertEqual(document.body, body)

    def test__sync__epic_filled_decision_table_after_registry__without_reference__rejected(
        self,
    ) -> None:
        epic = self.duty_cases()[1][1]
        body = (
            "# Epic\n\n"
            f"{self.registry_body(
                '## Принятые решения\n'
                '| Вопрос | Выбрано | Отклонено | Основание | Обратимость |\n'
                '|---|---|---|---|---|\n'
                '| Срез | один | два | интуиция | обратимо |\n'
            )}"
        )

        result, prepared = self.sync_prepared("epic", epic, body, stage="active")

        self.assertEqual(result.returncode, 3)
        self.assertIn(
            "section ## Принятые решения requires an evidence reference",
            result.stderr,
        )
        self.assertTrue(prepared.exists())

    def test__sync__unresolved_reference__names_text_and_keeps_body(self) -> None:
        body = "\n".join(
            (
                "# Замысел",
                "",
                "Вывод опирается на [E9], которого нет в реестре.",
                "",
                "```yaml evidence-registry",
                "- id: E1",
                "  type: наблюдение",
                "  claim: утверждение",
                "  carrier: носитель",
                "```",
            )
        )
        idea = self.idea_path()

        result, prepared = self.sync_prepared(
            "idea", idea, body, stage="exploring", outcome="open"
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("line 3: unresolved evidence reference [E9]", result.stderr)
        self.assertTrue(prepared.exists())
        self.assertFalse(idea.exists())

    def test__sync__duty_section_without_reference__rejected_for_every_kind(
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
                "idea resolved without reference",
                "idea",
                self.idea_path(),
                {"stage": "resolved", "outcome": "decision"},
                "## Решение\nИсход: decision\nОснование: наблюдение автора.\n",
                "section ## Решение requires an evidence reference [id]",
            ),
            (
                "epic decision row without reference",
                "epic",
                epic,
                {"stage": "active"},
                "## Принятые решения\n"
                "| Вопрос | Выбрано | Отклонено | Основание | Обратимость |\n"
                "|---|---|---|---|---|\n"
                "| Срез | один | два | интуиция | обратимо |\n",
                "section ## Принятые решения requires an evidence reference [id]",
            ),
            (
                "roadmap section without reference",
                "roadmap",
                epic_directory / "ROADMAP.md",
                {"parent": epic, "state": "active"},
                "## Основание порядка\nПорядок продиктован сроком.\n",
                "section ## Основание порядка requires an evidence reference [id]",
            ),
            (
                "feature section without reference",
                "feature",
                feature_directory / "README.md",
                {"readiness": "ready"},
                "## Договор взаимодействия\nАктор вызывает действие.\n",
                "section ## Договор взаимодействия requires an evidence reference [id]",
            ),
            (
                "roadmap section missing",
                "roadmap",
                epic_directory / "ROADMAP.md",
                {"parent": epic, "state": "active"},
                "",
                "missing required section ## Основание порядка "
                "with an evidence reference",
            ),
            (
                "feature section missing",
                "feature",
                feature_directory / "README.md",
                {"readiness": "ready"},
                "",
                "missing required section ## Договор взаимодействия "
                "with an evidence reference",
            ),
        )

        for name, kind, target, fields, duty, expected in cases:
            with self.subTest(case=name):
                body = f"# {kind.title()}\n\n{self.registry_body(duty)}"
                previous = target.read_bytes() if target.exists() else None

                result, prepared = self.sync_prepared(kind, target, body, **fields)

                self.assertEqual(result.returncode, 3)
                self.assertIn(expected, result.stderr)
                self.assertTrue(prepared.exists())
                if previous is None:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), previous)
                prepared.unlink()

    def test__sync__markdown_link__is_not_a_registry_reference(self) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        self.sync_product("epic", epic, "# Epic\n", stage="shaping")
        roadmap = epic_directory / "ROADMAP.md"
        body = (
            "# Roadmap\n\n"
            f"{self.registry_body(
                '## Основание порядка\n'
                'Описание в [Wiki](https://example.com) и [E1](./doc.md).\n'
            )}"
        )

        result, prepared = self.sync_prepared(
            "roadmap", roadmap, body, parent=epic, state="active"
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn(
            "section ## Основание порядка requires an evidence reference", result.stderr
        )
        self.assertNotIn("unresolved evidence reference", result.stderr)
        self.assertTrue(prepared.exists())
        self.assertFalse(roadmap.exists())

    def test__sync__early_stage_and_empty_decision_table__create_no_duty(
        self,
    ) -> None:
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        cases = (
            (
                "idea exploring has no decision section",
                "idea",
                self.idea_path(),
                {"stage": "exploring", "outcome": "open"},
                "",
            ),
            (
                "epic decision table is empty",
                "epic",
                epic,
                {"stage": "shaping"},
                "## Принятые решения\n"
                "| Вопрос | Выбрано | Отклонено | Основание | Обратимость |\n"
                "|---|---|---|---|---|\n",
            ),
        )

        for name, kind, target, fields, duty in cases:
            with self.subTest(case=name):
                body = f"# {kind.title()}\n\n{self.registry_body(duty)}"

                self.sync_product(kind, target, body, **fields)

                document = product_state.read_document(target)
                self.assertEqual(document.body, body)

    def test__sync__registry_rejection__keeps_prepared_body_and_target(
        self,
    ) -> None:
        idea = self.idea_path()
        self.sync_idea()
        before = idea.read_bytes()
        cases = (
            (
                "block boundary",
                "# Замысел\n\n```yaml evidence-registry\n- id: E1\n",
                "closing fence is required",
            ),
            (
                "yaml syntax",
                "# Замысел\n\n```yaml evidence-registry\n"
                "- id: E1\n\ttype: наблюдение\n```\n",
                "tab indentation is unsupported",
            ),
            (
                "record composition",
                "# Замысел\n\n```yaml evidence-registry\n"
                "- id: E1\n  claim: утверждение\n  carrier: носитель\n```\n",
                "field type is missing",
            ),
            (
                "reference",
                f"# Замысел\n\n{self.registry_body('Вывод опирается на [E9].\n')}",
                "line 10: unresolved evidence reference [E9]",
            ),
        )

        for name, body, expected in cases:
            with self.subTest(case=name):
                result, prepared = self.sync_prepared(
                    "idea", idea, body, stage="exploring", outcome="open"
                )

                self.assertEqual(result.returncode, 3)
                self.assertIn(expected, result.stderr)
                self.assertTrue(prepared.exists())
                self.assertEqual(idea.read_bytes(), before)
                prepared.unlink()

    def test__sync__new_idea__writes_version_one(self) -> None:
        body = complete_body("idea", "# Idea\n")

        result = self.sync_idea(body)

        self.assertEqual(json.loads(result.stdout)["version"], 1)
        self.assert_product_document(
            self.idea_path(),
            {
                "plan_type": "idea",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(body),
                "analysis_by": "planner:product-baseline",
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
        changed_body = complete_body("idea", "# Idea\n\n")

        self.sync_idea(changed_body, semantic_change="no")

        self.assert_product_document(
            self.idea_path(),
            {
                "plan_type": "idea",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(changed_body),
                "analysis_by": "planner:product-baseline",
                "stage": "exploring",
                "outcome": "open",
            },
            changed_body,
        )

    def test__sync__epic_with_origin__records_parent_snapshot(self) -> None:
        idea_body = complete_body("idea", "# Idea\n")
        self.sync_idea(idea_body)
        epic_directory = self.epics / "EPIC-0001-provider-routing"
        epic_directory.mkdir()
        epic = epic_directory / "EPIC.md"
        epic_body = complete_body("epic", "# Epic\n")

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
                "analysis_by": "planner:product-baseline",
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
        epic_body = complete_body("epic", "# Epic\n")
        self.sync_product("epic", epic, epic_body, stage="shaping")
        roadmap = epic_directory / "ROADMAP.md"
        roadmap_body = complete_body("roadmap", "# Roadmap\n")

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
                "analysis_by": "planner:product-baseline",
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
            "--analysis-by",
            "planner:product-baseline",
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
        epic_body = complete_body("epic", "# Epic\n")
        self.sync_product("epic", epic, epic_body, stage="shaping")
        feature_directory = self.features / "FEAT-0001-provider-routing"
        feature_directory.mkdir()
        feature = feature_directory / "README.md"
        feature_body = complete_body("feature", "# Feature\n")

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
                "analysis_by": "planner:product-baseline",
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
                changed_body = complete_body(kind, f"# Changed {kind.title()}\n")
                prepared = self.prepared_body(path, changed_body)

                result = self.run_cli(
                    "sync",
                    kind,
                    str(path),
                    "--body-file",
                    str(prepared),
                    "--semantic-change",
                    "no",
                    "--analysis-by",
                    "planner:product-baseline",
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
        resolved_body = complete_body("idea", "# Resolved idea\n", "resolved")
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
        epic_body = complete_body("epic", "# Epic\n")
        self.sync_product(
            "epic", epic, epic_body, parent=idea, stage="shaping"
        )
        epic_before_roadmap = self.inspect_product(epic)
        epic_bytes = epic.read_bytes()
        roadmap = epic_directory / "ROADMAP.md"
        roadmap_body = complete_body("roadmap", "# Roadmap\n")
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
            "--analysis-by", "planner:product-baseline",
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
                    "--analysis-by", "planner:product-baseline",
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
        roadmap_body = complete_body("roadmap", "# Roadmap\nKeep this body.\n")
        self.sync_product(
            "roadmap", roadmap, roadmap_body, parent=epic, state="active"
        )
        roadmap_before = roadmap.read_bytes()
        roadmap_state_before = self.inspect_product(roadmap)

        changed_epic_body = complete_body("epic", "# Changed epic\n")
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
        prepared = self.prepared_body(
            idea, complete_body("idea", "# Invalid replacement\n")
        )

        result = self.run_cli(
            "sync",
            "idea",
            str(idea),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
            "--analysis-by",
            "planner:product-baseline",
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
