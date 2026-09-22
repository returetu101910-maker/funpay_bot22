import re
import asyncio

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command

from database.storage import (
    inc_link_count, reset_link_count,
    ban_user, is_banned, unban_user,
)

router = Router()

URL_REGEX = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/)",
    re.IGNORECASE,
)

MAX_LINKS = 3


def has_link(message: Message) -> bool:
    if message.entities:
        for ent in message.entities:
            if ent.type in ("url", "text_link"):
                return True
    text = message.text or message.caption or ""
    if text and URL_REGEX.search(text):
        return True
    return False


async def is_admin(message: Message) -> bool:
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )
    except Exception:
        return False


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def antilink_handler(message: Message):
    if not message.from_user or message.from_user.is_bot:
        return
    if message.text and message.text.startswith("/"):
        return

    # Забаненный — сразу кик
    if is_banned(message.chat.id, message.from_user.id):
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
            )
        except Exception:
            pass
        return

    # Админ — пропуск
    if await is_admin(message):
        return

    # Нет ссылки — пропуск
    if not has_link(message):
        return

    # Удаляем
    try:
        await message.delete()
    except Exception:
        pass

    count = inc_link_count(message.chat.id, message.from_user.id)

    # Кик за 3-ю
    if count >= MAX_LINKS:
        ban_user(message.chat.id, message.from_user.id)
        try:
            await message.bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
            )
        except Exception:
            pass
        try:
            warn = await message.answer(
                f"🚫 {message.from_user.mention} забанен и кикнут "
                f"за {MAX_LINKS} ссылки!"
            )
            await asyncio.sleep(10)
            try:
                await warn.delete()
            except Exception:
                pass
        except Exception:
            pass
        return

    # Предупреждение
    try:
        warn = await message.answer(
            f"⚠️ {message.from_user.mention}, "
            f"ссылки могут отправлять только администраторы!\n"
            f"Предупреждение: <b>{count}/{MAX_LINKS}</b>"
        )
        await asyncio.sleep(8)
        try:
            await warn.delete()
        except Exception:
            pass
    except Exception:
        pass


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return
    if not await is_admin(message):
        return

    target_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id

    try:
        await message.delete()
    except Exception:
        pass

    if not target_id:
        return

    reset_link_count(message.chat.id, target_id)
    unban_user(message.chat.id, target_id)
    try:
        await message.bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
        )
    except Exception:
        pass

    try:
        info = await message.answer(f"✅ Сброшено для <code>{target_id}</code>")
        await asyncio.sleep(5)
        try:
            await info.delete()
        except Exception:
            pass
    except Exception:
        pass
