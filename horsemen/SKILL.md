---
name: horsemen
description: Set up and maintain VISION, PROGRESS, BRAIN, and STRUCTURE, with README, CHANGELOG, and TECHSTACK. Use before project work and before finishing each project task, including discussions and work outside Git, or for "horsemen init/update/upgrade/inspect/inspect-and-update/check/diagram/help", "inspect and proceed", project status, adoption, handoff, knowledge filing, or "horsemen". Preserve the owner's direction, update progress from evidence, and keep knowledge in its agreed location. Legacy STATUS.md is PROGRESS.
---

# Horsemen

The four records let a person or an agent with no context understand a
project in minutes, without rebuilding it from chats and scattered files.
They live as Markdown files at the project root, for every kind of project:
software, business, growth, research, or personal.

| Record | Answers | Written for | Owns | Does not own |
| --- | --- | --- | --- | --- |
| VISION.md | Why must this exist, and what world does it build? | Owner, partners, investors | The manifesto: declaration, why we exist, the world we are building, who we build for, what we believe, how we get there, what we will never become | Features, specs, architecture, decisions, status |
| PROGRESS.md | What shipped, what is in the pipeline, what waits? | Stakeholders and users first; technical details in toggles | Status bullets per item, roadmap, dated updates, evidence and gates (in toggles) | Direction, specs |
| BRAIN.md | What do we know outside the repository, and how do we reach it? | Agents and the team | Providers (Markdown folder, Obsidian, Drive, Notion, ...), what each holds, where past discussions with agents live, access routes, save rules, access holds | Repository files, folder trees |
| STRUCTURE.md | Where is everything? | Agents and builders | Repository map (code, commands, where new work goes) and brain map (folders and key documents per provider, how to open them) | Access rules, status |

VISION is the project's manifesto: the grand mission in the owner's voice,
not a PRD, an ADR, or a plan. Make it ambitious, entrepreneurial and grounded
in real value; adapt business sustainability to mission, impact and funding for
nonprofits. Never invent owner intent or turn inspiration into unsupported claims.

PROGRESS has three toggled parts: the latest day (shipped, up next, decisions
and relevant active work), historical ships with delivery proof, and the
upcoming roadmap. Use plain language and Markdown headings that remain readable
without HTML. BRAIN and STRUCTURE split
knowledge this way: BRAIN says which providers exist, what each holds, and
how to get in; STRUCTURE shows how the repository and each provider are
organized inside.

Three supporting documents are not records, but every project keeps them and
they change whenever their sources change:

| Document | What it is | Updates when |
| --- | --- | --- |
| README.md | VISION and the install guide, cut down to one screen: what it is, who it is for, how to install or reach it, how to start | VISION's pitch or audience changes; install or run steps change; a capability ships that newcomers should know |
| TECHSTACK.md | Current tools, stack, resources and integrations: purpose, verified version or plan, source, and limits | A tool, dependency, integration, resource, or its usage changes |
| CHANGELOG.md | Only what reached people, newest first. Never pending, half-done, or planned work | A PROGRESS item becomes `Shipped` or `Partly shipped` (the shipped part only) |

PROGRESS covers more than CHANGELOG: pending, partly shipped, blocked, and
roadmap items as well as shipped ones. Optional guides (CONTRIBUTING, a full
install or deployment guide) are linked from STRUCTURE and README. Published
team guides use the destination and available document tools named by BRAIN.

## Orient before you act

1. Before any project work, read the PROGRESS latest-day snapshot with Next action and Gates
   (for legacy layouts, everything above the first dated heading) and STRUCTURE's "Read
   before changing" section. The session-start hook injects both; read them
   yourself only if they were not injected or the injection says it is
   incomplete. In a legacy project, read STATUS.md in full instead.
2. Read VISION before a decision about scope, priority, or design.
3. Read BRAIN before you search for, cite, or save knowledge outside the
   repository.
