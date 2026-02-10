# Полный свод правил TDD (Test-Driven Development)

## Содержание
1. [Философия и суть TDD](#1-философия-и-суть-tdd)
2. [Три закона TDD (Uncle Bob)](#2-три-закона-tdd-uncle-bob)
3. [Канонический TDD (Kent Beck)](#3-канонический-tdd-kent-beck)
4. [Цикл Red-Green-Refactor](#4-цикл-red-green-refactor)
5. [Принципы FIRST для тестов](#5-принципы-first-для-тестов)
6. [Анти-паттерны TDD](#6-анти-паттерны-tdd)
7. [Изоляция и моки](#7-изоляция-и-моки)
8. [TDD с AI-агентами](#8-tdd-с-ai-агентами)
9. [Практические рекомендации](#9-практические-рекомендации)

---

## 1. Философия и суть TDD

**TDD** — это методология разработки, созданная [Kent Beck](https://tidyfirst.substack.com/p/canon-tdd) в конце 1990-х, где тесты пишутся **ДО** кода.

### Цели TDD:
- Писать **"чистый код, который работает"** (Kent Beck)
- Обеспечить уверенность: существующая функциональность не сломана
- Новое поведение работает как ожидается
- Система готова к изменениям

### Ключевой принцип:
> "Превратить страх в скуку" — продолжать цикл, пока неуверенность в поведении кода не превратится в рутину.

---

## 2. Три закона TDD (Uncle Bob)

[Robert Martin](http://blog.cleancoder.com/uncle-bob/2014/12/17/TheCyclesOfTDD.html) формализовал TDD в три закона:

| # | Закон |
|---|-------|
| 1 | **Нельзя писать production-код**, пока нет падающего теста |
| 2 | **Нельзя писать больше теста**, чем достаточно для падения (ошибка компиляции = падение) |
| 3 | **Нельзя писать больше production-кода**, чем достаточно для прохождения теста |

### Гранулярность:
Uncle Bob учился у Kent Beck и описывает процесс как **построчный**: одна строка теста → одна строка кода.

---

## 3. Канонический TDD (Kent Beck)

[Kent Beck определяет](https://tidyfirst.substack.com/p/canon-tdd) пять шагов:

### Шаг 1: Test List
Создать список сценариев и граничных случаев.

**Ошибка**: Смешивать требования с решениями по реализации.

### Шаг 2: Write a Test
Превратить **ровно один** пункт списка в конкретный, запускаемый тест.

**Ошибка**: Писать тесты без assertions только для coverage.

### Шаг 3: Make It Pass
Изменить код, чтобы тест прошёл.

**Ошибка**: Копировать actual-значения в expected (вместо понимания результата).

### Шаг 4: Optionally Refactor
Улучшить дизайн реализации после прохождения тестов.

**Ошибка**: Рефакторить больше, чем нужно для текущей сессии.

### Шаг 5: Repeat Until Empty
Повторять шаги 2-4, пока список не исчерпан.

---

## 4. Цикл Red-Green-Refactor

[Классический цикл TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html):

### RED: Напиши падающий тест
```
1. Написать тест для нужного поведения
2. Предсказать (мысленно/вслух) КАК тест упадёт
3. Запустить тест
4. Убедиться, что падает ОЖИДАЕМЫМ образом
```

### GREEN: Сделай тест зелёным
```
1. Написать МИНИМАЛЬНЫЙ код для прохождения
2. Допустимы: хардкод, if-statements, "fake it till you make it"
3. Цель: ASAP, любой ценой
```

### REFACTOR: Улучши код
```
1. Улучшить дизайн БЕЗ изменения поведения
2. Удалить дублирование
3. Улучшить имена
4. "Искупить грехи" фазы GREEN
```

> [Martin Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html): "Самая частая ошибка — пропускать третий шаг. Рефакторинг критичен, иначе получается хаотичная куча фрагментов."

---

## 5. Принципы FIRST для тестов

[FIRST](https://medium.com/@tasdikrahman/f-i-r-s-t-principles-of-testing-1a497acda8d6) — акроним для качественных unit-тестов (Robert Martin):

| Принцип | Описание | Нарушение |
|---------|----------|-----------|
| **F**ast | Тесты выполняются быстро | Ожидание 30+ минут убивает TDD |
| **I**ndependent | Тесты не зависят друг от друга | Падение одного теста вызывает каскад |
| **R**epeatable | Одинаковый результат в любом окружении | Зависимость от сети, БД, времени |
| **S**elf-validating | Чёткий pass/fail без ручной проверки | "Посмотри в консоль, там должно быть..." |
| **T**imely | Тесты пишутся ДО production-кода | Написание тестов после факта |

### Практические следствия:

```python
# Нарушение Fast
def test_slow():
    time.sleep(5)  # Каждый тест +5 секунд

# Нарушение Independent
def test_second():
    # Зависит от результата test_first
    assert global_state['created_in_test_first']

# Нарушение Repeatable
def test_network():
    response = requests.get('https://external-api.com')  # Может упасть из-за сети

# Правильно
def test_isolated(mock_api):
    mock_api.return_value = {'data': 'test'}
    result = service.fetch_data()
    assert result == {'data': 'test'}
```

---

## 6. Анти-паттерны TDD

[James Carr описал 22+ анти-паттерна](https://www.codurance.com/publications/tdd-antipatters-series). Ключевые:

### The Liar (Лжец)
Тест, который **никогда не может упасть** корректно.

```python
# Тест всегда проходит
def test_liar():
    result = calculate_total([])
    assert True  # Что бы ни случилось
```

### Excessive Setup (Избыточная настройка)
Десятки строк setup для одной проверки.

```python
# 50 строк setup для проверки одного поля
def test_excessive():
    user = create_user()
    company = create_company(user)
    department = create_department(company)
    team = create_team(department)
    project = create_project(team)
    task = create_task(project)
    # ... ещё 40 строк
    assert task.status == 'pending'
```

### The Giant (Гигант)
Множество assertions в одном тесте.

```python
# 20 assertions = 20 причин падения
def test_giant():
    result = process_order(order)
    assert result.id is not None
    assert result.status == 'created'
    assert result.items == [...]
    # ... ещё 17 assertions
```

### The Slow Poke (Тормоз)
Тест выполняется так долго, что разработчики перестают его запускать.

### The Peeping Tom (Подглядывающий)
Тесты видят результаты друг друга через shared state.

### Skipping Refactoring
**Пропуск рефакторинга** — самая частая ошибка по [Martin Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html).

---

## 7. Изоляция и моки

### Когда использовать моки:

| Ситуация | Подход |
|----------|--------|
| Внешние API/сервисы | **Мок** — изоляция от сети |
| База данных | **Мок** для unit, **реальная** для integration |
| Время (datetime) | **Мок** через freezegun |
| Внутренняя логика | **НЕ мокать** — тест становится бессмысленным |

### Правила мокирования:

```python
# Мокаем внешние зависимости
def test_payment(mock_payment_gateway):
    mock_payment_gateway.charge.return_value = {'status': 'success'}
    result = order_service.process_payment(order)
    assert result.paid

# Не мокаем внутреннюю логику
def test_over_mocked():
    # Мокаем всё, тест ничего не тестирует
    mock_calculator.calculate.return_value = 100
    assert process(mock_calculator) == 100  # Бессмысленно
```

### [Баланс моков и интеграционных тестов](https://www.jamesshore.com/v2/blog/2018/testing-without-mocks):

> "Если тестировать код трудно — использовать его тоже трудно."

Изолируйте side-effects:
```python
# Разделение логики и I/O
def calculate_discount(order: Order) -> Decimal:
    """Чистая функция — легко тестировать"""
    if order.total > 1000:
        return order.total * Decimal('0.1')
    return Decimal('0')

def apply_discount(order_id: int) -> None:
    """Оркестрация — тестируем интеграционно"""
    order = Order.objects.get(id=order_id)
    discount = calculate_discount(order)
    payment_service.apply(order, discount)
```

---

## 8. TDD с AI-агентами

### Исследования показывают эффективность

Согласно [исследованиям IEEE/ACM](https://dl.acm.org/doi/10.1145/3691620.3695527):
- Предоставление тестов LLM **улучшает качество генерации кода**
- GPT-4 с тестами решает больше задач, чем без них
- TDD особенно эффективен для repository-level задач

### Workflow TDD + AI-агент

```
1. ЧЕЛОВЕК пишет тест (определяет контракт)
2. AI генерирует код для прохождения теста
3. ЧЕЛОВЕК проверяет код и запускает тесты
4. AI рефакторит при необходимости
5. Повтор
```

### Ключевые принципы:

| Принцип | Обоснование |
|---------|-------------|
| **Тесты пишет человек** | Человек определяет требования и границы |
| **AI генерирует реализацию** | AI хорош в написании кода по спецификации |
| **Тесты — это спецификация** | AI получает чёткие ограничения |
| **Edge cases заранее** | Включайте граничные случаи в тесты сразу |

### Особенности тестирования AI-систем

Согласно [LangWatch](https://langwatch.ai/blog/from-scenario-to-finished-how-to-test-ai-agents-with-domain-driven-tdd):

```python
# Традиционное тестирование: детерминированный результат
assert calculate_sum([1, 2, 3]) == 6

# AI-тестирование: многомерная оценка
def test_ai_response():
    response = ai_agent.generate(prompt)

    # Проверяем несколько аспектов
    assert len(response) < 500  # Длина
    assert 'ключевое_слово' in response  # Содержание
    assert not contains_pii(response)  # Безопасность
    assert llm_judge.evaluate(response) > 0.8  # Качество
```

### Подходы к тестированию LLM-приложений

Из [DAGWorks](https://blog.dagworks.io/p/test-driven-development-tdd-of-llm):

1. **Exact matching** — точное соответствие
2. **Fuzzy matching** — семантическое сходство
3. **LLM-based grading** — AI оценивает AI
4. **Human review** — человеческая оценка
5. **Static measures** — длина, формат, safety checks

```python
import pytest

@pytest.mark.parametrize('prompt,expected_keywords', [
    ('Объясни TDD', ['тест', 'разработка', 'цикл']),
    ('Что такое Python', ['язык', 'программирование']),
])
def test_llm_response_contains_keywords(prompt, expected_keywords):
    response = llm.generate(prompt)
    for keyword in expected_keywords:
        assert keyword.lower() in response.lower()
```

### Variance Testing для AI

```python
def test_llm_consistency():
    """Запускаем один промпт несколько раз для проверки стабильности"""
    responses = [llm.generate('Объясни TDD') for _ in range(5)]

    # Все ответы должны содержать ключевые концепции
    for response in responses:
        assert 'тест' in response.lower()
        assert len(response) > 100
```

---

## 9. Практические рекомендации

### Структура теста (AAA/Given-When-Then)

```python
def test_order_discount():
    # Arrange / Given
    order = Order(items=[Item(price=1500)])

    # Act / When
    discount = calculate_discount(order)

    # Assert / Then
    assert discount == Decimal('150')
```

### Именование тестов

```python
# Паттерн: test__{что_тестируем}__{сценарий}__{ожидаемый_результат}
def test__calculate_discount__order_over_1000__returns_10_percent(): ...
def test__calculate_discount__order_under_1000__returns_zero(): ...
def test__process_payment__gateway_timeout__raises_error(): ...
```

### Один тест = одно поведение

```python
# Плохо: тестируем несколько вещей
def test_user_registration():
    user = register_user(email='test@test.com')
    assert user.id is not None
    assert user.email_verified is False
    assert len(user.password_hash) == 64
    assert notification_sent(user.email)

# Хорошо: отдельные тесты для каждого аспекта
def test__register_user__creates_user_with_id(): ...
def test__register_user__email_not_verified_by_default(): ...
def test__register_user__password_is_hashed(): ...
def test__register_user__sends_notification(): ...
```

### Когда НЕ использовать TDD

Согласно [Brainhub](https://brainhub.eu/library/test-driven-development-tdd):

| Ситуация | Рекомендация |
|----------|--------------|
| Быстрый прототип | Пропустить TDD |
| Exploratory coding | Сначала исследовать, потом тесты |
| Жёсткие дедлайны | TDD требует времени на старте |
| Legacy без тестов | Сначала покрыть критичное |
| UI/UX эксперименты | Тесты после стабилизации |

### Целевое покрытие

> Стремитесь к **70-80% осмысленного покрытия**, а не к 100% compliance. ([Codurance](https://www.codurance.com/publications/tdd-anti-patterns-chapter-1))

---

## Чек-лист безопасного TDD

### Перед написанием теста:
- [ ] Понимаю требуемое поведение
- [ ] Тест проверяет ОДНО поведение
- [ ] Имя теста описывает сценарий и ожидание
- [ ] Продумал граничные случаи

### При написании теста:
- [ ] Тест падает по ПРАВИЛЬНОЙ причине
- [ ] Setup минимален и понятен
- [ ] Assertions конкретны и информативны
- [ ] Нет зависимости от других тестов

### После прохождения теста:
- [ ] Код минимален для прохождения
- [ ] Провёл рефакторинг
- [ ] Тесты всё ещё зелёные
- [ ] Удалил дублирование

### С AI-агентом:
- [ ] Тест написан человеком (спецификация)
- [ ] AI генерирует реализацию
- [ ] Проверил сгенерированный код
- [ ] Edge cases включены в тесты заранее

---

## Sources

- [Canon TDD - Kent Beck](https://tidyfirst.substack.com/p/canon-tdd)
- [The Cycles of TDD - Uncle Bob](http://blog.cleancoder.com/uncle-bob/2014/12/17/TheCyclesOfTDD.html)
- [Test Driven Development - Martin Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [TDD Anti-patterns - Codurance](https://www.codurance.com/publications/tdd-antipatters-series)
- [FIRST Principles of Testing](https://medium.com/@tasdikrahman/f-i-r-s-t-principles-of-testing-1a497acda8d6)
- [TDD and LLM Code Generation - IEEE/ACM](https://dl.acm.org/doi/10.1145/3691620.3695527)
- [TDD for LLM Applications - DAGWorks](https://blog.dagworks.io/p/test-driven-development-tdd-of-llm)
- [Testing AI Agents with Domain-Driven TDD - LangWatch](https://langwatch.ai/blog/from-scenario-to-finished-how-to-test-ai-agents-with-domain-driven-tdd)
- [AI-Powered TDD Guide 2025](https://www.nopaccelerate.com/test-driven-development-guide-2025/)
- [Testing Without Mocks - James Shore](https://www.jamesshore.com/v2/blog/2018/testing-without-mocks)
- [TDD Quick Guide - Brainhub](https://brainhub.eu/library/test-driven-development-tdd)
