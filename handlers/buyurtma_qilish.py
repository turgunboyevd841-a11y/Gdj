from datetime import date, timedelta

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery, Message,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from database import queries
from keyboards.admin import booking_actions_kb
from keyboards.reply import BTN_BOOK, main_menu
from states.booking import Booking

router = Router()


# ---------- 1. Boshlash va xizmat tanlash ----------
@router.message(F.text == BTN_BOOK)
async def book_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Booking.service)

    services = await queries.get_services()
    kb = InlineKeyboardBuilder()
    for sid, name, price in services:
        kb.button(
            text=f"{name} — {price:,} so'm".replace(",", " "),
            callback_data=f"srv:{sid}",
        )
    kb.adjust(1)
    await message.answer("Xizmatni tanlang:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("srv:"))
async def choose_service(call: CallbackQuery, state: FSMContext):
    service_id = int(call.data.split(":")[1])
    service = await queries.get_service(service_id)
    if not service:
        await call.answer("Xizmat topilmadi", show_alert=True)
        return

    await state.update_data(service_id=service_id, service_name=service[1])
    await state.set_state(Booking.day)

    kb = InlineKeyboardBuilder()
    for i in range(7):
        d = date.today() + timedelta(days=i)
        kb.button(text=d.strftime("%d.%m"), callback_data=f"day:{d.isoformat()}")
    kb.adjust(4)

    await call.message.edit_text("📅 Sanani tanlang:", reply_markup=kb.as_markup())
    await call.answer()


# ---------- 2. Sana ----------
@router.callback_query(Booking.day, F.data.startswith("day:"))
async def choose_day(call: CallbackQuery, state: FSMContext):
    day = call.data.split(":", 1)[1]
    free = await queries.get_free_times(day)

    if not free:
        await call.answer("Bu kunda bo'sh vaqt yo'q, boshqa kunni tanlang", show_alert=True)
        return

    await state.update_data(day=day)
    await state.set_state(Booking.time)

    kb = InlineKeyboardBuilder()
    for t in free:
        kb.button(text=t, callback_data=f"time:{t}")
    kb.adjust(3)

    await call.message.edit_text("🕐 Vaqtni tanlang:", reply_markup=kb.as_markup())
    await call.answer()


# ---------- 3. Vaqt ----------
@router.callback_query(Booking.time, F.data.startswith("time:"))
async def choose_time(call: CallbackQuery, state: FSMContext):
    await state.update_data(time=call.data.split(":", 1)[1])
    await state.set_state(Booking.name)
    await call.message.edit_text("👤 Ismingizni yozing:")
    await call.answer()


# ---------- 4. Ism ----------
@router.message(Booking.name, F.text)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(Booking.phone)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "📞 Telefon raqamingizni yuboring (tugma bosing yoki yozing):",
        reply_markup=kb,
    )


# ---------- 5. Telefon va SAQLASH ----------
@router.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext, bot: Bot):
    phone = message.contact.phone_number if message.contact else message.text
    if not phone:
        await message.answer("❗ Telefon raqamini yuboring.")
        return

    data = await state.get_data()
    await state.clear()

    # bookings jadvali users ga bog'langan, shuning uchun avval foydalanuvchini saqlaymiz
    user = message.from_user
    await queries.add_user(user.id, user.full_name, user.username)

    booking_id = await queries.add_booking(
        user_id=user.id,
        service_id=data["service_id"],
        day=data["day"],
        time=data["time"],
        name=data["name"],
        phone=phone,
    )

    if booking_id is None:
        await message.answer(
            "😔 Kechirasiz, bu vaqt hozirgina band bo'ldi. Boshqa vaqt tanlang.",
            reply_markup=main_menu(),
        )
        return

    summary = (
        f"🔹 Xizmat: {data['service_name']}\n"
        f"🔹 Sana: {data['day']}\n"
        f"🔹 Vaqt: {data['time']}\n"
        f"🔹 Ism: {data['name']}\n"
        f"🔹 Telefon: {phone}"
    )

    await message.answer(
        "✅ Arizangiz qabul qilindi! Admin tasdiqlagach xabar beramiz.\n\n" + summary,
        reply_markup=main_menu(),
    )

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 <b>Yangi buyurtma</b>\n\n{summary}",
                reply_markup=booking_actions_kb(booking_id),
            )
        except Exception as e:
            print("Adminga yuborib bo'lmadi:", e)