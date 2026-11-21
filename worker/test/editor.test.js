/* Browser editing (slice 4a): the opt-in editor app and the one write route, /write/canvas.
   Failure modes covered:
   - an instance without editor secrets offers editing, or fails to start
   - editor sign-in: without a viewer session; with the viewer's state cookie (or the reverse); as another GitHub
     account than the viewer session; tokens visible in the cookie; the viewer flow changes
   - token confusion: a read with the editor token; a write with the viewer token; a viewer refresh that drops the
     editor token; sign-out that leaves the editor token alive
   - the write route: no session, a viewer session only, the public view, a wrong method, a missing or foreign
     Origin, a cross-site fetch, a missing or wrong CSRF token, a wrong content type, a body over the limit (with and
     without Content-Length), a body that is not JSON, keys that are not in the contract, each bad repository,
     root, canvas, and base, a canvas that the reader refuses, a newer format version
   - GitHub: the file changed (conflict), a file made or deleted by someone else, a head that moves during the commit
     (retry, three times at most), a replayed request, an unchanged file, missing install or push access, an expired
     editor token (refresh, or sign-in again); GitHub error text never reaches the browser
   - the commit: the Worker builds the path, the branch, and the message; the content is the canonical text */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import worker from '../src/index.js';

const require = createRequire(import.meta.url);
const F = require('../../web/canvas-format.js');
const ORIGIN = 'https://horsemen.example';
const indexHTML = readFileSync(new URL('../../web/index.html', import.meta.url), 'utf8');
const EDITOR = { EDITOR_CLIENT_ID: 'Iv1.editor', EDITOR_CLIENT_SECRET: 'editor-secret', EDITOR_APP_SLUG: 'horsemen-editor-test' };
const env = (extra = {}) => ({
  GITHUB_CLIENT_ID: 'Iv1.fictional', GITHUB_CLIENT_SECRET: 'fictional-secret', GITHUB_APP_SLUG: 'horsemen-test',
  SESSION_KEY: Buffer.alloc(32, 7).toString('base64'), GITHUB_API: 'https://api.github.test', GITHUB_WEB: 'https://github.test',
  ASSETS: { fetch: async req => new Response(['/', '/index.html'].includes(new URL(req.url).pathname) ? indexHTML : 'not found', { status: ['/', '/index.html'].includes(new URL(req.url).pathname) ? 200 : 404 }) },
  ...EDITOR, ...extra,
});
let calls = [];
const mockFetch = handler => { calls = []; globalThis.fetch = async (input, init = {}) => { const req = new Request(input, init); calls.push(req); return handler(req); }; };
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const call = (path, init = {}, e = env()) => worker.fetch(new Request(ORIGIN + path, init), e);
const cookieOf = (res, name = '__Host-horsemen') => res.headers.getSetCookie().map(c => c.split(';')[0]).find(c => c.startsWith(name + '=')) || '';
const csrfOf = async (cookie, e) => (await (await call('/', { headers: { cookie } }, e)).text()).match(/name="horsemen-session" content="([^"]+)"/)[1];

async function signIn(e = env()) {
  mockFetch(async req => req.url.endsWith('/login/oauth/access_token') ? json({ access_token: 'ghu_viewer', refresh_token: 'ghr_viewer', expires_in: 28800, refresh_token_expires_in: 15897600 }) : json({ login: 'operator' }));
  const login = await call('/auth/login', {}, e), state = new URL(login.headers.get('location')).searchParams.get('state');
  const cookie = cookieOf(await call(`/auth/callback?code=c&state=${state}`, { headers: { cookie: cookieOf(login, '__Host-horsemen-state') } }, e));
  return { cookie, csrf: await csrfOf(cookie, e) };
}
async function editorSignIn(e = env(), { login = 'operator', token = { access_token: 'ghu_editor', refresh_token: 'ghr_editor', expires_in: 28800, refresh_token_expires_in: 15897600 } } = {}) {
  const viewer = await signIn(e);
  const start = await call('/auth/edit/login?next=' + encodeURIComponent('/example/alpha?canvas=progress'), { headers: { cookie: viewer.cookie } }, e);
  const state = new URL(start.headers.get('location')).searchParams.get('state');
  mockFetch(async req => req.url.endsWith('/login/oauth/access_token') ? json(token) : json({ login }));
  const back = await call(`/auth/edit/callback?code=c&state=${state}`, { headers: { cookie: viewer.cookie + '; ' + cookieOf(start, '__Host-horsemen-edit-state') } }, e);
  const cookie = cookieOf(back) || viewer.cookie;
  return { start, back, cookie, csrf: viewer.csrf, viewer, headers: { cookie, 'x-horsemen-session': viewer.csrf } };
}

