"""Create a CSV pickup manifest from orders and an address book."""

import argparse
import csv
import io
import json
from pathlib import Path
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="dispatch")
    commands = parser.add_subparsers(dest="command", required=True)
    manifest = commands.add_parser("manifest", help="write a pickup manifest")
    manifest.add_argument("--orders", required=True)
    manifest.add_argument("--customers", required=True)
    manifest.add_argument("--output", required=True)
    manifest.add_argument("--express", action="store_true")
    args = parser.parse_args(argv)
    try:
        orders = json.loads(Path(args.orders).read_text(encoding="utf-8"))
        customers = json.loads(Path(args.customers).read_text(encoding="utf-8"))
        if not isinstance(orders, list) or not isinstance(customers, list):
            raise ValueError("orders and customers must be lists")
        # Address books can contain corrections; the first matching entry wins.
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(["order_id", "customer", "zone", "service", "postage_cents"])
        for order in orders:
            order_id = order["id"]
            grams = order["grams"]
            if isinstance(grams, bool) or not isinstance(grams, int) or not 1 <= grams <= 20000:
                raise ValueError(f"order {order_id}: grams must be an integer from 1 to 20000")
            customer = None
            for entry in customers:
                if entry["id"] == order["customer_id"]:
                    customer = entry
                    break
            if customer is None:
                raise ValueError(f"order {order_id}: unknown customer {order['customer_id']}")
            zone = customer["zone"]
            if zone not in ("local", "national", "international"):
                raise ValueError(f"order {order_id}: unknown zone {zone}")
            base = {"local": 350, "national": 500, "international": 1200}[zone]
            postage = base + ((grams - 1) // 500) * 80 + (200 if args.express else 0)
            writer.writerow([order_id, customer["name"], zone,
                             "express" if args.express else "standard", postage])
        Path(args.output).write_bytes(buffer.getvalue().encode("utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0
