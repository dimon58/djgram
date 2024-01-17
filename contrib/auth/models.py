from .user_model_base import AbstractUser

try:
    from user_model import USER_MODEL  # pyright: ignore [reportMissingImports]

    User: type[AbstractUser] = USER_MODEL  # pyright: ignore [reportGeneralTypeIssues]
except ImportError:

    class User(AbstractUser):
        ...
