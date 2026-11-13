# Templates

Copy a template, then replace every `{{...}}` prompt with a fact from the
project or the user. `check` flags any prompt that remains. Delete optional
sections that do not apply; do not fill them with filler. See
[examples](examples.md) for the intended length and tone.

Shared rules:

- Write short, plain sentences. One fact has one home (see [sync](sync.md)).
- Write `Unknown` or move the item to Open questions when a fact is missing.
  Never invent a fact, path, link, date, or release.
- Use ISO dates (`2026-11-01`). A path in backticks is relative to the project
  root, and `check` verifies that it exists. Write any location outside the
  project with a prefix: `drive:Research/`, `notion:Specs`, `other-repo:src/`.
  Write a pattern with angle brackets, such as `applications/<status>/<slug>/`;
  `check` skips it.
- Public repositories hold no private IDs, private URLs, account emails, or
  secrets. Use a neutral project key that resolves in a private registry.

## VISION.md

VISION is the project's manifesto. It says what we are building, why it must
exist, who it is for, and the world we expect when it works. It is the grand
mission in the owner's voice, not a plan. Readers are the owner, partners,
investors, and every agent that must decide what the project should become.

Make it entrepreneurial and inspiring without hype: name the change worth
building, the people it serves, why now, and the distinctive value it creates.
For a business, connect that value to sustainable demand and a viable model.
For a nonprofit, emphasize mission, measurable social benefit, stewardship and
sustainable funding rather than forcing revenue or growth language. For a
personal project, use the owner's ambition and practical benefit. Never invent
market size, traction, targets or impact; keep unconfirmed bets separate.

Write it in the first person plural ("we"), in confident, plain prose. Each
section is a short paragraph or a few bullets. No tables. Leave out
features, screens, architecture, tools, file paths, and task lists. They
belong in PROGRESS, STRUCTURE, or a spec that BRAIN points to.

