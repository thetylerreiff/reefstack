# Category totals

A user sees how much they spent per category and in total.

## What it is

Prints one line per category, sorted by name, and a final `total` line.

## How to reach it

- cli: `python3 -m tally summary`

## Setup

The three seeded expenses from the index.

## Key paths

- With the seed: `food 12.25`, `travel 30.00`, `total 42.25`.
- With an empty ledger: `No expenses yet`.

## Success looks like

Exit code 0 and totals matching the seeded amounts.
