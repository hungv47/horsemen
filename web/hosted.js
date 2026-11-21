'use strict';
/* Hosted mode glue. The Worker injects this script and the "hosted" mode meta.
   It answers the app's /api/* calls in the browser with the reader port, which
   reads GitHub through the Worker's read-only proxy. Nothing is stored. */
(function () {
  const mode = document.querySelector('meta[name="horsemen-mode"]')?.content;
  if (mode !== 'hosted' && mode !== 'public') return;
  /* Public mode: a signed-out view of a public repository. Reads go through /pub with no session. */
  const PUBLIC = mode === 'public', BASE = PUBLIC ? '/pub' : '/gh';
  const R = window.HorsemenReader;
  const token = document.querySelector('meta[name="horsemen-session"]').content;
  const headers = extra => (PUBLIC ? { ...extra } : { 'X-Horsemen-Session': token, ...extra });
  let refreshing = null, pollSeconds = 60, installURL = null;

  const signedOut = () => { location.assign('/'); };
  function refresh() {
    refreshing = refreshing || fetch('/auth/refresh', { method: 'POST', headers: headers(), cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error('signin'); return r.json(); })
      .finally(() => { refreshing = null; });
    return refreshing;
  }
  /* One GitHub read through the proxy. Expired tokens refresh once; ended sessions return to sign-in. */
  async function request(path, etag) {
    for (let attempt = 0; ; attempt++) {
      const res = await fetch(BASE + path, { headers: headers(etag ? { 'If-None-Match': etag } : {}), cache: 'no-store' });
      if (res.status === 304) return { status: 304 };
      let data = null; try { data = await res.json(); } catch { /* handled below */ }
      if (res.status === 401 && !PUBLIC) {
        if (data?.code === 'expired' && attempt === 0) {
          try { await refresh(); continue; } catch { /* fall through to sign-in */ }
        }
        signedOut(); throw new R.ProviderError('Your GitHub session ended. Sign in again.', 401);
      }
      if (!res.ok || data === null) throw new R.ProviderError(data?.error || 'GitHub request failed. Retry.', res.status || 502);
      return { status: res.status, data, etag: res.headers.get('etag') };
    }
  }
  const gh = async path => (await request(path)).data;

  async function repositories() {
    if (PUBLIC) {
      if (!target) throw new R.ProviderError('Open a public repository link, such as /owner/repo.', 404);
      return [await gh(`/repos/${target.repo}`)];
    }
    const repos = new Map(), installations = [];
    for (let page = 1; page < 50; page++) {
      const found = (await gh(`/user/installations?per_page=100&page=${page}`)).installations || [];
      installations.push(...found);
      if (found.length < 100) break;
    }
    // Installations are independent: read their repository lists in parallel.
    await Promise.all(installations.map(async installation => {
      for (let p = 1; p < 100; p++) {
        const list = (await gh(`/user/installations/${installation.id}/repositories?per_page=100&page=${p}`)).repositories || [];
        for (const repo of list) repos.set(repo.id, repo);
        if (list.length < 100) break;
      }
    }));
    if (!repos.size) throw new R.ProviderError('Horsemen cannot see any repositories yet. Select Choose repositories, then install the GitHub App on the projects you want to read.', 404);
    // A shared link's repository goes first, so its project opens as soon as possible.
    return R.prioritize([...repos.values()].sort((a, b) => String(b.pushed_at || '').localeCompare(String(a.pushed_at || ''))), target);
  }

  const login = PUBLIC ? 'Public view' : (document.querySelector('meta[name="horsemen-login"]')?.content || null);
  const target = R.shareTarget(new URL(location.href));
  /* Status with a clear issue when a shared link points to a project this account cannot read. */
  function status() {
    const snap = state.snapshot();
    if (target && ['ready', 'partial', 'error'].includes(snap.phase) && !snap.projects.some(p => R.matchesTarget(p, target))) {
      const where = `${target.repo}${target.root ? ' / ' + target.root : ''}`;
      snap.issues.unshift({ message: PUBLIC
        ? `${where} has no Horsemen records at this path. A project needs at least two of VISION, PROGRESS, BRAIN, and STRUCTURE.`
        : `Horsemen cannot open ${where}. Your GitHub account needs access to it, and the Horsemen app must be installed on it. Select Choose repositories to add it. If the repository is public, add ?view=public to the link.` });
    }
    return snap;
  }
  const reader = new R.Reader(gh, repositories, 30000, login);
  /* Head checks use ETags: an unchanged branch returns 304 and does not use rate limit. */
  const heads = new Map();
  reader.head = async target => {
    const path = `/repos/${target.repo}/commits/${R.quote(target.branch, '')}`, known = heads.get(path);
    const res = await request(path, known?.etag);
    if (res.status === 304 && known) return known.sha;
    if (res.etag) heads.set(path, { etag: res.etag, sha: res.data.sha });
    return res.data.sha;
  };
  const state = new R.ScanState(reader, { concurrency: 12 });

  /* Saved discovery index: repository names, record paths, revisions, and ETags.
     It never holds record text. It lets a reload show projects at once, then checks
     each branch in the background. Sign-out and Clear workspace remove it. */
  const INDEX_KEY = 'horsemen.discovery.v1';
  function saveIndex() {
    if (PUBLIC) return;  // A public view keeps nothing in the browser.
    const index = state.exportIndex();
    if (!index) return;
    index.heads = [...heads].slice(-2000);
    try { localStorage.setItem(INDEX_KEY, JSON.stringify(index)); } catch { /* Storage is optional. */ }
  }
  function forgetIndex() { try { localStorage.removeItem(INDEX_KEY); } catch { /* Storage is optional. */ } }
  let restored = false;
  if (!PUBLIC) try {
    const index = JSON.parse(localStorage.getItem(INDEX_KEY) || 'null');
    restored = state.restore(index, login);
    if (restored && Array.isArray(index.heads)) for (const [path, value] of index.heads) if (value?.etag) heads.set(path, value);
    if (!restored && index) forgetIndex();
  } catch { forgetIndex(); }
  let revalidation = null;
  function revalidate() {
    revalidation = revalidation || state.revalidate().then(() => {
      saveIndex();
      document.dispatchEvent(new CustomEvent('horsemen:projects', { detail: status() }));
    }).finally(() => { revalidation = null; });
    return revalidation;
  }
  // Let the first project load before the background check starts.
  let revalidateTimer = restored ? setTimeout(revalidate, 1500) : null;

  /* Live updates: while a project is open and the tab is visible, check its branch for new commits. */
  let watched = null, timer = null, checking = false;
  async function check() {
    if (checking || !watched || document.visibilityState !== 'visible') return;
    checking = true;
    try {
      const updated = await state.refreshProject(watched);
      if (updated) { saveIndex(); document.dispatchEvent(new CustomEvent('horsemen:updated', { detail: updated })); }
    } catch { /* The next check retries. */ } finally { checking = false; }
  }
  function watch(id) { watched = id; clearInterval(timer); timer = setInterval(check, pollSeconds * 1000); }
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') check(); });

  async function api(path, method = 'GET') {
    const url = new URL(path, location.origin), q = k => url.searchParams.get(k) || '';
    try {
      switch (url.pathname) {
        case '/api/status': return status();
        case '/api/scan': {
          if (method !== 'POST') break;
          watched = null; clearTimeout(revalidateTimer);
          const started = state.start();
          if (started) state.running.then(saveIndex);
          return { started };
        }
        case '/api/clear': if (method !== 'POST') break; watched = null; clearTimeout(revalidateTimer); state.clear(); forgetIndex(); return { cleared: true };
        case '/api/project': { const data = await state.loadProject(q('id')); watch(q('id')); return data; }
        case '/api/document': return await state.loadDocument(q('id'), q('link'));
        case '/api/pr': return await state.pullRequest(q('project'), q('number'));
        /* Image bytes for a registered image link; the app shows them as a blob: URL. */
        case '/api/image': return await state.loadImage(q('id'), q('link'));
        /* The text of a registered CSV or TSV link; the app draws it as a table. */
        case '/api/table': return await state.loadTable(q('id'), q('link'));
      }
    } catch (error) { throw Error(error instanceof R.ProviderError ? error.message : 'Request failed. Retry.'); }
    throw Error('Not found.');
  }

  /* Editing (slice 4a): the opt-in editor app. The viewer token never writes; the Worker keeps the editor token
     in the same cookie and uses it only for /write/*. Drafts stay in this tab (sessionStorage); sign-out removes them. */
  let editorInfo = { available: false, signed_in: false, install_url: null };
  const access = new Map();
  const DRAFTS = 'horsemen.draft.v1:';
  function forgetDrafts() {
    try { for (const key of Object.keys(sessionStorage)) if (key.startsWith(DRAFTS)) sessionStorage.removeItem(key); } catch { /* Storage is optional. */ }
  }
  async function writeJSON(path, init) {
    const res = await fetch(path, { cache: 'no-store', ...init, headers: headers(init?.headers || {}) });
    let data = null; try { data = await res.json(); } catch { /* handled below */ }
    if (res.status === 401) { signedOut(); throw new R.ProviderError('Your GitHub session ended. Sign in again.', 401); }
    return { status: res.status, data: data || { error: 'The request failed. Retry.' } };
  }
  const editor = {
    info: () => ({ ...editorInfo }),
    /* 'signin', 'install', 'no-push', or 'ok' for this repository, asked once for each repository in this tab. */
    async access(repo) {
      if (!editorInfo.available) return 'unavailable';
      if (!editorInfo.signed_in) return 'signin';
      if (!access.has(repo)) access.set(repo, writeJSON('/write/access?repo=' + encodeURIComponent(repo)).then(r => r.status === 200 ? r.data.editor : Promise.reject(new Error(r.data.error))).catch(error => { access.delete(repo); throw error; }));
      const result = await access.get(repo);
      if (result !== 'ok') access.delete(repo);
      return result;
    },
    /* One save: { repo, root, canvas, base, text } and, with new files, media: [{ name, data }] (slice 4b). The Worker builds
       the paths, the branch, and the message. */
    async save(payload) {
      const res = await writeJSON('/write/canvas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (res.data.code === 'editor-signin') { editorInfo.signed_in = false; access.clear(); }
      if (res.data.code === 'editor-install' || res.data.code === 'no-push') access.clear();  // Ask GitHub again next time.
      return res;
    },
    /* Where the next save of a canvas goes (slice 4c): { branch, default_branch, protected, sha, pull_request? }.
       A read with the editor token; the Worker checks the protection of the default branch. */
    async target(repo, root, canvas) {
      const res = await writeJSON('/write/target?' + new URLSearchParams({ repo, root: root || '', canvas }));
      if (res.data.code === 'editor-signin') { editorInfo.signed_in = false; access.clear(); }
      if (res.data.code === 'editor-install' || res.data.code === 'no-push') access.clear();
      return res;
    },
    /* The open pull requests of horsemen/canvas, through the read-only proxy with the viewer token; null when GitHub
       does not answer. */
    async pullRequests(repo) {
      try { return await gh(`/repos/${repo}/pulls?` + new URLSearchParams({ state: 'open', head: repo.split('/')[0] + ':horsemen/canvas', per_page: '1' })); }
      catch { return null; }
    },
    /* The text of a canvas file by its blob SHA, through the read-only proxy with the viewer token. */
    async readBlob(repo, sha) {
      const data = await gh(`/repos/${repo}/git/blobs/${sha}`);
      return R.decodeBlob(data, { encoding: 'Unsupported canvas encoding.', unreadable: 'The canvas file could not be decoded as UTF-8 text.', large: 'The canvas file is larger than 512 KiB.' });
    },
    signIn() { location.assign('/auth/edit/login?next=' + encodeURIComponent(location.pathname + location.search)); },
    async stop() {
      await writeJSON('/auth/edit/logout', { method: 'POST' });
      editorInfo.signed_in = false; access.clear();
      document.dispatchEvent(new CustomEvent('horsemen:editor', { detail: editor.info() }));
    },
    forgetDrafts,
  };

  async function signOut() {
    forgetIndex(); forgetDrafts();
    try { await fetch('/auth/logout', { method: 'POST', headers: headers(), cache: 'no-store' }); } finally { signedOut(); }
  }

  /* Hosted controls in the account menu: choose repositories, copy link, and sign out. */
  function decorate() {
    const github = document.querySelector('#menu [data-menu-group=github]');
    const item = (tag, id, icon, label) => {
      const el = document.createElement(tag); el.id = id; el.setAttribute('role', 'menuitem');
      if (tag === 'button') el.type = 'button';
      el.innerHTML = '<svg class="icon" aria-hidden="true"><use href="/assets/icons/icons.svg#' + icon + '"/></svg><span></span>'; el.querySelector('span').textContent = label;
      return el;
    };
    if (PUBLIC && github && !document.getElementById('public-sign-in')) {
      const signIn = item('a', 'public-sign-in', 'github', 'Sign in with GitHub');
      signIn.href = '/auth/login?next=' + encodeURIComponent(location.pathname + location.search);
      github.append(signIn);
    }
    if (!PUBLIC && github && !document.getElementById('choose-repos')) {
      const choose = item('a', 'choose-repos', 'layers', 'Choose repositories');
      choose.rel = 'noopener'; choose.target = '_blank'; choose.hidden = !installURL; if (installURL) choose.href = installURL;
      github.append(choose);
      /* The project switcher also leads to the page where a person adds a repository. */
      const pop = document.getElementById('workspace-pop');
      if (pop) {
        const connect = document.createElement('a'); connect.id = 'connect-repo'; connect.className = 'workspace-connect'; connect.rel = 'noopener'; connect.target = '_blank';
        connect.innerHTML = '<svg class="icon" aria-hidden="true"><use href="/assets/icons/icons.svg#plus"/></svg><span>Connect a repository</span>';
        connect.hidden = !installURL; if (installURL) connect.href = installURL;
        pop.append(connect);
      }
      const group = document.createElement('div'); group.setAttribute('role', 'group'); group.setAttribute('aria-label', 'Session'); group.id = 'hosted-controls';
      const out = item('button', 'sign-out', 'back', 'Sign out'); out.addEventListener('click', signOut);
      group.append(out);
      document.querySelector('#menu-note')?.before(group);
    }
    /* Copy link: the address bar always holds the readable link for the open project and record. */
    const copyLink = async () => {
      try { await navigator.clipboard.writeText(location.href); window.showToast?.(PUBLIC ? 'Link copied. Anyone can open it while the repository stays public.' : 'Link copied. People who open it need GitHub access to this repository.'); }
      catch { window.showToast?.('Copy failed. Copy the link from the address bar.'); }
    };
    const shareButton = (id, label, cls) => {
      const b = document.createElement('button'); b.type = 'button'; b.id = id; b.className = cls; b.title = PUBLIC ? 'Copy link. Anyone can open it while the repository stays public.' : 'Copy link. People who open it need GitHub access.';
      b.innerHTML = '<svg class="icon" aria-hidden="true"><use href="/assets/icons/icons.svg#link"/></svg><span></span>'; b.querySelector('span').textContent = label;
      b.addEventListener('click', copyLink); return b;
    };
    const actions = document.querySelector('.heading-actions');
    if (actions && !document.getElementById('share-link')) actions.prepend(shareButton('share-link', 'Copy link', 'btn share-link'));
    const close = document.getElementById('close-peek');
    if (close && !document.getElementById('share-record')) { const b = shareButton('share-record', 'Copy link', 'icon-btn share-record'); b.setAttribute('aria-label', 'Copy link'); close.parentElement.prepend(b); }
    const note = document.getElementById('menu-note');
    if (note) note.textContent = PUBLIC ? 'Public view of a public repository. Read-only. Nothing stored. Checks for new commits every minute.' : 'Nothing stored on the server. Saves of canvas edits are commits by you. Open projects check for new commits every minute.';
  }
  if (!PUBLIC) fetch('/api/session', { headers: headers(), cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(info => {
    if (!info) return;
    pollSeconds = Math.max(5, Number(info.poll_seconds) || 60); installURL = info.install_url;
    if (info.editor && info.editor.available) { editorInfo = { available: true, single: !!info.editor.single, signed_in: !!info.editor.signed_in, install_url: String(info.editor.install_url || '') }; document.dispatchEvent(new CustomEvent('horsemen:editor', { detail: editor.info() })); }
    for (const id of ['choose-repos', 'connect-repo']) { const link = document.getElementById(id); if (link) { link.href = installURL; link.hidden = false; } }
    if (watched) watch(watched);
  }).catch(() => {});
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', decorate); else decorate();

  window.HorsemenHosted = { api, signOut, state, check, target, public: PUBLIC, editor: PUBLIC ? null : editor, shareURL: (project, record, canvas, node) => R.shareURL(location.origin, project, record, canvas, node) };
})();
