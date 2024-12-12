from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Generic, TypeAlias, TypeVar

import phonenumbers
from aiogram.types import Message
from aiogram_dialog import DialogManager
from email_validator import EmailNotValidError, validate_email
from phonenumbers import NumberParseException

if TYPE_CHECKING:
    # noinspection PyPackageRequirements
    import dns.resolver

    from .inputs import FormInput

    DnsResolver = dns.resolver.Resolver

else:
    DnsResolver = object

T = TypeVar("T")

FormInputValidationCallback: TypeAlias = Callable[[Message, "FormInput", DialogManager], Awaitable[None]]


class FormInputValidator(ABC, Generic[T]):
    # noinspection PyMethodMayBeStatic
    def check_support(self, form_input: "FormInput") -> bool:
        return True

    @abstractmethod
    async def validate(
        self,
        data: T,
        message: Message,
        form_input: "FormInput",
        manager: DialogManager,
    ) -> tuple[bool, T | None]:
        raise NotImplementedError


class EmailValidator(FormInputValidator[str]):
    def __init__(
        self,
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
        Все параметры передаются в функцию validate_email из библиотеки email_validator

        https://github.com/JoshData/python-email-validator
        """
        self.allow_smtputf8 = allow_smtputf8
        self.allow_empty_local = allow_empty_local
        self.allow_quoted_local = allow_quoted_local
        self.allow_domain_literal = allow_domain_literal
        self.allow_display_name = allow_display_name
        self.check_deliverability = check_deliverability
        self.test_environment = test_environment
        self.globally_deliverable = globally_deliverable
        self.timeout = timeout
        self.dns_resolver = dns_resolver

    async def validate(
        self,
        data: str,
        message: Message,
        form_input: "FormInput",
        manager: DialogManager,
    ) -> tuple[bool, str | None]:
        try:
            emailinfo = validate_email(
                data,
                allow_smtputf8=self.allow_smtputf8,
                allow_empty_local=self.allow_empty_local,
                allow_quoted_local=self.allow_quoted_local,
                allow_domain_literal=self.allow_domain_literal,
                allow_display_name=self.allow_display_name,
                check_deliverability=self.check_deliverability,
                test_environment=self.test_environment,
                globally_deliverable=self.globally_deliverable,
                timeout=self.timeout,
                dns_resolver=self.dns_resolver,
            )

        except EmailNotValidError as exc:
            await message.answer(str(exc))
            return False, None

        else:
            return True, emailinfo.normalized


class PhoneNumberValidator(FormInputValidator[str]):
    def __init__(
        self,
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
        self.default_region = default_region
        self.check_region = check_region
        self.output_number_format = output_number_format

    async def validate(
        self,
        data: str,
        message: Message,
        form_input: "FormInput",
        manager: DialogManager,
    ) -> tuple[bool, str | None]:
        try:
            phone_number = phonenumbers.parse(
                data,
                region=self.default_region,
                _check_region=self.check_region,
            )
            return True, phonenumbers.format_number(phone_number, self.output_number_format)
        except NumberParseException as exc:
            await message.answer(str(exc))
            return False, None
