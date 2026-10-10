# Contributing

Reefstack should improve time to verified delivery while keeping small tasks lightweight. A change earns its place when it fixes an observed failure, resolves a real boundary, or makes verification more reliable.

## Development

Use Python 3.9 or newer. Runtime scripts and tests use the standard library; there is no dependency installation step.

```sh
python3 scripts/health.py
python3 -m unittest discover -s tests -v
python3 scripts/package.py --output ../reefstack-plugin.zip
```

Use a fresh output path for each archive. The builder refuses overwrites.

## Changes to procedures

Provide the ordinary user request and the observed failure. Explain which routing or verification decision should change. Keep role-neutral guidance in the core and Codex mechanics in the adapter. Preserve read-only discussion/review boundaries and direct handling of small edits.

Update a realistic case in evaluations/cases.json when routing behavior changes. Tests of strings or metadata do not demonstrate that an agent follows the procedure; inspect actions and artifacts in an isolated task when behavioral validation matters. For verification and review behavior, add or update a runnable case and run it with `scripts/run_evals.py` as described in [the playbook](evaluations/playbook.md); a procedure change is done when every case passes on two consecutive runs. When the same failure shows up twice, follow [enforcement](references/enforcement.md) and record it in [the failure log](docs/failure-log.md).

## Changes to hooks or scripts

Test the actual command transport and output shape, including paths with spaces, invalid input/settings, partial overrides, and disabled behavior when affected. Keep context bounded and preserve separation between root and delegated-agent instructions.

Hook trust belongs to the user and host. Do not add bypasses, mutate trust records, read unrelated transcripts, or broaden tool permissions as part of activation.

## Pull requests

Describe the concrete problem, resulting behavior, checks performed, and remaining limitations. Keep the diff focused. Do not claim native activation, deployment, or a speed improvement based solely on a package test.

Generated assets should retain clear provenance. Contributions are licensed under this repository's MIT license.
