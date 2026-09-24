"""Generate a professional PDF invoice for a confirmed Cindy Bakes order."""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from business_rules import PERSONALISATION_PRICES
from catalog import CAKE_PRICES
from database import DEFAULT_DATABASE_PATH

BRAND_COLOR = colors.HexColor("#B5754A")
CURRENCY = "KES"
PERSONALISATION_LABELS = {
    "none": "None",
    "non_edible_topper": "Non-edible topper",
    "edible_print": "Edible print",
}


def _invoice_directory() -> Path:
    directory = Path(os.getenv("INVOICE_DIR") or Path(DEFAULT_DATABASE_PATH).parent / "invoices")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def invoice_number_for(order_id: int) -> str:
    return f"CB-{order_id:06d}"


def _line_items(order: dict) -> list[dict]:
    items = [{
        "name": f"{order['flavour']} cake ({order['weight_kg']}kg)",
        "qty": order["quantity"],
        "unit_price": CAKE_PRICES.get(order["flavour"], {}).get(order["weight_kg"], 0),
    }]
    personalisation_type = order.get("personalisation_type") or "none"
    if personalisation_type != "none":
        items.append({
            "name": PERSONALISATION_LABELS.get(personalisation_type, personalisation_type),
            "qty": order["quantity"],
            "unit_price": PERSONALISATION_PRICES.get(personalisation_type, 0),
        })
    delivery_cost = order.get("delivery_cost") or 0
    if order.get("fulfilment") == "delivery" and delivery_cost:
        items.append({"name": "Delivery", "qty": 1, "unit_price": delivery_cost})
    return items


def build_invoice_pdf(order: dict) -> tuple[str, str]:
    """Create a PDF invoice for a confirmed order. Returns (invoice_number, file_path)."""
    invoice_number = invoice_number_for(order["id"])
    file_path = _invoice_directory() / f"{invoice_number}.pdf"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CindyTitle", parent=styles["Title"], textColor=BRAND_COLOR, fontSize=22)
    label_style = ParagraphStyle("CindyLabel", parent=styles["Normal"], textColor=colors.grey, fontSize=9)
    value_style = styles["Normal"]

    doc = SimpleDocTemplate(str(file_path), pagesize=A4, topMargin=22 * mm, bottomMargin=18 * mm)
    story = [
        Paragraph("Cindy Bakes Delights", title_style),
        Paragraph("Custom-made cakes and celebration bakes &bull; Syokimau, Machakos, Kenya", label_style),
        Spacer(1, 14),
        Paragraph(f"<b>Invoice</b> {invoice_number}", styles["Heading2"]),
        Paragraph(f"Date: {order['created_at'][:10]}", value_style),
        Spacer(1, 10),
        Paragraph(f"<b>Bill to:</b> {order['customer_name']}", value_style),
        Paragraph(f"Phone: {order['phone_number']}", value_style),
    ]
    if order.get("fulfilment") == "delivery" and order.get("delivery_location"):
        story.append(Paragraph(f"Delivery location: {order['delivery_location']}", value_style))
        story.append(Paragraph(f"Delivery date: {order['date_needed']}", value_style))
    else:
        story.append(Paragraph(f"Pickup date: {order['date_needed']}", value_style))
    story.append(Spacer(1, 14))

    items = _line_items(order)
    table_data = [["Item", "Qty", "Unit price", "Amount"]]
    for item in items:
        amount = item["qty"] * item["unit_price"]
        table_data.append([
            item["name"], str(item["qty"]),
            f"{CURRENCY} {item['unit_price']:,.2f}", f"{CURRENCY} {amount:,.2f}",
        ])
    total = order["subtotal"] + (order.get("delivery_cost") or 0)
    table_data.append(["", "", "Total", f"{CURRENCY} {total:,.2f}"])
    table_data.append(["", "", "Required deposit (70%)", f"{CURRENCY} {order['required_deposit']:,.2f}"])
    table_data.append(["", "", "Balance due", f"{CURRENCY} {total - order['required_deposit']:,.2f}"])

    table = Table(table_data, colWidths=[70 * mm, 20 * mm, 40 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -4), 0.4, colors.lightgrey),
        ("FONTNAME", (2, -3), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "A 70% deposit confirms this order. Exact delivery charges (when applicable) are confirmed "
        "by staff. Payment is due at least 3 days before the delivery or pickup date.",
        label_style,
    ))

    doc.build(story)
    return invoice_number, str(file_path)
