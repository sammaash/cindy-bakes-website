"""Current-conversation order state and completeness checks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date

from catalog import find_flavour


MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def parse_date_needed(value: str) -> date:
    """Normalize a customer date to a valid 2026 ISO date."""
    raw = str(value).strip()
    if not raw:
        raise ValueError("Please provide a delivery or pickup date.")

    cleaned = raw.strip().lower().replace("/", " ")
    cleaned = re.sub(r"(?<=\d)(?i:st|nd|rd|th)\b", "", cleaned)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass

    day_month_match = re.match(r"^(\d{1,2})\s*[-\s]+\s*(\d{1,2}|[a-z]+)", cleaned)
    if day_month_match:
        day = int(day_month_match.group(1))
        month_token = day_month_match.group(2)
        month = int(month_token) if month_token.isdigit() else MONTH_NAMES.get(month_token)
        if month is None:
            raise ValueError("Please give the date in a clear day-month format, such as 12 Aug or 12/08.")
        return date(2026, month, day)

    month_day_match = re.match(r"^(\d{1,2}|[a-z]+)\s*[-\s]+\s*(\d{1,2})$", cleaned)
    if month_day_match:
        month_token = month_day_match.group(1)
        day = int(month_day_match.group(2))
        month = int(month_token) if month_token.isdigit() else MONTH_NAMES.get(month_token)
        if month is None:
            raise ValueError("Please give the date in a clear day-month format, such as Aug 12 or 08/12.")
        return date(2026, month, day)

    try:
        normalized = re.sub(r"[^0-9a-z]", " ", cleaned)
        parts = normalized.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return date(2026, int(parts[1]), int(parts[0]))
    except ValueError:
        pass

    raise ValueError("Please use a date like 12 Aug, 12/08, or 2026-08-12.")


@dataclass
class OrderDraft:
    customer_name: str | None = None
    flavour: str | None = None
    weight_kg: int | None = None
    quantity: int | None = None
    date_needed: str | None = None
    personalisation_type: str | None = None
    fulfilment: str | None = None
    delivery_location: str | None = None
    phone_number: str | None = None

    def update(self, **fields) -> dict:
        for name, value in fields.items():
            if value is not None and hasattr(self, name):
                setattr(self, name, value)
        if self.flavour:
            self.flavour = find_flavour(str(self.flavour)) or self.flavour.strip()
        if self.fulfilment:
            self.fulfilment = str(self.fulfilment).strip().lower()
        if self.personalisation_type:
            self.personalisation_type = str(self.personalisation_type).strip().lower()
        if self.date_needed:
            try:
                self.date_needed = parse_date_needed(self.date_needed).isoformat()
            except ValueError:
                pass
        return self.as_dict()

    def missing_fields(self) -> list[str]:
        required = [
            ("customer_name", self.customer_name), ("flavour", self.flavour),
            ("weight_kg", self.weight_kg), ("quantity", self.quantity),
            ("date_needed", self.date_needed), ("personalisation_type", self.personalisation_type),
            ("fulfilment", self.fulfilment), ("phone_number", self.phone_number),
        ]
        missing = [name for name, value in required if value is None or value == ""]
        if self.fulfilment == "delivery" and not self.delivery_location:
            missing.append("delivery_location")
        return missing

    def as_dict(self) -> dict:
        data = asdict(self)
        data["missing_fields"] = self.missing_fields()
        return data
