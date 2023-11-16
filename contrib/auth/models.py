from .user_model_base import AbstractUser

try:
    from user_model import USER_MODEL

    User: type[AbstractUser] = USER_MODEL
except ImportError:

    class User(AbstractUser):
        ...
