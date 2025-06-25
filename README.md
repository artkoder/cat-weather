# Cat Weather Bot

Telegram bot for posting weather updates. Requires Python 3.11 and aiogram v3.

The bot stores timezone settings and tracks channels automatically. It works via
a Telegram webhook.

```bash
TELEGRAM_BOT_TOKEN=... \
WEBHOOK_URL=https://your-app.fly.dev \
DB_PATH=weather.db python -m cat_weather.main
```

WEBHOOK_URL must be a public HTTPS URL accessible by Telegram.

If you are deploying to **Fly.io**, make sure the application has an IPv4
address. Telegram does not support IPv6-only hosts, so you need to allocate
an IPv4 address with:

```bash
fly ips allocate-v4
# or from Python:
# import subprocess; subprocess.run(["fly", "ips", "allocate-v4"], check=True)
```

Until this is done Telegram will report `bad webhook: Failed to resolve host`
when the bot tries to register its webhook.
