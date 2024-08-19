import os
import shutil
import sys
from pathlib import Path

import click
import jinja2

BASE_DIR = Path(__file__).resolve().parent
APP_TEMPLATE_DIR = BASE_DIR / "app_template" / "app"

INIT_TEMPLATE_DIR = BASE_DIR / "app_template" / "init"
INIT_COMMON_TEMPLATE_DIR = INIT_TEMPLATE_DIR / "common"
INIT_BASE_TEMPLATE_DIR = INIT_TEMPLATE_DIR / "base"
INIT_FULL_TEMPLATE_DIR = INIT_TEMPLATE_DIR / "full"


@click.group()
def cli():
    pass


@cli.command()
@click.argument("name")
def startapp(name: str):
    """
    Создаёт новое приложение
    """

    # путь до нового приложения
    app_dir = name

    if os.path.exists(app_dir):  # noqa: PTH110
        click.echo(f"\033[31mПриложение {name} уже существует\033[0m", err=True)
        sys.exit()
    else:
        os.makedirs(app_dir)  # noqa: PTH103

    environment = jinja2.Environment(  # nosec: B701 # noqa: S701
        loader=jinja2.FileSystemLoader(APP_TEMPLATE_DIR),
        keep_trailing_newline=True,
    )

    template_format = ".jinja2"

    # Копируем и рендерим все файлы
    for dir_, _, files in os.walk(APP_TEMPLATE_DIR):
        for file_name in files:
            original_file = os.path.join(dir_, file_name)  # noqa: PTH118
            relative_path = os.path.join(os.path.relpath(dir_, APP_TEMPLATE_DIR), file_name)  # noqa: PTH118

            # Jinja2 не понимает обратных слешей, поэтому переименовываем
            if relative_path.startswith(".\\"):
                relative_path = relative_path[2:]

            # Файлы с расширением ".jinja2" рендерим, а остальные просто копируем
            if file_name.endswith(template_format):
                template = environment.get_template(relative_path.replace("\\", "/"))

                # Переименовываем все файлы с расширением ".jinja2", удаляя ".jinja2" в конце
                output_file = Path(os.path.join(app_dir, relative_path[: -len(template_format)]))  # noqa: PTH118
                output_file.parent.mkdir(exist_ok=True, parents=True)

                template.stream(app_name=name).dump(output_file.as_posix())

            else:
                output_file = Path(os.path.join(app_dir, relative_path))  # noqa: PTH118
                output_file.parent.mkdir(exist_ok=True, parents=True)
                shutil.copy(original_file, output_file)

    click.echo(f"\033[32mСоздано приложение {name}\033[0m")


def render_folder(init_template_dir: str | os.PathLike, app_dir: str) -> None:
    for dir_, _, files in os.walk(init_template_dir):
        for file_name in files:
            original_file = os.path.join(dir_, file_name)  # noqa: PTH118
            relative_path = os.path.join(os.path.relpath(dir_, init_template_dir), file_name)  # noqa: PTH118

            output_file = Path(os.path.join(app_dir, relative_path))  # noqa: PTH118
            output_file.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(original_file, output_file)


@cli.command()
@click.argument("type", type=click.Choice(["base", "full"], case_sensitive=False), default="base")
def init(type: str):  # noqa: A002
    """
    Инициализация проекта

    base - использует базу данных sqlite, хранит состояния в оперативной памяти, нет сбора аналитики

    full - использует базу данных PostgreSql, хранит состояния в redis, есть сбор аналитики, работает через docker
    """

    app_dir = os.getcwd()  # noqa: PTH109

    # Копируем все файлы
    render_folder(INIT_COMMON_TEMPLATE_DIR, app_dir)

    if type == "base":
        render_folder(INIT_BASE_TEMPLATE_DIR, app_dir)
    elif type == "full":
        render_folder(INIT_FULL_TEMPLATE_DIR, app_dir)
    else:
        click.echo("Not supported initialization type", err=True)

    # Переименовываем example.env -> .env
    try:
        shutil.copy(
            os.path.join(app_dir, "example.env"),  # noqa: PTH118
            os.path.join(app_dir, ".env"),  # noqa: PTH118
        )
    except FileExistsError:
        click.echo("\033[33mFile .env already exists. Created example.env\033[0m")

    click.echo("\033[32mdjgram initialized\033[0m")
    click.echo("\033[35mRead generated readme.md file for further information\033[0m")