/* ---------------------------------------------------------------- a fake repository for writes */
const sha = text => require('node:crypto').createHash('sha1').update(text).digest('hex');
const PATH = '.horsemen/canvas/progress.canvas';
const canvasText = nodes => F.canonical({ horsemen: { version: 1 }, nodes, edges: [] });
const NOTE = { id: 'note-first', type: 'text', x: 0, y: 0, width: 320, height: 140, text: 'Ask the operators.' };
const ORIGINAL = canvasText([NOTE]);
function fakeRepo({ expectedToken = 'ghu_editor', files = { [PATH]: ORIGINAL }, push = true, putConflicts = 0, putStatus = null, repoStatus = 200, installed = true, onConflict = null } = {}) {
  const repo = { files: { ...files }, puts: [], commits: 0 };
  mockFetch(async req => {
    const u = new URL(req.url), p = decodeURIComponent(u.pathname);
    if (req.headers.get('authorization') !== 'Bearer ' + expectedToken) return json({ message: 'Bad credentials for this test' }, 401);
    if (p === '/repos/example/alpha') return repoStatus === 200 ? json({ full_name: 'example/alpha', default_branch: 'trunk', private: true, permissions: { pull: true, push } }) : json({ message: 'private detail' }, repoStatus);
    if (p === '/user/installations') return json({ installations: installed ? [{ id: 9 }] : [] });
    if (p === '/user/installations/9/repositories') return json({ repositories: [{ id: 1, full_name: 'example/alpha', permissions: { pull: true, push } }, { id: 2, full_name: 'example/other', permissions: { pull: true, push: false } }] });
    const m = p.match(/^\/repos\/example\/alpha\/contents\/(.+)$/);
    if (m && req.method === 'GET') {
      assert.equal(u.searchParams.get('ref'), 'trunk', 'reads the default branch');
      const text = repo.files[m[1]];
      return text === undefined ? json({ message: 'Not Found' }, 404) : json({ type: 'file', sha: sha(text), size: text.length, encoding: 'base64', content: Buffer.from(text).toString('base64') });
    }
    if (m && req.method === 'PUT') {
      const body = await req.json(); repo.puts.push({ path: m[1], body });
      if (putStatus) return json({ message: 'provider detail: secret path' }, putStatus);
      if (putConflicts > 0) { putConflicts--; onConflict?.(repo); return json({ message: 'is at x but expected y' }, 409); }
      const current = repo.files[m[1]];
      if ((current === undefined) !== (body.sha === undefined) || (current !== undefined && sha(current) !== body.sha)) return json({ message: 'does not match' }, current === undefined ? 404 : 409);
      repo.files[m[1]] = Buffer.from(body.content, 'base64').toString('utf8'); repo.commits++;
      return json({ content: { sha: sha(repo.files[m[1]]) }, commit: { sha: String(repo.commits).padStart(40, 'c'), html_url: 'https://github.test/example/alpha/commit/' + String(repo.commits).padStart(40, 'c') } }, current === undefined ? 201 : 200);
    }
    return json({ message: 'Not Found' }, 404);
  });
  return repo;
}
const body = (extra = {}) => JSON.stringify({ repo: 'example/alpha', root: '', canvas: 'progress', base: sha(ORIGINAL), text: canvasText([{ ...NOTE, x: 40 }]), ...extra });
const post = (s, payload = body(), headers = {}, e = env()) => call('/write/canvas', { method: 'POST', body: payload, headers: { ...s.headers, origin: ORIGIN, 'sec-fetch-site': 'same-origin', 'content-type': 'application/json', 'content-length': String(Buffer.byteLength(payload)), ...headers } }, e);

/* ---------------------------------------------------------------- configuration and sign-in */
test('without editor secrets the instance is a viewer: no editor sign-in, no write route', async () => {
  const e = env({ EDITOR_CLIENT_ID: '', EDITOR_CLIENT_SECRET: '', EDITOR_APP_SLUG: '' });
  assert.equal((await call('/healthz', {}, e)).status, 200);
  const s = await signIn(e), headers = { cookie: s.cookie, 'x-horsemen-session': s.csrf };
  assert.deepEqual((await (await call('/api/session', { headers }, e)).json()).editor, { available: false });
  assert.equal((await call('/auth/edit/login', { headers: { cookie: s.cookie } }, e)).status, 404);
  mockFetch(async () => json({}));
  const res = await post({ headers }, body(), {}, e);
  assert.equal(res.status, 404); assert.equal(calls.length, 0);
});

