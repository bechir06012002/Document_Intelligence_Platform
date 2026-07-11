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


class InvoiceLineItem(BaseModel):
    description: str | None
    quantity: float | None
    unit_price: Decimal | None
    amount: Decimal | None

    @classmethod
    def from_document_fields(cls, fields: dict[str, DocumentField]) -> InvoiceLineItem:
        return cls(
            description=get_string(fields, "Description"),
            quantity=get_number(fields, "Quantity"),
            unit_price=get_amount(fields, "UnitPrice"),
            amount=get_amount(fields, "Amount"),
        )


class InvoiceFields(BaseModel):
    vendor_name: str | None
    vendor_vat_id: str | None
    customer_name: str | None
    customer_vat_id: str | None
    invoice_number: str | None
    purchase_order: str | None
    invoice_date: date | None
    due_date: date | None
    currency: str | None
    subtotal: Decimal | None
    total_tax: Decimal | None
    invoice_total: Decimal | None
    line_items: list[InvoiceLineItem]
    confidence: float | None = None

    @classmethod
    def from_document_fields(
        cls, fields: dict[str, DocumentField], confidence: float | None = None
    ) -> InvoiceFields:
        return cls(
            vendor_name=get_string(fields, "VendorName"),
            vendor_vat_id=get_string(fields, "VendorTaxId"),
            customer_name=get_string(fields, "CustomerName"),
            customer_vat_id=get_string(fields, "CustomerTaxId"),
            invoice_number=get_string(fields, "InvoiceId"),
            purchase_order=get_string(fields, "PurchaseOrder"),
            invoice_date=get_date(fields, "InvoiceDate"),
            due_date=get_date(fields, "DueDate"),
            currency=(
                get_currency_code(fields, "InvoiceTotal") or get_currency_code(fields, "SubTotal")
            ),
            subtotal=get_amount(fields, "SubTotal"),
            total_tax=get_amount(fields, "TotalTax"),
            invoice_total=get_amount(fields, "InvoiceTotal"),
            line_items=[InvoiceLineItem.from_document_fields(item) for item in get_items(fields)],
            confidence=confidence,
        )
