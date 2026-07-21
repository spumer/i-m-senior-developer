# CONTRIBUTING — вход в fpf-competency-bank

Этот файл — правила допуска пакета (DPF/LPF) в банк. Как писать сам пакет — не здесь, а в `dpf-authoring` (плагин `fpf-integration`, скилл `dpf-authoring`, `references/method.md`): 6-фазный конвейер авторинга.

## Различение DPF/LPF

Два критерия решают `kind`, и `kind` обязан совпасть с ОБОИМИ:
- **SoTA-опора** — свод стоит минимум на 3 независимых традициях/источниках (не на одном фреймворке и не на личном опыте автора);
- **Объявленный контекст/читатель** — `declaredDomainOrLocalContext` и `intendedReaderOrOperator` явно названы во frontmatter/теле пакета.

Если контекст доменный (применим за пределами одного проекта/пайплайна) и SoTA-опора есть — `kind: "Domain Principle Framework"`. Если контекст локален к конкретному пайплайну/проекту — `kind: "Local Practice Framework"`, даже при сильной SoTA-опоре. За глубиной различения — `dpf-authoring/references/method.md`.

## Fail-closed гейт двух слоёв

Пакет входит в банк, только если проходит ОБА слоя. Провал любого — пакет в банк не входит.

**Слой 1 — механика.** `resolve.py --verify <id> --scope bank`:
- структура и обязательные поля frontmatter (`dpf_id`, `kind`, `status`, `review_due`, `owner`);
- `kind` из enum (`Domain Principle Framework` \| `Local Practice Framework`);
- свежесть (`status: active`, `review_due` не истёк);
- положительная финальная conformance-строка в `DPF.md` — `E.4.DPF.DA: admissibleForDeclaredDPFUse`. Источник — сам `DPF.md`, не `references/`.

**Слой 2 — содержание.** Критик `dpf-authoring`, роль `DPF-ADVERSARIAL-REVIEW` (E.4.DPF.DA): проверка по PFM1–PFM11 и D1–D11, статус вердикта. Этот слой ловит то, что механика не видит: несогласованный `kind`, отсутствие ≥3 традиций в SoTA, `seedOnly`-пакет с формально правильной структурой, но без содержательной опоры.

**Итог.** `seedOnly` и `repairBeforeDPFUse` (нет положительной conformance-строки) в банк не входят — независимо от того, насколько аккуратна структура файла.
