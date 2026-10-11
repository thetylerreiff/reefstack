"""Write deterministic shipment data; all files stay in the requested directory."""

import argparse
import json
from pathlib import Path


def write_workload(directory, order_count=18000, customer_count=3000):
    if order_count < 0 or customer_count < 1:
        raise ValueError("orders must be nonnegative and customers positive")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    customers = [{"id": f"C{index:05}", "name": f"Customer {index}, Dispatch",
                  "zone": ("local", "national", "international")[index % 3]}
                 for index in range(customer_count)]
    orders = [{"id": f"P{index:06}", "customer_id": f"C{(index * 997) % customer_count:05}",
               "grams": 1 + (index * 499) % 20000}
              for index in range(order_count)]
    for name, rows in (("customers", customers), ("orders", orders)):
        (directory / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")
    return orders, customers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--orders", type=int, default=18000)
    parser.add_argument("--customers", type=int, default=3000)
    args = parser.parse_args()
    write_workload(args.directory, args.orders, args.customers)
