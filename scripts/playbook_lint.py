#!/usr/bin/env python3
"""Check that graph playbooks form the dependency graphs described in skills/reefstack/references/playbooks/graph.md."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
CONVENTIONS = "graph.md"
# Playbooks converted to the graph format; later phases add the rest.
GRAPH_PLAYBOOKS = ("bug-fix", "feature", "refactoring", "performance", "prototype")
FIELDS = ("Needs", "Output", "Check", "On fail", "Repeat", "Bound", "Completion check")
STEP = re.compile(r"^(\d+)\. \*\*[^*]+\*\*(.*)$")
STEP_LIKE = re.compile(r"^\s*\d+\.\s")
FIELD = re.compile(r"\*\*([A-Z][A-Za-z ]*):\*\*")
ENTRY_LABEL = "**Enter at:**"
ENTRY = re.compile(r"^\*\*Enter at:\*\* step (\d+) with (.*)$")
TARGET = re.compile(r"→ step (\d+)")
ANY_TARGET = re.compile(r"\bsteps?\W*\d+", re.I)
CONVENTIONS_LINK = re.compile(r"\]\(graph\.md(#[^)]*)?\)")
NAME = re.compile(r"`([^`]+)`")
VOCABULARY_ROW = re.compile(r"^\| `([a-z][a-z-]*)` \|", re.M)


def vocabulary(text):
    return set(VOCABULARY_ROW.findall(text))


def parse_steps(text):
    """Return ([(number, {field: value}, unknown labels, duplicate labels)], parse errors).

    A step is a numbered line plus any indented continuation lines up to a blank line.
    """
    blocks, errors, current = [], [], None
    for number, line in enumerate(text.splitlines(), 1):
        match = STEP.match(line)
        if match:
            current = [int(match.group(1)), match.group(2)]
            blocks.append(current)
        elif STEP_LIKE.match(line):
            errors.append(f"line {number}: looks like a step but does not parse; write '1. **Name.** ...' "
                          "at the start of the line, with no '*' inside the name")
            current = None
        elif current is not None and line.strip() and line[:1].isspace():
            current[1] += " " + line.strip()
        else:
            current = None
            if FIELD.search(line) and ENTRY_LABEL not in line:
                errors.append(f"line {number}: field outside a step; indent it under its step or join it "
                              "to the step's line")
    steps = []
    for number, body in blocks:
        parts = FIELD.split(body)
        fields, unknown, duplicate = {}, [], []
        for label, value in zip(parts[1::2], parts[2::2]):
            if label not in FIELDS:
                unknown.append(label)
            elif label in fields:
                duplicate.append(label)
            else:
                fields[label] = value.strip()
        steps.append((number, fields, unknown, duplicate))
    return steps, errors


def lint_playbook(name, text, names):
    errors = []
    if not CONVENTIONS_LINK.search(text):
        errors.append(f"{name}: link the conventions as [dependency graph]({CONVENTIONS})")
    steps, parse_errors = parse_steps(text)
    errors.extend(f"{name} {error}" for error in parse_errors)
    if not steps:
        return errors + [f"{name}: no numbered steps found; write steps as '1. **Name.** ...'"]
    found = [number for number, _, _, _ in steps]
    if found != list(range(1, len(steps) + 1)):
        errors.append(f"{name}: steps are numbered {found}; number them consecutively from 1")
        return errors
    producer, needs = {}, {}
    for number, fields, unknown, duplicate in steps:
        where = f"{name} step {number}"
        for label in unknown:
            errors.append(f"{where}: unknown field '**{label}:**'; use one of " + ", ".join(FIELDS))
        for label in duplicate:
            errors.append(f"{where}: '**{label}:**' appears twice; merge them")
        for label, value in fields.items():
            if not value.strip(" ."):
                errors.append(f"{where}: '**{label}:**' is empty; say what it requires")
        last = number == len(steps)
        if last and "Completion check" not in fields:
            errors.append(f"{where}: the last step needs a '**Completion check:**'")
        if not last and "Check" not in fields:
            errors.append(f"{where}: add a '**Check:**' that must hold before later steps use the output")
        if not last and "Completion check" in fields:
            errors.append(f"{where}: only the last step has a '**Completion check:**'")
        output = fields.get("Output", "")
        match = NAME.match(output)
        if not match:
            errors.append(f"{where}: start '**Output:**' with its name in backticks, e.g. `change`")
        else:
            produced = match.group(1)
            if produced not in names:
                errors.append(f"{where}: output `{produced}` is not in the {CONVENTIONS} output names; "
                              "reuse a name or add a row there")
            if produced in producer:
                errors.append(f"{where}: output `{produced}` is already produced by step {producer[produced]}")
            else:
                producer[produced] = number
        needed = NAME.findall(fields.get("Needs", ""))
        if number > 1 and not needed:
            errors.append(f"{where}: add '**Needs:**' naming the earlier outputs this step consumes")
        needs[number] = []
        for item in needed:
            if item not in producer or producer[item] >= number:
                errors.append(f"{where}: needs `{item}`, which no earlier step outputs")
            else:
                needs[number].append((item, producer[item]))

    def ancestors(number):
        found, pending = set(), [step for _, step in needs.get(number, [])]
        while pending:
            step = pending.pop()
            if step not in found:
                found.add(step)
                pending.extend(earlier for _, earlier in needs.get(step, []))
        return found

    for number, fields, _, _ in steps:
        where = f"{name} step {number}"
        if ("Repeat" in fields) != ("Bound" in fields):
            errors.append(f"{where}: a '**Repeat:**' needs a '**Bound:**' that stops it, and a Bound needs a Repeat")
        if "Repeat" in fields and number == len(steps):
            errors.append(f"{where}: the last step cannot repeat; put the loop on the step whose check it follows")
        if "Bound" in fields:
            reachable = {item for item, step in producer.items() if step in ancestors(number)}
            named = set(NAME.findall(fields["Bound"]))
            if not named & reachable and not re.search(r"\busers?\b", fields["Bound"], re.I):
                errors.append(f"{where}: the '**Bound:**' must name an earlier output this step depends on, such as "
                              "the items or stopping condition, or a decision by the user")
        for label, allowed, wording in (
            ("On fail", ancestors(number), "an earlier step whose output it needs"),
            ("Repeat", ancestors(number) | {number}, "this step or an earlier step whose output it needs"),
        ):
            if label not in fields:
                continue
            targets = [int(target) for target in TARGET.findall(fields[label])]
            if not targets or len(targets) != len(ANY_TARGET.findall(fields[label])):
                errors.append(f"{where}: write every '**{label}:**' target as '→ step K', "
                              "and name other steps without the word 'step'")
            for target in targets:
                if target not in allowed:
                    errors.append(f"{where}: {label.lower()} returns to step {target}, which this step "
                                  f"does not depend on; return to {wording}")

    for line in text.splitlines():
        if ENTRY_LABEL not in line:
            continue
        match = ENTRY.match(line)
        if not match:
            errors.append(f"{name}: write the entry as '{ENTRY_LABEL} step K with `output`, ...' "
                          "on its own line")
            continue
        start, carried = int(match.group(1)), set(NAME.findall(match.group(2)))
        if not 1 < start <= len(steps):
            errors.append(f"{name}: enter at step {start}, which is not a later step of this playbook")
            continue
        for item in sorted(carried):
            if producer.get(item, start) >= start:
                errors.append(f"{name}: entry carries `{item}`, which no step before step {start} outputs")
        for number in range(start, len(steps) + 1):
            for item, step in needs[number]:
                if step < start and item not in carried:
                    errors.append(f"{name}: entering at step {start} skips `{item}`, which step {number} "
                                  "needs; carry it in the entry line")
    return errors


def lint_package(root=ROOT):
    folder = Path(root) / "skills/reefstack/references/playbooks"
    conventions = folder / CONVENTIONS
    if not conventions.is_file():
        return [f"missing {CONVENTIONS}: graph playbooks need its step fields and output names"]
    names = vocabulary(conventions.read_text(encoding="utf-8"))
    if not names:
        return [f"{CONVENTIONS}: no output names found; list them as rows like '| `change` | ... |'"]
    errors = []
    for path in sorted(folder.glob("*.md")):
        if path.stem not in GRAPH_PLAYBOOKS and path.name != CONVENTIONS \
                and CONVENTIONS_LINK.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path.name} links {CONVENTIONS} but is not linted; add it to GRAPH_PLAYBOOKS "
                          "in scripts/playbook_lint.py")
    for playbook in GRAPH_PLAYBOOKS:
        path = folder / (playbook + ".md")
        if not path.is_file():
            errors.append(f"missing graph playbook {playbook}.md")
            continue
        errors.extend(lint_playbook(playbook + ".md", path.read_text(encoding="utf-8"), names))
    return errors


def main():
    errors = lint_package()
    for error in errors:
        print(error)
    if not errors:
        print("playbook graphs: pass (" + ", ".join(GRAPH_PLAYBOOKS) + ")")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
