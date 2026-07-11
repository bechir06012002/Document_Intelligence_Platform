from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.correction_email.eligibility import eligible_issues
from app.documents.database import get_session
from app.documents.models import Document
from app.documents.service import DocumentNotFoundError, DocumentService
from app.pipeline.validate import ValidationIssue, ValidationResult
from app.services.azure_openai_service import AzureOpenAIService

router = APIRouter(prefix="/documents", tags=["correction-email"])

_azure_openai_service = AzureOpenAIService()


class CorrectionEmailDraft(BaseModel):
    subject: str
    body: str


def get_document_service(session: Session = Depends(get_session)) -> DocumentService:
    return DocumentService(session)


def _document_label(document: Document) -> str:
    fields = document.fields or {}
    if document.document_type == "invoice":
        return (
            f"vendor {fields.get('vendor_name', 'unknown')}, "
            f"invoice number {fields.get('invoice_number', 'unknown')}"
        )
    return (
        f"merchant {fields.get('merchant_name', 'unknown')}, "
        f"dated {fields.get('transaction_date', 'unknown')}"
    )


def _draft_email(document: Document, issues: list[ValidationIssue]) -> CorrectionEmailDraft:
    issue_lines = "\n".join(f"- {issue.message}" for issue in issues)
    prompt = (
        "Draft a polite, professional email in English to a supplier requesting a "
        "corrected document. Keep it concise and specific.\n\n"
        f"Document: {_document_label(document)}\n\n"
        f"Issues to raise:\n{issue_lines}\n\n"
        "Respond in exactly this format, with nothing before or after it:\n"
        "Subject: <subject line>\n\n<email body>"
    )
    text = _azure_openai_service.create_response(prompt)
    subject, _, body = text.partition("\n\n")
    subject = subject.removeprefix("Subject:").strip()
    return CorrectionEmailDraft(subject=subject, body=body.strip())


@router.post("/{document_id}/correction-email", response_model=CorrectionEmailDraft)
def draft_correction_email(
    document_id: int, service: DocumentService = Depends(get_document_service)
) -> CorrectionEmailDraft:
    try:
        document = service.get(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    validation = ValidationResult.model_validate(document.validation or {"issues": []})
    issues = eligible_issues(validation.issues)
    if not issues:
        raise HTTPException(status_code=409, detail="No supplier-fixable issues to raise.")

    return _draft_email(document, issues)
