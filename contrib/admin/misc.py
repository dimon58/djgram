from typing import Any

from djgram.system_configs import MIDDLEWARE_AUTH_USER_KEY, MIDDLEWARE_TELEGRAM_USER_KEY


def get_admin_representation_for_logging(telegram_user, user) -> str:  # noqa: ANN001
    return (
        f"[id={user.id}] [telegram_id={telegram_user.id}, username={telegram_user.username}] {telegram_user.full_name}"
    )


def get_admin_representation_for_logging_from_middleware_data(middleware_data: dict[str, Any]) -> str:
    telegram_user = middleware_data[MIDDLEWARE_TELEGRAM_USER_KEY]
    user = middleware_data[MIDDLEWARE_AUTH_USER_KEY]

    return get_admin_representation_for_logging(telegram_user, user)
