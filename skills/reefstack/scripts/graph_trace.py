#!/usr/bin/env python3
"""Check a final report's step trace against the playbook it names.

    python3 graph_trace.py report.txt      # or "-" to read the report from standard input

The trace is a "Playbook: <name>" line followed by one numbered line per step, in the order the
steps ran. A step that ran again after a later step is listed again, and so is everything built on it.
"""

from pathlib import Path
import re
import sys


PLAYBOOKS = Path(__file__).resolve().parent.parent / "references/playbooks"
HEADER = re.compile(r"(?im)^[\s>*_#-]*playbook\W+([a-z][a-z -]*[a-z])")
LINE = re.compile(r"^[\s>*-]*(\d+)[.)]\s*(.*)$")
STEP = re.compile(r"(?m)^(\d+)\. \*\*[^*]+\*\*(.*(?:\n[ \t]+\S.*)*)")
OUTPUT = re.compile(r"\*\*Output:\*\* `([^`]+)`")
NEEDS = re.compile(r"\*\*Needs:\*\*([^*]*)")
SKIPPED = re.compile(r"(?i)\bskipped\b\W*(.*)")


def playbook_steps(name, playbooks=PLAYBOOKS):
    """Return {number: (output name or None, [numbers of the steps it needs])}, or None for an unknown playbook."""
    path = Path(playbooks) / (name + ".md")
    if name == "graph" or not path.is_file():
        return None
    found = [(int(number), body) for number, body in STEP.findall(path.read_text(encoding="utf-8"))]
    producer = {match.group(1): number for number, body in found for match in [OUTPUT.search(body)] if match}
    steps = {}
    for number, body in found:
        output, needs = OUTPUT.search(body), NEEDS.search(body)
        named = re.findall(r"`([^`]+)`", needs.group(1)) if needs else []
        steps[number] = (output.group(1) if output else None,
                         sorted({producer[item] for item in named if producer.get(item, number) < number}))
    return steps


def playbook_name(report, playbooks=PLAYBOOKS):
    match = HEADER.search(report)
    if not match:
        return None
    words = match.group(1).lower().replace("pull request", "pr").split()
    known = sorted(path.stem for path in Path(playbooks).glob("*.md") if path.stem != "graph")
    for size in range(len(words), 0, -1):  # "Bug fix", "opening a PR", and "feature playbook" all resolve
        for candidate in ("-".join(words[:size]), "-".join(word for word in words[:size] if word != "a")):
            if candidate in known:
                return candidate
    return "-".join(words)


def check(report, playbooks=PLAYBOOKS):
    """Return (playbook name or None, errors). No "Playbook:" line means no trace: (None, [])."""
    name = playbook_name(report, playbooks)
    if name is None:
        return None, []
    steps = playbook_steps(name, playbooks)
    if steps is None:
        return name, [f"unknown playbook '{name}'; name the playbook file you followed, such as 'Playbook: feature'"]
    errors, current, ran = [], set(), set()
    lines = report[HEADER.search(report).end():].splitlines()
    for number, text in ((int(m.group(1)), m.group(2).strip(" *_`")) for m in map(LINE.match, lines) if m):
        if number not in steps:
            errors.append(f"step {number} is not in the {name} playbook, which has steps 1 to {max(steps)}")
            continue
        output, needs = steps[number]
        skipped = SKIPPED.search(text)
        if skipped and len(skipped.group(1).split()) < 2:
            errors.append(f"step {number}: give the reason it was skipped, as 'skipped: <reason>'")
        if not skipped:
            if output and output not in text:
                errors.append(f"step {number}: name its output `{output}` and say what it contains")
            missing = [need for need in needs if need not in current]
            if missing:
                errors.append(f"step {number} ran before step {missing[0]}, whose output it needs, was current; "
                              f"list step {missing[0]} first, as done or skipped with a reason")
            ran.add(number)
        # Running a step again makes everything built on it stale until those steps are listed again.
        stale, grew = {number}, True
        while grew:
            grew = False
            for later, (_, later_needs) in steps.items():
                if later not in stale and stale & set(later_needs):
                    stale.add(later)
                    grew = True
        current -= stale
        current.add(number)
    for number in sorted(set(steps) - current):
        errors.append(f"step {number} has no current line; after returning to an earlier step, list again every "
                      "step that depends on it" if number in ran else
                      f"step {number} is missing; list it as done or as 'skipped: <reason>'")
    if max(steps) in current and max(steps) not in ran:
        errors.append(f"step {max(steps)} carries the completion check and cannot be skipped")
    return name, errors


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    report = sys.stdin.read() if argv[0] == "-" else Path(argv[0]).read_text(encoding="utf-8")
    name, errors = check(report)
    if name is None:
        print("no step trace: start it with a 'Playbook: <name>' line, then one numbered line per step")
        return 1
    print("\n".join(f"{name}: {error}" for error in errors) or f"{name}: step trace ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
