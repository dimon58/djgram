#### Переопределение настроек

В корне проекта нужно создать файл `configs.py`,
в котором можно переопределить все настройки из модуля `djgram/configs.py`


#### Переопределение пользователя

Для переопределения стандартного пользователя нужно создать файл `user_model.py` в корне проекта,
в котором должен быть класс наследник `AbstractUser` записанный в переменную `USER_MODEL`.

Можно сделать просто ссылку

```python
from path.to.user.model import User

USER_MODEL = User
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