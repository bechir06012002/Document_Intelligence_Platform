from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: Literal["error", "warning"]


@dataclass
class ValidationResult:
    issues: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ValidationResult:
        issues = [ValidationIssue(**issue) for issue in (data or {}).get("issues", [])]
        return cls(issues=issues)


@dataclass
class GlClassification:
    account: str
    rationale: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GlClassification | None:
        if data is None:
            return None
        return cls(account=data["account"], rationale=data["rationale"])


@dataclass
class DocumentSummary:
    id: int
    original_filename: str
    status: str
    document_type: str | None
    vendor_or_merchant_name: str | None
    total: str | None
    currency: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentSummary:
        return cls(
            id=data["id"],
            original_filename=data["original_filename"],
            status=data["status"],
            document_type=data.get("document_type"),
            vendor_or_merchant_name=data.get("vendor_or_merchant_name"),
            total=data.get("total"),
            currency=data.get("currency"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class DocumentDetail:
    id: int
    original_filename: str
    content_type: str
    status: str
    document_type: str | None
    fields: dict[str, Any] | None
    validation: ValidationResult
    gl_classification: GlClassification | None
    field_sources: dict[str, str]
    selected_gl_account_code: str | None
    gl_overridden: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentDetail:
        classification = data.get("classification") or {}
        return cls(
            id=data["id"],
            original_filename=data["original_filename"],
            content_type=data["content_type"],
            status=data["status"],
            document_type=classification.get("document_type"),
            fields=data.get("fields"),
            validation=ValidationResult.from_dict(data.get("validation")),
            gl_classification=GlClassification.from_dict(data.get("gl_classification")),
            field_sources=data.get("field_sources") or {},
            selected_gl_account_code=data.get("selected_gl_account_code"),
            gl_overridden=data.get("gl_overridden", False),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class CorrectionEmailDraft:
    subject: str
    body: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrectionEmailDraft:
        return cls(subject=data["subject"], body=data["body"])
