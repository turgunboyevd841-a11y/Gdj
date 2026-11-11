
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config


def services_kb(services: list[tuple]) -> InlineKeyboardMarkup:
    """services: [(id, name, price), ...]"""
    kb = InlineKeyboardBuilder()
    for service_id, name, price in services:
        kb.button(text=f"{name} — {price:,} so'm".replace(",", " "),
                  callback_data=f"info:{service_id}")
    kb.adjust(1)
    return kb.as_markup()


def book_kb(service_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Shu xizmatga yozilish", callback_data=f"srv:{service_id}")
    kb.button(text="⬅️ Orqaga", callback_data="services_back")
    kb.adjust(1)
    return kb.as_markup()

def map_kb(lat: float, lon: float) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📍 Google Maps",
              url=f"https://www.google.com/maps?q={config.latitude},{config.longitude}")
    kb.button(text="🗺 Yandex Maps",
              url=f"https://yandex.com/maps/?pt={lon},{lat}&z=17&l=map")
    kb.button(text="🧭 2GIS",
              url=f"https://2gis.uz/geo/{lon},{lat}")
    kb.adjust(1)
    return kb.as_markup()

def contact_kb(telegram: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.adjust(2)
    return kb.as_markup()