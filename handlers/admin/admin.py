import asyncio
from datetime import date, timedelta

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from keyboards.admin import days_kb, BTN_SCHEDULE,stats_period_kb,BTN_STATS

from database import queries
from filters import IsAdmin

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())
from keyboards.admin import (
    admin_menu, booking_actions_kb,
    BTN_TODAY, BTN_TOMORROW, BTN_ADD_SERVICE, BTN_BROADCAST, BTN_EXIT,
)
from keyboards.reply import main_menu
from states.admin import AddService, Broadcast

router = Router()
# Bu routerdagi hamma handlerlar faqat adminlar uchun
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

STATUS_ICON = {"pending": "🕓", "confirmed": "✅", "cancelled": "❌"}


# ---------- Kirish / chiqish ----------
@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🛠 Admin panel", reply_markup=admin_menu())


@router.message(F.text == BTN_EXIT)
async def admin_exit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=main_menu())


# ---------- Yozilishlarni ko'rish ----------
async def send_day_bookings(message: Message, day: date):
    rows = await queries.get_bookings_by_day(day.isoformat())
    if not rows:
        await message.answer(f"{day.strftime('%d.%m.%Y')} uchun yozilishlar yo'q.")
        return

    await message.answer(f"📋 <b>{day.strftime('%d.%m.%Y')}</b> — {len(rows)} ta yozilish:")
    for booking_id, time, service, name, phone, status in rows:
        text = (
            f"{STATUS_ICON.get(status, '')} <b>{time}</b> — {service}\n"
            f"👤 {name}\n📞 {phone}"
        )
        kb = booking_actions_kb(booking_id) if status == "pending" else None
        await message.answer(text, reply_markup=kb)


@router.message(F.text == BTN_TODAY)
async def today(message: Message):
    await send_day_bookings(message, date.today())


@router.message(F.text == BTN_TOMORROW)
async def tomorrow(message: Message):
    await send_day_bookings(message, date.today() + timedelta(days=1))


# ---------- Tasdiqlash / rad etish ----------
@router.callback_query(F.data.startswith("adm_ok:"))
async def confirm_booking(call: CallbackQuery, bot: Bot):
    booking_id = int(call.data.split(":")[1])
    booking = await queries.get_booking(booking_id)
    if not booking:
        await call.answer("Topilmadi", show_alert=True)
        return

    _, user_id, service, day, time, *_ = booking
    await queries.set_booking_status(booking_id, "confirmed")

    await call.message.edit_text(call.message.html_text + "\n\n✅ <b>Tasdiqlandi</b>")
    await call.answer("Tasdiqlandi")

    try:
        await bot.send_message(
            user_id,
            f"✅ Yozilishingiz tasdiqlandi!\n\n"
            f"💇 {service}\n📅 {day}\n🕐 {time}\n\nKutib qolamiz! 🌸",
        )
    except Exception:
        await call.message.answer("⚠️ Mijozga xabar yuborib bo'lmadi (botni bloklagan bo'lishi mumkin).")


@router.callback_query(F.data.startswith("adm_no:"))
async def reject_booking(call: CallbackQuery, bot: Bot):
    booking_id = int(call.data.split(":")[1])
    booking = await queries.get_booking(booking_id)
    if not booking:
        await call.answer("Topilmadi", show_alert=True)
        return

    _, user_id, service, day, time, *_ = booking
    await queries.set_booking_status(booking_id, "cancelled")  # vaqt bo'shaydi

    await call.message.edit_text(call.message.html_text + "\n\n❌ <b>Rad etildi</b>")
    await call.answer("Rad etildi")

    try:
        await bot.send_message(
            user_id,
            f"😔 Kechirasiz, {day} kuni soat {time} dagi yozilishingiz tasdiqlanmadi.\n"
            "Iltimos, boshqa vaqtni tanlang.",
        )
    except Exception:
        pass


# ---------- Xizmat qo'shish ----------
@router.message(F.text == BTN_ADD_SERVICE)
async def add_service_start(message: Message, state: FSMContext):
    await state.set_state(AddService.name)
    await message.answer("Xizmat nomini yozing (masalan: 💆 Massaj):")


@router.message(AddService.name, F.text)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddService.price)
    await message.answer("Narxini yozing (faqat raqam, masalan: 120000):")


@router.message(AddService.price, F.text)
async def add_service_price(message: Message, state: FSMContext):
    digits = message.text.replace(" ", "")
    if not digits.isdigit():
        await message.answer("❗ Faqat raqam kiriting, masalan: 120000")
        return

    data = await state.get_data()
    await queries.add_service(data["name"], int(digits))
    await state.clear()
    await message.answer(
        f"✅ Qo'shildi: {data['name']} — {int(digits):,} so'm".replace(",", " "),
        reply_markup=admin_menu(),
    )