test('editor sign-in needs a viewer session, uses the editor app, and keeps its own state cookie', async () => {
  const out = await call('/auth/edit/login?next=%2Fexample%2Falpha');
  assert.equal(out.status, 302); assert.equal(out.headers.get('location'), '/auth/login?next=%2Fexample%2Falpha', 'signed out: sign in to the viewer first');
  const { start, back, cookie, viewer } = await editorSignIn();
  const to = new URL(start.headers.get('location'));
  assert.equal(to.origin + to.pathname, 'https://github.test/login/oauth/authorize');
  assert.equal(to.searchParams.get('client_id'), 'Iv1.editor');
  assert.equal(to.searchParams.get('redirect_uri'), ORIGIN + '/auth/edit/callback');
  assert.match(start.headers.get('set-cookie'), /^__Host-horsemen-edit-state=.*HttpOnly.*Secure.*SameSite=Lax.*Max-Age=600/);
  const exchange = new URLSearchParams(await calls.find(r => r.url.endsWith('/login/oauth/access_token')).text());
  assert.equal(exchange.get('client_id'), 'Iv1.editor'); assert.equal(exchange.get('client_secret'), 'editor-secret');
  assert.equal(back.status, 302); assert.equal(back.headers.get('location'), '/example/alpha?canvas=progress');
  assert.notEqual(cookie, viewer.cookie); assert.doesNotMatch(cookie, /ghu_|ghr_|operator/);
  const info = await (await call('/api/session', { headers: { cookie, 'x-horsemen-session': viewer.csrf } })).json();
  assert.deepEqual(info.editor, { available: true, signed_in: true, install_url: 'https://github.test/apps/horsemen-editor-test/installations/new' });
  assert.equal(info.install_url, 'https://github.test/apps/horsemen-test/installations/new', 'the viewer install page does not change');
});

test('the viewer and editor state cookies cannot finish each other\'s sign-in', async () => {
  const viewer = await signIn();
  const editStart = await call('/auth/edit/login', { headers: { cookie: viewer.cookie } });
  const editState = new URL(editStart.headers.get('location')).searchParams.get('state');
  const viewStart = await call('/auth/login');
  const viewState = new URL(viewStart.headers.get('location')).searchParams.get('state');
  mockFetch(async req => req.url.endsWith('/access_token') ? json({ access_token: 'ghu_editor' }) : json({ login: 'operator' }));
  const crossed = await call(`/auth/edit/callback?code=c&state=${viewState}`, { headers: { cookie: viewer.cookie + '; __Host-horsemen-edit-state=' + cookieOf(viewStart, '__Host-horsemen-state').split('=')[1] } });
  assert.equal(crossed.status, 400);
  const crossed2 = await call(`/auth/callback?code=c&state=${editState}`, { headers: { cookie: '__Host-horsemen-state=' + cookieOf(editStart, '__Host-horsemen-edit-state').split('=')[1] } });
  assert.equal(crossed2.status, 400);
  assert.equal(calls.length, 0, 'no code exchange');
});

test('editor sign-in as another GitHub account is refused and keeps the session read-only', async () => {
  const { back, viewer } = await editorSignIn(env(), { login: 'someone-else' });
  assert.equal(back.status, 400); assert.match(await back.text(), /same GitHub account/);
  assert.equal(cookieOf(back), '', 'the session cookie does not change');
  const info = await (await call('/api/session', { headers: { cookie: viewer.cookie, 'x-horsemen-session': viewer.csrf } })).json();
  assert.equal(info.editor.signed_in, false);
  assert.ok(calls.some(r => r.method === 'DELETE' && r.url.endsWith('/applications/Iv1.editor/token')), 'the unused editor token is revoked');
});

