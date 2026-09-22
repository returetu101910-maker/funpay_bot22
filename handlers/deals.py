import secrets
import re
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME, ADMIN_ID, GUARANTOR_ID, PROFIT_PHOTO
from states.deal_states import DealStates
from keyboards.deal_kb import (
    deal_method_kb, deal_currency_kb, deal_amount_kb,
    deal_description_kb, deal_card_kb, deal_offer_kb,
    deal_seller_kb, deal_done_kb, deal_cancelled_kb,
    deal_admin_notify_kb,
)
from keyboards.menus import main_menu_kb, back_kb, language_kb, language_first_kb
from utils.notifier import show_screen, show_screen_edit
from utils.i18n import t, USER_LANGS, LANG_HEADER
from database.storage import (
    get_cards, get_user, create_deal, get_deal, update_deal,
    add_balance, add_stars, inc_completed_deals, get_completed_deals,
    ensure_user, is_coadmin, add_referral, get_all_chats,
)
from handlers.start import main_text

router = Router()


NFT_PATTERNS = [
    re.compile(r"^https?://t\.me/nft/", re.IGNORECASE),
    re.compile(r"^https?://portals\.tg/", re.IGNORECASE),
    re.compile(r"^https?://getgems\.io/", re.IGNORECASE),
    re.compile(r"^https?://fragment\.com/", re.IGNORECASE),
    re.compile(r"^https?://mrkt\.ton/", re.IGNORECASE),
    re.compile(r"^https?://ton\.diamonds/", re.IGNORECASE),
    re.compile(r"^https?://tonnel\.network/", re.IGNORECASE),
]


def is_nft_link(text: str) -> bool:
    text = (text or "").strip()
    return any(p.match(text) for p in NFT_PATTERNS)