4. Read STRUCTURE before you create, move, or look for code, folders, or
   documents, in the repository or in the brain.
5. Open only the section you need. Follow links for detail. Do not load a
   whole knowledge backend to answer one question.

## Commands

Use [command routing](references/commands.md) for `horsemen init`, `update`,
`upgrade`, `inspect`, `inspect-and-update`, `check`, `diagram` and `help`. These are agent workflows,
not additional legacy Python script commands. The optional standalone CLI
implements a smaller deterministic subset; see [CLI parity and release gates](references/cli.md).
`horsmen` is a conversational alias.
`inspect` and `check` are read-only; their boundaries override routine upkeep.
`upgrade` migrates project documents, not the installed skill or dependencies.

## Inspect and proceed

Invoke with `$horsemen inspect and proceed` (or “Use Horsemen to inspect and
proceed in this project”). This is a conversational mode, not a shell command.
Use it for a full session-start review or when the user asks what to do next
across the project. Follow [inspect and proceed](references/inspect-and-proceed.md).

Inspect all project worktrees, branches, PRs, and changes, plus the project
state routed by the records. Review the four Horsemen against that evidence,
then give a short, ranked recommendation. `inspect and proceed` preserves the
original inspect-and-update workflow: refresh supported record facts within
saved permissions, then recommend next steps. Plain `inspect` is read-only.
Neither mode authorizes code/Git changes or implementation of recommendations.
Ordinary sessions still use the lightweight orientation above; hooks do not
run this broader inspection. This explicit report is an exception to routine
silent maintenance below.

## Maintain the brain as well as the code

