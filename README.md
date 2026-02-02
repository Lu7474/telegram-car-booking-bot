# Car Booking Bot

Telegram-бот для бронирования автомобилей с интегрированной системой оплаты.

## Описание

Бот позволяет пользователям просматривать каталог автомобилей, бронировать их на определённые даты и оплачивать через Telegram Payments. Администраторы могут управлять каталогом автомобилей через специальные команды.

## Функционал

### Для пользователей
- Регистрация с подтверждением номера телефона
- Просмотр каталога автомобилей с фильтрацией по типу (седан, внедорожник, хэтчбек)
- Бронирование автомобиля на выбранные даты
- Проверка доступности авто на указанный период
- Оплата бронирования через Telegram Payments

### Для администраторов
- `/add_car` — добавление нового автомобиля
- `/list_cars` — просмотр всех автомобилей
- `/delete_car <id>` — удаление автомобиля

## Технологии

- **Python 3.10+**
- **aiogram 3.x** — асинхронный фреймворк для Telegram Bot API
- **SQLAlchemy 2.0** — ORM для работы с базой данных
- **aiosqlite** — асинхронный драйвер для SQLite
- **SQLite** — база данных

## Структура проекта

```
├── bot.py              # Точка входа
├── config.py           # Конфигурация (токены, ID админов)
├── core/
│   ├── handlers.py     # Обработчики команд и сообщений
│   ├── keyboards.py    # Клавиатуры бота
│   ├── utils.py        # Вспомогательные функции
│   └── database/
│       ├── models.py   # Модели базы данных
│       └── requests.py # Функции для работы с БД
└── db.sqlite3          # База данных
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Lu7474/telegram-car-booking-bot.git
cd telegram-car-booking-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv env
source env/bin/activate  # Linux/macOS
env\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install aiogram aiosqlite sqlalchemy
```

4. Настройте конфигурацию в `config.py`:
```python
TELEGRAM_BOT_TOKEN = "ваш_токен_бота"
PAYMENTS_TOKEN = "ваш_платёжный_токен"
ADMIN_IDS = [ваш_telegram_id]
```

5. Запустите бота:
```bash
python bot.py
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом |
| `/help` | Справка по командам |
| `/cancel` | Отменить текущее действие |
| `/add_car` | Добавить автомобиль (админ) |
| `/list_cars` | Список автомобилей (админ) |
| `/delete_car` | Удалить автомобиль (админ) |

## База данных

### Таблицы

- **users** — пользователи (id, tg_id, name, phone, created_at)
- **cars** — автомобили (id, brand, model, type, description, price_per_day, is_available, image_url)
- **bookings** — бронирования (id, user_id, car_id, start_date, end_date, total_price, payment_status)

## Лицензия

MIT