# ---------- Hammaga xabar yuborish ----------
@router.message(F.text == BTN_BROADCAST)
async def broadcast_start(message: Message, state: FSMContext):
    await state.set_state(Broadcast.text)
    await message.answer("Barcha mijozlarga yuboriladigan xabarni yozing\n(bekor qilish: /cancel):")


@router.message(Broadcast.text, F.text)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = await queries.get_all_user_ids()
    sent = failed = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram limitiga tushmaslik uchun

    await message.answer(
        f"📢 Yuborildi: {sent}\n⚠️ Yuborilmadi: {failed}",
        reply_markup=admin_menu(),
    )

    # ---------- Kunlik jadval: kim yozilgan, qaysi soat bo'sh ----------
async def build_schedule(day_iso: str) -> str:
    rows = await queries.get_bookings_by_day(day_iso)
    by_time = {r[1]: r for r in rows}   # r = (id, time, service, name, phone, status)

    d = date.fromisoformat(day_iso)
    lines = [f"📅 <b>{d.strftime('%d.%m.%Y')}</b>\n"]

    busy = 0
    for t in queries.TIMES:
        if t in by_time:
            _, _, service, name, phone, status = by_time[t]
            icon = STATUS_ICON.get(status, "")
            lines.append(f"<b>{t}</b> {icon} {name} — {service} ({phone})")
            busy += 1
        else:
            lines.append(f"<b>{t}</b> 🟢 bo'sh")

    free = len(queries.TIMES) - busy
    lines.append(f"\n👥 Band: <b>{busy}</b> ta | 🟢 Bo'sh: <b>{free}</b> ta")
    lines.append("🕓 kutilmoqda  ✅ tasdiqlangan")
    return "\n".join(lines)


@router.message(F.text == BTN_SCHEDULE)
async def schedule_menu(message: Message):
    text = await build_schedule(date.today().isoformat())
    await message.answer(text + "\n\nBoshqa kunni tanlang 👇", reply_markup=days_kb())


@router.callback_query(F.data.startswith("sch:"))
async def schedule_day(call: CallbackQuery):
    day_iso = call.data.split(":", 1)[1]
    text = await build_schedule(day_iso)
    try:
        await call.message.edit_text(text + "\n\nBoshqa kunni tanlang 👇", reply_markup=days_kb())
    except TelegramBadRequest:
        pass   # shu kun qayta bosilsa, matn o'zgarmaydi
    await call.answer()

from keyboards.admin import (
    admin_menu, booking_actions_kb, days_kb,
    manage_list_kb, manage_service_kb, confirm_delete_kb,
    BTN_SCHEDULE, BTN_TODAY, BTN_TOMORROW, BTN_ADD_SERVICE,
    BTN_MANAGE, BTN_BROADCAST, BTN_EXIT,
)
from states.admin import AddService, Broadcast, EditService

# ---------- Xizmatlarni boshqarish ----------
def fmt(price: int) -> str:
    return f"{price:,}".replace(",", " ")


@router.message(F.text == BTN_MANAGE)
async def manage_services(message: Message, state: FSMContext):
    await state.clear()
    services = await queries.get_services()
    if not services:
        await message.answer("Xizmatlar yo'q. Avval ➕ Xizmat qo'shish ni bosing.")
        return
    await message.answer("Qaysi xizmatni o'zgartirmoqchisiz?", reply_markup=manage_list_kb(services))


@router.callback_query(F.data == "mng_back")
async def manage_back(call: CallbackQuery):
    services = await queries.get_services()
    await call.message.edit_text(
        "Qaysi xizmatni o'zgartirmoqchisiz?", reply_markup=manage_list_kb(services)
    )
    await call.answer()


@router.callback_query(F.data.startswith("mng:"))
async def manage_one(call: CallbackQuery):
    service_id = int(call.data.split(":")[1])
    service = await queries.get_service(service_id)
    if not service:
        await call.answer("Topilmadi", show_alert=True)
        return
    _, name, price = service
    await call.message.edit_text(
        f"<b>{name}</b>\n💵 Narxi: <b>{fmt(price)}</b> so'm",
        reply_markup=manage_service_kb(service_id),
    )
    await call.answer()


# --- Narxni o'zgartirish ---
@router.callback_query(F.data.startswith("mng_price:"))
async def edit_price_start(call: CallbackQuery, state: FSMContext):
    service_id = int(call.data.split(":")[1])
    await state.set_state(EditService.price)
    await state.update_data(service_id=service_id)
    await call.message.answer("Yangi narxni yozing (faqat raqam, masalan: 150000):")
    await call.answer()


