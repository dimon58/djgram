import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

import phonenumbers
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram_dialog import DialogManager, DialogProtocol
from aiogram_dialog.widgets.input import MessageInput

from djgram.contrib.analytics import dialog_analytics

from .validators import (
    DnsResolver,
    EmailValidator,
    FormInputValidationCallback,
    FormInputValidator,
    PhoneNumberValidator,
)


class FormInput(MessageInput, ABC):
    """
    Базовый класс поля ввода

    Основан на MessageInput из aiogram-dialog

    При пользовательском вводе валидирует данные и, если всё корректно, сохраняет в dialog_data в поле key
    """

    def __init__(  # noqa: D107
        self,
        key: str,
        on_validation_success: FormInputValidationCallback | None = None,
        on_validation_failure: FormInputValidationCallback | None = None,
        validators: Sequence[FormInputValidator] | None = None,
        content_types: Sequence[str] | str = ContentType.ANY,
        filter: Callable[..., Any] | None = None,  # noqa: A002
    ):
        super().__init__(
            func=self.form_input_func,
            content_types=content_types,
            filter=filter,
        )
        self.key = key
        self.on_validation_success = on_validation_success
        self.on_validation_failure = on_validation_failure

        if validators is None:
            validators = []

        for validator in validators:
            if not validator.check_support(self):
                raise ValueError(f"Validator {validator.__class__} does not support {self.__class__}")

        self.validators = validators

    @staticmethod
    async def form_input_func(message: Message, form_input: "FormInput", manager: DialogManager) -> None:
        manager.dialog_data[form_input.key] = form_input.get_input_data(message)

    async def process_message(
        self,
        message: Message,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        for handler_filter in self.filters:
            if not await handler_filter.call(
                manager.event,
                **manager.middleware_data,
            ):
                # Обязательно нужно обращаться через имя модуля,
                # чтобы получать актуальное значение DIALOG_ANALYTICS_ENABLED
                if dialog_analytics.DIALOG_ANALYTICS_ENABLED:
                    await dialog_analytics.save_input_statistics(
                        processor="form_input_process_message",
                        processed=False,
                        process_time=None,
                        not_processed_reason="filtered",
                        input_=self,
                        message=message,
                        dialog=dialog,
                        manager=manager,
                    )

                return False

        data = self.get_input_data(message)
        for validator in self.validators:
            is_valid, data = await validator.validate(data, message, self, manager)
            if not is_valid:
                if self.on_validation_failure is not None:
                    await self.on_validation_failure(message, self, manager)

                if dialog_analytics.DIALOG_ANALYTICS_ENABLED:
                    await dialog_analytics.save_input_statistics(
                        processor="form_input_process_message",
                        processed=False,
                        process_time=None,
                        not_processed_reason="skip_due_validation",
                        input_=self,
                        message=message,
                        dialog=dialog,
                        manager=manager,
                    )

                return True

        start = time.perf_counter()
        await self.func.process_event(message, self, manager)
        if self.on_validation_success is not None:
            await self.on_validation_success(message, self, manager)
        end = time.perf_counter()

        await dialog_analytics.save_input_statistics(
            processor="form_input_process_message",
            processed=True,
            process_time=end - start,
            input_=self,
            message=message,
            dialog=dialog,
            manager=manager,
        )

        return True

    @abstractmethod
    def get_input_data(self, message: Message) -> Any:
        raise NotImplementedError


class TextFormInput(FormInput):
    """
    Поле ввода текста
    """

    def __init__(  # noqa: D107
        self,
        key: str,
        on_validation_success: FormInputValidationCallback | None = None,
        on_validation_failure: FormInputValidationCallback | None = None,
        validators: Sequence[FormInputValidator] | None = None,
        filter: Callable[..., Any] | None = None,  # noqa: A002
    ):
        super().__init__(
            key=key,
            on_validation_success=on_validation_success,
            on_validation_failure=on_validation_failure,
            validators=validators,
            content_types=ContentType.TEXT,
            filter=filter,
        )

    def get_input_data(self, message: Message) -> Any:
        return message.text


class EmailFormInput(TextFormInput):
    """
    Поле ввода электронной почты

    Проверяет её корректность с помощью библиотеки email_validator

    https://github.com/JoshData/python-email-validator
    """

    def __init__(
        self,
        key: str,
        on_validation_success: FormInputValidationCallback | None = None,
        on_validation_failure: FormInputValidationCallback | None = None,
        validators: Sequence[FormInputValidator] | None = None,
        filter: Callable[..., Any] | None = None,  # noqa: A002
        /,  # prior arguments are positional-only
        *,  # subsequent arguments are keyword-only
        allow_smtputf8: bool | None = None,
        allow_empty_local: bool = False,
        allow_quoted_local: bool | None = None,
        allow_domain_literal: bool | None = None,
        allow_display_name: bool | None = None,
        check_deliverability: bool | None = None,
        test_environment: bool | None = None,
        globally_deliverable: bool | None = None,
        timeout: int | None = None,
        dns_resolver: DnsResolver | None = None,
    ):
        """
        Все параметры после /* передаются в функцию validate_email из библиотеки email_validator

        https://github.com/JoshData/python-email-validator?tab=readme-ov-file#options
        """
        if validators is None:
            validators = []

        super().__init__(
            key=key,
            on_validation_success=on_validation_success,
            on_validation_failure=on_validation_failure,
            validators=[
                EmailValidator(
                    allow_smtputf8=allow_smtputf8,
                    allow_empty_local=allow_empty_local,
                    allow_quoted_local=allow_quoted_local,
                    allow_domain_literal=allow_domain_literal,
                    allow_display_name=allow_display_name,
                    check_deliverability=check_deliverability,
                    test_environment=test_environment,
                    globally_deliverable=globally_deliverable,
                    timeout=timeout,
                    dns_resolver=dns_resolver,
                ),
                *validators,
            ],
            filter=filter,
        )


class PhoneNumberFormInput(TextFormInput):
    """
    Поле ввода номера телефона

    Проверяет её корректность с помощью библиотеки phonenumbers

    https://github.com/daviddrysdale/python-phonenumbers
    """

    def __init__(
        self,
        key: str,
        on_validation_success: FormInputValidationCallback | None = None,
        on_validation_failure: FormInputValidationCallback | None = None,
        validators: Sequence[FormInputValidator] | None = None,
        filter: Callable[..., Any] | None = None,  # noqa: A002
        default_region: str | None = None,
        check_region: bool = True,
        output_number_format: int = phonenumbers.PhoneNumberFormat.E164,
    ):
        """
        :param default_region: Регион номера по умолчанию. Полезен, когда номер не записан в международном формате.
        :param check_region: Проверять корректность региона номера
        :param output_number_format: Формат номера на выходе:
                E164: +771234567890
                INTERNATIONAL: +7 71234567890
                NATIONAL: 71234567890
                RFC3966: tel:+7-71234567890
        """
        if validators is None:
            validators = []

        super().__init__(
            key=key,
            on_validation_success=on_validation_success,
            on_validation_failure=on_validation_failure,
            validators=[
                PhoneNumberValidator(
                    default_region=default_region,
                    check_region=check_region,
                    output_number_format=output_number_format,
                ),
                *validators,
            ],
            filter=filter,
        )
