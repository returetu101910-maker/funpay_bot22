import asyncio

from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER

from config import ADMIN_ID, GUARANTOR_ID
from database.storage import set_setting, get_setting, is_coadmin

router = Router()


def is_admin(user_id: int) -> bool:
    return is_coadmin(user_id) or user_id in {ADMIN_ID, GUARANTOR_ID}


# ==================== АВТО-СОХРАНЕНИЕ ПРИ ДОБАВЛЕНИИ В ГРУППУ ====================

@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER)
)
async def on_bot_added(event: ChatMemberUpdated):
    """Когда бота добавили в группу — сохраняем её ID."""
    if event.chat.type not in ("group", "supergroup"):
        return

    set_setting("profit_chat_id", str(event.chat.id))
    print(f"[SETCHAT] Бот добавлен в чат {event.chat.id} ({event.chat.title}) — сохранено")

    try:
        await event.bot.send_message(
            event.chat.id,
            "✅ <b>Чат сохранён для профитов!</b>\n\n"
            "Теперь сюда будут приходить уведомления о сделках.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[SETCHAT] Не удалось отправить приветствие: {e}")


# ==================== /setchat ====================

@router.message(Command("setchat"))
async def cmd_setchat(message: Message):
    print(f"[SETCHAT] Команда! from={message.from_user.id} "
          f"chat={message.chat.id} type={message.chat.type}")

    if message.chat.type not in ("group", "supergroup"):
        try:
            await message.answer("⚠️ Команду надо писать в группе.")
        except Exception:
            pass
        return

    if not is_admin(message.from_user.id):
        print(f"[SETCHAT] Отказано: {message.from_user.id} не админ "
              f"(ADMIN_ID={ADMIN_ID}, GUARANTOR_ID={GUARANTOR_ID})")
        try:
            await message.answer(
                f"❌ У вас нет прав.\nВаш ID: <code>{message.from_user.id}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    set_setting("profit_chat_id", str(message.chat.id))
    print(f"[SETCHAT] Сохранён chat_id={message.chat.id}")

    try:
        await message.delete()
    except Exception:
        pass

    try:
        info = await message.answer(
            f"✅ <b>Этот чат сохранён для профитов.</b>\n"
            f"ID: <code>{message.chat.id}</code>"
        )
        await asyncio.sleep(5)
        try:
            await info.delete()
        except Exception:
            pass
    except Exception:
        pass


# ==================== /chatid — узнать ID чата ====================

@router.message(Command("chatid"))
async def cmd_chatid(message: Message):
    try:
        await message.answer(
            f"🆔 ID этого чата: <code>{message.chat.id}</code>\n"
            f"📌 Тип: <code>{message.chat.type}</code>\n"
            f"👤 Ваш ID: <code>{message.from_user.id}</code>",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ==================== /unsetchat ====================

@router.message(Command("unsetchat"))
async def cmd_unsetchat(message: Message):
    if not is_admin(message.from_user.id):
        return
    set_setting("profit_chat_id", "")
    print("[SETCHAT] Чат удалён")
    try:
        await message.answer("❌ Чат для профитов удалён.")
    except Exception:
        pass


# ==================== /getchat — показать текущий сохранённый чат ====================

@router.message(Command("getchat"))
async def cmd_getchat(message: Message):
    if not is_admin(message.from_user.id):
        return
    current = get_setting("profit_chat_id")
    try:
        if current:
            await message.answer(f"📌 Текущий чат для профитов: <code>{current}</code>")
        else:
            await message.answer("📌 Чат для профитов не задан.")
    except Exception:
        pass
