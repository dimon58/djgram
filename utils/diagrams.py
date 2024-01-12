import logging

from aiogram import Router
from aiogram_dialog.tools import render_transitions
from graphviz import ExecutableNotFound

logger = logging.getLogger(__name__)


def render_transitions_safe(
    router: Router,
    title: str = "Aiogram Dialog",
    filename: str = "aiogram_dialog",
    format: str = "png",
):
    """
    Рендерит диаграммы диалогов

    Предотвращает падение приложения при отсутствии установленного Graphviz

    https://aiogram-dialog.readthedocs.io/en/stable/helper_tools/index.html
    """

    try:
        render_transitions(
            router=router,
            title=title,
            filename=filename,
            format=format,
        )
    except ExecutableNotFound:
        logger.warning(
            "Can not render %s because Graphviz executable not found. "
            "Install it https://graphviz.org/download/ or set ENABLE_DIALOG_DIAGRAMS_GENERATION=False in configs.py",
            title,
        )
