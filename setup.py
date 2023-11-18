import logging

from aiogram import Dispatcher

from djgram.contrib.communication import router as communication_router

logger = logging.getLogger(__name__)


def setup(dp: Dispatcher):
    dp.include_router(communication_router)

    logger.info("djgram setup")
