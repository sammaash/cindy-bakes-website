"""Backward-compatible local entry point for the Cindy Bakes web service."""

from __future__ import annotations

import os
from whatsapp_webhook import create_app


if __name__ == "__main__":
    create_app().run(
        host=os.getenv("WEB_CHAT_HOST", "127.0.0.1"),
        port=int(os.getenv("WEB_CHAT_PORT", "5001")),
        debug=False,
    )