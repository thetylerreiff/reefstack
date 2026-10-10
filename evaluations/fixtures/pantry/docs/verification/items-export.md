# Items export

A user downloads everything in the pantry as a CSV file.

## What it is

A CSV with a `name,quantity` header and one row per item, offered as `pantry.csv`.

## How to reach it

- web: `/items` then the `Download CSV` link
- web: `/items/export`

## Setup

The seeded data from the index.

## Key paths

- Download with the three seeded items.
- Add an item, then download again; the new row appears.

## Success looks like

Status 200, `Content-Type: text/csv`, a `Content-Disposition` naming `pantry.csv`, and rows matching the items page.
