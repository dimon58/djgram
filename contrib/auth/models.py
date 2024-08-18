from .user_model_base import AbstractUser

try:
    from user_model import User  # pyright: ignore [reportMissingImports]

except ImportError:

    class User(AbstractUser): ...

else:

    if not issubclass(User, AbstractUser):
        raise TypeError(f"{User} should be a subclass of {AbstractUser}")
