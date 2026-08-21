import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

import plan_state


SCRIPT = Path(__file__).with_name("plan_state.py")


def body_hash(body: str) -> str:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode()).hexdigest()


class PlanStateCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.architecture = self.root / "ARCHITECTURE.md"
        self.execution = self.root / "PLANNER_EXECUTION.md"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def prepared_body(self, target: Path, body: str) -> Path:
        prepared = target.with_name(f"{target.name}.prepared")
        prepared.write_text(body)
        return prepared

    def sync_architecture(
        self, body: str = "# Architecture\n", semantic_change: str = "yes"
    ) -> None:
        prepared = self.prepared_body(self.architecture, body)
        result = self.run_cli(
            "sync-architecture",
            str(self.architecture),
            "--body-file",
            str(prepared),
            "--semantic-change",
            semantic_change,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(prepared.exists())

    def sync_execution(
        self, body: str = "# Execution\n", semantic_change: str = "yes"
    ) -> None:
        prepared = self.prepared_body(self.execution, body)
        result = self.run_cli(
            "sync-execution",
            str(self.execution),
            "--body-file",
            str(prepared),
            "--architecture",
            str(self.architecture),
            "--semantic-change",
            semantic_change,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(prepared.exists())

    def write_valid_architecture(self, body: str = "# Original\n") -> bytes:
        content = plan_state.render_architecture(1, body_hash(body), body)
        self.architecture.write_text(content)
        return content.encode()

    def assert_plan_document(
        self,
        path: Path,
        expected_metadata: dict[str, object],
        expected_body: str,
    ) -> plan_state.PlanDocument:
        document = plan_state.read_document(path)
        self.assertTrue(document.has_frontmatter)
        self.assertEqual(document.metadata, expected_metadata)
        self.assertEqual(document.body, expected_body)
        return document

    def test__inspect__legacy_architecture__reports_version_zero_without_write(self) -> None:
        original = "# Legacy architecture\n"
        self.architecture.write_text(original)

        result = self.run_cli("inspect", str(self.architecture))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "content_sha256": body_hash(original),
                "path": str(self.architecture.resolve()),
                "plan_type": "architecture",
                "status": "current",
                "version": 0,
            },
        )
        self.assertEqual(self.architecture.read_text(), original)

    def test__inspect__legacy_markdown_separator__reports_version_zero_without_write(self) -> None:
        original = "---\n\n# Legacy architecture\n"
        self.architecture.write_text(original)

        result = self.run_cli("inspect", str(self.architecture))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["version"], 0)
        self.assertEqual(self.architecture.read_text(), original)

    def test__sync_architecture__new_document__writes_version_one_and_hash(self) -> None:
        body = "# Architecture\n"
        prepared = self.prepared_body(self.architecture, body)

        result = self.run_cli(
            "sync-architecture",
            str(self.architecture),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_plan_document(
            self.architecture,
            {
                "plan_type": "architecture",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(body),
            },
            body,
        )
        self.assertFalse(prepared.exists())

    def test__sync_architecture__unchanged_document__is_idempotent(self) -> None:
        body = "# Architecture\n"
        self.sync_architecture(body)
        original = self.architecture.read_bytes()

        self.sync_architecture(body, semantic_change="no")

        self.assertEqual(self.architecture.read_bytes(), original)

    def test__sync_architecture__semantic_body_change__increments_version(self) -> None:
        self.sync_architecture()
        changed_body = "# Changed architecture\n"

        self.sync_architecture(changed_body)

        self.assert_plan_document(
            self.architecture,
            {
                "plan_type": "architecture",
                "version": 2,
                "status": "current",
                "content_sha256": body_hash(changed_body),
            },
            changed_body,
        )

    def test__sync_architecture__nonsemantic_body_change__preserves_version(self) -> None:
        self.sync_architecture()
        changed_body = "# Architecture\n\n"

        self.sync_architecture(changed_body, semantic_change="no")

        self.assert_plan_document(
            self.architecture,
            {
                "plan_type": "architecture",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(changed_body),
            },
            changed_body,
        )

    def test__sync_execution__new_document__records_architecture_state(self) -> None:
        architecture_body = "# Architecture\n"
        self.sync_architecture(architecture_body)
        execution_body = "# Execution\n"
        prepared = self.prepared_body(self.execution, execution_body)

        result = self.run_cli(
            "sync-execution",
            str(self.execution),
            "--body-file",
            str(prepared),
            "--architecture",
            str(self.architecture),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_plan_document(
            self.execution,
            {
                "plan_type": "execution",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(execution_body),
                "architecture": {
                    "path": "./ARCHITECTURE.md",
                    "version": 1,
                    "content_sha256": body_hash(architecture_body),
                },
            },
            execution_body,
        )
        self.assertFalse(prepared.exists())

    def test__sync_execution__quoted_architecture_path__round_trips(self) -> None:
        architecture = self.root / 'Architecture "draft".md '
        architecture_body = "# Architecture\n"
        architecture.write_text(
            plan_state.render_architecture(
                1, body_hash(architecture_body), architecture_body
            )
        )
        execution_body = "# Execution\n"
        prepared = self.prepared_body(self.execution, execution_body)

        result = self.run_cli(
            "sync-execution",
            str(self.execution),
            "--body-file",
            str(prepared),
            "--architecture",
            str(architecture),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        expected_path = './Architecture "draft".md '
        self.assert_plan_document(
            self.execution,
            {
                "plan_type": "execution",
                "version": 1,
                "status": "current",
                "content_sha256": body_hash(execution_body),
                "architecture": {
                    "path": expected_path,
                    "version": 1,
                    "content_sha256": body_hash(architecture_body),
                },
            },
            execution_body,
        )
        check = self.run_cli("check", str(self.execution))
        self.assertEqual(check.returncode, 0, check.stderr)

    def test__sync_execution__unchanged_document__is_idempotent(self) -> None:
        self.sync_architecture()
        body = "# Execution\n"
        self.sync_execution(body)
        original = self.execution.read_bytes()

        self.sync_execution(body, semantic_change="no")

        self.assertEqual(self.execution.read_bytes(), original)

    def test__check__matching_documents__returns_current(self) -> None:
        self.sync_architecture()
        self.sync_execution()

        result = self.run_cli("check", str(self.execution))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "current")

    def test__check__architecture_body_changed_directly__returns_stale(self) -> None:
        self.sync_architecture()
        self.sync_execution()
        self.architecture.write_text(
            self.architecture.read_text().replace(
                "# Architecture\n", "# Changed directly\n"
            )
        )

        result = self.run_cli("check", str(self.execution))

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "stale")
        self.assertEqual(payload["reason"], "architecture content hash mismatch")

    def test__check__mark_stale__preserves_execution_body_and_version(self) -> None:
        self.sync_architecture()
        execution_body = "# Execution\nKeep this body.\n"
        self.sync_execution(execution_body)
        self.architecture.write_text(
            self.architecture.read_text().replace(
                "# Architecture\n", "# Changed directly\n"
            )
        )

        result = self.run_cli("check", str(self.execution), "--mark-stale")

        self.assertEqual(result.returncode, 2)
        self.assert_plan_document(
            self.execution,
            {
                "plan_type": "execution",
                "version": 1,
                "status": "stale",
                "content_sha256": body_hash(execution_body),
                "architecture": {
                    "path": "./ARCHITECTURE.md",
                    "version": 1,
                    "content_sha256": body_hash("# Architecture\n"),
                },
            },
            execution_body,
        )

    def test__check__already_stale__preserves_original_mismatch_reason(self) -> None:
        self.sync_architecture()
        self.sync_execution()
        self.architecture.write_text(
            self.architecture.read_text().replace(
                "# Architecture\n", "# Changed directly\n"
            )
        )
        first = self.run_cli("check", str(self.execution), "--mark-stale")
        self.assertEqual(first.returncode, 2)

        second = self.run_cli("check", str(self.execution))

        self.assertEqual(second.returncode, 2)
        self.assertEqual(
            json.loads(second.stdout)["reason"],
            "architecture content hash mismatch",
        )

    def test__validate_architecture_target__distinct_path__returns_current(self) -> None:
        source = self.root / "README.md"
        source.write_text("# Requirements\n")

        result = self.run_cli(
            "validate-architecture-target",
            str(self.architecture),
            "--directory",
            str(self.root),
            "--source",
            str(source),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "current")

    def test__validate_architecture_target__wrong_name__returns_invalid(self) -> None:
        target = self.root / "README.md"

        result = self.run_cli(
            "validate-architecture-target",
            str(target),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("ARCHITECTURE.md", result.stderr)

    def test__validate_architecture_target__symlink_outside_directory__returns_invalid(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        external = outside / "ARCHITECTURE.md"
        external.write_text("# External\n")
        self.architecture.symlink_to(external)

        result = self.run_cli(
            "validate-architecture-target",
            str(self.architecture),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("symbolic link", result.stderr)

    def test__validate_architecture_target__hard_link_to_source__returns_invalid(self) -> None:
        source = self.root / "README.md"
        source.write_text("# Requirements\n")
        os.link(source, self.architecture)

        result = self.run_cli(
            "validate-architecture-target",
            str(self.architecture),
            "--directory",
            str(self.root),
            "--source",
            str(source),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("hard link", result.stderr)

    def test__validate_execution_target__same_path__returns_invalid(self) -> None:
        result = self.run_cli(
            "validate-execution-target",
            str(self.architecture),
            "--architecture",
            str(self.architecture),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("different files", result.stderr)

    def test__validate_execution_target__symlink_alias__returns_invalid(self) -> None:
        self.architecture.write_text("# Architecture\n")
        self.execution.symlink_to(self.architecture)

        result = self.run_cli(
            "validate-execution-target",
            str(self.execution),
            "--architecture",
            str(self.architecture),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("symbolic link", result.stderr)

    def test__validate_execution_target__hard_link_alias__returns_invalid(self) -> None:
        self.architecture.write_text("# Architecture\n")
        os.link(self.architecture, self.execution)

        result = self.run_cli(
            "validate-execution-target",
            str(self.execution),
            "--architecture",
            str(self.architecture),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("hard link", result.stderr)

    def test__validate_execution_target__distinct_paths__returns_current(self) -> None:
        result = self.run_cli(
            "validate-execution-target",
            str(self.execution),
            "--architecture",
            str(self.architecture),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "current")
        self.assertEqual(payload["execution_path"], str(self.execution.resolve()))
        self.assertEqual(
            payload["architecture_path"], str(self.architecture.resolve())
        )

    def test__validate_execution_target__architecture_in_other_directory__returns_invalid(self) -> None:
        other = self.root / "other"
        other.mkdir()
        architecture = other / "ARCHITECTURE.md"

        result = self.run_cli(
            "validate-execution-target",
            str(self.execution),
            "--architecture",
            str(architecture),
            "--directory",
            str(self.root),
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("same directory", result.stderr)

    def test__sync_execution__same_path_as_architecture__returns_invalid(self) -> None:
        self.sync_architecture()
        prepared = self.prepared_body(self.execution, "# Execution\n")

        result = self.run_cli(
            "sync-execution",
            str(self.architecture),
            "--body-file",
            str(prepared),
            "--architecture",
            str(self.architecture),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("different files", result.stderr)

    def test__sync_architecture__target_as_body_file__preserves_target(self) -> None:
        original = self.write_valid_architecture()

        result = self.run_cli(
            "sync-architecture",
            str(self.architecture),
            "--body-file",
            str(self.architecture),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("prepared body", result.stderr)
        self.assertEqual(self.architecture.read_bytes(), original)

    def test__sync_architecture__arbitrary_neighbor_body_file__preserves_file(self) -> None:
        source = self.root / "README.md"
        original = b"# Requirements\n"
        source.write_bytes(original)

        result = self.run_cli(
            "sync-architecture",
            str(self.architecture),
            "--body-file",
            str(source),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("ARCHITECTURE.md.prepared", result.stderr)
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(self.architecture.exists())

    def test__sync_architecture__symlink_body_file__returns_invalid(self) -> None:
        source = self.root / "body.md"
        source.write_text("# Changed\n")
        prepared = self.architecture.with_name("ARCHITECTURE.md.prepared")
        prepared.symlink_to(source)

        result = self.run_cli(
            "sync-architecture",
            str(self.architecture),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("symbolic link", result.stderr)
        self.assertFalse(self.architecture.exists())

    def test__sync_architecture__hard_link_body_file__returns_invalid(self) -> None:
        source = self.root / "body.md"
        source.write_text("# Changed\n")
        prepared = self.architecture.with_name("ARCHITECTURE.md.prepared")
        os.link(source, prepared)

        result = self.run_cli(
            "sync-architecture",
            str(self.architecture),
            "--body-file",
            str(prepared),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("hard link", result.stderr)
        self.assertFalse(self.architecture.exists())

    def test__sync_architecture__replace_failure__preserves_old_target(self) -> None:
        original = self.write_valid_architecture()
        prepared = self.prepared_body(self.architecture, "# Changed\n")

        with mock.patch.object(
            plan_state.os, "replace", side_effect=PermissionError("denied")
        ):
            with self.assertRaises(plan_state.PlanStateError):
                plan_state.sync_architecture(self.architecture, prepared, True)

        self.assertEqual(self.architecture.read_bytes(), original)
        self.assertFalse(prepared.exists())

    def test__sync_architecture__body_file_delete_failure__preserves_old_target(self) -> None:
        original = self.write_valid_architecture()
        prepared = self.prepared_body(self.architecture, "# Changed\n")

        with mock.patch.object(
            Path, "unlink", side_effect=PermissionError("denied")
        ):
            with self.assertRaises(plan_state.PlanStateError):
                plan_state.sync_architecture(self.architecture, prepared, True)

        self.assertEqual(self.architecture.read_bytes(), original)
        self.assertTrue(prepared.exists())

    def test__sync_execution__invalid_architecture__consumes_prepared_and_preserves_target(self) -> None:
        self.sync_architecture()
        self.sync_execution()
        original = self.execution.read_bytes()
        self.architecture.write_text(
            self.architecture.read_text().replace(
                "plan_type: architecture", "plan_type: unknown"
            )
        )
        prepared = self.prepared_body(self.execution, "# Changed\n")

        result = self.run_cli(
            "sync-execution",
            str(self.execution),
            "--body-file",
            str(prepared),
            "--architecture",
            str(self.architecture),
            "--semantic-change",
            "yes",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("plan_type", result.stderr)
        self.assertFalse(prepared.exists())
        self.assertEqual(self.execution.read_bytes(), original)

    def test__inspect__invalid_frontmatter__returns_invalid(self) -> None:
        self.architecture.write_text(
            "---\nplan_type: unknown\nversion: 1\nstatus: current\n---\n# Body\n"
        )

        result = self.run_cli("inspect", str(self.architecture))

        self.assertEqual(result.returncode, 3)
        self.assertIn("plan_type", result.stderr)

    def test__inspect__duplicate_top_level_field__returns_invalid(self) -> None:
        self.architecture.write_text(
            "---\n"
            "plan_type: architecture\n"
            "version: 1\n"
            "version: 2\n"
            "status: current\n"
            "---\n"
            "# Body\n"
        )

        result = self.run_cli("inspect", str(self.architecture))

        self.assertEqual(result.returncode, 3)
        self.assertIn("duplicate frontmatter field version", result.stderr)

    def test__check__duplicate_nested_field__returns_invalid(self) -> None:
        fingerprint = "1" * 64
        self.execution.write_text(
            "---\n"
            "plan_type: execution\n"
            "version: 1\n"
            "status: current\n"
            f"content_sha256: {fingerprint}\n"
            "architecture:\n"
            '  path: "./ARCHITECTURE.md"\n'
            "  version: 1\n"
            "  version: 2\n"
            f"  content_sha256: {fingerprint}\n"
            "---\n"
            "# Body\n"
        )

        result = self.run_cli("check", str(self.execution))

        self.assertEqual(result.returncode, 3)
        self.assertIn(
            "duplicate frontmatter field architecture.version",
            result.stderr,
        )

    def test__inspect__unicode_version_digit__returns_invalid_without_traceback(self) -> None:
        self.architecture.write_text(
            "---\nplan_type: architecture\nversion: ²\nstatus: current\n---\n# Body\n"
        )

        result = self.run_cli("inspect", str(self.architecture))

        self.assertEqual(result.returncode, 3)
        self.assertIn("version must be a non-negative integer", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test__read_document__all_digit_fingerprint__keeps_string(self) -> None:
        digest = "1" * 64
        self.architecture.write_text(
            "---\n"
            "plan_type: architecture\n"
            "version: 1\n"
            "status: current\n"
            f"content_sha256: {digest}\n"
            "---\n"
            "# Body\n"
        )

        document = plan_state.read_document(self.architecture)

        self.assertEqual(document.metadata["content_sha256"], digest)

    def test__inspect__missing_file__returns_invalid(self) -> None:
        result = self.run_cli("inspect", str(self.architecture))

        self.assertEqual(result.returncode, 3)
        self.assertIn(str(self.architecture), result.stderr)

    def test__check__four_space_nested_field__returns_invalid(self) -> None:
        self.sync_architecture()
        self.sync_execution()
        malformed = self.execution.read_text().replace(
            "  version: 1\n", "    version: 1\n"
        )
        self.execution.write_text(malformed)

        result = self.run_cli("check", str(self.execution))

        self.assertEqual(result.returncode, 3)
        self.assertIn("two-space nesting", result.stderr)

    def test__atomic_write__temp_creation_failure__raises_domain_error(self) -> None:
        self.architecture.write_text("# Original\n")

        with mock.patch.object(
            plan_state.tempfile,
            "mkstemp",
            side_effect=PermissionError("denied"),
        ):
            with self.assertRaises(plan_state.PlanStateError):
                plan_state.atomic_write(self.architecture, "# Changed\n")

        self.assertEqual(self.architecture.read_text(), "# Original\n")

    def test__atomic_write__cleanup_failure__raises_domain_error(self) -> None:
        self.architecture.write_text("# Original\n")

        with mock.patch.object(
            plan_state.os, "replace", side_effect=PermissionError("replace denied")
        ):
            with mock.patch.object(
                Path, "unlink", side_effect=PermissionError("cleanup denied")
            ):
                with self.assertRaises(plan_state.PlanStateError):
                    plan_state.atomic_write(self.architecture, "# Changed\n")

        self.assertEqual(self.architecture.read_text(), "# Original\n")

    def test__check__execution_body_changed_directly__returns_invalid(self) -> None:
        self.sync_architecture()
        self.sync_execution()
        self.execution.write_text(
            self.execution.read_text().replace("# Execution\n", "# Changed directly\n")
        )

        result = self.run_cli("check", str(self.execution))

        self.assertEqual(result.returncode, 3)
        self.assertIn("execution content hash mismatch", result.stderr)

    def test__cli__missing_required_arguments__returns_usage(self) -> None:
        result = self.run_cli("sync-architecture")

        self.assertEqual(result.returncode, 64)
        self.assertIn("usage:", result.stderr)

    def test__reserve_report__fresh_directory__creates_first_number(self) -> None:
        for kind, filename in (
            ("implementation", "IMPLEMENTATION-01.md"),
            ("review", "REVIEW-01.md"),
            ("documentation", "DOCUMENTATION-01.md"),
        ):
            with self.subTest(kind=kind):
                directory = self.root / f"fresh-{kind}"
                directory.mkdir()

                result = self.run_cli(
                    "reserve-report", "--directory", str(directory), "--kind", kind
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertTrue(payload["created"])
                self.assertEqual(payload["kind"], kind)
                self.assertEqual(payload["number"], 1)
                self.assertEqual(payload["path"], str((directory / filename).resolve()))
                self.assertEqual(payload["empties"], [])
                target = directory / filename
                self.assertTrue(target.exists())
                self.assertEqual(target.stat().st_size, 0)

    def test__reserve_report__next_number__is_max_occupied_plus_one(self) -> None:
        cases = [
            (["IMPLEMENTATION-01.md", "IMPLEMENTATION-02.md"], 3, "IMPLEMENTATION-03.md", []),
            (["IMPLEMENTATION-07.md"], 8, "IMPLEMENTATION-08.md", []),
            (["IMPLEMENTATION-09.md", "IMPLEMENTATION-10.md"], 11, "IMPLEMENTATION-11.md", []),
            (["REVIEW-01.md", "REVIEW-05.md"], 6, "REVIEW-06.md", []),
        ]
        for index, (occupied, expected_number, expected_name, _) in enumerate(cases):
            with self.subTest(occupied=occupied):
                directory = self.root / f"numbers-{index}"
                directory.mkdir()
                for name in occupied:
                    (directory / name).write_text("# Report\n")

                result = self.run_cli(
                    "reserve-report", "--directory", str(directory), "--kind",
                    expected_name.split("-")[0].lower(),
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["number"], expected_number)
                self.assertEqual(payload["path"], str((directory / expected_name).resolve()))
                self.assertFalse((directory / "IMPLEMENTATION-0007.md").exists())

    def test__reserve_report__abandoned_reservation__consumes_number_and_is_listed(
        self,
    ) -> None:
        directory = self.root / "feature"
        directory.mkdir()
        abandoned = directory / "IMPLEMENTATION-02.md"
        abandoned.touch()
        abandoned_resolved = abandoned.resolve()

        result = self.run_cli(
            "reserve-report", "--directory", str(directory), "--kind", "implementation"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["number"], 3)
        self.assertEqual(payload["path"], str((directory / "IMPLEMENTATION-03.md").resolve()))
        self.assertEqual(payload["empties"], [str(abandoned_resolved)])

    def test__reserve_report__number_over_99__refuses_loudly_before_creation(self) -> None:
        cases = [
            (["IMPLEMENTATION-99.md"], []),
            (["IMPLEMENTATION-98.md", "IMPLEMENTATION-99.md"], ["IMPLEMENTATION-98.md"]),
        ]
        for index, (occupied, expected_empties) in enumerate(cases):
            with self.subTest(occupied=occupied):
                directory = self.root / f"limit-{index}"
                directory.mkdir()
                for name in occupied:
                    target = directory / name
                    if name in expected_empties:
                        target.touch()
                    else:
                        target.write_text("# Report\n")

                result = self.run_cli(
                    "reserve-report", "--directory", str(directory), "--kind",
                    "implementation",
                )

                self.assertEqual(result.returncode, 3)
                self.assertIn("IMPLEMENTATION-100.md", result.stderr)
                self.assertNotIn("exceeded", result.stderr)
                for name in expected_empties:
                    self.assertIn(str(directory / name), result.stderr)
                listing = sorted(
                    entry.name
                    for entry in directory.iterdir()
                    if entry.name.startswith("IMPLEMENTATION-")
                )
                self.assertEqual(listing, sorted(occupied))

    def test__reserve_report__collision__advances_to_next_number(self) -> None:
        directory = self.root / "feature"
        directory.mkdir()
        (directory / "IMPLEMENTATION-01.md").write_text("# Report\n")
        real_open = os.open
        calls = []

        def conflicting_open(path, flags, mode=0o777):
            if str(path).endswith("IMPLEMENTATION-02.md") and len(calls) < 1:
                calls.append(path)
                raise FileExistsError(errno.EEXIST, "File exists", str(path))
            return real_open(path, flags, mode)

        with mock.patch.object(plan_state.os, "open", side_effect=conflicting_open):
            payload = plan_state.reserve_report(directory, "implementation")

        self.assertEqual(payload["number"], 3)
        self.assertTrue((directory / "IMPLEMENTATION-03.md").exists())

    def reserve_concurrently(
        self, directory: Path, participants: int
    ) -> tuple[list, list]:
        # Без предельного времени участник, упавший до входа в барьер, оставил
        # бы остальных ждать навсегда, и набор завис бы вместо отказа.
        barrier = threading.Barrier(participants, timeout=30)
        real_numbers = plan_state.report_directory_numbers

        def synchronized_numbers(*args, **kwargs):
            barrier.wait()
            return real_numbers(*args, **kwargs)

        payloads = []
        errors = []

        def worker():
            try:
                payloads.append(
                    plan_state.reserve_report(directory, "implementation")
                )
            except Exception as error:  # noqa: BLE001
                errors.append(error)

        with mock.patch.object(
            plan_state, "report_directory_numbers", side_effect=synchronized_numbers
        ):
            threads = [threading.Thread(target=worker) for _ in range(participants)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        return payloads, errors

    def test__reserve_report__concurrent_calls__get_distinct_paths(self) -> None:
        participants = 8
        # Одного круга мало: варианту «посмотреть, потом записать» случается
        # разойтись во времени и разминуться — примерно шесть раз из ста.
        # Повторы убирают этот зазор.
        for attempt in range(5):
            with self.subTest(round=attempt):
                directory = self.root / f"race-{attempt}"
                directory.mkdir()

                payloads, errors = self.reserve_concurrently(directory, participants)

                self.assertEqual(errors, [])
                paths = sorted(payload["path"] for payload in payloads)
                self.assertEqual(len(paths), participants)
                self.assertEqual(len(set(paths)), participants)
                created = sorted(
                    entry.name
                    for entry in directory.iterdir()
                    if entry.name.startswith("IMPLEMENTATION-")
                )
                self.assertEqual(len(created), participants)

    def test__reserve_report__missing_directory__returns_invalid(self) -> None:
        result = self.run_cli(
            "reserve-report",
            "--directory",
            str(self.root / "absent"),
            "--kind",
            "implementation",
        )

        self.assertEqual(result.returncode, 3)
        self.assertIn("must exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
