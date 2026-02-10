# P0: Context-Adaptive Default Values

> **Зависимостям — минимум для валидности, потребителям — максимум для пользы.**

Это универсальный принцип проектирования, применимый к любым компонентам: fixtures, factories, API defaults, конфигурации.

---

## Core Rule

Один и тот же концепт может иметь разные defaults в зависимости от роли в коде:

| Роль компонента | Оптимальные defaults | Почему |
|-----------------|---------------------|--------|
| **FK-зависимость** | Минимально валидные | Потребителю не важны детали |
| **Точка входа** | Максимально полезные | Потребитель хочет работать, не настраивать |
| **Edge case** | Явно отличающиеся | Отклонение должно быть видимым |

---

## 1. FK-зависимость (минимум для валидности)

Объект создаётся только для удовлетворения внешнего ключа. Потребителю не важны его детали.

```python
@pytest.fixture()
def campaign(db) -> Campaign:
    """Минимально валидный объект для FK-зависимостей."""
    return Campaign.objects.create(
        name='Test Campaign',
        status=CampaignStatus.ACTIVE,
    )
```

**Правило**: Только обязательные поля. Никаких "на всякий случай" данных.

---

## 2. Точка входа (максимум пользы)

Объект создаётся для работы — потребитель хочет использовать его сразу, без настройки.

```python
@pytest.fixture()
def create_applicant(huntflow_admin) -> Callable[..., CreatedApplicant]:
    """
    Default: полный applicant с Tilda данными.
    Edge case: with_tilda=False для миграционных сценариев.
    """
    def _create(
        with_tilda: bool = True,
        tilda_position: str = 'backend',
        telegram: str = '@testuser',
        resume: str = 'https://github.com/test',
        ...
    ) -> CreatedApplicant:
        ...
    return _create
```

**Правило**: Вызов без параметров создаёт объект для типичного сценария.

---

## 3. Edge case (явное отклонение)

Отклонение от типичного сценария должно быть явно маркировано параметром.

```python
def test__migrated_applicant__gets_tilda_from_migration_task(create_applicant):
    applicant = create_applicant(with_tilda=False)  # Явно маркирован
    ...
```

**Правило**: Edge case объясняется контекстом, а не комментарием.

---

## Матрица выбора механизма

| Что варьируется | Механизм | Пример |
|-----------------|----------|--------|
| Полнота объекта | Отдельный класс/фикстура | `NonInitializedPerson` vs `Person` |
| Состояние процесса | Trait или bool-параметр | `bound_smz=True`, `with_tilda=False` |
| Конкретные данные | Параметры функции | `position='backend'` |

### Трёхуровневая типология (Factory Boy)

**1. Structural level** — принципиально разный набор полей:
```python
class NonInitializedPersonFactory(DjangoModelFactory):
    """Минимум для FK."""
    inn = factory.Faker('individuals_inn')

class PersonFactory(NonInitializedPersonFactory):
    """Полный объект для тестов."""
    first_name = factory.Faker('first_name_male')
    last_name = factory.Faker('last_name_male')
```

**2. State level** — разные этапы бизнес-процесса:
```python
class Params:
    smz = factory.Trait(npd_status=REGISTERED)
    bound_smz = factory.Trait(smz=True, partner_bound_at=...)
```

**3. Data level** — вариативность данных без изменения семантики:
```python
def create_applicant(
    tilda_position: str = 'backend',
    telegram: str = '@testuser',
):
```

---

## Критерии проверки

1. **Тест "пустого вызова"** — вызов без параметров делает "правильную вещь"
2. **Тест "нулевой документации"** — разработчик может использовать без документации
3. **Тест "объяснимых исключений"** — edge case объясняется контекстом

---

## ВАЖНО: Default ≠ Error Hiding

| Ситуация | Правильное поведение |
|----------|---------------------|
| Данных нет (легитимно) | `return None` — это default |
| Данные есть, но ошибка парсинга | `raise` — это баг |
| Внешний API вернул ошибку | `raise` — нужно знать |

Возврат "пустого" значения при ошибке — это НЕ "поведение по умолчанию", это Error Hiding.

---

## Антипаттерны

```python
# ❌ Trait для каждого значения
class Params:
    backend_position = factory.Trait(position='backend')
    frontend_position = factory.Trait(position='frontend')

# ✅ Параметр функции
def create_applicant(tilda_position: str = 'backend'):
    ...

# ❌ Две функции вместо параметра
def create_applicant_with_tilda(...): ...
def create_applicant_without_tilda(...): ...

# ✅ Один параметр для edge case
def create_applicant(with_tilda: bool = True):
    ...
```

---

## Применение за пределами тестов

Принцип P0 работает везде:

| Контекст | FK-зависимость (минимум) | Точка входа (максимум) |
|----------|--------------------------|------------------------|
| **Fixtures** | `Campaign(name='Test')` | `create_applicant(with_tilda=True, ...)` |
| **Factories** | `NonInitializedPersonFactory` | `PersonFactory` |
| **API defaults** | Internal DTO: только required | Public API: sensible defaults |
| **Config** | Library internals: minimal | User config: works out of box |

**Критерий**: Компонент должен быть полезен без документации в своём контексте.
