# Horsemen commands

These are agent commands, not shell commands. The optional standalone CLI
has a deliberately narrower [command contract](cli.md); do not conflate them. Say `horsemen init` or invoke
`$horsemen init` in a host that supports skill invocation. Accept `horsmen`
as a conversational spelling alias. Do not install the optional CLI without authorization or pretend that
`python3 horsemen.py init` runs this workflow. The legacy Python script implements
`check`, internal `hook`, and `hooks install/uninstall/status` only.

## Route the request

Route `help` and unknown commands before project discovery; do not read project
records or providers just to show the menu. `check` only reads local records.
For other commands, resolve the named project, or use the current project. Ask only if the target
or consequential scope is ambiguous. Read its applicable instructions and
saved provider boundaries first. Unknown commands show the help menu and ask
which command was intended; they never fall through to a write operation.

Each command grants no new permission to share, publish, delete, connect an
account, change VISION or bypass provider write holds. Preserve concurrent
edits, unique owner content and unchanged dates. A denied action stops that
action; finish independent work. An uncertain write requires a fresh read
before any retry. Never claim a provider save from a local file or cache.

### brain / vision / structure / status

Read/report just the named record by default: BRAIN.md, VISION.md, STRUCTURE.md,
or PROGRESS.md (legacy STATUS.md where applicable). No writes, bulk sync,
companion refresh or provider-original updates. This read-only boundary overrides
routine maintenance. Report missing content and access limits, not invented facts.

An explicit `horsemen brain update` (likewise the other names) authorizes only
that record's update within current saved permissions. Read its original, gather
required evidence, verify owner direction/provider holds where relevant, and
replace only the supported changed content. Preserve all other records and dates.
Mention downstream work if useful; do not perform it within this narrow request.
If the original is provider-backed, use its configured authorized host adapter;
never substitute a local copy. Fail clearly if input or provider access is missing.
Distinguish a draft from a verified save. No live real-document writes during QA.

The executable CLI uses `COMMAND --path PATH` and an explicit
`COMMAND update --changes FILE --exclusive` local path. It requires an exact
source hash and replacement, not autonomous content generation. Use `--dry-run`
for review. Do not assert `--exclusive` unless no other editor or sync process
can write the file during the save. Provider originals remain a host workflow;
see [CLI parity](cli.md). Existing Brain adapter revision/authorization rules stay intact.

### init

