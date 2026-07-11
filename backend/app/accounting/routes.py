from fastapi import APIRouter

from app.accounting.catalog import GL_ACCOUNTS

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.get("/gl-accounts")
def list_gl_accounts() -> list[str]:
    return list(GL_ACCOUNTS)
