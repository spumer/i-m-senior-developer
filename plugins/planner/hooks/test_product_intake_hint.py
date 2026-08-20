#!/usr/bin/env python3
"""Тесты UserPromptSubmit-хука `product_intake_hint.py`.

Запуск:
  python3 test_product_intake_hint.py
  python3 -m unittest test_product_intake_hint

stdlib only (unittest) — pytest в окружении отсутствует.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import product_intake_hint as hook  # noqa: E402

HOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "product_intake_hint.py")

PRODUCT_PROMPTS = (
    "Есть мысль: люди у нас теряют то, что сами же сохранили. Обсудим?",
    "Надо сделать корзину для удалённых элементов, историю изменений по каждому "
    "элементу и уведомления, когда кто-то другой правит твой элемент. С чего начнём?",
    "Есть идея — давай обсудим",
    "Хотим, чтобы пользователь мог вернуть удалённое. С чего начать?",
    "/plan-idea сырой замысел про поиск",
    "/plan-epic собрать общую гипотезу",
    "/plan-roadmap задать порядок фич",
    "/plan-feat требования фичи",
)

TECHNICAL_PROMPTS = (
    "Почему падает тест test_sync_rejects_stale_parent?",
    "Отрефактори этот модуль, он разросся",
    "Исправь баг: helper затирает подготовленный файл",
    "Оптимизируй запрос, он выполняется 4 секунды",
    "Реализуй по готовой архитектуре из ARCHITECTURE.md",
    "Какой синтаксис у tool_used грейдера?",
)


class DetectProductIntakeTests(unittest.TestCase):
    def test_product_shaped_prompts_are_detected(self) -> None:
        for prompt in PRODUCT_PROMPTS:
            with self.subTest(prompt=prompt):
                self.assertTrue(hook.is_product_intake(prompt))

    def test_technical_prompts_are_not_detected(self) -> None:
        for prompt in TECHNICAL_PROMPTS:
            with self.subTest(prompt=prompt):
                self.assertFalse(hook.is_product_intake(prompt))

    def test_technical_marker_suppresses_idea_wording(self) -> None:
        prompt = "Есть идея, как исправить баг в парсере — обсудим?"
        self.assertFalse(hook.is_product_intake(prompt))

    def test_product_command_wins_over_technical_marker(self) -> None:
        self.assertTrue(hook.is_product_intake("/plan-feat починить баг в корзине"))

    def test_empty_prompt_is_not_detected(self) -> None:
        self.assertFalse(hook.is_product_intake(""))
        self.assertFalse(hook.is_product_intake("   \n"))


class ParsePromptPayloadTests(unittest.TestCase):
    def test_valid_payload_returns_prompt(self) -> None:
        self.assertEqual(
            hook.parse_prompt_payload('{"prompt": "есть идея, обсудим?"}'),
            "есть идея, обсудим?",
        )

    def test_broken_or_missing_payload_returns_empty(self) -> None:
        for raw in ("", "   ", "{not json", "[1,2]", "{}", '{"prompt": 42}'):
            with self.subTest(raw=raw):
                self.assertEqual(hook.parse_prompt_payload(raw), "")


class HintTextTests(unittest.TestCase):
    def test_hint_names_the_skill_and_forbids_direct_answer(self) -> None:
        text = hook.build_hint()
        self.assertIn("planner:product-discovery", text)
        self.assertIn("Skill", text)


class HookProcessTests(unittest.TestCase):
    def run_hook(self, payload: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, HOOK_PATH],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_product_prompt_emits_hint_and_exits_zero(self) -> None:
        payload = json.dumps({"prompt": PRODUCT_PROMPTS[0], "session_id": "s1"})

        result = self.run_hook(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("planner:product-discovery", result.stdout)

    def test_technical_prompt_stays_silent_and_exits_zero(self) -> None:
        payload = json.dumps({"prompt": TECHNICAL_PROMPTS[0], "session_id": "s1"})

        result = self.run_hook(payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_broken_payload_never_blocks_the_prompt(self) -> None:
        result = self.run_hook("{not json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
