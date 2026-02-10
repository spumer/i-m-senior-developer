# Django Testing Patterns

Паттерны тестирования Django-приложений. Используются совместно с pytest через `pytest-django`.

---

## 1. Django DB Marker

### Transaction Mode

```python
pytestmark = [
    pytest.mark.django_db(transaction=True),  # Required for background tasks
]
```

**RULE**: Use `transaction=True` when:
- Testing background tasks (Dramatiq, APScheduler, Celery)
- Testing code that uses `transaction.atomic()`
- Testing `select_for_update()`
- Testing signal handlers that rely on commit

Without `transaction=True`, Django wraps each test in a transaction that never commits.

### Standard Mode

```python
@pytest.mark.django_db
def test_simple_model_creation():
    campaign = Campaign.objects.create(name='Test', status=CampaignStatus.ACTIVE)
    assert campaign.pk is not None
```

Use standard `django_db` for simple model CRUD tests without transaction requirements.

---

## 2. Factory Boy with Django

### Трёхуровневая типология

#### 1. Structural level — Полнота объекта

**Механизм:** Отдельные классы/фикстуры

```python
class NonInitializedPersonFactory(DjangoModelFactory):
    """Минимум для FK."""
    inn = factory.Faker('individuals_inn')
    partner = factory.SubFactory(PartnerFactory)

class PersonFactory(NonInitializedPersonFactory):
    """Полный объект для тестов."""
    first_name = factory.Faker('first_name_male')
    last_name = factory.Faker('last_name_male')
    ...
```

**Когда использовать:** Принципиально разный набор обязательных полей.

#### 2. State level — Состояние жизненного цикла

**Механизм:** Traits (factory_boy) или параметры

```python
class Params:
    smz = factory.Trait(npd_status=REGISTERED)
    bound_smz = factory.Trait(smz=True, partner_bound_at=...)
```

**Когда использовать:** Разные этапы бизнес-процесса (NEW → PROCESSING → DONE).

#### 3. Data level — Вариативность данных

**Механизм:** Параметры функций

```python
def create_applicant(
    tilda_position: str = 'backend',
    telegram: str = '@testuser',
):
```

**Когда использовать:** Разные значения без изменения семантики.

### Composite Factory Fixtures

```python
@pytest.fixture()
def customer(
    apibank,
    customer_code,
    customer_type,
    customer_inn,
    owner,
    compliance_status,
):
    """Create customer with all related data."""
    data = {
        'code': customer_code,
        'type': customer_type,
        'taxCode': customer_inn,
        'relations': [
            {'type': owner_relation_type, 'relationCustomerCode': owner.code},
        ],
    }
    return apibank.reg_customer(data, compliance_status=compliance_status)
```

**RULE**: Composite fixtures:
- Depend on multiple smaller fixtures
- Register data in mock services
- Return the registered entity

---

## 3. Background Task Testing

### Direct Task Invocation

```python
pytestmark = [
    pytest.mark.django_db(transaction=True),
]

def test__created_initial_requests_to_fns(fns_admin, fns_npd_person):
    """Проверяем, что подхватываем и регистрируем чеки."""

    # Setup: Create entities in different states
    generated_offline = factories.IncomeRequestFactory.create(
        person_inn=fns_npd_person.inn,
        generated_offline=True,
    )
    not_registered = factories.IncomeRequestFactory.create(
        person_inn=fns_npd_person.inn,
    )
    already_registered = factories.IncomeRequestFactory.create(
        person_inn=fns_npd_person.inn,
        registered=True,
        registered_at=timezone.now() - dt.timedelta(minutes=30),
    )

    # Execute task directly (not via dramatiq.send)
    tasks.register_taxpayer_income()

    # Verify: Already registered unchanged
    already_registered.refresh_from_db()
    assert already_registered.registered_at == some_time_ago

    # Verify: Not registered now has async request
    not_registered.refresh_from_db()
    assert not_registered.state == models.IncomeRequestState.IN_PROGRESS
```

**RULE**:
- Call tasks directly (not via dramatiq.send or celery.delay)
- Use `transaction=True` in `pytest.mark.django_db`
- Test batch behavior (multiple entities in different states)

---

## 4. Django Model State Verification

### Pattern: refresh_from_db

```python
def test_non_smz__fail(fns_admin, create_income_request):
    income_request = create_income_request(
        protocol.SmzPlatformError(
            code=protocol.ErrorCode.TAXPAYER_UNREGISTERED,
            message=f'Taxpayer not found by INN {fns_npd_person.inn}',
        )
    )

    fns_admin.unreg_taxpayer(fns_npd_person.inn)
    tasks.register_taxpayer_income()

    # ALWAYS refresh from DB after task execution
    fns_npd_person.refresh_from_db()
    assert fns_npd_person.npd_status == models.NPDStatus.UNREGISTERED

    income_request.refresh_from_db()
    assert income_request.state == models.IncomeRequestState.ERROR
    assert income_request.error_code == models.IncomeRequestErrorCode.NO_NPD_STATUS
```

