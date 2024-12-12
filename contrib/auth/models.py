from typing import TYPE_CHECKING

from .user_model_base import AbstractUser

if TYPE_CHECKING:

    class User(AbstractUser): ...

    import contextlib

    with contextlib.suppress(ImportError):
        # noinspection PyUnresolvedReferences
        from user_model import User  # pyright: ignore [reportMissingImports]

else:
    try:
        from user_model import User  # pyright: ignore [reportMissingImports]

    except ImportError:

        class User(AbstractUser): ...

    else:
        if not issubclass(User, AbstractUser):
            raise TypeError(f"{User} should be a subclass of {AbstractUser}")
