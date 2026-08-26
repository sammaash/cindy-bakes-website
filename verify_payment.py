"""Human staff command for manually verifying a customer's required deposit."""

from __future__ import annotations

import argparse

from database import DEFAULT_DATABASE_PATH, verify_payment


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manually verify a Cindy Bakes deposit.")
    parser.add_argument("order_id", type=int)
    parser.add_argument("--verified-by")
    parser.add_argument("--database", default=str(DEFAULT_DATABASE_PATH))
    args = parser.parse_args()
    order = verify_payment(args.order_id, args.verified_by, args.database)
    print(f"Order {order['id']} is confirmed; payment verified at {order['payment_verified_at']}.")
