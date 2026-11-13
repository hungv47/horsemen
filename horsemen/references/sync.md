# Synchronization rules

## One owner per fact

| Fact | Owner | Others may |
| --- | --- | --- |
| The declaration, why we exist, the world we are building, audience, beliefs, horizons, boundaries, how it sustains itself | VISION | README summarizes it in public words |
| Which providers play which role, the owner's setup choices, accounts, access routes, exact save destinations, write and bin permissions, access holds | BRAIN | STRUCTURE maps the brain; PROGRESS links the tracker project |
| Decisions | Where BRAIN's save rules put them (the brain, or a repository file that STRUCTURE maps) | VISION records direction changes only |
| Status of a work item, blockers, roadmap, dated updates, evidence, gates | PROGRESS | A tracker holds task detail; PROGRESS links it in a toggle |
| Repository paths, commands, where new work goes | STRUCTURE (repository map) | README repeats setup commands |
| Folders and key documents inside each provider, and how to open them | STRUCTURE (brain map) | - |
| What reached people | CHANGELOG | PROGRESS keeps latest-day ships plus Historical ships with proof |
| Pending, partly shipped, blocked, and roadmap items | PROGRESS | CHANGELOG holds only the shipped part of a partly shipped item |
| Tools, stack, resources, integrations and verified usage | TECHSTACK | README summarizes setup; STRUCTURE links commands; BRAIN owns permissions |
| Pitch for newcomers, install and use steps | README (cut down from VISION and the install guide) | STRUCTURE holds the full command list |
| Agent rules for this project | AGENTS.md | `CLAUDE.md` imports it |

When you are about to write a fact in a second place, link to the owner
instead. The only allowed copies are listed in the right column.

## Brain care

Use this proactively at task start and task end for the knowledge area the task touches, even when no code or knowledge file changed. BRAIN is the
directory; the original documents hold the knowledge.

1. Read the saved provider, account, root, exact destination, and write and
   cleanup rules in BRAIN. Follow STRUCTURE to the area needed. Initial
   interview answers remain in force; do not rely on memory or repeat the
   interview. A new user instruction can change those choices within its
   stated scope. Record a lasting change with its date.
2. Open relevant original resources, not only their map. Check current claims
   against task evidence, links, duplicates, superseded versions, decisions,
   and unresolved questions. Do not infer freshness from file timestamps.
   A full project inspection covers the in-scope brain with pagination and
   stated access gaps; routine work stays within its relevant subject.
3. Decide whether the result will help future work: a decision with its
   reason, a corrected fact, useful research, or a changed operating rule.
   Skip transcripts, task recaps, repeated facts, temporary output, and
   results already kept in their proper source.
4. Open the exact destination. Update the existing document or section.
   Create a document only when the saved rules allow a distinct subject
   and no existing original fits. Use the saved folder or parent page;
   never scatter new task documents across the brain root.
5. Check the documents in the area this task touched for copies made stale
   by this change. Retain unique facts, sources, unresolved questions, and
   history before retiring anything. Old dates alone do not mean stale.
6. Move confirmed stale copies to the configured `bin` inside that project's
   existing brain when the saved permission or current request covers the
   move. Preserve the original filename, relative location, and document ID
   where the provider supports it. Keep a dated entry in the bin's index:
   original location, bin location, reason, replacement, and how to restore.
   Avoid overwrites; keep incoming links working or update them within the
   authorized scope. A provider with pages uses the chosen `bin` parent.
7. Ask about the specific files and proposed bin when permission, ownership,
   the destination, or the effect on shared links is unclear. Keep them in
   place until answered. Never empty the bin, delete unique history, or
   move material to a different provider as routine cleanup.
8. Read back the saved section and confirm its location. Check the moved
   items and recovery index. Then update BRAIN's directory and STRUCTURE's
   map if locations changed. A mounted write proves a local save; it does
   not prove cloud sync. Report that limit when it matters.

If access fails, keep the known destination and the access hold. Do not
switch accounts or create a substitute folder. Record the unsaved result's
destination and the blocker in PROGRESS's Technical details, so the next
task can finish it without rebuilding the chat.

## State that must survive a task

