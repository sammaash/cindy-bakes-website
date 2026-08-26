"""Local staff dashboard for Cindy Bakes orders."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from business_rules import PERSONALISATION_PRICES
from catalog import CAKE_PRICES
from database import DEFAULT_DATABASE_PATH, get_order, list_orders, update_delivery_cost, verify_payment

PERSONALISATION_LABELS = {
    "none": "None",
    "non_edible_topper": "Non-edible topper",
    "edible_print": "Edible print",
}


def create_app(database_path: str | Path = DEFAULT_DATABASE_PATH) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("DASHBOARD_SECRET_KEY", "local-cindy-bakes-dashboard")
    app.config["DATABASE_PATH"] = database_path

    def present(order: dict) -> dict:
        cake_total = CAKE_PRICES.get(order["flavour"], {}).get(order["weight_kg"], 0) * order["quantity"]
        personalisation_total = PERSONALISATION_PRICES.get(order["personalisation_type"], 0) * order["quantity"]
        delivery_cost = order["delivery_cost"] or 0
        return {
            **order,
            "personalisation_label": PERSONALISATION_LABELS.get(
                order["personalisation_type"], order["personalisation_type"]
            ),
            "cake_total": cake_total,
            "personalisation_total": personalisation_total,
            "total_order_amount": (order["subtotal"] or 0) + delivery_cost,
            "remaining_balance": (order["subtotal"] or 0) + delivery_cost - (order["required_deposit"] or 0),
            "delivery_disclaimer": (
                "Exact delivery charge is confirmed later by staff."
                if order["fulfilment"] == "delivery" else "Pickup: no delivery charge."
            ),
        }

    @app.template_filter("money")
    def money(value):
        return f"KSh {float(value or 0):,.2f}"

    @app.route("/")
    def orders():
        selected_status = request.args.get("status", "all")
        search = request.args.get("search", "").strip()
        rows = list_orders(search, selected_status, app.config["DATABASE_PATH"])
        return render_template(
            "admin_orders.html",
            orders=[present(order) for order in rows],
            selected_status=selected_status,
            search=search,
        )

    @app.route("/orders/<int:order_id>")
    def order_detail(order_id: int):
        order = get_order(order_id, app.config["DATABASE_PATH"])
        if order is None:
            return "Order not found", 404
        return render_template("admin_order_detail.html", order=present(order))

    @app.post("/orders/<int:order_id>/verify")
    def mark_deposit_paid(order_id: int):
        if request.form.get("confirm_payment") != "yes":
            flash("Payment was not changed. Confirmation is required.", "warning")
            return redirect(url_for("order_detail", order_id=order_id))
        try:
            verify_payment(
                order_id,
                request.form.get("verified_by", "").strip() or None,
                app.config["DATABASE_PATH"],
            )
            flash("Deposit marked as paid and order confirmed.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("order_detail", order_id=order_id))

    @app.post("/orders/<int:order_id>/delivery-cost")
    def save_delivery_cost(order_id: int):
        try:
            update_delivery_cost(
                order_id, request.form.get("delivery_cost", ""), app.config["DATABASE_PATH"]
            )
            flash("Delivery cost saved and balance recalculated.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("order_detail", order_id=order_id))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("DASHBOARD_PORT", "5000")), debug=False)
