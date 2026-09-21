from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID, GUARANTOR_ID
from database.storage import (
    add_coadmin, is_coadmin,
    set_balance, set_stars, set_rating, set_deals_count, set_deals_sum,
    save_message, get_chat_history, find_user_by_username, get_user,
    block_user, unblock_user, is_blocked, clear_chat_history,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return is_coadmin(user_id) or user_id in {ADMIN_ID, GUARANTOR_ID}


# ==================== /nemoteam ====================

@router.message(Command("nemoteam"))
async def cmd_nemoteam(message: Message):
    uid = message.from_user.id
    if is_coadmin(uid):
        await message.answer("Вы уже со-админ.")
        return
    add_coadmin(uid)
    await message.answer("<b>✅ Вы получили статус со-админа!</b>")


# ==================== /setbalance ====================

@router.message(Command("setbalance"))
async def cmd_setbalance(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /setbalance <сумма>")
        return
    try:
        value = float(parts[1].replace(",", "."))
    except ValueError:
        await message.answer("Введите число.")
        return
    set_balance(message.from_user.id, value)
    await message.answer(f"✅ Баланс установлен: <b>{value:.2f}</b>")


# ==================== /setstars ====================

@router.message(Command("setstars"))
async def cmd_setstars(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /setstars <кол-во>")
        return
    try:
        value = float(parts[1].replace(",", "."))
    except ValueError:
        await message.answer("Введите число.")
        return
    set_stars(message.from_user.id, value)
    await message.answer(f"✅ Звёзды установлены: <b>{value:.0f}</b>")


# ==================== /set_ret ====================

@router.message(Command("set_ret"))
async def cmd_set_ret(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /set_ret 1-5")
        return
    try:
        value = int(parts[1])
    except ValueError:
        await message.answer("Введите число 1-5.")
        return
    if not 1 <= value <= 5:
        await message.answer("От 1 до 5.")
        return
    set_rating(message.from_user.id, value)
    await message.answer(f"✅ Рейтинг: <b>{value}/5</b>")


@router.message(Command("setrait"))
async def cmd_setrait(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /setrait 1-5")
        return
    try:
        value = int(parts[1])
    except ValueError:
        await message.answer("Введите число 1-5.")
        return
    if not 1 <= value <= 5:
        await message.answer("От 1 до 5.")
        return
    set_rating(message.from_user.id, value)
    await message.answer(f"✅ Рейтинг: <b>{value}/5</b>")


# ==================== /set_sdel ====================

@router.message(Command("set_sdel"))
async def cmd_set_sdel(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /set_sdel <кол-во>")
        return
    try:
        value = int(parts[1])
    except ValueError:
        await message.answer("Введите число.")
        return
    set_deals_count(message.from_user.id, value)
    await message.answer(f"✅ Сделок: <b>{value}</b>")


@router.message(Command("setsdelk"))
async def cmd_setsdelk(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /setsdelk <кол-во>")
        return
    try:
        value = int(parts[1])
    except ValueError:
        await message.answer("Введите число.")
        return
    set_deals_count(message.from_user.id, value)
    await message.answer(f"✅ Сделок: <b>{value}</b>")


# ==================== /sdelkmoney ====================

@router.message(Command("sdelkmoney"))
async def cmd_sdelkmoney(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /sdelkmoney <сумма>")
        return
    try:
        value = float(parts[1].replace(",", "."))
    except ValueError:
        await message.answer("Введите число.")
        return
    set_deals_sum(message.from_user.id, value)
    await message.answer(f"✅ Сумма сделок продавца: <b>{value:.1f}$</b>")


# ==================== /send <текст> <юз/айди> ====================

@router.message(Command("send"))
async def cmd_send(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Использование: <code>/send текст @username</code>\n"
            "или <code>/send текст 123456789</code>",
            parse_mode="HTML"
        )
        return

    target_raw = parts[-1]
    text_to_send = " ".join(parts[1:-1]).strip()

    if not text_to_send:
        await message.answer("Введите текст сообщения.")
        return

    if target_raw.startswith("@") or target_raw.isalpha():
        target_id = find_user_by_username(target_raw)
        if not target_id:
            await message.answer(
                f"❌ Юзер {target_raw} не найден в базе.\n"
                "<i>Он должен хотя бы раз написать боту /start.</i>",
                parse_mode="HTML"
            )
            return
    else:
        try:
            target_id = int(target_raw)
        except ValueError:
            await message.answer("Неверный ID или username.")
            return

    try:
        await message.bot.send_message(
            target_id,
            f"📨 <b>Сообщение от администрации:</b>\n\n{text_to_send}",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить: {e}")
        return

    save_message(uid, target_id, text_to_send)

    await message.answer(f"✅ Отправлено на <code>{target_id}</code>")


# ==================== /chat <юз/айди> ====================

@router.message(Command("chat"))
async def cmd_chat(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/chat @username</code> "
            "или <code>/chat 123456789</code>",
            parse_mode="HTML"
        )
        return

    target_raw = parts[1].strip()

    if target_raw.startswith("@") or target_raw.isalpha():
        target_id = find_user_by_username(target_raw)
        if not target_id:
            await message.answer(f"❌ Юзер {target_raw} не найден в базе.")
            return
    else:
        try:
            target_id = int(target_raw)
        except ValueError:
            await message.answer("Неверный ID или username.")
            return

    # История
    history = get_chat_history(uid, target_id, limit=50)

    target_user = get_user(target_id)
    target_name = f"@{target_user['username']}" if target_user["username"] else str(target_id)

    if not history:
        body = "📭 <i>История переписки пуста.</i>"
    else:
        lines = []
        for msg in history:
            dt = datetime.fromtimestamp(msg["ts"], tz=timezone.utc).strftime("%d.%m %H:%M")
            if msg["from_id"] == uid:
                lines.append(f"[{dt}] ➡️ <b>Вы:</b> {msg['text']}")
            else:
                lines.append(f"[{dt}] ⬅️ <b>Он:</b> {msg['text']}")
        body = "\n".join(lines)

    text = f"💬 <b>История переписки с {target_name}</b>\n\n{body}"

    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>... (обрезано)</i>"

    await message.answer(text, parse_mode="HTML")

    # Автоматически блокируем юзера (бот перестаёт отвечать на его сообщения)
    if not is_blocked(target_id):
        block_user(target_id)
        await message.answer(
            f"🚫 Юзер <code>{target_id}</code> заблокирован ботом.\n"
            f"<i>Бот больше не реагирует на его сообщения и команды.</i>\n\n"
            f"Чтобы разблокировать — <code>/unblock {target_id}</code>",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"ℹ️ Юзер <code>{target_id}</code> уже был заблокирован.")


# ==================== /unblock <юз/айди> ====================

@router.message(Command("unblock"))
async def cmd_unblock(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /unblock <id|@username>")
        return

    target_raw = parts[1].strip()

    if target_raw.startswith("@") or target_raw.isalpha():
        target_id = find_user_by_username(target_raw)
        if not target_id:
            await message.answer(f"❌ Юзер {target_raw} не найден.")
            return
    else:
        try:
            target_id = int(target_raw)
        except ValueError:
            await message.answer("Неверный ID.")
            return

    unblock_user(target_id)
    await message.answer(f"✅ Юзер <code>{target_id}</code> разблокирован.")