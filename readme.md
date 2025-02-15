#### Инициализация проекта

Пока предварительно нужно установить несколько библиотек
```shell
pip install click jinja2
```

```shell
python -m djgram init
```


#### Переопределение настроек

В корне проекта нужно создать файл `configs.py`,
в котором можно переопределить все настройки из модуля `djgram/configs.py`


#### Переопределение пользователя

Для переопределения стандартного пользователя нужно создать файл `user_model.py` в корне проекта,
в котором должен быть класс наследник `AbstractUser` с именем `User`.

Можно сделать просто ссылку

```python
from path.to.user.model import User
```

И в другом месте переопределить модель пользователя

```python
from sqlalchemy import Column
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import sqltypes

from djgram.contrib.auth.user_model_base import AbstractUser


class User(AbstractUser):
    bio: Mapped[str | None] = Column(
        sqltypes.String,
        nullable=True,
        doc="Биография пользователя",
    )
```