Set up missing VISION, PROGRESS, BRAIN, STRUCTURE, README, CHANGELOG and
TECHSTACK using the [initialization procedure](../SKILL.md#initialize).
Use verified project evidence. Ask for missing owner intent and provider
choices rather than inventing them. Existing records are inputs, not files
to replace. When records already exist, check gaps and offer `upgrade` for
format migration. Repeating init with complete records is a no-op.

### update

Reconcile changed facts using [sync](sync.md) and the task-end review.
Check the four records, all companions and relevant original Brain resources.
Update only supported changes, within existing permissions. Do not rewrite
VISION from implementation drift. Keep denied or unsupported saves visible;
no substitute Brain, automatic provider switching or duplicate originals.
Routine upkeep is silent. An explicit update request gets a short result,
not a compliance checklist. No change means no date refresh.

### upgrade

Bring project documents to the current Horsemen contract through
[adoption](adopt.md). This does not update the installed Horsemen package,
software dependencies or runtime hooks. Inventory legacy content first.
Preserve unique facts, original dates, VISION and permission restrictions.
For TECH.md migration, if both files exist, reconcile unique owner content
before any authorized removal. Fix inbound links and check the result.
Repeated upgrades are no-ops once the contract is met. Do not replace owner
sections with a template just to achieve uniform formatting.

### inspect

Read-only project review using the inspection steps in
[inspect and proceed](inspect-and-proceed.md). Plain `inspect` does not
authorize record maintenance or implementation of recommendations. Inspect relevant records, originals, worktrees, branches,
PRs, tracker and delivery evidence; disclose stale, partial or blocked reads.
Return the current picture, ranked next steps and proposed corrections.
No record edits, cleanup, new diagrams, provider writes or Git changes.
This command's read-only boundary overrides routine maintenance instructions.

### inspect-and-update

Aliases: `inspect and update` and legacy `inspect and proceed`.
Inspect the whole in-scope project, then perform evidence-backed record maintenance
using the [inspection procedure](inspect-and-proceed.md) and `update` rules.
This preserves the original inspect-and-proceed workflow; plain `inspect`
is the separate read-only option.

Reconcile the four records, companions and relevant Brain originals within
existing permissions. Re-read each target before applying precise changes;
preserve concurrent edits, unchanged facts/dates and owner VISION. Respect
provider write holds and verified read-back requirements. If an original
cannot be safely updated, report the unsaved change and continue independent
work. Do not create a substitute original or claim a blocked save succeeded.

No code changes, Git-state changes, installs, automatic publication, merge,
deployment or implementation of recommended tasks. Keep proposed priorities
separate from the agreed roadmap. Report material factual corrections,
blocked saves and ranked next steps, not a routine maintenance checklist.

### check

Validate local records without editing them. Run
`python3 <skill>/scripts/horsemen.py check <project> --json` and explain errors
and useful warnings. Validation is not a live-provider audit or proof that
features shipped. Fixing findings is a separate `update` or `upgrade` scope.

### diagram

Explain a named topic or the project's connections. Verify the facts and
find the existing visual first through STRUCTURE and the owning documents.
Preserve the existing format and canonical location unless the user requests
a change. Reuse the current view for the same question; no duplicate v2 files.

- **Mermaid:** Small, text-based connection or flow diagrams in the owning
  Markdown document. Keep runtime traffic separate from development/release.
- **Excalidraw:** Editable explanations through the existing `show-me-bro`
  skill. It owns scene creation, rendering, topic discovery and visual QA.
  Horsemen supplies the verified facts and approved destination. Do not
  implement a second renderer or hard-code another skill's installation path.
- **pele.run:** No verified adapter is included. Do not send project data to
  it or imply support. If requested, verify its current input, export,
  privacy and sharing behavior before proposing an authorized integration.

Honor an explicit format choice. For a new lightweight Markdown flow, use
Mermaid; for a richer editable view use Excalidraw. If the required renderer
is unavailable, report the limit; offer another format instead of silently
replacing the existing artifact. Render and inspect changed visuals when the
renderer is available. Syntax checks alone are not proof of readability.

Keep diagrams factual and small, with named components and labeled arrows.
Mark planned or unknown edges, not invented infrastructure. Link the same
visual from TECHSTACK and STRUCTURE rather than keeping duplicate diagrams.
Do not publish private data, upload to a hosted renderer, or create a public
share without applicable approval. Store code-bound diagrams with the code;
other knowledge follows BRAIN's existing source and permission rules.
A remote artifact needs verified destination read-back. If saving is blocked,
report what remains unsaved; do not call a local preview a successful save.

### help

Show this short menu and one example, without reading private project data:

| Command | Result |
| --- | --- |
| brain / vision / structure / status | Read one record; add `update` for an explicitly scoped edit |
| init | Set up missing project records |
| update | Refresh changed facts and relevant Brain originals |
| upgrade | Migrate project documents without losing content |
| inspect | Read-only status and ranked next steps |
| inspect-and-update | Inspect, refresh authorized records, recommend next steps |
| check | Validate local records; do not fix them |
| diagram | Explain connections in an existing or requested visual |
| help | Show these commands |

Example: `horsemen brain` (read only), then `horsemen brain update` for a scoped change.
No command implies merge, deployment or installation. Ordinary background
maintenance stays silent; direct requests receive the useful result, and
necessary permission questions or actionable blockers are never hidden.