test('reads use the viewer token and writes use the editor token, never the other way', async () => {
  const s = await editorSignIn();
  mockFetch(async () => json({ ok: true }));
  await call('/gh/user', { headers: s.headers });
  assert.equal(calls.at(-1).headers.get('authorization'), 'Bearer ghu_viewer');
  const repo = fakeRepo();
  const res = await post(s);
  assert.equal(res.status, 200, await res.clone().text());
  assert.ok(calls.length >= 3 && calls.every(r => r.headers.get('authorization') === 'Bearer ghu_editor'), 'every write call has the editor token');
  assert.equal(repo.commits, 1);
});

test('a viewer refresh keeps the editor token; sign-out revokes both tokens; Stop editing revokes one', async () => {
  const s = await editorSignIn();
  mockFetch(async req => req.url.endsWith('/access_token') ? json({ access_token: 'ghu_viewer2', refresh_token: 'ghr_viewer2', expires_in: 28800 }) : json({}));
  const refreshed = await call('/auth/refresh', { method: 'POST', headers: s.headers });
  const cookie = cookieOf(refreshed), headers = { cookie, 'x-horsemen-session': s.csrf };
  assert.equal((await (await call('/api/session', { headers })).json()).editor.signed_in, true);
  mockFetch(async () => new Response(null, { status: 204 }));
  const stop = await call('/auth/edit/logout', { method: 'POST', headers });
  assert.equal(stop.status, 200);
  assert.deepEqual(calls.map(r => [r.method, r.url, r.headers.get('authorization')]), [['DELETE', 'https://api.github.test/applications/Iv1.editor/token', 'Basic ' + Buffer.from('Iv1.editor:editor-secret').toString('base64')]]);
  assert.equal(JSON.parse(await calls[0].text()).access_token, 'ghu_editor');
  const after = { cookie: cookieOf(stop), 'x-horsemen-session': s.csrf };
  assert.equal((await (await call('/api/session', { headers: after })).json()).editor.signed_in, false, 'the viewer session stays');
  const again = await editorSignIn();
  mockFetch(async () => new Response(null, { status: 204 }));
  await call('/auth/logout', { method: 'POST', headers: again.headers });
  assert.deepEqual(calls.map(r => r.url.replace('https://api.github.test', '')).sort(), ['/applications/Iv1.editor/token', '/applications/Iv1.fictional/token']);
  assert.equal((await call('/auth/edit/logout', { method: 'GET', headers: s.headers })).status, 405);
  assert.equal((await call('/auth/edit/logout', { method: 'POST', headers: { cookie: s.cookie } })).status, 403, 'Stop editing needs the CSRF token');
});

/* ---------------------------------------------------------------- the gate of the write route */
test('a write needs a session with the editor token: no session, public view, and viewer token only are refused', async () => {
  mockFetch(async () => json({}));
  const payload = body(), plain = { origin: ORIGIN, 'sec-fetch-site': 'same-origin', 'content-type': 'application/json', 'content-length': String(payload.length) };
  const none = await call('/write/canvas', { method: 'POST', body: payload, headers: plain });
  assert.equal(none.status, 401); assert.equal((await none.json()).code, 'signin');
  const viewer = await signIn(); mockFetch(async () => json({}));
  const only = await post({ headers: { cookie: viewer.cookie, 'x-horsemen-session': viewer.csrf } });
  assert.equal(only.status, 403); assert.equal((await only.json()).code, 'editor-signin');
  assert.equal(calls.length, 0, 'the viewer token is never used for a write');
  const publicPage = await call('/pub/repos/example/alpha/contents/' + PATH, { method: 'PUT', body: payload, headers: plain });
  assert.equal(publicPage.status, 405, 'the public proxy never writes');
  assert.equal((await call('/gh/repos/example/alpha/contents/' + PATH, { method: 'PUT', body: payload, headers: { ...plain, cookie: viewer.cookie, 'x-horsemen-session': viewer.csrf } })).status, 405, 'the read proxy never writes');
  assert.equal(calls.length, 0);
});

