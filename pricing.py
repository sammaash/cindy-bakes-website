"""Validated price and deposit calculations for Cindy Bakes."""

from business_rules import DELIVERY_RATE_PER_KM, PERSONALISATION_PRICES, REQUIRED_DEPOSIT_RATE
from catalog import CAKE_PRICES, find_flavour


def calculate_quote(
    flavour: str,
    weight: int,
    quantity: int,
    personalisation_type: str,
    delivery_cost: float | int | None = None,
    delivery_distance_km: float | int | None = None,
    delivery_rate_per_km: float | int = DELIVERY_RATE_PER_KM,
) -> dict:
    """Return a standard-cake quote. Delivery is human-confirmed and added to remaining balance after the deposit."""
    canonical_flavour = find_flavour(flavour)
    if canonical_flavour is None:
        raise ValueError("Custom flavours require contact for pricing.")
    if weight not in CAKE_PRICES[canonical_flavour]:
        raise ValueError("Standard cakes are available only in 1kg, 2kg, or 3kg sizes.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    if personalisation_type not in PERSONALISATION_PRICES:
        raise ValueError("Choose no personalisation, a non-edible topper, or an edible print.")

    delivery_cost_value = 0 if delivery_cost is None else float(delivery_cost)
    if delivery_cost_value < 0:
        raise ValueError("Delivery cost cannot be negative.")

    cake_total = CAKE_PRICES[canonical_flavour][weight] * quantity
    personalisation_fee_per_cake = PERSONALISATION_PRICES[personalisation_type]
    personalisation_total = personalisation_fee_per_cake * quantity
    base_total = cake_total + personalisation_total
    deposit = round(base_total * REQUIRED_DEPOSIT_RATE, 2)
    total_order_amount = base_total + delivery_cost_value
    remaining_balance = round(float(total_order_amount - deposit), 2)

    return {
        "flavour": canonical_flavour,
        "weight_kg": weight,
        "quantity": quantity,
        "cake_total": cake_total,
        "personalisation_type": personalisation_type,
        "personalisation_fee_per_cake": personalisation_fee_per_cake,
        "personalisation_total": personalisation_total,
        "delivery_cost": round(delivery_cost_value, 2),
        "delivery_distance_km": delivery_distance_km,
        "delivery_rate_per_km": delivery_rate_per_km,
        "subtotal": round(float(base_total), 2),
        "total_order_amount": round(float(total_order_amount), 2),
        "required_deposit": round(float(deposit), 2),
        "remaining_balance": remaining_balance,
        "currency": "KSh",
        "human_delivery_confirmation_required": delivery_cost is None,
    }
