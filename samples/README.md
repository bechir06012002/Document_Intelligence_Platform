# Sample invoices

A generated golden corpus of 12 fictional invoices plus one Dutch fuel receipt in English, Dutch, German, and French. `manifest.json` records the expected document type, normalized fields, and policy outcomes for each sample. No private document or random internet scrape belongs in this repository.

The committed set contains eleven PDFs and two PNG images. VAT values are fictional checksum examples and are never presented as verified business registrations.

`generate_corpus.py` (run via the backend's `uv` environment, e.g. `cd backend && uv run --locked --no-sync python ../samples/generate_corpus.py`) regenerates every file in `generated/` from `manifest.json`'s own `expected` values using `reportlab`/`pillow`. Re-run it after editing `manifest.json`'s fictional fields (e.g. the customer entity name) so the documents stay in sync with what the manifest expects.

Microsoft's official sample invoice can be downloaded locally for a first Azure provider smoke check, and is ignored by Git:

```bash
curl -L \
  https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-invoice.pdf \
  -o samples/sample-invoice.pdf
```

Optional external research datasets:

- [FATURA](https://zenodo.org/records/8261508): 10,000 synthetic English invoices across 50 layouts, CC BY 4.0.
- [DocILE](https://docile.rossum.ai/): annotated and synthetic business documents with research access.
- [CORD](https://github.com/clovaai/cord): Indonesian receipts, useful for expanding receipt evaluation.
- [SROIE](https://arxiv.org/abs/2103.10213): scanned receipt OCR benchmark.
