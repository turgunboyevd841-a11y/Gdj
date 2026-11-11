from aiogram.fsm.state import State, StatesGroup


class AddService(StatesGroup):
    name = State()
    price = State()


class Broadcast(StatesGroup):
    text = State()

class EditService(StatesGroup):
    price = State()
    name = State()