def get_default_word_builder(
    word_0: str,
    word_1: str,
    word_234: str,
):
    def inner(number: int):
        """
        Ставит слово "чат" в нужное число в зависимости от number. Например:

        0 чатов
        1 чат
        2 чата
        3 чата
        4 чата
        5 чатов
        6 чатов
        7 чатов
        8 чатов
        9 чатов
        10 чатов
        11 чатов
        12 чатов
        13 чатов
        14 чатов
        15 чатов
        16 чатов
        17 чатов
        18 чатов
        19 чатов
        20 чатов
        21 чат
        ...
        """
        number %= 100
        if 5 <= number <= 20:
            return word_0

        number %= 10

        if number == 1:
            return word_1

        if 2 <= number <= 4:
            return word_234

        return word_0

    return inner
