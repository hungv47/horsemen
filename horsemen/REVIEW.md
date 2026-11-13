# Horsemen review package

## Outcome and scope

This change keeps the four records and their provider ownership intact, adds
TECHSTACK as a companion, makes Brain care proactive but quiet, and provides
a real optional CLI for local checks, inspection, proposals and review diffs.
It is a review pre-release. It does not merge itself, install globally, publish
a package, write provider originals or apply a patch to a project.

## Why this design

- One source: the old checker/hook implementation now lives in the package;
  its original script is a compatibility wrapper, not a second implementation.
- The skill owns reasoning, interviews, scope and permission-aware workflows.
  The CLI owns deterministic local work. Their command names do not promise
  identical capabilities; [the parity table](references/cli.md) states each.
- Plans preserve owner content and disclose missing facts. Input references,
  hashes, tests and exported patches are not authority to write.
- Review patches are useful now without pretending that a hash check followed
  by file replacement is a race-free conditional write.
- Drive remains authoritative where BRAIN says so. No new registry, cache of
  knowledge, background service, credentials or provider switching is added.

## Important compatibility corrections

The original `inspect and proceed` workflow included record maintenance. It
remains an alias for `inspect-and-update`; plain inspect is the separate
read-only mode. Init does not reset existing records. Legacy TECH.md remains
covered by privacy/link checks and record-only commit classification, but is
not a fifth record, a project marker or a substitute for TECHSTACK.md.

The new standalone CLI disables executable Git fsmonitor and clean/process
helpers during local inspection. Existing hook script behavior remains
unchanged. Patch output counts LF-delimited lines, preserving CRLF, missing
final newlines and Unicode separators without corrupting the diff.

## Human review checkpoints

1. Review the diff and command parity. Pay particular attention to owner
   VISION, read-only versus compound inspection and legacy adoption.
2. Review the no-follow file reads, exact source/anchor checks, batch rejection
   and absence of a write/apply path. Tests use temporary fixtures only.
3. Verify source and installed-wheel tests for this exact commit. Configured
   CI is not a passed check. Review Linux/macOS and Python 3.10/3.14 results.
4. Decide whether the limited pre-release is useful before requesting a merge.
   Merging does not authorize installation, package publication or provider
   writes. Stable release/support decisions remain separate.

There is no `--yes`, embedded approval flag, release credential or automatic
publish/install/merge workflow. CI has read-only repository permissions.
The project is public under MIT. It has no automatic PyPI publication.

## Verification and its limits

Reproduction commands are in [CLI.md](CLI.md). The CLI suite
runs both from source and against a built wheel. It covers no-op/date/mode
preservation, missing inputs, legacy migration, stale anchors, wrong roots,
path traversal, symlinks, late batch errors, unsafe approval fields, configured
Git helpers and review-patch round trips. Existing checker/hook and engine
suites remain required. The unified verifier also checks the skill bundle and installed CLI.
The original collection keeps its private import history separately.

Tests establish observed behavior; they do not imply independent reviewer
approval. No live
provider save or autonomous agent-host dispatch is claimed.

## Genuine remaining blockers and deferred integrations

- Automatic apply needs a trusted approval transport and a supported write
  concurrency contract. The existing local filesystem path supplies neither.
  A deterministic test demonstrates the read/check/replace race. No unsafe
  fallback is implemented.
- Safe Drive Markdown conditional writes and a live host bridge remain absent.
  The native Docs adapter is intentionally narrow and does not solve them.
- Init/upgrade produce missing-input and migration-review plans, not invented
  content or semantic migration of every historical prose format.
- Local CLI inspect does not query PRs, CI, deployments, provider originals or
  all worktree contents. Those remain skill workflows with verified access.
- Diagrams remain Mermaid and the existing show-me-bro agent integration.
  No CLI renderer or pele.run connection/upload is claimed.
- Windows local planning/export is unsupported. A production support matrix
  requires explicit acceptance and exact-revision test evidence.

These are visible boundaries, not silent feature substitutes. The next safe
extension is separately reviewed staging/export integration, followed by an
explicit choice of trusted approval and write mechanisms.

## Owner feedback: document presentation

VISION guidance now asks for entrepreneurial, inspiring and grounded language,
using business value/sustainability or nonprofit mission/impact/stewardship as
appropriate. It never invents owner intent, traction or targets. README asks
for a concrete description of inputs/actions and results, beyond the pitch.
PROGRESS uses Latest day, Historical ships with proof, and Upcoming roadmap,
each in a toggle with ordinary Markdown headings as readable fallback. The
parser supports this without abandoning older formats. Historical ships remain
visible to shipment checks; moving an item into history is not a new shipment.
Non-Git projects can use delivery artifacts or dated owner confirmation.
