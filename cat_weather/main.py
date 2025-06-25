"""fly.toml snippet
app = "cat-weather"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
"""

import asyncio
import contextlib
import os
from urllib.parse import urlparse
try:
    from aiogram.exceptions import TelegramBadRequest
except Exception:  # pragma: no cover - fallback for tests
    class TelegramBadRequest(Exception):
        pass
try:
    from aiogram.types import Update
except Exception:  # pragma: no cover - fallback for tests
    class Update(dict):
        def __init__(self, **data):
            super().__init__(**data)
async def ensure_webhook(bot: Bot, base_url: str, *, attempts: int = 5) -> None:
    """Ensure Telegram webhook is set with retries."""
    delay = 5
    for attempt in range(1, attempts + 1):
        try:
            info = await bot.get_webhook_info()
            current = getattr(info, "url", "")
            if current != expected:
                await bot.set_webhook(expected)
                logging.info("Webhook registered: %s", expected)
            else:
                logging.info("Webhook already registered: %s", expected)
            return
        except Exception as e:
            if isinstance(e, TelegramBadRequest):
                msg = e.message if hasattr(e, "message") else str(e)
            else:
                msg = str(e)
            logging.warning(
                "Webhook setup failed on attempt %d/%d: %s", attempt, attempts, msg
            )
            if attempt < attempts:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logging.error("Could not register webhook after %d attempts", attempts)
    token = os.environ.get("TELEGRAM_TOKEN")
    webhook_base = os.environ.get("WEBHOOK_URL")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN environment variable is required")
    if not webhook_base:
        raise RuntimeError("WEBHOOK_URL environment variable is required")

    db_path = os.environ.get("DB_PATH", "weather.db")

    bot = Bot(token)
    db = Database(db_path)
    from .handlers import tz, channels

    webhook_url = webhook_base.rstrip("/") + "/webhook"
    path = urlparse(webhook_url).path or "/webhook"

    app["webhook_url"] = webhook_url

    async def handle_webhook(request: web.Request) -> web.Response:
        data = await request.json()
        update = Update(**data)
        await dp.process_update(update)
        return web.Response(text="ok")
    app.router.add_post(path, handle_webhook)
        await bot.start()
        app["wh_task"] = asyncio.create_task(ensure_webhook(bot, webhook_base))

        await bot.delete_webhook()
        task = app.get("wh_task")
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from .handlers import channels, tz
    dp.include_router(tz.router)
    dp.include_router(channels.router)

    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app["config"] = config

    app.router.add_post("/webhook", handle_webhook)

    async def on_startup(app: web.Application) -> None:

        try:
            await ensure_webhook(bot, config.webhook_url)
        except Exception:
            # ensure_webhook already logged the error
            raise


    async def on_cleanup(app: web.Application) -> None:

        await bot.session.close()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
