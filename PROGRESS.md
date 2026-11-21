# Progress

Updated: 2026-11-21 · Stage: live · Health: On track

## Latest day

<details open>
<summary>Latest day</summary>

Next action: Finish the single GitHub App migration. Verify a live canvas save after the installation owner approves Contents read and write access.

Use the canvas editor and the hosted viewer on real projects and note what to improve; the open audit items are in docs/product/design-audit.md. Still note which you open first: the canvas of a record or its reading view.

## Shipped

- **Saves to protected branches** (2026-11-20): When GitHub does not allow a direct commit on the default branch, a canvas save goes to the branch `horsemen/canvas`, and the edit bar shows a link to open a pull request. Before, the save failed. Horsemen never opens the pull request and never writes another branch. Live on horsemen.forsvn.com.

- **Images, tables, and links in the canvas editor** (2026-11-20): In edit mode, a person can drop or paste an image (PNG, JPEG, GIF, WebP, 1 MiB or less), a CSV or TSV table, or a web address. One save is one commit with the canvas file and its new files in `.horsemen/media/`. Before the first file goes to a public repository, a dialog asks for confirmation. Live on horsemen.forsvn.com.

- **Junction logo** (2026-11-20): The owner asked for a more modern logo. The new app icon and favicon show four connected tiles for Vision, Progress, Brain, and Structure, and stay clear at 16 px. Live on horsemen.forsvn.com and in the local app from main.

- **Canvas editing in the browser** (2026-11-20): A person can add, move, connect, and remove cards on a canvas at horsemen.forsvn.com and save. Each save is one commit by that person, through a second, optional GitHub App, Horsemen Editor. People who only read see no new permission request; the public view and the local app stay read-only. Live on horsemen.forsvn.com.

- **Players and tables on canvases** (2026-11-20): A canvas link to YouTube, Vimeo, Loom, Figma, or a Google document, sheet, or slides shows a player that loads only after a click; nothing loads from the provider before. A CSV or TSV file on a canvas shows as a table. Live on horsemen.forsvn.com and in the local app from main.

- **Quiet Stop hook** (2026-11-20): The Stop hook blocked at every stop, so hosts that show only the last turn, such as T3 Code, hid each task report behind a note about the record review. Now it blocks only for new record drift, and then asks the agent to end with its full task report again. Available from main; the owner's global skill is refreshed. Other installations get it after a refresh.

- **Short session start for agents** (2026-11-20): A person can select a short start for agent sessions with `hooks install --pointer`. The agent then gets the next action and the gates in 700 characters or less and reads the rest when the task needs it. The Stop hook also tells the agent when it breaks a canvas, and when canvas files are not on GitHub yet. Off until a person selects it. Available from main; other installations get it after a refresh.

- **Canvas tools for agents** (2026-11-19): Agents can read a project in a few short calls and add notes, proof, and connectors to a canvas. `horsemen show` prints an index, one section, or a canvas outline; `horsemen canvas apply` checks and writes a canvas file; `horsemen mcp` gives the same two tools, `read` and `canvas_edit`, to Claude Code and Codex through a small local server. Section cards that agents add get the same IDs as the cards on the live site. Available from main; other installations get it after a refresh, and a person runs `horsemen mcp install` before a host gets the tools.