**RULE**: After executing code that modifies database:
1. Call `refresh_from_db()` on all objects under test
2. Verify status/state fields
3. Verify error codes and messages
4. Check no unintended state changes

---

## 5. Django Signal Verification

```python
def test_non_smz__fail(fns_admin, mocker, create_income_request):
    # Spy on signal emission
    unregister_signal_spy = mocker.spy(signals, 'send_unregister_person')

    # ... setup and execute ...

    # Verify signal was called
    assert unregister_signal_spy.call_count == 1
```

**RULE**: Use `mocker.spy()` on Django signals to verify:
- Signal was emitted
- Correct number of calls
- Arguments if needed

---

## 6. ESB Event Verification

### Event Outbox Testing

```python
def test__process_response__ok(esb_events_outbox):
    # ... execute code that produces ESB events ...

    esb_events = esb_events_outbox.pop_all_dict()
    assert esb_events == UnorderedList([
        AnyDict({
            '@sender': 'npd',
            '@type': 'npdReceiptChanged',
            'npdReceiptChanged': {
                'state': models.IncomeRequest.State.REGISTERED,
                'extKey': income_request.ext_key,
                'inn': income_request.person_inn,
                'receiptId': income_request.receipt_id,
                'errorCode': None,
            },
        }),
    ])
```

**RULE**:
- Use `esb_events_outbox` fixture to capture events
- Call `.pop_all_dict()` to get and clear events
- Use `UnorderedList` for multiple events
- Use `AnyDict` to match only relevant fields

---

## 7. Midnight / Timezone Testing

```python
@pytest.fixture(params=['current', 'midnight'])
def _check_midnight(request, freezer2):
    """Проверяем что корректно работаем в любое время суток.

    Частая ошибка: отсечение времени и поиск по полученной дате
    без учета часового пояса клиента.
    """
    if request.param == 'midnight':
        freezer2.move_to(timezone.localtime().replace(hour=0, minute=0))
```

**RULE**: Always test timezone-sensitive code at:
- Current time
- Server midnight (catches timezone conversion bugs)

This is critical for Django projects using `timezone.localtime()`, `timezone.now()`, and date-based filters.

---

## 8. Error Handling Test Pattern

### Comprehensive Error Coverage

For error scenarios in Django, verify:

```python
def test_non_smz__fail(fns_admin, create_income_request, mocker, esb_events_outbox):
    # Setup error
    income_request = create_income_request(
        protocol.SmzPlatformError(
            code=protocol.ErrorCode.TAXPAYER_UNREGISTERED,
            message='Not found',
        )
    )
    unregister_signal_spy = mocker.spy(signals, 'send_unregister_person')
    fns_admin.unreg_taxpayer(fns_npd_person.inn)

    # Execute
    tasks.register_taxpayer_income()

    # 1. Verify database state
    fns_npd_person.refresh_from_db()
    assert fns_npd_person.npd_status == models.NPDStatus.UNREGISTERED
    income_request.refresh_from_db()
    assert income_request.state == models.IncomeRequestState.ERROR
    assert income_request.error_code == models.IncomeRequestErrorCode.NO_NPD_STATUS

    # 2. Verify signals
    assert unregister_signal_spy.call_count == 1

    # 3. Verify ESB events
    assert esb_events_outbox.pop_all_dict() == [
        AnyDict({
            '@type': 'npdReceiptChanged',
            'npdReceiptChanged': {
                'state': models.IncomeRequest.State.ERROR,
                'errorCode': IncomeRequestErrorCode.NO_NPD_STATUS,
            },
        }),
    ]
```

**RULE**: For error scenarios, verify all layers:
1. **Database state** — error codes, status updates
2. **Signal emissions** — using `mocker.spy`
3. **Side effects** — ESB events, logs
4. **No unintended changes** — other objects not affected

---

## Summary of Key Rules

### Django DB:
1. Use `transaction=True` for background tasks and atomic operations
2. Standard `django_db` for simple CRUD tests
3. Always `refresh_from_db()` after task execution

### Factory Boy:
4. Structural level: separate classes for different completeness
5. State level: traits for lifecycle stages
6. Data level: parameters for value variations

### Background Tasks:
7. Call tasks directly (not via message broker)
8. Test batch behavior (multiple entities, different states)
9. Verify state transitions and error handling

### Verification:
10. Check database state changes
11. Spy on Django signals
12. Verify ESB/event outbox
13. Test at midnight for timezone issues
14. Verify all error layers (DB + signals + events)
