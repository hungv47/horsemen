# Inspect and proceed

A fresh project picture and a recommended next move, especially at the start
of a session. Work from current evidence, not the previous session's summary.
Choose the mode explicitly:
- Plain `inspect` is read-only. Do not write records or provider originals,
  change code or Git state, create visuals, or perform cleanup. This boundary
  overrides routine task-end upkeep. List proposed corrections instead.
- `inspect-and-update`, `inspect and update`, and legacy `inspect and proceed`
  inspect first, then apply evidence-backed record maintenance within existing
  permissions. Use the compound command's preservation and verification rules
  in [command routing](commands.md#inspect-and-update).
Neither mode turns a recommendation into an owner's decision or authorizes
code changes, Git-state changes or implementation of recommended tasks.

## Establish the boundary

Resolve the current project from the user's target, repository root, and
STRUCTURE. Read applicable AGENTS instructions and all four records, including
PROGRESS's snapshot, gates, and Next action. A hook snapshot is orientation,
not a substitute for this review. For legacy projects read STATUS; identify
missing records without inventing VISION or providers.

Use STRUCTURE and BRAIN to identify related repositories, submodules, trackers,
release/deployment sources, and relevant outside knowledge. Inspect only this
project's sources, not every account or repository on the machine. Confirm an
ambiguous project boundary before broadening it. A non-Git project still gets
the records, deliverables, tracker, and blockers reviewed; mark Git sections
not applicable.

## Collect the current picture

Prefer supported read-only connectors and installed tools. Record the check
time and source. Do not silently treat a limited page of results as complete.

- **Worktrees:** Enumerate every registered worktree (`git worktree list
  --porcelain`), including locked, missing, prunable, and detached entries.
  Inspect each accessible worktree independently, without switching it. Note
  its path, branch/HEAD, staged and unstaged changes, untracked files,
  conflicts, and any merge/rebase/cherry-pick in progress. Summarize changed
  files and diffs enough to identify the work and overlapping edits. Treat
  untracked files as work to preserve; do not execute them or print secrets.
  Report inaccessible entries rather than pruning or repairing them.
- **Branches and saved work:** Enumerate all local and remote-tracking refs,
  upstreams, and stashes. Compare local heads with their upstream and the
  verified default branch: ahead/behind, unique commits, and no-upstream or
  gone-upstream branches. Do not assume the default is `main` or `master`.
  Local remote-tracking refs can be stale. Use a live remote/API read to
  confirm heads; if commits needed for comparison are absent, report the
  limit rather than invent counts. Fetch only when separately authorized,
  without prune, reset, checkout, or changes to the working files. No branch
  or stash is disposable just because it looks old or appears merged.
- **Pull requests:** Enumerate all open PRs for each in-scope repository,
  including drafts, with pagination. Match worktree/branch heads to PR head
  SHAs. Check relevant merged/closed PRs when explaining local leftover work.
  For each open PR, inspect purpose, base/head, current checks, reviews,
  unresolved feedback, merge/conflict state, and dependencies on other PRs.
  Distinguish required checks from optional ones, stale checks from checks
  on the current SHA, and unknown mergeability from an actual conflict.
  No PR access means unknown, not zero PRs.
- **Project state:** Check active issues and commitments in the configured
  tracker, relevant releases/deployments, tests or CI already recorded, and
  the project documents needed to explain blockers and dependencies. Follow
  BRAIN's account, scope, and write holds. Do not crawl the whole backend.
  Read existing test evidence first; this mode does not authorize installs,
  migrations, deployments, costly jobs, or running untrusted project code.
  Say which checks ran now, were only read, failed, or were unavailable.

Cross-reference worktrees, branch heads, PRs, issues, and shipped artifacts.
Identify duplicated efforts, overlapping dirty files, unpushed work, missing
reviews, failing gates, and disagreements with the recorded plan. Large
inventories may be grouped for readability, but retain counts and disclose
anything not inspected. If one source is unavailable, finish independent
checks and state what that gap prevents you from concluding.

## Review the Horsemen and companions

- **VISION:** Does current work serve the confirmed direction? Flag drift or
  unconfirmed intent; do not rewrite the owner's direction to fit the code.
- **PROGRESS:** Reconcile shipped, active, blocked, and next work with actual
  evidence. A merge or green CI is not proof of delivery. Keep proposed
  priorities separate from the agreed Next action and roadmap.
- **BRAIN:** Open relevant originals, not just routes. Check stale claims,
  broken links, duplicates, superseded versions and unresolved decisions.
  Identify needed corrections and recoverable cleanup. Plain inspect only
  proposes them; compound mode applies them only within saved permissions.
  Note missing destinations and access holds. Do not imply that an
  unqueried provider was checked or create a replacement knowledge store.
- **TECHSTACK:** Reconcile tools, stack, resources and integrations with manifests,
  configuration and observed usage. Distinguish installed from connected and
  tested; link access rules in BRAIN and keep unknowns explicit.
- **STRUCTURE:** Verify relevant repository/worktree entry points, commands,
  and brain locations. Do not add transient worktrees as permanent structure.

In plain inspect, list maintainable fact corrections without writing them.
In compound mode, apply supported corrections under the update rules and run
the record checker afterward. Check README and CHANGELOG when their sources
changed. The local record checker itself is read-only.
Do not refresh dates or create an audit file merely to prove a review happened.

## Recommend the next move

Return a concise decision brief, expanding the inventory only when useful:

1. **Current picture:** what is live, what is active, what is at risk. Include
   worktree/branch/PR counts and material dirty or unpushed work.
2. **Recommended next step:** one concrete action, why it comes first, its
   target branch/worktree/PR, dependencies, and how success will be verified.
3. **Then:** a few ranked follow-ups with the reason and any decision needed.
4. **Limits:** unknowns, unavailable sources, stale evidence, and record drift
   that changes the recommendation. Link precise evidence where available.

Separate facts, inferences, and recommendations. Prefer unblocking existing
work and preserving unfinished changes over starting duplicate work. State
when the agreed Next action differs from the recommendation; let the owner
choose a priority change. Do not turn suggestions into assigned tasks,
roadmap commitments, or actions. Continue implementation only when the user's
request separately authorizes that specific work. Inspection alone never
permits merge, push, deployment, branch/worktree deletion, stash application,
reset, or cleanup, including work created by another session.
