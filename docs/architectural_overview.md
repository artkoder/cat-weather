# Telegram Weather Bot - Architectural Overview

## 1. Project Overview
**Название**: Telegram Weather Bot

**Цель**: Автоматически публиковать и обновлять прогноз погоды в Telegram-каналах, используя OpenMeteo API.

**Ожидаемая аудитория**: каналы с хэштегом `#котопогода` и другие тематические чаты.

## 2. Технические требования
- **Язык**: Python 3.11
- **Фреймворк**: aiogram v3.x
- **База данных**: SQLite (в дальнейшем PostgreSQL)
- **API погоды**: OpenMeteo (без ключа, запрос по широте/долготе)
- **Планировщик**: APScheduler или аналогичный, интегрированный в бот
- **Контейнеризация**: Docker + Fly.io (fly.toml)
- **CI/CD**: GitHub Actions, автоматический деплой на Fly.io


### WeatherService

#### Open-Meteo API
Базовый URL

```bash
https://api.open-meteo.com/v1/forecast
```

Параметры запроса

- `latitude` (обязательно) — широта в десятичном формате, например `54.7104`
- `longitude` (обязательно) — долгота в десятичном формате, например `20.4522`
- `current_weather` (обязательно) — `true` для получения текущей погоды
- `hourly` (опционально) — список почасовых параметров через запятую:
  `temperature_2m,weathercode,windspeed_10m,winddirection_10m`
- `daily` (опционально) — список суточных параметров:
  `temperature_2m_max,temperature_2m_min,weathercode`
- `timezone` (обязательно) — часовой пояс в формате IANA или смещение `+03:00`
- `(опционально) temperature_unit` — `celsius` или `fahrenheit` (по умолчанию `celsius`)
- `(опционально) wind_speed_unit` — `kmh` (по умолчанию) или `ms`, `mph`, `kn`
- `(опционально) precipitation_unit` — `mm` (по умолчанию) или `inch`

Пример запроса

```bash
curl "https://api.open-meteo.com/v1/forecast?latitude=54.7104&longitude=20.4522&current_weather=true&hourly=temperature_2m,weathercode,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=+03:00"
```

Структура ответа

```json
{
  "latitude": 54.7104,
  "longitude": 20.4522,
  "generationtime_ms": 0.123,
  "utc_offset_seconds": 10800,
  "timezone": "UTC+3",
  "current_weather": {
    "temperature": 18.7,
    "windspeed": 3.4,
    "winddirection": 245,
    "weathercode": 3,
    "time": "2025-06-25T14:00"
  },
  "hourly": {
    "time": ["2025-06-25T14:00", "..."],
    "temperature_2m": [18.7, "..."],
    "weathercode": [3, "..."],
    "windspeed_10m": [3.4, "..."],
    "winddirection_10m": [245, "..."]
  },
  "daily": {
    "time": ["2025-06-25", "2025-06-26"],
    "temperature_2m_max": [21.3, 22.1],
    "temperature_2m_min": [12.4, 13.0],
    "weathercode": [1, 2]
  }
}
```

#### Geocoding
URL

```bash
https://geocoding-api.open-meteo.com/v1/search
```

Параметры

- `name` (обязательно) — строка запроса (город, почтовый индекс)
- `count` (опционально) — число результатов (по умолчанию `10`)

Пример

```bash
curl "https://geocoding-api.open-meteo.com/v1/search?name=Kaliningrad&count=5"
```

Фрагмент ответа

```json
{
  "results": [
    {
      "id": 2961082,
      "name": "Kaliningrad",
      "latitude": 54.7104,
      "longitude": 20.4522,
      "country": "Russia",
      "admin1": "Kaliningrad Oblast",
      "timezone": "Europe/Kaliningrad"
    }
    // ...
  ]
}
```

#### Методы

```python
def fetch_current(lat: float, lon: float, tz: str) -> CurrentWeather:
    """
    Запрашивает текущую погоду у Open-Meteo.
    Параметры:
      - lat, lon: координаты города
      - tz: смещение или IANA-часовой пояс
    Возвращает:
      CurrentWeather(
        temperature: float,
        weathercode: int,
        windspeed: float,
        winddirection: int,
        time: datetime
      )
    """

def fetch_tomorrow(lat: float, lon: float, tz: str) -> TomorrowForecast:
    """
    Запрашивает ежедневный прогноз у Open-Meteo.
    Параметры:
      - lat, lon: координаты города
      - tz: смещение или IANA-часовой пояс
    Возвращает:
      TomorrowForecast(
        date: date,
        temp_max: float,
        temp_min: float,
        weathercode: int
      )
    """
```


## 3. Архитектура
Telegram Weather Bot построен по модульному принципу и состоит из следующих основных слоёв и компонентов:

### 3.1 Bot Core
- **handlers/commands** — обработчики команд, поступающих от пользователей и каналов.
- **callbacks/inline buttons** — обработчики нажатий на inline-кнопки.
- **webhooks + aiohttp server** — получение обновлений через webhook, запуск aiohttp-сервера для Telegram.

