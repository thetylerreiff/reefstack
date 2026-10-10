# tally verification map

How agents reach and check tally's commands. Read this index, then the feature file for the change.

## Launch

- No server. Run each command as `TALLY_HOME=$(mktemp -d) python3 -m tally <command>` from the project root so runs never touch the user's ledger.
- Seed with `python3 -m tally add 10 food`, `python3 -m tally add 2.25 food`, and `python3 -m tally add 30 travel` in the same `TALLY_HOME`.
- Evidence is the exact command, stdout, stderr, and exit code.

## Features

- [Record an expense](./add-expense.md): add and list expenses.
- [Category totals](./category-totals.md): totals per category.
