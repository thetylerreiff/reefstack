#!/usr/bin/env python3
"""Check that a feature map (docs/verification/) has the shape agents rely on and is not stale."""

import argparse
from pathlib import Path
import re
import subprocess
import sys


INDEX = "README.md"
INDEX_SECTIONS = ("Launch", "Features")
SECTIONS = ("What it is", "How to reach it", "Setup", "Key paths", "Success looks like")
OPTIONAL_SECTIONS = ("Gotchas", "Last checked")
KINDS = ("web", "cli", "api", "mobile", "desktop", "other")
STATUSES = ("verified", "unreachable", "blocked", "not tried")
MAX_LINES = 80
PLACEHOLDER = re.compile(r"<[^<>]*>|(TODO|TBD|FIXME)\b.*|\?+")
ENTRY = re.compile(r"^- (\w+):\s*(.*)$")
STATUS = re.compile(r"^Status: (" + "|".join(STATUSES) + r")\b", re.M)
# Inline links (optionally <bracketed> or titled) and reference definitions.
# Interpreter and runner words in front of a CLI's own command name.
LAUNCHERS = {"python", "python3", "node", "npx", "npm", "yarn", "pnpm", "uv", "poetry", "pipenv", "bundle",
             "exec", "run", "go", "cargo", "java", "-m", "--"}
PROSE = {".md", ".markdown", ".rst", ".txt", ".adoc"}
LINK = re.compile(r"\]\(<?([^)#\s>]+)>?(?:#[^)\s]*)?(?:\s+\"[^\"]*\")?\)|^\[[^\]]+\]:\s*<?([^#\s>]+)", re.M)


def sections(text):
    """Return the H1 title and an ordered list of (H2 heading, body lines, line number)."""
    title, found, current = None, [], None
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~") and fence in (None, marker):
            fence = None if fence else marker
            continue
        fenced = fence is not None
        if not fenced and line.startswith("# ") and title is None and not found:
            title = line[2:].strip()
        elif not fenced and line.startswith("## "):
            current = (line[3:].strip(), [], number)
            found.append(current)
        elif current is not None:
            current[1].append(line)
    return title, found


def is_placeholder(text):
    text = text.strip().lstrip("-").strip().strip("`").strip()
    return not text or PLACEHOLDER.fullmatch(text) is not None


def has_content(lines):
    return any(not is_placeholder(line) for line in lines)


def lint_feature(name, text):
    errors = []
    title, found = sections(text)
    if not title:
        errors.append(f"{name}: start with an H1 title naming the feature")
    if len(text.splitlines()) > MAX_LINES:
        errors.append(f"{name}: over {MAX_LINES} lines; split it into smaller features")
    headings = [heading for heading, _, _ in found]
    required = [heading for heading in headings if heading in SECTIONS]
    if required != list(SECTIONS):
        missing = [heading for heading in SECTIONS if heading not in headings]
        if missing:
            errors.append(f"{name}: missing section(s) {', '.join('## ' + h for h in missing)}")
        else:
            errors.append(f"{name}: put sections in this order: {', '.join('## ' + h for h in SECTIONS)}")
    for heading, body, number in found:
        if heading not in SECTIONS + OPTIONAL_SECTIONS:
            errors.append(f"{name}:{number}: unknown section '## {heading}'; allowed: "
                          + ", ".join(SECTIONS + OPTIONAL_SECTIONS))
        elif heading in SECTIONS and not has_content(body):
            errors.append(f"{name}:{number}: '## {heading}' is empty or a placeholder; write what an agent needs")
        if heading in OPTIONAL_SECTIONS and any(later in SECTIONS for later in headings[headings.index(heading):]):
            errors.append(f"{name}:{number}: '## {heading}' goes after the required sections")
    for heading, body, number in found:
        if heading == "How to reach it":
            errors.extend(lint_entries(name, body, number))
        elif heading == "Key paths" and not any(line.startswith("- ") and line[2:].strip() for line in body):
            errors.append(f"{name}:{number}: '## Key paths' needs at least one '- ' bullet naming a path to check")
        elif heading == "Last checked" and not STATUS.search("\n".join(body)):
            errors.append(f"{name}:{number}: '## Last checked' needs a line 'Status: <status>' with one of: "
                          + ", ".join(STATUSES))
    return errors


def lint_entries(name, body, start):
    errors, count = [], 0
    for offset, line in enumerate(body, 1):
        if not line.startswith("- "):
            continue
        count += 1
        where = f"{name}:{start + offset}"
        match = ENTRY.match(line)
        if not match or match.group(1) not in KINDS:
            errors.append(f"{where}: write entry points as '- <kind>: `handle`' with kind one of {', '.join(KINDS)}")
            continue
        handles = re.findall(r"`([^`]*)`", match.group(2))
        if not handles or any(is_placeholder(handle) for handle in handles):
            errors.append(f"{where}: empty entry point; name the real URL, command, endpoint, or screen in backticks")
    if not count:
        errors.append(f"{name}:{start}: '## How to reach it' needs at least one entry point")
    return errors


