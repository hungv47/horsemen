# Local CLI prototype

An independently runnable, read-only CLI backed by the existing Horsemen
checker and Git helpers. This is an isolated prototype, not a published release.
It has no runtime dependencies beyond Python and optional Git.

## Try it without installing

From this checkout:

    PYTHONPATH=horsemen/scripts python3 -B -m horsemen_core --help
    PYTHONPATH=horsemen/scripts python3 -B -m horsemen_core check /path/to/project --json
    PYTHONPATH=horsemen/scripts python3 -B -m horsemen_core inspect /path/to/project --json

`check` preserves the existing checker rules. `inspect` adds the local progress
snapshot, current HEAD, branch, changed files and registered worktree listing.
It does not inspect other worktrees, fetch, contact providers or read PR/CI data.
Remote and provider states always say `not_checked`. Detached HEAD has a null
branch. Other null Git fields mean unavailable or not applicable.

`help` and `--version` do not read project data. Unknown/unimplemented commands
fail without writing. The CLI does not execute project scripts or run hooks.

JSON uses `schema_version: 1`, `command`, `status` and `report`. The legacy
checker report is nested unchanged under `report`. Exit codes: 0 means no
validation errors, 1 means validation errors, 2 means invalid invocation or
an operational error. Warnings alone do not fail. Argument syntax errors use
argparse's stderr output; valid invocations with `--json` use JSON for results
and operational errors. Output may include private local paths and record
content: do not upload or log it publicly.

## Package and test in a virtual environment

    python3 -m venv /tmp/horsemen-cli-test
    /tmp/horsemen-cli-test/bin/python -m pip wheel ./horsemen --no-deps -w /tmp/horsemen-wheels
    /tmp/horsemen-cli-test/bin/python -m pip install --no-index --no-deps /tmp/horsemen-wheels/horsemen_local_prototype-0.1.0a5-py3-none-any.whl
    HORSEMEN_CLI=/tmp/horsemen-cli-test/bin/horsemen python3 -B horsemen/scripts/test_cli.py

The build backend downloads setuptools from the official package registry if
needed. Do not install globally. The declared floor is Python 3.10; this
prototype was tested on Python 3.14 on macOS, not a version/platform matrix.

## Compatibility and limits

`scripts/horsemen.py` remains the existing checker/hook entrypoint. It delegates
to `horsemen_core/legacy.py`, which retains the existing behavior and adds tested support for the latest-day,
historical-ships and roadmap layout.
Importers share the same module globals, including the hook deadline. Old
script command syntax, return codes, caches and hook paths remain intact.
The new CLI does not install or alter host hooks.

The package exposes check/inspect/help and plan-only init/update/upgrade. The skill retains
init/update/upgrade/inspect-and-update/diagram workflows. Do not interpret
standalone local `inspect` as the skill's full connected-project inspection.
Missing work includes deeper lifecycle planning, an approval bridge, guarded writes,
provider authentication, remote inspection and CLI diagram integration.
The existing Brain/records/Docs modules remain in the skill, unchanged and
not included in this first wheel. Drive Markdown writes remain unsupported.
No database, duplicate provider registry, credential store or background
service was added.

Run `test_cli.py` both from source and against the built wheel, then the
existing `test_techstack.py`, `test_commands.py`, engine tests and `e2e.py`.
The latter verifies old hooks through the compatibility wrapper.

## Lifecycle plans (never apply)

    horsemen init /path/to/new-project --plan --json
    horsemen upgrade /path/to/project --plan --json
    horsemen update /path/to/project --plan --changes /path/to/changes.json --json

The explicit `--plan` flag is required. Init uses the exact directory supplied,
not an existing parent project. It lists missing documents and unresolved
inputs without generating owner intent or provider choices. Existing files
are preserved. Upgrade proposes review of STATUS→PROGRESS and TECH→TECHSTACK,
including both-file reconciliation, and lists checker findings. It does not
rename/delete files or pretend to migrate every old prose format.

Update needs a JSON object with a `changes` array. Each entry has `file` (a
supported root document), `before` (one exact nonempty anchor), `after`, and
a nonempty `evidence` array of references. Optional `owner_agreement` is only
a reference, never permission. Repeated targets, path traversal, symlink
targets, unsupported fields and malformed edits fail. Original and proposed
hashes describe a snapshot, not executable approval. VISION, BRAIN and agent
instruction changes flag an owner/permission review gap. No supplied edits
is not proof of freshness.

