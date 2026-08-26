"""SQLite persistence for WhatsApp conversations and webhook idempotency."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from database import DEFAULT_DATABASE_PATH, _connect


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_whatsapp_tables(database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    with _connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_conversations (
                wa_id TEXT PRIMARY KEY,
                phone_number TEXT NOT NULL,
                draft_json TEXT NOT NULL,
                input_items_json TEXT NOT NULL,
                current_order_id INTEGER,
                last_activity_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (current_order_id) REFERENCES orders(id)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_events (
                message_id TEXT PRIMARY KEY,
                wa_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                received_at TEXT NOT NULL,
                processed_at TEXT,
                processing_status TEXT NOT NULL,
                error_message TEXT
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_orders_whatsapp_wa_id ON orders(whatsapp_wa_id)")


def load_conversation(wa_id: str, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict | None:
    initialize_whatsapp_tables(database_path)
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM whatsapp_conversations WHERE wa_id = ?", (wa_id,)
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["draft"] = json.loads(result.pop("draft_json"))
    result["input_items"] = json.loads(result.pop("input_items_json"))
    return result


def save_conversation(wa_id: str, phone_number: str, draft: dict, input_items: list,
                      current_order_id: int | None = None,
                      database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    initialize_whatsapp_tables(database_path)
    now = _now()
    with _connect(database_path) as connection:
        connection.execute("""
            INSERT INTO whatsapp_conversations (
                wa_id, phone_number, draft_json, input_items_json, current_order_id,
                last_activity_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(wa_id) DO UPDATE SET
                phone_number = excluded.phone_number,
                draft_json = excluded.draft_json,
                input_items_json = excluded.input_items_json,
                current_order_id = COALESCE(excluded.current_order_id, whatsapp_conversations.current_order_id),
                last_activity_at = excluded.last_activity_at,
                updated_at = excluded.updated_at
        """, (wa_id, phone_number, json.dumps(draft), json.dumps(input_items), current_order_id,
              now, now, now))


def claim_event(message_id: str, wa_id: str, message_type: str,
                database_path: str | Path = DEFAULT_DATABASE_PATH) -> bool:
    initialize_whatsapp_tables(database_path)
    with _connect(database_path) as connection:
        cursor = connection.execute("""
            INSERT OR IGNORE INTO whatsapp_events (
                message_id, wa_id, message_type, received_at, processing_status
            ) VALUES (?, ?, ?, ?, 'RECEIVED')
        """, (message_id, wa_id, message_type, _now()))
    return cursor.rowcount == 1


def complete_event(message_id: str, status: str = "PROCESSED", error_message: str | None = None,
                   database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    with _connect(database_path) as connection:
        connection.execute("""
            UPDATE whatsapp_events
            SET processed_at = ?, processing_status = ?, error_message = ?
            WHERE message_id = ?
        """, (_now(), status, error_message, message_id))


def latest_order_id(wa_id: str, database_path: str | Path = DEFAULT_DATABASE_PATH) -> int | None:
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT id FROM orders WHERE whatsapp_wa_id = ? ORDER BY id DESC LIMIT 1", (wa_id,)
        ).fetchone()
    return row[0] if row else None
