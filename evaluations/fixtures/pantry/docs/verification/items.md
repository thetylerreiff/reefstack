# Items list

The items page lists everything in the pantry and lets a user add or update an item.

## What it is

A table of item names and quantities, sorted by name, with an `Add item` form below it.

## How to reach it

- web: `/items`
- web: `/` redirects to `/items`

## Setup

The seeded data from the index.

## Key paths

- Open `/items` and see the three seeded items.
- Add `Lentils` with quantity 3; the page reloads with Lentils in the table.
- Submit a blank name; the page shows the alert `Name is required` and status 400.

## Success looks like

The table shows each item's name and quantity, and a second load of `/items` shows the saved change.
