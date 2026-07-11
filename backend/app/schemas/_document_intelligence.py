from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from azure.ai.documentintelligence.models import DocumentField


def get_string(fields: dict[str, DocumentField], name: str) -> str | None:
    field = fields.get(name)
    return field.value_string if field is not None else None


def get_date(fields: dict[str, DocumentField], name: str) -> date | None:
    field = fields.get(name)
    return field.value_date if field is not None else None


def get_number(fields: dict[str, DocumentField], name: str) -> float | None:
    field = fields.get(name)
    return field.value_number if field is not None else None


def get_amount(fields: dict[str, DocumentField], name: str) -> Decimal | None:
    field = fields.get(name)
    if field is None or field.value_currency is None:
        return None
    return Decimal(str(field.value_currency.amount))


def get_currency_code(fields: dict[str, DocumentField], name: str) -> str | None:
    field = fields.get(name)
    if field is None or field.value_currency is None:
        return None
    return field.value_currency.currency_code


def get_items(
    fields: dict[str, DocumentField], name: str = "Items"
) -> list[dict[str, DocumentField]]:
    field = fields.get(name)
    if field is None or field.value_array is None:
        return []
    return [item.value_object or {} for item in field.value_array]
