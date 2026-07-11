# Build sequence

Follow these phases in order. Each one ends with a concrete verification step — don't move to the next phase until that one passes. This mirrors, in order, how the original project (e2e-invoice-review) was actually built, with Streamlit swapped in for the frontend phase.

Read `docs/client-brief.md` and `docs/architecture.md` before starting.

## Phase 0 — Setup

- [x] `cd backend && uv sync --locked` (already verified working in this starter).
- [x] Create (or reuse) an Azure Document Intelligence resource and an Azure OpenAI resource. Reusing existing resources from another project is fine — nothing about their configuration needs to change.
- [x] Copy `backend/.env.example` to `backend/.env` and fill in the real endpoint/key values.
- [x] Verify: a one-off script that builds `azure.ai.documentintelligence.DocumentIntelligenceClient` from those settings and calls it against one sample in `samples/generated/` succeeds.

## Phase 1 — Document Intelligence service

- [x] `backend/app/services/document_intelligence_service.py`: a `DocumentIntelligenceService` class wrapping `DocumentIntelligenceClient`. Two methods, `analyze_invoice(file_path)` and `analyze_receipt(file_path)`, both routed through a private `_analyze(model_id, file_path)` that resolves content-type from the file suffix (`.pdf`/`.png`/`.jpg`/`.jpeg`) via a small `CONTENT_TYPES_BY_SUFFIX` dict.
- [x] `backend/app/config.py`: a `Settings(BaseSettings)` reading the four Azure env vars from `backend/.env`, module-level `settings = Settings()` singleton. This is the *only* place env vars get read anywhere in the backend.
- [x] Verify: run `analyze_invoice` against `samples/generated/01-en-happy-classic.pdf` and print the raw result — confirm real field data comes back (vendor name, totals, etc.).

## Phase 2 — Normalized schemas

