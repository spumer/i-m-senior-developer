#!/usr/bin/env python3
"""Тесты режима --verify резолвера. Запуск:
  python3 -m pytest test_resolve.py
  python3 test_resolve.py

Фикстуры — мини-пакеты DPF.md во временных каталогах, по одной причине
отказа на каждую проверку контракта (0..4) плюс переключение --scope.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import resolve  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resolve.py")

ADMISSIBLE = (
    "> conformance: CC-DPF.1–9 verified; "
    "E.4.DPF.DA: admissibleForDeclaredDPFUse (critic, guardian, 2026-07-13)"
)
REPAIR = (
    "> conformance: CC-DPF.1–9 verified; "
    "E.4.DPF.DA: repairBeforeDPFUse (critic, guardian, 2026-07-13)"
)


def make_pkg(
    root,
    pkg_id,
    *,
    dpf_id="__same__",
    kind="Domain Principle Framework",
    status="active",
    review_due="2099-01-01",
    owner="guardian",
    conformance=ADMISSIBLE,
    references=None,
    apply_prompt=None,
):
    if dpf_id == "__same__":
        dpf_id = pkg_id
    pkg_dir = os.path.join(root, pkg_id)
    os.makedirs(pkg_dir, exist_ok=True)
    fm_lines = ["---"]
    for key, val in (
        ("dpf_id", dpf_id),
        ("kind", kind),
        ("status", status),
        ("review_due", review_due),
        ("owner", owner),
        ("name", "человекочитаемое назначение"),
    ):
        if val is not None:
            fm_lines.append(f"{key}: {val}")
    fm_lines.append("---")
    body = ["", "# Тело пакета", ""]
    if conformance:
        body.append(conformance)
    with open(os.path.join(pkg_dir, "DPF.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(fm_lines + body) + "\n")
    if references is not None:
        ref_dir = os.path.join(pkg_dir, "references")
        os.makedirs(ref_dir, exist_ok=True)
        with open(os.path.join(ref_dir, "critic-review.md"), "w", encoding="utf-8") as fh:
            fh.write(references + "\n")
    if apply_prompt is not None:
        assets = os.path.join(pkg_dir, "assets")
        os.makedirs(assets, exist_ok=True)
        with open(os.path.join(assets, "apply-prompt.md"), "w", encoding="utf-8") as fh:
            fh.write(apply_prompt + "\n")
    return pkg_dir


def levels_for(root):
    return [("project", root)]


def check(result, name):
    for c in result["checks"]:
        if c["name"] == name:
            return c
    raise AssertionError(f"нет проверки {name!r} в {[c['name'] for c in result['checks']]}")


# --- проверка 0: резолюция ---

def test_not_found_exits_1():
    with tempfile.TemporaryDirectory() as root:
        result, code = resolve.run_verify("DPF-NOPE", "bank", levels_for(root))
        assert code == 1
        assert result["ok"] is False
        assert check(result, "resolve")["ok"] is False


# --- проверка 1: структура + поля ---

def test_valid_admissible_passes_bank():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-VALID")
        result, code = resolve.run_verify("DPF-VALID", "bank", levels_for(root))
        assert code == 0, result
        assert result["ok"] is True
        assert all(c["ok"] for c in result["checks"])


def test_missing_owner_fails_field_check_both_scopes():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-NOOWNER", owner=None)
        for scope in ("local", "bank"):
            result, code = resolve.run_verify("DPF-NOOWNER", scope, levels_for(root))
            assert code == 2, (scope, result)
            c = check(result, "structure")
            assert c["ok"] is False
            assert c["reason"] == "missing field: owner"


# --- проверка 2: kind enum ---

def test_kind_not_in_enum_fails():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-BADKIND", kind="Something Else")
        result, code = resolve.run_verify("DPF-BADKIND", "local", levels_for(root))
        assert code == 2
        c = check(result, "kind")
        assert c["ok"] is False
        assert c["reason"] == "kind not in enum: Something Else"


# --- проверка 3: свежесть (гейтит только bank) ---

def test_stale_review_due_gates_bank_only():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-STALE", review_due="2000-01-01")

        result_local, code_local = resolve.run_verify("DPF-STALE", "local", levels_for(root))
        assert code_local == 0, result_local
        assert result_local["ok"] is True
        assert check(result_local, "freshness")["ok"] is False

        result_bank, code_bank = resolve.run_verify("DPF-STALE", "bank", levels_for(root))
        assert code_bank == 2
        assert result_bank["ok"] is False
        assert check(result_bank, "freshness")["ok"] is False


# --- проверка 4: критик-вердикт ---

def test_no_conformance_line_gates_bank_only():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-DRAFT", conformance=None)

        result_local, code_local = resolve.run_verify("DPF-DRAFT", "local", levels_for(root))
        assert code_local == 0, result_local
        assert result_local["ok"] is True
        assert check(result_local, "conformance")["ok"] is False

        result_bank, code_bank = resolve.run_verify("DPF-DRAFT", "bank", levels_for(root))
        assert code_bank == 2
        c = check(result_bank, "conformance")
        assert c["ok"] is False
        assert c["reason"] == "no admissible E.4.DPF.DA conformance line in DPF.md"


def test_repair_token_fails_conformance():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-REPAIR", conformance=REPAIR)
        result, code = resolve.run_verify("DPF-REPAIR", "bank", levels_for(root))
        assert code == 2
        assert check(result, "conformance")["ok"] is False


def test_verdict_read_from_dpf_md_not_references():
    # references несёт отрицательный токен, но DPF.md — положительный.
    # Читаем DPF.md → PASS (иначе false-positive/negative от references).
    negative_ref = (
        "ранний вердикт: "
        "E.4.DPF.DA: repairBeforeDPFUse; позже admissibleForDeclaredDPFUse "
        "не заявляется"
    )
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-REFNEG", conformance=ADMISSIBLE, references=negative_ref)
        result, code = resolve.run_verify("DPF-REFNEG", "bank", levels_for(root))
        assert code == 0, result
        assert result["ok"] is True
        assert check(result, "conformance")["ok"] is True


def test_last_e4_line_wins_when_two_conformance_lines():
    # Как у DPF-COUPLING на диске: строка покрытия + строка вердикта.
    two_lines = (
        "> conformance: покрытие CC-DPF.1–9 — references/quality-record.md\n"
        + ADMISSIBLE
    )
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-TWOLINE", conformance=two_lines)
        result, code = resolve.run_verify("DPF-TWOLINE", "bank", levels_for(root))
        assert code == 0, result
        assert check(result, "conformance")["ok"] is True


# --- executable-класс ---

def test_executable_pkg_with_apply_prompt_passes():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(
            root,
            "LPF-EXEC",
            kind="Local Practice Framework",
            apply_prompt="применить стадию",
        )
        result, code = resolve.run_verify("LPF-EXEC", "bank", levels_for(root))
        assert code == 0, result
        assert result["ok"] is True


# --- вывод / формат ---

def test_json_shape():
    with tempfile.TemporaryDirectory() as root:
        make_pkg(root, "DPF-VALID")
        result, _ = resolve.run_verify("DPF-VALID", "bank", levels_for(root))
        assert set(result.keys()) == {"id", "scope", "checks", "ok"}
        assert result["id"] == "DPF-VALID"
        assert result["scope"] == "bank"
        for c in result["checks"]:
            assert set(c.keys()) == {"name", "ok", "reason"}


# --- CLI end-to-end (exit-коды + fail-closed) ---

def run_cli(project_root, *cli_args):
    env = dict(os.environ)
    home = tempfile.mkdtemp()
    env["HOME"] = home
    proc = subprocess.run(
        [sys.executable, SCRIPT, *cli_args],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
    )
    return proc


def test_non_utf8_dpf_md_does_not_crash_and_reports_unreadable():
    # ISSUE-004: не-UTF-8 DPF.md раньше давал необработанный UnicodeDecodeError
    # (exit 1, путался с «не найден»); теперь — аккуратный отказ с explicit reason.
    with tempfile.TemporaryDirectory() as project:
        fw = os.path.join(project, ".claude", "frameworks")
        pkg_dir = os.path.join(fw, "DPF-BAD")
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "DPF.md"), "wb") as fh:
            fh.write(b"---\ndpf_id: DPF-BAD\n---\n\xff\xfe garbage not utf8")

        info, code = resolve.run_verify("DPF-BAD", "bank", levels_for(fw))
        assert code == 2, info
        assert info["ok"] is False
        assert check(info, "resolve")["ok"] is True  # DPF.md найден, просто нечитаем

        cli = run_cli(project, "DPF-BAD")
        assert cli.returncode == 2, cli.stderr + cli.stdout
        assert "Traceback" not in cli.stderr, cli.stderr
        assert "unreadable DPF.md" in cli.stderr, cli.stderr


def test_cli_missing_local_exits_1_without_traceback():
    with tempfile.TemporaryDirectory() as project:
        missing = run_cli(project, "--verify", "DPF-NOPE", "--scope", "local")

        assert missing.returncode == 1, missing.stderr + missing.stdout
        assert "Traceback" not in missing.stderr, missing.stderr
        assert "verify: FAIL — not found: DPF-NOPE" in missing.stdout


def test_cli_bank_pass_and_fail():
    with tempfile.TemporaryDirectory() as project:
        fw = os.path.join(project, ".claude", "frameworks")
        os.makedirs(fw)
        make_pkg(fw, "DPF-VALID")
        make_pkg(fw, "DPF-DRAFT", conformance=None)

        ok = run_cli(project, "--verify", "DPF-VALID", "--scope", "bank")
        assert ok.returncode == 0, ok.stderr + ok.stdout
        assert "verify: PASS (scope=bank)" in ok.stdout

        fail = run_cli(project, "--verify", "DPF-DRAFT", "--scope", "bank")
        assert fail.returncode == 2, fail.stdout
        assert "verify: FAIL" in fail.stdout

        # тот же черновик под local-дефолтом проходит
        draft_local = run_cli(project, "--verify", "DPF-DRAFT")
        assert draft_local.returncode == 0, draft_local.stdout

        missing = run_cli(project, "--verify", "DPF-NOPE", "--scope", "bank")
        assert missing.returncode == 1, missing.stdout


def _run_all():
    failures = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures.append((name, exc))
                print(f"FAIL {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failures.append((name, exc))
                print(f"ERROR {name}: {exc!r}")
    print(f"\n{len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_all())
