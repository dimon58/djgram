"""
Ограничения telegram
"""

# Обложка видео
# https://core.telegram.org/bots/api#sendvideo
TELEGRAM_VIDEO_THUMBNAIL_FORMAT = "jpg"
TELEGRAM_VIDEO_THUMBNAIL_MAX_SIDE = 2000  # px, хотя в документации написано про лимит в 320px
TELEGRAM_VIDEO_THUMBNAIL_MAX_SIZE = 200 * 2**10  # 200 kb
