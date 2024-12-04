"""
Функции для постобработки результатов рендеринга jinja2.

В сообщениях телеграм поддерживается только малая часть тегов html

Далее цитата из документации:

<b>bold</b>, <strong>bold</strong>
<i>italic</i>, <em>italic</em>
<u>underline</u>, <ins>underline</ins>
<s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
<span class="tg-spoiler">spoiler</span>, <tg-spoiler>spoiler</tg-spoiler>
<b>bold <i>italic bold <s>italic bold strikethrough <span class="tg-spoiler">italic bold strikethrough spoiler
</span></s> <u>underline italic bold</u></i> bold</b>
<a href="http://www.example.com/">inline URL</a>
<a href="tg://user?id=123456789">inline mention of a user</a>
<code>inline fixed-width code</code>
<pre>pre-formatted fixed-width code block</pre>
<pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language
</code></pre>

Подробнее https://core.telegram.org/bots/api#html-style
"""


def telegramify(html: str, collapse_spaces: bool = True) -> str:
    """
    Костыльный метод добавляющий поддержку тега <br> в сообщения телеграмм.

    Должен вызваться после рендеринга шаблона с помощью jinja2

    Схлопывает все пробельные символы (если collapse_spaces=True),
    заменяет теги <br> на перенос строки,
    убирает лишние пробельные символы на концах получившихся строк,
    """
    # Схлопываем все пробельные символы в один пробел
    if collapse_spaces:
        html = " ".join(html.split())
    # Удаляем теги <p></p>, которые генерирует ckeditor
    html = html.replace("&nbsp;", "").replace("<p>", "").replace("</p>", "\n")
    # Превращает теги <br> в перенос строки
    html = html.replace("<br>", "\n")
    # На концах получившихся строк убираем лишние пробельные символы
    return "\n".join(line.strip() for line in html.split("\n"))
