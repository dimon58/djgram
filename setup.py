import logging

from aiogram import Dispatcher
from aiogram.filters import Command

from djgram.contrib.communication import router as communication_router
from djgram.contrib.misc.handlers import cancel_handler

logger = logging.getLogger(__name__)


def setup(dp: Dispatcher):
    dp.message.register(cancel_handler, Command("cancel"))
    dp.include_router(communication_router)

    logger.info("djgram setup")
