import os
import shutil
import sys
from pathlib import Path

import click
import jinja2

BASE_DIR = Path(__file__).resolve().parent
APP_TEMPLATE_DIR = BASE_DIR / "app_template" / "app"


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
        click.echo(f"Приложение {name} уже существует", err=True)
        sys.exit()
    else:
        os.mkdir(app_dir)  # noqa: PTH102

    environment = jinja2.Environment(  # nosec # noqa: S701
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

    click.echo(f"Создано приложение {name}")


if __name__ == "__main__":
    cli()
