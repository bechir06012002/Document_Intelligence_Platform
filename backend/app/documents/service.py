from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.accounting.catalog import validate_gl_account_code
from app.documents.database import UPLOADS_DIR
from app.documents.models import Document
from app.documents.repository import DocumentRepository, normalize_key
from app.pipeline.classify import ClassificationStep
from app.pipeline.classify_gl import GLClassificationStep
from app.pipeline.context import DocumentContext
from app.pipeline.extract import ExtractionStep
from app.pipeline.pipeline import Pipeline
from app.pipeline.read_text import ReadTextStep
from app.pipeline.validate import (
    ValidationIssue,
    ValidationResult,
    check_duplicate_invoice,
    validate_invoice,
    validate_receipt,
)
from app.schemas.invoice import InvoiceFields
from app.schemas.receipt import ReceiptFields

Decision = Literal["approve", "reject"]

_PIPELINE = Pipeline(
    [ReadTextStep(), ClassificationStep(), ExtractionStep(), GLClassificationStep()]
)


class DocumentNotFoundError(Exception):
    def __init__(self, document_id: int) -> None:
        self.document_id = document_id
        super().__init__(f"Document {document_id} not found.")


class DocumentLockedError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Document is already {status} and can no longer be changed.")


class ApprovalBlockedError(Exception):
    pass


class DocumentService:
    def __init__(self, session: Session) -> None:
        self._repo = DocumentRepository(session)

    def get(self, document_id: int) -> Document:
        document = self._repo.get(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        return document

    def list_all(self) -> list[Document]:
        return self._repo.list_all()

    def create(self, original_filename: str, content_type: str, content: bytes) -> Document:
        suffix = Path(original_filename).suffix
        stored_filename = f"{uuid.uuid4().hex}{suffix}"
        file_path = UPLOADS_DIR / stored_filename
        file_path.write_bytes(content)

        document = Document(
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            status="processing",
        )
        document = self._repo.add(document)

        try:
            context = _PIPELINE.run(DocumentContext(file_path=file_path))
        except Exception:
            document.status = "failed"
            self._repo.update(document)
            raise

        self._apply_extraction(document, context)
        document.status = "needs_review"
        return self._repo.update(document)

    def correct(self, document_id: int, updates: dict[str, Any]) -> Document:
        document = self.get(document_id)
        self._ensure_editable(document)

        document_type = (document.classification or {}).get("document_type")
        merged = {**(document.fields or {}), **updates}

        if document_type == "invoice":
            invoice_fields = InvoiceFields.model_validate(merged)
            issues = validate_invoice(invoice_fields)
            issues.extend(self._duplicate_issue(invoice_fields, document.id))
            document.normalized_vendor_name = (
                normalize_key(invoice_fields.vendor_name) if invoice_fields.vendor_name else None
            )
            document.normalized_invoice_number = (
                normalize_key(invoice_fields.invoice_number)
                if invoice_fields.invoice_number
                else None
            )
            fields: InvoiceFields | ReceiptFields = invoice_fields
        else:
            receipt_fields = ReceiptFields.model_validate(merged)
            issues = validate_receipt(receipt_fields)
            fields = receipt_fields

        field_sources = dict(document.field_sources or {})
        for key in updates:
            field_sources[key] = "human"

        document.fields = fields.model_dump(mode="json")
        document.field_sources = field_sources
        document.validation = ValidationResult(issues=issues).model_dump(mode="json")
        return self._repo.update(document)

    def select_gl_account(self, document_id: int, code: str) -> Document:
        document = self.get(document_id)
        self._ensure_editable(document)
        validate_gl_account_code(code)

        suggested_code = None
        if document.gl_classification:
            suggested_code = document.gl_classification.get("account")

        document.selected_gl_account_code = code
        document.gl_overridden = suggested_code is not None and code != suggested_code
        return self._repo.update(document)

    def decide(self, document_id: int, decision: Decision) -> Document:
        document = self.get(document_id)
        self._ensure_editable(document)

        if decision == "approve":
            validation = ValidationResult.model_validate(document.validation or {"issues": []})
            if not validation.is_valid:
                raise ApprovalBlockedError("Open validation errors must be resolved first.")
            if not document.selected_gl_account_code:
                raise ApprovalBlockedError("A GL account must be selected before approval.")
            document.status = "approved"
        else:
            document.status = "rejected"

        return self._repo.update(document)

    def delete(self, document_id: int) -> None:
        document = self.get(document_id)
        file_path = UPLOADS_DIR / document.stored_filename
        self._repo.delete(document)
        file_path.unlink(missing_ok=True)

    def _ensure_editable(self, document: Document) -> None:
        if document.status in ("approved", "rejected"):
            raise DocumentLockedError(document.status)

    def _duplicate_issue(
        self, fields: InvoiceFields, exclude_id: int
    ) -> list[ValidationIssue]:
        if not fields.vendor_name or not fields.invoice_number:
            return []
        duplicate = self._repo.find_duplicate(
            fields.vendor_name, fields.invoice_number, exclude_id=exclude_id
        )
        issue = check_duplicate_invoice(duplicate is not None)
        return [issue] if issue is not None else []

    def _apply_extraction(self, document: Document, context: DocumentContext) -> None:
        fields = context.fields

        if isinstance(fields, InvoiceFields):
            issues = validate_invoice(fields)
            issues.extend(self._duplicate_issue(fields, document.id))
            document.normalized_vendor_name = (
                normalize_key(fields.vendor_name) if fields.vendor_name else None
            )
            document.normalized_invoice_number = (
                normalize_key(fields.invoice_number) if fields.invoice_number else None
            )
        else:
            issues = validate_receipt(fields)

        document.classification = context.classification.model_dump(mode="json")
        document.fields = fields.model_dump(mode="json")
        document.validation = ValidationResult(issues=issues).model_dump(mode="json")
        document.gl_classification = (
            context.gl_classification.model_dump(mode="json")
            if context.gl_classification is not None
            else None
        )
