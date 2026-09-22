from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import t, COUNTRIES
from config import WEBAPP_URL


def main_menu_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(user_id, "btn_create_deal"), callback_data="create_deal", style="success")
    builder.button(text=t(user_id, "btn_profile"), callback_data="profile", style="success")
    builder.button(text=t(user_id, "btn_withdraw"), callback_data="withdraw", style="success")
    builder.button(text=t(user_id, "btn_details"), callback_data="details", style="success")
    builder.button(text=t(user_id, "btn_referrals"), callback_data="referrals", style="success")
    builder.button(text=t(user_id, "btn_language"), callback_data="language", style="success")
    builder.button(
        text=t(user_id, "btn_reviews"),
        web_app=WebAppInfo(url=WEBAPP_URL),
        style="primary"   # ⚡ Отзывы — синяя
    )
    builder.button(text=t(user_id, "btn_support"), callback_data="support", style="success")
    builder.adjust(1, 1, 2, 2, 1, 1, 1)
    return builder.as_markup()


def back_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"← {t(user_id, 'btn_back')}",
        callback_data="back_to_main",
        style="danger"
    )
    builder.adjust(1)
    return builder.as_markup()


def profile_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(user_id, "btn_withdraw"), callback_data="withdraw", style="success")
    builder.button(
        text=f"← {t(user_id, 'btn_back')}",
        callback_data="back_to_main",
        style="danger"
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def language_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, flag, name in COUNTRIES:
        builder.button(text=f"{flag} {name}", callback_data=f"lang_{code}", style="success")
    builder.button(
        text=f"← {t(user_id, 'btn_back')}",
        callback_data="back_to_main",
        style="danger"
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def language_first_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, flag, name in COUNTRIES:
        builder.button(text=f"{flag} {name}", callback_data=f"lang_{code}", style="success")
    builder.adjust(2, 2)
    return builder.as_markup()
