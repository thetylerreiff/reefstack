# Pantry

Track what's in your kitchen from the browser.

## Run

```sh
python3 -m pantry
```

Opens on http://127.0.0.1:8000 (set `PANTRY_PORT` to change it). Data lives in `./data/items.json`; set `PANTRY_DATA` to use another directory. A fresh data directory starts with three items.

## Checks

```sh
python3 -m unittest
```