Plan states: `no_change`, `planned`, `needs_input`, `conflict`. Exit 0 means a
valid plan was produced, even with gaps/conflicts. Inspect the plan status;
it never means edits were applied or facts verified. Invalid input exits 2.
Plan output can contain private text: keep it local. There is still no
inspect-and-update writer, provider connection or approval bridge.

Version 0.1.0a5 was built offline using cached setuptools 84.2.1 and tested
inside an isolated virtual environment. No global install or network needed.

## Local application safety decision

Automatic local application is intentionally not implemented. There are two
separate missing guarantees:

1. **Current authorization.** The CLI has no trusted host callback that can
   verify the user approved the exact target, content and scope under current
   holds. A plan, owner-agreement reference, file, environment variable or
   `--yes` cannot supply that authority. The existing Brain library has a
   callback interface, but no standalone CLI bridge is wired to it.
2. **Conditional writes.** The local adapter has no filesystem operation that
   replaces an arbitrary existing Markdown file only if its current bytes
   still match the reviewed snapshot. Reading a hash and then using atomic
   replacement has a race between the check and replacement. Advisory file
   locks do not protect against editors that do not honor the same lock.
   Read-back detects an outcome after the fact; it cannot restore a concurrent
   edit that has already been overwritten. Snapshot hashes alone do not solve
   this. Multiple files add partial-completion and recovery problems.

The tests include a deterministic interleaving in disposable files proving
that read/check/replace can overwrite a concurrent edit. They also prove that
apply/yes flags and approval fields do not enable writes, a late invalid batch
item does not partially apply earlier items, mixed valid/conflicting changes
leave both originals intact, stale-anchor replanning fails, and no-op planning
preserves timestamps and file permissions. These prove the current fail-closed
boundary, not a working transaction engine.

Next implementation checkpoint: choose and verify a trusted approval transport
and a storage/write primitive with real revision preconditions. A constrained
editor protocol would need an explicit exclusive-writer contract; it must not
be advertised as safe for arbitrary concurrent editors. Until then, use the
plans for human review and application outside this CLI. No local/cloud write
fallback, automatic retry, rollback claim or new permission source is added.

Reproduce safety checks with `python3 -B horsemen/scripts/test_cli.py` or set
`HORSEMEN_CLI` to the isolated installed executable for the same tests.

## Export a review patch

    horsemen update /path/to/project --plan --changes changes.json --json > plan.json
    horsemen export-patch /path/to/project --plan-file plan.json > review.patch

Shell redirection is your choice of output destination; the CLI only writes
to stdout. Choose a new review filename, not an original document. It never
opens or overwrites an output file, applies a patch, creates a branch or commit,
or changes the original project. Plan and patch text may contain private data.

Export accepts only a nonconflicting version-1 update plan for the resolved
project. It rechecks every current source hash, unique anchor, proposed hash,
allowed filename and action before emitting any patch bytes. Duplicate JSON
keys, repeated targets, unsupported fields and symlinks are rejected. No-op
plans emit an empty patch. Unknown init/upgrade prose migrations cannot be
exported as if they were exact edits. Owner-review gaps remain gaps; exporting
a diff neither verifies evidence nor authorizes application.

Reads use directory descriptors and no-follow opens on supported platforms.
This prevents final-component symlink following, not every possible hostile
filesystem race. Hash checks describe the source snapshot read during export.
A later edit can make the patch stale. UTF-8, CRLF and missing final newlines
are preserved and tested by applying patches only in disposable fixtures.
The CLI still performs no conditional filesystem or provider writes.

Staging remains separate future work: review the patch in an isolated worktree,
validate changes there, and explicitly choose any later integration. This
prototype never creates project branches or review commits automatically.

## Release review

See [CLI/skill parity and release gates](references/cli.md). The standalone CLI
disables configured Git fsmonitor and clean/process helpers during its local
inspection; existing legacy hook scripts are unchanged. New tests cover this
boundary and LF-only diff line splitting for Unicode separators. CI verifies
source and built-wheel behavior on Linux/macOS and Python 3.10/3.14. No upload,
release, auto-merge or global-install workflow exists.

Progress presentation: new documents use three toggled parts with readable
Markdown headings. Latest-day snapshots exclude history and roadmap; historical
ships retain delivery proof and remain recognized by shipment checks. Existing
layouts stay supported, and owner VISION is never rewritten for a style refresh.
