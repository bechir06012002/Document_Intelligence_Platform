# Document Review System

An AI-assisted invoice and receipt review app for a fictional facilities-management company. It extracts and validates supplier documents in English, Dutch, German, and French, flags policy issues before they reach bookkeeping, and lets a reviewer correct, categorize, and approve or reject each one.

## How it works

1. **Upload** a PDF/PNG/JPEG invoice or receipt.
2. **Extract** — Azure AI Document Intelligence pulls structured fields (vendor, VAT IDs, dates, totals, line items).
3. **Classify** — Azure OpenAI determines document type and suggests a general ledger account.
4. **Validate** — deterministic rules check VAT format/checksum, totals reconciliation, required fields, and duplicate invoices.
5. **Review** — a human sees the evidence, corrects any field, picks a GL account, and approves or rejects. Supplier-caused errors can be turned into an AI-drafted correction email.

## Tech stack

- **Backend:** FastAPI, SQLAlchemy + SQLite, Azure AI Document Intelligence, Azure OpenAI (via `pydantic-ai`)
- **Frontend:** Streamlit
- **Deployment:** Docker, Azure Container Apps

## Live demo

- App: **[invoice-review-ui.blacktree-b3a09823.westeurope.azurecontainerapps.io](https://invoice-review-ui.blacktree-b3a09823.westeurope.azurecontainerapps.io)**
- API health: [invoice-review.blacktree-b3a09823.westeurope.azurecontainerapps.io/health](https://invoice-review.blacktree-b3a09823.westeurope.azurecontainerapps.io/health)

All data is fictional. The demo database is ephemeral and may reset on redeploy.

## Running locally

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), an Azure Document Intelligence resource, and an Azure OpenAI resource.

```bash
cd backend && uv sync --locked
cd ../streamlit_app && uv sync --locked
```

Copy `backend/.env.example` to `backend/.env` and fill in your Azure endpoint/key values. Then, from the repo root:

```bash
run-dev.bat
```

This starts the API on `http://127.0.0.1:8000` and the UI on `http://127.0.0.1:8501`, and stops both on any keypress.

## Deployment

`Dockerfile.api` and `Dockerfile.ui` build the two services as separate images, deployed as two Azure Container Apps sharing one Container Apps Environment. Azure credentials are passed as Container Apps secrets, never baked into the image.

## Demo video

🎥 _Coming soon._