def lint_index(files):
    errors = []
    title, found = sections(files[INDEX])
    headings = {heading: (body, number) for heading, body, number in found}
    if not title:
        errors.append(f"{INDEX}: start with an H1 title naming the app")
    for heading in INDEX_SECTIONS:
        if heading not in headings or not has_content(headings[heading][0]):
            errors.append(f"{INDEX}: needs a non-empty '## {heading}' section")
    linked = set()
    features = "\n".join(headings.get("Features", ([], 0))[0])
    for target in (inline or reference for inline, reference in LINK.findall(features)):
        target = target[2:] if target.startswith("./") else target
        # Links elsewhere in the repository are context, not map entries.
        if "://" in target or "/" in target or not target.endswith(".md"):
            continue
        linked.add(target)
        if target not in files:
            errors.append(f"{INDEX}: links to missing file '{target}'; fix or remove the entry")
    for name in sorted(set(files) - {INDEX} - linked):
        errors.append(f"{INDEX}: '{name}' is not listed; add it under '## Features'")
    return errors


def lint_files(files):
    """Lint a map given as {file name: text}; returns a list of error strings."""
    if INDEX not in files:
        return [f"{INDEX}: missing; add an index with '## Launch' and '## Features'"]
    errors = lint_index(files)
    features = sorted(name for name in files if name != INDEX)
    if not features:
        errors.append("no feature files; add one short file per feature")
    for name in features:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*\.md", name):
            errors.append(f"{name}: use a lowercase-hyphenated .md file name")
        errors.extend(lint_feature(name, files[name]))
    return errors


def lint_directory(directory):
    directory = Path(directory)
    if not directory.is_dir():
        return [f"{directory}: no feature map directory"]
    files = {path.name: path.read_text(encoding="utf-8") for path in sorted(directory.glob("*.md"))}
    return lint_files(files)


def template_files(path):
    """Extract the README and feature examples fenced in the feature-map template."""
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.findall(r"^```markdown file=(\S+)\n(.*?)^```$", text, re.M | re.S)
    if not blocks:
        raise ValueError("template has no ```markdown file=<name> examples")
    return dict(blocks)


def entry_handles(text):
    """Yield (kind, handle) for every backticked handle under '## How to reach it'."""
    for heading, body, _ in sections(text)[1]:
        if heading != "How to reach it":
            continue
        for line in body:
            match = ENTRY.match(line)
            if match:
                for handle in re.findall(r"`([^`]+)`", match.group(2)):
                    yield match.group(1), handle


def handle_tokens(kind, handle):
    """Source literals a handle depends on: route paths, command words, or the label itself."""
    handle = re.sub(r"\b[a-z][a-z0-9+.-]*://[^/\s`]*", "", handle)  # keep only the path of a full URL
    # A route cut short by a parameter (<id>, {id}, :id, [id]) keeps its static prefix, like "/items/".
    paths = [path for path in re.findall(r"(?<![\w.])/[^\s`<{:\[?#]*", handle) if path != "/"]
    if paths:
        return paths
    if kind == "cli":
        words = []
        for word in handle.split():
            if not re.fullmatch(r"-{0,2}[A-Za-z][\w-]*", word):
                break
            if word not in LAUNCHERS:
                words.append(word)
        return words
    return [handle.strip()]


def static_part(literal):
    return re.split(r"[<{:\[]", literal, maxsplit=1)[0]


def quoted_literals(text):
    return {match[1] for match in re.findall(r"([\"'`])([^\"'`\n]{1,200})\1", text)}


def git(repo, *args):
    run = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if run.returncode:
        raise ValueError("git " + " ".join(args) + " failed: " + run.stderr.strip())
    return run.stdout


def stale_entries(directory, base):
    """Map handles whose source literal the change since base removed from every code file."""
    directory = Path(directory).resolve()
    repo = Path(git(directory, "rev-parse", "--show-toplevel").strip())
    map_path = directory.relative_to(repo).as_posix()
    diff = git(repo, "diff", "--unified=0", base, "--", ".", ":(exclude)" + map_path)
    removed = {static_part(literal) for literal in quoted_literals("\n".join(
        line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")))}
    current = set()
    for name in git(repo, "ls-files", "-co", "--exclude-standard", "-z").split("\0"):
        path = repo / name
        # Prose that still mentions an old route does not keep it alive.
        if (not name or name.startswith(map_path + "/") or path.suffix.lower() in PROSE
                or not path.is_file() or path.stat().st_size > 1_000_000):
            continue
        data = path.read_bytes()
        if b"\0" in data:  # compiled or binary files are not source
            continue
        current |= {static_part(literal) for literal in quoted_literals(data.decode("utf-8", errors="ignore"))}
    errors = []
    for feature in sorted(directory.glob("*.md")):
        if feature.name == INDEX:
            continue
        for kind, handle in entry_handles(feature.read_text(encoding="utf-8")):
            for token in handle_tokens(kind, handle):
                if token in removed and token not in current:
                    errors.append(f"{feature.name}: entry `{handle}` names '{token}', which this change removed "
                                  "from the source; update the map entry in the same change")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/verification")
    parser.add_argument("--since", metavar="BASE",
                        help="also flag entry points whose route, command, or label the change since BASE removed")
    args = parser.parse_args()
    try:
        errors = lint_directory(args.directory)
        if args.since and Path(args.directory).is_dir():
            errors += stale_entries(args.directory, args.since)
    except (OSError, UnicodeError, ValueError) as error:
        errors = [f"{args.directory}: cannot read map: {error}"]
    for error in errors:
        print(error)
    if errors:
        return 1
    print(f"{args.directory}: feature map ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
