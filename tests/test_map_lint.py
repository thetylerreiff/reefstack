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

2026-10-10, revision `abc1234`, web `/cart`.
Status: verified
Evidence: `/tmp/shop/checkout.png`.
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

    def test_todo_app_handles_are_not_placeholders(self):
        files = valid_map()
        files["checkout.md"] = CHECKOUT.replace("`shop checkout --cart demo`", '`todo add "milk"`').replace(
            "A signed-in shopper pays for the items in their cart.", "Todo items shown in the list.")
        self.assertEqual(MAP_LINT.lint_files(files), [])

    def test_fences_anchors_crlf_and_outside_links_are_handled(self):
        files = valid_map()
        files["README.md"] = INDEX.replace("## Launch\n", "## Launch\n\nSee [dev setup](../../docs/dev-setup.md).\n").replace(
            "(./checkout.md)", "(<checkout.md> \"Checkout\")").replace("(orders-api.md)", "(orders-api.md#key-paths)") + "- Background: [API guide](../api/guide.md)\n"
        files["checkout.md"] = CHECKOUT.replace(
            "## Setup\n", "## Setup\n\n~~~sh\n## not a heading\nnpm run seed\n~~~\n\n```\n# nor this\n```\n")
        files = {name: text.replace("\n", "\r\n") for name, text in files.items()}
        self.assertEqual(MAP_LINT.lint_files(files), [])
        files["README.md"] = files["README.md"].replace("(orders-api.md#key-paths)", "")
        files["README.md"] += "\r\n[orders]: ./orders-api.md\r\n"
        self.assertEqual(MAP_LINT.lint_files(files), [])

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
        for status in ("Status: looked fine", "Status: not verified", "It was verified."):
            with self.subTest(status=status):
                files["checkout.md"] = CHECKOUT.replace("Status: verified", status)
                self.assert_error(files, "needs a line 'Status: <status>'")
        files["checkout.md"] = CHECKOUT.replace("Status: verified", "Status: blocked (port 3000 denied)")
        self.assertEqual(MAP_LINT.lint_files(files), [])
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

    def committed_fixture(self, parent, fixture):
        project = Path(parent) / fixture
        shutil.copytree(ROOT / "evaluations/fixtures" / fixture, project, ignore=shutil.ignore_patterns("__pycache__"))
        (project / "gitignore").rename(project / ".gitignore")
        identity = ["-c", "user.name=Sam", "-c", "user.email=sam@example.test"]
        for args in (["init", "-q"], ["add", "-A"], [*identity, "commit", "-qm", "start"]):
            subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True)
        return project

    def test_renamed_route_leaves_stale_entry_until_the_map_moves_with_it(self):
        with tempfile.TemporaryDirectory() as parent:
            project = self.committed_fixture(parent, "pantry")
            app = project / "pantry/app.py"
            app.write_text(app.read_text().replace('"/items/export"', '"/export/items.csv"'))
            # A compiled file that still holds the old literal is not source and must not mask the change.
            (project / "app.cpython-39.pyc").write_bytes(b'\x00\x01"/items/export"\x00')
            stale = MAP_LINT.stale_entries(project / "docs/verification", "HEAD")
            self.assertEqual(len(stale), 1)
            self.assertIn("items-export.md: entry `/items/export` names '/items/export'", stale[0])
            entry = project / "docs/verification/items-export.md"
            entry.write_text(entry.read_text().replace("`/items/export`", "`/export/items.csv`"))
            self.assertEqual(MAP_LINT.stale_entries(project / "docs/verification", "HEAD"), [])

    def test_renamed_cli_command_is_flagged_but_a_kept_alias_is_not(self):
        with tempfile.TemporaryDirectory() as parent:
            project = self.committed_fixture(parent, "tally")
            cli = project / "tally/cli.py"
            original = cli.read_text()
            cli.write_text(original.replace('add_parser("summary"', 'add_parser("report"'))
            checks = project / "test_tally.py"
            checks.write_text(checks.read_text().replace('"summary"', '"report"'))
            stale = MAP_LINT.stale_entries(project / "docs/verification", "HEAD")
            self.assertEqual([error.split(":")[0] for error in stale], ["category-totals.md"])
            self.assertIn("names 'summary'", stale[0])
            cli.write_text(original.replace('add_parser("summary"', 'add_parser("report", aliases=["summary"]'))
            self.assertEqual(MAP_LINT.stale_entries(project / "docs/verification", "HEAD"), [])

    def test_drift_check_handles_prose_urls_parameters_and_launchers(self):
        with tempfile.TemporaryDirectory() as parent:
            project = self.committed_fixture(parent, "pantry")
            entry = project / "docs/verification/items-export.md"
            entry.write_text(entry.read_text().replace(
                "- web: `/items/export`", "- web: `http://127.0.0.1:8765/items/export`\n- web: `/items/<id>`"))
            app = project / "pantry/app.py"
            app.write_text(app.read_text().replace('elif path == "/items":', 'elif path == "/items/<int:item_id>":'))
            subprocess.run(["git", "-C", str(project), "-c", "user.name=Sam", "-c", "user.email=sam@example.test",
                            "commit", "-qam", "detail route"], check=True)
            app.write_text(app.read_text().replace('"/items/export"', '"/export/items.csv"')
                           .replace('"/items/<int:item_id>"', '"/products/<int:item_id>"'))
            # A prose mention of the old route does not keep the entry alive.
            (project / "NOTES.md").write_text('Old download: "/items/export"\n')
            stale = MAP_LINT.stale_entries(project / "docs/verification", "HEAD")
            self.assertEqual(sorted(error.split("names ")[1].split(",")[0] for error in stale),
                             ["'/items/'", "'/items/export'"])
            self.assertTrue(any("`http://127.0.0.1:8765/items/export`" in error for error in stale), stale)
        with tempfile.TemporaryDirectory() as parent:
            project = self.committed_fixture(parent, "tally")
            helper = project / "tally/runner.py"
            helper.write_text('COMMAND = ["python3", "-m", "tally"]\n')
            subprocess.run(["git", "-C", str(project), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(project), "-c", "user.name=Sam", "-c", "user.email=sam@example.test",
                            "commit", "-qm", "helper"], check=True)
            helper.write_text('import sys\nCOMMAND = [sys.executable, "-m", "tally"]\n')
            self.assertEqual(MAP_LINT.stale_entries(project / "docs/verification", "HEAD"), [])

    def test_since_flag_runs_the_drift_check_from_the_command_line(self):
        with tempfile.TemporaryDirectory() as parent:
            project = self.committed_fixture(parent, "pantry")
            command = [sys.executable, str(ROOT / "scripts/map_lint.py"), "docs/verification", "--since", "HEAD"]
            run = subprocess.run(command, cwd=project, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout)
            app = project / "pantry/app.py"
            app.write_text(app.read_text().replace('"/items/export"', '"/csv"'))
            run = subprocess.run(command, cwd=project, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("update the map entry in the same change", run.stdout)
            run = subprocess.run(command[:-1] + ["no-such-revision"], cwd=project, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("cannot read map", run.stdout)

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