VISION comes from the owner. Write it only from the
[vision interview](interviews.md#vision-discovery) or from the owner's own
words. Target: 40 to 100 lines. Changes need the owner's confirmation.
Use this template for setup or a requested revision. Do not reformat an
existing VISION or reset its confirmation during routine maintenance.

```markdown
# Vision

Owner: {{name}} · Confirmed: {{YYYY-MM-DD, or "not yet (draft from evidence)"}}

{{The declaration, two or three sentences: what we believe should be true, what we are building, and for whom. Someone who reads only this knows why the project exists.}}

## Why we exist

{{The problem in the words of the people who have it, what it costs them today, and why now is the moment to fix it.}}

## The world we are building

{{Three to six sentences in the present tense, written as if the mission has played out. How the lives of the people we serve are different, what the project is known for, how big it is, and how it sustains itself.}}

## Who we build for

{{The exact people, in a short paragraph: who they are, what they need, and why they choose us. Name the second audience if there is one.}}

{{Who we do not build for, and why.}}

## What we believe

- {{A conviction that decides trade-offs. One line each, three to six lines.}}

## How we get there

- Now: {{what we must prove first, and the signal that proves it, with a date}}.
- Next: {{what grows once that is true}}.
- Later: {{the full picture}}.

## What we will never become

- {{A direction we refuse, even if a customer asks or money is offered.}}

## How it sustains itself

{{Optional. Who runs it, how it earns money or what it costs, what stays human.}}

## Bets

- {{Optional. A belief the mission depends on that is not proven yet. Its source, and how it gets tested.}}

## Open questions

- {{Question. Who decides.}}

## Direction changes

- {{YYYY-MM-DD: what changed and why. Previous direction in one line.}}
```

Rules:

- Only the owner's confirmed statements go in the main sections. Inferences
  go in Bets. Unknowns go in Open questions.
- When only some sections are confirmed, say which on the `Confirmed:` line,
  for example `Confirmed: 2026-10-23 for why and who · the rest drafted
  2026-11-02, awaiting the owner`.
- The test for every line: would the owner say it out loud to a partner or
  an investor? If it reads like a ticket or a spec, cut it.
- `check` warns when VISION holds a code block or a file path, when a core
  section is missing, and when VISION still uses the old business-plan
  sections (Purpose, Who it serves, How it plays out).
- Fit the sections to the project type. A personal or support project
  (tooling, dotfiles) writes the world it makes for its owner, and "How it
  sustains itself" as the time and money it costs to keep. An experiment puts
  its hypothesis and kill criteria under Now. Research names the decision it
  informs under Why we exist.

## PROGRESS.md

PROGRESS helps a reader catch up in three parts: the latest day's update,
historical ships with proof, and the upcoming roadmap. Keep each part in a
`details` toggle, with ordinary Markdown headings and text that still make
sense when the reader does not render HTML. The latest-day toggle starts open.
Do not invent activity for today; use the date of the latest verified update.

```markdown
# Progress

Updated: {{YYYY-MM-DD}} · Stage: {{stage}} · Health: {{health}}

{{Two short sentences: what changed on the latest update day and why it matters.}}

Next action: {{one concrete next step and its owner}}

## Latest day

<details open>
<summary>Latest day · {{YYYY-MM-DD}}</summary>

## Shipped

- **{{Item}}** ({{YYYY-MM-DD}}): {{what reached people on this update day}}.

## Up next

- **{{Item}}** (target {{date or month}}): {{the next committed outcome}}.

## Needs decision

- **{{Question}}**: {{who decides and what waits}}.

## In progress

- **{{Item}}** (started {{date}}): {{optional current work needed to understand the next step}}.

| Item | Evidence |
| --- | --- |
| {{same item name}} | {{link to a release, live result, sent deliverable, or dated owner confirmation; PR link as supporting evidence}} |

Gates: {{constraints that must be respected; link the source}}.
Task tracking: {{tracker link or none}}.

</details>

## Historical ships

<details>
<summary>Historical ships · newest first</summary>

| Date | Shipped | Proof |
| --- | --- | --- |
| {{YYYY-MM-DD}} | {{outcome people received, before the latest day}} | {{delivery proof link; PR link where relevant}} |

{{Keep older shipped history here or link its unchanged archive. Preserve unique dated decisions and blockers in the existing log, with a link here; do not delete them to fit this layout.}}

</details>

## Upcoming roadmap

<details>
<summary>Upcoming roadmap</summary>

- Next: {{milestone beyond the immediate Up next work; target if agreed}}.
- Later: {{direction, dependencies and uncertainty}}.
- Idea: {{explicitly not committed}}.

</details>
```

Rules:

- The first part is the latest update day, not a rolling list of all past
  releases. Say `Nothing shipped on this update day` if that is the truth.
  Keep Shipped, Up next and Needs decision visible within this toggle; add
  Ready to ship, In progress or Blocked only when relevant.
- One status bullet per item, with a bold plain-language name. Its matching
  Item/Evidence row holds proof or the next verification step. Keep dates
  unchanged when nothing changed. A newer date alone is not progress.
- Move older shipped outcomes into Historical ships, newest first, without
  losing their original dates or proof. Do not list the same ship in both
  latest-day and history. History may link an existing archive; never discard
  earlier ships or unique decisions because a display limit was reached.
- Link actual delivery proof. A PR may support the story, but merge/green CI
  alone is not delivery. Non-Git projects use a published artifact, sent
  deliverable, event/result record or dated owner confirmation. Keep private
  proof in its approved scope; public records use safe references.
- Partly shipped means only the delivered part is historical fact. Say what
  remains. CHANGELOG records delivered outcomes only; pending work stays in
  latest-day status or roadmap. Each new ship still needs its CHANGELOG entry.
- The third part is the upcoming roadmap, not another history or duplicate
  task list. Separate agreed milestones from tentative ideas. Priority changes
  still need the owner's agreement.
- The latest-day block is the session-start snapshot. History and roadmap
  remain in the document for deeper review. Existing untoggled/dated layouts
  stay readable and supported; migration must preserve their unique content.
- Put a blank line after each summary and before its closing details tag.
  Keep the three sections' headings outside the toggles for readable fallback.
  Never hide an actionable blocker solely behind a collapsed history section.

## BRAIN.md

BRAIN is the directory of the project's outside providers: the brain that
holds knowledge outside this repository (documents, research, test lists,
and the record of past discussions between the owner and agents), the task tracker, and any other
provider the project needs. It says what each holds and how to reach it. It does not
hold the knowledge itself, and it does not list repository files (STRUCTURE
maps those). The owner chooses the brain provider: a folder of Markdown files, an
Obsidian vault, Google Drive, Notion, or anything an agent can reach. If all
knowledge is in the repository, write
`Brain: None (all knowledge is in this repository)` and stop after
Visibility.

Target: under 100 lines. Record setup choices once so later tasks do not
need to reconstruct the interview. Provider verification and owner agreement
are different facts; date each from its own evidence.

```markdown
# Brain

Brain: {{provider names, or "None (all knowledge is in this repository)"}} · Access verified: {{YYYY-MM-DD, or "not yet"}}

Visibility: {{private / public}}

Setup choices: {{date and source of the owner's choices; list any unresolved choice in Open questions}}.

## Providers

| Role | Provider | Root or project | Access route | Account and scope | Verified |
| --- | --- | --- | --- | --- | --- |
| Brain | {{Google Drive}} | {{drive:Projects/Name, or a neutral key in a public repository}} | {{connector, CLI command, or mounted path}} | {{personal account only}} | {{YYYY-MM-DD or "not yet"}} |
| Task tracking | {{Linear}} | {{team and project, or "not linked yet"}} | {{connector or CLI}} | {{workspace}} | {{YYYY-MM-DD or "not yet"}} |

## What lives in the brain

| Knowledge | Provider › location | Why it is not in the repository |
| --- | --- | --- |
| {{Customer interviews}} | {{Drive › Research/Interviews}} | {{private, edited by non-engineers, large files}} |
| Past discussions with agents | {{Obsidian › Decisions/, Drive › Decisions log, or Notion › Decisions}} | {{running record of what was asked, decided, and why}} |

## Retrieve

1. {{Where to look first for each kind of question.}}
2. When a question may have come up before, search the past discussions first.
3. Open the original. A summary, memory hit, or search result is a pointer, not proof.

## Save

| Knowledge | Exact destination | When a new document is allowed |
| --- | --- | --- |
| {{Decisions and reasons}} | {{provider, original document link or ID, and section; neutral key in a public repo}} | {{update the existing log; no new session document}} |
| {{Research}} | {{provider and exact folder or parent page}} | {{a distinct subject with no existing original}} |

- Agents may save {{automatically / after asking / never; source or date of the choice}}.
- Keep useful, lasting changes only. Update the original before creating an
  item. Save a decision's date, question, answer, and reason when it adds
  knowledge; skip transcripts, routine task recaps, and repeated facts.
- To the repository: {{code, the project records, specs that ship with the code}}.
- Never save: {{raw chats, drafts, secrets, duplicates}}.

## Cleanup

- Bin: {{exact project bin folder or parent page; use the existing archive if agreed; "Not decided" when unknown}}.
- Recovery index: {{exact document; entries keep date, source location, bin location, reason, replacement, and restore steps}}.
- Agents may move confirmed stale copies {{automatically / after asking / never; source or date of choice}}.
- Preserve unique facts, history, and unresolved questions. Ask if permission,
  ownership, or effects on links are unclear. Do not empty the bin or delete
  unique material during routine maintenance.

## Access rules

- {{Binding limits: account and scope, approved route, pending moves, write holds with their dates.}}

## Access problems

- Moved or renamed: search by title in the same provider, then fix the
  location here and in STRUCTURE.
- Missing or no access: report it. Do not switch account, provider, sharing,
  credentials, or settings. Work that does not depend on that access continues.

## Open questions

- {{Unresolved knowledge setup question. Who decides.}}
```

## STRUCTURE.md

STRUCTURE is the map of where everything is. It has two parts: the technical
structure inside the repository, and the business and document structure
inside the brain, with how to open each part. BRAIN owns the access rules;
STRUCTURE gives the concrete location and the command or link.

Target: under 150 lines. A map of what matters, not a full listing.

~~~markdown
# Structure

{{One line: what the repository holds and what the brain holds.}}

## Map

```text
{{project-folder}}/
├── {{src/}}
│   ├── {{app/}}                 {{what lives here}} (start here)
│   └── {{api/}}                 {{what lives here}}
├── {{content/}}                 {{what lives here}} (edit content here)
├── {{dist/}}                    {{build output}} (generated; do not edit)
├── {{docs/}}                    {{dated notes}} (history; do not update)
└── {{package.json}}             {{commands and the build pipeline}}
```

## How it fits together

```mermaid
flowchart LR
  {{source["Content or input<br/>path"]}} --> {{logic["Logic<br/>path"]}}
  {{logic}} --> {{output["Pages, API, or app<br/>path"]}}
  {{output}} --> {{live["Where it runs: host and branch"]}}
```

{{One line on what never feeds the product, for example the brain.}}

## Repository

| Key file | Why it matters |
| --- | --- |
| `{{path/to/file}}` | {{why an agent opens it}} |

Commands: `{{install}}`, `{{run}}`, `{{test}}`, `{{build}}`.

Where new work goes:

| To add | Put it in |
| --- | --- |
| {{a new API route}} | `{{src/routes/}}` |

Conventions: {{naming, layering, or ownership rules an agent must follow}}.

## Read before changing

- {{`path/README.md` before changing that domain; a manifest or contract an agent must load first.}}

## Brain

Access rules and accounts live in [BRAIN.md](BRAIN.md).

### {{Provider}}: {{root}}

Open with: {{connector, CLI command, or link}}.

```text
{{Root}}/
├── {{Folder/}}              {{what it holds}}
│   └── {{Subfolder/}}       {{what it holds}}
├── {{bin/}}                 {{stale documents; recovery index inside, if configured}}
└── {{Key document}}         {{what it is for}} (start here)
```

| Document | Location | Use it for |
| --- | --- | --- |
| {{Pricing model}} | {{Sales/Pricing (sheet)}} | {{current prices and discount rules}} |

## Other documents

- {{README.md: pitch and setup. CHANGELOG.md: what shipped. TECHSTACK.md: tools and integrations. docs/...}}
~~~

Rules:

- **Map** is one annotated tree in `tree` style (`├──`, `└──`, `│`), at most
  three levels deep. Show the folders that matter and the root files an agent
  needs; skip lockfiles and editor settings. The first line may name the
  project folder. Tag special nodes at the end of their description:
  `(start here)`, `(edit content here)`, `(generated; do not edit)`,
  `(history; do not update)`. `check` joins each node to its parent and
  verifies the full path; patterns such as `*.png` or `<slug>/` are skipped.
- **How it fits together** is a Mermaid flowchart of four to eight nodes:
  how input becomes the product, and where it runs. GitHub draws it; agents
  read the text. Label each node in plain words, with its path on a second
  line. Skip it for a project without a flow (a folder of documents).
- **Repository** lists only key files the tree does not show, then commands
  and where new work goes. Do not repeat the tree as a table.
- A project without code replaces Map and How it fits together with
  `No code.` under Repository. Several repositories: one Map per repository.
- **Brain** repeats `### Provider: root` for each provider in BRAIN, with the
  same tree style. Map the folders people use and the few documents that
  matter; do not dump a full listing. Skip the section when BRAIN says
  `Brain: None`. `check` does not verify brain trees against the repository.
- Read before changing is optional. Agents receive it at session start, so
  keep it to the documents that are truly mandatory.

## Supporting documents

README, CHANGELOG, and TECHSTACK are not records, but every project keeps all three, and
they change whenever their sources change (see [sync](sync.md)).

### README.md

README is VISION and the install guide, cut down to what a newcomer needs in
one screen: what this is, who it is for, how to install or reach it, and how
to start. No roadmap, no status, no business model. Rewrite the pitch when
VISION changes; rewrite the steps when the install changes.

```markdown
# {{Project name}}

{{Two to four sentences cut down from VISION: what this is, who it is for, and the change it makes for them.}}

## What it does

{{Two concrete sentences: what someone brings or does, what the project does with it, and what they receive. Describe real current behavior, not only the mission.}}

## What you get

- {{A capability people can use today. Only shipped work.}}

## Install

{{Steps that work today. Link the full install or deployment guide when one exists.}}

## Use

{{The first thing to do after install.}}

## Project records

- [VISION.md](VISION.md): what this becomes and why
- [PROGRESS.md](PROGRESS.md): what shipped, what is left, what comes next
- [BRAIN.md](BRAIN.md): knowledge outside this repository
- [STRUCTURE.md](STRUCTURE.md): map of the repository and the brain
- [CHANGELOG.md](CHANGELOG.md): what shipped
- [TECHSTACK.md](TECHSTACK.md): tools, stack, resources, and integrations
```

For a project without software, use `## Access` or `## Get started` instead
of Install and Use. `check` warns when README has no such section.

### CHANGELOG.md

CHANGELOG lists only what reached people, newest first, in their words. It
never holds pending, half-done, or planned work; PROGRESS holds those. For a
`Partly shipped` item, write only the part that shipped. Use a version and
date heading when the project has versions, a date heading otherwise.

```markdown
# Changelog

## {{version - YYYY-MM-DD, or YYYY-MM-DD}}

- {{What people can do now, in their words. Link the release when there is one.}}
```

## AGENTS.md entrypoint

`CLAUDE.md` contains only `@AGENTS.md`.

```markdown
# Project context

Before project work, read the PROGRESS snapshot. Read the other records when
the task needs them. Before finishing each task, use the `horsemen` skill to
review all four records, including work outside Git. Update only changed
facts. Keep VISION unless a revision is requested or a direction change is
agreed. Use BRAIN's exact destinations and saved permissions. If nothing
changed, leave files and dates alone.

- [VISION.md](VISION.md): what the project becomes and why
- [PROGRESS.md](PROGRESS.md): what shipped, what is left, what comes next
- [BRAIN.md](BRAIN.md): knowledge outside this repository and how to reach it
- [STRUCTURE.md](STRUCTURE.md): map of the repository and the brain

{{Project-specific agent rules, if any.}}
```

### TECHSTACK.md

TECHSTACK owns the current tool and integration inventory. It is not a lockfile,
architecture design, status log, credential store, or permission registry.
Include non-code projects: research tools and workflow resources matter too.
Use “Not used” only after checking, and “Unknown” when evidence is missing.
Never infer a paid plan or live connection from an installed package.
Write for a junior to middle-level engineer: short sentences, familiar words,
and explain necessary jargon once. Start with a two-sentence system overview.
For each tool, name the need it addresses, what it needs to work (runtime,
configuration, service or access), and how it helps this project. Keep each
cell to one short phrase. Put versions beside tool names. Keep detailed setup and evidence below the
summary or link their owner. Do not repeat whole setup guides.

```markdown
# Technology and tools

Checked: {{date and exact scope checked}}

{{What the project does and how its main parts connect, in two sentences.}}

## Stack and tools

Cover every applicable layer. Use “Not used” or “Unknown” explicitly rather
than omitting a layer. Separate what is in use from proposed replacements.

- Frontend: languages, framework, UI, styling, assets and accessibility tools.
- Backend: runtime, API framework, jobs and server-side services.
- Data: database, storage, schema/migration tools, cache and backup approach.
- Infrastructure: hosting, deployment, domains, CI/CD and observability.
- Testing: unit, integration, browser, accessibility and security checks.
- Developer tools: package manager, build tools, formatters and local workflow.

| Tool and version | Need it addresses | What it needs | How it helps |
| --- | --- | --- | --- |
| {{tool, version and layer; Unknown if unverified}} | {{project problem}} | {{runtime, configuration or access; no secrets}} | {{concrete benefit}} |

## Integrations and resources

| Service or resource (version/plan if known) | Need it addresses | What it needs | How it helps |
| --- | --- | --- | --- |
| {{service}} | {{project problem}} | {{required connection or access}} | {{benefit and important limit}} |

## Runtime connections

{{One small Mermaid diagram or link to the existing editable visual showing
actual runtime components and labeled data flow. Mark unknowns; omit for a
non-runtime project and say why. Do not invent a database or hosting service.}}

## Development and release

{{One small diagram or existing visual link showing local tools, checks and
release steps. Separate planned steps from verified automation. Do not imply
that a successful build deploys the project.}}

## Evidence

- {{Tool: pinned or observed version/plan, source and date. Unknown if unverified.}}
- {{Integration: observed connection, data direction and limits, source and date.}}

Access and permissions: [BRAIN](BRAIN.md). Paths and commands: [STRUCTURE](STRUCTURE.md).

## Gaps and changes to verify

- {{Unknown claim, what would verify it, and who can resolve it}}
```

Update changed facts in place; link long guides and originals instead of
copying them. Preserve deprecation context where useful. No credentials,
private account IDs in public repositories, or implied integration approval.
