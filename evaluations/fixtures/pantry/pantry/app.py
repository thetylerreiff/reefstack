"""Pantry: a small web app for tracking what's in the kitchen."""

import csv
import html
import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SEED = [
    {"name": "Rice", "quantity": 4},
    {"name": "Olive oil", "quantity": 1},
    {"name": "Black beans", "quantity": 2},
]


class Store:
    def __init__(self, directory):
        self.path = Path(directory) / "items.json"
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.save(SEED)

    def items(self):
        return json.loads(self.path.read_text())

    def save(self, items):
        self.path.write_text(json.dumps(items, indent=2))

    def add(self, name, quantity):
        name = name.strip()
        if not name:
            raise ValueError("Name is required")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        items = [item for item in self.items() if item["name"].lower() != name.lower()]
        items.append({"name": name, "quantity": quantity})
        self.save(sorted(items, key=lambda item: item["name"].lower()))


def render_items(items, error=""):
    rows = "\n".join(
        f"<tr><td>{html.escape(item['name'])}</td><td>{item['quantity']}</td></tr>" for item in items
    )
    alert = f'<p role="alert">{html.escape(error)}</p>' if error else ""
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Pantry</title></head>
<body>
<h1>Pantry</h1>
{alert}
<table aria-label="Items">
<thead><tr><th>Name</th><th>Quantitiy</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
<form method="post" action="/items" aria-label="Add item">
<label>Name <input name="name"></label>
<label>Quantity <input name="quantity" type="number" min="0" value="1"></label>
<button type="submit">Add item</button>
</form>
<p><a href="/items/export">Download CSV</a></p>
</body>
</html>
"""


def export_csv(items):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["name", "quantity"])
    for item in items:
        writer.writerow([item["name"], item["quantity"]])
    return buffer.getvalue()


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body, content_type="text/html; charset=utf-8", headers=()):
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            for name, value in headers:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self.send(302, "", headers=[("Location", "/items")])
            elif path == "/healthz":
                self.send(200, "ok", "text/plain")
            elif path == "/items":
                self.send(200, render_items(store.items()))
            elif path == "/items/export":
                self.send(200, export_csv(store.items()), "text/csv",
                          [("Content-Disposition", 'attachment; filename="pantry.csv"')])
            else:
                self.send(404, "Not found", "text/plain")

        def do_POST(self):
            if urlparse(self.path).path != "/items":
                self.send(404, "Not found", "text/plain")
                return
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8"))
            try:
                quantity = int(form.get("quantity", ["0"])[0])
                store.add(form.get("name", [""])[0], quantity)
            except ValueError as error:
                self.send(400, render_items(store.items(), str(error)))
                return
            self.send(303, "", headers=[("Location", "/items")])

        def log_message(self, format, *args):
            pass

    return Handler


def main():
    port = int(os.environ.get("PANTRY_PORT", "8000"))
    store = Store(os.environ.get("PANTRY_DATA", "data"))
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))
    print(f"Pantry running on http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