At task start, inspect the existing originals relevant to the work, not just
BRAIN's directory. At task end, proactively check that same area even if no
code changed. Follow [brain care](references/sync.md#brain-care): verify facts,
links, duplicates, superseded versions, decisions, and unresolved questions;
update the original and clean up within saved permissions. Do not wait for
a separate brain-audit request. A project-wide inspection checks the whole
in-scope brain with pagination and stated gaps, not unrelated accounts.

A directory check is not a content check. An old date is not proof that a
resource is wrong. Preserve unique history and recovery paths. Routine
maintenance grants no new sharing, deletion, provider, or account permission
and does not override a write hold. Ask for missing approval or report the
exact blocked save. Keep PROGRESS useful for catching up: changed outcomes
and open blockers with links to originals, not a maintenance activity log.

TECHSTACK is a companion, not a fifth Horseman or a second BRAIN. It describes
the full stack, tools, integrations and resources in use and their purpose. Cover frontend,
backend, data, infrastructure, testing and developer tools where applicable;
mark unused layers and unknowns rather than inventing a stack. BRAIN still owns account scope,
authorization and knowledge destinations; STRUCTURE owns paths and commands.
Link to those owners instead of copying their rules. Never record secrets.
Keep TECHSTACK concise enough for a junior to middle-level engineer. For each
tool, explain the project need, what it needs to work, and how it helps.
Use short plain-language descriptions; link detailed setup and evidence.

## Work silently

Perform routine orientation, record review, checks, and maintenance silently.
Keep the final response about the user's actual task. Do not add a Horsemen
checklist, compliance receipt, maintenance summary, or “all four reviewed”
section unless the user asks for that report. Silence does not waive a needed
permission question or hide an actionable blocker or unsaved result. Mention
only the concrete consequence for the task, not the skill's internal steps.

## Before finishing each task

Review all four records against what the task changed. This applies to code,
research, discussions, decisions, and work in outside tools, even without a
commit or local edit. Read the relevant current sections; chat memory and a
hook's silence are not proof that the records are current.

| Record | Check and act |
| --- | --- |
| VISION | Keep it unchanged during routine work, including format upgrades. Update only when the user asks for a revision or has agreed to a direction change during the task. If the work drifted without that agreement, flag the conflict and ask before changing intent. Reuse confirmation already given; do not ask again |
| BRAIN | Reuse the setup choices and filing rules from the initial interview. Save only useful, lasting knowledge; update the exact original document, not a new task summary. Check stale material in the area touched by this task and use the agreed bin or ask about the specific cleanup. Follow [brain care](references/sync.md#brain-care) |
| PROGRESS | Record changed results, work that remains, and blockers in straightforward words. Avoid business and technical jargon. Keep evidence in the toggle and distinguish finished work from delivered work |
| STRUCTURE | Fix changed paths, commands, entry points, and brain locations. Include document moves and bin locations when they affect how people find things |

Check README, CHANGELOG, and TECHSTACK when their sources changed. Run `check` after
record edits. If nothing worth recording changed, leave files and dates alone.
If a needed save is blocked, record the exact destination and what remains
unsaved in PROGRESS's Technical details; report it in the handoff. Do not
create a substitute brain or claim the save succeeded.

Hooks remind; the agent performs this review. Hosts without hooks use the
same rule through AGENTS.md. Do not add a task receipt, a new document, or a
user-facing checklist just to prove the review happened.

## Lifecycle

| Situation | Do this | Enforced by |
| --- | --- | --- |
| New project | [Initialize](#initialize) | User asks, or agent offers once (hook hint) |
| Existing project without current records | [Adopt](references/adopt.md) | Hook health lines; agent offers |
| Vision unclear, contradictory, or unconfirmed | [Vision interview](references/interviews.md#vision-discovery) before you finalize VISION | User answers |
| Brain or task tracker undefined, unreachable, or holding less than BRAIN claims | [Provider interview](references/interviews.md#providers) | User answers |
| An update is ambiguous (see [When to interview](#when-to-interview)) | [Quick interview](references/interviews.md#quick-interview), then write | User answers |
| Any project task is ending | Review all four records using the checklist above; edit only changed facts | Stop hook; AGENTS.md when hooks are unavailable |
| Meaningful decision made | Save it where BRAIN's save rules say | Instruction |
| Work started, finished, blocked, or reprioritized | Move the PROGRESS bullet to its status section; update the `Updated:` date, and the dated entry when there is an outcome | Task review; stop hook adds commit evidence when available |
| Work shipped (with evidence) | PROGRESS bullet to `Shipped` with evidence in the toggle; a dated entry for stakeholders; a CHANGELOG entry; README if newcomers should know | Stop hook checks the PROGRESS and CHANGELOG pair |
| Part of an item shipped | PROGRESS bullet to `Shipped`, marked `(partly shipped date)`, saying what is out and what is left; CHANGELOG gets the shipped part only | Stop hook checks the pair |
| Install, setup, or run steps changed | README Install and Use; STRUCTURE commands | Instruction |
| Code or folders reorganized | Update STRUCTURE's repository map | Stop hook and `check` detect drift |
| Knowledge moved inside a provider | STRUCTURE's brain map | Instruction |
| Provider added, replaced, or access changed | BRAIN (owner confirms), then STRUCTURE's brain map | `check` warns on a missing map |
| Direction changed | Reuse the owner's agreement, update VISION, log the change, rewrite the README pitch, review downstream; ask only if intent is unclear | Task review; stop hook flags a VISION edit |
| Agent enters an unfamiliar project | Orient (above) | Session-start hook; AGENTS.md entrypoint |

## Who writes what

The owner writes VISION; agents write the rest.

- VISION comes from the owner. When it is missing, vague, or unconfirmed,
  interview the owner. Never write intent from a guess.
- The owner chooses the providers once (brain and task tracker). After that,
  agents keep BRAIN and the documents it routes to current within the saved
  write and cleanup permissions. Record those choices, exact destinations,
  and permissions in BRAIN, so another session can use them.
- PROGRESS, STRUCTURE, README, CHANGELOG, and TECHSTACK are maintained automatically
  from evidence: the codebase, releases, deployments, and the tracker. Do
  not ask the owner what the evidence already shows.

## When to interview

The records are only as good as the owner's answers. Ask instead of guessing.

**Interview at setup** for owner choices that are missing or unclear.
Reuse answers already in the conversation, records, or user instructions.
An existing confirmed VISION or working Brain setup does not need a new
interview because the skill or its format changed. A missing save destination
needs a filing answer, not a repeat of the full provider interview.

**Interview along the way** when an update is ambiguous, especially for
VISION and providers:

| Trigger | Example |
| --- | --- |
| A change would alter intent | New audience, pricing, channel, horizon, or boundary; work that VISION says the project will never become |
| Evidence conflicts with VISION or with another record | VISION says personal use, but a public launch is planned |
| A provider question | Knowledge or tasks need a home BRAIN does not name; a provider is unreachable or holds less than BRAIN claims; it is unclear which folder or tracker project belongs to this project |
| A status you cannot prove | Work may have shipped, but no release, deployment, or confirmation exists |
| Two sources disagree and the latest owner statement is unclear | The tracker and PROGRESS name different next steps |

How to ask:

- Ask at most three questions at a time, with options drawn from the
  evidence, the recommended option first, and "Not decided yet". Use the
  host's question tool when it has one.
- Never ask what the evidence, the records, or the user's global
  instructions already answer. If the global instructions name default
  providers, offer them as the recommended answer.
- During an unrelated task, do not block it. Finish the task, then ask the
  questions at the end of the same reply.
- Record each answer with its date in the owning record. An unanswered
  question goes to Open questions with who decides and what it prevents.
  Keep active write holds and unresolved outcomes visible until resolved.
- A delegated worker that cannot ask the user writes the question as an Open
  question and lists it in its final reply; the parent session asks the user.

## Initialize

1. Collect what exists: the user's request, conversation, README, docs,
   issues, linked documents. Reuse it; do not make the user repeat it.
2. Run the [vision interview](references/interviews.md#vision-discovery) to
   the depth the gaps require. Run the
   [provider interview](references/interviews.md#providers) for the brain and
   the task tracker.
3. Write the four records from [templates](references/templates.md), plus TECHSTACK from verified tools and integrations, the
   AGENTS.md entrypoint (`CLAUDE.md` contains `@AGENTS.md`), README, and
   CHANGELOG (with a first entry once anything has shipped).
4. Run `python3 <this-skill>/scripts/horsemen.py check` and fix every error.
   Exception: a record that waits for the owner's answers stays missing; list
   it as pending instead of writing filler to pass the check.
5. Show the user a short summary: confirmed facts, assumptions, open questions.

If the owner does not answer (unavailable, or "later"), stop with the open
questions in your reply. Write a record only when the owner asks for a draft:
then use `Confirmed: not yet`, put every unanswered element in Open questions,
and leave the main sections empty rather than guessed.

## Maintain

Change only the record that owns the changed fact (see
[sync rules](references/sync.md)). Preserve unrelated content and history.
If nothing material changed, change nothing; do not refresh dates.

- PROGRESS: one bullet per item, `- **Item** (date): what it means for
  people`, under its status section. Write plainly:
  what people can do now, what is being worked on, what waits on whom. Avoid
  business terms, engineering terms, and vague activity reports. Keep
  the latest day separate from historical ships and their proof. Put PRs, commits, paths, and checks
  inside the relevant toggle, with delivery proof beside shipped outcomes. Update `Updated:` only when the snapshot
  changes. Keep dated historical ships with their proof; do not invent an outcome
  for a day without one. Preserve unique existing activity logs. Editing the records themselves is not progress.
- STRUCTURE: describe the new reality after a move, with exact paths, in the
  repository map or the brain map.
- BRAIN: fix a moved location after you find the item again; record a new
  provider only after the user chooses it. Keep exact filing destinations,
  write permissions, cleanup rules, and any holds current. Update the routed
  documents when lasting knowledge changes; BRAIN remains their directory.
  List nothing that is in the repository.
- VISION: preserve it unless a revision is requested or a direction change
  is agreed. Existing agreement is sufficient. Record the old
  direction in one line under Direction changes. Keep it a manifesto about
  people, the mission, and the world it builds; send engineering detail
  elsewhere.
- After any record edit, run `check`. Fix errors before you finish.

## Truth rules

Facts fall into three classes. Treat each one differently.

| Class | Examples | Rule |
| --- | --- | --- |
| Maintainable from evidence | Paths, commands, a merged PR, a passing deploy check, a moved Drive file | Update without asking. Cite the evidence |
| Needs the owner's choice | A VISION revision or direction change, priorities, a new provider, a roadmap idea to `Up next`, deleting history | Use the user's explicit request or existing agreement; ask only when missing, then record with a date |
| Unverified | Inferences, old measurements, a teammate's claim | Write it as an assumption or open question, with its source |

- Partial delivery: mark the item `(partly shipped date)` and say what is
  out and what is left. CHANGELOG records only the shipped part. When the
  rest becomes separate work, split it into its own bullet with its own gate.
- `Shipped` means the work reached its audience: a release, a deployment you
  verified, a published URL, a sent deliverable, or the owner's confirmation.
  Tests, a merge, or an agent's report mean `Ready to ship`.
- Never invent a fact, path, link, date, decision, or release. Write `Unknown`.
- Distinguish a check you ran now from a recorded earlier check. Keep dates.
- Preserve history. Move old log entries to `docs/progress-log.md`; record
  direction changes; do not delete unique material from legacy files.
- Pausing or archiving does not mean done. Record the true end state; keep
  unresolved outcomes as historical remainders, never as invented completion
  and never as revived active work without the owner's decision.

## Privacy

Public repositories hold no private IDs, private URLs, account emails,
internal discussion, or secrets. Use a neutral project key that resolves in a
private registry named by the user's global instructions. A link does not
grant access. Never change sharing, credentials, permissions, or network
settings, or switch accounts or providers, to make a link work. Access limits
recorded in BRAIN (account scope, pending moves, write holds) stay binding
until the owner changes them. BRAIN's `Visibility:` line makes `check` scan a
public repository for private links.

## Optional Brain engine

For a precise original-document update, use the [Brain engine contract](references/brain-engine.md).
Its provider-neutral library prepares exact text changes, checks host approval,
rejects stale originals, verifies writes, and refreshes disposable navigation.
The CLI only prepares changes; the native Docs adapter is guarded and narrow.
Use the [shared record contract](references/sync.md#shared-update-guarantees) for all four records. Existing
provider choices, account limits, and ask-before-write rules still apply.

## Hooks

Two hooks, installed once per machine, support the review without writing
records: session start injects the PROGRESS snapshot and health lines;
stop requests the four-record check at each normal task end and adds detected
drift. The host's `stop_hook_active` flag prevents recursion. Hooks cannot
see whether outside documents changed or judge what is worth keeping.
Hosts without hooks follow the same rules
through AGENTS.md. Details, install commands, and failure modes:
[hooks](references/hooks.md).

## References

- [commands.md](references/commands.md): command routing, read/write boundaries and diagrams

- [templates.md](references/templates.md): the four records, the README, CHANGELOG, and TECHSTACK supporters, AGENTS.md, with the rules for each
- [examples.md](references/examples.md): filled examples for a software and a non-software project
- [interviews.md](references/interviews.md): vision discovery, provider selection, and quick interviews for ambiguous updates
- [sync.md](references/sync.md): ownership, brain care, saved state, change propagation, contradictions
- [adopt.md](references/adopt.md): adopting an existing project and migrating legacy records
- [hooks.md](references/hooks.md): hook contract, check codes, install, limits
