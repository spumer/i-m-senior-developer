# Pytest Testing Patterns

Паттерны организации тестов с pytest. Применимы к любому Python-проекту.

---

## 1. Fixture Organization

### File Structure

```
tests/
├── conftest.py              # Global pytest configuration
├── fixtures/                # All fixture modules
│   ├── __init__.py
│   ├── fixtures.py          # Common test data fixtures
│   ├── fns.py               # FNS service mock
│   ├── apibank.py           # ApiBank service mock
│   ├── esb.py               # ESB service mock
│   └── const.py             # Constants used across tests
```

### Plugin Registration

```python
pytest_plugins = [
    'tests.fixtures.fixtures',
    'tests.fixtures.fns',
    'tests.fixtures.apibank',
    # ... all fixture modules
]
```

**RULE**: All fixtures must be registered in `pytest_plugins` list in `conftest.py`.

### Conftest Organization

Conftest.py should contain (in order):

1. Library imports and configuration
2. Platform-specific workarounds
3. Third-party library patches
4. Plugin registration (`pytest_plugins`)
5. Session-level fixtures (`autouse=True`)
6. Common fixtures used across all tests

```python
import platform
import freezegun
import requests_mock.response
import simplejson

# Configure libraries
requests_mock.response.jsonutils = simplejson

# Platform-specific workarounds
if platform.system() == 'Darwin':
    import socket
    socket.gethostbyname = lambda x: '127.0.1'

# Register fixture plugins
pytest_plugins = [
    'tests.fixtures.fixtures',
    # ...
]

# Session-level configuration
@pytest.fixture(scope='session', autouse=True)
def _logging_no_console_handler(request):
    """Disable console logging for CI."""
    ...

# Common fixtures
@pytest.fixture()
def assert_all_responses_were_requested() -> bool:
    return False
```

---

## 2. Fixture Defaults (P0 Pattern)

> See **`references/P0_DEFAULT_CONTEXT.md`** for the full P0 pattern (always loaded, framework-agnostic).

**Quick reminder**: FK = minimal, Entry point = maximal, Edge case = explicit.

---

## 3. Fixture Composition

### Layered Fixture Dependencies

```python
@pytest.fixture()
def fns_server(requests_mock, httpx_mock):
    """Low-level server mock"""
    server = FakeFNSServer(requests_mock, httpx_mock)
    yield server
    # Teardown assertion
    for resp_type, resp_queue in server.response_type2response_queues.items():
        assert not resp_queue, f'Unconsumed responses for {resp_type}'

@pytest.fixture()
def fns_admin(fns_server):
    """High-level admin interface for test setup"""
    admin = FNSAdmin(fns_server)
    yield admin
    # Teardown assertion
    for inn, notifications in admin.inn2notifications.items():
        taxpayer = admin.taxpayers.get(inn)
        if taxpayer and taxpayer.permissions:
            assert all(n.is_delivered for n in notifications)
```

**RULE**: Create layered fixtures:
- **Low-level** (`fns_server`): Direct mock control
- **High-level** (`fns_admin`): Business-logic-friendly interface

### Fixture Assertions in Teardown

Fixtures can include assertions in teardown to verify:
- All enqueued responses were consumed
- All expected side effects occurred
- No unexpected state remains

### Parametrized Fixtures

```python
@pytest.fixture(params=['300005480'], ids=['default'])
def customer_code(request):
    return request.param

@pytest.fixture(params=['I', 'J'])
def customer_type(request):
    assert request.param in ['I', 'J']
    return request.param

@pytest.fixture(params=[None], ids=['not_set'])
def compliance_status(request):
    if request.param is not None:
        assert request.param in CustomerComplianceStatus.__members__
    return request.param
```

**RULE**: Use parametrized fixtures for:
- Different entity types (Individual vs Legal)
- Optional values (None vs set)
- Test variations across multiple tests

---

## 4. Test Organization

### Module-level Markers

```python
pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.parametrize(
        '_stub_fns_requests_grinder',
        ['disabled'],
        indirect=['_stub_fns_requests_grinder'],
    ),
]
```

**RULE**: Use module-level `pytestmark` for markers applied to ALL tests in file.

### Test Naming Convention

```python
# Pattern: test__{scenario}__{outcome}
def test__process_response_from_fns__ok(...)
def test__no_response_from_fns__offline_registration_ok(...)
def test_non_smz__fail(...)
def test_partner_not_bound__fail(...)
```

**RULE**:
- Use double underscore `__` to separate test parts
- End with `__ok` for success cases, `__fail` for error cases
- Middle part describes the scenario

---

