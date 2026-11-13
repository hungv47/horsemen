# Adopt an existing project

Use this when a project has no records, partial records, or records in an
older format (STATUS.md, ROADMAP.md, INDEX.md, MEMORY.md, provider-binding
preambles). The goal is the current format with no lost information.

## Principles

- The four records are always Markdown files in the project. A tool such as
  Linear, Notion, or Drive may hold detail (tasks, research, files), and the
  records link to it. A record is never replaced by a pointer to a provider.
- Content moves; history stays. Git history keeps the old files. Unique
  material that has no home in the new format goes to `docs/` or the
  knowledge home, and a record links to it.
- Preserve an existing VISION unless the user asks to revise it or agrees to
  a direction change. A format warning does not authorize a rewrite or a
  reset of its confirmation date.
- Do not upgrade facts during migration. A state, date, or measurement keeps
  its original evidence and date. Migration is not verification.
- You may run a fresh, read-only check during migration (a deployment
  status, a live URL, the test suite) and record it with today's date. A
  fresh check can correct a status in either direction; say so in the dated
  entry. For example, in an earlier migration: two "not shipped" items were
  live, and lint failed although tests passed.

## Steps

1. **Inventory.** Run `python3 <this-skill>/scripts/horsemen.py check`. Read
   every legacy record in full, plus README and `docs/`. List each distinct
   fact once.
2. **Map** each fact to its new owner:

   | Legacy content | New home |
   | --- | --- |
   | STATUS "Shipped/delivered" sections | PROGRESS latest-day Shipped bullets and Historical ships with proof; every shipped item also in CHANGELOG |
   | STATUS current work, gaps, next steps | PROGRESS bullets under the status sections |
   | PROGRESS status table (`Status \| Item \| What it means \| Date`) | One bullet per row under the matching status section; the Technical details table stays |
   | STATUS long verification narratives | The linked release or verification document; PROGRESS keeps one line and the link in a toggle |
   | ROADMAP plans | PROGRESS `Up next` (committed) or Roadmap (planned and ideas) |
   | INDEX or tree listings | STRUCTURE repository map (meaningful map only) |
   | Drive, Notion, or Confluence folder listings | STRUCTURE brain map |
   | MEMORY, lessons, decisions | The decision home that BRAIN's save rules name |
   | Old BRAIN `Key decisions` index | The decision home; drop the index from BRAIN |
   | Old BRAIN rows for repository files (`docs/...`) | STRUCTURE repository map |
   | Old VISION features, architecture, or tool choices | Leave VISION unchanged during routine adoption; move detail only as part of an authorized VISION revision |
   | "Working authority" and "Intended provider (cutover not verified)" preambles | Delete the boilerplate only after you move every specific restriction into BRAIN Access rules: account and scope, approved route, pending destination, recorded access failures (for example a 401 with its date), and writes that wait on them. A wanted provider move becomes a BRAIN Open question |
   | Release gates, acceptance checklists, rehearsal steps | PROGRESS Gates in the snapshot toggle (one line each, link the checklist) |
   | Mandatory domain reading (task README, manifest, contract) | STRUCTURE Read before changing |
   | Historical, unresolved outcomes of an archived project | An archive ledger in `docs/` (moved unchanged) that PROGRESS links; never active rows |
   | Provider links (Drive folder, Linear project) | BRAIN Providers table; STRUCTURE brain map |

3. **Rebuild PROGRESS.** Use the three-part template: Latest day (open toggle),
   Historical ships (collapsed, proof links), Upcoming roadmap (collapsed).
   Use the latest verified evidence date, not an automatic date refresh.
   Keep today's/that day's shipped outcomes, up-next work and decisions in the
   first part; add active/blocked states when relevant. Move older ships with
   their original dates and proof into history, not out of the document merely
   to meet a display limit. Link an existing archive when needed. Preserve all
   unique decisions, blockers and delivery evidence from dated legacy entries
   in place or an explicitly linked log. A PR alone does not prove delivery.
   Non-Git work uses sent/published artifacts or dated owner confirmation.
   Preserve priority commitments; tentative roadmap ideas remain tentative.
