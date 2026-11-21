# Hosted viewer

A Cloudflare Worker that serves the Horsemen visual workspace to anyone who
signs in with GitHub. It keeps no project data. One GitHub App supports reading and saving canvas edits on selected repositories. Public viewing requires no sign-in.

## How it works

```text
browser ──/gh/* (CSRF token + encrypted cookie)──▶ Worker ──user token──▶ GitHub API
   ▲  parses records (web/hosted-reader.js)            │ allowlisted GET calls only
   └──────────────── JSON passes through ◀─────────────┘ nothing logged or stored
```

- **Sign-in.** A GitHub App with "Request user authorization". The user
  installs the app on the repositories they choose. The user token can only
  read repositories that the user can access and the app is installed on.
- **Session.** The token lives in an AES-GCM encrypted `__Host-` cookie that
  is HttpOnly, Secure, and SameSite=Lax. There is no database, KV, or server
  session store. Expiring tokens refresh through `/auth/refresh`.
- **Reads.** The Worker forwards only these GET calls: the user, installations,
  installation repositories, branch commits, trees, blobs, contents at a
  revision, and pull requests. It drops unknown query keys and rejects path
  traversal. GitHub error text is never passed to the browser.
- **Parsing.** The browser runs `web/hosted-reader.js`, a port of the Python
  reader. `tests/test_hosted_reader.cjs` checks that both produce the same
  links, sections, project roots, and canvas file lists.
