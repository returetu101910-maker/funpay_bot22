from aiogram import Router
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER

from config import ADMIN_ID, GUARANTOR_ID
from database.storage import (
    is_coadmin, add_chat, remove_chat, get_all_chats,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return is_coadmin(user_id) or user_id in {ADMIN_ID, GUARANTOR_ID}


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
)
async def on_bot_added(event: ChatMemberUpdated):
    if event.chat.type not in ("group", "supergroup"):
        return
    add_chat(event.chat.id, event.chat.title or "")
    print(f"[CHAT] Добавлен: {event.chat.id} ({event.chat.title})")
    try:
        await event.bot.send_message(
            event.chat.id,
            "✅ <b>Чат подключён!</b>\n\n"
            "Теперь сюда будут приходить уведомления о сделках, "
            "а также работает защита от ссылок.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[CHAT] Приветствие не отправилось: {e}")


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER)
)
async def on_bot_removed(event: ChatMemberUpdated):
    if event.chat.type not in ("group", "supergroup"):
        return
    remove_chat(event.chat.id)
    print(f"[CHAT] Удалён: {event.chat.id}")


@router.message(Command("chats"))
async def cmd_chats(message: Message):
    if not is_admin(message.from_user.id):
        return
    chats = get_all_chats()
    if not chats:
        await message.answer("📭 Бот ещё не добавлен ни в одну группу.")
        return
    text = "📋 <b>Чаты бота:</b>\n\n"
    text += "\n".join(f"• <code>{cid}</code>" for cid in chats)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("chatid"))
async def cmd_chatid(message: Message):
    try:
        await message.answer(
            f"🆔 ID: <code>{message.chat.id}</code>\n"
            f"📌 Тип: <code>{message.chat.type}</code>\n"
            f"👤 Ваш ID: <code>{message.from_user.id}</code>",
            parse_mode="HTML"
        )
    except Exception:
        pass