test('a write must be a same-origin POST with the CSRF token and a JSON body', async () => {
  const s = await editorSignIn(); mockFetch(async () => json({}));
  const cases = [
    [{ origin: undefined }, 403, 'no Origin'], [{ origin: 'https://evil.example' }, 403, 'foreign Origin'], [{ origin: 'null' }, 403, 'opaque Origin'],
    [{ 'sec-fetch-site': 'cross-site' }, 403, 'cross-site'], [{ 'sec-fetch-site': 'same-site' }, 403, 'same-site'],
    [{ 'x-horsemen-session': undefined }, 403, 'no CSRF token'], [{ 'x-horsemen-session': s.csrf.replace(/^./, c => c === 'a' ? 'b' : 'a') }, 403, 'wrong CSRF token'],
    [{ 'content-type': 'text/plain' }, 415, 'text/plain'], [{ 'content-type': 'application/x-www-form-urlencoded' }, 415, 'form'], [{ 'content-type': undefined }, 415, 'no type'],
    [{ 'content-type': 'application/json-patch+json' }, 415, 'another JSON type'],
  ];
  for (const [change, status, label] of cases) {
    const headers = { ...s.headers, origin: ORIGIN, 'sec-fetch-site': 'same-origin', 'content-type': 'application/json', ...change };
    for (const [k, v] of Object.entries(headers)) if (v === undefined) delete headers[k];
    const res = await call('/write/canvas', { method: 'POST', body: body(), headers }); assert.equal(res.status, status, label);
  }
  assert.equal((await call('/write/canvas', { method: 'GET', headers: { ...s.headers, origin: ORIGIN } })).status, 405);
  assert.equal((await post(s, body(), { 'content-type': 'application/json; charset=utf-8' })).status !== 415, true, 'a charset is allowed');
  assert.equal(calls.filter(r => r.method === 'PUT').length <= 1, true);
});

test('the body has a size limit, with and without Content-Length', async () => {
  const s = await editorSignIn(); mockFetch(async () => json({}));
  const big = body({ text: 'x'.repeat(6 * 1024 * 1024) });  // 6 MiB: a canvas and four media files of 1 MiB (slice 4b).
  assert.equal((await post(s, big)).status, 413, 'declared length');
  assert.equal((await post(s, body(), { 'content-length': String(6 * 1024 * 1024 + 1) })).status, 413, 'a declared length over the limit is refused before the body is read');
  const headers = { ...s.headers, origin: ORIGIN, 'sec-fetch-site': 'same-origin', 'content-type': 'application/json' };
  assert.equal((await call('/write/canvas', { method: 'POST', body: big, headers })).status, 413, 'no declared length: the Worker stops reading at the limit');
  assert.equal((await post(s, body({ text: 'x'.repeat(600 * 1024) }))).status, 422, 'a canvas over 512 KiB in a body under the limit');
  assert.equal(calls.length, 0, 'nothing reaches GitHub');
});

test('the body must name a repository, a root, a canvas, and a base with fixed patterns; the Worker builds the path', async () => {
  const s = await editorSignIn(); mockFetch(async () => json({}));
  const bad = [
    ['not JSON', '{"repo":'], ['a list', '[]'], ['an extra key', body({ path: '.github/workflows/x.yml' })], ['a branch', body({ branch: 'main' })],
    ['a message', body({ message: 'evil' })], ['media', body({ media: [] })], ['no text', JSON.stringify({ repo: 'example/alpha', root: '', canvas: 'progress', base: null })],
    ...['example', 'example/alpha/x', '../alpha', 'example/..', 'example/.', '-ex/alpha', 'ex ample/alpha', 'example/al%2Fpha', 'example/alpha\n', '', 7, null].map(repo => ['repo ' + JSON.stringify(repo), body({ repo })]),
    ...['/apps/web', 'apps/web/', '../web', 'apps/../web', 'apps//web', 'apps\\web', '.hidden', 'apps/.git', 'apps/web\u0000', 'a'.repeat(201), 7, null].map(root => ['root ' + JSON.stringify(root), body({ root })]),
    ...['Progress', '../progress', 'a/b', '', 'home', '-x', 'x'.repeat(65), 'progress.canvas', 'pro gress', 7, null].map(canvas => ['canvas ' + JSON.stringify(canvas), body({ canvas })]),
    ...['xyz', 'a'.repeat(39), 'A'.repeat(40), 'a'.repeat(41), 7, ''].map(base => ['base ' + JSON.stringify(base), body({ base })]),
  ];
  for (const [label, payload] of bad) {
    const res = await post(s, payload);
    assert.equal(res.status, 400, label); assert.ok((await res.json()).error, label);
  }
  assert.equal(calls.length, 0, 'nothing reaches GitHub');
  const repo = fakeRepo({ files: { ['apps/web/' + PATH]: ORIGINAL } });
  assert.equal((await post(s, body({ root: 'apps/web' }))).status, 200);
  assert.deepEqual(repo.puts.map(p => p.path), ['apps/web/.horsemen/canvas/progress.canvas']);
});

