"""Flask webhook for the official WhatsApp Cloud API."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

from agent import CindyBakesAgent
from admin_routes import create_admin_blueprint
from notifications import WhatsAppCloudNotifier, WhatsAppUnavailableSender
from whatsapp_agent_service import WhatsAppAgentService
from whatsapp_database import claim_event

logger = logging.getLogger(__name__)


def create_app(service: WhatsAppAgentService | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    # The dashboard blueprint is unavailable until its two Railway variables are set.
    app.config["SECRET_KEY"] = os.getenv("DASHBOARD_SECRET_KEY") or os.urandom(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=True,
    )
    app.register_blueprint(create_admin_blueprint())
    app.config["WHATSAPP_VERIFY_TOKEN"] = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    app.config["WHATSAPP_APP_SECRET"] = os.getenv("WHATSAPP_APP_SECRET", "")
    allowed_origins = {
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    }
    browser_sessions = {}
    if service is None:
        notifier = WhatsAppCloudNotifier.from_environment()
        notifier = notifier or WhatsAppUnavailableSender()
        service = WhatsAppAgentService(notifier)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok"}), 200

    @app.post("/api/chat")
    def browser_chat():
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        session_id = str(payload.get("session_id", "")).strip() or str(uuid.uuid4())
        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        try:
            agent = browser_sessions.get(session_id)
            if agent is None:
                agent = CindyBakesAgent()
                browser_sessions[session_id] = agent
            return jsonify({"reply": agent.respond(message), "session_id": session_id})
        except Exception:
            app.logger.exception("Browser chat request failed")
            return jsonify({"error": "The chat assistant is temporarily unavailable."}), 503

    @app.route("/api/chat", methods=["OPTIONS"])
    def browser_chat_options():
        return "", 204

    @app.get("/webhook")
    def verify_webhook():
        if (
            request.args.get("hub.mode") == "subscribe"
            and app.config["WHATSAPP_VERIFY_TOKEN"]
            and hmac.compare_digest(request.args.get("hub.verify_token", ""), app.config["WHATSAPP_VERIFY_TOKEN"])
        ):
            return request.args.get("hub.challenge", ""), 200
        return "Forbidden", 403

    @app.post("/webhook")
    def receive_webhook():
        if not getattr(service.sender, "configured", True):
            return jsonify({"error": "WhatsApp sending credentials are not configured"}), 503
        signature = request.headers.get("X-Hub-Signature-256", "")
        secret = app.config["WHATSAPP_APP_SECRET"]
        expected = "sha256=" + hmac.new(secret.encode(), request.get_data(), hashlib.sha256).hexdigest()
        if not secret or not hmac.compare_digest(signature, expected):
            return jsonify({"error": "Invalid signature"}), 403

        payload = request.get_json(silent=True) or {}
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                contacts = {item.get("wa_id"): item.get("wa_id") for item in value.get("contacts", [])}
                for message in value.get("messages", []):
                    if message.get("type") != "text":
                        continue
                    wa_id = message.get("from")
                    message_id = message.get("id")
                    text = message.get("text", {}).get("body")
                    if (
                        not wa_id or not message_id or not text
                        or not claim_event(message_id, wa_id, "text", service.database_path)
                    ):
                        continue
                    logger.info(
                        "WhatsApp incoming message message_id=%s wa_id=%s text=%r",
                        message_id, wa_id, text,
                    )
                    phone_number = contacts.get(wa_id, wa_id)
                    service.process_text(message_id, wa_id, phone_number, text)
        return jsonify({"received": True}), 200

    frontend_dist = Path(__file__).with_name("dist")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        # API and webhook paths are explicit routes above, never SPA fallbacks.
        if path == "health" or path == "webhook" or path.startswith("api/"):
            return jsonify({"error": "Route not found"}), 404
        requested_file = frontend_dist / path
        if path and requested_file.is_file():
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, "index.html")

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    create_app().run(
        host=os.getenv("WHATSAPP_WEBHOOK_HOST", "127.0.0.1"),
        port=int(os.getenv("WHATSAPP_WEBHOOK_PORT", "5001")),
        debug=False,
    )
