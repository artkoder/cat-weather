from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from ..database import Database

router = Router()


@router.message(Command("tz"), F.text)
async def set_timezone(message: Message) -> None:
    if not message.from_user:
        return
    if not message.text:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /tz <offset>")
        return
    try:
        offset = int(parts[1])
    except ValueError:
        await message.answer("Offset must be an integer")
        return
    if offset < -12 or offset > 14:
        await message.answer("Offset must be between -12 and 14")
        return
    db: Database = message.bot.get("db")
    db.set_timezone(message.from_user.id, offset)
    await message.answer(f"Часовой пояс установлен: {offset:+d}")
