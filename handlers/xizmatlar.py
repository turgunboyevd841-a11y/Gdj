from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import queries
from keyboards.reply import BTN_SERVICES
from keyboards.inline_keyboard import services_kb, book_kb

router = Router()


def format_price(price: int) -> str:
    return f"{price:,}".replace(",", " ")


@router.message(F.text == BTN_SERVICES)
async def show_services(message: Message):
    services = await queries.get_services()
    if not services:
        await message.answer("Hozircha xizmatlar ro'yxati bo'sh.")
        return

    text = "<b>💰 Xizmatlar va narxlar:</b>\n\n"
    for _, name, price in services:
        text += f"{name} — <b>{format_price(price)}</b> so'm\n"
    text += "\nBatafsil ma'lumot uchun xizmatni tanlang 👇"

    await message.answer(text, reply_markup=services_kb(services))


@router.callback_query(F.data.startswith("info:"))
async def service_info(call: CallbackQuery):
    service_id = int(call.data.split(":")[1])
    service = await queries.get_service(service_id)
    if not service:
        await call.answer("Xizmat topilmadi", show_alert=True)
        return

    _, name, price = service
    await call.message.edit_text(
        f"<b>{name}</b>\n\n💵 Narxi: <b>{format_price(price)}</b> so'm",
        reply_markup=book_kb(service_id),
    )
    await call.answer()


@router.callback_query(F.data == "services_back")
async def services_back(call: CallbackQuery):
    services = await queries.get_services()

    text = "<b>💰 Xizmatlar va narxlar:</b>\n\n"
    for _, name, price in services:
        text += f"{name} — <b>{format_price(price)}</b> so'm\n"
    text += "\nBatafsil ma'lumot uchun xizmatni tanlang 👇"

    await call.message.edit_text(text, reply_markup=services_kb(services))
    await call.answer()