@router.message(EditService.price, F.text)
async def edit_price_save(message: Message, state: FSMContext):
    digits = message.text.replace(" ", "")
    if not digits.isdigit():
        await message.answer("❗ Faqat raqam kiriting, masalan: 150000")
        return
    data = await state.get_data()
    await queries.update_service_price(data["service_id"], int(digits))
    await state.clear()
    await message.answer(f"✅ Narx yangilandi: {fmt(int(digits))} so'm", reply_markup=admin_menu())


# --- Nomini o'zgartirish ---
@router.callback_query(F.data.startswith("mng_name:"))
async def edit_name_start(call: CallbackQuery, state: FSMContext):
    service_id = int(call.data.split(":")[1])
    await state.set_state(EditService.name)
    await state.update_data(service_id=service_id)
    await call.message.answer("Yangi nomni yozing (masalan: 💆 Massaj):")
    await call.answer()


@router.message(EditService.name, F.text)
async def edit_name_save(message: Message, state: FSMContext):
    data = await state.get_data()
    await queries.update_service_name(data["service_id"], message.text.strip())
    await state.clear()
    await message.answer("✅ Nom yangilandi", reply_markup=admin_menu())


# --- O'chirish ---
@router.callback_query(F.data.startswith("mng_del:"))
async def delete_ask(call: CallbackQuery):
    service_id = int(call.data.split(":")[1])
    service = await queries.get_service(service_id)
    if not service:
        await call.answer("Topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"🗑 <b>{service[1]}</b> xizmatini o'chirasizmi?",
        reply_markup=confirm_delete_kb(service_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("mng_del_yes:"))
async def delete_yes(call: CallbackQuery):
    service_id = int(call.data.split(":")[1])
    await queries.delete_service(service_id)
    await call.message.edit_text("✅ Xizmat o'chirildi (mijozlarga ko'rinmaydi).")
    await call.answer()


# ---------- Statistika ----------
PERIOD_TITLES = {
    "today": "Bugun",
    "week": "Shu hafta",
    "month": "Shu oy",
    "30d": "Oxirgi 30 kun",
}


def period_range(key: str) -> tuple[date, date]:
    today = date.today()
    if key == "today":
        return today, today
    if key == "week":
        return today - timedelta(days=today.weekday()), today   # dushanbadan bugungacha
    if key == "month":
        return today.replace(day=1), today
    return today - timedelta(days=29), today                    # 30d


async def build_stats(key: str) -> str:
    d_from, d_to = period_range(key)
    s = await queries.get_stats(d_from.isoformat(), d_to.isoformat())

    st = s["by_status"]
    pending = st.get("pending", 0)
    confirmed = st.get("confirmed", 0)
    cancelled = st.get("cancelled", 0)
    total = pending + confirmed + cancelled

    cancel_rate = round(cancelled / total * 100) if total else 0

    lines = [
        f"📈 <b>Statistika: {PERIOD_TITLES[key]}</b>",
        f"<i>{d_from.strftime('%d.%m.%Y')} – {d_to.strftime('%d.%m.%Y')}</i>\n",
        f"📋 Jami yozilishlar: <b>{total}</b>",
        f"   🕓 Kutilmoqda: {pending}",
        f"   ✅ Tasdiqlangan: {confirmed}",
        f"   ❌ Bekor/rad: {cancelled} ({cancel_rate}%)\n",
        f"👥 Mijozlar soni: <b>{s['clients']}</b>",
        f"💰 Taxminiy daromad: <b>{s['revenue']:,}</b> so'm".replace(",", " "),
        "   <i>(faqat tasdiqlanganlar)</i>\n",
    ]

    if s["top_services"]:
        lines.append("🏆 <b>Ommabop xizmatlar:</b>")
        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        for i, (name, count) in enumerate(s["top_services"]):
            lines.append(f"{medals[i]} {name} — {count} ta")
    else:
        lines.append("Bu davrda ma'lumot yo'q.")

    lines.append(f"\n🤖 Botdagi jami foydalanuvchilar: {s['total_users']}")
    return "\n".join(lines)


@router.message(F.text == BTN_STATS)
async def stats_menu(message: Message):
    text = await build_stats("today")
    await message.answer(text, reply_markup=stats_period_kb())


@router.callback_query(F.data.startswith("st:"))
async def stats_period(call: CallbackQuery):
    key = call.data.split(":")[1]
    if key not in PERIOD_TITLES:
        await call.answer()
        return
    text = await build_stats(key)
    try:
        await call.message.edit_text(text, reply_markup=stats_period_kb())
    except TelegramBadRequest:
        pass   # bir xil davr qayta bosilsa, matn o'zgarmaydi
    await call.answer()