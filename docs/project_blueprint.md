# Focus Day Bot Blueprint

## Folder Structure

```text
finance/
├── app/
│   ├── api/
│   │   ├── static/
│   │   ├── templates/
│   │   └── main.py
│   ├── bot/
│   │   ├── keyboards.py
│   │   ├── handlers.py
│   │   └── main.py
│   ├── config/
│   │   └── settings.py
│   ├── db/
│   │   ├── database.py
│   │   └── repository.py
│   └── services/
│       └── dashboard.py
├── docs/
│   └── project_blueprint.md
├── .env.example
├── .railwayignore
├── Procfile
├── README.md
├── requirements.txt
├── railway.json
└── run.py
```

## Architecture Overview

- `aiogram` handles Telegram updates and the simple command flow.
- `FastAPI` serves the Mini App and JSON endpoints.
- `SQLite` stores users and productive-day marks.
- `dashboard.py` builds a complete demo-friendly dashboard view model.
- `run.py` launches API and bot from one command.
- `railway.json` fixes the start command and healthcheck for Railway deploys.

## Database Schema

### `users`

- `id` INTEGER PRIMARY KEY
- `telegram_user_id` INTEGER UNIQUE NOT NULL
- `first_name` TEXT
- `username` TEXT
- `created_at` TEXT NOT NULL

### `daily_marks`

- `id` INTEGER PRIMARY KEY
- `user_id` INTEGER NOT NULL
- `mark_date` TEXT NOT NULL
- `created_at` TEXT NOT NULL
- `UNIQUE(user_id, mark_date)`

## Implementation Plan

1. Load environment variables and initialize SQLite.
2. Build repository helpers for user sync, day marking, and streaks.
3. Build the dashboard service for cards, tasks, quote, and activity history.
4. Implement bot handlers for `/start`, help, streak, and mark actions.
5. Implement FastAPI routes for HTML and JSON.
6. Add a polished mobile-first UI.
7. Prepare Railway deployment with a public domain and optional persistent volume.

## Pseudocode

```text
on run.py:
    ensure .env exists
    init database
    start FastAPI on local port or Railway PORT
    start bot if BOT_TOKEN is valid

on /start:
    create user
    seed demo history
    send Russian welcome + menu

on mark action:
    save today's mark
    calculate streak
    send short confirmation

on GET /api/dashboard:
    resolve Telegram user or demo user
    build dashboard data
    return JSON
```
