from datetime import date, timedelta

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

BTN_SCHEDULE = "📊 Jadval"
BTN_TODAY = "📅 Bugun"
BTN_TOMORROW = "📆 Ertaga"
BTN_ADD_SERVICE = "➕ Xizmat qo'shish"
BTN_MANAGE = "🛠 Xizmatlarni boshqarish"
BTN_BROADCAST = "📢 Xabar yuborish"
BTN_EXIT = "⬅️ Chiqish"
BTN_STATS = "📈 Statistika"


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=BTN_SCHEDULE)
    kb.button(text=BTN_STATS)
    kb.button(text=BTN_TODAY)
    kb.button(text=BTN_TOMORROW)
    kb.button(text=BTN_ADD_SERVICE)
    kb.button(text=BTN_MANAGE)
    kb.button(text=BTN_BROADCAST)
    kb.button(text=BTN_EXIT)
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup(resize_keyboard=True)


def booking_actions_kb(booking_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"adm_ok:{booking_id}")
    kb.button(text="❌ Rad etish", callback_data=f"adm_no:{booking_id}")
    kb.adjust(2)
    return kb.as_markup()


def days_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(7):
        d = date.today() + timedelta(days=i)
        kb.button(text=d.strftime("%d.%m"), callback_data=f"sch:{d.isoformat()}")
    kb.adjust(4)
    return kb.as_markup()


def manage_list_kb(services: list[tuple]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for sid, name, price in services:
        kb.button(
            text=f"{name} — {price:,} so'm".replace(",", " "),
            callback_data=f"mng:{sid}",
        )
    kb.adjust(1)
    return kb.as_markup()


def manage_service_kb(service_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Narxni o'zgartirish", callback_data=f"mng_price:{service_id}")
    kb.button(text="✏️ Nomini o'zgartirish", callback_data=f"mng_name:{service_id}")
    kb.button(text="🗑 O'chirish", callback_data=f"mng_del:{service_id}")
    kb.button(text="⬅️ Orqaga", callback_data="mng_back")
    kb.adjust(1)
    return kb.as_markup()


def confirm_delete_kb(service_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chirish", callback_data=f"mng_del_yes:{service_id}")
    kb.button(text="❌ Yo'q", callback_data=f"mng:{service_id}")
    kb.adjust(2)
    return kb.as_markup()

def stats_period_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Bugun", callback_data="st:today")
    kb.button(text="Shu hafta", callback_data="st:week")
    kb.button(text="Shu oy", callback_data="st:month")
    kb.button(text="Oxirgi 30 kun", callback_data="st:30d")
    kb.adjust(2)
    return kb.as_markup()