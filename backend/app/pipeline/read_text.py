from __future__ import annotations

from app.pipeline.context import DocumentContext
from app.services.document_intelligence_service import DocumentIntelligenceService


class ReadTextStep:
    def __init__(self, service: DocumentIntelligenceService | None = None) -> None:
        self._service = service or DocumentIntelligenceService()

    def run(self, context: DocumentContext) -> DocumentContext:
        result = self._service.analyze_invoice(context.file_path)
        return context.evolve(text=result.content)
