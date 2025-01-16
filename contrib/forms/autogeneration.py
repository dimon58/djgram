from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from aiogram.fsm.state import State
from aiogram.types import UNSET_PARSE_MODE
from aiogram.types.base import UNSET_DISABLE_WEB_PAGE_PREVIEW
from aiogram_dialog import Dialog, Window
from aiogram_dialog.api.internal.widgets import MarkupFactory
from aiogram_dialog.dialog import OnResultEvent
from aiogram_dialog.widgets.kbd import Back, Cancel, Keyboard
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.utils import GetterVariant
from aiogram_dialog.window import _DEFAULT_MARKUP_FACTORY

from djgram.contrib.forms.actions import switch_to
from djgram.contrib.forms.inputs import FormInput, TextFormInput
from djgram.contrib.forms.validators import FormInputValidationCallback

T = TypeVar("T", bound=FormInput)


@dataclass
class FormWindowBuilder:
    """
    Сборщик окна, соответствующего элементу формы
    """

    key: Hashable | Sequence[Hashable]
    input_class: type[FormInput]
    input_kwargs: dict[str, Any]
    text: str

    state: State
    getter: GetterVariant = None
    on_process_result: OnResultEvent | None = None
    markup_factory: MarkupFactory = _DEFAULT_MARKUP_FACTORY
    parse_mode: str | None = UNSET_PARSE_MODE
    disable_web_page_preview: bool | None = UNSET_DISABLE_WEB_PAGE_PREVIEW
    preview_add_transitions: list[Keyboard] | None = None
    preview_data: GetterVariant = None

    def build(
        self,
        back_text: str,
        on_validation_success: FormInputValidationCallback,
        *,
        first_window: bool,
    ) -> Window:
        return Window(
            Const(self.text),
            self.input_class(self.key, on_validation_success, **self.input_kwargs),
            Cancel(Const(back_text)) if first_window else Back(Const(back_text)),
            state=self.state,
            getter=self.getter,
            on_process_result=self.on_process_result,
            markup_factory=self.markup_factory,
            parse_mode=self.parse_mode,
            disable_web_page_preview=self.disable_web_page_preview,
            preview_add_transitions=self.preview_add_transitions,
            preview_data=self.preview_data,
        )


def form_element(
    key: str,
    text: str,
    state: State,
    input_class: type[FormInput] = TextFormInput,
    **input_kwargs,
) -> FormWindowBuilder:
    """
    Создаёт элемент формы
    """

    return FormWindowBuilder(
        key=key,
        text=text,
        input_class=input_class,
        input_kwargs=input_kwargs,
        state=state,
    )


class LinearFormDialog(Dialog):
    """
    Последовательная форма
    """

    def __init__(
        self,
        key: Hashable | Sequence[Hashable],
        back_text: str,
        on_validation_success: FormInputValidationCallback,
        elements: Sequence[FormWindowBuilder],
    ):
        """
        Args:
            key: ключ, по которому данные сохраняются в dialog data
            back_text: текст на кнопках назад
            on_validation_success: колбек, вызываемый при завершении заполнении формы
            elements: элементы формы
        """

        self.key = key

        widgets = (
            elements[idx].build(
                back_text,
                first_window=idx == 0,
                on_validation_success=switch_to(elements[idx + 1].state),
            )
            for idx in range(len(elements) - 1)
        )

        super().__init__(
            *widgets,
            elements[-1].build(
                back_text=back_text,
                on_validation_success=on_validation_success,
                first_window=len(elements) == 1,
            ),
        )
