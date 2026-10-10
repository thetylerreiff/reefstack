"""tally: a small command-line expense tracker."""

import argparse
import csv
import json
import os
from pathlib import Path
import sys


def ledger_path():
    return Path(os.environ.get("TALLY_HOME", Path.home() / ".tally")) / "expenses.json"


def load():
    path = ledger_path()
    return json.loads(path.read_text()) if path.exists() else []


def save(expenses):
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(expenses, indent=2))


def cents(text):
    try:
        value = round(float(text) * 100)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an amount: {text}")
    if value <= 0:
        raise argparse.ArgumentTypeError("amount must be positive")
    return value


def money(value):
    return f"{value / 100:.2f}"


def command_add(args):
    expenses = load()
    expenses.append({"amount": args.amount, "category": args.category.lower(), "note": args.note or ""})
    save(expenses)
    print(f"Added {money(args.amount)} to {args.category.lower()}")


def command_list(args):
    expenses = load()
    if args.category:
        expenses = [item for item in expenses if item["category"] == args.category.lower()]
    if not expenses:
        print("No expenses yet")
        return
    for index, item in enumerate(expenses, 1):
        note = f"  {item['note']}" if item["note"] else ""
        print(f"{index:>3}  {money(item['amount']):>9}  {item['category']}{note}")


def command_summary(args):
    totals = {}
    for item in load():
        totals[item["category"]] = totals.get(item["category"], 0) + item["amount"]
    if not totals:
        print("No expenses yet")
        return
    for category in sorted(totals):
        print(f"{category:<12} {money(totals[category]):>9}")
    print(f"{'total':<12} {money(sum(totals.values())):>9}")


def command_export(args):
    writer = csv.writer(sys.stdout)
    writer.writerow(["amount", "category", "note"])
    for item in load():
        writer.writerow([money(item["amount"]), item["category"], item["note"]])


def parser():
    root = argparse.ArgumentParser(prog="tally", description="Track expenses from the terminal.")
    commands = root.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="record an expense")
    add.add_argument("amount", type=cents)
    add.add_argument("category")
    add.add_argument("--note")
    add.set_defaults(handler=command_add)
    listing = commands.add_parser("list", help="show recorded expenses")
    listing.add_argument("--category")
    listing.set_defaults(handler=command_list)
    summary = commands.add_parser("summary", help="totals per category")
    summary.set_defaults(handler=command_summary)
    export = commands.add_parser("export", help="write all expenses as CSV")
    export.set_defaults(handler=command_export)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    args.handler(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
