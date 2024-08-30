"""
Модифицированные библиотечные классы
"""

from sqlalchemy_utils import PhoneNumber as _PhoneNumber


class PhoneNumber(_PhoneNumber):
    """
    Хранит номер в формате E164 в базе данных
    """

    def __composite_values__(self):
        return self.e164, self.region
