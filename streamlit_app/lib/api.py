from __future__ import annotations

from typing import Any

import requests

from lib.env import get_api_base_url
from lib.types import CorrectionEmailDraft, DocumentDetail, DocumentSummary


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
    response = requests.request(method, f"{get_api_base_url()}{path}", **kwargs)
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(response.status_code, detail)
    return response


def upload_document(filename: str, content_type: str, content: bytes) -> DocumentDetail:
    response = _request(
        "POST",
        "/documents",
        files={"file": (filename, content, content_type)},
        timeout=120,
    )
    return DocumentDetail.from_dict(response.json())


def list_documents() -> list[DocumentSummary]:
    response = _request("GET", "/documents", timeout=30)
    return [DocumentSummary.from_dict(item) for item in response.json()]


def get_document(document_id: int) -> DocumentDetail:
    response = _request("GET", f"/documents/{document_id}", timeout=30)
    return DocumentDetail.from_dict(response.json())


def get_document_file(document_id: int) -> bytes:
    response = _request("GET", f"/documents/{document_id}/file", timeout=30)
    return response.content


def delete_document(document_id: int) -> None:
    _request("DELETE", f"/documents/{document_id}", timeout=30)


def correct_document(document_id: int, updates: dict[str, Any]) -> DocumentDetail:
    response = _request("PUT", f"/documents/{document_id}", json=updates, timeout=30)
    return DocumentDetail.from_dict(response.json())


def select_gl_account(document_id: int, gl_account_code: str) -> DocumentDetail:
    response = _request(
        "PUT",
        f"/documents/{document_id}/accounting",
        json={"gl_account_code": gl_account_code},
        timeout=30,
    )
    return DocumentDetail.from_dict(response.json())


def decide_document(document_id: int, decision: str) -> DocumentDetail:
    response = _request(
        "POST", f"/documents/{document_id}/decision", json={"decision": decision}, timeout=30
    )
    return DocumentDetail.from_dict(response.json())


def draft_correction_email(document_id: int) -> CorrectionEmailDraft:
    response = _request("POST", f"/documents/{document_id}/correction-email", timeout=60)
    return CorrectionEmailDraft.from_dict(response.json())


def list_gl_accounts() -> list[str]:
    response = _request("GET", "/accounting/gl-accounts", timeout=30)
    return response.json()
