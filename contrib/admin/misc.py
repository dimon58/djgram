from typing import Any


def get_admin_representation_for_logging(telegram_user, user) -> str:  # noqa: ANN001
    return (
        f"[id={user.id}] [telegram_id={telegram_user.id}, username={telegram_user.username}] {telegram_user.full_name}"
    )


def get_admin_representation_for_logging_from_middleware_data(middleware_data: dict[str, Any]) -> str:

    # TODO: починить круговой импорт и вынести на верхний уровень
    from djgram.contrib.auth.middlewares import MIDDLEWARE_USER_KEY
    from djgram.contrib.telegram.middlewares import MIDDLEWARE_TELEGRAM_USER_KEY

    telegram_user = middleware_data[MIDDLEWARE_TELEGRAM_USER_KEY]
    user = middleware_data[MIDDLEWARE_USER_KEY]

    return get_admin_representation_for_logging(telegram_user, user)
