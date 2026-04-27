# FEAT-0004 — Plugin `sdlc-mobile` (Mobile stack: Android/iOS/React Native)

> **Статус:** Backlog
> **Marketplace:** `i-m-senior-developer`
> **Категория:** development / mobile
> **Зависимость:** требует FEAT-0002 (`sdlc`) — расширение skills под mobile-стек.

## Problem Statement

`sdlc` плагин (FEAT-0002) покрывает backend-python и frontend-react (web). Mobile-задачи (нативный Android/iOS, React Native, Flutter) остаются без покрытия — оркестратор `/plan-do` для мобильной фичи попадает в gap.

## Scope (черновик)

Mobile отличается от web/backend по нескольким осям:
- **Lifecycle и state management** другие (Activity/Fragment, ViewController, navigation stacks).
- **Build pipelines** специфичны (Gradle, Xcode, Fastlane).
- **Distribution** через store'ы (App Store Connect, Google Play Console).
- **Тестирование** — instrumentation, espresso, XCUITest, snapshot tests.
- **Performance constraints** жёстче (battery, network, memory).

Возможны три пути:

**Вариант A — расширение FEAT-0002:**
- `architect/references/mobile-android.md`, `mobile-ios.md`, `react-native.md`, `flutter.md`
- `code-implementer/references/mobile-android.md`, ...
- `code-reviewer/references/mobile-android.md`, ...

**Вариант B — отдельный плагин `sdlc-mobile`:**
3 skill, специализированных под mobile-цикл (включая отдельный hand-off под distribution).

**Вариант C — два под-плагина:**
`sdlc-mobile-native` (Android+iOS) и `sdlc-mobile-cross` (RN+Flutter) — если разница в практиках слишком большая.

Решение принять при подъёме фичи из backlog.

## Triggers (когда вынуть из backlog)

- Появился реальный мобильный проект, где установлен `sdlc` и нужен multi-agent конвейер.
- Или: набралось 3+ просьб от пользователей плагина.

## Open Questions

1. **React Native vs Flutter** — два разных стека или одно «cross-platform»?
2. **TDD на iOS/Android:** XCTest/Espresso — что считать минимумом для Definition of Done?
3. **CI/CD** — пересечение с FEAT-0003 (sdlc-infra)? Кто owns Fastlane lanes?
4. **App Store / Play Console** — нужны ли automation-helpers как часть скилла?

## Sources

Будут добавлены при подъёме из backlog.

---

**Status:** On hold. Не двигать без явного запроса.
