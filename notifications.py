"""Replaceable customer-notification interface; currently logs simulated messages."""

from __future__ import annotations

import logging
import os
from typing import Protocol

import requests

logger = logging.getLogger(__name__)


class PaymentNotifier(Protocol):
    def send_payment_reminder(self, order: dict) -> None: ...

    def send_cancellation_notification(self, order: dict) -> None: ...


class SimulatedNotifier:
    """Local stand-in for a future WhatsApp notifier."""

    def __init__(self):
        self.events: list[tuple[str, int]] = []

    def send_payment_reminder(self, order: dict) -> None:
        self.events.append(("payment_reminder", order["id"]))
        logging.info("SIMULATED payment reminder for order %s to %s", order["id"], order["phone_number"])

    def send_cancellation_notification(self, order: dict) -> None:
        self.events.append(("cancellation", order["id"]))
        logging.info("SIMULATED cancellation notification for order %s to %s", order["id"], order["phone_number"])


class WhatsAppUnavailableSender:
    """Explicit sender used while Cloud API credentials are not configured."""

    configured = False

    def send_text(self, recipient: str, message: str) -> None:
        raise RuntimeError(
            "WhatsApp Cloud API sending is unavailable. Configure WHATSAPP_ACCESS_TOKEN "
            "and WHATSAPP_PHONE_NUMBER_ID."
        )


class WhatsAppCloudNotifier:
    """Send payment lifecycle messages through the WhatsApp Cloud API."""

    def __init__(self, access_token: str, phone_number_id: str,
                 api_version: str = "v21.0"):
        self.url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        self.access_token = access_token
        self.configured = True

    @classmethod
    def from_environment(cls) -> "WhatsAppCloudNotifier | None":
        access_token = os.getenv("ACCESS_TOKEN") or os.getenv("WHATSAPP_ACCESS_TOKEN")
        phone_number_id = os.getenv("PHONE_NUMBER_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        if not access_token or not phone_number_id:
            return None
        return cls(access_token, phone_number_id, os.getenv("WHATSAPP_API_VERSION", "v21.0"))

    def _send(self, order: dict, message: str) -> None:
        self.send_text(_whatsapp_number(order["phone_number"]), message)

    def send_text(self, recipient: str, message: str) -> None:
        logger.info("WhatsApp send started recipient=%s message_length=%d", recipient, len(message))
        response = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": message},
            },
            timeout=15,
        )
        logger.info("WhatsApp API response status=%s", response.status_code)
        response.raise_for_status()

    def send_payment_reminder(self, order: dict) -> None:
        self._send(
            order,
            f"Cindy Bakes order #{order['id']}: your deposit of KSh {order['required_deposit']:.2f} "
            f"is due by {order['payment_deadline']} to keep your order for {order['date_needed']} active. "
            "Please send proof of payment or contact us.",
        )

    def send_cancellation_notification(self, order: dict) -> None:
        self._send(
            order,
            f"Cindy Bakes order #{order['id']} has been cancelled because the required deposit was not "
            f"received by {order['payment_deadline']}. Please contact us if you still need the order.",
        )


def _whatsapp_number(phone_number: str) -> str:
    """Convert a Kenyan local number to the international format WhatsApp expects."""
    digits = "".join(character for character in str(phone_number) if character.isdigit())
    if digits.startswith("0"):
        return "254" + digits[1:]
    if digits.startswith("254"):
        return digits
    raise ValueError("Customer phone number must be a Kenyan number starting with 0 or 254.")


def create_payment_notifier() -> PaymentNotifier:
    """Use WhatsApp when configured, otherwise preserve local checker behavior."""
    notifier = WhatsAppCloudNotifier.from_environment()
    if notifier is None:
        logging.warning("WhatsApp credentials are not configured; using simulated notifications.")
        return SimulatedNotifier()
    return notifier
