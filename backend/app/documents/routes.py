from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.accounting.catalog import InvalidGLAccountError
from app.documents.database import UPLOADS_DIR, get_session
from app.documents.models import Document
from app.documents.service import (
    ApprovalBlockedError,
    DocumentLockedError,
    DocumentNotFoundError,
    DocumentService,
)
from app.services.document_intelligence_service import CONTENT_TYPES_BY_SUFFIX

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_SUFFIXES = frozenset(CONTENT_TYPES_BY_SUFFIX)
MAX_UPLOAD_BYTES = 4 * 1024 * 1024


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    status: str
    document_type: str | None
    vendor_or_merchant_name: str | None
    total: str | None
    currency: str | None
    created_at: dt.datetime
    updated_at: dt.datetime


class DocumentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    status: str
    classification: dict[str, Any] | None
    fields: dict[str, Any] | None
    validation: dict[str, Any] | None
    gl_classification: dict[str, Any] | None
    field_sources: dict[str, str]
    selected_gl_account_code: str | None
    gl_overridden: bool
    created_at: dt.datetime
    updated_at: dt.datetime


class GLAccountSelectionRequest(BaseModel):
    gl_account_code: str


class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]


def get_document_service(session: Session = Depends(get_session)) -> DocumentService:
    return DocumentService(session)


@router.post("", status_code=201, response_model=DocumentDetail)
def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> Document:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix or '(none)'}")

    content = file.file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 4 MB limit.")

    try:
        return service.create(
            file.filename or "upload", file.content_type or "application/octet-stream", content
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Document processing failed.") from exc


@router.get("", response_model=list[DocumentSummary])
def list_documents(service: DocumentService = Depends(get_document_service)) -> list[Document]:
    return service.list_all()


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int, service: DocumentService = Depends(get_document_service)
) -> Document:
    try:
        return service.get(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{document_id}/file")
def get_document_file(
    document_id: int, service: DocumentService = Depends(get_document_service)
) -> FileResponse:
    try:
        document = service.get(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    file_path = UPLOADS_DIR / document.stored_filename
    return FileResponse(
        file_path, media_type=document.content_type, filename=document.original_filename
    )


@router.put("/{document_id}", response_model=DocumentDetail)
def correct_document(
    document_id: int,
    updates: dict[str, Any],
    service: DocumentService = Depends(get_document_service),
) -> Document:
    try:
        return service.correct(document_id, updates)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int, service: DocumentService = Depends(get_document_service)
) -> None:
    try:
        service.delete(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{document_id}/accounting", response_model=DocumentDetail)
def select_gl_account(
    document_id: int,
    payload: GLAccountSelectionRequest,
    service: DocumentService = Depends(get_document_service),
) -> Document:
    try:
        return service.select_gl_account(document_id, payload.gl_account_code)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidGLAccountError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/decision", response_model=DocumentDetail)
def decide_document(
    document_id: int,
    payload: DecisionRequest,
    service: DocumentService = Depends(get_document_service),
) -> Document:
    try:
        return service.decide(document_id, payload.decision)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ApprovalBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
