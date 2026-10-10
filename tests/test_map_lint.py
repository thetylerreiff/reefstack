import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_map_lint", ROOT / "scripts/map_lint.py")
MAP_LINT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MAP_LINT)

INDEX = """# Shop verification map

## Launch

- Start: `npm run dev` serves `http://localhost:3000`; ready when `/api/health` returns 200.

## Features

- [Checkout](./checkout.md)
- [Orders API](orders-api.md)
"""

CHECKOUT = """# Checkout

## What it is

A signed-in shopper pays for the items in their cart.

## How to reach it

- web: `/cart` then the `Checkout` button
- cli: `shop checkout --cart demo`

## Setup

Run `npm run seed`; sign in as `shopper@example.test`.

## Key paths

- Pay with the test card `4242 4242 4242 4242`.
- Declined card shows `Payment declined`.

## Success looks like

The confirmation page shows an order number and the order appears in `/orders`.

## Last checked

2026-10-10, revision `abc1234`, web `/cart`: verified. Evidence: `/tmp/shop/checkout.png`.
"""

ORDERS = """# Orders API

## What it is

Returns a shopper's orders as JSON.

## How to reach it

- api: `GET /api/orders/<id>`

## Setup

None beyond the seeded data.

## Key paths

- Known ID returns 200; unknown ID returns 404.

## Success looks like

The body has `id`, `status`, and `total` for the requested order.
"""


def valid_map():
    return {"README.md": INDEX, "checkout.md": CHECKOUT, "orders-api.md": ORDERS}


