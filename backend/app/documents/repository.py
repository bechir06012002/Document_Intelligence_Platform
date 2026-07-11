from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.documents.models import Document


def normalize_key(value: str) -> str:
    return value.strip().lower()


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document: Document) -> Document:
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        return document

    def get(self, document_id: int) -> Document | None:
        return self._session.get(Document, document_id)

    def list_all(self) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        return list(self._session.scalars(stmt))

    def update(self, document: Document) -> Document:
        self._session.commit()
        self._session.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self._session.delete(document)
        self._session.commit()

    def find_duplicate(
        self, vendor_name: str, invoice_number: str, exclude_id: int | None = None
    ) -> Document | None:
        stmt = select(Document).where(
            Document.normalized_vendor_name == normalize_key(vendor_name),
            Document.normalized_invoice_number == normalize_key(invoice_number),
            Document.status != "rejected",
        )
        if exclude_id is not None:
            stmt = stmt.where(Document.id != exclude_id)
        return self._session.scalars(stmt).first()