test('a canvas that the reader refuses is not saved, and its fault is named', async () => {
  const s = await editorSignIn(); mockFetch(async () => json({}));
  const cases = [
    ['not JSON', '{"nodes":[', 'file is not valid JSON'],
    ['conflict markers', '<<<<<<< ours\n{}\n=======\n{}\n>>>>>>> theirs\n', 'file has Git conflict markers'],
    ['script address', canvasText([{ id: 'evil', type: 'link', x: 0, y: 0, width: 200, height: 100, url: 'javascript:alert(1)' }]), 'node evil: url must be an http or https address of 2,048 characters or less'],
    ['CSS in a colour', canvasText([{ ...NOTE, color: 'red;background:url(x)' }]), 'node note-first: color must be "1" to "6" or #RRGGBB'],
    ['a path outside the project', canvasText([{ id: 'up', type: 'file', x: 0, y: 0, width: 200, height: 100, file: '../secrets.md' }]), 'node up: file must be a path inside the project (no leading "/", no "." or ".." part, no backslash)'],
    ['an edge to no node', F.canonical({ horsemen: { version: 1 }, nodes: [NOTE], edges: [{ id: 'e', fromNode: 'note-first', toNode: 'gone' }] }), 'edge e: toNode gone is not a node'],
    ['a duplicate ID', F.canonical({ nodes: [NOTE, NOTE], edges: [] }), 'duplicate id note-first'],
    ['too many nodes', JSON.stringify({ nodes: Array.from({ length: 501 }, (_, i) => ({ ...NOTE, id: 'n' + i })) }), 'more than 500 nodes'],
    ['a newer version', F.canonical({ horsemen: { version: 2 }, nodes: [NOTE], edges: [] }), 'the file uses format version 2; this site saves version 1 only'],
  ];
  for (const [label, text, error] of cases) {
    const res = await post(s, body({ text }));
    assert.equal(res.status, 422, label);
    const data = await res.json(); assert.equal(data.code, 'invalid', label); assert.equal(data.error, 'The canvas is not valid: ' + error + '.', label);
  }
  assert.equal(calls.length, 0);
});

/* ---------------------------------------------------------------- the commit */
test('a save is one commit on the default branch, with the canonical text and a message the Worker writes', async () => {
  const s = await editorSignIn(), repo = fakeRepo();
  const handWritten = JSON.stringify({ nodes: [{ ...NOTE, x: 40 }, { id: 'note-2', type: 'text', x: 0, y: 400, width: 320, height: 140, text: 'Second' }], edges: [] }, null, 2);
  const res = await post(s, body({ text: handWritten }));
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.deepEqual(Object.keys(data).sort(), ['canvas_sha', 'commit', 'message', 'url']);
  assert.equal(data.message, 'canvas(progress): add 1, move 1 [skip ci]');
  const put = repo.puts[0];
  assert.deepEqual(Object.keys(put.body).sort(), ['branch', 'content', 'message', 'sha']);
  assert.equal(put.body.branch, 'trunk'); assert.equal(put.body.sha, sha(ORIGINAL)); assert.equal(put.body.message, data.message);
  const written = Buffer.from(put.body.content, 'base64').toString('utf8');
  assert.equal(written, F.canonical(JSON.parse(handWritten)), 'the Worker writes the canonical text'); assert.ok(F.isCanonical(written));
  assert.equal(data.canvas_sha, sha(written)); assert.match(data.commit, /^[0-9a-f]{40}$/); assert.equal(data.url, 'https://github.test/example/alpha/commit/' + data.commit);
  assert.equal(calls.filter(r => r.method === 'PUT').length, 1);
  assert.equal(res.headers.get('access-control-allow-origin'), null, 'no CORS headers');
});

test('a new file is made with no base; a file that someone else made or deleted is a conflict', async () => {
  const s = await editorSignIn();
  let repo = fakeRepo({ files: {} });
  const made = await post(s, body({ canvas: 'launch-plan', base: null }));
  assert.equal(made.status, 200); assert.equal(repo.puts[0].path, '.horsemen/canvas/launch-plan.canvas'); assert.equal(repo.puts[0].body.sha, undefined);
  assert.equal((await made.json()).message, 'canvas(launch-plan): add 1 [skip ci]');
  repo = fakeRepo();
  const exists = await post(s, body({ base: null }));
  assert.equal(exists.status, 409); assert.deepEqual(await exists.json(), { error: 'The canvas changed on GitHub. Merge, then save again.', code: 'conflict', current: sha(ORIGINAL) });
  repo = fakeRepo({ files: {} });
  const gone = await post(s, body());
  assert.equal(gone.status, 409); assert.equal((await gone.json()).current, null);
  assert.equal(repo.puts.length, 0);
});

