# Focus Day Bot

Небольшой showcase-проект: Telegram bot + Telegram Mini App с аккуратным productivity dashboard.

## Что внутри

- бот приветствует пользователя
- позволяет отметить продуктивный день
- показывает текущую серию
- открывает Mini App

Mini App сделан как главная визуальная часть проекта:

- hero-блок с приветствием
- карточки серии и прогресса
- история за последние 7 дней
- 3 фокус-задачи на сегодня
- мотивационная цитата
- summary-блок для красивого demo-экрана

## Архитектура

Blueprint лежит в [docs/project_blueprint.md](/C:/VSCode/projects/bots_portfolio/finance/docs/project_blueprint.md).

## Стек

- Python
- aiogram 3
- FastAPI
- SQLite / PostgreSQL
- HTML / CSS / JavaScript

## Локальный запуск

### 1. Создай виртуальное окружение

```bash
python -m venv .venv
```

### 2. Активируй его

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Создай `.env`

Windows:

```bash
copy .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Минимально нужно заполнить `BOT_TOKEN`.

### 5. Запусти проект

```bash
python run.py
```

`run.py`:

- инициализирует базу данных
- поднимает FastAPI
- запускает Telegram-бота
- следит за логами обоих процессов

Маршруты:

- `/` — Mini App
- `/health` — healthcheck
- `/api/dashboard` — данные дашборда
- `/api/mark-today` — отметить день

## Railway deployment

Проект подготовлен под деплой из GitHub на Railway.

Что уже учтено:

- сервис слушает `0.0.0.0:$PORT`, если Railway передаёт `PORT`
- публичный URL автоматически собирается из `RAILWAY_PUBLIC_DOMAIN`, если `BASE_URL` не задан
- если задан `DATABASE_URL`, приложение работает с PostgreSQL
- если `DATABASE_URL` не задан, остаётся fallback на SQLite
- в репозитории есть `Procfile` и `railway.json` для явного старт-команда и healthcheck

### Переменные Railway

Обязательная:

- `BOT_TOKEN`

Опциональные:

- `BASE_URL` — если хочешь явно переопределить публичный URL
- `DATABASE_URL` — основной вариант для Railway PostgreSQL
- `DATABASE_PATH` — по умолчанию `data/finance_tracker.db`
- `ENABLE_RELOAD` — для Railway не нужен, оставляй `false`

### SQLite на Railway

Если база должна сохраняться между деплоями, подключи Volume к сервису.

Рекомендуемая схема:

1. Создай Volume в Railway.
2. Подключи его к сервису.
3. Укажи mount path `/app/data`.

По документации Railway volume mount path становится доступен в рантайме через `RAILWAY_VOLUME_MOUNT_PATH`, а относительные пути приложения обычно нужно монтировать внутрь `/app/...`. Источники: [Variables Reference](https://docs.railway.com/reference/variables), [Volumes Guide](https://docs.railway.com/guides/volumes).

### Как задеплоить

1. Запушь репозиторий в GitHub.
2. В Railway создай новый проект через `Deploy from GitHub repo`.
3. Выбери этот репозиторий.
4. Добавь `BOT_TOKEN` в Variables.
5. В Settings -> Networking нажми `Generate Domain`.
6. В Settings -> Healthcheck укажи `/health`, если Railway не подхватит его из config-as-code.
7. Для SQLite persistence подключи Volume.

Railway по документации сам выдаёт публичный домен только после `Generate Domain`, а приложение должно слушать `PORT`. Источники: [Working with Domains](https://docs.railway.com/networking/domains/working-with-domains), [Build & Deploy](https://docs.railway.com/build-deploy).

## GitHub

Целевой remote:

```text
https://github.com/3oL1v/finance.git
```

## Demo-логика

- проект intentionally simple
- история за прошлые дни мягко инициализируется при первом входе
- интерфейс выглядит полным и аккуратным для скриншотов и портфолио
