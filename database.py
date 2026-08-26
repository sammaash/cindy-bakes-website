"""SQLite persistence for confirmed Cindy Bakes orders and payment workflow."""

from __future__ import annotations

import sqlite3
import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from business_rules import DEPOSIT_PAYMENT_DEADLINE_DAYS
from order import parse_date_needed

DEFAULT_DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", Path(__file__).with_name("cindy_bakes.db"))
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect(database_path: str | Path = DEFAULT_DATABASE_PATH):
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            flavour TEXT NOT NULL,
            weight_kg INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            date_needed TEXT NOT NULL,
            personalisation_type TEXT NOT NULL,
            fulfilment TEXT NOT NULL,
            delivery_origin TEXT,
            delivery_location TEXT,
            delivery_distance_km REAL,
            delivery_rate_per_km REAL,
            delivery_cost REAL,
            subtotal REAL NOT NULL,
            required_deposit REAL NOT NULL,
            order_status TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            payment_verified INTEGER NOT NULL DEFAULT 0,
            payment_verified_at TEXT,
            payment_verified_by TEXT,
            payment_deadline TEXT NOT NULL,
            payment_reminder_sent_at TEXT,
            cancelled_at TEXT,
            cancellation_notification_sent_at TEXT,
            whatsapp_wa_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(orders)")}
    for column_name, column_type in {
        "delivery_origin": "TEXT",
        "delivery_location": "TEXT",
        "delivery_distance_km": "REAL",
        "delivery_rate_per_km": "REAL",
        "delivery_cost": "REAL",
        "whatsapp_wa_id": "TEXT",
    }.items():
        if column_name not in columns:
            connection.execute(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _row_as_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    data["payment_verified"] = bool(data["payment_verified"])
    return data


def create_pending_order(draft: dict, quote: dict, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict:
    """Persist a customer-confirmed order that awaits human payment verification."""
    date_needed = parse_date_needed(draft["date_needed"])
    payment_deadline = date_needed - timedelta(days=DEPOSIT_PAYMENT_DEADLINE_DAYS)
    timestamp = _now()
    values = {
        "customer_name": draft["customer_name"], "phone_number": draft["phone_number"],
        "flavour": draft["flavour"], "weight_kg": draft["weight_kg"],
        "quantity": draft["quantity"], "date_needed": date_needed.isoformat(),
        "personalisation_type": draft["personalisation_type"],
        "fulfilment": draft["fulfilment"],
        "delivery_origin": quote.get("delivery_origin") or "Dainty Haven, JWCQ+MW8, Beijing Road, Mlolongo, Kenya",
        "delivery_location": draft.get("delivery_location") or (None if draft.get("fulfilment") == "pickup" else None),
        "delivery_distance_km": quote.get("delivery_distance_km", 0),
        "delivery_rate_per_km": quote.get("delivery_rate_per_km", 32),
        "delivery_cost": quote.get("delivery_cost", 0),
        "subtotal": quote["subtotal"],
        "required_deposit": quote["required_deposit"], "order_status": "PENDING_PAYMENT",
        "payment_status": "PENDING", "payment_deadline": payment_deadline.isoformat(),
        "whatsapp_wa_id": draft.get("whatsapp_wa_id"),
        "created_at": timestamp, "updated_at": timestamp,
    }
    with _connect(database_path) as connection:
        cursor = connection.execute("""
            INSERT INTO orders (
                customer_name, phone_number, flavour, weight_kg, quantity, date_needed,
                personalisation_type, fulfilment, delivery_origin, delivery_location,
                delivery_distance_km, delivery_rate_per_km, delivery_cost,
                subtotal, required_deposit, order_status, payment_status,
                payment_deadline, whatsapp_wa_id, created_at, updated_at
            ) VALUES (
                :customer_name, :phone_number, :flavour, :weight_kg, :quantity, :date_needed,
                :personalisation_type, :fulfilment, :delivery_origin, :delivery_location,
                :delivery_distance_km, :delivery_rate_per_km, :delivery_cost,
                :subtotal, :required_deposit, :order_status, :payment_status,
                :payment_deadline, :whatsapp_wa_id, :created_at, :updated_at
            )
        """, values)
        order_id = cursor.lastrowid
    return get_order(order_id, database_path)


def get_order(order_id: int, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict | None:
    with _connect(database_path) as connection:
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _row_as_dict(row)


def list_orders(search: str | None = None, status: str = "all",
                database_path: str | Path = DEFAULT_DATABASE_PATH) -> list[dict]:
    """Return orders for staff views without changing their stored state."""
    conditions = []
    parameters: list[str | int] = []
    if status == "pending_payment":
        conditions.append("order_status = 'PENDING_PAYMENT'")
    elif status == "paid_confirmed":
        conditions.append("payment_status = 'PAID'")
    elif status == "overdue":
        conditions.append("payment_status = 'OVERDUE'")
    elif status == "cancelled":
        conditions.append("order_status = 'CANCELLED'")
    if search:
        conditions.append("(CAST(id AS TEXT) = ? OR customer_name LIKE ? OR phone_number LIKE ?)")
        parameters.extend([search, f"%{search}%", f"%{search}%"])
    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with _connect(database_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM orders{where_clause} ORDER BY created_at DESC, id DESC", parameters
        ).fetchall()
    return [_row_as_dict(row) for row in rows]


def update_delivery_cost(order_id: int, delivery_cost: float | int,
                         database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict:
    """Save a staff-confirmed delivery cost for an unpaid delivery order."""
    try:
        amount = float(delivery_cost)
    except (TypeError, ValueError) as error:
        raise ValueError("Delivery cost must be a valid amount.") from error
    if amount < 0:
        raise ValueError("Delivery cost cannot be negative.")
    with _connect(database_path) as connection:
        order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order is None:
            raise ValueError("Order not found.")
        if order["fulfilment"] != "delivery":
            raise ValueError("Delivery cost can only be set for delivery orders.")
        if order["payment_verified"] or order["order_status"] == "CANCELLED":
            raise ValueError("Delivery cost cannot be changed after payment verification or cancellation.")
        connection.execute(
            "UPDATE orders SET delivery_cost = ?, updated_at = ? WHERE id = ?",
            (amount, _now(), order_id),
        )
    return get_order(order_id, database_path)


def get_payment_status(order_id: int, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict | None:
    """Return only payment facts the AI may use when answering a customer."""
    order = get_order(order_id, database_path)
    if order is None:
        return None
    return {
        key: order[key]
        for key in ("id", "order_status", "payment_status", "payment_verified",
                    "payment_verified_at", "payment_deadline", "required_deposit")
    }


def verify_payment(order_id: int, verified_by: str | None = None,
                   database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict:
    """Human-only action that verifies a deposit and confirms the order."""
    timestamp = _now()
    with _connect(database_path) as connection:
        cursor = connection.execute("""
            UPDATE orders
            SET payment_verified = 1, payment_status = 'PAID', order_status = 'CONFIRMED',
                payment_verified_at = ?, payment_verified_by = ?, updated_at = ?
            WHERE id = ? AND payment_verified = 0 AND order_status != 'CANCELLED'
        """, (timestamp, verified_by, timestamp, order_id))
        if cursor.rowcount != 1:
            raise ValueError("Order cannot be verified; it may not exist, is already verified, or is cancelled.")
    return get_order(order_id, database_path)


def find_orders_requiring_reminders(as_of: date,
                                    database_path: str | Path = DEFAULT_DATABASE_PATH) -> list[dict]:
    with _connect(database_path) as connection:
        rows = connection.execute("""
            SELECT * FROM orders
            WHERE payment_verified = 0
              AND order_status = 'PENDING_PAYMENT'
              AND payment_status IN ('PENDING', 'AWAITING_FINAL_PAYMENT')
              AND payment_deadline <= ?
              AND payment_reminder_sent_at IS NULL
        """, (as_of.isoformat(),)).fetchall()
    return [_row_as_dict(row) for row in rows]


def find_orders_requiring_cancellation(as_of: date,
                                        database_path: str | Path = DEFAULT_DATABASE_PATH) -> list[dict]:
    """Find overdue, previously-reminded orders that have not yet been cancelled."""
    with _connect(database_path) as connection:
        rows = connection.execute("""
            SELECT * FROM orders
            WHERE payment_verified = 0
              AND order_status = 'PENDING_PAYMENT'
              AND payment_reminder_sent_at IS NOT NULL
              AND payment_deadline < ?
              AND cancelled_at IS NULL
        """, (as_of.isoformat(),)).fetchall()
    return [_row_as_dict(row) for row in rows]


def mark_payment_reminder_sent(order_id: int, database_path: str | Path = DEFAULT_DATABASE_PATH) -> bool:
    timestamp = _now()
    with _connect(database_path) as connection:
        cursor = connection.execute("""
            UPDATE orders
            SET payment_status = 'AWAITING_FINAL_PAYMENT', payment_reminder_sent_at = ?, updated_at = ?
            WHERE id = ? AND payment_verified = 0 AND order_status = 'PENDING_PAYMENT'
              AND payment_reminder_sent_at IS NULL
        """, (timestamp, timestamp, order_id))
    return cursor.rowcount == 1


def cancel_overdue_order(order_id: int, database_path: str | Path = DEFAULT_DATABASE_PATH) -> bool:
    """Idempotently cancel an unpaid order after its deadline."""
    timestamp = _now()
    with _connect(database_path) as connection:
        cursor = connection.execute("""
            UPDATE orders
            SET payment_status = 'OVERDUE', order_status = 'CANCELLED', cancelled_at = ?, updated_at = ?
            WHERE id = ? AND payment_verified = 0 AND order_status = 'PENDING_PAYMENT'
              AND cancelled_at IS NULL
        """, (timestamp, timestamp, order_id))
    return cursor.rowcount == 1


def mark_cancellation_notification_sent(order_id: int,
                                        database_path: str | Path = DEFAULT_DATABASE_PATH) -> bool:
    timestamp = _now()
    with _connect(database_path) as connection:
        cursor = connection.execute("""
            UPDATE orders SET cancellation_notification_sent_at = ?, updated_at = ?
            WHERE id = ? AND cancelled_at IS NOT NULL AND cancellation_notification_sent_at IS NULL
        """, (timestamp, timestamp, order_id))
    return cursor.rowcount == 1
