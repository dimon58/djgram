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
        os.makedirs(app_dir)

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

                with open(output_file, "w", encoding="utf8") as output_file_io:
                    template.stream(app_name=name).dump(output_file_io)

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
def init(type: str):
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
        clickhouse_scripts = os.path.join(app_dir, "docker", "clickhouse")  # noqa: PTH118
        os.makedirs(clickhouse_scripts, exist_ok=True)
        djgram_path = Path(__file__).resolve().parent
        sqls = djgram_path / "contrib" / "analytics" / "sql"
        for file in os.listdir(sqls):
            file_path = sqls / file
            if file_path.is_file():
                shutil.copy(file_path, clickhouse_scripts)
    else:
        click.echo("Not supported initialization type", err=True)

    # Переименовываем example.env -> .env
    try:
        os.rename(  # noqa: PTH104
            os.path.join(app_dir, "example.env"),  # noqa: PTH118
            os.path.join(app_dir, ".env"),  # noqa: PTH118
        )
    except FileExistsError:
        click.echo("\033[33mFile .env already exists. Created example.env\033[0m")

    click.echo("\033[32mdjgram initialized\033[0m")
    click.echo("\033[35mRead generated readme.md file for further information\033[0m")


if __name__ == "__main__":
    cli()
