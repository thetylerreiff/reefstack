# tally

Track expenses from the terminal.

```sh
python3 -m tally add 12.50 food --note lunch
python3 -m tally list
python3 -m tally summary
python3 -m tally export > expenses.csv
```

Expenses are stored in `~/.tally/expenses.json`; set `TALLY_HOME` to use another directory.

## Checks

```sh
python3 -m unittest
```
