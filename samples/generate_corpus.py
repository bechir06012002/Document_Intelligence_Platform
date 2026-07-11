"""Regenerate the fictional sample invoice/receipt corpus so the customer entity reads
"Delta Facilities B.V." everywhere, driven by samples/manifest.json's own `expected` values.

One-off dev script. Not part of the backend application.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifest.json"
OUTPUT_DIR = ROOT / "generated"

CUSTOMER_NAME = "Delta Facilities B.V."
CUSTOMER_ADDRESS = "Prinsengracht 100, 1015 DX Amsterdam, Netherlands"

VENDOR_ADDRESS_BY_COUNTRY = {
    "FR": "12 Rue de la Paix, 75002 Paris, France",
    "DE": "Hauptstrasse 1, 10115 Berlin, Germany",
    "NL": "Kerkstraat 5, 1017 GC Amsterdam, Netherlands",
}

LABELS = {
    "en": dict(
        title="INVOICE",
        number="Invoice Number",
        inv_date="Invoice Date",
        due_date="Due Date",
        po="PO Number",
        bill_to="Bill To",
        vat="VAT Number",
        desc="Description",
        qty="Qty",
        unit_price="Unit Price",
        amount="Amount",
        subtotal="Subtotal",
        tax="Tax",
        total="Total",
        from_="From",
    ),
    "nl": dict(
        title="FACTUUR",
        number="Factuurnummer",
        inv_date="Factuurdatum",
        due_date="Vervaldatum",
        po="PO-nummer",
        bill_to="Factuuradres",
        vat="BTW-nummer",
        desc="Omschrijving",
        qty="Aantal",
        unit_price="Prijs",
        amount="Bedrag",
        subtotal="Subtotaal",
        tax="BTW",
        total="Totaal",
        from_="Van",
    ),
    "de": dict(
        title="RECHNUNG",
        number="Rechnungsnummer",
        inv_date="Rechnungsdatum",
        due_date="Falligkeitsdatum",
        po="Bestellnummer",
        bill_to="Rechnungsempfanger",
        vat="USt-IdNr.",
        desc="Beschreibung",
        qty="Menge",
        unit_price="Einzelpreis",
        amount="Betrag",
        subtotal="Zwischensumme",
        tax="MwSt",
        total="Gesamtbetrag",
        from_="Von",
    ),
    "fr": dict(
        title="FACTURE",
        number="Numero de facture",
        inv_date="Date de facture",
        due_date="Date d'echeance",
        po="Numero de commande",
        bill_to="Facture a",
        vat="Numero de TVA",
        desc="Description",
        qty="Qte",
        unit_price="Prix unitaire",
        amount="Montant",
        subtotal="Sous-total",
        tax="TVA",
        total="Total",
        from_="De",
    ),
}

RECEIPT_LABELS_NL = dict(
    title="KASSABON",
    date="Datum",
    desc="Omschrijving",
    qty="Aantal",
    unit_price="Prijs",
    amount="Bedrag",
    subtotal="Subtotaal",
    tax="BTW",
    total="Totaal",
)


def vendor_country(vendor_name: str) -> str:
    if "GmbH" in vendor_name:
        return "DE"
    if "S.A.S." in vendor_name:
        return "FR"
    return "NL"


@dataclass
class InvoiceSpec:
    filename: str
    language: str
    layout: str
    vendor_name: str
    vendor_vat_id: str | None
    customer_vat_id: str
    invoice_number: str
    purchase_order: str | None
    invoice_date: str
    due_date: str
    currency: str
    subtotal: str
    total_tax: str
    invoice_total: str
    item_count: int = 4


def load_invoice_specs() -> list[InvoiceSpec]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    specs = []
    for entry in manifest:
        if entry["document_type"] != "invoice":
            continue
        expected = entry["expected"]
        specs.append(
            InvoiceSpec(
                filename=entry["filename"],
                language=entry["language"],
                layout=entry["layout"],
                vendor_name=expected["vendor_name"],
                vendor_vat_id=expected["vendor_vat_id"],
                customer_vat_id=expected["customer_vat_id"],
                invoice_number=expected["invoice_number"],
                purchase_order=expected["purchase_order"],
                invoice_date=expected["invoice_date"],
                due_date=expected["due_date"],
                currency=expected["currency"],
                subtotal=expected["subtotal"],
                total_tax=expected["total_tax"],
                invoice_total=expected["invoice_total"],
                item_count=8 if entry["filename"] == "12-en-two-page.pdf" else 4,
            )
        )
    return specs


def line_items(spec: InvoiceSpec) -> list[tuple[str, str, str, str]]:
    subtotal = float(spec.subtotal)
    n = spec.item_count
    unit = subtotal / n
    return [
        (f"Facility service item {i + 1}", "1", f"{unit:.2f}", f"{unit:.2f}")
        for i in range(n)
    ]


PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def draw_header_block(c: Canvas, spec: InvoiceSpec, labels: dict[str, str]) -> float:
    country = vendor_country(spec.vendor_name)
    vendor_address = VENDOR_ADDRESS_BY_COUNTRY[country]
    y = PAGE_H - MARGIN

    if spec.layout == "modern":
        c.setFillColor(colors.HexColor("#1F3A5F"))
        c.rect(0, y - 4 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(MARGIN, y + 6 * mm, labels["title"])
        c.setFont("Helvetica", 10)
        c.drawRightString(
            PAGE_W - MARGIN, y + 6 * mm, f"{labels['number']}: {spec.invoice_number}"
        )
        c.setFillColor(colors.black)
        y -= 26 * mm
        body_font, bold_font = "Helvetica", "Helvetica-Bold"
    elif spec.layout == "compact":
        c.setFont("Helvetica-Bold", 14)
        c.drawString(MARGIN, y, labels["title"])
        c.setFont("Helvetica", 9)
        c.drawRightString(PAGE_W - MARGIN, y, f"{labels['number']}: {spec.invoice_number}")
        y -= 8 * mm
        body_font, bold_font = "Helvetica", "Helvetica-Bold"
    else:  # classic
        c.setFont("Times-Bold", 18)
        c.drawString(MARGIN, y, labels["title"])
        c.setFont("Times-Roman", 11)
        c.drawRightString(PAGE_W - MARGIN, y, f"{labels['number']}: {spec.invoice_number}")
        y -= 12 * mm
        c.setLineWidth(0.5)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        y -= 8 * mm
        body_font, bold_font = "Times-Roman", "Times-Bold"

    line_h = 5 * mm
    c.setFont(bold_font, 10)
    c.drawString(MARGIN, y, labels["from_"] + ":")
    c.setFont(body_font, 10)
    c.drawString(MARGIN, y - line_h, spec.vendor_name)
    c.drawString(MARGIN, y - 2 * line_h, vendor_address)
    if spec.vendor_vat_id is not None:
        c.drawString(MARGIN, y - 3 * line_h, f"{labels['vat']}: {spec.vendor_vat_id}")

    c.setFont(bold_font, 10)
    c.drawString(PAGE_W / 2, y, labels["bill_to"] + ":")
    c.setFont(body_font, 10)
    c.drawString(PAGE_W / 2, y - line_h, CUSTOMER_NAME)
    c.drawString(PAGE_W / 2, y - 2 * line_h, CUSTOMER_ADDRESS)
    c.drawString(PAGE_W / 2, y - 3 * line_h, f"{labels['vat']}: {spec.customer_vat_id}")

    y -= 5 * line_h
    c.setFont(body_font, 10)
    c.drawString(MARGIN, y, f"{labels['inv_date']}: {spec.invoice_date}")
    c.drawString(MARGIN, y - line_h, f"{labels['due_date']}: {spec.due_date}")
    if spec.purchase_order is not None:
        c.drawString(MARGIN, y - 2 * line_h, f"{labels['po']}: {spec.purchase_order}")
        y -= 2 * line_h
    else:
        y -= line_h
    return y


def draw_items_table(
    c: Canvas, items: list[tuple[str, str, str, str]], labels: dict[str, str], top: float
) -> float:
    body_font = "Helvetica"
    col_desc, col_qty, col_price = (
        MARGIN,
        PAGE_W - MARGIN - 55 * mm,
        PAGE_W - MARGIN - 40 * mm,
    )
    y = top
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_desc, y, labels["desc"])
    c.drawString(col_qty, y, labels["qty"])
    c.drawString(col_price, y, labels["unit_price"])
    c.drawRightString(PAGE_W - MARGIN, y, labels["amount"])
    y -= 4 * mm
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 5 * mm

    c.setFont(body_font, 9)
    for description, qty, unit_price, amount in items:
        c.drawString(col_desc, y, description)
        c.drawString(col_qty, y, qty)
        c.drawString(col_price, y, unit_price)
        c.drawRightString(PAGE_W - MARGIN, y, amount)
        y -= 6 * mm
    return y


def draw_totals(c: Canvas, spec: InvoiceSpec, labels: dict[str, str], top: float) -> None:
    y = top - 4 * mm
    c.line(PAGE_W - MARGIN - 60 * mm, y, PAGE_W - MARGIN, y)
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(PAGE_W - MARGIN - 60 * mm, y, labels["subtotal"])
    c.drawRightString(PAGE_W - MARGIN, y, f"{spec.currency} {spec.subtotal}")
    y -= 6 * mm
    c.drawString(PAGE_W - MARGIN - 60 * mm, y, labels["tax"])
    c.drawRightString(PAGE_W - MARGIN, y, f"{spec.currency} {spec.total_tax}")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(PAGE_W - MARGIN - 60 * mm, y, labels["total"])
    c.drawRightString(PAGE_W - MARGIN, y, f"{spec.currency} {spec.invoice_total}")


def render_invoice_pdf(spec: InvoiceSpec, out_path: Path) -> None:
    labels = LABELS[spec.language]
    c = Canvas(str(out_path), pagesize=A4)
    items = line_items(spec)

    if spec.item_count > 4:
        page1_items, page2_items = items[:4], items[4:]
        header_bottom = draw_header_block(c, spec, labels)
        table_top = header_bottom - 10 * mm
        draw_items_table(c, page1_items, labels, table_top)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(MARGIN, MARGIN, "... continued on next page ...")
        c.showPage()

        c.setFont("Helvetica-Bold", 12)
        continuation = (
            f"{labels['title']} {spec.invoice_number} "
            f"({labels['from_']} {spec.vendor_name})"
        )
        c.drawString(MARGIN, PAGE_H - MARGIN, continuation)
        table_bottom = draw_items_table(c, page2_items, labels, PAGE_H - MARGIN - 15 * mm)
        draw_totals(c, spec, labels, table_bottom)
    else:
        header_bottom = draw_header_block(c, spec, labels)
        table_top = header_bottom - 10 * mm
        table_bottom = draw_items_table(c, items, labels, table_top)
        draw_totals(c, spec, labels, table_bottom)

    c.showPage()
    c.save()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    return ImageFont.truetype(path, size)


def render_invoice_png_scan(spec: InvoiceSpec, out_path: Path) -> None:
    """Render an invoice as a somewhat degraded scan-quality PNG image."""
    labels = LABELS[spec.language]
    width, height = 1240, 1754  # ~150dpi A4
    img = Image.new("L", (width, height), color=250)
    draw = ImageDraw.Draw(img)

    title_font = load_font(34, bold=True)
    bold_font = load_font(18, bold=True)
    body_font = load_font(18)

    x_margin = 80
    y = 70
    draw.text((x_margin, y), labels["title"], font=title_font, fill=10)
    draw.text((width - x_margin - 260, y + 8), spec.invoice_number, font=body_font, fill=10)
    y += 70
    draw.line((x_margin, y, width - x_margin, y), fill=60, width=2)
    y += 30

    country = vendor_country(spec.vendor_name)
    vendor_address = VENDOR_ADDRESS_BY_COUNTRY[country]
    draw.text((x_margin, y), labels["from_"] + ":", font=bold_font, fill=10)
    draw.text((x_margin, y + 26), spec.vendor_name, font=body_font, fill=10)
    draw.text((x_margin, y + 52), vendor_address, font=body_font, fill=10)
    if spec.vendor_vat_id is not None:
        vat_line = f"{labels['vat']}: {spec.vendor_vat_id}"
        draw.text((x_margin, y + 78), vat_line, font=body_font, fill=10)

    x2 = width // 2
    draw.text((x2, y), labels["bill_to"] + ":", font=bold_font, fill=10)
    draw.text((x2, y + 26), CUSTOMER_NAME, font=body_font, fill=10)
    draw.text((x2, y + 52), CUSTOMER_ADDRESS, font=body_font, fill=10)
    draw.text((x2, y + 78), f"{labels['vat']}: {spec.customer_vat_id}", font=body_font, fill=10)

    y += 130
    draw.text((x_margin, y), f"{labels['inv_date']}: {spec.invoice_date}", font=body_font, fill=10)
    y += 26
    draw.text((x_margin, y), f"{labels['due_date']}: {spec.due_date}", font=body_font, fill=10)
    if spec.purchase_order is not None:
        y += 26
        draw.text((x_margin, y), f"{labels['po']}: {spec.purchase_order}", font=body_font, fill=10)

    y += 60
    col_desc, col_qty, col_price, col_amount = x_margin, width - 420, width - 320, width - 200
    draw.text((col_desc, y), labels["desc"], font=bold_font, fill=10)
    draw.text((col_qty, y), labels["qty"], font=bold_font, fill=10)
    draw.text((col_price, y), labels["unit_price"], font=bold_font, fill=10)
    draw.text((col_amount, y), labels["amount"], font=bold_font, fill=10)
    y += 30
    draw.line((x_margin, y, width - x_margin, y), fill=60, width=2)
    y += 20

    for description, qty, unit_price, amount in line_items(spec):
        draw.text((col_desc, y), description, font=body_font, fill=10)
        draw.text((col_qty, y), qty, font=body_font, fill=10)
        draw.text((col_price, y), unit_price, font=body_font, fill=10)
        draw.text((col_amount, y), amount, font=body_font, fill=10)
        y += 34

    label_x, value_x = width - x_margin - 340, width - x_margin - 160
    y += 20
    draw.line((label_x, y, width - x_margin, y), fill=60, width=2)
    y += 24
    draw.text((label_x, y), labels["subtotal"], font=body_font, fill=10)
    draw.text((value_x, y), f"{spec.currency} {spec.subtotal}", font=body_font, fill=10)
    y += 28
    draw.text((label_x, y), labels["tax"], font=body_font, fill=10)
    draw.text((value_x, y), f"{spec.currency} {spec.total_tax}", font=body_font, fill=10)
    y += 28
    draw.text((label_x, y), labels["total"], font=bold_font, fill=10)
    draw.text((value_x, y), f"{spec.currency} {spec.invoice_total}", font=bold_font, fill=10)

    # Simulate scan-quality degradation: mild blur, rotation, noise, contrast drop.
    img = img.rotate(1.2, expand=True, fillcolor=250)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    rng = random.Random(42)
    pixels = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.01)):
        px = rng.randrange(w)
        py = rng.randrange(h)
        pixels[px, py] = max(0, min(255, pixels[px, py] + rng.randint(-40, 40)))

    img.convert("RGB").save(out_path)


@dataclass
class ReceiptSpec:
    filename: str
    merchant_name: str
    transaction_date: str
    currency: str
    subtotal: str
    total_tax: str
    total: str


def load_receipt_spec() -> ReceiptSpec:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = next(e for e in manifest if e["document_type"] == "receipt")
    expected = entry["expected"]
    return ReceiptSpec(
        filename=entry["filename"],
        merchant_name=expected["vendor_name"],
        transaction_date=expected["invoice_date"],
        currency=expected["currency"],
        subtotal=expected["subtotal"],
        total_tax=expected["total_tax"],
        total=expected["invoice_total"],
    )


def render_receipt_png(spec: ReceiptSpec, out_path: Path) -> None:
    labels = RECEIPT_LABELS_NL
    width, height = 640, 900
    img = Image.new("L", (width, height), color=250)
    draw = ImageDraw.Draw(img)

    title_font = load_font(28, bold=True)
    bold_font = load_font(18, bold=True)
    body_font = load_font(18)

    x_margin = 40
    y = 40
    draw.text((width / 2, y), labels["title"], font=title_font, fill=10, anchor="ma")
    y += 50
    draw.text((width / 2, y), spec.merchant_name, font=bold_font, fill=10, anchor="ma")
    y += 30
    date_line = f"{labels['date']}: {spec.transaction_date}"
    draw.text((width / 2, y), date_line, font=body_font, fill=10, anchor="ma")
    y += 50
    draw.line((x_margin, y, width - x_margin, y), fill=60, width=2)
    y += 24

    qty, unit_price = "25", "2.00"
    subtotal_amount = f"{spec.currency} {spec.subtotal}"
    draw.text((x_margin, y), "Euro 95 Benzine", font=body_font, fill=10)
    y += 26
    draw.text((x_margin, y), f"{qty} x {spec.currency} {unit_price}", font=body_font, fill=10)
    draw.text((width - x_margin, y), subtotal_amount, font=body_font, fill=10, anchor="ra")
    y += 46

    draw.line((x_margin, y, width - x_margin, y), fill=60, width=2)
    y += 24
    draw.text((x_margin, y), labels["subtotal"], font=body_font, fill=10)
    draw.text((width - x_margin, y), subtotal_amount, font=body_font, fill=10, anchor="ra")
    y += 28
    draw.text((x_margin, y), labels["tax"], font=body_font, fill=10)
    tax_amount = f"{spec.currency} {spec.total_tax}"
    draw.text((width - x_margin, y), tax_amount, font=body_font, fill=10, anchor="ra")
    y += 28
    draw.text((x_margin, y), labels["total"], font=bold_font, fill=10)
    total_amount = f"{spec.currency} {spec.total}"
    draw.text((width - x_margin, y), total_amount, font=bold_font, fill=10, anchor="ra")

    img.convert("RGB").save(out_path)


def main() -> None:
    for spec in load_invoice_specs():
        out_path = OUTPUT_DIR / spec.filename
        if out_path.suffix.lower() == ".pdf":
            render_invoice_pdf(spec, out_path)
        else:
            render_invoice_png_scan(spec, out_path)
        print(f"wrote {out_path.name}")

    receipt_spec = load_receipt_spec()
    render_receipt_png(receipt_spec, OUTPUT_DIR / receipt_spec.filename)
    print(f"wrote {receipt_spec.filename}")


if __name__ == "__main__":
    main()