@router.callback_query(F.data == "create_deal")
async def cb_create_deal(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    ensure_user(uid, call.from_user.username or "")
    await state.clear()
    await state.set_state(DealStates.choosing_method)
    await show_screen(call, "💳 <b>Выберите способ оплаты:</b>", deal_method_kb(uid))
    await call.answer()


@router.callback_query(F.data == "deal_method_card")
async def cb_method_card(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    if not get_cards(uid):
        await call.answer("У вас нету карты в реквизитах!", show_alert=True)
        return
    await state.update_data(method="card")
    await state.set_state(DealStates.choosing_currency)
    is_special = is_coadmin(uid) or uid in {ADMIN_ID, GUARANTOR_ID}
    await show_screen(
        call,
        "🌐 <b>Выберите валюту:</b>",
        deal_currency_kb(uid, is_special)
    )
    await call.answer()


@router.callback_query(F.data == "deal_method_stars")
async def cb_method_stars(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    await state.update_data(method="stars", currency="STARS")
    await state.set_state(DealStates.entering_amount)
    await show_screen(call, "💰 <b>Сколько вы платите?</b>", deal_amount_kb(uid))
    await call.answer()


@router.callback_query(F.data.startswith("deal_currency_"))
async def cb_currency(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    currency = call.data.replace("deal_currency_", "")
    await state.update_data(currency=currency)
    await state.set_state(DealStates.entering_amount)
    await show_screen(call, f"💰 <b>Сколько вы платите? ({currency})</b>", deal_amount_kb(uid))
    await call.answer()


@router.message(DealStates.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    uid = message.from_user.id
    try:
        await message.delete()
    except Exception:
        pass

    txt = (message.text or "").strip().replace(",", ".")
    try:
        amount = float(txt)
    except ValueError:
        return
    if amount <= 0:
        return

    await state.update_data(amount=amount)
    await state.set_state(DealStates.entering_description)
    await show_screen_edit(
        message.bot, uid, message.chat.id,
        "🔗 <b>Отправьте ссылку товара (NFT):</b>",
        deal_description_kb(uid)
    )


@router.message(DealStates.entering_description)
async def process_description(message: Message, state: FSMContext):
    uid = message.from_user.id
    raw = (message.text or "").strip()

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    amount = data.get("amount")
    currency = data.get("currency")
    method = data.get("method", "card")

    if amount is None or currency is None:
        await state.clear()
        await show_screen_edit(
            message.bot, uid, message.chat.id,
            "⚠️ <b>Сессия устарела.</b>\n\n"
            "Нажмите /start → <b>Создать сделку</b>, чтобы начать заново.",
            back_kb(uid)
        )
        return

    if not is_nft_link(raw):
        await show_screen_edit(
            message.bot, uid, message.chat.id,
            "❌ <b>Это не похоже на ссылку NFT.</b>\n\n"
            "Пример:\n"
            "<code>https://t.me/nft/Snake-1234</code>\n\n"
            "<i>Поддержка: t.me/nft, portals.tg, getgems.io, fragment.com, "
            "mrkt.ton, ton.diamonds, tonnel.network</i>",
            deal_description_kb(uid)
        )
        return

    description = raw
    user = get_user(uid)

    deal_id = secrets.token_hex(4)
    create_deal(
        deal_id=deal_id,
        creator_id=uid,
        amount=amount,
        currency=currency,
        description=description,
        method=method,
    )

    link = f"https://t.me/{BOT_USERNAME}?start={deal_id}"

    if method == "stars":
        give_str = f"⭐ {amount:.0f} Stars"
        pay_str = f"⭐ {amount:.0f} Stars"
    else:
        give_str = f"💰 {amount:.1f} {currency}"
        pay_str = f"💰 {amount:.1f} {currency}"

    seller_display = f"@{user['username']}" if user["username"] else "---"

    text = (
        f"🎁 <b>Сделка</b> <code>{deal_id}</code>\n"
        f"<b>Тип сделки:</b> 🎁 Подарки\n\n"
        f"👤 <i>Вы покупатель, у вас есть 15 минут на оплату сделки!</i>\n\n"
        f"🎯 <b>Продавец:</b> {seller_display}\n"
        f"• <b>Количество сделок продавца:</b> {user['deals_count']}\n"
        f"• <b>Сумма сделок продавца:</b> {user['deals_sum']:.1f}$\n\n"
        f"• <b>Вы покупаете:</b> {description}\n"
        f"• <b>Вы отдаете:</b> {give_str}\n\n"
        f"<b>Реквизиты для оплаты:</b>\n"
        f"💬 <b>Оплата через поддержку</b>\n"
        f"Нажмите кнопку «Саппорт» ниже — оператор подскажет, как оплатить.\n\n"
        f"👉 @FunPayUaHelper\n\n"
        f"💵 <b>Сумма к оплате:</b>\n"
        f"{pay_str}\n\n"
        f"🔖 <b>Комментарий к транзакции:</b>\n"
        f"<code>{deal_id}</code>\n\n"
        f"🔗 <b>Ссылка для покупателя:</b>\n"
        f"<code>{link}</code>\n\n"
        f"<blockquote>❗ Пожалуйста, убедитесь что при оплате указываете "
        f"обязательный комментарий (memo) и точную сумму!</blockquote>\n\n"
        f"<i>После оплаты ожидайте подтверждения администратором.</i>"
    )

    await show_screen_edit(
        message.bot, uid, message.chat.id,
        text, deal_card_kb(uid, deal_id, link)
    )
    await state.clear()


@router.callback_query(F.data == "deal_back_to_method")
async def cb_back_method(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    await state.set_state(DealStates.choosing_method)
    await show_screen(call, "💳 <b>Выберите способ оплаты:</b>", deal_method_kb(uid))
    await call.answer()


@router.callback_query(F.data == "deal_back_to_currency")
async def cb_back_currency(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    await state.set_state(DealStates.choosing_currency)
    is_special = is_coadmin(uid) or uid in {ADMIN_ID, GUARANTOR_ID}
    await show_screen(
        call,
        "🌐 <b>Выберите валюту:</b>",
        deal_currency_kb(uid, is_special)
    )
    await call.answer()


@router.callback_query(F.data == "deal_back_to_amount")
async def cb_back_amount(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    await state.set_state(DealStates.entering_amount)
    await show_screen(call, "💰 <b>Сколько вы платите?</b>", deal_amount_kb(uid))
    await call.answer()


@router.callback_query(F.data == "deal_cancel")
async def cb_deal_cancel(call: CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    await state.clear()
    await show_screen(
        call,
        "✅ <b>Сделка отменена успешно</b>",
        deal_cancelled_kb(uid)
    )
    await call.answer()


@router.message(CommandStart(deep_link=True))
async def cmd_start_with_deal(message: Message):
    uid = message.from_user.id
    ensure_user(uid, message.from_user.username or "")

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return
    payload = parts[1].strip()

    if payload.startswith("ref_"):
        try:
            referrer_id = int(payload.replace("ref_", ""))
        except ValueError:
            return
        add_referral(referrer_id, uid)
        try:
            await message.bot.send_message(
                referrer_id,
                f"🎉 <b>Новый реферал!</b>\n\n"
                f"👤 {message.from_user.full_name}",
                parse_mode="HTML"
            )
        except Exception:
            pass

        if uid not in USER_LANGS:
            await show_screen(message, LANG_HEADER, language_first_kb())
        else:
            await show_screen(message, main_text(uid), main_menu_kb(uid))
        return

    deal_id = payload
    deal = get_deal(deal_id)
    if not deal:
        await message.answer("❌ <b>Сделка не найдена</b>", parse_mode="HTML")
        return

    if deal["creator_id"] != uid:
        add_referral(deal["creator_id"], uid)

    status = deal["status"]
    if status == "accepted":
        await message.answer("⚠️ <b>Сделка уже принята</b>", parse_mode="HTML")
        return
    if status == "sent_to_admin":
        await message.answer("⏳ <b>Сделка уже на проверке у администратора</b>", parse_mode="HTML")
        return
    if status == "completed":
        await message.answer("✅ <b>Сделка уже завершена</b>", parse_mode="HTML")
        return
    if status == "cancelled":
        await message.answer("❌ <b>Сделка отменена</b>", parse_mode="HTML")
        return

    if deal["method"] == "stars":
        sum_line = f"<b>{deal['amount']:.0f} STARS</b>"
    else:
        sum_line = f"<b>{deal['amount']:.1f} {deal['currency']}</b>"

    text = (
        f"📩 <b>Вам предложили сделку</b>\n"
        f"🆔 Сделка номер: <code>#{deal_id}</code>\n\n"
        f"💵 <b>Вам предлагают:</b>\n"
        f"{sum_line}\n"
        f"📦 <b>за:</b>\n"
        f"<b>{deal['description']}</b>"
    )
    await message.answer(text, reply_markup=deal_offer_kb(uid, deal_id), parse_mode="HTML")


@router.callback_query(F.data.startswith("deal_accept_"))
async def cb_deal_accept(call: CallbackQuery):
    uid = call.from_user.id
    deal_id = call.data.replace("deal_accept_", "")
    deal = get_deal(deal_id)

    if not deal:
        await call.answer("Сделка не найдена", show_alert=True)
        return
    if deal["status"] != "waiting_payment":
        await call.answer("Сделка уже принята", show_alert=True)
        return

    update_deal(deal_id, seller_id=uid, status="accepted")

    text = (
        "✅ <b>Сделка принята!</b>\n\n"
        f"📦 Отправьте {deal['description']}\n"
        f"на аккаунт <b>@FunPayUaHelper</b>\n\n"
        "После получения NFT покупатель оплатит сделку.\n\n"
        "Когда отправите — нажмите кнопку <b>«Я отправил!»</b> ниже."
    )
    await show_screen(call, text, deal_seller_kb(uid, deal_id))
    await call.answer()


@router.callback_query(F.data.startswith("deal_decline_"))
async def cb_deal_decline(call: CallbackQuery):
    uid = call.from_user.id
    deal_id = call.data.replace("deal_decline_", "")
    update_deal(deal_id, status="cancelled")
    await call.answer("Сделка отклонена", show_alert=True)


@router.callback_query(F.data.startswith("deal_sent_"))
async def cb_deal_sent(call: CallbackQuery):
    uid = call.from_user.id
    deal_id = call.data.replace("deal_sent_", "")
    deal = get_deal(deal_id)

    if not deal:
        await call.answer("Сделка не найдена", show_alert=True)
        return
    if deal["status"] != "accepted":
        await call.answer("Сделка не в статусе ожидания NFT", show_alert=True)
        return

    update_deal(deal_id, status="sent_to_admin")

    await show_screen(
        call,
        "⏳ <b>Ждём подтверждения администратора.</b>\n\n"
        "Пожалуйста, подождите — обычно это занимает несколько минут.",
        back_kb(uid)
    )
    await call.answer("Отправлено админу")

    admin_text = (
        f"🔔 <b>Вам отправили!</b>\n\n"
        f"🆔 <b>Сделка:</b> <code>{deal_id}</code>\n"
        f"📦 <b>NFT:</b> {deal['description']}\n"
        f"💰 <b>Сумма:</b> {deal['amount']:.1f} {deal['currency']}\n"
        f"👤 <b>Продавец:</b> <code>{uid}</code>\n\n"
        f"Проверьте NFT и нажмите кнопку ниже:"
    )

    for admin_id in {ADMIN_ID, GUARANTOR_ID}:
        try:
            await call.bot.send_message(
                admin_id,
                admin_text,
                reply_markup=deal_admin_notify_kb(deal_id),
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("deal_confirm_"))
async def cb_deal_confirm(call: CallbackQuery):
    uid = call.from_user.id
    if not (is_coadmin(uid) or uid in {ADMIN_ID, GUARANTOR_ID}):
        await call.answer("Нет доступа", show_alert=True)
        return

    deal_id = call.data.replace("deal_confirm_", "")
    deal = get_deal(deal_id)

    if not deal:
        await call.answer("Сделка не найдена", show_alert=True)
        return
    if deal["status"] == "completed":
        await call.answer("Сделка уже подтверждена", show_alert=True)
        return

    creator_id = deal["creator_id"]
    seller_id = deal["seller_id"]
    amount = deal["amount"]
    method = deal["method"]

    payout = amount * 0.97

    if method == "stars":
        add_stars(seller_id, payout)
        payout_str = f"⭐ {payout:.2f} Stars"
    else:
        add_balance(seller_id, payout)
        payout_str = f"💰 {payout:.2f} {deal['currency']}"

    update_deal(deal_id, status="completed")
    inc_completed_deals(creator_id)
    inc_completed_deals(seller_id)

    try:
        await call.bot.send_message(
            seller_id,
            f"✅ <b>Сделка успешно завершена!</b>\n\n"
            f"🆔 Сделка: <code>{deal_id}</code>\n"
            f"💵 <b>Сумма зачислена на баланс:</b> {payout_str}\n\n"
            f"<i>Комиссия платформы: 3%</i>",
            reply_markup=deal_done_kb(seller_id),
            parse_mode="HTML"
        )
    except Exception:
        pass

    try:
        await call.bot.send_message(
            creator_id,
            f"🎉 <b>Сделка завершена!</b>\n\n"
            f"🆔 <code>{deal_id}</code>\n"
            f"Продавец получил оплату. Спасибо!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    chats = get_all_chats()
    if chats:
        buyer = get_user(creator_id)
        buyer_name = (
            f"@{buyer['username']}" if buyer["username"]
            else f"<code>{creator_id}</code>"
        )

        profit_caption = (
            "💰 <b>НОВЫЙ ПРОФИТ!</b>\n\n"
            f"👨‍💻 <b>Воркер:</b> {buyer_name}\n"
            f"🎁 <b>NFT:</b> {deal['description']}"
        )

        photo = None
        try:
            photo = FSInputFile(PROFIT_PHOTO)
        except Exception as e:
            print(f"[PROFIT] Не нашёл фото: {e}")

        for chat_id in chats:
            try:
                if photo:
                    await call.bot.send_photo(
                        chat_id,
                        photo=photo,
                        caption=profit_caption,
                        parse_mode="HTML",
                    )
                else:
                    await call.bot.send_message(
                        chat_id,
                        profit_caption,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                print(f"[PROFIT] Отправлено в {chat_id}")
            except Exception as e:
                print(f"[PROFIT] Ошибка в {chat_id}: {e}")

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await call.answer("✅ Сделка подтверждена")


@router.callback_query(F.data == "withdraw")
async def cb_withdraw(call: CallbackQuery):
    uid = call.from_user.id
    done = get_completed_deals(uid)

    if done < 3:
        body = (
            "🔒 <b>Для безопасности вывода нужно совершить 3 сделки</b>\n\n"
            f"📊 Совершено сделок: <b>{done}/3</b>"
        )
    else:
        body = (
            "✅ <b>Вывод доступен</b>\n\n"
            f"📊 Совершено сделок: <b>{done}</b>"
        )

    text = f"💸 <b>Вывод</b>\n\n{body}"
    await show_screen(call, text, back_kb(uid))
    await call.answer()
