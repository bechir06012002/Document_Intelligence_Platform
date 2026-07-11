from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel
from stdnum.eu import vat as eu_vat

from app.schemas.invoice import InvoiceFields
from app.schemas.receipt import ReceiptFields

DELTA_CUSTOMER_NAME = "Delta Facilities B.V."
DELTA_CUSTOMER_VAT_ID = "NL00449544B01"

TOTAL_RECONCILIATION_TOLERANCE = Decimal("0.01")
MIN_EXTRACTION_CONFIDENCE = 0.80

Severity = Literal["error", "warning"]


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Severity


class ValidationResult(BaseModel):
    issues: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


def _totals_reconcile(subtotal: Decimal, total_tax: Decimal, total: Decimal) -> bool:
    return abs((subtotal + total_tax) - total) <= TOTAL_RECONCILIATION_TOLERANCE


def _confidence_issue(confidence: float | None) -> ValidationIssue | None:
    if confidence is not None and confidence < MIN_EXTRACTION_CONFIDENCE:
        return ValidationIssue(
            code="low_extraction_confidence",
            message=f"Primary extraction confidence {confidence:.2f} is below 0.80.",
            severity="warning",
        )
    return None


def validate_invoice(fields: InvoiceFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not fields.vendor_name:
        issues.append(
            ValidationIssue(
                code="vendor_name_required", message="Vendor name is missing.", severity="error"
            )
        )

    if fields.customer_name != DELTA_CUSTOMER_NAME:
        issues.append(
            ValidationIssue(
                code="customer_name_mismatch",
                message=f"Customer name does not match {DELTA_CUSTOMER_NAME}.",
                severity="error",
            )
        )

    if fields.vendor_vat_id is None:
        issues.append(
            ValidationIssue(
                code="vendor_vat_id_required",
                message="Vendor VAT ID is missing.",
                severity="error",
            )
        )
    elif not eu_vat.is_valid(fields.vendor_vat_id):
        issues.append(
            ValidationIssue(
                code="vendor_vat_id_invalid",
                message="Vendor VAT ID is not a valid EU VAT number.",
                severity="error",
            )
        )

    if fields.customer_vat_id != DELTA_CUSTOMER_VAT_ID:
        issues.append(
            ValidationIssue(
                code="customer_vat_id_mismatch",
                message=f"Customer VAT ID does not match {DELTA_CUSTOMER_VAT_ID}.",
                severity="error",
            )
        )

    if not fields.invoice_number:
        issues.append(
            ValidationIssue(
                code="invoice_number_required",
                message="Invoice number is missing.",
                severity="error",
            )
        )

    if fields.invoice_date is None:
        issues.append(
            ValidationIssue(
                code="invoice_date_required",
                message="Invoice date is missing.",
                severity="error",
            )
        )

    if not fields.currency:
        issues.append(
            ValidationIssue(
                code="currency_required", message="Currency is missing.", severity="error"
            )
        )

    if fields.invoice_total is None:
        issues.append(
            ValidationIssue(
                code="invoice_total_required",
                message="Invoice total is missing.",
                severity="error",
            )
        )
    elif fields.invoice_total <= 0:
        issues.append(
            ValidationIssue(
                code="invoice_total_not_positive",
                message="Invoice total must be positive.",
                severity="error",
            )
        )

    if (
        fields.invoice_date is not None
        and fields.due_date is not None
        and fields.due_date < fields.invoice_date
    ):
        issues.append(
            ValidationIssue(
                code="due_date_before_invoice_date",
                message="Due date is before the invoice date.",
                severity="error",
            )
        )

    if (
        fields.subtotal is not None
        and fields.total_tax is not None
        and fields.invoice_total is not None
        and not _totals_reconcile(fields.subtotal, fields.total_tax, fields.invoice_total)
    ):
        issues.append(
            ValidationIssue(
                code="invoice_total_mismatch",
                message="Subtotal plus tax does not reconcile with the invoice total.",
                severity="error",
            )
        )

    if fields.purchase_order is None:
        issues.append(
            ValidationIssue(
                code="purchase_order_missing",
                message="Purchase order is missing.",
                severity="warning",
            )
        )

    confidence_issue = _confidence_issue(fields.confidence)
    if confidence_issue is not None:
        issues.append(confidence_issue)

    return issues


def validate_receipt(fields: ReceiptFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not fields.merchant_name:
        issues.append(
            ValidationIssue(
                code="merchant_name_required",
                message="Merchant name is missing.",
                severity="error",
            )
        )

    if fields.transaction_date is None:
        issues.append(
            ValidationIssue(
                code="transaction_date_required",
                message="Transaction date is missing.",
                severity="error",
            )
        )

    if not fields.currency:
        issues.append(
            ValidationIssue(
                code="currency_required", message="Currency is missing.", severity="error"
            )
        )

    if fields.total is None:
        issues.append(
            ValidationIssue(
                code="total_required", message="Total is missing.", severity="error"
            )
        )
    elif fields.total <= 0:
        issues.append(
            ValidationIssue(
                code="total_not_positive", message="Total must be positive.", severity="error"
            )
        )

    if (
        fields.subtotal is not None
        and fields.total_tax is not None
        and fields.total is not None
        and not _totals_reconcile(fields.subtotal, fields.total_tax, fields.total)
    ):
        issues.append(
            ValidationIssue(
                code="total_mismatch",
                message="Subtotal plus VAT does not reconcile with the total.",
                severity="error",
            )
        )

    confidence_issue = _confidence_issue(fields.confidence)
    if confidence_issue is not None:
        issues.append(confidence_issue)

    return issues


def check_duplicate_invoice(is_duplicate: bool) -> ValidationIssue | None:
    if not is_duplicate:
        return None
    return ValidationIssue(
        code="duplicate_invoice",
        message="An invoice with the same vendor and invoice number already exists.",
        severity="error",
    )
