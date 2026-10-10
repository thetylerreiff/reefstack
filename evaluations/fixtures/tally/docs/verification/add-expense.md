# Record an expense

A user records an amount with a category and an optional note, then sees it in the list.

## What it is

`add` stores an expense; `list` prints numbered expenses, optionally filtered by category.

## How to reach it

- cli: `python3 -m tally add 12.50 food --note lunch`
- cli: `python3 -m tally list --category food`

## Setup

An empty `TALLY_HOME` from the index.

## Key paths

- Add `12.50 food --note lunch`; stdout is `Added 12.50 to food`.
- `list` shows the expense with its note.
- `add -5 food` exits 2 with `amount must be positive` on stderr.

## Success looks like

Exit code 0 and the expense appears in `list` from a second command in the same `TALLY_HOME`.