## 5. End-to-End Flow Test Pattern

**Один тест = один бизнес-flow от входа до выхода.**

### Правило 1: Тест отражает реальный pipeline

```python
# ✅ Хорошо: полный flow в одном тесте
def test__welcome_email__full_flow():
    applicant = create_applicant(...)           # Вход
    outbox = create_welcome_email_outbox(...)   # Шаг 1
    process_email_outbox()                      # Шаг 2
    assert len(mail.outbox) == 1                # Выход
    assert applicant.status == 'sent'           # Побочный эффект

# ❌ Плохо: отдельные тесты на каждый шаг
def test__create_outbox(): ...
def test__process_outbox(): ...
```

### Правило 2: Параметризация — только для данных, не для поведения

```python
# ✅ Одинаковое поведение, разные данные
@pytest.mark.parametrize('position,form_id', [
    (FRONTEND, 'THXtCMfZ'),
    (QA, 'uXiIWpuQ'),
])
def test__welcome_email__typeform_positions(position, form_id):
    assert f'typeform.com/to/{form_id}#user_id=' in html

# ✅ Разный фокус = разные тесты
def test__backend_with_cabinet__creates_invite(): ...
def test__backend_without_contest__logs_warning(): ...

# ❌ Параметризация меняет суть проверки
@pytest.mark.parametrize('has_contest,expected_behavior', [
    (True, 'invite_created'),
    (False, 'warning_logged'),  # Это другой тест!
])
def test__backend(has_contest, expected_behavior):
    if expected_behavior == 'invite_created':  # if = красный флаг
        ...
```

**Индикатор:** `if` по параметру в тесте — сигнал разделить на отдельные тесты.

### Правило 3: Сложность — в фикстурах, простота — в тесте

```python
@pytest.fixture()
def campaign_with_contest(campaign, cabinet_admin):
    cabinet_contest = cabinet_admin.create_contest(...)
    contest = Contest.objects.create(...)
    campaign.contest = contest
    campaign.save()
    return campaign

def test__backend_with_cabinet(campaign_with_contest):
    applicant = create_applicant(campaign=campaign_with_contest)
    # ... простой flow
```

### Метрика качества

```
N_тестов = N_уникальных_flows + N_edge_cases
```

Не `N_функций × N_параметров`.

---

## 6. Assertion Helpers

```python
from testing import AnyDict, ReStr, UnorderedList, model_to_dict

# Partial dict matching (specified keys only, ignores others)
assert response == AnyDict({
    'status': 'success',
    'data': {'id': ReStr(r'[a-f0-9-]{36}')},
})

# Order-independent list matching
assert events == UnorderedList([event1, event2])

# Regex string matching
assert_log_messages(ReStr(r'.*?<Amount>33000\.1</Amount>.*?'))

# Django model comparison (excluding timestamps)
assert model_to_dict(obj, exclude=['created_at']) == expected_dict
```

**RULE**: Use custom matchers for:
- **AnyDict**: Partial dict matching
- **UnorderedList**: Order-independent list matching
- **ReStr**: Regex string matching
- **model_to_dict**: Model comparison (excluding volatile fields)

### Assertions через AnyDict/ReStr — проверяй важное, игнорируй шум

```python
# ✅ Проверяем структуру, не привязываемся к деталям
assert outbox.data == AnyDict({
    'email': 'test@example.com',
    'form_url': ReStr(r'typeform\.com.*#user_id='),
})

# ❌ Хрупкие точные сравнения
assert outbox.data == {
    'email': 'test@example.com',
    'form_url': 'https://form.typeform.com/to/ABC123#user_id=550e8400-...',
    'created_at': '2025-01-22T12:00:00Z',  # Зачем?
}
```

---

## 7. External Service Mocking

### Stateful Fake Servers

```python
class FakeApiBank:
    """Stateful mock for synchronous API."""

    def __init__(self, requests_mock):
        self.requests_mock = requests_mock
        self.customers: Dict[str, Customer] = {}
        self.received_requests: List[Request] = []

        requests_mock.get(
            re.compile(r'.*/customers/.*'),
            json=self._get_customer_response
        )

    def _get_customer_response(self, request, context):
        customer_code = self._extract_code(request.url)
        customer = self.customers.get(customer_code)
        if customer is None:
            context.status_code = 404
            return {'error': 'Customer not found'}
        context.status_code = 200
        return customer.to_dict()
```

### Admin Pattern for Test Data Setup

```python
class FNSAdmin:
    """High-level interface for managing mock state."""

    def __init__(self, fns: FakeFNSServer):
        self.fns = fns
        self.taxpayers = {}

    def reg_taxpayer(self, inn: str, permissions=None):
        taxpayer = Taxpayer(inn=inn, permissions=permissions)
        self.taxpayers[taxpayer.inn] = taxpayer
```

