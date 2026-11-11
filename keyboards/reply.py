from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_BOOK = "📝 Yozilish"
BTN_SERVICES = "💰 Xizmatlar"
BTN_ADDRESS = "📍 Manzil"
BTN_CONTACT = "📞 Aloqa"


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_BOOK)
    kb.button(text=BTN_SERVICES)
    kb.button(text=BTN_ADDRESS)
    kb.button(text=BTN_CONTACT)
    kb.adjust(1, 2, 1)
    return kb.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang...",
    )