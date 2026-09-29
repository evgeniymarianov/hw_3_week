# Внешние API

Этот файл описывает внешние ручки, которые можно вызвать из приложения.
Создание `httpx` или `aiohttp` клиента и обработку ответов ученики реализуют сами.

## Payment API

Базовый URL: `PAYMENT_API_URL` из `app/config.py`.

### Расчет платежа

- Метод: `POST`
- Эндпоинт: `/payment/calculate`
- JSON-параметры:
  - `booking_id: int` - id брони
  - `amount: int` - сумма брони в копейках
  - `currency: str` - валюта, например `RUB`
- Может вернуть:
  - `commission: int`
  - `total: int`
  - `payment_methods: list[str]`
  - `expires_at: datetime | None`

```python
...
```

### Оплата брони

- Метод: `POST`
- Эндпоинт: `/payment/pay`
- JSON-параметры:
  - `booking_id: int` - id брони
  - `amount: int` - сумма к списанию в копейках
  - `currency: str` - валюта, например `RUB`
  - `payment_method: str` - выбранный способ оплаты
- Может вернуть:
  - `transaction_id: str`

```python
...
```

## Protection API

Базовый URL: `PROTECTION_API_URL` из `app/config.py`.

### Расчет защиты билетов

- Метод: `POST`
- Эндпоинт: `/protection/calculate`
- JSON-параметры:
  - `booking_id: int` - id брони
  - `ticket_amount: int` - стоимость билетов в копейках
  - `event_category: str` - категория мероприятия
  - `event_starts_at: str` - дата начала мероприятия в ISO-формате
- Может вернуть:
  - `available: bool`
  - `price: int`
  - `covered_amount: int`
  - `description: str | None`

```python
...
```
