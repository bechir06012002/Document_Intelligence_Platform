from fastapi import FastAPI

from app.accounting.routes import router as accounting_router
from app.correction_email.routes import router as correction_email_router
from app.documents.database import init_db
from app.documents.routes import router as documents_router

init_db()

app = FastAPI(title="Delta Document Review System")

app.include_router(documents_router)
app.include_router(accounting_router)
app.include_router(correction_email_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