class MapLintTests(unittest.TestCase):
    def assert_error(self, files, fragment):
        errors = MAP_LINT.lint_files(files)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_valid_map_passes_including_route_parameters(self):
        self.assertEqual(MAP_LINT.lint_files(valid_map()), [])

    def test_packaged_template_passes_its_own_lint(self):
        files = MAP_LINT.template_files(ROOT / "references/feature-map-template.md")
        self.assertIn("README.md", files)
        self.assertGreater(len(files), 1)
        self.assertEqual(MAP_LINT.lint_files(files), [])

    def test_missing_and_misordered_sections_are_named(self):
        files = valid_map()
        files["checkout.md"] = CHECKOUT.replace("## Setup\n\nRun `npm run seed`; sign in as `shopper@example.test`.\n\n", "")
        self.assert_error(files, "missing section(s) ## Setup")
        files["checkout.md"] = CHECKOUT.replace("## What it is", "## Temp").replace("## Setup", "## What it is").replace("## Temp", "## Setup")
        self.assert_error(files, "put sections in this order")

    def test_empty_and_placeholder_entry_points_fail(self):
        for entry in ("- web:", "- web: ``", "- web: `<url>`", "- web: `TODO`", "- web: the cart page"):
            with self.subTest(entry=entry):
                files = valid_map()
                files["checkout.md"] = CHECKOUT.replace("- web: `/cart` then the `Checkout` button", entry)
                self.assert_error(files, "empty entry point")

    def test_entry_point_kind_must_be_known(self):
        files = valid_map()
        files["checkout.md"] = CHECKOUT.replace("- cli:", "- terminal:")
        self.assert_error(files, "kind one of web, cli, api")

    def test_moved_entry_point_left_without_replacement_fails(self):
        # An agent moving checkout deletes the old entry lines but never adds the new one.
        files = valid_map()
        files["checkout.md"] = CHECKOUT.replace("- web: `/cart` then the `Checkout` button\n- cli: `shop checkout --cart demo`\n", "")
        self.assert_error(files, "needs at least one entry point")

    def test_empty_sections_and_key_paths_fail(self):
        files = valid_map()
        files["orders-api.md"] = ORDERS.replace("Returns a shopper's orders as JSON.", "TBD")
        self.assert_error(files, "'## What it is' is empty or a placeholder")
        files["orders-api.md"] = ORDERS.replace("- Known ID returns 200; unknown ID returns 404.", "Check it works.")
        self.assert_error(files, "'## Key paths' needs at least one '- ' bullet")

    def test_last_checked_needs_a_status_and_must_come_last(self):
        files = valid_map()
        files["checkout.md"] = CHECKOUT.replace(": verified.", ": looked fine.")
        self.assert_error(files, "must state one of: verified, unreachable, blocked, not tried")
        last = CHECKOUT.index("## Last checked")
        moved = CHECKOUT[last:] + "\n" + CHECKOUT[:last]
        files["checkout.md"] = "# Checkout\n\n" + moved.replace("# Checkout\n\n", "", 1)
        self.assert_error(files, "goes after the required sections")

    def test_index_must_list_every_file_and_no_dead_links(self):
        files = valid_map()
        files["search.md"] = ORDERS.replace("# Orders API", "# Search")
        self.assert_error(files, "'search.md' is not listed")
        files = valid_map()
        del files["orders-api.md"]
        self.assert_error(files, "links to missing file 'orders-api.md'")
        files = valid_map()
        files["README.md"] = INDEX.replace("## Launch\n\n- Start: `npm run dev` serves `http://localhost:3000`; ready when `/api/health` returns 200.\n", "## Launch\n")
        self.assert_error(files, "non-empty '## Launch'")
        self.assertIn("README.md: missing", MAP_LINT.lint_files({"checkout.md": CHECKOUT})[0])

    def test_unknown_section_long_file_and_bad_name_fail(self):
        files = valid_map()
        files["checkout.md"] = CHECKOUT + "\n## Internals\n\nUses Stripe.\n"
        self.assert_error(files, "unknown section '## Internals'")
        files["checkout.md"] = CHECKOUT + "\n## Gotchas\n\n" + "- note\n" * 80
        self.assert_error(files, "split it into smaller features")
        files = valid_map()
        files["Checkout_Flow.md"] = files.pop("checkout.md")
        files["README.md"] = INDEX.replace("./checkout.md", "Checkout_Flow.md")
        self.assert_error(files, "lowercase-hyphenated")

    def test_cli_reports_errors_and_exit_codes_from_a_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "app docs" / "verification"
            directory.mkdir(parents=True)
            for name, text in valid_map().items():
                (directory / name).write_text(text)
            command = [sys.executable, str(ROOT / "scripts/map_lint.py"), str(directory)]
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout)
            self.assertIn("feature map ok", run.stdout)
            (directory / "orders-api.md").write_text(ORDERS.replace("`GET /api/orders/<id>`", "``"))
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("orders-api.md:9: empty entry point", run.stdout)
            run = subprocess.run([sys.executable, str(ROOT / "scripts/map_lint.py"), str(Path(parent) / "absent")],
                                 text=True, capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("no feature map directory", run.stdout)

    def test_health_lints_template_and_project_map(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "relocated plugin"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", ".git", "dist", "docs"))
            env = dict(os.environ)
            env.pop("PLUGIN_DATA", None)
            health = [sys.executable, str(root / "scripts/health.py")]
            report = json.loads(subprocess.run(health, text=True, capture_output=True, env=env, check=True).stdout)
            self.assertEqual((report["feature_map_template"], report["feature_map"]), ("pass", "not_present"))
            directory = root / "docs/verification"
            directory.mkdir(parents=True)
            for name, text in valid_map().items():
                (directory / name).write_text(text)
            report = json.loads(subprocess.run(health, text=True, capture_output=True, env=env, check=True).stdout)
            self.assertEqual(report["feature_map"], "pass")
            (directory / "checkout.md").write_text(CHECKOUT.replace("## Key paths", "## Paths"))
            run = subprocess.run(health, text=True, capture_output=True, env=env)
            self.assertEqual(run.returncode, 1)
            self.assertIn("feature map fails lint", json.loads(run.stdout)["reason"])
            template = root / "references/feature-map-template.md"
            template.write_text(template.read_text().replace("- api: `GET /api/invoices.csv`", "- api: ``"))
            run = subprocess.run(health, text=True, capture_output=True, env=env)
            self.assertIn("feature map template fails lint", json.loads(run.stdout)["reason"])


if __name__ == "__main__":
    unittest.main()