- **Canvas files** (2026-11-19): The sidebar now lists boards after the records. A canvas file in `.horsemen/canvas/` adds notes, images, link cards, groups, and labelled connectors to the canvas of a record, or makes a board, such as the [roadmap of this project](https://horsemen.forsvn.com/hungv47/horsemen?canvas=roadmap). A section card opens the reading view at its section. A file that is not valid shows a message and the generated canvas. Read-only. Live on horsemen.forsvn.com and in the local app from main.

- **Record canvases** (2026-11-19): The sidebar now has a project switcher and a list of canvases. Each record opens as a canvas with one card for each section, and a card opens the reading view at that section. A link such as `?canvas=progress&node=s-shipped` opens one canvas at one card. Read-only. Live on horsemen.forsvn.com and in the local app from main.

## In progress

- **Canvas workspace** (started 2026-11-19): All slices are on main and live: record canvases, canvas files, players and tables, agent tools and hooks, editing in the browser, media, and protected branches. Still open: the owner's use on real projects, and the one-week test of pointer mode.

### Technical details

| Item | Evidence |
| --- | --- |
| Saves to protected branches | Worker tests (`worker/test/protected.test.js`) cover classic protection, ruleset rules that block or do not block, a refused commit, the side branch missing, ahead, behind, diverged, in conflict, or deleted during the save, and a check that each write goes only to the default branch or `horsemen/canvas`, never forced or deleted. The browser check ends at the pull request link. Merged in [PR #44](https://github.com/hungv47/horsemen/pull/44) after CI passed; deployed from main, and the live files match main. Live check on 2026-11-21 in the fictional test repository hungv47/horsemen-canvas-test with `main` protected: the save made one commit on `horsemen/canvas` with the `main` head as parent, `main` did not move, and the compare page opens. The protection is off again. |
| Images, tables, and links in the canvas editor | Media rule tests (magic bytes, SVG refusal, sizes, names), edit tests, and Worker tests (`worker/test/media.test.js`): one GraphQL commit with paths that the Worker builds, size limits, path escapes, and a protected branch. The browser check drops an image, confirms the public warning, pastes a YouTube address and a CSV, and saves one commit with all files, byte for byte. Merged in [PR #45](https://github.com/hungv47/horsemen/pull/45) after CI passed; deployed from main, and the live files match main. Live check on 2026-11-21 in hungv47/horsemen-canvas-test: one commit by the owner with the canvas file and `.horsemen/media/poster-78544f2b.jpg` (116 KB); the canvas refers to the image by that path. |
| Junction logo | A logo study compared Junction, Fan, and Compass on light and dark backgrounds from 16 to 512 px; the owner chose Junction. The full verification command and the GUI check in all eight themes passed. Merged in [PR #43](https://github.com/hungv47/horsemen/pull/43) after CI passed; deployed from main. |
| Canvas editing in the browser | Worker tests (`worker/test/editor.test.js`, `worker/test/setup.test.js`) cover the editor sign-in, separate tokens, the write route gate (origin, CSRF, content type, size), invalid canvases, conflicts, and that the viewer app stays read-only. Edit tests (`tests/test_canvas_edit.cjs`) cover each draft operation and the conflict table. The browser check (`scripts/test_hosted_edit_e2e.py`) moves, adds, connects, saves, merges, resolves a conflict, and checks eight themes and phone width. Merged in [PR #41](https://github.com/hungv47/horsemen/pull/41) after CI passed; deployed from main. Live check on 2026-11-20 in hungv47/horsemen-canvas-test: the owner's save made commit `e711c6b` (`canvas(progress): add 1 [skip ci]`), authored by the owner, with only the canvas file changed, and started no Actions run. |
| Public view | Worker tests cover public and private repositories, no user token on public reads, repository routes only, cross-site requests, and the edge cache; the hosted browser check opens a public repository without sign-in. Merged in [PR #25](https://github.com/hungv47/horsemen/pull/25) and [PR #26](https://github.com/hungv47/horsemen/pull/26) after CI passed; deployed from main. GitHub refused anonymous reads from the shared Cloudflare IP (rate limit used up), so the Worker now reads public repositories with a read-only public token (5,000 requests an hour). Live checks: horsemen.forsvn.com/hungv47/horsemen opens in public mode and shows all seven records in a signed-out browser; a private repository still asks for sign-in; `/pub/user` returns 404 and cross-site requests return 403. |
| Diagrams and images | Markdown, media, reader parity, and Worker tests cover Mermaid figures, parse errors, theme colours, image links, path traversal, non-image files, SVG checks, the 1 MiB limit, and the CSP (`blob:` images only, no `eval`). The fixture and hosted browser checks draw diagrams in three themes and load repository images; full verification passed locally. Merged in [PR #27](https://github.com/hungv47/horsemen/pull/27) after CI passed; deployed from main, and the live files match main. Live check: the Tech stack record of hungv47/horsemen draws both of its diagrams in the public view. |
| Quiet Stop hook | Merged in [PR #38](https://github.com/hungv47/horsemen/pull/38) after CI passed. Hook scenarios (205), unit tests, and full verification passed. The owner's global skill was refreshed with `npx skills update horsemen -g -y` and matches main; a live check of the installed hook printed nothing for a clean stop and blocked for new folders. |
| Publish reminder | Hook scenario S20 passes: uncommitted and unpushed record edits fire once, published edits and repositories without a remote do not. All 150 hook scenarios and full verification passed locally. Merged in [PR #14](https://github.com/hungv47/horsemen/pull/14) after CI passed. The owner's global skill now installs from this repository and matches main; the Claude Code and Codex hooks run it. |
| Style themes | Theme tests check every theme and mode for contrast (4.5:1 for text, 7:1 in High contrast), the 12px floor, licensed fonts, and that each theme differs from the others in at least three style traits. The fixture browser check applies each theme, reloads it, checks its fonts, and checks for overflow at desktop and phone width. The hosted browser check, Worker tests, and full verification passed locally. Squash-merged in [PR #20](https://github.com/hungv47/horsemen/pull/20) after CI passed, with a fix for Terminal small-card titles; deployed from main, and the live files match main. |
| Calm workspace | [Design audit, minimal pass](docs/product/design-audit.md#minimal-pass-2026-11-19) and [artifact views](docs/product/artifact-views.md). Impeccable critique went from 27/40 to 31/40; the rendered-page detector went from 2 findings to 0 at desktop, tablet, and phone width. View, preview, theme, canvas, Worker, fixture browser, and hosted browser checks passed locally, and full verification passed. Squash-merged in [PR #18](https://github.com/hungv47/horsemen/pull/18) after CI passed; deployed from main, and the live files match main. |
| Players and tables on canvases | Unit tests for each provider address, unknown and look-alike hosts, and hostile addresses; table tests for CSV and TSV quoting, limits, and escaping; Worker and local tests check the same `frame-src` list. Browser checks with a fake player: no provider request before a click, the exact frame address and sandbox after it, tables in all eight themes and at phone width. Merged in [PR #39](https://github.com/hungv47/horsemen/pull/39) after CI passed; deployed from main, and the live files match main. Live check in the fictional test repository [hungv47/horsemen-canvas-test](https://horsemen.forsvn.com/hungv47/horsemen-canvas-test?canvas=live-check): before a click, no frame and no request to a provider; after the clicks, the real YouTube, Vimeo, and Google Sheets players load with no content security policy error; the CSV shows five rows; a look-alike YouTube host stays a link card. |
| Short session start for agents | [Hook reference](horsemen/references/hooks.md#pointer-mode) and the design's [hooks as built](docs/product/canvas-workspace.md#hooks-as-built). 204 hook scenarios passed from source and from the packaged skill; one compares the default mode byte for byte with the release before. CI passed on [PR #34](https://github.com/hungv47/horsemen/pull/34); merged to main in [PR #37](https://github.com/hungv47/horsemen/pull/37). Not done: the owner's one-week test of pointer mode on a real project. |
| Canvas tools for agents | [Canvas guide](horsemen/references/canvas.md), [shared format cases](tests/fixtures/canvas/README.md), and the design's [agent section](docs/product/canvas-workspace.md#agent-access-tools-cli-and-hooks). The Python canvas format, four `check` rules, `horsemen show`, `horsemen canvas apply`, `horsemen mcp install` and `status`, and the skill text. Unit, server (through a subprocess), budget, and distribution tests pass; the browser and Python readers agree on all shared cases, including section card IDs. A new Claude Code session and a new Codex session in a temporary fictional project each called `read` and `canvas_edit`. Full verification passed. Merged in [PR #32](https://github.com/hungv47/horsemen/pull/32) after CI passed. On this project, `horsemen show` lists the records and the roadmap board, and `check` passes. |
| Canvas files | Format, view, reader, and Worker tests; the browser reader passes the 73 shared cases. Browser checks, local and hosted, draw a hand-written canvas file, show a message for an invalid one, and cover hostile files (script text, `javascript:` addresses, CSS in a colour, `..` paths, 5,000 nodes, a 2 MiB file, an SVG with a script). Full verification passed. Merged in [PR #33](https://github.com/hungv47/horsemen/pull/33) after CI passed; deployed from main, and the live files match main. Live check: the first real canvas file, `.horsemen/canvas/roadmap.canvas` ([PR #35](https://github.com/hungv47/horsemen/pull/35)), opens at horsemen.forsvn.com/hungv47/horsemen?canvas=roadmap in a signed-out browser with its 13 elements, groups, section cards, and connectors. |
| Record canvases | Merged in [PR #30](https://github.com/hungv47/horsemen/pull/30) after CI passed; deployed from main, and the live files match main. Live check: a signed-out browser opened `hungv47/horsemen?canvas=progress&node=s-shipped` with the Shipped card selected, and the Vision canvas in List view at phone width. Tests: see the Canvas workspace row. |
| Canvas workspace | [Design](docs/product/canvas-workspace.md) with its [owner questions](docs/product/canvas-workspace.md#owner-questions), a [canvas file schema](docs/product/canvas.schema.json), and a [clickable mock](docs/show-me/canvas-workspace/index.html) with fictional data. The fixture check passed locally with a JSON Schema validator (`python3 docs/show-me/canvas-workspace/check.py --schema`), and the mock passed browser checks at desktop and phone width. VISION holds the proposed direction text. The owner approved the design, the VISION text, and all eleven proposed answers in [PR #29](https://github.com/hungv47/horsemen/pull/29). Slice 1 (generated canvases, read-only): [as built](docs/product/canvas-workspace.md#slice-1-as-built). Rule tests cover the same layout for the same record, no overlap, stable IDs, repeated headings, card text, and links (`node tests/test_canvas_sections.cjs`). Reader and Worker tests cover `canvas` and `node` in share links and through sign-in. The fixture and hosted browser checks open each canvas, open the reading view at a section, reload a link, and use the keyboard, at desktop and phone width and in each theme; full verification passed locally. A regression test covers a local server fault that the browser checks found: the server refused connections when many arrived at once. Merged in [PR #30](https://github.com/hungv47/horsemen/pull/30) after CI passed; deployed from main, and the live files match main. Live check: a signed-out browser opened `hungv47/horsemen?canvas=progress&node=s-shipped` with the Shipped card selected, and the Vision canvas in List view at phone width. |

### Gates

Existing installations do not change until refreshed. The local workspace stays a source preview and read-only. The hosted viewer stores no project data. Reading needs only the viewer app; saving needs the optional Horsemen Editor app, and each save is one commit by the person who saves. Public view covers public repositories only, read-only; private repositories need sign-in.

Canvas workspace: all slices are live. Saves write only canvas files and `.horsemen/media/` files, to the default branch or to `horsemen/canvas` when the default branch is protected; Horsemen never opens a pull request, forces, or deletes a branch.

</details>

## Historical ships

<details>
<summary>Historical ships</summary>

### 2026-11-19

- **Diagrams and images** (2026-11-19): Records now show Mermaid diagrams and charts, such as flowcharts, sequence diagrams, and pie and XY charts, in the colours of the active theme. Each one has a View code toggle. Images stored in the repository show in place when a record links to them. Live on horsemen.forsvn.com and in the local app from main.

- **Public view** (2026-11-19): Anyone can open the canvas of a public repository without signing in, for example horsemen.forsvn.com/hungv47/horsemen. Private repositories still need sign-in, and nothing is stored. Live on horsemen.forsvn.com.

- **Style themes** (2026-11-19): The owner asked for several themes that each look different. The account menu and Jump now show a gallery of eight themes: Engraved (default, with its six palettes), Modern, Editorial, Terminal, Swiss, Blueprint, Soft, and High contrast. Each theme has its own fonts, shapes, borders, shadows, spacing, canvas, and focus. Modern and High contrast replace the type sets for readable text. Live on horsemen.forsvn.com.

- **Calm workspace** (2026-11-19): The owner asked for a simpler screen and better record views. The workspace now shows few controls: the project list, one account menu, Jump, and Canvas or List. Cards show the record name and a few key lines. A record opens as one reading column; Progress starts with the next action, then the work now, then shipped work by day. Live on horsemen.forsvn.com.

- **Share links** (2026-11-19): Each project and record on horsemen.forsvn.com has a readable link, such as `/owner/repo?record=progress`, and a Copy link button. People with GitHub access to the repository open the same record after sign-in. Live on horsemen.forsvn.com.

- **Publish reminder** (2026-11-19): When an agent changes a record but the change has not reached the remote default branch, the Stop hook asks it to commit and push. Then the hosted viewer shows the update. Available from main; other installations get it after a refresh.

- **Readable type and design audit** (2026-11-19): The workspace now has three type sets: Engraved (default), Modern, and System. Choose one from the theme button or Ctrl/Cmd + K. Small labels are larger, phones open in List view, and keyboard focus is easier to see. The audit lists the fixes and the larger ideas still open. Live on horsemen.forsvn.com.

- **Faster hosted loading** (2026-11-19): A reload shows your projects at once from a saved list of repository names and paths, then checks for changes in the background. A first visit reads more repositories at the same time. Live on horsemen.forsvn.com.

- **Hosted viewer** (2026-11-19): horsemen.forsvn.com is live. People sign in with GitHub, choose repositories, and read their projects. Nothing is stored on the server. An open project updates when a new commit lands.

- **Views for each record type** (2026-11-19): Each record opens in a layout made for it. Progress groups work by day on a status board with proof links; other records get a brief, library, map, timeline, cards, or guide. Each type also has a list layout. Live on horsemen.forsvn.com and in the local app from main.

- **Visual workspace** (2026-11-19): A private local app shows each project as a canvas of its records. Each record opens in a peek with its own layout, a section outline, and a way to jump between records. It has six themes and reads GitHub through the existing sign-in. Available from main; run `python3 scripts/serve_gui.py`.

#### Technical details

| Item | Evidence |
| --- | --- |
| Share links | Link, Worker, and browser checks pass: a signed-out visitor returns to the shared record after sign-in; sign-in never redirects outside the app; a repository without access shows a clear message. Merged in [PR #16](https://github.com/hungv47/horsemen/pull/16) after CI passed; deployed from main, the live files match main, and a live share link keeps its target through sign-in. |
| Readable type and design audit | [Design audit](docs/product/design-audit.md). Theme and type tests, canvas rule tests, Worker tests, the fixture browser check, and the hosted browser check passed locally. Squash-merged in [PR #10](https://github.com/hungv47/horsemen/pull/10) after CI passed; deployed from main, and the live files match main. |
| Faster hosted loading | Benchmark with 80 repositories and 150 ms GitHub delay (`scripts/bench_hosted.py`): first project on reload 2.1 s to 0.36 s; first visit 2.2 s to 1.9 s; discovery 8.9 s to 5.9 s. Reader, Worker, and browser checks pass. Merged in [PR #9](https://github.com/hungv47/horsemen/pull/9) after CI passed; deployed from main, and the live files match main. |
| Hosted viewer | Merged in [PR #6](https://github.com/hungv47/horsemen/pull/6) and deployed from main; the live files match main, `/healthz` reports ok, and the live sign-in redirect was checked. Reader parity and Worker tests passed, and the hosted browser check passed against a fake GitHub: sign-in, project load, live update, and sign-out. Full verification passed locally. See [deploy and limits](worker/README.md). The owner signed in with a real account and saw the projects load on 2026-11-19. |
| Views for each record type | [Artifact views](docs/product/artifact-views.md). View tests (`node tests/test_gui_views.cjs`) and the fixture browser check passed locally at desktop and phone width; full repository verification passed locally. Merged in [PR #7](https://github.com/hungv47/horsemen/pull/7) after CI passed on Linux and macOS; deployed from main, and the live files match main. |
| Visual workspace | [Prototype](docs/show-me/product-gui/prototype.html), [canvas options](docs/show-me/product-gui/index.html), and [GUI requirements](docs/product/gui-requirements.md). Demo checks passed at desktop, tablet, and phone sizes; full repository verification passed locally. Run [the demo checks](docs/show-me/product-gui/verify.py) or the verification command in CONTRIBUTING.md. The owner chose a private local app first. Run `python3 scripts/serve_gui.py`; [setup and limits](web/README.md). Reader tests and fixture browser checks passed for discovery, source views, missing records, access failures, saved layouts, and clearing old content. Full source, wheel, and packaged-skill verification passed locally. Search and preview tests passed, including selection during an active scan. Live timing checks confirmed faster repeat loads; no private records were saved as test output. Linked-document tests cover source-authorized reads, nested navigation, external links, and visual overviews. Canvas rule and browser checks cover selection, group movement, drag cancellation, zoom, and shared branch collapse. Card controls passed mouse, keyboard, and list-view checks without selecting, dragging, or opening the card. Arrangement rule tests and browser checks found no overlap for nested and parallel branches. Browser checks passed in the light and dark themes; see [the icon system](docs/product/icon-system.md). Markdown, theme contrast, peek navigation, and reload checks passed locally. Merged in [PR #5](https://github.com/hungv47/horsemen/pull/5); CI passed on Linux and macOS. |

### 2026-11-17

- **Shorter records** (2026-11-17): Horsemen edits changed prose before saving. New source installs include the rule.

#### Technical details

| Item | Evidence |
| --- | --- |
| Shorter records | [Pre-save edit](horsemen/references/sync.md#pre-save-edit) and the distribution regression test. The source, wheel, and packaged skill checks passed locally. |

### 2026-11-13

- **Direct record commands** (2026-11-13): Brain, vision, structure and status have read-only reports and explicit local updates. Whole-project checks remain; planning tools share one menu. Available from main through the documented source installation.

- **Easy installation and a project cover** (2026-11-13): The README starts with the skills.sh install command and the original owner-approved cover.

- **One Horsemen project** (2026-11-13): Published source, one version, clear setup, and verification for both ways to use it.

#### Decisions

- Public repository and MIT license confirmed by the owner on 2026-11-13.
- Preserve private history in the original collection; publish only the checked source.

#### Technical details

| Item | Evidence |
| --- | --- |
| Direct record commands | [PR #1](https://github.com/hungv47/horsemen/pull/1), merged as [b9a9e5a](https://github.com/hungv47/horsemen/commit/b9a9e5a0538ddf03c72878d44d8464c23e0338b2). All four PR checks passed on Linux/macOS and Python 3.10/3.14. |
| Easy installation and a project cover | [README](README.md); skills CLI discovery and a temporary Codex installation matched the source; [original cover and verified checksum](assets/README.md). |
| One Horsemen project | [Public source](https://github.com/hungv47/horsemen) is available. Source, installed CLI, and unpacked-skill checks passed locally on 2026-11-13. Reproduce with [CONTRIBUTING.md](CONTRIBUTING.md). The private skills collection now points here. |

Existing installed copies are unchanged.

#### Command review evidence

- Full local verification passed on 2026-11-13: source tests, installed CLI,
  packaged skill and legacy hooks. Added coverage for each record, exact-edit
  validation, isolation, legacy callers and configured knowledge routes;
  simulated storage and read-back failures use disposable files. Reproduce
  with CONTRIBUTING.md. Remote main checks are published in Actions.
- Local writes require the caller to exclude other editors. Provider originals
  still use their authorized host workflow; no live provider writes were tested.

#### Gates

- Local checks pass. Cross-platform results are visible in [Actions](https://github.com/hungv47/horsemen/actions).
- Batch application and live Drive saves remain unavailable. Explicit local single-record updates are available from main.

Earlier personal installations are not public releases of this repository.

</details>

## Upcoming roadmap

<details>
<summary>Upcoming roadmap</summary>

- Hosted viewer next steps: branch and PR views. Public links to private repositories would need stored share settings.
- Gather feedback on the existing skill and CLI while developing the visual workspace.
- Safe automatic writes remain separate future work, with no promised date.

</details>
