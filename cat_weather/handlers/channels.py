import logging
from aiogram import Router
from aiogram.types import ChatMemberUpdated

from ..database import Database

router = Router()
logger = logging.getLogger(__name__)


@router.my_chat_member()
async def track_bot_in_chat(event: ChatMemberUpdated) -> None:
    db: Database = event.bot.get("db")
    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status
    chat = event.chat

    if new_status in {"administrator", "member"} and old_status == "left":
        db.add_channel(chat.id, chat.title or "")
        logger.info("Channel added %s", chat.id)
    elif new_status == "left":
        db.remove_channel(chat.id)
        logger.info("Channel removed %s", chat.id)
