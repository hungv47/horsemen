# Local GitHub workspace

Open real Horsemen projects as a calm canvas. Double-click a record to read it
or inspect its exact Markdown. Each record also opens as a canvas of its
sections. The local app reads GitHub; it does not edit files.

From this source checkout, with Python 3.10+ and GitHub CLI installed:

```sh
gh auth status
# If needed: gh auth login
python3 scripts/serve_gui.py
```

Open <http://127.0.0.1:8787>. Use `--port 8790` if that port is occupied.
The first visit scans repositories available to the active github.com account.
Refresh GitHub (in the account menu) repeats discovery. Clear workspace
removes the in-memory scan; it does not sign out of GitHub. Stop the server
with Ctrl+C.

The same app also runs as a hosted viewer with GitHub sign-in. The hosted site uses one GitHub App to read records and save canvases
(see [edit a canvas](#edit-a-canvas-hosted)).
See [the hosted viewer](../worker/README.md).

## Reading and navigation

The screen shows few controls. Everything else is in one of three places:
the account menu, the Jump field, and the keyboard.

- **Rail.** The rail has the project switcher, then the canvases of the open
  project: Home, each record that the project has, and then the boards (see
  [canvas files](#canvas-files)). Select the switcher to
  see your projects. A lock marks a private repository. A search field
  appears when you have more than eight projects. Multiple search words
  narrow the result. Nested project roots are separate entries. The Up and
  Down arrow keys move in the list; Escape closes it. A project opens on the
  canvas that you used last, until the page reloads. In hosted mode, the
  list also has Connect a repository.
- **Account menu.** Select your account name at the bottom of the rail. The
  menu holds Refresh GitHub (with the time of the last check), the theme
  gallery, and Clear workspace. In hosted mode it also holds Choose
  repositories and Sign out.
- **Header.** The header names the open canvas: the project on Home, the
  record on a record canvas, the board on a board. One line follows: the
  number of sections (on a record canvas), the number of elements from the
  canvas file, the repository, when PROGRESS says it was updated, and the
  commit that the app read. It has Jump, Canvas or List, and in hosted mode
  Copy link.
- **Jump.** Press Ctrl + K (Command + K on macOS) or select Jump. One field
  reaches each record, canvas, linked document, project, canvas action, and
  theme. Canvas actions include Fit, Select tool, Hand tool, Open the
  selected card, Collapse all linked branches, Reset layout (on Home),
  Refresh GitHub, and Clear workspace.
- **Shortcuts.** Press `?` or choose Keyboard shortcuts in Jump to see every
  key.
- The status line under the header shows only while discovery runs, after
  an error, or after Clear workspace. Problems with a repository show under
  it until they are fixed.

### Record canvases

Select a record in the rail to open its canvas. The canvas is generated from
the record each time. It needs no file, and the app saves nothing about it.
A [canvas file](#canvas-files) can add elements to it.

- The canvas has one card for each second-level heading (`## Heading`), in
  reading order, in three columns. A card shows the heading and a few lines
  from that section. It shows a count when the section has two or more list
  items or table rows. These are excerpts, not generated claims.
- Each card has a stable ID: `s-` and the heading in lower-case letters,
  digits, and hyphens, such as `s-in-progress`. A repeated heading gets `-2`,
  `-3`. A record without second-level headings shows one card for the whole
  record.
- The layout is fixed. The same record gives the same canvas to each person,
  and a new last section does not move the cards before it. You cannot move
  a section card; a drag that starts on a card moves the canvas.
- Click selects a card. Enter or double-click opens the reading view at that
  section, over the canvas. The view uses the layout of the record when the
  layout names the section; if not, it uses the full document. Close the
  view to return to the same card.
- List view shows the same cards in reading order. One click opens a card.
- A record canvas without a canvas file has no connectors. Connectors
  between cards come from a [canvas file](#canvas-files). Home keeps its
  connectors between records and linked documents.
- The address names the canvas and the selected card. In the local app it is
  `#p=<project>&c=progress&n=s-shipped`; `&r=progress` is added while the
  reading view is open. The hosted form is
  `/owner/repo?canvas=progress&node=s-shipped`. A link to a section whose
  heading changed opens the canvas and says that the card is not there.
  Links from before canvases, such as `?record=progress`, open the record
  over Home as before.

### Canvas files

A canvas file is a JSON Canvas 1.0 file in `<project root>/.horsemen/canvas/`,
such as `.horsemen/canvas/progress.canvas`. A person or an agent writes the
file and pushes it. The app reads it and draws it. The local app and the
public view do not change it. In the hosted app, a person with the editor app
can [edit a canvas](#edit-a-canvas-hosted). The format and its limits are in
[the canvas workspace design](../docs/product/canvas-workspace.md#canvas-file-format).

- **Which canvas.** A file with the name of a record (`vision`, `progress`,
  `brain`, `structure`, `readme`, `changelog`, `techstack`) belongs to the
  canvas of that record. A file with another name is a board. The rail lists
  the boards after the records, in name order, with the name in title case
  (`launch-plan` shows as "Launch plan"). A project can have 20 canvas files.
- **A record with a file.** The elements of the file show at their saved
  places and sizes. Each section that the file does not place still shows as
  a generated card, in one column at the left of the saved elements. The
  cards do not overlap, and the same input gives the same layout.
- **Elements.**

  | Element | In the file | Shows as |
  | --- | --- | --- |
  | Note | `text` node | Markdown from the same safe renderer as the records. |
  | Section card | `file` node with a `.md` file and a `subpath` (`#Heading`) | The live text of that section. A card of another record says "from Progress". Enter or double-click opens the reading view of that record at the section. |
  | Record or document | `file` node with a `.md` file and no `subpath` | A card that opens the record or the document in the reading view. |
  | Portal | `file` node with a `.canvas` file of the same project | "Open canvas". Enter or double-click opens that canvas. |
  | Image | `file` node with a PNG, JPEG, GIF, WebP, or SVG file | The image, from a `blob:` address, with its `alt` text. The limit is 1 MiB for a file and 100 images for a canvas. |
  | Table | `file` node with a CSV or TSV file | A table: the first row is the header, then the first 200 rows and 30 columns. A long or wide table scrolls in its card. The limit is 1 MiB for a file and 20 tables for a canvas. |
  | Other file | `file` node with another file, such as XLSX | A file card with a link to the file on GitHub. |
  | Player | `link` node with a YouTube, Vimeo, Loom, Figma, Google Docs, Google Sheets, or Google Slides address | "Load video" or "Load preview". The player loads only after you select the button. See [players and tables](#players-and-tables). |
  | Link card | `link` node with another address | The stored `title`, the host, and "Open link". The app fetches nothing from the address. |
  | Group | `group` node | A frame with its label, behind the other elements. |
  | Connector | edge | A curve with an arrow and its label. |
  | Other type | any other node type | "Not supported". |

- **Colours.** A preset (`"1"` to `"6"`) takes a colour of the active theme.
  A hex value (`#RRGGBB`) shows as written. The colour shows as a stripe on
  the element in each theme.
- **A file that is not valid.** The app shows one message above the canvas,
  with a link to the file on GitHub, and the rail marks the canvas. For a
  file that is not JSON, is too large, or breaks a limit, no element of the
  file shows: a record shows its generated canvas, and a board is empty. For
  a file with some elements that are not valid, the other elements show, and
  the message gives the count and the first fault. Select "Show 3 faults"
  (with the count of your file) to see the list.
- **Section not found.** A section card whose heading is not in the record
  now says "Section not found". The card still opens the record. A portal to
  a canvas that the project does not have says "Canvas not found".
- **Selection and links.** Click selects an element. Enter selects the
  element that has focus; Enter again opens it when it can open. An element
  has a fixed place: a drag that starts on it moves the canvas. The address
  names the canvas and the selected element, such as
  `#p=<project>&c=launch-plan&n=note-risk` or
  `/owner/repo?canvas=launch-plan&node=note-risk`. A link inside a note or a
  card stays a link.
- **List view.** The list shows each element in reading order: the elements
  outside groups from top to bottom, then each group with its elements. An
  element names its connectors as text lines, such as "proof → Pilot board".
  The list is the form of a canvas for a phone and for assistive technology.

Not in this step: an XLSX preview, group background
images, a canvas file for Home (`home.canvas` is not shown), and the overview
of references between canvases.

### Players and tables

A link card for a known provider shows a player. A CSV or TSV file shows as a
table. The rules are in `web/canvas-embeds.js` and `web/canvas-table.js`.

- **Before you select the button.** The card shows the title, a button, the
  host, and "Open on YouTube" (or the provider name). The browser contacts no
  provider: there is no frame and no thumbnail.
- **After you select the button.** The app makes a frame with the sandbox
  `allow-scripts allow-same-origin allow-presentation`. The app builds the
  frame address from an ID that it reads from the stored address, such as
  `https://www.youtube-nocookie.com/embed/<ID>`. A stored address never goes
  into a frame. The provider then sees your IP address and the site origin.
  Only the YouTube frame sends the site origin as the referrer, because the
  YouTube player needs it; no frame sends the repository path.
- **Addresses that give a player.**

  | Provider | Addresses | Frame |
  | --- | --- | --- |
  | YouTube | `youtube.com/watch?v=`, `youtu.be/`, `/embed/`, `/shorts/`, `/live/`; a `t` or `start` time | `www.youtube-nocookie.com/embed/<ID>` |
  | Vimeo | `vimeo.com/<ID>`, `vimeo.com/<ID>/<hash>`, `vimeo.com/channels/<name>/<ID>`, `player.vimeo.com/video/<ID>` | `player.vimeo.com/video/<ID>?dnt=1` |
  | Loom | `loom.com/share/<ID>`, `loom.com/embed/<ID>` | `www.loom.com/embed/<ID>` |
  | Figma | `figma.com/file`, `/design`, `/proto`, `/board`, `/slides`, or `/deck` with a file key; a `node-id` | `www.figma.com/embed?embed_host=horsemen&url=…` |
  | Google Docs, Sheets, Slides | `docs.google.com/document/d/<ID>`, `/spreadsheets/d/<ID>`, `/presentation/d/<ID>`, and published `/d/e/<ID>` files | `/preview`, or `/embed` for slides |

  Any other address, also a look-alike host such as
  `youtube.com.example.net`, stays a link card.
- **When the player stays empty.** A provider can refuse the frame, or you
  can have no access to the file. Then use "Open on …" in the card. A private
  Google file asks for a Google sign-in, which the page does not allow in a
  frame.
- **Tables.** The first row is the header. A field in double quotes can hold
  a comma, a tab, a line break, or a doubled quote. A column of numbers
  aligns right. Each cell is text: no cell becomes a link or markup. The line
  under the table gives its size, such as "Shows 200 of 1,234 rows and 30 of
  45 columns." A file that is not UTF-8 text, is larger than 1 MiB, or is a
  Git LFS pointer shows a message and the link to GitHub.
- **Keyboard and pointer.** Tab reaches the button of a player; Enter or
  Space loads it. Over a table, the wheel and the arrow keys scroll the table;
  Ctrl or Cmd with the wheel still zooms the canvas.
- **List view and phones.** A player keeps its shape (16:9 for a video). A
  table scrolls inside its card. A live update of the canvas draws the cards
  again, so a loaded player returns to its button.

### Edit a canvas (hosted)

Sign in to the hosted app and open a record canvas or a board. Public and local views are read-only.

1. Select **Edit**. The repository must be selected in the Horsemen installation and your account must have push access. If GitHub asks for updated permissions, the installation owner must approve Contents read and write access.
2. Edit. A bar shows the actions and the state of the draft.

   | Action | Mouse | Keyboard |
   | --- | --- | --- |
   | Move | Drag an element. A section card that the record makes is saved into the file when it moves. | Arrow keys move the selected elements (Shift: 10 px, Alt: 20 px). |
   | Add a note | **Add note**. The note goes in free space in the middle of the view. | N |
   | Edit a note | Double-click the note. The text is Markdown. | Enter on the selected note; Ctrl + Enter closes the editor. |
   | Connect | Select two elements (Shift-click), then **Connect**. The connector goes from the first to the second. With a connector between them, the button is **Disconnect**. | C |
   | Add an image or a table | **Add file**, drop a file on the canvas, or paste an image. PNG, JPEG, GIF, and WebP images and CSV and TSV tables of 1 MiB or less. A drop puts the card where you drop it. | Ctrl + V (Command + V on macOS) |
   | Add a link or a player | **Add link**, or paste or drop an address. A YouTube, Vimeo, Loom, Figma, or Google address gets a player that loads only after a click; another address gets a link card. | L, or Ctrl + V |
   | Paste a table or text | Paste rows with the same number of commas or tabs on each line: they become a CSV or TSV file. Other text becomes a note. | Ctrl + V |
   | Delete | **Delete**. The connectors of an element go with it. A section card that the record makes stays. | Delete or Backspace |
   | Save | **Save**, then **Commit** in the preview. | Ctrl + S (Command + S on macOS) |

3. The preview shows the file, the new media files with their sizes, the
   commit message, the branch, and the changed elements. For a public repository it says that anyone can see the
   canvas. One save is one commit by you on the default branch, with a
   message such as `canvas(progress): add 1, move 2 [skip ci]`.

   When the default branch is protected, the bar says **Saves to
   horsemen/canvas**. The save goes to the branch `horsemen/canvas`, without
   `[skip ci]`, and the default branch does not change. After the save, the
   bar links **Open a pull request**, or **Pull request #N** when one is
   open. Open the pull request on GitHub to merge the change. The draft
   starts from the file on `horsemen/canvas`, so earlier saves stay. The
   canvas shows the default branch until the pull request merges.
4. If the file changed on GitHub since your draft started, the app merges
   the two versions by element ID and saves again. When the same element
   changed on both sides, a dialog asks which version to keep for each
   element. When the 60-second check finds a new commit while a draft is open,
   the bar says so and offers **Merge now**.

The draft stays in this browser tab until you save or discard it; **Done**
asks first. The page warns before it closes with an unsaved draft, and
sign-out removes drafts.

Files that you add (slice 4b):

- A file gets the name `<name>-<8 hex characters of its SHA-256>.<type>`
  in `.horsemen/media/` of the project, for example
  `.horsemen/media/harbour-route-1a2b3c4d.png`. The type comes from the
  bytes of the file, not from its name. The same file always gets the same
  name.
- Until you save, the file shows from memory in this tab. The save sends the
  canvas and its new files together: one commit.
- A save holds four new files at most. Save, then add more.
- Before the first file goes to a public repository, a dialog asks you to
  confirm: anyone can see the file, and Git history keeps it after you delete
  it.
- The app refuses SVG files, videos, files over 1 MiB, and other types. For a
  video or a large file, put it on a host and paste its address.
- Removing a card does not delete its file.

- On a protected default branch, the files go to `horsemen/canvas` with the
  canvas. The viewer shows them after the pull request merges.

Not in this step: resize, groups, colours, undo, and a choice of the target
branch.

### Home canvas

- Each card shows the record name and a few key lines from the source. These
  are excerpts, not generated claims. The icon has the colour of the record.
  Open the card for full context.
- Click to select; Shift-click adds or removes a card. Drag an empty area to
  select several cards, then drag the selection to move it together.
- Press `V` for the Select tool and `H` for the Hand tool. Space + drag pans
  even over a card. Middle or right mouse drag also pans. Scroll pans;
  Ctrl/Cmd + scroll or pinch zooms. The zoom control in the corner zooms and
  fits the map.
- Enter or double-click opens the selected card. Arrow keys move selected
  cards by one pixel; Shift + arrows moves them by ten. Escape cancels an
  unfinished drag or clears the selection. Shift + 1 fits the map; Shift + 2
  fits the selection. `0` resets zoom to 100%.
- The link count on a card expands or collapses its linked items. No
  selection is required. Unopened Markdown documents load their links on
  demand. These controls also work in List view. Shift + C collapses all
  branches. Shared documents stay visible while another expanded branch
  reaches them. Linked cards that appear take free space beside their parent,
  so cards do not overlap. Cards you moved keep their place. Reset layout (in
  Jump) arranges all links again. Deeper exploration reveals the ancestor
  path.
- List view keeps single-click opening. These controls follow the navigation
  pattern in [Excalidraw](https://plus.excalidraw.com/changelog); this app does
  not include freehand drawing, shape editing, or the Excalidraw editor.
- On a screen 640px wide or less, the app opens in List view, so cards stay
  readable. Select Canvas to see the map. The project switcher sits beside
  the app icon, and the canvases are one row that scrolls sideways.

### Record view

- A record opens as one reading column of about 70 characters. The header
  shows the record name and the facts that the record states, such as
  "Updated yesterday" and "Stage: pilot". Header actions: Copy link (hosted
  mode), Open on GitHub, the ⋯ menu, and Close.
- The ⋯ menu shows the record in its two layouts, as the full document, or
  as its exact Markdown source. The browser saves the layout choice for each
  record type. "Read the full document" at the end of a layout is one more
  way to see everything.
- Each type has its own layout. See [artifact views](../docs/product/artifact-views.md).
  Progress: the next action first, then Now (work in progress and items that
  need attention), Up next, and shipped work by day, newest first. Proof
  links are small chips. The board is the second layout. Vision: the purpose
  sentence, then simple sections. Brain: the sources, each with its access
  line. Structure: the tree, with Copy buttons for commands. Changelog: a
  dated list. Tech stack: a compact table. README and linked documents: the
  rendered document.
- Dates show as relative time, such as "2 days ago". Hover shows the exact
  date. Each item has a small link to its source line (`L12`).
- The left column lists the records. "On this page" appears only for long
  records. The path above the page appears when you open a linked document;
  each step goes back. Use the left and right arrow keys, or the arrows at
  the end of the page, to change record.
- On a phone, the record view fills the screen.
- The address keeps the selected project, the open canvas, the selected
  section card, and the open record. A reload returns to the same place.
- Linked repository Markdown opens inside the app at the same scanned commit.
  External documents and other file types show the link and its source.
  Horsemen does not fetch their contents. Missing and unreadable files show
  an error without replacing the parent record.
- Changelog PR links can load merge details and the PR description. Image
  attachments appear as links. A merge alone is not proof of delivery.

## Design

The default look is a calm reading desk: bone paper, ink, and one pigment
for each record. Vision is gilt, Progress is vermilion, Brain is indigo, and
Structure is verdigris. The pigment appears on the record icon and a few
labels only. Names and icons carry the same meaning without colour.

### Themes

Open the account menu or Jump (Ctrl/Cmd + K) to choose a theme. Each tile
shows a small card and a line of text in that theme's own fonts and colours.
A theme applies at once. The browser saves it and applies it before first
paint, so the page does not flash. Each theme sets its own fonts, corner
radius, borders, shadows, spacing, canvas, accent, and focus ring.

| Theme | Look | Modes | Fonts |
| --- | --- | --- | --- |
| **Engraved** (default) | Carved titles and book text on bone paper | Six palettes | Cleft, Gravure, Halden, Vellum, Signal |
| **Modern** | A clean product interface: grey, rounded, one blue accent | Light, dark | Beacon, Signal |
| **Editorial** | A newspaper page: Didone titles, double rules, no shadows | Light | Opaline, Folio, Signal |
| **Terminal** | A phosphor screen: monospace, dashed borders, amber accent, compact | Dark | Diode titles, device monospace |
| **Swiss** | A column grid, a bold grotesk, black and white, one red | Light | Halden, Signal |
| **Blueprint** | White line work on a blue field, a grid, corner ticks, mono labels | Dark | Tessera, Signal |
| **Soft** | Pastel colours, very round corners, wide spacing, soft shadows | Light, dark | Brioche, Mallow, Signal |
| **High contrast** | Black and white, larger text, 2px borders, a thick focus ring | Light, dark | Beacon, Signal |

The selected tile shows its options. Engraved shows its six palettes: Bone
and Ink, and one for each horse (White, Red, Black, and Pale). System
chooses Bone or Ink from the device. A theme with a light and a dark mode
shows System, Light, and Dark; System follows the device.

For easier reading, choose Modern or High contrast. They replace the
earlier type sets: a browser that saved the Modern or System type set opens
in the Modern theme. The hosted sign-in page stays Engraved, but it uses the
Beacon type for people who chose Modern or High contrast.

A test checks every theme and mode. Text and pigments meet a 4.5:1 contrast
ratio (7:1 in High contrast), focus rings meet 3:1, and text is 12px or
larger. Motion stops when the system asks for reduced motion.

### Fonts

The browser downloads only the fonts of the active theme, and theme.js
preloads only its main files. The theme gallery shows a live preview of each
theme, so the first time it opens, it loads one or two fonts for each theme.
Fonts come from [fontzz](https://fontzz.vercel.app) and are served locally.
See [the font notice](assets/fonts/NOTICE.txt) and
[their licence](assets/fonts/OFL.txt). Icons, seals, and the app icon are
original; see [the icon system](../docs/product/icon-system.md). The latest
design audit and its open items are in
[the design audit](../docs/product/design-audit.md).

## Boundaries

This is a source-only local preview, not a hosted or multi-user service.
The wheel and skill do not include the web assets. There is no public sharing,
OAuth app, file editing, webhook, local-folder import, or background refresh.

Canvas files are untrusted input. The app checks each file with the rules
in `web/canvas-format.js` before it draws an element. Text from a file is
always text: a note goes through the Markdown renderer, and each other value
is escaped. A link address must start with `http://` or `https://`. A colour
is a preset or `#RRGGBB`. A path cannot leave the project. A file larger
than 512 KiB is not requested. An SVG image shows only as an image from a
`blob:` address, so its script does not run, also when a person opens that
address as a page. The app reads only the files that a loaded canvas names.
A table cell is always text. A player frame loads only after a click, from an
address that the app builds, and the content security policy allows frames
from five origins only (see [players and tables](#players-and-tables)).

Discovery reads default branches, including archived repositories. A project
needs at least two core records and either VISION or PROGRESS (legacy STATUS
is supported). Missing records are reported. Truncated repository trees are
reported as incomplete scans. Files larger than 512 KiB are not loaded.
Markdown supports headings, wrapped paragraphs, nested and numbered lists,
task lists, tables, quotes, rules, fenced code, links, and simple expandable
sections. Fenced `mermaid` blocks show as diagrams and charts. Relative image
links to PNG, JPEG, GIF, WebP, or SVG files up to 1 MiB show the image; other
images appear as links. Other HTML is shown as text. Footnotes and
reference-style links are not supported; exact source is always available.
PR comments are not scanned.
Connections currently use inline Markdown links, excluding code examples and
comments. Reference-style and HTML links are not indexed. A document exposes
up to 200 links; a project retains up to 4,000 link targets per scan. Only a
link found in an already-loaded record can authorize another repository read.
The peek history holds up to 32 levels; Back and project changes release it.

The server binds only to 127.0.0.1. It reads credentials locally through `gh`;
they never reach the browser. Requests are read-only. Repository metadata and record contents are not saved to disk
by the app. The browser stores only opaque project IDs, the positions of Home cards, the theme, palette, and mode choices, and the layout choice for each record type. It stores nothing about record canvases, boards, or canvas files.
In hosted mode, the browser also keeps a discovery index without record text; see
[fast reloads](../worker/README.md#how-it-works).
External images do not load automatically. Opening an external link leaves
the local app. Do not expose this server through a tunnel or reverse proxy.
After switching GitHub accounts, refresh discovery. Project loads also check
the local credential identity and reject account changes. The remote account
check is reused for up to 30 seconds; revocation of an unchanged credential
can take that long to invalidate cached content.

Records and canvas files load in parallel. Up to 16 projects are cached in
server memory at the scanned revision. Refresh and Clear workspace discard
this cache. Failed record and canvas loads are retried instead of cached.
Nothing is written to disk.

## Verification

```sh
python3 -m unittest discover -s tests -p 'test_gui*.py'
node tests/test_gui_previews.cjs
node tests/test_gui_views.cjs
node tests/test_gui_markdown.cjs
node tests/test_gui_themes.cjs
node tests/test_canvas_state.cjs
node tests/test_canvas_sections.cjs
node tests/test_canvas_format.cjs
node tests/test_canvas_view.cjs
python3 scripts/test_gui_e2e.py --output /tmp/horsemen-gui-check
```

`tests/test_canvas_format.cjs` checks the reader of canvas files. It also
runs the shared cases in `tests/fixtures/canvas/`, which the Python reader
runs too, so both readers accept and refuse the same files with the same
errors. When that folder is not in the checkout, the test reads the cases
from the Git branch `origin/canvas/agent-tools`; with neither, it says that
it skipped them. `tests/test_canvas_view.cjs` checks how a file and a record
become one drawing.

The browser check needs `agent-browser`. It uses fictional GitHub fixtures,
checks reading/source views, canvas files (`scripts/canvas_fixture.py`), and
browser safety, and saves screenshots and command output outside the
repository. Full package checks remain in
[CONTRIBUTING](../CONTRIBUTING.md).
