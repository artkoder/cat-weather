import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import Config
from .database import Database
from .handlers import tz, channels


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


def create_app() -> tuple[Bot, Dispatcher]:
    config = Config.from_env()
    bot = Bot(config.telegram_token)
    dp = Dispatcher()
    db = Database(config.db_path)
    dp["db"] = db

    dp.include_router(tz.router)
    dp.include_router(channels.router)

    return bot, dp


async def main() -> None:
    setup_logging()
    bot, dp = create_app()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
