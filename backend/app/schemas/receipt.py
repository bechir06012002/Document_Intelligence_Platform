from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.schemas._document_intelligence import (
    get_amount,
    get_currency_code,
    get_date,
    get_items,
    get_number,
    get_string,
)

if TYPE_CHECKING:
    from azure.ai.documentintelligence.models import DocumentField


class ReceiptLineItem(BaseModel):
    description: str | None
    quantity: float | None
    unit_price: Decimal | None
    amount: Decimal | None

    @classmethod
    def from_document_fields(cls, fields: dict[str, DocumentField]) -> ReceiptLineItem:
        return cls(
            description=get_string(fields, "Description"),
            quantity=get_number(fields, "Quantity"),
            unit_price=get_amount(fields, "Price"),
            amount=get_amount(fields, "TotalPrice"),
        )


class ReceiptFields(BaseModel):
    merchant_name: str | None
    transaction_date: date | None
    currency: str | None
    subtotal: Decimal | None
    total_tax: Decimal | None
    total: Decimal | None
    line_items: list[ReceiptLineItem]
    confidence: float | None = None

    @classmethod
    def from_document_fields(
        cls, fields: dict[str, DocumentField], confidence: float | None = None
    ) -> ReceiptFields:
        return cls(
            merchant_name=get_string(fields, "MerchantName"),
            transaction_date=get_date(fields, "TransactionDate"),
            currency=get_currency_code(fields, "Total") or get_currency_code(fields, "Subtotal"),
            subtotal=get_amount(fields, "Subtotal"),
            total_tax=get_amount(fields, "TotalTax"),
            total=get_amount(fields, "Total"),
            line_items=[ReceiptLineItem.from_document_fields(item) for item in get_items(fields)],
            confidence=confidence,
        )
