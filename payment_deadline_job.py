"""Standalone scheduled job for deposit reminders and overdue cancellations."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from database import (
    DEFAULT_DATABASE_PATH, cancel_overdue_order, find_orders_requiring_cancellation,
    find_orders_requiring_reminders, get_order, mark_cancellation_notification_sent,
    mark_payment_reminder_sent,
)
from notifications import PaymentNotifier, create_payment_notifier


def run_payment_deadline_check(database_path: str | Path = DEFAULT_DATABASE_PATH,
                               notifier: PaymentNotifier | None = None,
                               as_of: date | None = None) -> dict:
    """Send one reminder before allowing a later run to cancel an unpaid order."""
    notifier = notifier or create_payment_notifier()
    as_of = as_of or date.today()
    cancellations = find_orders_requiring_cancellation(as_of, database_path)
    reminders = find_orders_requiring_reminders(as_of, database_path)
    result = {"reminders_sent": 0, "orders_cancelled": 0}

    for order in reminders:
        notifier.send_payment_reminder(order)
        if mark_payment_reminder_sent(order["id"], database_path):
            result["reminders_sent"] += 1

    for order in cancellations:
        if cancel_overdue_order(order["id"], database_path):
            cancelled_order = get_order(order["id"], database_path)
            notifier.send_cancellation_notification(cancelled_order)
            mark_cancellation_notification_sent(order["id"], database_path)
            result["orders_cancelled"] += 1
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Cindy Bakes payment deadlines.")
    parser.add_argument("--database", default=str(DEFAULT_DATABASE_PATH))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print(run_payment_deadline_check(args.database))
