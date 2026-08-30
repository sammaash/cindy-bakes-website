"""Authenticated staff order dashboard routes."""

from __future__ import annotations

import hmac
import os
import secrets

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from business_rules import PERSONALISATION_PRICES
from catalog import CAKE_PRICES
from database import get_order, list_orders, update_delivery_cost, verify_payment

PERSONALISATION_LABELS = {
    "none": "None", "non_edible_topper": "Non-edible topper", "edible_print": "Edible print",
}


def create_admin_blueprint() -> Blueprint:
    """Create private staff routes; they stay unavailable until configured."""
    admin = Blueprint("admin", __name__, url_prefix="/admin")

    def configured() -> bool:
        return bool(os.getenv("DASHBOARD_PASSWORD") and os.getenv("DASHBOARD_SECRET_KEY"))

    def present(order: dict) -> dict:
        cake_total = CAKE_PRICES.get(order["flavour"], {}).get(order["weight_kg"], 0) * order["quantity"]
        personalisation_total = PERSONALISATION_PRICES.get(order["personalisation_type"], 0) * order["quantity"]
        delivery_cost = order["delivery_cost"] or 0
        return {
            **order,
            "personalisation_label": PERSONALISATION_LABELS.get(order["personalisation_type"], order["personalisation_type"]),
            "cake_total": cake_total,
            "personalisation_total": personalisation_total,
            "total_order_amount": (order["subtotal"] or 0) + delivery_cost,
            "remaining_balance": (order["subtotal"] or 0) + delivery_cost - (order["required_deposit"] or 0),
            "delivery_disclaimer": "Exact delivery charge is confirmed later by staff." if order["fulfilment"] == "delivery" else "Pickup: no delivery charge.",
        }

    def csrf_token() -> str:
        token = session.get("admin_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["admin_csrf_token"] = token
        return token

    def require_admin() -> None:
        if not configured():
            abort(404)
        if not session.get("admin_authenticated"):
            abort(401)

    def valid_csrf() -> bool:
        return hmac.compare_digest(request.form.get("csrf_token", ""), session.get("admin_csrf_token", ""))

    @admin.before_request
    def require_login_for_private_routes():
        if request.endpoint in {"admin.login", "admin.authenticate"}:
            return None
        if not configured():
            abort(404)
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.login"))
        return None

    @admin.app_template_filter("money")
    def money(value):
        return f"KSh {float(value or 0):,.2f}"

    @admin.app_context_processor
    def inject_admin_template_values():
        return {"admin_csrf_token": csrf_token}

    @admin.get("/login")
    def login():
        if not configured():
            abort(404)
        if session.get("admin_authenticated"):
            return redirect(url_for("admin.orders"))
        return render_template("admin_login.html")

    @admin.post("/login")
    def authenticate():
        if not configured():
            abort(404)
        if hmac.compare_digest(request.form.get("password", ""), os.environ["DASHBOARD_PASSWORD"]):
            session.clear()
            session["admin_authenticated"] = True
            csrf_token()
            return redirect(url_for("admin.orders"))
        flash("Incorrect password.", "error")
        return redirect(url_for("admin.login"))

    @admin.post("/logout")
    def logout():
        require_admin()
        if not valid_csrf():
            abort(400)
        session.clear()
        return redirect(url_for("admin.login"))

    @admin.get("/")
    def orders():
        require_admin()
        selected_status = request.args.get("status", "all")
        search = request.args.get("search", "").strip()
        return render_template("admin_orders.html", orders=[present(order) for order in list_orders(search, selected_status)], selected_status=selected_status, search=search)

    @admin.get("/orders/<int:order_id>")
    def order_detail(order_id: int):
        require_admin()
        order = get_order(order_id)
        if order is None:
            return "Order not found", 404
        return render_template("admin_order_detail.html", order=present(order))

    @admin.post("/orders/<int:order_id>/verify")
    def mark_deposit_paid(order_id: int):
        require_admin()
        if not valid_csrf():
            abort(400)
        if request.form.get("confirm_payment") != "yes":
            flash("Payment was not changed. Confirmation is required.", "warning")
            return redirect(url_for("admin.order_detail", order_id=order_id))
        try:
            verify_payment(order_id, request.form.get("verified_by", "").strip() or None)
            flash("Deposit marked as paid and order confirmed.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("admin.order_detail", order_id=order_id))

    @admin.post("/orders/<int:order_id>/delivery-cost")
    def save_delivery_cost(order_id: int):
        require_admin()
        if not valid_csrf():
            abort(400)
        try:
            update_delivery_cost(order_id, request.form.get("delivery_cost", ""))
            flash("Delivery cost saved and balance recalculated.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("admin.order_detail", order_id=order_id))

    return admin
