"""Single local record operations under an explicit exclusive-writer contract."""
import json
import os
import secrets
import stat
from pathlib import Path

from . import legacy
from .plans import digest, read_original
from .patches import unique_object

NAMES = {'brain': 'BRAIN.md', 'vision': 'VISION.md',
         'structure': 'STRUCTURE.md', 'status': 'PROGRESS.md'}


def document_name(root, command):
    name = NAMES[command]
    if command == 'status':
        current = read_original(root, name)
        old = read_original(root, 'STATUS.md')
        if current is not None and old is not None and not legacy.is_pointer(old):
            raise ValueError('Both PROGRESS.md and STATUS.md contain records. Reconcile them before a single-record operation.')
        if current is None and old is not None:
            name = 'STATUS.md'
    return name


def report(root, name, source):
    # Check only the target. In particular, do not read or validate other records.
    result = legacy.check(root, only=name, selected_text=source)
    if source is None and not any(item['code'] == 'missing-record' for item in result['errors']):
        result['errors'].append({'file': name, 'code': 'missing-record', 'message': f'{name} is missing.'})
    return result


def prepare(root, name, changes):
    if not changes:
        raise ValueError('Update needs --changes FILE with one exact edit and its source_sha256; no content was generated or saved.')
    fd = os.open(Path(changes), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('Edit input must be a regular, non-symlink JSON file.')
        with os.fdopen(fd, encoding='utf-8') as handle:
            fd = None
            edit = json.load(handle, object_pairs_hook=unique_object)
    finally:
        if fd is not None:
            os.close(fd)
    required = {'file', 'source_sha256', 'before', 'after', 'evidence'}
    if not isinstance(edit, dict) or not required.issubset(edit) or set(edit) - required - {'owner_agreement'}:
        raise ValueError('Expected one edit object: file, source_sha256, before, after, evidence, optional owner_agreement.')
    if edit['file'] != name:
        raise ValueError(f'Only {name} may be updated by this command.')
    if not isinstance(edit['before'], str) or not edit['before'] or not isinstance(edit['after'], str):
        raise ValueError('before must be nonempty text; after must be text.')
    if not isinstance(edit['evidence'], list) or not edit['evidence'] or any(not isinstance(e, str) or not e.strip() for e in edit['evidence']):
        raise ValueError('Evidence references are required; the CLI cannot verify their truth.')
    if name in ('BRAIN.md', 'VISION.md') and (not isinstance(edit.get('owner_agreement'), str) or not edit['owner_agreement'].strip()):
        raise ValueError('An owner_agreement reference is required for BRAIN/VISION; it is not a provider permission grant.')
    source = read_original(root, name)
    if source is None:
        raise ValueError(f'{name} is missing. Use plan init or the agent setup workflow; update does not invent a document.')
    if edit['source_sha256'] != digest(source):
        raise ValueError(f'Source changed: {name}. Read it again and review a fresh edit.')
    if source.count(edit['before']) != 1:
        raise ValueError('The before anchor must match exactly once.')
    return source, source.replace(edit['before'], edit['after'], 1)


def save_exclusive(root, name, source, proposed):
    """Atomic replacement, NOT compare-and-swap against arbitrary editors.

    The caller promises exclusive ownership. Our lock excludes other Horsemen
    writers; a final reread detects changes before replacement, not in its gap.
    """
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    lock = f'.horsemen-{name}.lock'
    temporary = f'.horsemen-{secrets.token_hex(12)}.tmp'
    locked = created = replaced = False
    try:
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        except FileExistsError:
            raise ValueError(f'{name} is locked. Resolve the other writer or stale lock explicitly; no automatic retry.') from None
        os.close(fd)
        locked = True
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('Update requires a regular, non-symlink file with one hard link.')
        if read_original(root, name) != source:
            raise ValueError('Source changed before save; nothing written.')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        created = True
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
            handle.write(proposed)
            handle.flush()
            os.fchmod(handle.fileno(), stat.S_IMODE(info.st_mode))
            os.fsync(handle.fileno())
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_mode, current.st_nlink) != (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_mode, info.st_nlink) or read_original(root, name) != source:
            raise ValueError('Source changed before replacement; nothing written.')
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        created = False
        replaced = True
        if read_original(root, name) != proposed:
            raise ValueError('Read-back differs after replacement; inspect the target before any retry.')
    except (OSError, ValueError) as error:
        if replaced:
            raise ValueError(f'Save occurred but verification failed: {error}') from error
        raise
    finally:
        if created:
            os.unlink(temporary, dir_fd=directory)
        if locked:
            os.unlink(lock, dir_fd=directory)
        os.close(directory)


def run(root, command, *, action=None, changes=None, exclusive=False, dry_run=False, provider='local'):
    if provider != 'local':
        raise ValueError('This CLI supports local root records only. Use the configured provider through its authorized host workflow; no local fallback or provider write occurred.')
    if action is None and (changes or exclusive or dry_run):
        raise ValueError('Update options require the explicit update action.')
    name = document_name(root, command)
    source = read_original(root, name)
    result = {'schema_version': 1, 'command': command, 'document': name,
              'mode': 'read_only', 'content': source, 'source_sha256': digest(source) if source is not None else None,
              'providers': {'status': 'not_checked', 'detail': 'Local record only. Configured outside originals and permissions are not read or changed.'}}
    if action == 'update':
        if not dry_run and not exclusive:
            raise ValueError('Saving requires --exclusive: you must ensure no other editor writes this file until completion. Use --dry-run to review without saving.')
        source, proposed = prepare(root, name, changes)
        result['mode'] = 'draft' if dry_run else 'local_update'
        result['status'] = 'no_change' if source == proposed else 'planned' if dry_run else 'updated'
        result['proposed_sha256'] = digest(proposed)
        result['proposed_content'] = proposed
        if not dry_run and source != proposed:
            save_exclusive(root, name, source, proposed)
        result['content'] = source if dry_run else proposed
        result['source_sha256'] = digest(result['content'])
    result['report'] = report(root, name, result['content'])
    if action is None:
        result['status'] = 'failed' if result['report']['errors'] else 'ok'
    return result
