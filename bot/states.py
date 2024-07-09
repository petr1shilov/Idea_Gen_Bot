from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    get_agents = State()
    get_len = State()
    get_them = State()
    get_instrustion = State()