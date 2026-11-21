"""End-to-end check of canvas editing in the hosted viewer, against a disposable fake GitHub.

Runs the real Worker with `wrangler dev` and one GitHub App on a fake GitHub.
A person signs in, moves a section card, adds a note, connects
the two, and saves one commit. Then a commit from outside arrives while a draft is open (Merge now),
and a save meets a conflict on the same note (the person takes the GitHub version). Slice 4b: the person
drops an image, pastes a video address and a CSV table, confirms the public-repository warning, and saves
one GraphQL commit with the canvas and both files. Then the default
branch becomes protected (slice 4c): Edit says that saves go to horsemen/canvas, the save makes that
branch, and the bar links the compare page, then the open pull request. It also checks the keyboard,
phone width, the themes, the public view, and that editing uses the original sign-in. Saves screenshots, a recording, and logs to --output (outside the repository).

    python3 scripts/test_hosted_edit_e2e.py --output /tmp/horsemen-edit-check
"""
import argparse
import base64
import hashlib
import struct
import zlib
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--port', type=int, default=8789)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))

# A fictional project. PROGRESS has two sections; the canvas file comes from edits in the browser.
SOURCES = {
    'VISION.md': '# Vision\n## Why we exist\nHelp small teams keep decisions close to their work.\n',
    'PROGRESS.md': '# Progress\nNext action: Invite three operators to the pilot.\n## Shipped\n- Search is available to the pilot group.\n## Up next\n- Invite three operators.\n',
    'BRAIN.md': '# Brain\n## Providers\n- Research notebook.\n',
}
CANVAS = '.horsemen/canvas/progress.canvas'
SIDE = 'horsemen/canvas'
world = {'rev': 'a' * 40, 'files': dict(SOURCES), 'commits': [], 'authorize': [], 'tokens': [], 'put_tokens': set(), 'revoked': [],
         # Slice 4c: classic protection of main, the branch horsemen/canvas ({files, base, own, sha} or None),
         # the open pull requests of that branch, the ref writes, and the tokens that read the pull requests.
         'protected': False, 'side': None, 'pulls': [], 'ref_writes': [], 'pull_tokens': set(),
         'graphql': []}
lock = threading.Lock()
def raw(value): return value if isinstance(value, bytes) else value.encode()
def sha(value): return hashlib.sha1(raw(value)).hexdigest()
def png(width, height, rgb):
    """A small real PNG (the editor decodes it to size the card)."""
    chunk = lambda kind, data: struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')
def bump():
    world['rev'] = hashlib.sha1((world['rev'] + str(time.time())).encode()).hexdigest()