test('a base that is not the current file is a conflict; a replayed request is a conflict too', async () => {
  const s = await editorSignIn(), repo = fakeRepo();
  const stale = await post(s, body({ base: 'b'.repeat(40) }));
  assert.equal(stale.status, 409); assert.equal((await stale.json()).current, sha(ORIGINAL)); assert.equal(repo.puts.length, 0);
  const payload = body();
  assert.equal((await post(s, payload)).status, 200);
  const replay = await post(s, payload);
  assert.equal(replay.status, 409, 'the same request again finds a new file'); assert.equal(repo.commits, 1);
});

test('a head that moves during the commit is tried again, three times at most; a file that changed is a conflict', async () => {
  const s = await editorSignIn();
  let repo = fakeRepo({ putConflicts: 1 });
  assert.equal((await post(s)).status, 200); assert.equal(repo.puts.length, 2); assert.equal(repo.commits, 1);
  repo = fakeRepo({ putConflicts: 5 });
  const busy = await post(s);
  assert.notEqual((await busy.json()).code, 'busy', 'slice 4c: after three refusals the save goes to horsemen/canvas (worker/test/protected.test.js)');
  assert.equal(repo.puts.length, 3);
  repo = fakeRepo({ putConflicts: 1, onConflict: r => { r.files[PATH] = canvasText([{ ...NOTE, text: 'Changed on GitHub.' }]); } });
  const changed = await post(s);
  assert.equal(changed.status, 409); assert.equal((await changed.json()).code, 'conflict'); assert.equal(repo.puts.length, 1);
});

test('an unchanged canvas makes no commit', async () => {
  const s = await editorSignIn(), repo = fakeRepo();
  const res = await post(s, body({ text: ORIGINAL }));
  assert.equal(res.status, 200); assert.deepEqual(await res.json(), { unchanged: true, canvas_sha: sha(ORIGINAL) }); assert.equal(repo.puts.length, 0);
});

test('missing access maps to plain messages without GitHub text', async () => {
  const s = await editorSignIn();
  for (const [options, status, code] of [[{ push: false }, 403, 'no-push'], [{ repoStatus: 404 }, 403, 'editor-install'], [{ putStatus: 404 }, 403, 'editor-install'], [{ putStatus: 422 }, 502, 'github'], [{ putStatus: 500 }, 502, 'github'], [{ repoStatus: 500 }, 502, 'github']]) {
    fakeRepo(options);
    const res = await post(s), data = await res.json();
    assert.equal(res.status, status, JSON.stringify(options)); assert.equal(data.code, code, JSON.stringify(options));
    assert.doesNotMatch(JSON.stringify(data), /provider detail|private detail|secret path/);
  }
  mockFetch(async () => { throw new TypeError('down'); });
  assert.equal((await post(s)).status, 502);
});

test('an expired editor token refreshes with the editor app; a failed refresh asks for editor sign-in again', async () => {
  const s = await editorSignIn(env(), { token: { access_token: 'ghu_old', refresh_token: 'ghr_editor_old', expires_in: -10, refresh_token_expires_in: 1000 } });
  const repo = fakeRepo(), handler = globalThis.fetch;
  mockFetch(async req => req.url.endsWith('/login/oauth/access_token') ? json({ access_token: 'ghu_editor', refresh_token: 'ghr_editor_new', expires_in: 28800, refresh_token_expires_in: 1000 }) : handler(req));
  const res = await post(s);
  assert.equal(res.status, 200);
  const exchange = new URLSearchParams(await calls[0].text());
  assert.deepEqual([exchange.get('client_id'), exchange.get('grant_type'), exchange.get('refresh_token')], ['Iv1.editor', 'refresh_token', 'ghr_editor_old']);
  assert.ok(cookieOf(res), 'the new token goes into the cookie'); assert.equal(repo.commits, 1);
  mockFetch(async () => json({ error: 'bad_refresh_token' }));
  const failed = await post(s);
  assert.equal(failed.status, 403); assert.equal((await failed.json()).code, 'editor-signin');
  const cookie = cookieOf(failed); assert.ok(cookie, 'the editor token leaves the cookie');
  const info = await (await call('/api/session', { headers: { cookie, 'x-horsemen-session': s.csrf } })).json();
  assert.equal(info.editor.signed_in, false); assert.equal(info.login, 'operator', 'the viewer session stays');
});

