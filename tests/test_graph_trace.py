import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("reefstack_graph_trace", ROOT / "skills/reefstack/scripts/graph_trace.py")
GRAPH_TRACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GRAPH_TRACE)
FEATURE = ("acceptance", "contract", "workstream", "change", "evidence", "findings")


def trace(lines, name="feature"):
    return f"Done.\n\nPlaybook: {name}\n" + "\n".join(lines) + "\n"


def feature(*extra):
    return trace([f"{number}. {output}: done" for number, output in enumerate(FEATURE, 1)] + list(extra))


class GraphTraceTests(unittest.TestCase):
    def test_every_graph_playbook_step_names_one_output_and_earlier_needs(self):
        for name in ("bug-fix", "feature", "refactoring", "performance", "prototype"):
            steps = GRAPH_TRACE.playbook_steps(name)
            with self.subTest(name=name):
                self.assertEqual(sorted(steps), list(range(1, len(steps) + 1)))
                self.assertTrue(all(output for output, _ in steps.values()))
                self.assertTrue(all(need < number for number, (_, needs) in steps.items() for need in needs))
        self.assertIsNone(GRAPH_TRACE.playbook_steps("graph"))

    def test_complete_trace_passes_and_report_without_one_is_not_an_error(self):
        self.assertEqual(GRAPH_TRACE.check(feature()), ("feature", []))
        self.assertEqual(GRAPH_TRACE.check("Fixed the typo."), (None, []))
        # Markdown emphasis, a spelled-out name, and a skipped step with a reason are all accepted.
        report = "**Playbook:** Bug fix\n" + "\n".join(
            ["1. skipped: cause already established", "2. skipped: cause already established",
             "3. `fix-boundary`: one guard", "4. change: applied", "5. evidence: repro passes", "6. findings: none"])
        self.assertEqual(GRAPH_TRACE.check(report), ("bug-fix", []))

    def test_missing_unknown_and_unexplained_steps_are_named(self):
        _, errors = GRAPH_TRACE.check(feature().replace("3. workstream: done\n", ""))
        self.assertIn("step 3 is missing", " ".join(errors))
        self.assertIn("step 4 ran before step 3", " ".join(errors))
        _, errors = GRAPH_TRACE.check(feature().replace("2. contract: done", "2. skipped"))
        self.assertIn("step 2: give the reason", " ".join(errors))
        _, errors = GRAPH_TRACE.check(feature().replace("5. evidence: done", "5. tests pass"))
        self.assertIn("step 5: name its output `evidence`", " ".join(errors))
        _, errors = GRAPH_TRACE.check(feature().replace("6. findings: done", "6. skipped: nothing to review here"))
        self.assertIn("cannot be skipped", " ".join(errors))
        _, errors = GRAPH_TRACE.check(feature("7. extra: done"))
        self.assertIn("step 7 is not in the feature playbook", " ".join(errors))
        self.assertIn("unknown playbook", " ".join(GRAPH_TRACE.check(trace(["1. x"], "nonsense"))[1]))

    def test_returning_to_a_step_makes_everything_built_on_it_stale(self):
        _, errors = GRAPH_TRACE.check(feature("3. workstream: redone after a failed check"))
        self.assertEqual(len(errors), 3)
        self.assertIn("step 4 has no current line", errors[0])
        again = feature("3. workstream: redone", "4. change: rejoined", "5. evidence: rerun", "6. findings: rechecked")
        self.assertEqual(GRAPH_TRACE.check(again), ("feature", []))

    def test_command_line_reads_standard_input_and_sets_the_exit_status(self):
        for report, status, expected in ((feature(), 0, "step trace ok"), ("no trace", 1, "no step trace"),
                                         (feature("2. contract: revised"), 1, "has no current line")):
            with self.subTest(expected=expected), mock.patch("sys.stdin", io.StringIO(report)), \
                    mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(GRAPH_TRACE.main(["-"]), status)
                self.assertIn(expected, out.getvalue())


if __name__ == "__main__":
    unittest.main()
