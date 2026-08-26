"""Approved standard cake catalogue for Cindy Bakes."""

CAKE_PRICES = {
    "Vanilla": {1: 2500, 2: 4200, 3: 5600},
    "Carrot": {1: 2500, 2: 4200, 3: 5600},
    "Lemon": {1: 2500, 2: 4200, 3: 5600},
    "Orange": {1: 2500, 2: 4200, 3: 5600},
    "White Forest": {1: 3100, 2: 4700, 3: 6000},
    "Black Forest": {1: 3100, 2: 4700, 3: 6000},
    "Blueberry": {1: 2700, 2: 4550, 3: 5800},
    "Caramel": {1: 3100, 2: 4700, 3: 6000},
    "Rainbow": {1: 3750, 2: 5000, 3: 6700},
    "Red Velvet": {1: 3100, 2: 4700, 3: 6000},
    "Chocolate": {1: 3100, 2: 4700, 3: 6000},
}


def find_flavour(name: str) -> str | None:
    """Return the canonical catalogue name for a customer-supplied flavour."""
    return next((flavour for flavour in CAKE_PRICES if flavour.lower() == name.strip().lower()), None)