### 3.2 WeatherService
- **fetch_current(lat, lon)** — получение текущих погодных данных.
- **fetch_tomorrow(lat, lon)** — получение прогноза на завтра.
- **Таймауты**: 3 часа кэширование для текущей погоды и 6 часов для прогноза.

### 3.3 Storage Layer
- **Модели SQLAlchemy/схемы SQLite** — доступ к базе данных.
- Таблицы: `superadmins`, `channels`, `users`, `cities`, `channel_configs`, `logs`, `schedule_tasks`.
- Привязка названий городов к координатам хранится в `cities`. WeatherService получает lat/lon из этой таблицы.

### 3.4 Templates
- **Файлы**: `templates/today.tpl` и `templates/tomorrow.tpl`.
- **Система плейсхолдеров**: `{Город|now}`, `{Город|nextday-morning}`, `{Город|nextday-day}`, `{Город|nextday-evening}`, `{Город|nextday-night}`.
- **Маркер-разделитель**: `•` (точка-буллет) для разделения текста шаблона и места вставки.

### 3.5 Scheduler
- Автоматическое обновление «сегодня» каждые 1 час.
- Обновление «завтра» раз в сутки в заданное время (учитывается смещение часового пояса).
- Отдельная задача сохраняет актуальную погоду в БД и пишет результаты в `logs`.

### 3.6 Logging
- Логирование операций в файле/консоли с уровнями INFO, WARNING, ERROR.
- Для каждой user story логируется начало операции, результат (успех или ошибка) и стек при ошибке.

## 4. Database Schema
Ниже представлена текстовая ER-диаграмма и перечисление таблиц с их полями и типами.

### Таблицы
- **superadmins** (`user_id INTEGER PRIMARY KEY`, `telegram_id BIGINT`, `added_at DATETIME`)
- **channels** (`chat_id BIGINT PRIMARY KEY`, `title TEXT`, `added_at DATETIME`)
- **cities** (`id INTEGER PRIMARY KEY`, `name_ru TEXT`, `lat REAL`, `lon REAL`, `api_source TEXT`)
- **channel_configs** (`channel_id BIGINT`, `city_id INTEGER`, `enable_now BOOLEAN`, `enable_tomorrow BOOLEAN`, `marker_symbol TEXT`, `button_text TEXT`, `button_url TEXT`)
- **schedule_tasks** (`id INTEGER PRIMARY KEY`, `type TEXT`, `channel_id BIGINT`, `template_type TEXT`, `run_time DATETIME`, `interval_rrule TEXT`)
- **logs** (`id INTEGER PRIMARY KEY`, `timestamp DATETIME`, `level TEXT`, `component TEXT`, `message TEXT`, `metadata TEXT`)

### Предустановленные города
- **Калининград** — 54.7108 N, 20.4522 E
- **Светлогорск** — 54.9419 N, 20.1515 E

Эти записи находятся в таблице `cities` и используются для определения координат при запросах к OpenMeteo.

## 5. User Stories (US)
Нумерованный перечень пользовательских историй и требований к логированию:
1. **US-0**: Сохранение суперадмина (`/tz` уже реализована).
2. **US-1**: `/tz <offset>` — установить смещение часового пояса.
   - *Роль*: суперадмин
   - *Действие*: отправляет команду в личном чате
   - *Критерий*: значение сохраняется в БД, все задачи учитывают новое смещение
   - *Лог*: INFO о начале, SUCCESS либо ERROR при проблеме
3. **US-2**: Авто-регистрация/удаление каналов при изменении прав бота.
   - *Критерий*: бот видит новый канал, добавляет/удаляет запись в `channels`
   - *Лог*: INFO при добавлении/удалении
4. **US-3**: `/channels` — вывести список каналов и их настроенных функций.
   - *Критерий*: список выводится суперадмину
   - *Лог*: INFO о запросе списка
5. **US-4**: `/addbutton <post_url> <text> <url>` — добавить inline-кнопку к существующему сообщению.
   - *Критерий*: кнопка добавлена и сохранена в `channel_configs`
   - *Лог*: INFO об обновлении
6. **US-5**: Плановое получение и сохранение погодных данных.
   - *Критерий*: сервис раз в час сохраняет текущую погоду в БД
   - *Лог*: INFO о запуске задачи, WARNING/ERROR при сбое

7. **US-6**: `/set_today_template <post_url>` — вставить сегодня-шаблон до маркера `•`.
   - *Критерий*: шаблон добавлен к указанному посту
   - *Лог*: SUCCESS или ERROR
8. **US-7**: По расписанию 1×/сутки находить последний пост с `#котопогода` и вставлять tomorrow.tpl перед маркером.
   - *Критерий*: сообщение обновлено, лог SUCCESS
9. **US-8**: `/addcity <name> <lat> <lon>` — добавить город в БД.
   - *Критерий*: запись появляется в `cities`
   - *Лог*: INFO добавление, ERROR при неверных данных
