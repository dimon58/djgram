"""
Ограничения telegram
"""

# Скорость отправки сообщений
# https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
MAX_MESSAGES_PER_SECOND = 30
MAX_MESSAGES_PER_USER_PER_SECOND = 2
MAX_MESSAGES_PER_GROUP_PER_SECOND = 20 / 60  # 20 в мин

# Обложка видео
# https://core.telegram.org/bots/api#sendvideo
TELEGRAM_VIDEO_THUMBNAIL_FORMAT = "jpg"
TELEGRAM_VIDEO_THUMBNAIL_MAX_SIDE = 2000  # px, хотя в документации написано про лимит в 320px
TELEGRAM_VIDEO_THUMBNAIL_MAX_SIZE = 200 * 2**10  # 200 kb

# Платежи
# https://core.telegram.org/bots/api#payments
INVOICE_TITLE_MAX_LENGTH = 32
INVOICE_DESCRIPTION_MAX_LENGTH = 255
INVOICE_PAYLOAD_MAX_SIZE_BYTES = 128
