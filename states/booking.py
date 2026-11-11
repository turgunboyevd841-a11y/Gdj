from aiogram.fsm.state import State, StatesGroup


class Booking(StatesGroup):
    service = State()   # 1. xizmat tanlash
    day = State()       # 2. sana tanlash
    time = State()      # 3. vaqt tanlash
    name = State()      # 4. ism kiritish
    phone = State()     # 5. telefon raqam