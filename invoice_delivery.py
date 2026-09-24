"""Generate and deliver an invoice after an order is confirmed. Never breaks the order flow."""

from __future__ import annotations

import logging

from database import DEFAULT_DATABASE_PATH, get_order, save_invoice, update_whatsapp_delivery_status
from invoice import build_invoice_pdf
from notifications import _whatsapp_number

logger = logging.getLogger(__name__)


def generate_and_send_invoice(order_id: int, sender, database_path=DEFAULT_DATABASE_PATH) -> None:
    """Build the invoice PDF and attempt WhatsApp delivery; the order is kept regardless of outcome."""
    try:
        order = get_order(order_id, database_path)
        if order is None:
            logger.error("Invoice generation skipped: order %s not found", order_id)
            return
        invoice_number, file_path = build_invoice_pdf(order)
        save_invoice(order_id, invoice_number, file_path, database_path)
    except Exception:
        logger.exception("Invoice generation failed for order %s", order_id)
        return

    if not getattr(sender, "configured", False):
        update_whatsapp_delivery_status(order_id, "SKIPPED_NOT_CONFIGURED", database_path)
        logger.warning("WhatsApp invoice delivery skipped for order %s: sender not configured", order_id)
        return

    try:
        recipient = _whatsapp_number(order["phone_number"])
        total = order["subtotal"] + (order["delivery_cost"] or 0)
        caption = (
            f"Hi {order['customer_name']}, thank you for your order with Cindy Bakes. "
            f"Your invoice {invoice_number} is attached. Total: KSh {total:,.2f}."
        )
        sender.send_document(recipient, file_path, f"{invoice_number}.pdf", caption)
        update_whatsapp_delivery_status(order_id, "SENT", database_path)
    except Exception:
        logger.exception("WhatsApp invoice delivery failed for order %s", order_id)
        update_whatsapp_delivery_status(order_id, "FAILED", database_path)
