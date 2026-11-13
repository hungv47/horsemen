# Standalone CLI and skill parity

The standalone CLI is an optional pre-release package from the same source as
this skill. It does not replace the skill's reasoning or host permissions.
No global installation is required for the skill or its existing hooks.

| Intent | Agent workflow | Executable CLI |
| --- | --- | --- |
| Validate records | `horsemen check` | `horsemen check PATH [--json]` |
| Inspect | Connected-project review under BRAIN scope | `horsemen inspect PATH [--json]`: local only, no remote reads |
| Initialize | Gather evidence/owner choices and write missing records within authorization | `horsemen init PATH --plan [--json]`: gaps and draft requirements only |
| Update | Reconcile supported facts and originals within saved permissions | `horsemen update PATH --plan --changes FILE [--json]`: explicit edits only |
| Upgrade | Preserve unique legacy content and migrate within authorization | `horsemen upgrade PATH --plan [--json]`: review proposals, no renames |
| Inspect and update | Full compound workflow; aliases `inspect and update` and legacy `inspect and proceed` | Not implemented; never silently map it to read-only inspect |
| Diagram | Mermaid or existing show-me-bro workflow, preserving format/location | Not implemented; no hosted uploads or second renderer |
| Review an exact change | Review the proposed diff with the owner when needed | `horsemen export-patch PATH --plan-file FILE`: stdout only, no application |
| Help | Command menu without reading private project data | `horsemen help` or `horsemen --help` |

Unknown CLI commands fail rather than starting an agent or changing scope.
`horsmen` is an agent spelling alias, not a second executable. The original
`python3 <skill>/scripts/horsemen.py` checker and hook commands remain supported.
The separate Brain `prepare` script still prepares exact provider snapshots;
it does not connect a provider or apply CLI plans.

## Human checkpoints

Plans, evidence references, hashes, patch exports and owner-agreement strings
are not approval. The CLI never accepts `--yes` or an approval field to write.
Keep VISION, BRAIN permissions and provider holds under their existing rules.
Review exact targets/diffs and unresolved facts before any later manual action.
Neither a patch export nor a successful test permits merge, deployment,
provider writes, runtime installation or package publication.

A genuine future write path needs a trusted host decision for the exact plan
and a supported concurrency contract. Do not weaken the Brain adapter's atomic
revision requirements to fit a local overwrite. Staging in a separate worktree
can be designed independently, but is not implemented by this CLI.

## Release gate

This is a review pre-release, not a production replacement. Build and test the
wheel in an isolated environment; preserve the old hook paths and installed
copies until separately approved. Automated verification runs on Linux/macOS
and Python 3.10/3.14, but configured jobs are not proof they passed: check the
exact revision's results. Windows planning/export is unsupported and fails
closed when no-follow filesystem operations are unavailable.

No release/upload workflow or credentials are included. The private package
classifier blocks accidental public PyPI publication. A stable release needs
human review, passing exact-revision checks, an agreed support matrix and a
separate explicit installation/publication decision. There is no auto-merge.

See [prototype usage and design limits](../CLI-PROTOTYPE.md) for commands,
JSON states, proof of the write limitation and reproduction steps.
