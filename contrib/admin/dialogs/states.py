"""
Группы состояний
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """
    Состояния диалога администрирования
    """

    #: Список приложений
    app_list = State()
    #: Список моделей
    model_list = State()
    #: Список строк
    row_list = State()
    #: Поиск строки
    search_row = State()
    #: Детальный просмотр записи
    row_detail = State()
