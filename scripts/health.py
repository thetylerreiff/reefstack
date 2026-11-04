#!/usr/bin/env python3
"""Validate the skills package without claiming host installation or activation."""

import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
REFERENCES = "skills/reefstack/references/"
WORKFLOW_REFERENCES = tuple(REFERENCES + "playbooks/" + name + ".md" for name in (
    "investigation", "bug-fix", "feature", "resume", "refactoring", "performance",
    "prototype", "opening-pr", "pr-follow-up", "shipping", "graph",
))
EXPECTED_SKILLS = {"reefstack", "grill", "ground", "design", "deliver", "diagnose", "verify", "review", "setup", "map"}
# Codex refuses to load a skill whose description is longer.
DESCRIPTION_LIMIT = 1024


def inside_file(relative):
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents or not path.is_file():
        raise ValueError("invalid or missing package path: " + relative)
    return path


def check_feature_map():
    spec = importlib.util.spec_from_file_location("reefstack_map_lint", inside_file("skills/map/scripts/map_lint.py"))
    map_lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(map_lint)
    # Agents copy the template, so it must pass the lint it documents.
    errors = map_lint.lint_files(map_lint.template_files(inside_file(REFERENCES + "feature-map-template.md")))
    if errors:
        raise ValueError("feature map template fails lint: " + "; ".join(errors))
    if not (ROOT / "docs/verification").exists():
        return "not_present"
    errors = map_lint.lint_directory(ROOT / "docs/verification")
    if errors:
        raise ValueError("feature map fails lint: " + "; ".join(errors))
    return "pass"


def check_evaluations():
    spec = importlib.util.spec_from_file_location("reefstack_run_evals", inside_file("scripts/run_evals.py"))
    run_evals = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_evals)
    # Static only: case shape, fixtures, and blinding. Agent and judge runs are never started here.
    problems = run_evals.validate_suite()
    if problems:
        raise ValueError("evaluation suite: " + "; ".join(problems))


def check_playbook_graphs():
    spec = importlib.util.spec_from_file_location("reefstack_playbook_lint", inside_file("scripts/playbook_lint.py"))
    playbook_lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(playbook_lint)
    errors = playbook_lint.lint_package(ROOT)
    if errors:
        raise ValueError("playbook graphs: " + "; ".join(errors))


def local_links(path):
    # Links inside fenced examples, such as the feature-map template's, are not package links.
    text = re.sub(r"(?ms)^```.*?^```", "", path.read_text(encoding="utf-8"))
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" not in target and not target.startswith("#"):
            yield target, (path.parent / target.split("#", 1)[0]).resolve()


def check_workflow_references():
    """Require the playbooks, and keep every link under skills/ inside skills/, so the folders install on their own."""
    for relative in WORKFLOW_REFERENCES:
        inside_file(relative)
    skills = (ROOT / "skills").resolve()
    for path in sorted(skills.rglob("*.md")):
        for target, local in local_links(path):
            if skills not in local.parents or not local.is_file():
                raise ValueError("broken or out-of-skills reference in " + str(path.relative_to(skills.parent)) + ": " + target)


def check_skills():
    names = []
    for skill in sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir()):
        text = inside_file(str(skill.relative_to(ROOT) / "SKILL.md")).read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text:
            raise ValueError("missing frontmatter: " + skill.name)
        header = text.split("\n---\n", 1)[0] + "\n"
        description = re.search(r"\ndescription: (.*)\n", header)
        if f"\nname: {skill.name}\n" not in header or not description or not description.group(1).strip():
            raise ValueError("invalid skill metadata: " + skill.name)
        # Codex parses frontmatter as YAML and drops a skill it cannot parse; keep descriptions plain scalars.
        if ": " in description.group(1) or " #" in description.group(1) or description.group(1)[0] in "'\"[]{}&*!|>%@`#,?:-":
            raise ValueError(f"description of {skill.name} is not a plain YAML scalar; avoid ': ', ' #', and a leading indicator")
        if len(description.group(1)) > DESCRIPTION_LIMIT:
            raise ValueError(f"description of {skill.name} exceeds {DESCRIPTION_LIMIT} characters")
        names.append(skill.name)
    if set(names) != EXPECTED_SKILLS:
        raise ValueError("unexpected skills")
    return names


def check_package():
    manifest = json.loads(inside_file(".codex-plugin/plugin.json").read_text())
    if manifest.get("name") != "reefstack" or not isinstance(manifest.get("version"), str) or not manifest["version"].strip():
        raise ValueError("unexpected plugin identity")
    if "hooks" in manifest or (ROOT / "hooks").exists():
        raise ValueError("Reefstack is skills only; remove hooks from the package and .codex-plugin/plugin.json")
    inside_file(manifest["extensions"]["com.openai"]["onboardingSkill"])
    names = check_skills()
    check_workflow_references()
    feature_map = check_feature_map()
    check_playbook_graphs()
    check_evaluations()
    return {"package": "pass", "skills": names, "skill_links": "pass",
            "feature_map_template": "pass", "feature_map": feature_map, "evaluation_suite": "pass",
            "workflow_references": "pass", "playbook_graphs": "pass",
            "host_installation": "not_checked", "behavioral_evaluation": "not_checked"}


def main():
    try:
        report = check_package()
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"package": "fail", "reason": str(error)}))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
