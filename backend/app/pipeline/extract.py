from __future__ import annotations

from app.pipeline.context import DocumentContext
from app.schemas.invoice import InvoiceFields
from app.schemas.receipt import ReceiptFields
from app.services.document_intelligence_service import DocumentIntelligenceService


class ExtractionStep:
    def __init__(self, service: DocumentIntelligenceService | None = None) -> None:
        self._service = service or DocumentIntelligenceService()

    def run(self, context: DocumentContext) -> DocumentContext:
        document_type = context.classification.document_type

        if document_type == "invoice":
            result = self._service.analyze_invoice(context.file_path)
            document = result.documents[0]
            fields = InvoiceFields.from_document_fields(document.fields or {}, document.confidence)
        else:
            result = self._service.analyze_receipt(context.file_path)
            document = result.documents[0]
            fields = ReceiptFields.from_document_fields(document.fields or {}, document.confidence)

        return context.evolve(fields=fields)
