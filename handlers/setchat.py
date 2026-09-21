import asyncio

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_ID, GUARANTOR_ID
from database.storage import set_setting, is_coadmin

router = Router()


def is_admin(user_id: int) -> bool:
    return is_coadmin(user_id) or user_id in {ADMIN_ID, GUARANTOR_ID}


@router.message(Command("setchat"))
async def cmd_setchat(message: Message):
    print(f"[SETCHAT] Пришла команда от {message.from_user.id}, "
          f"чат: {message.chat.id}, тип: {message.chat.type}")

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("⚠️ Команду надо писать в группе.")
        return

    if not is_admin(message.from_user.id):
        print(f"[SETCHAT] Отказано: {message.from_user.id} не админ. "
              f"ADMIN_ID={ADMIN_ID}, GUARANTOR_ID={GUARANTOR_ID}, "
              f"is_coadmin={is_coadmin(message.from_user.id)}")
        return

    set_setting("profit_chat_id", str(message.chat.id))

    try:
        await message.delete()
    except Exception:
        pass

    try:
        info = await message.answer(
            f"✅ Этот чат сохранён для профитов.\n"
            f"ID: <code>{message.chat.id}</code>"
        )
        await asyncio.sleep(5)
        try:
            await info.delete()
        except Exception:
            pass
    except Exception:
        pass


@router.message(Command("unsetchat"))
async def cmd_unsetchat(message: Message):
    if not is_admin(message.from_user.id):
        return
    set_setting("profit_chat_id", "")
    try:
        await message.answer("❌ Чат для профитов удалён.")
    except Exception:
        pass