### Response Management Approaches

**A. Dict-based States (Default — Synchronous APIs)**

```python
def test_get_customer__exists(apibank, customer_code):
    # 1. Setup state
    apibank.reg_customer({'code': customer_code, 'fullName': 'Test'})
    # 2. Execute
    result = customer_service.get_customer(customer_code)
    # 3. Verify
    assert result.code == customer_code
```

**B. Queue-based Responses (ONLY for Asynchronous APIs)**

```python
def test_threshold__fail(fns_admin, create_income_request):
    # 1. Enqueue response
    income_request = create_income_request(protocol.SmzPlatformError(...))
    # 2. Execute
    tasks.register_taxpayer_income()
    # 3. Verify
    income_request.refresh_from_db()
    assert income_request.state == IncomeRequestState.ERROR
```

**RULE**: Dict-based by default. Queue-based ONLY for async APIs.

### Force Response Pattern

```python
class ApiBank:
    def force_response(self, func, status_code, json=None):
        self.force_responses[func.__name__].append((status_code, json))

# Usage
def test_apibank_error(apibank):
    apibank.force_response(apibank.get_customer_full, status_code=500)
    with pytest.raises(ApiError):
        customer_service.get_customer('12345')
```

### Request History Verification

```python
def test_api_call(apibank):
    # ... execute ...
    history = apibank.get_history(apibank.get_customer_full)
    assert len(history) == 1
    assert 'customerParts=DOCUMENTS' in history[0].url
```

**RULE**: Verify external API calls by:
- Checking `received_requests` in mock server
- Using `.get_history()` on matcher functions
- Asserting request parameters, not just that call was made

---

## 8. Time Control

### Freezegun

```python
@pytest.mark.parametrize('mode', ['exact-moment', 'late-moment'])
def test_finish(freezer2, mode):
    bind_request = factories.BindRequestFactory.create(
        finished=False,
        auto_finish_at=timezone.now() + dt.timedelta(seconds=1)
    )

    if mode == 'exact-moment':
        freezer2.tick(dt.timedelta(seconds=1))
    else:
        freezer2.tick(dt.timedelta(seconds=2))

    tasks.autofinish_bind_requests()
    bind_request.refresh_from_db()
    assert bind_request.finished
```

**RULE**:
- Use `freezer2` fixture (custom freezegun wrapper)
- Use `.tick()` to advance time
- Test both exact timing and "late" scenarios

---

## 9. Logging Verification

```python
def test_strip_invalid_xml_chars(fns_server, assert_log_messages):
    # ... setup and execute ...
    assert_log_messages(
        ReStr(r'.*?<Amount>33000\.1</Amount>.*?'),
        remove_whitespaces=False
    )

def test_invalid_hash__log_exception(assert_log_errors):
    # ... setup and execute ...
    assert_log_errors(
        f'Неправильный хэш для чека {income_request.pk}'
    )
```

**RULE**: Use logging assertion fixtures:
- `assert_log_messages`: Verify info/debug logs
- `assert_log_errors`: Verify error logs
- Use `ReStr` for regex matching in logs

---

## 10. Error Hiding Protection

```python
# ❌ Exception can be swallowed by intermediate layers
if not event.wait(timeout=2.0):
    raise TimeoutError('Test timeout')

# ✅ pytest.fail() cannot be caught by try-except
if not event.wait(timeout=2.0):
    pytest.fail('Test design error: timeout waiting for event')
```

**RULE**: Use `pytest.fail()` instead of `raise` in tests to prevent Error Hiding.

---

## Summary of Key Rules

### Fixture Design:
1. Register all fixture modules in `pytest_plugins`
2. Create layered fixtures (low-level + high-level admin)
3. Use parametrized fixtures for test variations
4. Include teardown assertions in fixtures
5. Follow P0 defaults pattern (FK=minimal, entry=maximal)

### Test Structure:
6. Apply module-level markers via `pytestmark`
7. Name tests with `test__{scenario}__{outcome}` pattern
8. One test = one business flow (end-to-end)
9. Parametrize data, not behavior

### Assertions:
10. Use custom matchers (AnyDict, UnorderedList, ReStr)
11. Verify side effects (events, signals, logs)
12. Check request history in mock servers

### External Mocking:
13. Create stateful fake servers, not simple stubs
14. Provide Admin classes for easy setup
15. Dict-based states by default, queue-based only for async
16. Verify all enqueued responses consumed in teardown