| State | Where it belongs | How it stays current |
| --- | --- | --- |
| Owner's direction and agreement | VISION, including dated direction changes | Change only on request or agreed drift; a format update leaves it alone |
| Brain and tracker choices, account, root, exact save targets, write and cleanup permission | BRAIN; private registry for private IDs in a public project | Save setup answers once, with their date or source; record unresolved choices explicitly |
| Lasting decisions, reasons, and research | The exact original named by BRAIN's save rules | Update it in place; link instead of copying into records or a new session summary |
| Current work, delivery evidence, blockers, next action, unsaved knowledge | PROGRESS | Review at task end; keep old evidence dates and name who can resolve a blocker |
| Repository and brain locations, bin and restore index | STRUCTURE | Correct after a move; keep access permissions in BRAIN |
| Stale documents and unique history | Agreed bin or existing archive, with a recovery index | Preserve source and restore location; age and a paused project do not mean completion |
| Installed skill and hook paths | Host settings and the installed package; source and install procedure in repository docs | Check actual files and hook targets; a recorded install or a hook count is not current proof |
| Session baseline and prior drift reminders | Disposable hook cache, described in hooks.md | Isolate by project and session; preserve on resume; never use it as project truth or permission |

Do not add a second state registry or completion ledger. If a future agent
needs a fact, keep it at its existing owner. Clear unresolved holds only
when evidence or the user's answer resolves them.

## What changes what

| Event | Update | Then check |
| --- | --- | --- |
| Work starts | PROGRESS bullet under `In progress`, evidence row in the toggle, dated entry | - |
| Work finished, not released | Move the bullet to `Ready to ship` | - |
| Released or delivered, with evidence | Move the bullet to `Shipped`, evidence in the toggle, dated entry for stakeholders, CHANGELOG entry | README "What you get" and Use if newcomers should know |
| Part of an item delivered | Bullet to `Shipped` as `(partly shipped date)` (what is out, what is left); CHANGELOG gets the shipped part only | Gates; split the rest into its own bullet when it becomes separate work |
| Install, setup, or run steps changed | README Install and Use, STRUCTURE commands | Full install guide, if one exists |
| Blocked or decision needed | Bullet to `Blocked` or `Needs decision`, with the blocker or decider | `Health:` in the header |
| Priority changed | Move items between `Up next` and Roadmap (owner confirms) | VISION if the reason is a direction change |
| Item dropped | Remove the bullet; log "Dropped X: reason" | - |
| Folder, module, or entry point moved | STRUCTURE repository map | README commands |
| New tool, dependency, resource or integration | TECHSTACK inventory; STRUCTURE commands and paths if changed | README setup; BRAIN only if provider or access rules changed |
| Knowledge moved inside a provider | STRUCTURE brain map | BRAIN "What lives in the brain" if the location changed |
| Lasting knowledge changed without a local edit | Exact original chosen by BRAIN's save rules | Task review of all four records; local Git cannot detect this |
| Stale copy retired | Agreed bin and recovery index | References, BRAIN, and STRUCTURE if locations changed |
| Provider added or replaced, or access changed | BRAIN (owner confirms), then STRUCTURE brain map | Migrate or link old material |
| Knowledge moved from the repository to the brain, or back | BRAIN and both STRUCTURE maps | Links in other records |
| Decision made | Where BRAIN's save rules say | VISION if it changes direction or scope |
| Direction changed | VISION and Direction changes line (owner confirms) | README pitch, PROGRESS `Up next` and Roadmap, BRAIN |
| Project paused or archived | PROGRESS `Stage` and `Health`, a final log line with the true end state | VISION Direction changes |

## Detecting contradictions

`check` catches structural problems: missing records, bad states, shipped
items without evidence, stale paths, broken links, future dates, leftover
placeholders, and legacy files. It cannot catch disagreements of meaning.
When you read records for a task, also look for:

- An `Up next` or Roadmap item that VISION says the project will never become.
- A CHANGELOG entry with no matching shipped evidence, a pending or planned
  line in CHANGELOG, or a `Shipped` bullet with no
  CHANGELOG entry.
- A README pitch that VISION no longer supports, or install steps that no
  longer work.
- BRAIN listing a repository file, or VISION describing features or
  architecture.
- README describing a capability that PROGRESS does not show as shipped.
- BRAIN and STRUCTURE naming different locations for the same knowledge.
- A recorded decision that VISION or STRUCTURE contradicts.

