
import logging
from typing import Any

import asyncio
import contextlib
from aiohttp import web
from aiogram import Bot, Dispatcher

from .config import Config
from .database import Database


async def ensure_webhook(bot: Bot, base_url: str) -> None:
    """Make sure Telegram webhook matches base_url."""
    expected = base_url.rstrip("/") + "/webhook"
    try:

        info = await bot.get_webhook_info()
        current = getattr(info, "url", "")
        if current != expected:
            await bot.set_webhook(expected)

            logging.info("Webhook registered: %s", expected)
        else:
            logging.info("Webhook already registered: %s", expected)
    except Exception as e:  # pragma: no cover - network errors
        logging.error("Failed to register webhook: %s", e)
        # Do not interrupt startup if Telegram is unreachable
        return


async def retry_webhook(bot: Bot, base_url: str, interval: int = 30) -> None:
    """Keep trying to register the webhook until successful."""
    expected = base_url.rstrip("/") + "/webhook"
    while True:
        await ensure_webhook(bot, base_url)
        try:
            info = await bot.get_webhook_info()
            if getattr(info, "url", "") == expected:
                break
        except Exception:
            pass
        await asyncio.sleep(interval)


async def handle_webhook(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]
    data = await request.json()
    await dp.feed_webhook_update(bot, data)
    return web.Response(text="ok")


def create_app() -> web.Application:
    config = Config.from_env()
    bot = Bot(config.telegram_token)
    dp = Dispatcher()
    db = Database(config.db_path)
    dp["db"] = db

    from .handlers import channels, tz
    dp.include_router(tz.router)
    dp.include_router(channels.router)

    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app["config"] = config

    app.router.add_post("/webhook", handle_webhook)

    async def on_startup(app: web.Application) -> None:
        # Try once at startup, then continue retrying in background
        await ensure_webhook(bot, config.webhook_url)
        app['webhook_task'] = asyncio.create_task(
            retry_webhook(bot, config.webhook_url)
        )


    async def on_cleanup(app: web.Application) -> None:
        task: asyncio.Task | None = app.get('webhook_task')
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
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
