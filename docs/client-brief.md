# Client brief

## The company

Delta Facilities B.V. is a fictional facilities-management company based in Amsterdam. It buys cleaning, maintenance, electrical, plumbing, and equipment services from suppliers across the European Union.

Maya works in finance and administration. Supplier invoices and employee expense receipts arrive as digital PDFs, scans, screenshots, and phone photos. They may be written in English, Dutch, German, or French. Before a document enters bookkeeping, Maya needs to know what it is, confirm the important values, check VAT and totals, and assign the correct account.

All product copy, source code, documentation, and teaching content is English. Only the example supplier documents vary in language.

## User story

> As a finance administrator at a European company, I want to upload a multilingual invoice or receipt and receive a prepared review containing the best combined extraction, VAT and policy results, and a suggested GL account so I can approve valid documents quickly and turn supplier errors into a clear correction request.

## What's included in the build

- One PDF or image per upload, with a 4 MB limit.
- Automatic invoice/receipt recognition with strict Azure OpenAI output.
- Azure AI Document Intelligence `prebuilt-invoice` and `prebuilt-receipt` extraction.
- Invoice supplier/customer details and VAT IDs, dates, PO, currency, and totals.
- Receipt merchant, transaction date, subtotal, VAT, and total.
- Offline EU invoice VAT format/checksum validation plus receipt VAT-total reconciliation.
- Separate deterministic invoice and receipt policies, duplicate detection, corrections, approval, and rejection.
- A fixed Delta GL catalog plus an Azure OpenAI structured suggestion that a reviewer can override.
- SQLite, local file storage, and a guided welcome → upload/preview → process → review flow.
- Review history with explicit local deletion so the same invoice can be demonstrated again.
- An on-demand Azure OpenAI correction-email draft with Copy and Close; the app never sends it.
- A 13-document fictional multilingual corpus containing 12 invoices and one imperfect Dutch fuel receipt.

## Delta policy

The Delta policy is simply the fictional company's rulebook expressed as ordinary Python. It decides what must be fixed before approval; Azure extracts evidence, but it does not own these rules.

### Invoice rules

Errors block approval: missing vendor/customer identity, missing or malformed supplier VAT, missing/mismatched customer VAT, missing invoice number/date/total/currency, non-positive total, invalid date order, total mismatch over EUR 0.01, and duplicate vendor/invoice keys. Missing PO and primary-extraction confidence below 0.80 are warnings.

### Receipt rules

A receipt records an expense that was already paid, so it does not need an invoice number, customer VAT, PO, or due date. Merchant, transaction date, currency, positive total, and VAT total are required. When subtotal and VAT are present, they must reconcile to the total within EUR 0.01. Low primary confidence is a warning.

A valid selected Delta GL account is also required for approval. The model may suggest one, but Maya remains responsible for the selection.

Document Intelligence stays primary. Maya sees where every value came from.
