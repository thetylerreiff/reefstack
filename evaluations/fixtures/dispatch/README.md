# dispatch

Build CSV pickup manifests from a JSON order list and customer address book.
Python 3.9 or later and the standard library are sufficient.

```sh
python3 make_workload.py /tmp/dispatch-data
python3 -m dispatch manifest --orders /tmp/dispatch-data/orders.json --customers /tmp/dispatch-data/customers.json --output /tmp/dispatch-data/manifest.csv
python3 -m unittest -v
```

Orders contain `id`, `customer_id` and integer `grams` (1 through 20000).
Customers contain `id`, `name` and `zone` (`local`, `national`, `international`).
The first address-book entry for a customer ID wins. Orders retain their input
order; repeated order IDs are allowed. The output is UTF-8 CSV with CRLF line
endings and a header, including for an empty order list. `--express` adds 200
cents per parcel. The first 500 grams cost 350, 500 or 1200 cents by zone; each
additional started 500-gram band costs 80 cents.

A successful command is silent. Invalid data returns status 2 and an `Error:`
message on stderr. The output file is written only after all rows are processed;
invalid input leaves an existing manifest intact and does not create a new one.
The command never changes the input files or creates output parent directories.

`make_workload.py` generates deterministic inputs with 18000 orders and 3000
customers by default. Its options can create smaller workloads for quick checks.

The dispatch desk currently uses printed manifests. Before adding an interactive
pickup selector, staff need to try ways to find a customer, select parcels and
see the selected parcel count and total weight. Any local sketch should use
fictional parcels and require no account, network service or package install.