test('the access check says whether this person can save to a repository', async () => {
  const viewer = await signIn(); mockFetch(async () => json({}));
  const ask = (s, repo = 'example/alpha') => call('/write/access?repo=' + encodeURIComponent(repo), { headers: { ...s.headers, origin: ORIGIN } });
  assert.equal((await (await ask({ headers: { cookie: viewer.cookie, 'x-horsemen-session': viewer.csrf } })).json()).editor, 'signin');
  assert.equal(calls.length, 0);
  const s = await editorSignIn();
  fakeRepo(); assert.deepEqual(await (await ask(s)).json(), { editor: 'ok' });
  fakeRepo(); assert.deepEqual(await (await ask(s, 'example/other')).json(), { editor: 'no-push' });
  fakeRepo(); assert.deepEqual(await (await ask(s, 'example/missing')).json(), { editor: 'install', install_url: 'https://github.test/apps/horsemen-editor-test/installations/new' });
  fakeRepo({ installed: false }); assert.equal((await (await ask(s)).json()).editor, 'install');
  assert.equal((await ask(s, '../x')).status, 400);
  assert.equal((await call('/write/access?repo=example/alpha', { headers: { cookie: s.cookie } })).status, 403, 'needs the CSRF token');
});

test('the signed-in app loads the edit rules; the public view does not', async () => {
  const s = await signIn();
  const html = await (await call('/', { headers: { cookie: s.cookie } })).text();
  assert.ok(html.indexOf('/canvas-edit.js') > 0 && html.indexOf('/canvas-edit.js') < html.indexOf('/app.js'));
  assert.ok(html.indexOf('/canvas-editor.js') > html.indexOf('/app.js'), 'edit mode runs after the app'); assert.match(html, /href="\/canvas-editor.css"/);
  mockFetch(async req => new URL(req.url).pathname === '/repos/example/open' ? json({ private: false }) : json({}, 404));
  const pub = await (await call('/example/open', {}, env({ CACHE: null }))).text();
  assert.match(pub, /content="public"/); assert.doesNotMatch(pub, /canvas-edit|canvas-editor/);
});

test('the sign-in page no longer says that Horsemen never writes, and says what the editor does', async () => {
  const html = await (await call('/')).text();
  assert.doesNotMatch(html, /never writes to your repositories/);
  assert.match(html, /<b>Read-only by default\.<\/b>/);
  assert.match(html, /editor app/i);
  const viewerOnly = await (await call('/', {}, env({ EDITOR_CLIENT_ID: '', EDITOR_CLIENT_SECRET: '', EDITOR_APP_SLUG: '' }))).text();
  assert.match(viewerOnly, /<b>Read-only\.<\/b> This site never writes to your repositories\./, 'an instance without the editor keeps the read-only promise');
});

test('single installation handles a save after one login and ignores legacy editor credentials', async () => {
  const e = env({ GITHUB_APP_MODE: 'single' });
  const s = await signIn(e);
  const headers = { cookie: s.cookie, 'x-horsemen-session': s.csrf };
  const info = await (await call('/api/session', { headers }, e)).json();
  assert.equal(info.editor.install_url, info.install_url);
  assert.equal(info.editor.signed_in, true);
  const repo = fakeRepo({ expectedToken: 'ghu_viewer' });
  assert.equal((await post({ headers }, body(), {}, e)).status, 200);
  assert.equal(repo.commits, 1);
});


test('single app requests an installation upgrade when the repository is still read-only', async () => {
  const e = env({ GITHUB_APP_MODE: 'single', EDITOR_CLIENT_ID: '', EDITOR_CLIENT_SECRET: '', EDITOR_APP_SLUG: '' });
  const s = await signIn(e);
  const headers = { cookie: s.cookie, 'x-horsemen-session': s.csrf };
  mockFetch(async req => req.url.includes('/repositories?')
    ? json({ repositories: [{ full_name: 'example/alpha', permissions: { push: true } }] })
    : json({ installations: [{ id: 9, permissions: { contents: 'read' } }] }));
  assert.equal((await (await call('/write/access?repo=example/alpha', { headers }, e)).json()).editor, 'upgrade');
});
