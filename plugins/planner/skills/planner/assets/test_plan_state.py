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

    def sync_documents(self, architecture: Path, execution: Path, body: str) -> None:
        architecture_body = "# Architecture\n"
        architecture_prepared = self.prepared_body(architecture, architecture_body)
        architecture_result = self.run_cli(
            "sync-architecture",
            str(architecture),
            "--body-file",
            str(architecture_prepared),
            "--semantic-change",
            "yes",
        )
        self.assertEqual(architecture_result.returncode, 0, architecture_result.stderr)

        execution_prepared = self.prepared_body(execution, body)
        execution_result = self.run_cli(
            "sync-execution",
            str(execution),
            "--body-file",
            str(execution_prepared),
            "--architecture",
            str(architecture),
            "--semantic-change",
            "yes",
        )
        self.assertEqual(execution_result.returncode, 0, execution_result.stderr)

    def initialize_repository(self, directory: Path) -> None:
        result = subprocess.run(
            ["git", "init"],
            cwd=directory,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def commit_output(self, directory: Path, path: Path, timestamp: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated output\n")
        relative_path = path.relative_to(directory)
        added = subprocess.run(
            ["git", "add", "--", str(relative_path)],
            cwd=directory,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(added.returncode, 0, added.stderr)
        environment = {
            **os.environ,
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
        committed = subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "record output",
            ],
            cwd=directory,
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )
        self.assertEqual(committed.returncode, 0, committed.stderr)

    def create_context_worktree(self, name: str) -> tuple[Path, Path]:
        main = self.root / name
        main.mkdir()
        self.initialize_repository(main)
        self.commit_output(
            main,
            main / "README.md",
            "2024-01-01T00:00:00 +0000",
        )
        worktree = self.root / f"{name}-worktree"
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree)],
            cwd=main,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return main, worktree

    def write_context(self, directory: Path, last_scan: str = "2024-01-01") -> Path:
        context = directory / ".claude" / "planner-context.md"
        context.parent.mkdir(exist_ok=True)
        context.write_text(
            "# Planner context\n\n"
            "## §7 Метаданные bootstrap\n\n"
            f"- **Last auto-scan:** {last_scan}\n"
        )
        return context

    def git_result(
        self, returncode: int, stdout: str = "", stderr: str = ""
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["git"], returncode, stdout, stderr)

    def assert_context_payload(
        self,
        payload: dict[str, object],
        path: Path | None,
        scope: str | None,
        status: str,
        start: Path,
        shared_root: Path | None,
        last_scan: str | None,
        searched: list[Path] | None = None,
    ) -> None:
        expected = {
            "bootstrap_last_scan": last_scan,
            "path": str(path.resolve()) if path is not None else None,
            "scope": scope,
            "shared_root": str(shared_root.resolve()) if shared_root is not None else None,
            "start": str(start.resolve()),
            "status": status,
        }
        if searched is not None:
            expected["searched"] = [str(candidate.resolve()) for candidate in searched]
        self.assertEqual(payload, expected)

    def create_work_hint_case(
        self, name: str, hint_status: str, stale: bool
    ) -> tuple[Path, Path, int]:
        directory = self.root / name
        directory.mkdir()
        architecture = directory / "ARCHITECTURE.md"
        execution = directory / "PLANNER_EXECUTION.md"
        body = "# Execution\n"
        if hint_status != "unavailable":
            body = "# Execution\nВыходы:\n- `./generated/output.md`\n"
        self.sync_documents(architecture, execution, body)
        self.initialize_repository(directory)
        if hint_status == "outputs_unchanged":
            self.commit_output(
                directory,
                directory / "generated" / "output.md",
                "2020-09-13T12:26:40 +0000",
            )
        elif hint_status == "outputs_changed":
            self.commit_output(
                directory,
                directory / "generated" / "output.md",
                "2024-01-01T00:00:00 +0000",
            )

        plan_built_at_ns = 1_700_000_000_123_456_789
        os.utime(execution, ns=(plan_built_at_ns, plan_built_at_ns))
        if stale:
            architecture.write_text(
                architecture.read_text().replace(
                    "# Architecture\n", "# Changed architecture\n"
                )
            )
        return architecture, execution, plan_built_at_ns

    def assert_existing_check_fields(
        self,
        payload: dict[str, object],
        architecture: Path,
        execution: Path,
        status: str,
    ) -> None:
        expected = {
            "architecture_path": str(architecture.resolve()),
            "current_version": 1,
            "execution_path": str(execution.resolve()),
            "recorded_version": 1,
            "status": status,
        }
        if status == "stale":
            expected["reason"] = "architecture content hash mismatch"
        self.assertEqual(
            {name: payload[name] for name in expected},
            expected,
        )

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

    def test__resolve_context__local_and_shared__prefers_local_context(self) -> None:
        main, worktree = self.create_context_worktree("local-preferred")
        shared = self.write_context(main, "2024-01-02")
        local = self.write_context(worktree, "2024-01-03")

        result = self.run_cli("resolve-context", "--start", str(worktree))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            worktree,
            main,
            "2024-01-03",
        )
        self.assertTrue(shared.exists())

    def test__resolve_context__only_shared_context__returns_shared_context(self) -> None:
        main, worktree = self.create_context_worktree("shared-fallback")
        shared = self.write_context(main, "2024-01-04")

        result = self.run_cli("resolve-context", "--start", str(worktree))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            shared,
            "shared",
            "ok",
            worktree,
            main,
            "2024-01-04",
        )

    def test__resolve_context__no_context_files__returns_missing_and_searched_paths(self) -> None:
        main, worktree = self.create_context_worktree("missing-context")
        local = worktree / ".claude" / "planner-context.md"
        shared = main / ".claude" / "planner-context.md"

        result = self.run_cli("resolve-context", "--start", str(worktree))

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            None,
            None,
            "missing",
            worktree,
            main,
            None,
            [local, shared],
        )

    def test__resolve_context__unreadable_local_context__returns_unreadable(self) -> None:
        main, worktree = self.create_context_worktree("unreadable-context")
        local = self.write_context(worktree)
        self.write_context(main, "2024-01-05")
        local.chmod(0)
        try:
            result = self.run_cli("resolve-context", "--start", str(worktree))
        finally:
            local.chmod(0o644)

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            None,
            None,
            "unreadable",
            worktree,
            main,
            None,
            [local],
        )

    def test__resolve_context__local_context_without_metadata__returns_malformed(self) -> None:
        main, worktree = self.create_context_worktree("malformed-context")
        local = worktree / ".claude" / "planner-context.md"
        local.parent.mkdir()
        local.write_text("# Planner context\n")
        self.write_context(main, "2024-01-06")

        result = self.run_cli("resolve-context", "--start", str(worktree))

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            None,
            None,
            "malformed",
            worktree,
            main,
            None,
            [local],
        )

    def test__resolve_context__live_bootstrap_metadata_outside_git__returns_local_context(
        self,
    ) -> None:
        outside = self.root / "outside-git"
        outside.mkdir()
        local = outside / ".claude" / "planner-context.md"
        local.parent.mkdir()
        local.write_text(
            "# Planner context\n\n"
            "## §7 Метаданные bootstrap\n\n"
            "- **Last auto-scan:** 2024-01-07\n"
        )

        result = self.run_cli("resolve-context", "--start", str(outside))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            outside,
            None,
            "2024-01-07",
        )

    def test__resolve_context__start_omitted__uses_working_directory(self) -> None:
        outside = self.root / "default-start"
        outside.mkdir()
        local = self.write_context(outside, "2024-01-08")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "resolve-context"],
            cwd=outside,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            outside,
            None,
            "2024-01-08",
        )

    def test__resolve_context__missing_start_directory__returns_usage(self) -> None:
        missing = self.root / "absent"

        result = self.run_cli("resolve-context", "--start", str(missing))

        self.assertEqual(result.returncode, 64)
        self.assertIn("must be an existing directory", result.stderr)

    def test__resolve_context__main_worktree__returns_root_context_path(self) -> None:
        main, _ = self.create_context_worktree("main-worktree")
        local = self.write_context(main, "2024-01-08")

        result = self.run_cli("resolve-context", "--start", str(main))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            main,
            main,
            "2024-01-08",
        )

    def test__resolve_context__trailing_space_in_repository_name__returns_local_context(
        self,
    ) -> None:
        main = self.root / "trailing-space "
        main.mkdir()
        self.initialize_repository(main)
        self.commit_output(main, main / "README.md", "2024-01-01T00:00:00 +0000")
        local = self.write_context(main, "2024-01-09")

        result = self.run_cli("resolve-context", "--start", str(main))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            main,
            main,
            "2024-01-09",
        )

    def test__resolve_context__candidate_replaced_before_read__returns_unreadable(
        self,
    ) -> None:
        start = self.root / "replacement"
        start.mkdir()
        candidate = self.write_context(start, "2024-01-10")
        foreign = self.root / "foreign-context.md"
        foreign.write_text(
            "# Foreign context\n\n"
            "## §7 Метаданные bootstrap\n\n"
            "- **Last auto-scan:** 2099-12-31\n"
        )
        resolved_candidate = candidate.resolve()
        original_path_open = Path.open
        original_os_open = os.open

        def replace_candidate() -> None:
            if not resolved_candidate.is_symlink():
                resolved_candidate.unlink()
                resolved_candidate.symlink_to(foreign)

        def open_after_replacement(
            path: Path, *arguments: object, **keywords: object
        ) -> object:
            if path == resolved_candidate:
                replace_candidate()
            return original_path_open(path, *arguments, **keywords)

        def secure_open_after_replacement(
            path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            if Path(path) == resolved_candidate:
                replace_candidate()
            return original_os_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(plan_state, "shared_git_root", return_value=None):
            with mock.patch.object(Path, "open", new=open_after_replacement):
                with mock.patch.object(
                    plan_state.os, "open", new=secure_open_after_replacement
                ):
                    with mock.patch.object(
                        plan_state,
                        "bootstrap_last_scan",
                        wraps=plan_state.bootstrap_last_scan,
                    ) as parsed:
                        with mock.patch.object(plan_state, "print_payload") as printed:
                            result = plan_state.resolve_context(start)

        payload = printed.call_args.args[0]
        self.assertNotEqual(payload["bootstrap_last_scan"], "2099-12-31")
        self.assertEqual(result, 3)
        parsed.assert_not_called()
        self.assertEqual(payload["status"], "unreadable")

    def test__resolve_context__separate_git_directory__does_not_invent_shared_root(
        self,
    ) -> None:
        main = self.root / "separate-main"
        metadata = self.root / "separate-metadata"
        initialized = subprocess.run(
            ["git", "init", "--separate-git-dir", str(metadata), str(main)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        self.commit_output(main, main / "README.md", "2024-01-01T00:00:00 +0000")
        worktree = self.root / "separate-linked"
        added = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree)],
            cwd=main,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(added.returncode, 0, added.stderr)
        invented = self.write_context(self.root, "2024-01-11")
        local = worktree / ".claude" / "planner-context.md"

        result = self.run_cli("resolve-context", "--start", str(worktree))

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            None,
            None,
            "missing",
            worktree,
            None,
            None,
            [local],
        )
        self.assertTrue(invented.exists())

    def test__resolve_context__bare_repository__checks_only_local_context(self) -> None:
        bare = self.root / "bare.git"
        initialized = subprocess.run(
            ["git", "init", "--bare", str(bare)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        local = self.write_context(bare, "2024-01-12")

        result = self.run_cli("resolve-context", "--start", str(bare))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            bare,
            None,
            "2024-01-12",
        )

    def test__resolve_context__template_bootstrap_metadata__returns_last_scan(
        self,
    ) -> None:
        outside = self.root / "template-metadata"
        outside.mkdir()
        local = outside / ".claude" / "planner-context.md"
        local.parent.mkdir()
        local.write_text(
            "# Planner context\n\n"
            "## 7. Метаданные bootstrap\n\n"
            "- Последний auto-scan: 2024-01-09\n"
        )

        result = self.run_cli("resolve-context", "--start", str(outside))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            outside,
            None,
            "2024-01-09",
        )

    def test__resolve_context__unnumbered_bootstrap_metadata__returns_last_scan(
        self,
    ) -> None:
        outside = self.root / "unnumbered-metadata"
        outside.mkdir()
        local = outside / ".claude" / "planner-context.md"
        local.parent.mkdir()
        local.write_text(
            "# Planner context\n\n"
            "## Метаданные bootstrap\n\n"
            "- Последний auto-scan: 2024-01-10\n"
        )

        result = self.run_cli("resolve-context", "--start", str(outside))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_context_payload(
            json.loads(result.stdout),
            local,
            "local",
            "ok",
            outside,
            None,
            "2024-01-10",
        )

    def test__shared_git_root__git_errors_or_invalid_output__raise_domain_error(
        self,
    ) -> None:
        root_output = f"{self.root}\n"
        cases = (
            ("launch failure", [FileNotFoundError("git")]),
            ("root command failure", [self.git_result(1, stderr="damaged")]),
            (
                "empty root output",
                [self.git_result(0, "\n"), self.git_result(0, ".git\n")],
            ),
            (
                "common command failure",
                [self.git_result(0, root_output), self.git_result(1, stderr="damaged")],
            ),
            (
                "empty common output",
                [self.git_result(0, root_output), self.git_result(0, "\n")],
            ),
            (
                "unparseable common output",
                [self.git_result(0, root_output), self.git_result(0, "\x00\n")],
            ),
            (
                "missing common directory",
                [
                    self.git_result(0, root_output),
                    self.git_result(0, "missing-common-dir\n"),
                ],
            ),
        )
        for name, responses in cases:
            with self.subTest(name=name):
                with mock.patch.object(
                    plan_state.subprocess, "run", side_effect=responses
                ):
                    with self.assertRaises(plan_state.PlanStateError):
                        plan_state.shared_git_root(self.root)

    def test__resolve_context__nonregular_candidates__return_unreadable_without_open(
        self,
    ) -> None:
        for node_type in ("symbolic link", "fifo"):
            with self.subTest(node_type=node_type):
                start = self.root / node_type
                start.mkdir()
                candidate = start / ".claude" / "planner-context.md"
                candidate.parent.mkdir()
                if node_type == "symbolic link":
                    target = self.root / "outside-context.md"
                    target.write_text("# Outside\n")
                    candidate.symlink_to(target)
                else:
                    os.mkfifo(candidate)

                with mock.patch.object(
                    plan_state, "shared_git_root", return_value=None
                ):
                    with mock.patch.object(plan_state, "print_payload") as printed:
                        with mock.patch.object(Path, "open") as opened:
                            result = plan_state.resolve_context(start)

                self.assertEqual(result, 3)
                opened.assert_not_called()
                self.assertEqual(printed.call_args.args[0]["status"], "unreadable")

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

    def test__check__matching_documents__returns_current_with_work_hint(self) -> None:
        self.sync_architecture()
        self.sync_execution()

        result = self.run_cli("check", str(self.execution))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        work_hint = payload.pop("work_hint")
        self.assertEqual(
            payload,
            {
                "architecture_path": str(self.architecture.resolve()),
                "current_version": 1,
                "execution_path": str(self.execution.resolve()),
                "recorded_version": 1,
                "status": "current",
            },
        )
        self.assertEqual(work_hint["status"], "unavailable")

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

    def test__check__work_hint_statuses__preserves_current_and_stale_exit_codes(self) -> None:
        for hint_status in (
            "outputs_unchanged",
            "outputs_changed",
            "unavailable",
        ):
            for stale in (False, True):
                with self.subTest(hint_status=hint_status, stale=stale):
                    architecture, execution, _ = self.create_work_hint_case(
                        f"{hint_status}-{stale}", hint_status, stale
                    )

                    result = self.run_cli("check", str(execution))

                    expected_status = "stale" if stale else "current"
                    expected_code = 2 if stale else 0
                    self.assertEqual(result.returncode, expected_code, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assert_existing_check_fields(
                        payload,
                        architecture,
                        execution,
                        expected_status,
                    )
                    self.assertEqual(payload["work_hint"]["status"], hint_status)

    def test__check__mark_stale__preserves_execution_mtime_for_repeated_work_hint(self) -> None:
        _, execution, plan_built_at_ns = self.create_work_hint_case(
            "preserved-mtime", "outputs_changed", True
        )

        first = self.run_cli("check", str(execution), "--mark-stale")

        self.assertEqual(first.returncode, 2, first.stderr)
        first_hint = json.loads(first.stdout)["work_hint"]
        self.assertEqual(first_hint["status"], "outputs_changed")

        second = self.run_cli("check", str(execution))

        self.assertEqual(second.returncode, 2, second.stderr)
        second_hint = json.loads(second.stdout)["work_hint"]
        self.assertEqual(second_hint["plan_built_at"], first_hint["plan_built_at"])
        self.assertEqual(second_hint["status"], "outputs_changed")
        self.assertEqual(execution.stat().st_mtime_ns, plan_built_at_ns)

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
        self.assertEqual(result.stdout, "")
        self.assertIn("execution content hash mismatch", result.stderr)

    def test__check__invalid_architecture__does_not_build_work_hint(self) -> None:
        self.sync_architecture()
        self.sync_execution()
        self.architecture.write_text(
            "---\nplan_type: unknown\nversion: 1\nstatus: current\n---\n# Body\n"
        )

        with mock.patch.object(plan_state, "build_work_hint") as build_work_hint:
            with self.assertRaises(plan_state.PlanStateError):
                plan_state.check_execution(self.execution, False)

        build_work_hint.assert_not_called()

    def test__cli__check_without_path__returns_usage(self) -> None:
        result = self.run_cli("check")

        self.assertEqual(result.returncode, 64)
        self.assertIn("usage:", result.stderr)

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

    def test__inspect_report__missing_path__returns_missing_with_null_size(self) -> None:
        absent = self.root / "IMPLEMENTATION-01.md"

        result = self.run_cli("inspect-report", str(absent))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "path": str(absent.resolve()),
                "size": None,
                "status": "missing",
            },
        )

    def test__inspect_report__empty_regular_file__returns_empty_with_zero_size(self) -> None:
        reserved = self.root / "IMPLEMENTATION-01.md"
        reserved.touch()

        result = self.run_cli("inspect-report", str(reserved))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "path": str(reserved.resolve()),
                "size": 0,
                "status": "empty",
            },
        )

    def test__inspect_report__nonempty_regular_file__returns_nonempty_with_actual_size(self) -> None:
        report = self.root / "IMPLEMENTATION-01.md"
        body = "# Full report\n" * 17
        report.write_text(body)

        result = self.run_cli("inspect-report", str(report))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "path": str(report.resolve()),
                "size": len(body.encode()),
                "status": "nonempty",
            },
        )

    def test__inspect_report__symbolic_link__returns_invalid_without_reading(self) -> None:
        target = self.root / "outside.md"
        target.write_text("# External report\n")
        link = self.root / "IMPLEMENTATION-01.md"
        link.symlink_to(target)

        result = self.run_cli("inspect-report", str(link))

        self.assertEqual(result.returncode, 3)
        self.assertIn("symbolic link", result.stderr)

    def test__inspect_report__directory__returns_invalid_without_reading(self) -> None:
        directory = self.root / "IMPLEMENTATION-01.md"
        directory.mkdir()

        result = self.run_cli("inspect-report", str(directory))

        self.assertEqual(result.returncode, 3)
        self.assertIn("regular file", result.stderr)

    def test__inspect_report__relative_path_from_directory__returns_absolute_path(self) -> None:
        directory = self.root / "feature"
        directory.mkdir()
        report = directory / "IMPLEMENTATION-01.md"
        report.write_text("# Report\n")

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "inspect-report", "IMPLEMENTATION-01.md"],
            cwd=directory,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout)["path"], str(report.resolve())
        )

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