4. **Check VISION.** Preserve its text and confirmation date. If it is
   missing, use the setup interview. If the user requested a revision or
   already agreed to a direction change, use those answers and the current
   template. Ask only about unresolved intent. An old layout alone is not a
   reason to rewrite it or repeat an interview.
5. **Restructure BRAIN.** Write the `Brain:` line from the existing content
   (old name: `Knowledge home:`). Fill the Providers table and "What lives in
   the brain". Open each provider and confirm that what BRAIN claims is
   there; a claim you cannot find becomes an Open question, not a row. Move
   repository files and folder-level detail to STRUCTURE.
   Preserve the initial setup choices. Fill exact save destinations and bin
   rules from existing evidence; ask only for missing choices that affect a
   needed write. Never assume a new provider or invent an intake folder.
   Set `Visibility:` from the repository host (for example
   `gh repo view --json visibility`). In a public repository, move private
   links to the private registry and keep only the neutral project key.
6. **Restructure STRUCTURE.** Rename `## Code` to `## Repository` and verify
   every path. Add "Where new work goes". Replace the old Knowledge section
   with a `## Brain` map: one subsection per provider, its folder tree, key
   documents, and how to open them.
7. **Supporters and entrypoints.** Create or reconcile TECHSTACK from manifests,
   configuration, usage evidence, and scoped provider reads. Keep unknowns
   explicit; do not install or connect tools to fill it. Link setup guides and
   preserve user-authored inventory. Migrate an existing TECH.md to TECHSTACK.md
   only within the task's file-change permission; update its inbound links.
   If both files exist, compare and reconcile unique owner content before any
   removal. Never overwrite either file blindly. The checker only reports a
   missing TECHSTACK.md; it does not rename or delete files. Rewrite README as the cut-down VISION
   pitch plus working install and use steps; keep every working command.
   Create CHANGELOG if it is missing, from shipped evidence only, with the
   original dates; do not reconstruct entries you cannot prove. Remove
   pending or planned lines from an existing CHANGELOG and make sure PROGRESS
   holds them. Read AGENTS.md and CLAUDE.md in full. Replace AGENTS.md
   with the template entrypoint, keeping every project-specific rule from
   both files. Only then set `CLAUDE.md` to `@AGENTS.md`. Fix README
   links. Update any script, template, or generator in the project that would
   recreate STATUS.md or the old preamble.
8. **Retire legacy files.** If a file you cannot change links to STATUS.md
   (for example a README locked by a release manifest, or another
   repository), keep STATUS.md as a pointer: one heading and one sentence
   that links PROGRESS.md and says when to delete it. `check` reports it as
   a warning, not a second owner.
   Otherwise delete STATUS.md, ROADMAP.md, INDEX.md, and
   MEMORY.md only after every unique fact has a new home. Mention the
   commit that holds the old version in the PROGRESS log line for the
   migration.
9. **Verify.** `check` reports no errors. Then do a cold-start test: from the
   records alone, answer (a) what the project is for, (b) where knowledge
   lives, (c) what shipped last and when, (d) what is in progress and
   blocked, (e) where to change a given feature, (f) how to open the main
   brain folder. Note any answer the records cannot give.

## Special cases

- **Archived or paused project:** `Stage: archived` (or `paused`) and a true
  `Health`. Keep a final `## Shipped` list and write `- Nothing right now.`
  under any open section. Keep the ledger of
  results and unresolved outcomes as history; do not turn it into `Up next` or
  `In progress` bullets. Retiring the project is not completing it.
- **Support repository** (tools, dotfiles, configuration, a catalog): write
  records for its actual role. VISION states what it supports and its limits;
  PROGRESS tracks changes to it. Do not invent product users or launches.
- **Repository that owns operational records** (for example a pipeline or
  ledger): those records keep their own format and owner. PROGRESS summarizes
  their state and links them; it does not copy them.

## Several projects at once

Migrate one project first and review it with the owner. Then migrate the rest
one repository per branch and pull request. Do not batch unrelated
repositories into one change.