10. **US-9**: Резервное копирование локальной БД перед обновлением и её восстановление после деплоя.
   - *Критерий*: База экспортируется и затем импортируется без потери данных
   - *Лог*: INFO о резервном копировании, ERROR при сбое


## 6. Commands & Flows
Ниже описаны основные команды бота.

### `/tz <offset>`
• **Trigger**: сообщение от суперадмина
• **Handler**: `handlers.tz.set_timezone`
• **Validation**: offset в диапазоне -12…14
• **DB действия**: обновление поля `tz_offset` в таблице `superadmins`
• **Ответ бота**: подтверждение установки
• **Логирование**: INFO начало, SUCCESS или ERROR

### Авто-регистрация каналов
• **Trigger**: событие `my_chat_member`
• **Handler**: `handlers.channels.track_bot_in_chat`
• **DB действия**: добавление/удаление записей в `channels`
• **Логирование**: INFO добавление или удаление канала

### `/channels`
• **Trigger**: команда от суперадмина
• **Handler**: `handlers.channels.list_channels`
• **Validation**: роль пользователя
• **DB действия**: чтение таблиц `channels` и `channel_configs`
• **Ответ бота**: список каналов с параметрами
• **Логирование**: INFO запрос списка

### `/addbutton <post_url> <text> <url>`
• **Trigger**: команда в чате
• **Handler**: `handlers.buttons.add_button`
• **Validation**: права на пост, валидность URL
• **DB действия**: обновление `channel_configs`
• **Ответ бота**: уведомление об успехе/ошибке
• **Логирование**: INFO добавление кнопки, ERROR при неудаче

### `/set_today_template <post_url>`
• **Trigger**: команда в чате
• **Handler**: `handlers.templates.set_today`
• **Validation**: наличие маркера `•`, доступ к посту
• **DB действия**: нет, обновляется сообщение через Telegram API
• **Ответ бота**: подтверждение
• **Логирование**: INFO и SUCCESS/ERROR
### `/addcity <name> <lat> <lon>`
• **Trigger**: команда от суперадмина
• **Handler**: `handlers.cities.add_city`
• **Validation**: уникальность названия, валидность координат
• **DB действия**: вставка записи в `cities`
• **Ответ бота**: подтверждение о добавлении
• **Логирование**: INFO успешное добавление, ERROR при проблеме


## 7. Template Files
Пример содержимого шаблонов:

**templates/today.tpl**
```
Погода сегодня в {Город|now}
•
```

**templates/tomorrow.tpl**
```
Прогноз на завтра:
Утром: {Город|nextday-morning}
Днём: {Город|nextday-day}
Вечером: {Город|nextday-evening}
Ночью: {Город|nextday-night}
•
```

Движок загружает шаблон, ищет плейсхолдеры вида `{Город|now}` и подставляет значения, полученные из `WeatherService`. Текст после маркера `•` в шаблонах игнорируется при вставке.

## 8. Error Handling & Timeouts
- При тайм-ауте или ошибке OpenMeteo сервис пробует повторить запрос 3 раза с увеличивающимся интервалом.
- Если данные всё ещё недоступны, бот пишет предупреждение в лог (WARNING) и пропускает обновление для данного города.
- При других исключениях пишется ERROR с трассировкой.

## 9. Deployment & CI/CD
Ниже приводятся примеры файлов для развёртывания.

### Dockerfile
```
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]
```

### fly.toml
```
app = "cat-weather"
primary_region = "fra"
[build]
  dockerfile = "Dockerfile"
[env]
  DB_PATH = "/data/weather.db"
  WEBHOOK_URL = "https://cat-weather.fly.dev"
```

### GitHub Actions — `.github/workflows/deploy.yml`
```
name: Deploy
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: superfly/flyctl-actions/setup-flyctl@master
    - run: flyctl deploy --remote-only
      env:
        FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

### Переменные окружения
- `TELEGRAM_TOKEN` — токен бота
- `OPENMETEO_URL` — базовый URL сервиса погоды
- `DB_PATH` — путь к файлу SQLite
- `WEBHOOK_URL` — публичный адрес приложения
- `TZ_OFFSET` — часовой пояс по умолчанию

## 10. Roadmap & Next Steps
Разбивка проекта на спринты и последовательность задач:
1. **Документация и окружение** — создание архитектуры, Dockerfile, начальный CI/CD.
2. **Skel-код** — базовый бот на aiogram, интеграция с OpenMeteo, простая SQLite.
3. **Реализация US-0…US-2** — управление суперадминами и каналами.
4. **Реализация US-3…US-4** — команды для управления шаблонами и кнопками.
5. **Реализация US-5…US-7** — автоматическая публикация прогнозов.
6. **Реализация US-8…US-9** — управление городами и резервное копирование БД.

### Checklist перед PR
- [ ] Все линтеры и тесты проходят локально
- [ ] Обновлена документация
- [ ] Проверена работа CI/CD
- [ ] Созданы необходимые шаблоны и конфиги

