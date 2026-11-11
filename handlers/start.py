from aiogram import Router,F,Bot,types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from keyboards.reply import main_menu,BTN_ADDRESS,BTN_CONTACT
from config import config
from keyboards.inline_keyboard import map_kb

router=Router()

@router.message(CommandStart())
async def start_handlers(msg:Message,state:FSMContext,bot:Bot):
    await state.clear()
    await msg.answer(
        f"Assalomu alaykum, {msg.from_user.first_name}! 🌸\n\n"
        "Go'zallik salonimizga xush kelibsiz.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu(),
    )



@router.message(F.text == BTN_ADDRESS)   
async def show_address(message: Message):
    await message.answer(
        f"📍 <b>Manzil:</b> {config.salon_address}\n"
        f"🕙 <b>Ish vaqti:</b> {config.work_hours}\n"
        f"📞 {config.salon_phone}",
        reply_markup=map_kb(config.latitude, config.longitude),
    )
    await message.answer_location(config.latitude, config.longitude)

@router.message(F.text == BTN_CONTACT)
async def show_contact(message: Message):
    await message.answer(
        f"📞 <b>Telefon:</b> {config.salon_phone}\n"
        f"🕙 <b>Ish vaqti:</b> {config.work_hours}\n\n"
    )
    await message.answer_contact(
        phone_number=config.salon_phone.replace(" ", ""),
        first_name=config.salon_name,
    )