## Resolving contradictions

1. The owner's latest explicit statement wins for intent, within its scope.
   Reuse agreement already given. Ask when the intended direction is unclear.
2. Evidence wins for facts: the repository, a release, a deployment check, or
   the original document beats any record that describes it.
3. The owning record wins over a copy. Fix the copy.
4. If the conflict changes intent or priority, ask the owner before you edit.
   Otherwise fix it, and mention the fix in your reply.
5. Never resolve a conflict by deleting the older statement silently. Keep it
   in a log line or Direction changes line when it carried meaning.

## Supporting documents

| Document | Rule |
| --- | --- |
| TECHSTACK.md | Companion inventory of tools, stack, resources and integrations: purpose, verified version or plan, usage, source/date and limits. Link BRAIN for access and STRUCTURE for commands. Never credentials, permission grants, status history or a replacement knowledge store |
| README.md | Not a record; every project keeps one. VISION and the install guide cut down to one screen: pitch, shipped capabilities, install, use, record links. No roadmap, status, or business model. Updates with VISION and with install steps |
| CHANGELOG.md | Not a record; every project that has shipped anything keeps one. Only what reached people, newest first, version and date or date headings. No `Unreleased` section; pending and partly done work stays in PROGRESS |
| CONTRIBUTING, INSTALL, deployment, architecture docs | Optional. Own their detail. STRUCTURE links each one under Other documents. Do not repeat their content in the four records |
| docs/progress-log.md | Archive of older PROGRESS log entries, unchanged, newest first |
| Decision records (in the brain, or a repository file) | Date, decision, reason, alternatives. BRAIN's save rules choose the home |
| ROADMAP, INDEX, MEMORY, STATUS (legacy) | Migrate per [adopt](adopt.md), then delete |

## Writing style

- Plain words, short sentences, active voice. One term per concept. Avoid
  business and technical jargon in PROGRESS's visible text.
- Outcomes over activity: "Consultants now sign in with Google", not
  "Worked on auth improvements".
- PROGRESS speaks to stakeholders and users. Say what people can do now and
  what waits. PR numbers, commits, branches, and checks go in the toggle.
- VISION speaks to the owner and partners as a manifesto. Say why it must
  exist, who it is for, what we believe, and the world it builds. Features
  and architecture go elsewhere.
- No repeated statements across sections. The latest-day snapshot says what changed now; Historical ships preserves
  delivered outcomes and proof; Upcoming roadmap shows future milestones.
- No preamble about authority, providers, or verification before the content.

## Shared update guarantees

Treat all four records equally carefully, not identically. For every changed
record: read the current original, make a precise proposal, retain evidence,
check current authorization, reject drift, read back the result, and leave
unrelated content and dates alone. No change means no write. Use
`scripts/records.py` with the provider-neutral engine when integrating a host.
The host verifies the meaning of evidence and owner agreement references;
nonempty text is not proof or permission. Existing checker gates still apply.

| Record | Distinct gate | Related records to review |
| --- | --- | --- |
| VISION | Owner request or agreed direction change; never infer intent from code | README pitch, PROGRESS priorities, BRAIN |
| PROGRESS | Evidence for status; delivery evidence for shipped; owner agreement for priority changes | CHANGELOG and README when delivered; VISION when priorities change |
| BRAIN | Exact original and existing save rules; owner agreement for provider or permission changes | STRUCTURE locations |
| STRUCTURE | Observed paths, commands, or provider locations; no invented map | BRAIN for moved knowledge, README for commands |

The event type and evidence must match what changed. A caller must not label
a delivery as a routine status change to avoid its evidence gate. The trusted
host checks the entire proposal. Semantic verification is not automated.
Related-record lists are review obligations, not commands to edit every file.
Prepare and authorize any resulting change separately; multi-record writes
are not atomic. If one save fails, stop affected writes and report the exact
partial state, keeping already verified evidence. Never claim a whole set
succeeded because one write did. Do not create a second completion ledger.

These guarantees run silently during ordinary tasks. User-facing updates
remain about the requested outcome. Give a record-maintenance report only
when requested; necessary permission questions and actionable blockers remain
visible. The session and stop hook instructions enforce the same wording.
