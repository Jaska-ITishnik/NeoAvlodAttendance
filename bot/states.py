from aiogram.fsm.state import State, StatesGroup


class AttendanceStates(StatesGroup):
    marking = State()
    confirming = State()
