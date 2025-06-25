# Cat Weather Bot

Telegram bot for posting weather updates. Requires Python 3.11 and aiogram v3.

The bot stores timezone settings and tracks channels automatically. It works via
a Telegram webhook.

```bash

TELEGRAM_BOT_TOKEN=... \
WEBHOOK_URL=https://your-app.fly.dev \
DB_PATH=weather.db python -m cat_weather.main

WEBHOOK_URL must be a public HTTPS URL accessible by Telegram.

The application will keep retrying webhook registration in the
background until the URL becomes reachable. This is useful when DNS
records for a freshly deployed app have not propagated yet.

```
