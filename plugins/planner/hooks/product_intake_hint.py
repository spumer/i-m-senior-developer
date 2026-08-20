#!/usr/bin/env python3
"""UserPromptSubmit-хук: продуктовый вход направляется в скилл проработки.

Хук не решает продуктовую задачу и ничего не пишет. Он опознаёт вход, который
должен попасть в `planner:product-discovery`, и выкладывает одну строку
требования. Опознание — только по явным признакам, без смыслового разбора.

Три канала срабатывания:
  1. Продуктовая команда в промпте (`/plan-idea`, `/plan-epic`, `/plan-roadmap`,
     `/plan-feat`) — сильнейший признак, технические маркеры его не отменяют.
  2. Формулировка замысла («есть идея», «есть мысль», «замысел», «хотим»).
  3. Вопрос о начале работы («с чего начнём», «с чего начать») — он отличает
     продуктовый запрос от простого упоминания фич.

Технические маркеры (баг, падает тест, рефактор, оптимизируй, готовая
архитектура) подавляют каналы 2 и 3: там продуктовые решения уже приняты.

Промпт никогда не блокируется: любой разбор входа завершается кодом 0.

Только stdlib.
"""

from __future__ import annotations

import json
import re
import sys

SKILL_NAME = "planner:product-discovery"

PRODUCT_COMMANDS = (
    "/plan-idea",
    "/plan-epic",
    "/plan-roadmap",
    "/plan-feat",
)

IDEA_MARKERS = (
    r"есть\s+иде[яю]",
    r"есть\s+мысл[ьи]",
    r"замысел",
    r"хотим",
    r"хочется",
    r"обсуди[мт]",
)

START_QUESTION_MARKERS = (
    r"с\s+чего\s+нач",
    r"с\s+чего\s+бы\s+нач",
    r"откуда\s+нач",
)

TECHNICAL_MARKERS = (
    r"баг",
    r"падает\s+тест",
    r"стектрейс",
    r"traceback",
    r"отрефактори",
    r"рефактор",
    r"оптимизируй",
    r"почему\s+не\s+работает",
    r"почему\s+падает",
    r"готов[ойая]\s+архитектур",
    r"синтаксис",
)


def matches_any(prompt: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, prompt, re.IGNORECASE | re.UNICODE) for pattern in patterns)


def has_product_command(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(command in lowered for command in PRODUCT_COMMANDS)


def is_product_intake(prompt: str) -> bool:
    """Опознаёт продуктовый вход. Пустой промпт и технические запросы — нет."""
    if not prompt.strip():
        return False
    if has_product_command(prompt):
        return True
    if matches_any(prompt, TECHNICAL_MARKERS):
        return False
    return matches_any(prompt, IDEA_MARKERS) or matches_any(prompt, START_QUESTION_MARKERS)


def build_hint() -> str:
    return (
        f"Это продуктовый вход. Вызови инструментом Skill скилл `{SKILL_NAME}` "
        "до ответа: сначала проблема, люди, исходы, границы и порядок срезов, "
        "и только потом техническое решение."
    )


def parse_prompt_payload(raw: str) -> str:
    """Достаёт поле промпта из JSON payload UserPromptSubmit. Битый JSON -> ''."""
    if not raw.strip():
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    prompt = payload.get("prompt", "")
    return prompt if isinstance(prompt, str) else ""


def main() -> int:
    prompt = parse_prompt_payload(sys.stdin.read())
    if is_product_intake(prompt):
        print(build_hint())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
