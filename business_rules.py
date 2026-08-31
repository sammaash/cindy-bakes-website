"""Approved Cindy Bakes business rules."""

PERSONALISATION_PRICES = {
    "none": 0,
    "non_edible_topper": 500,
    "edible_print": 1000,
}
REQUIRED_DEPOSIT_RATE = 0.70
DEPOSIT_PAYMENT_DEADLINE_DAYS = 3
RECOMMENDED_NOTICE_DAYS = 3
DELIVERY_RATE_PER_KM = 32
DELIVERY_ORIGIN = "Dainty Haven, JWCQ+MW8, Beijing Road, Mlolongo, Kenya"

BUSINESS_RULES = {
    "custom_flavours": "Custom flavours require the customer to contact Cindy Bakes for pricing.",
    "personalisation": (
        "No personalisation is free. A non-edible topper costs KSh 500 per cake, "
        "and an edible print costs KSh 1,000 per cake."
    ),
    "deposit": "A 70% deposit is required to confirm an order and must be paid at least 3 days before the delivery or pickup date.",
    "notice": "Orders should ideally be made at least 3 days in advance.",
    "delivery": (
        "Delivery cost is the actual driving distance in kilometres from Dainty Haven, "
        "JWCQ+MW8, Beijing Road, Mlolongo, Kenya, multiplied by KSh 32 per kilometre."
    ),
}
