import logging
from typing import Any

from aiohttp import web
from aiogram import Bot, Dispatcher

from .config import Config
from .database import Database


async def ensure_webhook(bot: Bot, base_url: str) -> None:
    """Make sure Telegram webhook matches base_url."""
    expected = base_url.rstrip("/") + "/webhook"
    try:
        info = await bot.api_request("getWebhookInfo")
        current = info.get("url", "")
        if current != expected:
            await bot.api_request("setWebhook", {"url": expected})
            logging.info("Webhook registered: %s", expected)
        else:
            logging.info("Webhook already registered: %s", expected)
    except Exception as e:  # pragma: no cover - network errors
        logging.error("Failed to register webhook: %s", e)
        raise


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
