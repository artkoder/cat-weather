
import asyncio
import logging
import os

from aiohttp import web
from aiogram import Dispatcher
from .scheduler_bot import SchedulerBot

from .config import Config
from .database import Database


FLY_APP_NAME = os.getenv("FLY_APP_NAME")
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL", f"https://{FLY_APP_NAME}.fly.dev" if FLY_APP_NAME else None
)
if not WEBHOOK_URL:
    raise RuntimeError(
        "WEBHOOK_URL не задан и FLY_APP_NAME отсутствует – "
        "нечего регистрировать в Telegram"
    )
os.environ.setdefault("WEBHOOK_URL", WEBHOOK_URL)


GET_WEBHOOK_INFO = "getWebhookInfo"
SET_WEBHOOK = "setWebhook"


async def ensure_webhook(bot: SchedulerBot, base_url: str) -> None:
    """Ensure Telegram webhook matches the configured URL."""
    expected = base_url.rstrip("/") + "/webhook"
    try:
        info = await bot.api_request(GET_WEBHOOK_INFO)
        current = info.get("result", {}).get("url")
        if current == expected:
            logging.info("Webhook уже зарегистрирован – %s", current)
            return
        resp = await bot.api_request(SET_WEBHOOK, {"url": expected})
        if resp.get("ok"):
            logging.info("Webhook зарегистрирован")
        else:
            logging.warning("Не удалось зарегистрировать webhook: %s", resp)
    except Exception as e:  # pragma: no cover - network errors
        logging.warning("Ошибка при регистрации webhook: %s", e)


async def handle_webhook(request: web.Request) -> web.Response:
    bot: SchedulerBot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]
    data = await request.json()
    await dp.feed_webhook_update(bot, data)
    return web.Response(text="ok")


def create_app() -> web.Application:
    config = Config.from_env()
    bot = SchedulerBot(config.telegram_token)
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
    app.router.add_get("/", lambda r: web.Response(text="ok"))

    async def on_startup(app: web.Application) -> None:
        try:
            await ensure_webhook(bot, WEBHOOK_URL)
        except Exception:
            logging.exception("Webhook init failed – continuing without it")


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
