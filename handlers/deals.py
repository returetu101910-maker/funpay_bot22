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
        await show_screen_edit