- **Canvas files.** The reader finds `.horsemen/canvas/<name>.canvas` in the
  tree that discovery already reads, so this costs no extra request. When a
  project opens, the browser reads each canvas file (20 at most) as a blob,
  checks it with `web/canvas-format.js`, and draws it. A file larger than
  512 KiB is not requested. An image that a canvas names loads through the
  contents route when it comes into view; a CSV or TSV file loads the same
  way and shows as a table. The Worker has no new route and no
  new permission: canvas files and their media use the blob and contents
  reads that are already on the list, in the signed-in view and in the
  public view. The server does not parse or keep a canvas file. See
  [canvas files](../web/README.md#canvas-files).
- **Live updates.** While a project is open and its tab is visible, the browser
  checks the branch every `POLL_SECONDS` (default 60) with an ETag. An
  unchanged branch returns 304, which GitHub does not count against the rate
  limit. A new commit reloads the project; an open record waits until it closes.
- **Fast reloads.** After discovery, the browser saves a discovery index in
  `localStorage`: repository names, record paths, revisions, and ETags. It
  never saves record text or canvas text; for a canvas file it keeps the
  path and the SHA. A reload shows the projects at once and opens the
  last project, then checks every branch in the background. Only changed or
  new repositories are scanned again. Sign-out and Clear workspace remove the
  index. Discovery reads up to 12 repositories in parallel.
- **Share links.** Every project, canvas, section card, and record has a
  readable link. `https://horsemen.forsvn.com/owner/repo?record=progress`
  opens a record. `?canvas=progress` opens the canvas of a record, and
  `?canvas=progress&node=s-shipped` opens it with one section card selected.
  `?canvas=launch-plan&node=note-risk` opens a board at one element.
  A project in a subfolder adds `root=apps%2Fweb`. The address bar always
  shows the link for the open project, canvas, card, and record; **Copy
  link** in the header and in the record copies it. A signed-out visitor
  signs in and returns to the same link: sign-in keeps `root`, `canvas`,
  `node`, and `record`, checks the form of each value, and drops other keys. The
  link carries no data: the visitor needs GitHub access to the repository, and
  the app must be installed on it. Otherwise the page says so. Agents can write
  these links in reports without any API.
- **Public view.** A link to a public repository, such as
  `https://horsemen.forsvn.com/hungv47/horsemen`, opens without sign-in. The
  Worker first checks that the repository is public, then reads it through
  `/pub/...` without any user token. It reads only repository routes. GitHub
  allows 60 such requests an hour per Cloudflare IP; set the optional secret
  `GITHUB_PUBLIC_TOKEN` (a fine-grained token with public read access and no
  permissions) for 5,000 an hour. Public data is cached at the edge: repository
  details and branch heads for 60 seconds, objects addressed by SHA for a day.
  A repository made private stops working within 60 seconds. The browser
  keeps nothing for a public view. A signed-in user can add `?view=public` to
  see what visitors see. Private repositories still need sign-in.
- **Diagrams and images.** A fenced `mermaid` block shows as a diagram or
  chart. The browser loads `web/vendor/mermaid.min.js` (Mermaid 12.3.0, MIT)
  only when a record has one, and draws it with `securityLevel: "strict"`.
  The CSP still blocks `eval` and inline scripts. A relative image link, such
  as `![Board](docs/img/board.png)`, shows the image when the file is in the
  repository at the scanned commit. The browser reads it through the same
  read-only proxy and shows it from a `blob:` URL; SVG files load as images,
  so their scripts never run. External images stay links. Images larger than
  1 MiB stay links.
- **Canvas editing.** Optional. See [canvas editing](#canvas-editing).
- **Agents.** Agents update records and canvas files the normal way: edit,
  commit, and push. A canvas file that an agent writes by hand shows after
  the push, at the next check of the branch. A file that is not valid shows
  a message and the generated canvas of the record.
  The viewer shows the default branch, so unpushed edits do not appear. The
  Horsemen Stop hook reminds the agent when a record it changed has not
  reached the remote default branch (see the Publish rule in
  [hooks](../horsemen/references/hooks.md)).

## Canvas editing

A person can move elements, add and edit notes, add images, tables, links,
and players, connect and delete elements on a record canvas or a board, and
save. Each save is one commit by
that person. The Worker uses the signed-in person's token for the save. The installation must grant Contents read and write access, and the person must have push access to the repository.

- **The write route.** `POST /write/canvas` is the only write. It needs the
  session cookie with an editor token, an `Origin` header of this site, the
  CSRF token, `Content-Type: application/json`, and a body of 6 MiB or less.
  The body has exactly `repo`, `root`, `canvas`, `base` (the blob SHA of the
  file that the draft started from, or `null`), and `text`, and `media` when
  the save adds files. The Worker builds
  the path `<root>/.horsemen/canvas/<canvas>.canvas` and the commit message
  `canvas(<canvas>): add 1, move 2 [skip ci]` from counts. It checks the text
  with the same reader as the browser (`web/canvas-format.js`) and writes the
  canonical text. The browser never sends a path, a branch, or a message.
- **Media.** `media` is a list of one to four `{ "name", "data" }` items:
  a name in the form `<stem>-<8 hex>.<png|jpg|gif|webp|csv|tsv>` and the
  bytes in base64. The Worker refuses a name that is not in this form, base64
  that is not strict, a file over 1 MiB, bytes that are not the type of the
  extension (magic numbers for images; UTF-8 text without NUL and not a Git
  LFS pointer for tables), a hash that is not the SHA-256 of the bytes, and a
  file that the canvas does not name. SVG is refused. A new file node that
  names a file in `.horsemen/media/` must have that file in the save or on the
  canvas on GitHub. The Worker builds each path, and writes only
  `<root>/.horsemen/canvas/` and `<root>/.horsemen/media/`. The rules are in
  `web/canvas-media.js`, shared with the browser.
- **The GitHub call.** A save without media uses the REST contents API (one
  `PUT`). A save with media uses the GraphQL `createCommitOnBranch` mutation:
  one commit for the canvas and its files, on the default branch or on
  `horsemen/canvas`. The mutation names the head that the Worker read
  (`expectedHeadOid`).
- **Conflicts.** The Worker reads the file on the default branch. A blob SHA
  that is not `base` returns `409` with `code: "conflict"` and the current
  SHA; the browser reads that file, merges by element ID
  (`web/canvas-edit.js`), and saves again. When the branch head moves during
  the commit, the Worker tries again, three times at most. With media, the
  Worker reads the head of the target branch, then the canvas at that commit,
  and names that head in the mutation. After a refused mutation it reads the
  head again: a moved head is tried again with a new conflict check; an
  unmoved head is a refusal (on the default branch, the save goes to
  `horsemen/canvas`).
- **Protected branches.** When GitHub does not allow a direct commit on the
  default branch (classic branch protection, a ruleset rule such as
  `pull_request` or `update`, or a refused commit), the Worker saves to the
  branch `horsemen/canvas`. It makes the branch from the head of the default
  branch, fast-forwards it, or merges the default branch into it. It never
  forces or deletes a ref, and it writes no other branch. The reply adds
  `branch`, `default_branch`, and `pull_request.compare_url`. The message has
  no `[skip ci]`, so the checks of the pull request run. Horsemen does not make
  the pull request; the person opens it on GitHub. `GET /write/target` tells
  the editor where the next save goes, with reads only. See
  [slice 4c as built](../docs/product/canvas-workspace.md#slice-4c-as-built).
- **Drafts.** A draft stays in the browser tab (`sessionStorage`) until it is
  saved or discarded. Sign-out removes drafts. The page warns before it
  closes with an unsaved draft.
- **What stays read-only.** The public view (`/pub/*`) and the read proxy
  (`/gh/*`) accept GET only. The read proxy lists open pull requests only for
  the head `<owner>:horsemen/canvas`, and only in the signed-in view. The public view and the local app do not load
  the edit script. An instance without the three editor secrets has no write
  route and keeps the read-only text on the sign-in page.

## Deploy

Needs Bun and a Cloudflare account with the target domain.

```sh
cd worker
bun install
# Edit wrangler.jsonc: set `name` and the custom domain.
bunx wrangler deploy
# Create the GitHub App, then store its settings and a new session key:
bun scripts/create-github-app.mjs --origin https://your.domain --session-key
```

The setup script opens a local page. Select **Continue to GitHub**, then
**Create GitHub App**. Add `--org your-org` to create the app in an
organization. The script saves `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`,
`GITHUB_APP_SLUG`, and `SESSION_KEY` with `wrangler secret put`. It never
prints them. It discards the app private key, which read-only user access
does not need. Then install the app from the link that the script prints.

For an existing installation, keep the primary app registration, callback, secrets, and session key. Change its Contents permission to read and write. Keep Metadata and Pull requests at read-only. Each installation owner approves the change in GitHub. The default Worker configuration uses `GITHUB_APP_MODE=single`. An installation awaiting approval can still view records. Verify a save on a selected test repository before retiring any previous editor registration. Older self-hosted deployments can retain the separate editor by omitting the single-app setting.

Before the first deploy with editing, check the GitHub calls on a disposable
repository that you own. The name must contain `check` or `disposable`. The
script uses your `gh` sign-in, writes and deletes one canvas file with four
commits marked `[skip ci]`, and prints statuses and SHAs only:

```sh
node scripts/live-edit-check.mjs --repo you/horsemen-edit-check          # reads only, then asks
node scripts/live-edit-check.mjs --repo you/horsemen-edit-check --yes
```

To rotate the session key, which signs everyone out:
`openssl rand -base64 32 | bunx wrangler secret put SESSION_KEY`.

`/healthz` returns 200 when the instance is configured and 503 when it is not.

## Develop and test

```sh
node --test ../tests/test_hosted_reader.cjs test/       # unit tests
node --test test/editor.test.js test/setup.test.js ../tests/test_canvas_edit.cjs   # editing
python3 ../scripts/test_hosted_e2e.py --output /tmp/horsemen-hosted-check
python3 ../scripts/test_hosted_edit_e2e.py --output /tmp/horsemen-edit-check
python3 ../scripts/bench_hosted.py --repos 80 --latency 150 --output /tmp/horsemen-bench
```

The benchmark uses a fake GitHub with a fixed delay for each call. It prints
the time to the first project and to the end of discovery, for a first visit
and a reload. `wrangler dev` uses HTTP/1.1, so the browser sends at most six
requests at a time; production uses HTTP/2, so real parallel reads are faster.

The end-to-end check runs `wrangler dev` against a fake GitHub. It signs in,
opens a fictional project, detects a new commit, and signs out. It also
pushes canvas files to the fake repository: a hand-written board shows with
no reload, a file that is not valid shows a message and the generated
canvas, a later push repairs it, and the public view opens a board from a
link. It needs `agent-browser` and saves screenshots and logs to `--output`.
Run `bun install` in `worker/` first, so that the check uses the local
`wrangler`.

The edit check runs the same way with both apps on the fake GitHub. It opts
in to the editor, moves a section card, adds and connects a note, and saves
one commit. Then a commit from outside arrives while a draft is open (Merge
now), and a save meets a conflict on the same note. It also checks Delete
and N on the keyboard, a phone width, the eight themes, the public view, and
sign-out. It saves screenshots and `edit-flow.webm` to `--output`.

## Limits

- Only default branches are shown. Branch and pull request views are not built.
- A first visit reads every installed repository: two calls for each one.
  A reload makes one branch check for each repository; unchanged branches
  return 304 and do not count against the GitHub rate limit (5,000 requests
  an hour).
- Links to private repositories work only for people with GitHub access.
  Public links to private repositories would need stored share settings.
- Private PR image attachments open on GitHub; the viewer does not load them.
- Editing covers canvas files and their media: move, notes, images, tables,
  links, connectors, and delete. It does not resize or change record text. A
  save adds four media files at most, 1 MiB each; SVG and video are refused. Saves go to the
  default branch; a protected branch refuses the commit (code `busy`).
- A project shows 20 canvas files at most;
  each one is one blob read when the project opens. A canvas loads 100
  images at most, one contents read for each image that comes into view,
  and 20 tables at most, one contents read for each table.
- Players: the content security policy has
  `frame-src https://www.youtube-nocookie.com https://player.vimeo.com https://www.loom.com https://www.figma.com https://docs.google.com`.
  A player frame loads only after a click; before it, the browser contacts
  no provider. The Worker fetches nothing from a provider. `frame-ancestors
  'none'` stays, so no other site can frame Horsemen. `web/canvas-embeds.js`
  has the same list, and a test fails when the two differ.
- Cloudflare's free plan allows 100,000 Worker requests a day. Each GitHub
  read is one request.
