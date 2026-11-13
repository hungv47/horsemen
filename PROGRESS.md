# Progress

Updated: 2026-11-13 · Stage: live · Health: On track

## Latest day

<details open>
<summary>Latest day</summary>

Horsemen now has one public MIT project for its agent skill and CLI.

Next action: Review the draft command update and its single-record save limits before any merge.

## Shipped

- **Easy installation and a project cover** (2026-11-13): The README starts with the skills.sh install command and the original owner-approved cover.

- **One Horsemen project** (2026-11-13): Published source, one version, clear setup, and verification for both ways to use it.

## Ready for review

- **Direct record commands**: Brain, vision, structure and status now have read-only reports and explicit local updates. Whole-project checks remain; planning tools share one menu. Not merged or released.

## Decisions

- Public repository and MIT license confirmed by the owner on 2026-11-13.
- Preserve private history in the original collection; publish only the checked source.

### Technical details

| Item | Evidence |
| --- | --- |
| Easy installation and a project cover | [README](README.md); skills CLI discovery and a temporary Codex installation matched the source; [original cover and verified checksum](assets/README.md). |
| One Horsemen project | [Public source](https://github.com/hungv47/horsemen) is available. Source, installed CLI, and unpacked-skill checks passed locally on 2026-11-13. Reproduce with [CONTRIBUTING.md](CONTRIBUTING.md). The private skills collection now points here. |

Existing installed copies are unchanged.

### Command review evidence

- Full local verification passed on 2026-11-13: source tests, installed CLI,
  packaged skill and legacy hooks. Added coverage for each record, exact-edit
  validation, isolation, legacy callers and configured knowledge routes;
  simulated storage and read-back failures use disposable files. Reproduce
  with CONTRIBUTING.md. Final revision checks remain a draft-PR review gate.
- Local writes require the caller to exclude other editors. Provider originals
  still use their authorized host workflow; no live provider writes were tested.

### Gates

- Local checks pass. Cross-platform results are visible in [Actions](https://github.com/hungv47/horsemen/actions).
- Batch application and live Drive saves remain unavailable. Explicit local single-record updates are pending review.

</details>

## Historical ships

<details>
<summary>Historical ships</summary>

Earlier personal installations are not public releases of this repository.

</details>

## Upcoming roadmap

<details>
<summary>Upcoming roadmap</summary>

- Gather feedback from use of the unified project before adding scope.
- Safe automatic writes remain separate future work, with no promised date.

</details>
