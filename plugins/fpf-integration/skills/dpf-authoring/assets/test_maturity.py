#!/usr/bin/env python3
"""Тесты `maturity.py` — парсеры канон-скелета/D-таблицы + вычисление уровня.

Запуск:
  python3 test_maturity.py
  python3 -m unittest test_maturity

stdlib only (unittest) — pytest в окружении отсутствует.

Фикстуры — синтетические мини-своды во временных каталогах
(tempfile.TemporaryDirectory), плюс golden-копии двух реальных seed-сводов
бэнка (DPF-COUPLING-GENERALIZATION, LPF-SIMPLIFICATION-REVIEW), скопированные
в temp перед прогоном — репозиторные файлы не мутируются.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maturity  # noqa: E402

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
BANK_FRAMEWORKS = os.path.join(REPO_ROOT, "plugins", "fpf-competency-bank", "frameworks")


# ---------------------------------------------------------------------------
# Синтетические билдеры фикстур
# ---------------------------------------------------------------------------

ADMISSIBLE_LINE = "> conformance: E.4.DPF.DA: admissibleForDeclaredDPFUse (critic, guardian, 2026-01-01)"


def make_dpf_md(
    tmp_dir,
    *,
    kind="Domain Principle Framework",
    review_due="2099-01-01",
    n_patterns=6,
    section5=True,
    per_pattern_relations=False,
    n_refresh_triggers=2,
    section10_cases=("A", "B"),
    pending_cases=(),
    conformance_line=ADMISSIBLE_LINE,
    omit_section4=False,
    omit_section5=False,
    omit_section10=False,
    omit_section11=False,
):
    lines = [
        "---",
        f'dpf_id: "TEST-PKG"',
        f'kind: "{kind}"',
        'status: "active"',
        f'review_due: "{review_due}"',
        "---",
        "",
        "# TEST-PKG",
        "",
        "## 1. Контекст",
        "текст",
        "",
        "## 2. Source pack",
        "текст",
        "",
        "## 3. Forces",
        "текст",
        "",
    ]
    if not omit_section4:
        lines.append("## 4. Паттерны")
        lines.append("")
        for i in range(1, n_patterns + 1):
            lines.append(f"### Паттерн {i}: имя")
            lines.append("- **Recognition:** текст")
            lines.append("- **Conformance:** текст")
            if per_pattern_relations:
                lines.append("- **Связи:** `require`/`sequence` — связь с соседним паттерном")
            lines.append("")
    if not omit_section5 and section5:
        lines.append("## 5. Связи паттернов")
        lines.append("")
        lines.append("| От → К | Тип связи | Смысл |")
        lines.append("|---|---|---|")
        lines.append("| П1 → П2 | `require`/`sequence` | текст |")
        lines.append("| П2 → П3 | `composition` | текст |")
        lines.append("| П3 → П4 | `conflict` (scoped) | текст |")
        lines.append("")
    lines.append("## 6. Типовые ошибки")
    lines.append("текст")
    lines.append("")
    lines.append("## 7. SoTA-Echoing")
    lines.append("текст")
    lines.append("")
    lines.append("## 8. Имена")
    lines.append("текст")
    lines.append("")
    lines.append("## 9. Relations")
    lines.append("текст")
    lines.append("")
    if not omit_section10:
        lines.append("## 10. Разнородные приёмочные случаи")
        lines.append("")
        for case_id in section10_cases:
            marker = " (не evidence — перенесённая иллюстрация)" if case_id in pending_cases else ""
            lines.append(f"**Случай {case_id} — заголовок кейса.** Текст кейса{marker}.")
            lines.append("")
    if not omit_section11:
        lines.append("## 11. Quality & refresh route")
        lines.append("")
        triggers = "; ".join(f"триггер {i}" for i in range(1, n_refresh_triggers + 1))
        lines.append(f"- **Refresh triggers:** {triggers}.")
        lines.append("")
    lines.append("## Артефакты каталога")
    lines.append("текст")
    lines.append("")
    if conformance_line:
        lines.append(conformance_line)
    with open(os.path.join(tmp_dir, "DPF.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


D_FULL_TABLE_HEADER = "| Coord | V | ShortRationale | EvidenceLocus | Repair / no-proposal |"
D_FULL_TABLE_SEP = "|---|---|---|---|---|"


def make_d_full_table(values, repairs=None):
    """values: dict[int,int]; repairs: dict[int,str] (default 'no-proposal')."""
    repairs = repairs or {}
    lines = [D_FULL_TABLE_HEADER, D_FULL_TABLE_SEP]
    for d_id in range(1, 12):
        v = values.get(d_id, 4)
        rep = repairs.get(d_id, "no-proposal")
        lines.append(f"| D{d_id} Name | {v} | rationale | §locus | {rep} |")
    return "\n".join(lines)


def make_adequacy(tmp_dir, date, *, status="admissibleForDeclaredDPFUse", d_table=None, critic_line=None, extra=""):
    ref_dir = os.path.join(tmp_dir, "references")
    os.makedirs(ref_dir, exist_ok=True)
    if d_table is None:
        d_table = make_d_full_table({})
    body = [
        f"# Package-adequacy {date}",
        "",
        f"**Статус: `{status}`**",
        "",
        d_table,
        "",
    ]
    if extra:
        body.append(extra)
        body.append("")
    if critic_line:
        body.append(critic_line)
        body.append("")
    path = os.path.join(ref_dir, f"package-adequacy-{date}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(body) + "\n")
    return path


# ---------------------------------------------------------------------------
# Frontmatter / секции
# ---------------------------------------------------------------------------


class FrontmatterTests(unittest.TestCase):
    def test_parses_simple_fields(self):
        text = '---\ndpf_id: "X"\nkind: "Domain Principle Framework"\n---\nbody'
        fm = maturity.parse_frontmatter(text)
        self.assertEqual(fm["dpf_id"], "X")
        self.assertEqual(fm["kind"], "Domain Principle Framework")

    def test_missing_frontmatter_returns_empty(self):
        self.assertEqual(maturity.parse_frontmatter("# no frontmatter"), {})


class SectionExtractionTests(unittest.TestCase):
    def test_extracts_section_between_headings(self):
        text = "## 4. Заголовок\nA\nB\n## 5. Следующий\nC\n"
        section = maturity.extract_section(text, 4)
        assert section is not None
        self.assertIn("A", section)
        self.assertIn("B", section)
        self.assertNotIn("C", section)

    def test_missing_section_returns_none(self):
        text = "## 4. Заголовок\nA\n"
        self.assertIsNone(maturity.extract_section(text, 5))

    def test_subheadings_do_not_terminate_section(self):
        text = "## 4. Заголовок\n### Паттерн 1\nA\n## 5. Следующий\n"
        section = maturity.extract_section(text, 4)
        assert section is not None
        self.assertIn("### Паттерн 1", section)


# ---------------------------------------------------------------------------
# canon-patterns + conformance
# ---------------------------------------------------------------------------


class CanonPatternsTests(unittest.TestCase):
    def test_counts_pattern_headings(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, n_patterns=6)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            count, found = maturity.count_canon_patterns(text)
            self.assertEqual(count, 6)
            self.assertTrue(found)

    def test_missing_section4_reported_not_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, omit_section4=True)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            count, found = maturity.count_canon_patterns(text)
            self.assertEqual(count, 0)
            self.assertFalse(found)


class ConformanceLineTests(unittest.TestCase):
    def test_admissible_line_detected(self):
        text = "body\n" + ADMISSIBLE_LINE + "\n"
        self.assertTrue(maturity.dpf_md_admissible(text))

    def test_repair_token_not_admissible(self):
        text = "> conformance: E.4.DPF.DA: repairBeforeDPFUse (x)\n"
        self.assertFalse(maturity.dpf_md_admissible(text))

    def test_last_line_wins_when_two_conformance_lines(self):
        text = (
            "> conformance: покрытие CC-DPF.1-9 — см. quality-record.md\n"
            + ADMISSIBLE_LINE
            + "\n"
        )
        self.assertTrue(maturity.dpf_md_admissible(text))

    def test_no_conformance_line_not_admissible(self):
        self.assertFalse(maturity.dpf_md_admissible("# body only\n"))


# ---------------------------------------------------------------------------
# PFR-network — §5 таблица И per-pattern fallback
# ---------------------------------------------------------------------------


class PfrNetworkTests(unittest.TestCase):
    def test_table_form_counts_edges_and_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, section5=True)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            edges, types, found = maturity.extract_relation_edges(text)
            self.assertGreaterEqual(edges, 3)
            self.assertGreaterEqual(len(types), 2)
            self.assertTrue(found)

    def test_per_pattern_form_counts_when_section5_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, section5=False, omit_section5=True, per_pattern_relations=True, n_patterns=4)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            edges, types, found = maturity.extract_relation_edges(text)
            self.assertGreaterEqual(edges, 3)
            self.assertIn("requires_specialization", types)

    def test_no_signal_when_neither_section_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, section5=False, omit_section5=True, omit_section4=True, per_pattern_relations=False)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            edges, types, found = maturity.extract_relation_edges(text)
            self.assertEqual(edges, 0)
            self.assertFalse(found)


# ---------------------------------------------------------------------------
# refresh-route
# ---------------------------------------------------------------------------


class RefreshRouteTests(unittest.TestCase):
    def test_counts_semicolon_separated_triggers(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, n_refresh_triggers=3)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            count, found = maturity.count_refresh_triggers(text)
            self.assertEqual(count, 3)
            self.assertTrue(found)

    def test_missing_section11_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, omit_section11=True)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            count, found = maturity.count_refresh_triggers(text)
            self.assertEqual(count, 0)
            self.assertFalse(found)

    def test_review_due_present_and_parses(self):
        fm = {"review_due": "2026-10-10"}
        self.assertTrue(maturity.review_due_present(fm))

    def test_review_due_missing(self):
        self.assertFalse(maturity.review_due_present({}))

    def test_review_due_unparseable(self):
        self.assertFalse(maturity.review_due_present({"review_due": "не дата"}))


# ---------------------------------------------------------------------------
# acceptance-cases
# ---------------------------------------------------------------------------


class AcceptanceCasesTests(unittest.TestCase):
    def test_counts_real_cases_as_nonpending(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, section10_cases=("A", "B"), pending_cases=())
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            total, nonpending, found = maturity.extract_acceptance_cases(text)
            self.assertEqual(total, 2)
            self.assertEqual(nonpending, 2)

    def test_pending_case_excluded_from_nonpending(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, section10_cases=("A", "B", "C"), pending_cases=("C",))
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            total, nonpending, found = maturity.extract_acceptance_cases(text)
            self.assertEqual(total, 3)
            self.assertEqual(nonpending, 2)

    def test_missing_section10_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, omit_section10=True)
            text = open(os.path.join(tmp, "DPF.md"), encoding="utf-8").read()
            total, nonpending, found = maturity.extract_acceptance_cases(text)
            self.assertEqual(total, 0)
            self.assertFalse(found)


# ---------------------------------------------------------------------------
# support-maps
# ---------------------------------------------------------------------------


class SupportMapsTests(unittest.TestCase):
    def test_detects_map_and_bridge_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref = os.path.join(tmp, "references")
            os.makedirs(ref)
            open(os.path.join(ref, "architecture-map.md"), "w").close()
            open(os.path.join(ref, "semantics-bridge.md"), "w").close()
            open(os.path.join(ref, "sota-research.md"), "w").close()
            self.assertEqual(maturity.count_support_maps(ref), 2)

    def test_excludes_package_adequacy_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref = os.path.join(tmp, "references")
            os.makedirs(ref)
            open(os.path.join(ref, "package-adequacy-2026-01-01.md"), "w").close()
            self.assertEqual(maturity.count_support_maps(ref), 0)

    def test_no_references_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(maturity.count_support_maps(os.path.join(tmp, "references")), 0)


# ---------------------------------------------------------------------------
# D1-D11 таблица: полноформатная + delta-формата + слияние
# ---------------------------------------------------------------------------


class DTableParsingTests(unittest.TestCase):
    def test_full_table_parses_11_ints_and_repair(self):
        text = make_d_full_table({1: 5, 4: 5}, repairs={2: "R2 остаётся"})
        values, repair, found = maturity.parse_d_scores(text)
        self.assertTrue(found)
        self.assertEqual(len(values), 11)
        self.assertEqual(values[1], 5)
        self.assertEqual(values[2], 4)
        self.assertEqual(repair[2], "R2 остаётся")
        self.assertEqual(repair[3], "no-proposal")

    def test_bold_value_with_parenthetical_history_takes_first_digit(self):
        table = (
            D_FULL_TABLE_HEADER
            + "\n"
            + D_FULL_TABLE_SEP
            + "\n"
            + "| **D5** Name | **4** (был 3) | rationale | §locus | addendum needed |\n"
        )
        values, repair, found = maturity.parse_d_scores(table)
        self.assertEqual(values[5], 4)
        self.assertEqual(repair[5], "addendum needed")

    def test_delta_table_takes_last_circle_column(self):
        table = (
            "| Координата | Круг 1 | Круг 2 | Обоснование |\n"
            "|---|---|---|---|\n"
            "| D2 Name | 3 | **4** | текст |\n"
            "| D1, D3, D4 | 4 | 4 | не менялись |\n"
        )
        values, repair, found = maturity.parse_d_scores(table)
        self.assertTrue(found)
        self.assertEqual(values[2], 4)
        self.assertIsNone(repair[2])
        self.assertEqual(values[1], 4)
        self.assertEqual(values[3], 4)
        self.assertEqual(values[4], 4)

    def test_later_table_overrides_earlier_in_document_order(self):
        full = make_d_full_table({2: 3}, repairs={2: "REPAIR открыт"})
        delta = (
            "| Координата | Круг 1 | Круг 2 | Обоснование |\n"
            "|---|---|---|---|\n"
            "| D2 Name | 3 | **4** | ремонт закрыт |\n"
        )
        text = full + "\n\n" + delta
        values, repair, found = maturity.parse_d_scores(text)
        self.assertEqual(values[2], 4)
        self.assertIsNone(repair[2])

    def test_d_scores_complete_requires_all_11(self):
        values, _, _ = maturity.parse_d_scores(make_d_full_table({}))
        self.assertTrue(maturity.d_scores_complete(values))
        self.assertFalse(maturity.d_scores_complete({1: 5}))

    def test_non_coordinate_table_is_ignored(self):
        text = "| PFM | Диспозиция |\n|---|---|\n| PFM1 | PASS |\n"
        values, repair, found = maturity.parse_d_scores(text)
        self.assertEqual(values, {})
        self.assertFalse(found)


# ---------------------------------------------------------------------------
# floor-fragile
# ---------------------------------------------------------------------------


class FloorFragileTests(unittest.TestCase):
    def test_v4_with_no_proposal_is_stable(self):
        values = {1: 4}
        repair = {1: "no-proposal (проверено: ...)"}
        self.assertEqual(maturity.compute_floor_fragile(values, repair), set())

    def test_v4_with_dash_is_stable(self):
        values = {1: 4}
        repair = {1: "—"}
        self.assertEqual(maturity.compute_floor_fragile(values, repair), set())

    def test_v4_with_open_repair_is_fragile(self):
        values = {1: 4}
        repair = {1: "R2 остаётся (индекс не написан)"}
        self.assertEqual(maturity.compute_floor_fragile(values, repair), {1})

    def test_v5_never_fragile_regardless_of_repair_text(self):
        values = {1: 5}
        repair = {1: "R2 остаётся"}
        self.assertEqual(maturity.compute_floor_fragile(values, repair), set())

    def test_none_repair_treated_as_resolved(self):
        values = {1: 4}
        repair = {1: None}
        self.assertEqual(maturity.compute_floor_fragile(values, repair), set())


# ---------------------------------------------------------------------------
# статус-токен + critic-ceiling
# ---------------------------------------------------------------------------


class StatusTokenTests(unittest.TestCase):
    def test_last_status_wins(self):
        text = "repairBeforeDPFUse ... позже ... admissibleForDeclaredDPFUse"
        self.assertEqual(maturity.extract_status_token(text), "admissibleForDeclaredDPFUse")

    def test_no_status_returns_none(self):
        self.assertIsNone(maturity.extract_status_token("ничего похожего"))

    def test_bold_declaration_wins_over_later_bare_historical_mention(self):
        # Как в реальном LPF package-adequacy: финальная строка-декларация
        # ("**`admissibleForDeclaredDPFUse`**") стоит РАНЬШЕ по тексту, чем
        # прозаическое упоминание истории одиночным backtick без bold
        # ("круг 1 (`repairBeforeDPFUse`, §1-§8) сохранён дословно выше").
        text = (
            "**`admissibleForDeclaredDPFUse`.**\n"
            "История: круг 1 (`repairBeforeDPFUse`, §1-§8) сохранён дословно выше.\n"
        )
        self.assertEqual(maturity.extract_status_token(text), "admissibleForDeclaredDPFUse")

    def test_declaration_matches_real_labelled_bold_form(self):
        # MINOR3: реальная форма — токен НЕ вплотную после "**", а после
        # лейбла внутри того же bold-спана ("**Статус (...): `TOKEN`**"
        # или "**Итог (спойлер): `TOKEN`**" — обе встречаются в бэнке).
        text = "- **Статус (E.4.DPF.DA:4.5): `admissibleForDeclaredDPFUse`** — все координаты ≥ пола."
        self.assertEqual(maturity.extract_status_token(text), "admissibleForDeclaredDPFUse")

    def test_declaration_form_wins_over_later_prose_mention_in_same_paragraph(self):
        # Без фикса MINOR3 это padало на bare-fallback и мог перепутать
        # порядок, если прозаическое упоминание другого токена стоит позже.
        text = (
            "- **Статус (E.4.DPF.DA:4.5): `admissibleForDeclaredDPFUse`** — обоснование.\n"
            "- Не `repairBeforeDPFUse` (три координаты ниже пола).\n"
        )
        self.assertEqual(maturity.extract_status_token(text), "admissibleForDeclaredDPFUse")


class CriticCeilingTests(unittest.TestCase):
    def test_parses_level_and_weak_components(self):
        line = "> maturity-critic: L3 confirmed (guardian, 2026-01-01); weak-components: [support-maps, acceptance-cases]"
        level, weak, malformed = maturity.extract_critic_ceiling(line)
        self.assertEqual(level, 3)
        self.assertEqual(weak, ["support-maps", "acceptance-cases"])
        self.assertFalse(malformed)

    def test_empty_weak_components_list(self):
        line = "> maturity-critic: L2 confirmed (guardian, 2026-01-01); weak-components: []"
        level, weak, malformed = maturity.extract_critic_ceiling(line)
        self.assertEqual(level, 2)
        self.assertEqual(weak, [])
        self.assertFalse(malformed)

    def test_no_line_returns_none_and_not_malformed(self):
        level, weak, malformed = maturity.extract_critic_ceiling("ничего")
        self.assertIsNone(level)
        self.assertEqual(weak, [])
        self.assertFalse(malformed)

    def test_last_line_wins(self):
        text = (
            "> maturity-critic: L2 confirmed (guardian, 2026-01-01); weak-components: []\n"
            "> maturity-critic: L3 confirmed (guardian, 2026-02-01); weak-components: []\n"
        )
        level, _, _ = maturity.extract_critic_ceiling(text)
        self.assertEqual(level, 3)

    # --- MINOR1: malformed строка отличима от отсутствующей ---

    def test_prefix_present_without_weak_components_is_malformed(self):
        line = "> maturity-critic: L3 confirmed (guardian, 2026-07-22)"
        level, weak, malformed = maturity.extract_critic_ceiling(line)
        self.assertIsNone(level)
        self.assertEqual(weak, [])
        self.assertTrue(malformed)

    # --- MAJOR: эхо ВНУТРИ раздела профиля не должно затенять источник ---

    def test_echo_inside_profile_section_is_not_read_as_source(self):
        text = (
            "> maturity-critic: L3 confirmed (guardian, 2026-01-01); weak-components: [support-maps]\n"
            "\n"
            "## Профиль зрелости\n"
            "\n"
            "(эхо источника: maturity-critic L3 confirmed; weak-components: [support-maps])\n"
        )
        level, weak, malformed = maturity.extract_critic_ceiling(text)
        self.assertEqual(level, 3)
        self.assertEqual(weak, ["support-maps"])
        self.assertFalse(malformed)

    def test_legacy_machine_readable_echo_after_heading_is_ignored(self):
        # Даже если бы эхо (старый формат, до фикса) выглядело МАШИННО как
        # источник — оно лежит ПОСЛЕ '## Профиль зрелости' и не должно
        # затенять подлинную строку до заголовка.
        text = (
            "> maturity-critic: L3 confirmed (guardian, 2026-01-01); weak-components: [support-maps]\n"
            "\n"
            "## Профиль зрелости\n"
            "\n"
            "> maturity-critic: L3 confirmed; weak-components: ['support-maps']\n"
        )
        level, weak, malformed = maturity.extract_critic_ceiling(text)
        self.assertEqual(level, 3)
        self.assertEqual(weak, ["support-maps"])


# ---------------------------------------------------------------------------
# compute_level — fail-closed по уровням, kind-развилка, критик-потолок
# ---------------------------------------------------------------------------


def base_ctx(**overrides):
    ctx = {
        "adequacy_present": True,
        "status_token": "admissibleForDeclaredDPFUse",
        "d_complete": True,
        "min_d": 4,
        "canon_patterns_count": 6,
        "dpf_conformance_admissible": True,
        "floor_fragile": set(),
        "pfr_edges": 3,
        "pfr_types": {"requires_specialization", "conflicts"},
        "refresh_triggers": 2,
        "review_due_present": True,
        "acceptance_nonpending": 2,
        "support_maps": 1,
        "is_lpf": False,
        "executable_sync": None,
        "critic_level": 3,
    }
    ctx.update(overrides)
    return ctx


class ComputeLevelTests(unittest.TestCase):
    def test_no_adequacy_is_l0(self):
        r = maturity.compute_level({"adequacy_present": False})
        self.assertEqual(r["final_level"], 0)

    def test_status_not_admissible_is_l0(self):
        r = maturity.compute_level(base_ctx(status_token="repairBeforeDPFUse"))
        self.assertEqual(r["final_level"], 0)

    def test_min_d_below_floor_is_l0(self):
        r = maturity.compute_level(base_ctx(min_d=3))
        self.assertEqual(r["final_level"], 0)

    def test_incomplete_d_table_is_l0(self):
        r = maturity.compute_level(base_ctx(d_complete=False))
        self.assertEqual(r["final_level"], 0)

    def test_l1_without_canon_patterns_stays_l0(self):
        r = maturity.compute_level(base_ctx(canon_patterns_count=2, critic_level=None))
        self.assertEqual(r["final_level"], 0)

    def test_l1_achieved_but_l2_blocked_by_floor_fragile(self):
        r = maturity.compute_level(base_ctx(floor_fragile={2, 5}, critic_level=None))
        self.assertEqual(r["final_level"], 1)

    def test_l1_achieved_but_l2_blocked_by_weak_pfr(self):
        r = maturity.compute_level(base_ctx(pfr_edges=1, critic_level=None))
        self.assertEqual(r["final_level"], 1)

    def test_l1_achieved_but_l2_blocked_by_weak_refresh(self):
        r = maturity.compute_level(base_ctx(refresh_triggers=1, critic_level=None))
        self.assertEqual(r["final_level"], 1)

    def test_l2_achieved_when_all_l2_requirements_met_and_l3_missing_support_maps(self):
        r = maturity.compute_level(base_ctx(support_maps=0, critic_level=None))
        self.assertEqual(r["final_level"], 2)

    def test_l3_missing_acceptance_cases_caps_at_l2(self):
        r = maturity.compute_level(base_ctx(acceptance_nonpending=1, critic_level=None))
        self.assertEqual(r["final_level"], 2)

    def test_l3_structural_without_critic_line_caps_to_l2(self):
        r = maturity.compute_level(base_ctx(critic_level=None))
        self.assertEqual(r["structural_level"], 3)
        self.assertEqual(r["final_level"], 2)

    def test_l3_structural_with_critic_line_l3_confirms(self):
        r = maturity.compute_level(base_ctx(critic_level=3))
        self.assertEqual(r["final_level"], 3)

    def test_critic_ceiling_lowers_final_below_structural(self):
        r = maturity.compute_level(base_ctx(critic_level=2))
        self.assertEqual(r["structural_level"], 3)
        self.assertEqual(r["final_level"], 2)

    def test_l4_requires_component_richness_not_all_d_equal_5(self):
        # D-полоса L2/L3 (все ==4) — L4 не требует "все D==5".
        r = maturity.compute_level(
            base_ctx(
                canon_patterns_count=8,
                acceptance_nonpending=4,
                support_maps=5,
                pfr_types={"requires_specialization", "composes_source_reuse", "conflicts", "evaluation", "teaching", "ethics"},
                refresh_triggers=3,
                critic_level=4,
            )
        )
        self.assertEqual(r["final_level"], 4)

    def test_l4_blocked_when_component_richness_insufficient_even_if_critic_says_l4(self):
        r = maturity.compute_level(base_ctx(critic_level=4))  # только L3-компоненты
        self.assertEqual(r["final_level"], 3)

    def test_lpf_without_domain_width_not_lowered(self):
        # LPF: у compute_level нет отдельного домен-широта требования —
        # is_lpf=True с executable_sync=True не блокирует L3.
        r = maturity.compute_level(base_ctx(is_lpf=True, executable_sync=True, critic_level=3))
        self.assertEqual(r["final_level"], 3)

    def test_lpf_executable_desync_caps_below_l3(self):
        r = maturity.compute_level(base_ctx(is_lpf=True, executable_sync=False, critic_level=None))
        self.assertEqual(r["final_level"], 2)


# ---------------------------------------------------------------------------
# analyze() — интеграционные сценарии на синтетических пакетах
# ---------------------------------------------------------------------------


class AnalyzeIntegrationTests(unittest.TestCase):
    def test_missing_dpf_md_is_unreadable_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = maturity.analyze(tmp)
            self.assertEqual(result["error"], "unreadable")
            self.assertEqual(result["code"], 1)

    def test_no_adequacy_gives_code_2_and_level_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            result = maturity.analyze(tmp)
            self.assertEqual(result["code"], 2)
            self.assertEqual(result["level_result"]["final_level"], 0)
            self.assertFalse(result["ctx"]["adequacy_present"])

    def test_multiple_dated_files_picks_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}, repairs={2: "R2 open"}))
            make_adequacy(tmp, "2026-02-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            self.assertEqual(result["ctx"]["adequacy_name"], "package-adequacy-2026-02-01.md")
            self.assertEqual(result["ctx"]["floor_fragile"], set())

    def test_full_admissible_package_reaches_l2(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, n_refresh_triggers=2)
            make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            self.assertEqual(result["code"], 0)
            self.assertEqual(result["level_result"]["final_level"], 2)

    def test_floor_fragile_caps_at_l1(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}, repairs={2: "R2 остаётся открытым"}))
            result = maturity.analyze(tmp)
            self.assertEqual(result["level_result"]["final_level"], 1)
            fragile_ids = {c["id"] for c in result["components"] if c["status"] != "ok"}
            self.assertIn("canon-patterns", {c["id"] for c in result["components"]})

    def test_weak_component_marked_from_critic_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            critic = "> maturity-critic: L3 confirmed (guardian, 2026-01-01); weak-components: [support-maps]"
            make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}), critic_line=critic)
            os.makedirs(os.path.join(tmp, "references"), exist_ok=True)
            open(os.path.join(tmp, "references", "arch-map.md"), "w").close()
            result = maturity.analyze(tmp)
            comp = next(c for c in result["components"] if c["id"] == "support-maps")
            self.assertEqual(comp["status"], "weak")

    def test_lpf_kind_adds_executable_sync_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, kind="Local Practice Framework")
            make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            ids = {c["id"] for c in result["components"]}
            self.assertIn("executable-sync", ids)

    def test_dpf_kind_has_no_executable_sync_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp, kind="Domain Principle Framework")
            make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            ids = {c["id"] for c in result["components"]}
            self.assertNotIn("executable-sync", ids)


# ---------------------------------------------------------------------------
# write-profile: идемпотентная перезапись, DPF.md не трогается
# ---------------------------------------------------------------------------


class WriteProfileTests(unittest.TestCase):
    def test_appends_section_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            path = make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            section = maturity.render_profile_section(result)
            maturity.write_profile(path, section)
            text = open(path, encoding="utf-8").read()
            self.assertIn("## Профиль зрелости", text)
            self.assertEqual(text.count("## Профиль зрелости"), 1)

    def test_rewrite_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            path = make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            section = maturity.render_profile_section(result)
            maturity.write_profile(path, section)
            maturity.write_profile(path, section)
            text = open(path, encoding="utf-8").read()
            self.assertEqual(text.count("## Профиль зрелости"), 1)

    def test_write_profile_does_not_touch_dpf_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            dpf_path = os.path.join(tmp, "DPF.md")
            before = open(dpf_path, encoding="utf-8").read()
            path = make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            result = maturity.analyze(tmp)
            section = maturity.render_profile_section(result)
            maturity.write_profile(path, section)
            after = open(dpf_path, encoding="utf-8").read()
            self.assertEqual(before, after)

    def test_cli_write_profile_without_adequacy_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            code = maturity.main([tmp, "--write-profile"])
            self.assertEqual(code, 2)

    def test_weak_components_echo_is_readable_not_python_repr(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            critic = (
                "> maturity-critic: L3 confirmed (guardian, 2026-01-01); "
                "weak-components: [support-maps, acceptance-cases]"
            )
            path = make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}), critic_line=critic)
            result = maturity.analyze(tmp)
            section = maturity.render_profile_section(result)
            # НЕ python-repr список (без кавычек/апострофов вокруг id компонентов).
            self.assertIn("weak-components: [support-maps, acceptance-cases]", section)
            self.assertNotIn("'support-maps'", section)
            self.assertNotIn('"support-maps"', section)

    # --- MAJOR regression: analyze -> render -> write -> analyze снова ---

    def test_round_trip_preserves_critic_ceiling_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            critic = (
                "> maturity-critic: L3 confirmed (guardian, 2026-01-01); "
                "weak-components: [support-maps, acceptance-cases]"
            )
            path = make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}), critic_line=critic)

            result1 = maturity.analyze(tmp)
            self.assertEqual(result1["ctx"]["critic_level"], 3)
            self.assertEqual(result1["ctx"]["weak_components"], ["support-maps", "acceptance-cases"])
            section1 = maturity.render_profile_section(result1)
            maturity.write_profile(path, section1)
            text_after_1 = open(path, encoding="utf-8").read()

            # Второй прогон: critic_level/weak_components ДОЛЖНЫ остаться теми же
            # (не затенены собственным эхо, не искажены repr-накоплением кавычек).
            result2 = maturity.analyze(tmp)
            self.assertEqual(result2["ctx"]["critic_level"], 3)
            self.assertEqual(result2["ctx"]["weak_components"], ["support-maps", "acceptance-cases"])
            section2 = maturity.render_profile_section(result2)
            self.assertEqual(section1, section2, "секция должна быть байт-в-байт идентична на 2-м прогоне")
            maturity.write_profile(path, section2)
            text_after_2 = open(path, encoding="utf-8").read()
            self.assertEqual(text_after_1, text_after_2, "второй write не должен менять файл (идемпотентность)")

            # Третий прогон — то же самое, для верности (не дрейфует со временем).
            result3 = maturity.analyze(tmp)
            self.assertEqual(result3["ctx"]["critic_level"], 3)
            self.assertEqual(result3["ctx"]["weak_components"], ["support-maps", "acceptance-cases"])
            section3 = maturity.render_profile_section(result3)
            self.assertEqual(section2, section3)
            maturity.write_profile(path, section3)
            text_after_3 = open(path, encoding="utf-8").read()
            self.assertEqual(text_after_2, text_after_3)

            # ровно один раздел профиля, ровно одна исходная критик-строка.
            self.assertEqual(text_after_3.count("## Профиль зрелости"), 1)
            self.assertEqual(text_after_3.count("> maturity-critic:"), 1)

    # --- MINOR2: подлинная критик-строка после раздела профиля не теряется молча ---

    def test_write_profile_refuses_to_silently_drop_genuine_critic_line_after_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dpf_md(tmp)
            path = make_adequacy(tmp, "2026-01-01", d_table=make_d_full_table({}))
            # Вручную имитируем нетиповой layout: раздел профиля уже есть, а
            # ПОДЛИННАЯ (не эхо) критик-строка почему-то дописана ПОСЛЕ него.
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(
                    "\n## Профиль зрелости\n\nстарый контент\n\n"
                    "> maturity-critic: L2 confirmed (guardian, 2026-01-01); weak-components: []\n"
                )
            result = maturity.analyze(tmp)
            section = maturity.render_profile_section(result)
            with self.assertRaises(SystemExit):
                maturity.write_profile(path, section)
            # файл не тронут отказавшимся вызовом
            text = open(path, encoding="utf-8").read()
            self.assertIn("> maturity-critic: L2 confirmed (guardian, 2026-01-01); weak-components: []", text)


# ---------------------------------------------------------------------------
# Golden: реальные seed-своды бэнка, скопированные в temp (read-only источник)
# ---------------------------------------------------------------------------


@unittest.skipUnless(os.path.isdir(BANK_FRAMEWORKS), "bank frameworks не найдены в этом дереве")
class GoldenFixtureTests(unittest.TestCase):
    def _copy_pkg(self, name, tmp):
        src = os.path.join(BANK_FRAMEWORKS, name)
        dst = os.path.join(tmp, name)
        shutil.copytree(src, dst)
        return dst

    def test_dpf_coupling_generalization_is_l1(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg_dir = self._copy_pkg("DPF-COUPLING-GENERALIZATION", tmp)
            result = maturity.analyze(pkg_dir)
            self.assertEqual(
                result["level_result"]["final_level"],
                1,
                result["level_result"]["notes"],
            )
            self.assertTrue(result["ctx"]["floor_fragile"], "ожидались floor-fragile координаты")

    def test_lpf_simplification_review_is_l2(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg_dir = self._copy_pkg("LPF-SIMPLIFICATION-REVIEW", tmp)
            result = maturity.analyze(pkg_dir)
            self.assertEqual(
                result["level_result"]["final_level"],
                2,
                result["level_result"]["notes"],
            )
            self.assertEqual(result["ctx"]["floor_fragile"], set())

    def test_golden_next_steps_reference_a_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg_dir = self._copy_pkg("LPF-SIMPLIFICATION-REVIEW", tmp)
            result = maturity.analyze(pkg_dir)
            self.assertTrue(result["next_steps"])
            self.assertTrue(any("support-maps" in s or "authoring" in s for s in result["next_steps"]))

    def test_golden_does_not_mutate_source_repo_files(self):
        # write-profile пишет только во временную копию — исходники бэнка нетронуты.
        src_adequacy = os.path.join(
            BANK_FRAMEWORKS, "LPF-SIMPLIFICATION-REVIEW", "references", "package-adequacy-2026-07-14.md"
        )
        before = open(src_adequacy, encoding="utf-8").read()
        with tempfile.TemporaryDirectory() as tmp:
            pkg_dir = self._copy_pkg("LPF-SIMPLIFICATION-REVIEW", tmp)
            maturity.main([pkg_dir, "--write-profile"])
        after = open(src_adequacy, encoding="utf-8").read()
        self.assertEqual(before, after)


def _run_all():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_run_all())
