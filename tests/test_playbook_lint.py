import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINT = load("reefstack_playbook_lint", "scripts/playbook_lint.py")
HEALTH = load("reefstack_health_graphs", "scripts/health.py")
NAMES = LINT.vocabulary((ROOT / "references/playbooks/graph.md").read_text())


def playbook(name):
    return (ROOT / "references/playbooks" / (name + ".md")).read_text()


class PlaybookGraphLintTests(unittest.TestCase):
    def assertLintError(self, name, text, fragment):
        errors = LINT.lint_playbook(name + ".md", text, NAMES)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_converted_playbooks_pass(self):
        self.assertEqual(LINT.lint_package(ROOT), [])
        HEALTH.check_playbook_graphs()

    def test_every_converted_step_is_parsed(self):
        for name, count in (("bug-fix", 6), ("feature", 6), ("refactoring", 5), ("performance", 5), ("prototype", 5)):
            with self.subTest(name=name):
                steps, errors = LINT.parse_steps(playbook(name))
                self.assertEqual(errors, [])
                self.assertEqual([number for number, _, _, _ in steps], list(range(1, count + 1)))
                self.assertTrue(all("Output" in fields for _, fields, _, _ in steps))

    def test_need_without_earlier_producer_fails(self):
        text = playbook("bug-fix").replace("**Needs:** `cause`.", "**Needs:** `root-cause`.")
        self.assertLintError("bug-fix", text, "needs `root-cause`, which no earlier step outputs")

    def test_need_on_a_later_output_fails(self):
        text = playbook("bug-fix").replace("**Needs:** `repro`. **Output:** `cause`", "**Needs:** `evidence`. **Output:** `cause`")
        self.assertLintError("bug-fix", text, "needs `evidence`, which no earlier step outputs")

    def test_forward_on_fail_fails(self):
        text = playbook("bug-fix").replace("→ step 2 if the original reproduction", "→ step 6 if the original reproduction")
        self.assertLintError("bug-fix", text, "returns to step 6, which this step does not depend on")

    def test_on_fail_to_an_unrelated_earlier_step_fails(self):
        text = (
            "[dependency graph](graph.md)\n\n"
            "1. **Ask.** A. **Output:** `question`: q. **Check:** c.\n"
            "2. **Trace.** B. **Needs:** `question`. **Output:** `path`: p. **Check:** c.\n"
            "3. **Probe.** C. **Needs:** `question`. **Output:** `observation`: o. **On fail:** → step 2. "
            "**Completion check:** done.\n"
        )
        self.assertLintError("synthetic", text, "returns to step 2, which this step does not depend on")

    def test_missing_check_fails(self):
        text = playbook("feature").replace(
            "**Check:** before fan-out, the thin blocking integration path works.", ""
        )
        self.assertLintError("feature", text, "step 2: add a '**Check:**'")

    def test_missing_completion_check_fails(self):
        text = playbook("bug-fix").replace("**Completion check:**", "**Check:**")
        self.assertLintError("bug-fix", text, "the last step needs a '**Completion check:**'")

    def test_unshared_output_name_fails(self):
        text = playbook("bug-fix").replace("**Output:** `fix-boundary`", "**Output:** `scope`")
        self.assertLintError("bug-fix", text, "output `scope` is not in the graph.md output names")

    def test_old_compound_check_label_fails(self):
        # The pre-graph feature playbook used this label; the lint must not silently ignore it.
        text = playbook("feature").replace(
            "**Check:** before substantial implementation,", "**Check before substantial implementation:**"
        )
        self.assertLintError("feature", text, "unknown field '**Check before substantial implementation:**'")

    def test_entry_that_skips_a_needed_output_fails(self):
        text = playbook("bug-fix").replace("step 3 with `repro` and `cause`", "step 3 with `cause`")
        self.assertLintError("bug-fix", text, "entering at step 3 skips `repro`, which step 5 needs")

    def test_entry_carrying_a_later_output_fails(self):
        text = playbook("bug-fix").replace("step 3 with `repro` and `cause`", "step 3 with `repro`, `cause`, and `change`")
        self.assertLintError("bug-fix", text, "entry carries `change`, which no step before step 3 outputs")

    def test_missing_conventions_link_fails(self):
        text = playbook("feature").replace("[dependency graph](graph.md)", "dependency graph")
        self.assertLintError("feature", text, "link the conventions")
        anchored = playbook("feature").replace("(graph.md)", "(graph.md#step-fields)")
        self.assertEqual(LINT.lint_playbook("feature.md", anchored, NAMES), [])

    def test_wrapped_forward_on_fail_fails(self):
        text = playbook("bug-fix").replace(
            " **On fail:** → step 3 if the regression check never", "\n   **On fail:** → step 6 if the regression check never"
        )
        self.assertLintError("bug-fix", text, "returns to step 6, which this step does not depend on")

    def test_unindented_wrapped_field_fails(self):
        text = playbook("bug-fix").replace(
            " **On fail:** → step 3 if the regression check never", "\n**On fail:** → step 6 if the regression check never"
        )
        self.assertLintError("bug-fix", text, "field outside a step")

    def test_capitalized_or_bare_target_fails(self):
        for target in ("→ Step 6 if", "back to step 6 if", "→ steps 6 if", "→ step-6 if"):
            with self.subTest(target=target):
                text = playbook("bug-fix").replace("→ step 3 if the regression check", target + " the regression check")
                self.assertLintError("bug-fix", text, "write every '**On fail:**' target as '→ step K'")

    def test_malformed_entry_fails(self):
        for entry in ("**Enter at:** Step 3 with `cause`", "**Enter at:** step 3, carrying `cause`"):
            with self.subTest(entry=entry):
                text = playbook("bug-fix").replace("**Enter at:** step 3 with `repro` and `cause`", entry)
                self.assertLintError("bug-fix", text, "write the entry as")

    def test_empty_field_fails(self):
        text = playbook("bug-fix").replace("**Check:** the explanation accounts for the observed failure.", "**Check:**")
        self.assertLintError("bug-fix", text, "step 2: '**Check:**' is empty")

    def test_unparseable_step_line_fails(self):
        for broken in (" 4. **Fix and integrate.**", "4. **Fix *and* integrate.**"):
            with self.subTest(broken=broken):
                text = playbook("bug-fix").replace("4. **Fix and integrate.**", broken)
                self.assertLintError("bug-fix", text, "looks like a step but does not parse")

    def test_duplicate_output_fails(self):
        text = playbook("bug-fix").replace("**Output:** `fix-boundary`", "**Output:** `cause`")
        self.assertLintError("bug-fix", text, "output `cause` is already produced by step 2")

    def test_unbounded_optimization_loop_fails(self):
        # The hillclimbing loop the performance playbook forbids: a Repeat with nothing that stops it.
        text = playbook("performance").replace(
            " **Bound:** the user's decision for each new hypothesis, or one already in the authorized scope; without it, stop and report.", ""
        )
        self.assertLintError("performance", text, "step 4: a '**Repeat:**' needs a '**Bound:**'")

    def test_bound_without_repeat_fails(self):
        text = playbook("prototype").replace(
            " **Repeat:** → step 3 to refine a sketch while a criterion needs finer resolution to decide.", ""
        )
        self.assertLintError("prototype", text, "step 4: a '**Repeat:**' needs a '**Bound:**'")

    def test_repeat_to_a_later_or_unrelated_step_fails(self):
        text = playbook("refactoring").replace("**Repeat:** → step 3 for the next unit", "**Repeat:** → step 4 for the next unit")
        self.assertLintError("refactoring", text, "repeat returns to step 4, which this step does not depend on")
        text = playbook("performance").replace("**Repeat:** → step 2 with", "**Repeat:** → Step 2 with")
        self.assertLintError("performance", text, "write every '**Repeat:**' target as '→ step K'")

    def synthetic(self, step3):
        return (
            "[dependency graph](graph.md)\n\n"
            "1. **Ask.** A. **Output:** `question`: q. **Check:** c.\n"
            "2. **Trace.** B. **Needs:** `question`. **Output:** `path`: p. **Check:** c.\n"
            "3. **Probe.** C. **Needs:** `question`. **Output:** `observation`: o. **Check:** c. " + step3 + "\n"
            "4. **Report.** D. **Needs:** `observation`. **Output:** `finding`: f. **Completion check:** done.\n"
        )

    def test_repeat_may_return_to_its_own_step_but_on_fail_may_not(self):
        bounded = "**Repeat:** → step 3 while gaps remain. **Bound:** the scope in `question`."
        self.assertEqual(LINT.lint_playbook("synthetic.md", self.synthetic(bounded), NAMES), [])
        self.assertLintError("synthetic", self.synthetic("**On fail:** → step 3 if unclear."),
                             "on fail returns to step 3, which this step does not depend on")

    def test_repeat_to_an_unrelated_earlier_step_fails(self):
        text = self.synthetic("**Repeat:** → step 2 while gaps remain. **Bound:** the scope in `question`.")
        self.assertLintError("synthetic", text, "repeat returns to step 2, which this step does not depend on")

    def test_bound_must_name_a_reachable_output_or_the_user(self):
        for bound in ("none.", "→.", "until done.", "the stopping condition in `path`."):
            with self.subTest(bound=bound):
                text = self.synthetic("**Repeat:** → step 3 while gaps remain. **Bound:** " + bound)
                self.assertLintError("synthetic", text, "the '**Bound:**' must name an earlier output this step depends on")
        # A loop bounded by its own product is open-ended.
        text = self.synthetic("**Repeat:** → step 3 while gaps remain. **Bound:** until `observation` looks complete.")
        self.assertLintError("synthetic", text, "the '**Bound:**' must name an earlier output")
        for bound in ("a decision by the user.", "User approval.", "the users' decision."):
            with self.subTest(bound=bound):
                text = self.synthetic("**Repeat:** → step 3 while gaps remain. **Bound:** " + bound)
                self.assertEqual(LINT.lint_playbook("synthetic.md", text, NAMES), [])

    def test_repeat_needs_a_target_and_appears_once(self):
        text = self.synthetic("**Repeat:** until done. **Bound:** the scope in `question`.")
        self.assertLintError("synthetic", text, "write every '**Repeat:**' target as '→ step K'")
        text = self.synthetic("**Repeat:** → step 3 a. **Repeat:** → step 3 b. **Bound:** the scope in `question`.")
        self.assertLintError("synthetic", text, "'**Repeat:**' appears twice")

    def test_last_step_cannot_repeat(self):
        text = self.synthetic("").replace(
            "**Completion check:** done.", "**Repeat:** → step 4 again. **Bound:** the user's call. **Completion check:** done."
        )
        self.assertLintError("synthetic", text, "the last step cannot repeat")

    def test_health_rejects_broken_or_missing_graph_files(self):
        cases = (
            ("references/playbooks/graph.md", None, "missing graph.md"),
            ("references/playbooks/feature.md", None, "missing graph playbook feature.md"),
            ("references/playbooks/bug-fix.md", ("→ step 2 if", "→ step 6 if"), "returns to step 6"),
            ("references/playbooks/investigation.md", ("# Investigation playbook", "# Investigation playbook\n[graph](graph.md)"),
             "investigation.md links graph.md but is not linted"),
        )
        for relative, replacement, message in cases:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                for folder in ("references", "skills", "harness", "scripts"):
                    shutil.copytree(ROOT / folder, root / folder)
                target = root / relative
                if replacement is None:
                    target.unlink()
                else:
                    target.write_text(target.read_text().replace(*replacement))
                with mock.patch.object(HEALTH, "ROOT", root), self.assertRaisesRegex(ValueError, message):
                    HEALTH.check_playbook_graphs()

if __name__ == "__main__":
    unittest.main()
