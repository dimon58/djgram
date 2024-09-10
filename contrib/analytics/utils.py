from aiogram import Bot

try:
    # noinspection PyUnresolvedReferences
    from aiogram.client.default import Default

    def set_defaults(data: dict, bot: Bot) -> dict:
        """
        Устанавливает все значения defaults в данных
        """

        for key, value in data.items():
            if isinstance(value, Default):
                data[key] = bot.default[value.name]

            elif isinstance(value, dict):
                data[key] = set_defaults(value, bot)

        return data

except ImportError:
    # Старые версии aiogram

    def set_defaults(data: dict, bot: Bot) -> dict:
        return data