class FakeGitHub(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def send(self, status, body=None, headers=None):
        raw = json.dumps(body).encode() if body is not None else b''
        self.send_response(status)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        if body is not None: self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def do_GET(self):
        url = urlsplit(self.path); q = parse_qs(url.query); p = url.path
        if p == '/login/oauth/authorize':
            world['authorize'].append(q['client_id'][0])
            return self.send(302, None, {'Location': q['redirect_uri'][0] + '?code=' + q['client_id'][0] + '&state=' + q['state'][0]})
        auth = self.headers.get('Authorization', '')
        if auth == '':  # The public view: example/open is a public copy of the same files.
            if p == '/repos/example/open': return self.send(200, {'id': 9, 'full_name': 'example/open', 'default_branch': 'main', 'private': False, 'archived': False})
            if not p.startswith('/repos/example/open/'): return self.send(404, {'message': 'Not Found'})
            p = p.replace('/repos/example/open/', '/repos/example/alpha/', 1)
        elif auth != 'Bearer ghu_viewer': return self.send(401, {'message': 'Bad credentials'})
        editor = auth == 'Bearer ghu_viewer'
        if p == '/user': return self.send(200, {'login': 'operator'})
        if p == '/user/installations': return self.send(200, {'installations': [{'id': 1, 'permissions': {'contents': 'write'}}]})
        if p in ('/user/installations/1/repositories', '/user/installations/2/repositories'):
            return self.send(200, {'repositories': [{'id': 1, 'full_name': 'example/alpha', 'default_branch': 'main', 'private': True, 'archived': False, 'pushed_at': '2026-11-19T00:00:00Z', 'permissions': {'pull': True, 'push': True}}]})
        if p == '/repos/example/alpha' and editor: return self.send(200, {'full_name': 'example/alpha', 'default_branch': 'main', 'private': True, 'permissions': {'pull': True, 'push': True}})
        with lock:
            files = dict(world['files'])
            side = dict(world['side']) if world['side'] else None
        if p == '/repos/example/alpha/branches/main': return self.send(200, {'name': 'main', 'protected': world['protected']})
        if p == '/repos/example/alpha/rules/branches/main': return self.send(200, [])
        if p == '/repos/example/alpha/git/ref/heads/main': return self.send(200, {'ref': 'refs/heads/main', 'object': {'type': 'commit', 'sha': world['rev']}})
        if p == '/repos/example/alpha/git/ref/heads/' + SIDE:
            return self.send(200, {'ref': 'refs/heads/' + SIDE, 'object': {'type': 'commit', 'sha': side['sha']}}) if side else self.send(404, {'message': 'Not Found'})
        if p == '/repos/example/alpha/compare/main...' + SIDE:
            if not side: return self.send(404, {'message': 'Not Found'})
            return self.send(200, {'ahead_by': side['own'], 'behind_by': 0 if side['base'] == world['rev'] else 1})
        if p == '/repos/example/alpha/pulls':
            world['pull_tokens'].add(auth)
            return self.send(200, world['pulls'] if q.get('head') == ['example:' + SIDE] and q.get('state') == ['open'] else [])
        if p == '/repos/example/alpha/commits/main':
            etag = f'"{world["rev"]}"'
            if self.headers.get('If-None-Match') == etag: return self.send(304, None, {'ETag': etag})
            return self.send(200, {'sha': world['rev'], 'commit': {'tree': {'sha': world['rev']}}}, {'ETag': etag})
        if p.startswith('/repos/example/alpha/git/trees/'):
            return self.send(200, {'truncated': False, 'tree': [{'path': k, 'type': 'blob', 'mode': '100644', 'sha': sha(v), 'size': len(raw(v))} for k, v in files.items()]})
        if p.startswith('/repos/example/alpha/git/blobs/'):
            for v in [*files.values(), *(side['files'].values() if side else [])]:
                if sha(v) == p.rsplit('/', 1)[1]: return self.send(200, {'encoding': 'base64', 'content': base64.b64encode(raw(v)).decode()})
        if p.startswith('/repos/example/alpha/contents/'):
            v = (side['files'] if side and q.get('ref') == [SIDE] else files).get(p.split('/contents/', 1)[1])
            if v is None: return self.send(404, {'message': 'Not Found'})
            return self.send(200, {'type': 'file', 'sha': sha(v), 'size': len(raw(v)), 'encoding': 'base64', 'content': base64.b64encode(raw(v)).decode()})
        return self.send(404, {'message': 'Not Found'})

    def do_PUT(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
        p = urlsplit(self.path).path
        world['put_tokens'].add(self.headers.get('Authorization', ''))
        if self.headers.get('Authorization') != 'Bearer ghu_viewer': return self.send(403, {'message': 'Resource not accessible by integration'})
        if not p.startswith('/repos/example/alpha/contents/'): return self.send(404, {'message': 'Not Found'})
        path = p.split('/contents/', 1)[1]
        with lock:
            if body.get('branch') == SIDE:
                side = world['side']
                if not side: return self.send(404, {'message': 'Branch not found'})
                current = side['files'].get(path)
                if (current is None) != ('sha' not in body) or (current is not None and sha(current) != body.get('sha')):
                    return self.send(409, {'message': 'does not match'})
                text = base64.b64decode(body['content']).decode()
                side['files'][path] = text; side['own'] += 1; side['sha'] = hashlib.sha1((side['sha'] + text).encode()).hexdigest()
                world['commits'].append({'path': path, 'message': body['message'], 'branch': SIDE, 'text': text})
                return self.send(200, {'content': {'sha': sha(text)}, 'commit': {'sha': side['sha']}})
            if world['protected']: return self.send(409, {'message': 'Protected branch update failed'})
            current = world['files'].get(path)
            if (current is None) != ('sha' not in body) or (current is not None and sha(current) != body.get('sha')):
                return self.send(409 if current is not None else 422, {'message': 'does not match'})
            text = base64.b64decode(body['content']).decode()
            world['files'][path] = text; bump()
            world['commits'].append({'path': path, 'message': body['message'], 'branch': body['branch'], 'text': text})
            return self.send(200, {'content': {'sha': sha(text)}, 'commit': {'sha': world['rev']}})

    def graphql(self, body):
        """createCommitOnBranch: the one commit of a save with media on main (slice 4b)."""
        world['graphql'].append(body['query'].split('(')[0])
        world['put_tokens'].add(self.headers.get('Authorization', ''))
        if self.headers.get('Authorization') != 'Bearer ghu_viewer': return self.send(401, {'message': 'Bad credentials'})
        v = body['variables']
        if not body['query'].startswith('mutation'): return self.send(200, {'data': None, 'errors': [{'type': 'UNEXPECTED', 'message': 'only the mutation'}]})
        with lock:
            change = v['input']
            if change['branch'] != {'repositoryNameWithOwner': 'example/alpha', 'branchName': 'main'}: return self.send(200, {'data': None, 'errors': [{'type': 'NOT_FOUND', 'message': 'no branch'}]})
            if world['protected']: return self.send(200, {'data': {'createCommitOnBranch': None}, 'errors': [{'type': 'FORBIDDEN', 'message': 'Protected branch update failed'}]})
            if change['expectedHeadOid'] != world['rev']: return self.send(200, {'data': {'createCommitOnBranch': None}, 'errors': [{'type': 'STALE_DATA', 'message': 'Expected branch to point to another commit'}]})
            paths = [a['path'] for a in change['fileChanges']['additions']]
            for a in change['fileChanges']['additions']:
                data = base64.b64decode(a['contents'])
                world['files'][a['path']] = data.decode() if a['path'].endswith('.canvas') else data
            bump()
            world['commits'].append({'path': paths[0], 'paths': paths, 'message': change['message']['headline'], 'branch': 'main', 'text': world['files'][v['path']], 'graphql': True})
            return self.send(200, {'data': {'createCommitOnBranch': {'commit': {'oid': world['rev'], 'file': {'oid': sha(world['files'][v['path']])}}}}})

    def do_PATCH(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
        if self.headers.get('Authorization') != 'Bearer ghu_viewer': return self.send(403, {'message': 'Resource not accessible by integration'})
        with lock:
            world['ref_writes'].append(('PATCH', urlsplit(self.path).path, body))
            if urlsplit(self.path).path != '/repos/example/alpha/git/refs/heads/' + SIDE or not world['side'] or body.get('force') is not False: return self.send(422, {'message': 'Not allowed here'})
            if world['side']['own'] or body.get('sha') != world['rev']: return self.send(422, {'message': 'Update is not a fast forward'})
            world['side'].update({'files': dict(world['files']), 'base': world['rev'], 'sha': world['rev']})
            return self.send(200, {'object': {'sha': world['rev']}})

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length') or 0)).decode()
        if self.path == '/graphql': return self.graphql(json.loads(data))
        if self.path == '/repos/example/alpha/git/refs':
            body = json.loads(data or '{}')
            if self.headers.get('Authorization') != 'Bearer ghu_viewer': return self.send(403, {'message': 'Resource not accessible by integration'})
            with lock:
                world['ref_writes'].append(('POST', self.path, body))
                if body.get('ref') != 'refs/heads/' + SIDE or world['side'] or body.get('sha') != world['rev']: return self.send(422, {'message': 'Reference already exists'})
                world['side'] = {'files': dict(world['files']), 'base': world['rev'], 'own': 0, 'sha': world['rev']}
                return self.send(201, {'ref': body['ref'], 'object': {'sha': world['rev']}})
        form = parse_qs(data)
        if self.path == '/login/oauth/access_token':
            client = form.get('client_id', [''])[0]; world['tokens'].append(client)
            token = 'ghu_editor' if client == 'Iv1.editor' else 'ghu_viewer'
            return self.send(200, {'access_token': token, 'refresh_token': 'ghr_' + token, 'expires_in': 28800, 'refresh_token_expires_in': 15897600})
        return self.send(404, {'message': 'Not Found'})

    def do_DELETE(self):
        self.rfile.read(int(self.headers.get('Content-Length') or 0))
        if self.path.startswith('/applications/'): world['revoked'].append(self.path.split('/')[2]); return self.send(204)
        return self.send(404, {'message': 'Not Found'})


def commit_from_outside(text):
    """A commit that another person or an agent pushes: the canvas file changes and the branch moves."""
    with lock:
        world['files'][CANVAS] = text; bump()


fake = ThreadingHTTPServer(('127.0.0.1', 0), FakeGitHub)
threading.Thread(target=fake.serve_forever, daemon=True).start()
github = f'http://127.0.0.1:{fake.server_port}'
origin = f'http://localhost:{args.port}'
log = []
variables = {'GITHUB_API': github, 'GITHUB_WEB': github, 'GITHUB_CLIENT_ID': 'Iv1.fictional', 'GITHUB_CLIENT_SECRET': 'fictional',
             'GITHUB_APP_SLUG': 'horsemen-fictional', 'GITHUB_APP_MODE': 'single',
             'SESSION_KEY': base64.b64encode(secrets.token_bytes(32)).decode(), 'POLL_SECONDS': '5'}
local_wrangler = root / 'worker/node_modules/.bin/wrangler'
command = [str(local_wrangler) if local_wrangler.exists() else 'bunx', *([] if local_wrangler.exists() else ['wrangler']), 'dev', '--port', str(args.port), '--ip', '127.0.0.1', '--local', '--local-upstream', f'localhost:{args.port}', '--show-interactive-dev-session=false', '--persist-to', str(args.output / 'wrangler-state')]
for k, v in variables.items(): command += ['--var', f'{k}:{v}']
dev = subprocess.Popen(command, cwd=root / 'worker', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
SESSION = f'horsemen-edit-test-{os.getpid()}'  # One browser session for each run: runs in other checkouts do not share it.


def browser(*parts):
    p = subprocess.run(['agent-browser', '--session', SESSION, *parts], capture_output=True, text=True, timeout=60)
    log.append(f'$ agent-browser {" ".join(parts)[:160]}\n{p.stdout}{p.stderr}')
    if p.returncode: raise AssertionError(p.stderr or p.stdout)
    return p.stdout


def value(code):
    result = json.loads(browser('eval', code))
    return json.loads(result) if isinstance(result, str) else result


def until(code, seconds=30):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            if value('!!(' + code + ')'): return
        except (AssertionError, ValueError): pass
        time.sleep(0.4)
    try: where = browser('eval', 'JSON.stringify([location.href, document.querySelector("#edit-status")?.textContent, [...document.querySelectorAll("dialog[open]")].map(d => d.id + ": " + d.innerText.slice(0, 200)), document.querySelector("#toast").textContent, document.body.innerText.slice(0, 200), [...document.querySelectorAll(".canvas-node")].map(n => n.dataset.kind + ":" + (n.querySelector("[data-state]")?.dataset.state || "") + ":" + n.innerText.slice(0, 60))])')
    except (AssertionError, ValueError): where = '(page not readable)'
    raise AssertionError('Timed out waiting for: ' + code + ' at ' + str(where))


def shot(name): browser('screenshot', str(args.output / name))
def center(selector):
    """A point near the top of the element that the element itself gets (the edit bar can cover the top edge)."""
    return value(f"JSON.stringify((c => {{ const r = c.getBoundingClientRect(), x = Math.round(r.x + r.width / 2); for (let y = Math.round(r.y + 24); y < r.bottom - 4; y += 8) if (c.contains(document.elementFromPoint(x, y))) return [x, y]; return [x, Math.round(r.y + 24)]; }})(document.querySelector('{selector}')))")
def drag(selector, dx, dy):
    """A real pointer drag: the app moves elements on pointer events, not on HTML drag and drop."""
    x, y = center(selector)
    browser('mouse', 'move', str(x), str(y)); browser('mouse', 'down')
    for i in range(1, 6): browser('mouse', 'move', str(x + dx * i // 5), str(y + dy * i // 5))
    browser('mouse', 'up')
def answer(choice):  # Select the button of the open edit dialog with this value.
    until(f"document.querySelector('#edit-dialog').open && !!document.querySelector('#edit-dialog button[value=\"{choice}\"]')", 10)
    browser('click', f'#edit-dialog button[value="{choice}"]')
    until("!document.querySelector('#edit-dialog').open", 10)
def drop(names, blobs, kind='image/png'):
    """Drop files on the middle of the canvas, as a drag from the desktop does."""
    data = json.dumps([base64.b64encode(raw(b)).decode() for b in blobs])
    browser('eval', f"""(() => {{ const dt = new DataTransfer(); {json.dumps(names)}.forEach((name, i) => dt.items.add(new File([Uint8Array.from(atob({data}[i]), c => c.charCodeAt(0))], name, {{ type: {json.dumps(kind)} }})));
      const c = document.querySelector('.canvas'), r = c.getBoundingClientRect(), at = {{ bubbles: true, cancelable: true, dataTransfer: dt, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2 }};
      c.dispatchEvent(new DragEvent('dragover', at)); c.dispatchEvent(new DragEvent('drop', at)); return true; }})()""")
def paste(text):
    """Paste text on the canvas, as Ctrl+V does."""
    browser('eval', f"(() => {{ const dt = new DataTransfer(); dt.setData('text/plain', {json.dumps(text)}); document.querySelector('.canvas').dispatchEvent(new ClipboardEvent('paste', {{ clipboardData: dt, bubbles: true, cancelable: true }})); return true; }})()")
def note_text():
    return value("JSON.stringify([...document.querySelectorAll('.canvas-node[data-kind=note]')].map(n => n.innerText.trim()))")
def saved(): return json.loads(world['files'][CANVAS])
def wait_commits(n, seconds=20):
    deadline = time.time() + seconds
    while len(world['commits']) < n and time.time() < deadline: time.sleep(0.2)
    assert len(world['commits']) == n, [c['message'] for c in world['commits']]
    until("document.querySelector('#edit-status').textContent === 'No changes'", 10)


try:
    for _ in range(120):
        try:
            with urllib.request.urlopen(origin + '/healthz', timeout=2) as r:
                if r.status == 200: break
        except Exception: time.sleep(0.5)
    else: raise AssertionError('wrangler dev did not start')

    # Sign-in page: the promise is true with the editor app present.
    browser('open', origin)
    assert value("document.body.innerText.includes('One GitHub sign-in.') && !document.body.innerText.includes('never writes')"), 'the sign-in page states the new promise'
    shot('01-sign-in.png')
    browser('eval', 'document.querySelector("a.btn").scrollIntoView({block:"center"})'); browser('click', 'a.btn')
    until("document.querySelector('meta[name=horsemen-mode]')?.content === 'hosted' && document.body.dataset.state === 'ready'")
    assert world['authorize'] == ['Iv1.fictional'], 'one GitHub authorization'
    browser('eval', 'window.__errors=[];window.__csp=[];addEventListener("error",e=>__errors.push(String(e.message)));document.addEventListener("securitypolicyviolation",e=>__csp.push(e.violatedDirective+" "+e.blockedURI))')
    browser('click', '[data-canvas="progress"]')
    until("canvasKey === 'progress' && document.querySelectorAll('.section-card').length === 2 && !document.querySelector('#edit-canvas').hidden")
    shot('02-before-edit.png')
    browser('record', 'start', str(args.output / 'edit-flow.webm'))

    browser('click', '#edit-canvas')
    assert world['authorize'] == ['Iv1.fictional']
    until("!document.querySelector('#edit-bar').hidden && document.querySelector('#edit-status').textContent === 'No changes'")

    # Move a section card, add a note, connect them, and save one commit.
    before = value("JSON.stringify(position('s-up-next'))")
    drag('[data-node="s-up-next"]', 200, 120)
    until("document.querySelector('#edit-status').textContent.startsWith('Draft:')")
    after = value("JSON.stringify(position('s-up-next'))")
    assert after != before and abs(after[0] - before[0] - 200) < 40, (before, after)
    browser('click', '#edit-add')
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog textarea')")
    browser('fill', '#edit-dialog textarea', 'Ask each operator for one sentence.')
    answer('save')
    until("JSON.stringify([...document.querySelectorAll('.canvas-node[data-kind=note]')].map(n => n.innerText.trim())) === JSON.stringify(['Ask each operator for one sentence.'])", 10)
    note_id = value("JSON.stringify([...selected][0])")
    browser('eval', f"setSelection(new Set(['{note_id}', 's-up-next']))")
    until("document.querySelector('#edit-connect').textContent === 'Connect' && !document.querySelector('#edit-connect').disabled")
    browser('click', '#edit-connect')
    until("document.querySelectorAll('.wires .edge').length === 1")
    shot('04-draft.png')
    browser('press', 'Control+s')
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog').innerText.includes('Save to GitHub')")
    preview = value("JSON.stringify(document.querySelector('#edit-dialog').innerText)")
    assert 'canvas(progress): add 2, connect 1 [skip ci]' in preview and '.horsemen/canvas/progress.canvas' in preview, preview
    shot('05-save-preview.png')
    answer('commit')
    wait_commits(1)
    assert len(world['commits']) == 1, world['commits']
    first = world['commits'][0]
    assert first['message'] == 'canvas(progress): add 2, connect 1 [skip ci]' and first['branch'] == 'main' and first['path'] == CANVAS
    assert world['put_tokens'] == {'Bearer ghu_viewer'}, 'the signed-in user token writes'
    doc = saved()
    assert sorted(n['id'] for n in doc['nodes']) == sorted([note_id, 's-up-next']) and doc['edges'][0]['fromNode'] == note_id
    assert {'file': 'PROGRESS.md', 'subpath': '#Up next'}.items() <= next(n for n in doc['nodes'] if n['id'] == 's-up-next').items()
    until("document.querySelector('#edit-status').textContent === 'No changes'", 10)
    # The next check of the branch loads the new commit; the canvas keeps the saved elements.
    until("document.querySelector('#project-description').textContent.includes(" + json.dumps(world['rev'][:7]) + ")", 20)
    shot('06-after-save.png')

    # A commit from outside while a draft is open: Merge now keeps both.
    drag(f'[data-node="{note_id}"]', 0, 160)
    until("document.querySelector('#edit-status').textContent.startsWith('Draft: move 1')")
    outside = json.loads(world['files'][CANVAS])
    outside['nodes'].append({'id': 'note-outside', 'type': 'text', 'x': 900, 'y': 0, 'width': 320, 'height': 140, 'text': 'Added by an agent.'})
    from_outside = '{\n"horsemen":{"version":1},\n"nodes":[\n' + ',\n'.join(json.dumps(n, separators=(',', ':')) for n in sorted(outside['nodes'], key=lambda n: n['id'])) + '\n],\n"edges":[\n' + json.dumps(outside['edges'][0], separators=(',', ':')) + '\n]\n}\n'
    commit_from_outside(from_outside)
    until("!document.querySelector('#edit-merge').hidden && document.querySelector('#edit-status').textContent === 'The canvas changed on GitHub.'", 20)
    shot('07-changed-on-github.png')
    browser('click', '#edit-merge')
    until("!!document.querySelector('[data-node=note-outside]') && document.querySelector('#edit-status').textContent === 'Draft: move 1'")
    browser('click', '#edit-save'); answer('commit')
    wait_commits(2)
    assert len(world['commits']) == 2 and world['commits'][1]['message'] == 'canvas(progress): move 1 [skip ci]'
    assert {n['id'] for n in saved()['nodes']} == {note_id, 's-up-next', 'note-outside'}, 'the outside note and my move are both in the file'

    # A conflict at save: the same note changed here and on GitHub. The person takes the GitHub version.
    browser('eval', f"setSelection(new Set(['{note_id}']));document.querySelector('[data-node=\"{note_id}\"]').focus()")
    browser('press', 'Enter')
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog textarea')")
    browser('fill', '#edit-dialog textarea', 'Mine: ask by email.')
    answer('save')
    drag('[data-node="s-up-next"]', -120, 0)
    until("document.querySelector('#edit-status').textContent === 'Draft: move 1, edit 1'")
    conflict = saved()
    for n in conflict['nodes']:
        if n['id'] == note_id: n['text'] = 'Theirs: ask in the weekly call.'
        if n['id'] == 'note-outside': n['x'] = 1200
    commit_from_outside(json.dumps(conflict))  # Not canonical: written by another tool.
    until("document.querySelector('#edit-status').textContent === 'The canvas changed on GitHub.'", 20)
    browser('press', 'Control+s'); answer('commit')
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog').innerText.includes('changed on both sides')", 20)
    shot('08-conflict-choice.png')
    browser('click', '#edit-dialog input[value="theirs"]'); answer('merge')
    wait_commits(3)
    assert world['commits'][2]['message'] == 'canvas(progress): move 1 [skip ci]', 'after the merge, only my move is new'
    final = saved()
    assert next(n for n in final['nodes'] if n['id'] == note_id)['text'] == 'Theirs: ask in the weekly call.'
    assert next(n for n in final['nodes'] if n['id'] == 'note-outside')['x'] == 1200, 'their other change is kept'
    assert world['commits'][-1]['text'] == world['files'][CANVAS] and len(world['commits']) == 3

    # Delete with the keyboard: the note and its connector go.
    browser('eval', f"setSelection(new Set(['{note_id}']));document.querySelector('[data-node=\"{note_id}\"]').focus()")
    browser('press', 'Delete')
    until(f"!document.querySelector('[data-node=\"{note_id}\"]') && document.querySelectorAll('.wires .edge').length === 0")
    browser('press', 'Control+s'); answer('commit')
    wait_commits(4)
    assert world['commits'][-1]['message'] == 'canvas(progress): remove 2 [skip ci]' and saved()['edges'] == [], [c['message'] for c in world['commits']]

    # Slice 4b: drop an image, paste a video address, paste a CSV table, then save one commit with all files.
    image, table = png(48, 32, (200, 90, 40)), 'stop,minutes\nHarbour gate,4\nOld mill,12\n'
    browser('eval', 'projects[current].private = false')  # The warning reads the project; the fake repository stays private.
    drop(['Harbour route.png'], [image])
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog').innerText.includes('Add a file to a public repository?')", 10)
    shot('12-public-warning.png')
    answer('add')
    until("document.querySelectorAll('.canvas-node[data-kind=image] img[src^=\"blob:\"]').length === 1", 10)
    paste('https://www.youtube.com/watch?v=EXAMPLE0000')
    until("document.querySelectorAll('.canvas-node[data-kind=embed] .embed-load').length === 1", 10)
    paste(table)
    until("(t => t && t.innerText.includes('Harbour gate'))(document.querySelector('.canvas-node[data-kind=table] .sheet-stage[data-state=shown]'))", 10)
    until("document.querySelector('#edit-status').textContent === 'Draft: add 3'", 10)
    assert not value("!!document.querySelector('iframe')"), 'no player loads before a click'
    shot('13-media-draft.png')
    rest = len(world['commits'])
    browser('press', 'Control+s')
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog').innerText.includes('New files')", 10)
    preview = value("JSON.stringify(document.querySelector('#edit-dialog').innerText)")
    assert 'canvas(progress): add 3 [skip ci]' in preview and '.horsemen/media/harbour-route-' in preview and '.horsemen/media/pasted-table-' in preview and 'This repository is public.' in preview, preview
    shot('14-media-save-preview.png')
    graphql_before = len(world['graphql'])
    answer('commit')
    wait_commits(rest + 1)
    last = world['commits'][-1]
    assert last.get('graphql') and last['message'] == 'canvas(progress): add 3 [skip ci]' and len(last['paths']) == 3, last
    assert last['paths'][0] == CANVAS and all(p.startswith('.horsemen/media/') for p in last['paths'][1:]), last['paths']
    media = {p: world['files'][p] for p in last['paths'][1:]}
    assert sorted(media.values(), key=len) == sorted([image, table.encode()], key=len), 'the bytes as dropped and pasted'
    assert world['graphql'][graphql_before:] == ['mutation'], 'one GraphQL commit'
    kinds = sorted((n['type'], n.get('file', n.get('url', ''))) for n in saved()['nodes'] if n['type'] == 'link' or n.get('file', '').startswith('.horsemen/media/'))
    assert kinds == sorted([('file', p) for p in media] + [('link', 'https://www.youtube.com/watch?v=EXAMPLE0000')]), kinds
    # The next check loads the commit; the image and the table still show (images load when they come into view).
    until("document.querySelector('#project-description').textContent.includes(" + json.dumps(world['rev'][:7]) + ")", 20)
    browser('eval', "(id => (setSelection(new Set([id])), revealNode(id)))(document.querySelector('.canvas-node[data-kind=image]').dataset.node)")
    until("document.querySelectorAll('.canvas-node[data-kind=image] img').length === 1 && document.querySelectorAll('.canvas-node[data-kind=table] .sheet-stage[data-state=shown]').length === 1", 20)
    # Four files at most in one save; the fifth gets a message.
    drop([f'shot {i}.png' for i in range(5)], [png(8 + i, 8, (40 * i, 120, 60)) for i in range(5)])
    until("document.querySelectorAll('.canvas-node[data-kind=image]').length === 5 && document.querySelector('#toast').textContent.includes('4 files at most')", 10)
    drop(['walkthrough.mp4'], [b'\x00\x00\x00\x18ftypmp42fictional'], 'video/mp4')
    until("document.querySelector('#toast').textContent.includes('Videos are not stored')", 10)
    browser('click', '#edit-discard'); answer('discard')
    until("document.querySelector('#edit-status').textContent === 'No changes' && document.querySelectorAll('.canvas-node[data-kind=image]').length === 1", 10)
    assert world['put_tokens'] == {'Bearer ghu_viewer'}, 'the signed-in user token writes'
    browser('eval', 'projects[current].private = true')
    browser('record', 'stop')
    assert value("JSON.stringify([window.__errors, window.__csp])") == [[], []], 'no script errors and nothing broke the CSP'

    # Keyboard only: N adds a note; Escape closes the dialog without a change.
    browser('focus', '.canvas'); browser('press', 'n')
    until("document.querySelector('#edit-dialog').open")
    browser('press', 'Escape')
    until("!document.querySelector('#edit-dialog').open && document.querySelector('#edit-status').textContent === 'Draft: add 1'")
    # Each theme draws the edit bar; a draft survives a reload of the tab.
    for style in ['engraved', 'modern', 'editorial', 'terminal', 'swiss', 'blueprint', 'soft', 'contrast']:
        browser('eval', f"applyTheme({{style:'{style}'}})")
        assert value("(b => b.width > 200 && getComputedStyle(document.querySelector('#edit-bar')).backgroundColor !== 'rgba(0, 0, 0, 0)')(document.querySelector('#edit-bar').getBoundingClientRect())"), style
        if style in ('terminal', 'contrast'): shot(f'09-theme-{style}.png')
    browser('eval', "applyTheme({style:'engraved'})")
    assert value("(e => (dispatchEvent(e), e.defaultPrevented))(new Event('beforeunload', {cancelable: true}))"), 'the page warns before it closes with an unsaved draft'
    browser('click', '#edit-done'); answer('keep')  # Leave edit mode; the draft stays in this tab.
    until("document.querySelector('#edit-bar').hidden && Object.keys(sessionStorage).some(k => k.startsWith('horsemen.draft.v1:example/alpha::progress'))")
    browser('eval', 'location.reload()')
    until("typeof canvasKey !== 'undefined' && document.body.dataset.state === 'ready' && canvasKey === 'progress' && !document.querySelector('#edit-canvas').hidden", 20)
    until("document.querySelector('#scan-status').textContent.includes('Checked') && document.querySelector('#project-description').textContent.includes(" + json.dumps(world['rev'][:7]) + ") && document.body.dataset.state === 'ready'", 20)
    browser('eval', 'window.__errors=[];window.__csp=[];addEventListener("error",e=>__errors.push(String(e.message)));document.addEventListener("securitypolicyviolation",e=>__csp.push(e.violatedDirective+" "+e.blockedURI))')
    browser('click', '#edit-canvas')
    until("document.querySelector('#edit-status').textContent === 'Draft: add 1'", 10)
    # Phone width: the bar wraps and nothing scrolls sideways.
    desktop = [str(n) for n in value('JSON.stringify([innerWidth, innerHeight])')]
    browser('set', 'viewport', '390', '844')
    until("(r => r.right <= innerWidth && r.left >= 0)(document.querySelector('#edit-bar').getBoundingClientRect()) && document.documentElement.scrollWidth <= innerWidth", 10)
    shot('10-phone.png')
    browser('set', 'viewport', *desktop)
    browser('click', '#edit-discard'); answer('discard')
    until("document.querySelector('#edit-status').textContent === 'No changes'")
    browser('click', '#edit-done')
    until("document.querySelector('#edit-bar').hidden && document.querySelector('#edit-canvas').getAttribute('aria-pressed') === 'false'")

    # Slice 4c: the default branch is protected. Edit says where the save goes; the save makes horsemen/canvas from the
    # head of main and commits there; main does not change; the bar links the compare page, then the open pull request.
    with lock: world['protected'] = True
    main_before, rev_before, made = world['files'][CANVAS], world['rev'], len(world['commits'])
    browser('click', '#edit-canvas')
    until("!document.querySelector('#edit-bar').hidden && !document.querySelector('#edit-target').hidden && document.querySelector('#edit-target').textContent === 'Saves to horsemen/canvas'")
    assert value("document.querySelector('#edit-pr').hidden"), 'no pull request link before the first save'
    drag('[data-node="s-up-next"]', 0, 140)
    until("document.querySelector('#edit-status').textContent === 'Draft: move 1'")
    browser('press', 'Control+s')
    until("document.querySelector('#edit-dialog').open && document.querySelector('#edit-dialog').innerText.includes('Save to horsemen/canvas')")
    preview = value("JSON.stringify(document.querySelector('#edit-dialog').innerText)")
    assert 'main is protected' in preview and 'horsemen/canvas, as you' in preview and 'canvas(progress): move 1' in preview and '[skip ci]' not in preview, preview
    shot('12-protected-preview.png')
    answer('commit')
    wait_commits(made + 1)
    side_commit = world['commits'][-1]
    assert side_commit['branch'] == SIDE and side_commit['message'] == 'canvas(progress): move 1', side_commit
    assert world['files'][CANVAS] == main_before and world['rev'] == rev_before, 'main does not change'
    assert [(m, w['ref']) for m, _, w in world['ref_writes']] == [('POST', 'refs/heads/' + SIDE)], world['ref_writes']
    until("!document.querySelector('#edit-pr').hidden && document.querySelector('#edit-pr').textContent === 'Open a pull request'", 10)
    assert value("JSON.stringify(document.querySelector('#edit-pr').href)") == github + '/example/alpha/compare/main...horsemen/canvas?expand=1'
    shot('13-protected-saved.png')
    # The person opens the pull request on GitHub. The next save continues the branch; the bar links that pull request.
    with lock: world['pulls'] = [{'number': 7, 'html_url': 'https://elsewhere.example/not-used'}]
    drag('[data-node="note-outside"]', 0, 120)
    until("document.querySelector('#edit-status').textContent === 'Draft: move 1'")
    browser('press', 'Control+s'); answer('commit')
    wait_commits(made + 2)
    assert world['commits'][-1]['branch'] == SIDE and world['side']['own'] == 2 and len(world['ref_writes']) == 1, 'the second save continues the branch'
    assert world['files'][CANVAS] == main_before
    until("document.querySelector('#edit-pr').textContent === 'Pull request #7'", 10)
    assert value("JSON.stringify(document.querySelector('#edit-pr').href)") == github + '/example/alpha/pull/7', 'the address is built from the number'
    assert world['pull_tokens'] == {'Bearer ghu_viewer'}, 'the pull request list is read with the viewer token'
    for style in ['engraved', 'modern', 'editorial', 'terminal', 'swiss', 'blueprint', 'soft', 'contrast']:
        browser('eval', f"applyTheme({{style:'{style}'}})")
        assert value("[...document.querySelectorAll('#edit-target, #edit-pr')].every(e => e.getBoundingClientRect().width > 40 && getComputedStyle(e).color !== getComputedStyle(document.querySelector('#edit-bar')).backgroundColor)"), style
        if style == 'blueprint': shot('14-protected-theme-blueprint.png')
    browser('eval', "applyTheme({style:'engraved'})")
    browser('set', 'viewport', '390', '844')
    until("(r => r.right <= innerWidth && r.left >= 0)(document.querySelector('#edit-bar').getBoundingClientRect()) && document.documentElement.scrollWidth <= innerWidth && document.querySelector('#edit-pr').getBoundingClientRect().right <= innerWidth", 10)
    shot('15-protected-phone.png')
    browser('set', 'viewport', *desktop)
    # Keyboard: Tab reaches the link in the bar.
    browser('eval', "document.querySelector('#edit-done').focus()")
    for _ in range(6):
        if value("document.activeElement?.id === 'edit-pr'"): break
        browser('press', 'Shift+Tab')
    assert value("document.activeElement?.id === 'edit-pr'"), 'the pull request link is reachable with the keyboard'
    browser('click', '#edit-done')
    until("document.querySelector('#edit-bar').hidden && document.querySelector('#toast').textContent.includes('until the pull request merges')", 10)
    # Known and not from this slice: the paper texture of the editorial theme is a data: image, which the hosted CSP blocks.
    errors, csp = value("JSON.stringify([window.__errors, window.__csp])")
    assert errors == [] and csp == [], (errors, csp)

    # Sign-out revokes both tokens and removes drafts; editing uses the original sign-in.
    browser('click', '#menu-toggle'); browser('click', '#sign-out')
    until("document.body.innerText.includes('Sign in with GitHub')")
    assert sorted(world['revoked']) == ['Iv1.fictional'], world['revoked']
    authorize = len(world['authorize'])
    browser('eval', 'document.querySelector("a.btn").scrollIntoView({block:"center"})'); browser('click', 'a.btn')
    until("document.body.dataset.state === 'ready'")
    assert world['authorize'][authorize:] == ['Iv1.fictional']
    browser('open', origin + '/example/alpha?canvas=progress')
    until("typeof canvasKey !== 'undefined' && canvasKey === 'progress' && !document.querySelector('#edit-canvas').hidden", 20)
    browser('click', '#edit-canvas')
    until("!document.querySelector('#edit-bar').hidden")
    browser('click', '#edit-done')
    assert value("Object.keys(sessionStorage).filter(k => k.startsWith('horsemen.draft')).length") == 0
    # The public view has no edit control and no edit script.
    browser('click', '#menu-toggle'); browser('click', '#sign-out')
    until("document.body.innerText.includes('Sign in with GitHub')")
    browser('open', origin + '/example/open?canvas=progress')
    until("document.querySelector('meta[name=horsemen-mode]')?.content === 'public' && typeof canvasKey !== 'undefined' && canvasKey === 'progress' && document.body.dataset.state === 'ready'", 20)
    assert value("!document.querySelector('#edit-canvas') && !window.HorsemenEditor && !document.querySelector('script[src=\"/canvas-editor.js\"]')"), 'the public view stays read-only'
    assert value("JSON.stringify([...document.querySelectorAll('.canvas-node')].map(n => n.dataset.node).sort())") == sorted(['s-shipped'] + [n['id'] for n in saved()['nodes']]), 'the public view shows the saved canvas file'
    browser('eval', "(id => (setSelection(new Set([id])), revealNode(id)))(document.querySelector('.canvas-node[data-kind=image]').dataset.node)")
    until("document.querySelectorAll('.canvas-node[data-kind=image] img').length === 1 && document.querySelectorAll('.canvas-node[data-kind=table] .sheet-stage[data-state=shown]').length === 1", 20)
    shot('11-public-view.png')
    print('Hosted edit E2E passed:', args.output)
    print('Commits:', json.dumps([c['message'] for c in world['commits']]))
finally:
    try: browser('record', 'stop')
    except Exception: pass
    try: browser('close')
    except Exception: pass
    try: os.killpg(dev.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: out, _ = dev.communicate(timeout=10)
    except subprocess.TimeoutExpired: os.killpg(dev.pid, signal.SIGKILL); out, _ = dev.communicate()
    fake.shutdown()
    (args.output / 'browser.log').write_text('\n'.join(log))
    (args.output / 'wrangler.log').write_text(out.replace(variables['SESSION_KEY'], '<session key>'))