def compare_models(
        db_model: type,
        aiogram_model: type,
        db_unnecessary_skip: set[str] | None = None,
        db_missing_skip: set[str] | None = None,
) -> bool:
    """
    Сравнивает схему данных и схему в aiogram

    Если совпадает, то возвращает True, иначе False и выводит в консоль различия

    :param db_model: модель базы данных для сравнения
    :param aiogram_model: модель aiogram для сравнения
    :param db_unnecessary_skip: дополнительные поля, которые есть только в схеме базы данных
    :param db_missing_skip: поля, которые могут отсутствовать схеме в базе данных
    :return:
    """
    from sqlalchemy import inspect
    if db_unnecessary_skip is None:
        db_unnecessary_skip = set()
    if db_missing_skip is None:
        db_missing_skip = set()

    aiogram_fields = aiogram_model.model_fields
    db_fields = inspect(db_model).attrs.items()

    aiogram_field_names = set(aiogram_fields.keys())
    db_field_names = {field_name for field_name, _ in db_fields}

    if aiogram_field_names == db_field_names:
        return True

    db_unnecessary = db_field_names - aiogram_field_names - db_unnecessary_skip
    if len(db_unnecessary) > 0:
        click.echo(f"\033[33mDB schema for {db_model} has unnecessary columns: {db_unnecessary}\033[0m", err=True)

    db_missing = (aiogram_field_names - db_field_names) - db_missing_skip
    if len(db_missing) > 0:
        click.echo(f"\033[31mDB schema for {db_model} has missing columns: {db_missing}\033[0m", err=True)

    return False


@cli.command()
def sync_tg_models():
    """
    Сравнивает схему базы данных с моделями в aiogram
    """

    from aiogram import types

    from djgram.contrib.telegram import models

    compare_models(
        models.TelegramUser,
        types.User,
        db_unnecessary_skip={"created_at", "updated_at"},
        # Fields returned only in getrMe https://core.telegram.org/bots/api#getme
        # Described in djgram.db.models.user_additional_info.TelegramUserAdditionalInfo
        db_missing_skip={
            "can_join_groups",
            "can_read_all_group_messages",
            "supports_inline_queries",
            "can_connect_to_business",
            "has_main_web_app",
        },
    )
    compare_models(
        models.TelegramChat,
        types.Chat,
        db_unnecessary_skip={"created_at", "updated_at"},
        # This fields deprecated:: API:7.3
        # https://core.telegram.org/bots/api-changelog#may-6-2024"""
        db_missing_skip={
            "accent_color_id",
            "active_usernames",
            "available_reactions",
            "background_custom_emoji_id",
            "bio",
            "birthdate",
            "business_intro",
            "business_location",
            "business_opening_hours",
            "can_set_sticker_set",
            "custom_emoji_sticker_set_name",
            "description",
            "emoji_status_custom_emoji_id",
            "emoji_status_expiration_date",
            "has_aggressive_anti_spam_enabled",
            "has_hidden_members",
            "has_private_forwards",
            "has_protected_content",
            "has_restricted_voice_and_video_messages",
            "has_visible_history",
            "invite_link",
            "join_by_request",
            "join_to_send_messages",
            "linked_chat_id",
            "location",
            "message_auto_delete_time",
            "permissions",
            "personal_chat",
            "photo",
            "pinned_message",
            "profile_accent_color_id",
            "profile_background_custom_emoji_id",
            "slow_mode_delay",
            "sticker_set_name",
            "unrestrict_boost_count",
        },
    )
    compare_models(models.TelegramChatFullInfo, types.ChatFullInfo, db_unnecessary_skip={"created_at", "updated_at"})


if __name__ == "__main__":
    cli()