- [x] `backend/app/schemas/invoice.py`: `InvoiceFields` (Pydantic model — vendor/customer name+VAT, invoice number, PO, dates, currency, subtotal/tax/total, `line_items`) and `InvoiceLineItem`, each with a `from_document_fields(fields)` classmethod mapping Azure's raw field dict onto typed values (`date`, `Decimal`, not `float`, for money).
- [x] `backend/app/schemas/receipt.py`: same shape for `ReceiptFields`/`ReceiptLineItem` — no invoice number, customer identity, PO, or due date (receipts don't have them).
- [x] `backend/app/schemas/_document_intelligence.py`: shared private helpers (`get_string`, `get_date`, `get_number`, `get_amount`, `get_currency_code`, `get_items`) that read `DocumentField.value_*` attributes — keep the Azure SDK type import under `TYPE_CHECKING` only.
- [x] Verify: map real `analyze_invoice`/`analyze_receipt` output from a few samples (including one with a missing field, e.g. `05-nl-missing-vendor-vat.pdf`) into these schemas and confirm `None` handling and field names match `samples/manifest.json`'s `expected` block. **Empirically confirm every Document Intelligence field name you map** (e.g. `VendorTaxId`, not a guess) by printing the raw field dict first — invoice and receipt field names differ (e.g. `SubTotal` vs `Subtotal`).

## Phase 3 — Azure OpenAI service

- [x] `backend/app/services/azure_openai_service.py`: a thin `AzureOpenAIService` wrapping a plain `openai.OpenAI` client pointed at the Azure resource's `/openai/v1` endpoint (the unified v1 surface — no `azure-identity`/`AzureOpenAI`-class ceremony needed if the endpoint already ends in `/openai/v1/`). One method, `create_response(input_text)`, calling the Responses API. Hardcode the deployment/model name as a module constant, e.g. `MODEL_NAME`.
- [x] Verify: a one-off call returns a real answer to a trivial prompt.

## Phase 4 — Pipeline

- [x] `backend/app/pipeline/context.py`: `DocumentContext`, a **frozen** dataclass (`file_path`, then progressively-filled `text`, `classification`, `fields`, `validation`, `gl_classification`), with an `evolve(**changes)` helper over `dataclasses.replace`. Steps never mutate a context — each returns a new one.
- [x] `backend/app/pipeline/pipeline.py`: a `Step` `Protocol` (`run(self, context) -> DocumentContext`) and a `Pipeline` class that runs an ordered list of steps, threading the context through each. Log each step's name and timing via `logging.getLogger(__name__)` at `INFO` — this is what lets you see progress when running it later.
- [x] `backend/app/pipeline/read_text.py`: `ReadTextStep` — calls `analyze_invoice` purely to get `.content` (Document Intelligence populates full OCR text on every prebuilt model's result, regardless of model type), stores it as `context.text`. This lets you classify a document before knowing what type it is.
- [x] `backend/app/pipeline/classify.py`: `DocumentClassification` (`document_type: Literal["invoice","receipt"]`) and `ClassificationStep`, built with a `pydantic_ai.Agent` (`OpenAIChatModel` + `AzureProvider`, using the same `MODEL_NAME`) for structured-output classification from `context.text`.
- [x] `backend/app/pipeline/extract.py`: `ExtractionStep` — branches on `context.classification.document_type`, calls the matching `analyze_invoice`/`analyze_receipt`, maps via the schemas from Phase 2.
- [x] `backend/app/pipeline/classify_gl.py`: a fictional ~10-account GL catalog (`Literal` of `"code - name"` strings) and `GLClassificationStep`, another small `pydantic_ai.Agent` that suggests one account from `context.fields`.
- [x] Verify: assemble `Pipeline([ReadTextStep, ClassificationStep, ExtractionStep, GLClassificationStep])` and run it against several samples — confirm sensible classification and GL suggestions, and that step-by-step logging is visible.

## Phase 5 — Validation (Delta policy)

- [x] `backend/app/pipeline/validate.py`: pure functions implementing every rule in `docs/client-brief.md`'s "Delta policy" section, each issue carrying a **severity** (`error` blocks approval, `warning` doesn't):
  - Invoice: vendor/customer name required, vendor VAT required + format-valid (`python-stdnum`'s `stdnum.eu.vat.is_valid`), customer VAT/name must match Delta's own fixed identity constants, invoice number/date/currency/total required, non-positive total, invalid date order (due date before invoice date), subtotal+tax vs total reconciliation (`Decimal`, EUR 0.01 tolerance), PO missing = **warning**.
  - Receipt: merchant/date/currency/total required, non-positive total, same total-reconciliation check.
  - Duplicate detection: a pure `check_duplicate_invoice(is_duplicate: bool)` — the *caller* decides `is_duplicate` by querying persisted documents (Phase 6); this function itself takes no database dependency, keeping it pure.
  - `ValidationResult` holds `issues: list[ValidationIssue]`; `is_valid` means "no errors" (warnings don't block).
- [x] Verify: run the full pipeline over all 13 samples in `samples/generated/`, compare each one's resulting issue codes against `samples/manifest.json`'s `expected_issue_codes`. Expect an exact match on every sample. (Real-world note from the original build: one sample's Document Intelligence extraction may genuinely miss a field the manifest assumes was extracted — verify by checking Document Intelligence's *raw* field output directly before assuming your validation code is wrong.)

## Phase 6 — Persistence and the full API

This is the biggest phase — build and verify it in the sub-steps below, in order.

- [x] `backend/app/documents/models.py`: one SQLAlchemy `Document` table — id, original/stored filename, content type, `status` (`processing|needs_review|approved|rejected|failed`), JSON columns for `classification`/`fields`/`validation`/`gl_classification`, `field_sources` (JSON dict tracking which fields a human corrected), `selected_gl_account_code`, `gl_overridden`, `normalized_vendor_name`/`normalized_invoice_number` (indexed, for duplicate lookup), timestamps.
- [x] `backend/app/documents/database.py`: SQLite engine + session factory + `init_db()`, pointed at a gitignored `backend/data/` directory (both the `.db` file and uploaded originals — `backend/data/uploads/`).
- [x] `backend/app/documents/repository.py`: CRUD plus `find_duplicate(vendor_name, invoice_number, exclude_id)` (excludes rejected documents).
- [x] `backend/app/documents/service.py`: orchestrates create (run pipeline → persist → real duplicate check via the repository → `ValidationResult.with_issue(...)`), `correct` (partial field update, re-validate, track `field_sources`, blocked once `approved`/`rejected`), `select_gl_account` (validate against the fixed catalog), `decide` (approve/reject — approval blocked by any open error or a missing GL selection).
- [x] `backend/app/documents/routes.py`: `POST /documents` (upload), `GET /documents` (list), `GET /documents/{id}`, `GET /documents/{id}/file`, `PUT /documents/{id}` (corrections), `DELETE /documents/{id}`, `PUT /documents/{id}/accounting`, `POST /documents/{id}/decision`.
- [x] `backend/app/accounting/catalog.py`: the fixed GL account list moves here from `pipeline/classify_gl.py` (which keeps only the *suggestion* step) — this module owns the source of truth and validates any selected code.
- [x] `backend/app/accounting/routes.py`: `GET /accounting/gl-accounts`.
- [x] `backend/app/correction_email/eligibility.py` + `routes.py`: which issue codes are supplier-fixable (exclude `duplicate_invoice` — that's Delta's own finding, not the supplier's to fix), `POST /documents/{id}/correction-email` drafting via `AzureOpenAIService`, `409` when nothing's eligible.
- [x] `backend/app/main.py`: wires all routers, `init_db()` at import time, `GET /health`.
- [x] Verify end to end via `curl` (no frontend needed yet): upload a happy-path sample → approve directly; upload a sample with a VAT error → approve blocked (`422`) → correct the field → error clears → select a GL account → approve succeeds; upload the same vendor+invoice-number twice → second one flags `duplicate_invoice` → reject it → draft a correction email → delete it from history.

## Phase 7 — Streamlit frontend

Full design reference: think of this as replacing a React SPA with server-rendered pages that are thin REST clients of the API you just built — no backend changes needed here at all.

- [x] Get explicit approval for the exact pinned versions of `streamlit` and `requests` before running `uv add` — required by this project's dependency policy.
- [x] `streamlit_app/pyproject.toml` + `uv.lock`: its own `uv`-managed project, mirroring `backend/`'s exact-pin conventions.
- [x] `streamlit_app/lib/env.py`: reads `API_BASE_URL`, fails clearly if absent — the only environment boundary.
- [x] `streamlit_app/lib/types.py`: typed shapes (dataclasses or `TypedDict`) mirroring the backend's response JSON — `DocumentSummary`, `DocumentDetail`, `ValidationIssue`/`ValidationResult`, `GlClassification`, `CorrectionEmailDraft`.
- [x] `streamlit_app/lib/api.py`: thin `requests`-based client — one function per endpoint (`upload_document`, `list_documents`, `get_document`, `delete_document`, `correct_document`, `select_gl_account`, `decide_document`, `draft_correction_email`, `list_gl_accounts`). Only this module calls `requests`.
- [x] `streamlit_app/pages/upload.py`: `st.file_uploader` (type + 4MB check, matching the API's own limits), preview, `st.spinner` while `POST /documents` runs, then hand off to the review page via `st.session_state`.
- [x] `streamlit_app/pages/review.py`: display extracted fields as `st.text_input` per field (pre-filled, diffed on submit → `PUT /documents/{id}`); `st.selectbox` for GL account (options from `GET /accounting/gl-accounts`) → `PUT /documents/{id}/accounting`; `st.error`/`st.warning` per validation issue by severity; Approve/Reject buttons → `POST /documents/{id}/decision`, disabled with `help=` text when the approval gate isn't met; a "Draft correction email" button opening an `@st.dialog` showing subject/body (verify `st.dialog` is available in your pinned Streamlit version — it's the current native modal API, not a bare `pages/` trick).
- [x] `streamlit_app/pages/inbox.py`: list documents (`st.dataframe` or a row-per-document loop with a status indicator), click to open in the review page, delete with an `@st.dialog` confirmation (replaces a browser `confirm()`).
- [x] `streamlit_app/app.py`: `st.Page`/`st.navigation` over the three pages above (this is the current recommended multipage API — confirm it's still current when you get here, APIs like this do shift).
- [x] Verify: full manual walkthrough against the real running backend — upload → review → correct a field → select GL → approve/reject → history → delete → correction email — same acceptance test as Phase 6, now through the actual UI.
- [x] `uv run --locked --no-sync ruff check .` inside `streamlit_app/` stays clean throughout.

## Phase 8 — Local dev loop

- [x] `run-dev.bat` (already scaffolded in this starter) launches both `uvicorn` and `streamlit run` in one window once Phases 6 and 7 are done — verify it actually starts both and stops both cleanly on a keypress.

## Phase 9 — Docker + Azure deployment

Streamlit can't be bundled into the FastAPI container the way a built React SPA could (it's its own long-running server, not static files) — this becomes **two** container images sharing one Azure Container Apps Environment.

- [x] `Dockerfile.api`: single-stage `python:3.12-slim`, `uv sync --locked --no-dev`, run `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- [x] `Dockerfile.ui`: single-stage `python:3.12-slim` for `streamlit_app/`, `uv sync --locked --no-dev`, run `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`, with `API_BASE_URL` pointed at the API container app's internal or external URL via env var.
- [x] Create (or reuse) a resource group you own — **not** a course/instructor repo or resource group you don't have write access to, avoiding the exact permission problem hit earlier. (Reused `rg-invoice-review`, confirmed as user-owned, with a pre-existing ACR + Container Apps Environment + backend container app from an earlier attempt.)
- [x] Build and push both images to one Azure Container Registry; deploy both as separate `az containerapp` apps in the same Container Apps Environment; pass the four Azure credentials to the API app as Container Apps secrets (never baked into the image); cap both apps at `--min-replicas 1 --max-replicas 1` (SQLite has no multi-writer story).
- [x] Verify: hit the API app's `/health`, hit the Streamlit app's URL in a browser, and run the full manual workflow against the deployed pair.
- [x] Known trade-off to accept or address: Container Apps storage is ephemeral by default — the SQLite database resets on restart/redeploy unless you explicitly add an Azure Files-backed volume. Decide this deliberately, don't let it be a surprise. (Decided: accepted ephemeral storage — no extra Azure resources for this demo-scoped project.)

## Phase 10 — Make it yours on GitHub

- [ ] `git init` this folder (already done if you started from this starter as scaffolded).
- [ ] Create a new, empty repository under your **own** GitHub account (or a fork, if you want the upstream link) — not the original course repository, which you won't have push access to.
- [ ] `git remote add origin https://github.com/<your-username>/<repo-name>.git`
- [ ] `git push -u origin main`
