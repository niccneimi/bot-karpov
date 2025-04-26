from aiogram.fsm.state import State, StatesGroup

class buyConnection(StatesGroup):
    selectValute = State()
    checkPromo = State()