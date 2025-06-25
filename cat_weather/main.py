
import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher

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


async def ensure_webhook(bot: Bot, base_url: str, attempts: int = 8) -> None:
    """Регистрирует webhook, повторяя попытки, пока DNS не станет доступным."""
    expected = base_url.rstrip("/") + "/webhook"

    backoff = 2  # секунд
    for i in range(1, attempts + 1):
        try:
            info = await bot.get_webhook_info()
            current = getattr(info, "url", "")
            if current == expected:
                logging.info("Webhook уже зарегистрирован – %s", current)
                return

            logging.info("Попытка %s/%s: регистрирую %s", i, attempts, expected)
            await bot.set_webhook(expected)
            logging.info("Webhook зарегистрирован")
            return
        except Exception as e:
            if "resolve host" in str(e):
                logging.warning("DNS не готов, жду %s сек…", backoff)
                await asyncio.sleep(backoff)
                backoff *= 2
            else:
                raise
    logging.error("Не удалось зарегистрировать webhook за %s попыток", attempts)


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
    app.router.add_get("/", lambda r: web.Response(text="ok"))

    async def on_startup(app: web.Application) -> None:

        try:
            await ensure_webhook(bot, WEBHOOK_URL)
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
