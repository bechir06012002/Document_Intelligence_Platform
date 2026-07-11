from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential

from app.config import settings

CONTENT_TYPES_BY_SUFFIX: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class DocumentIntelligenceService:
    def __init__(self) -> None:
        self._client = DocumentIntelligenceClient(
            endpoint=settings.azure_document_intelligence_endpoint,
            credential=AzureKeyCredential(settings.azure_document_intelligence_key),
        )

    def analyze_invoice(self, file_path: Path) -> AnalyzeResult:
        return self._analyze("prebuilt-invoice", file_path)

    def analyze_receipt(self, file_path: Path) -> AnalyzeResult:
        return self._analyze("prebuilt-receipt", file_path)

    def _analyze(self, model_id: str, file_path: Path) -> AnalyzeResult:
        try:
            content_type = CONTENT_TYPES_BY_SUFFIX[file_path.suffix.lower()]
        except KeyError as exc:
            raise ValueError(f"Unsupported file type: {file_path.suffix}") from exc

        with file_path.open("rb") as f:
            poller = self._client.begin_analyze_document(
                model_id, body=f, content_type=content_type
            )
        return poller.result()
