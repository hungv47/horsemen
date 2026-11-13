# Command-line guide

Read or check one project record, inspect the whole project, or apply one
explicit local edit. Python 3.10+ is required; Git is optional. The skill and
CLI share their checker and version. Nothing contacts a provider by default.

## Everyday commands

| Command | Result |
| --- | --- |
| `horsemen brain` | Read and check BRAIN.md: knowledge locations and access rules |
| `horsemen vision` | Read and check VISION.md: owner direction |
| `horsemen structure` | Read and check STRUCTURE.md: project map |
| `horsemen status` | Read and check PROGRESS.md, or legacy STATUS.md |
| `horsemen check PATH` | Validate all local records, including cross-record rules |
| `horsemen inspect PATH` | Check records and show local Git state and progress |
| `horsemen plan --help` | Setup, migration, edit proposals and review patches |

Add `--json` for machine-readable output. Named-record commands accept
`--path PATH`; otherwise they resolve the current project, including from a
subdirectory. They show the record's content and SHA256 in JSON. They do not
read other records or update dates. Their findings concern that document only;
use `check` for relationships between records, including public/private rules.
If both progress filenames contain real records, `status` fails and asks for
reconciliation. A legacy-only STATUS.md stays at that path, even on update.

`inspect` lists the current branch, changed files and registered worktrees.
It does not inspect other worktrees or query PRs, CI, deployments or providers.
Provider state is `not_checked`, even if BRAIN names Google Drive or another
knowledge home. A local BRAIN.md is a directory of knowledge, not a copy of
all its external originals. A named-record command never bulk-syncs those originals.

`--help` and `--version` need no project reads. Unknown commands fail.
The CLI does not run project scripts or install hooks.

## Update exactly one record

An update needs an explicit edit, not a request to invent fresh content:

```sh
horsemen brain --path /path/to/project --json
horsemen brain update --path /path/to/project --changes edit.json --dry-run --json
horsemen brain update --path /path/to/project --changes edit.json --exclusive --json
```

Use the same syntax for `vision`, `structure`, and `status`. The edit file is
one JSON object, not the batch format used by the older plan command:

```json
{
  "file": "BRAIN.md",
  "source_sha256": "COPY_THE_HASH_FROM_THE_READ_RESULT",
  "before": "one exact existing span",
  "after": "its reviewed replacement",
  "evidence": ["reference supporting this correction"],
  "owner_agreement": "reference to the owner's approval of this edit"
}
```

The filename must match the command. The source hash must match the complete
current UTF-8 document. `before` must occur exactly once. Empty replacement
text is allowed. Evidence is required; the CLI cannot verify its truth.
BRAIN and VISION also require an owner-agreement reference. That reference
records context; it does not authorize new provider access or override holds.
An agent must establish current permission before it invokes a saving command.

`--dry-run` validates and shows proposed content without saving. An actual
save requires `--exclusive`: the caller must ensure no other editor, agent,
sync client or process writes the target until completion. Do not use it on a
provider-mounted file or in a shared/synced directory that cannot meet that
condition. This is a local editing contract, not a provider adapter or an
approval callback. A plan or exported patch never turns into a write by itself.

The save replaces just the matched span in just the named record. It preserves
other text, CRLF/LF line endings, a missing final newline and POSIX permission
bits. No-op edits leave timestamps alone. It does not create missing records,
refresh dates, update companions or commit anything. File identity changes
on replacement; extended attributes/ACLs are not promised to be preserved.

The writer uses a per-record exclusive lock, no-follow reads, source checks,
a temporary file, atomic replacement and read-back. Existing locks, symlinks,
hard links, stale hashes, duplicate JSON keys and malformed input fail. It
cleans up its own temporary file and lock, never somebody else's lock.
A reported read-back failure after replacement means the save may already
have occurred: inspect the target before retrying.

**Concurrency limit:** atomic replacement is not compare-and-swap. An editor
that ignores Horsemen's lock can change the file between the final check and
replacement. `--exclusive` is a caller promise that prevents this situation,
not a mechanism that defeats arbitrary writers. Without that promise, use
`--dry-run` or the existing review-patch workflow. No automatic retry or
rollback is claimed. Local updates require POSIX no-follow file operations;
Windows is unsupported.

`--provider local` is the default. Other values fail before reading or writing
local content, directing you to the configured, authorized host workflow.
There is no CLI provider authentication or live remote save. The existing
Brain/records libraries retain their revision and host-authorization rules;
this local command does not weaken or bypass those adapters.

## Plans and compatibility

```sh
horsemen plan init /path/to/new-project --json
horsemen plan upgrade /path/to/project --json
horsemen plan update /path/to/project --changes changes.json --json > plan.json
horsemen plan export-patch /path/to/project --plan-file plan.json > review.patch
```

These commands never apply changes. Init identifies missing documents and
owner/provider inputs at the exact directory supplied. Upgrade proposes
STATUS→PROGRESS and TECH→TECHSTACK migration review, including both-file
reconciliation, without deleting or renaming content. Update takes the existing
`{"changes": [...]}` format: unique root `file`, exact `before`, `after`,
nonempty `evidence`, and optional `owner_agreement`. It preserves review gaps
for owner-controlled documents. Export revalidates source hashes, anchors and
proposed hashes before printing a unified patch. Shell redirection is the
caller's choice; never redirect onto an original document.

Existing `init/update/upgrade PATH --plan`, `export-patch PATH --plan-file FILE`
and `help` remain compatibility spellings. Their outputs and exit behavior
are unchanged, and none gains write behavior. They are omitted from the main
menu in favor of `plan` and `--help`. No caller was found that justified deleting
them. The original `python3 <skill>/scripts/horsemen.py` checker/hook entrypoint,
its return codes, caches and hook paths remain unchanged.

## Output and checks

JSON uses `schema_version: 1`, `command`, `status` and `report`. Named-record
results add `document`, `content`, `source_sha256`, `mode` and provider limits.
Updates add proposed content/hash. Modes distinguish `read_only`, `draft`,
and `local_update`; statuses distinguish `planned`, `updated`, `no_change`
and failures. After a save, validation can still report errors: `updated`
means bytes were saved, not that all document facts or formatting are valid.

Exit codes: 0 for a completed operation without validation errors, 1 for
validation errors, 2 for invalid input or operational failure. Legacy plans
retain exit 0 for a valid proposal even when its status is `needs_input` or
`conflict`; inspect that status. Syntax errors use argparse stderr; parsed
requests with `--json` return operational errors as JSON. Output may contain
private paths and content: keep it local.

From a checkout, replace `horsemen` with
`PYTHONPATH=horsemen/scripts python3 -B -m horsemen_core`. Run
`python3 -B horsemen/scripts/test_cli.py` for subprocess tests, or set
`HORSEMEN_CLI` to an isolated installed executable. Run
`python3 -B horsemen/scripts/test_documents.py` for simulated storage, race
and read-back failures. The full repository verifier covers source, installed
wheel, skill archive and legacy hooks; see the root CONTRIBUTING.md.

No live provider writes are used in QA. No release, merge, global installation,
background worker, new provider registry or credential store is part of this CLI.
