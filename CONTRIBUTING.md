# Develop Horsemen

Edit this repository. The skill and CLI have one shared checker in
`horsemen/scripts/horsemen_core/legacy.py`. The old hook entry point remains
`horsemen/scripts/horsemen.py`; keep it compatible.

## Verify

Create an isolated build environment once:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install 'setuptools==77.0.3' wheel
```

Then use one command, with a new output directory each time:

```sh
.venv/bin/python -B scripts/verify.py --output /tmp/horsemen-verification
```

It runs unit tests, source CLI tests, existing hook scenarios, a wheel build,
installed CLI tests, and hook scenarios from the unpacked skill. The result
directory contains logs, `verification.json`, the CLI wheel, and a skill ZIP
with a file manifest. Builds and tests use temporary projects. They do not
install global skills, change hook settings, or access provider accounts.

The command fails on the first unsuccessful check and retains its output.
Local results describe that machine only; CI covers Linux/macOS and Python
3.10/3.14. A configured workflow is not a passing run.

## Make a change

1. Read PROGRESS and STRUCTURE, then the relevant source.
2. Add a test for the failure or changed behavior before implementation.
3. Edit the shared source. Do not add a second checker for the CLI.
4. Run verification and review the result. Update affected project records.

Keep the skill self-contained. Its relative links must resolve within
`horsemen/`. Keep build tooling, CI, and project documentation at the repo root.
No generated package, installed copy, credential, private record, or test
output belongs in Git.

## One version, two artifacts

Change `horsemen/scripts/horsemen_core/__init__.py` for a version update.
Python package metadata and the skill builder read that value. The verifier
checks that the installed CLI reports the same version as the skill bundle.

The skill ZIP preserves its hook scripts and dependencies. The wheel contains
the executable CLI. Both come from the same source snapshot. Neither artifact
installs the other. Build with the verification command rather than assembling
release files by hand.

CI uploads test receipts and both artifacts for inspection. A release, PyPI
upload, global installation, and changes to provider documents are separate
actions. Do not claim any of them from a passing build alone.
