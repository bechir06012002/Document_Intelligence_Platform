from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.pipeline.classify import DocumentClassification
    from app.pipeline.classify_gl import GLSuggestion
    from app.pipeline.validate import ValidationResult
    from app.schemas.invoice import InvoiceFields
    from app.schemas.receipt import ReceiptFields


@dataclass(frozen=True)
class DocumentContext:
    file_path: Path
    text: str | None = None
    classification: DocumentClassification | None = None
    fields: InvoiceFields | ReceiptFields | None = None
    validation: ValidationResult | None = None
    gl_classification: GLSuggestion | None = None

    def evolve(self, **changes: Any) -> DocumentContext:
        return replace(self, **changes)
