def get_admin_representation_for_logging(telegram_user, user) -> str:  # noqa: ANN001
    return (
        f"[id={user.id}] [telegram_id={telegram_user.id}, username={telegram_user.username}] {telegram_user.full_name}"
    )
