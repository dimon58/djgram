"""
Группы состояний
"""
from aiogram.fsm.state import State, StatesGroup


# pylint: disable=too-few-public-methods
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
    #: Детальный просмотр записи
    row_detail = State()
