from .user_model_base import AbstractUser

try:
    from user_model import USER_MODEL  # pyright: ignore [reportMissingImports]

except ImportError:

    class User(AbstractUser): ...

else:
    if not issubclass(USER_MODEL, AbstractUser):
        raise TypeError(f"{USER_MODEL} should be a subclass of {AbstractUser}")

    User: type[USER_MODEL] = USER_MODEL  # pyright: ignore [reportRedeclaration, reportAssignmentType]

User: type[User]  # pyright: ignore [reportInvalidTypeForm]
