from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from sqlalchemy import JSON, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DocumentStatus = Literal["processing", "needs_review", "approved", "rejected", "failed"]


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    original_filename: Mapped[str]
    stored_filename: Mapped[str]
    content_type: Mapped[str]
    status: Mapped[str] = mapped_column(default="processing")

    classification: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    fields: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    gl_classification: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    field_sources: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)

    selected_gl_account_code: Mapped[str | None] = mapped_column(default=None)
    gl_overridden: Mapped[bool] = mapped_column(default=False)

    normalized_vendor_name: Mapped[str | None] = mapped_column(index=True, default=None)
    normalized_invoice_number: Mapped[str | None] = mapped_column(index=True, default=None)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @property
    def document_type(self) -> str | None:
        return (self.classification or {}).get("document_type")

    @property
    def vendor_or_merchant_name(self) -> str | None:
        fields = self.fields or {}
        return fields.get("vendor_name") or fields.get("merchant_name")

    @property
    def total(self) -> str | None:
        fields = self.fields or {}
        return fields.get("invoice_total") or fields.get("total")

    @property
    def currency(self) -> str | None:
        return (self.fields or {}).get("currency")
