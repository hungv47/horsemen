"""Local project checks, explicit single-record edits, and review plans."""
import argparse
import json
import sys
from pathlib import Path
from . import __version__, legacy
from .plans import lifecycle_plan, read_original, DOCUMENTS, MIGRATIONS
from .patches import export_patch
from .git_read import git_read
from . import documents


def report_for(path, exact=False):
    root, top = (path,legacy.git_top(path)) if exact else legacy.find_root(path)
    root = root or path
    report = legacy.check(root, top)
    since = legacy.commits_since(root, report['info']['progress_file']) if top else None
    report['info']['commits_since_progress'] = since[0] if since else None
    return root, top, report


def inspect_local(root, top, report):
    git = {'available': top is not None, 'scope': 'local checkout only'}
    if top:
        for key, args in (
            ('head', ('rev-parse', 'HEAD')),
            ('branch', ('symbolic-ref', '--quiet', '--short', 'HEAD')),
            ('status_porcelain', ('status', '--porcelain=v1', '--untracked-files=normal')),
            ('worktrees_porcelain', ('worktree', 'list', '--porcelain')),
        ):
            value = legacy.git(root, *args)
            git[key] = value.rstrip('\n') if value is not None else None
        git['limits'] = 'Null fields are unavailable or not applicable. Detached HEAD has no branch name. Other worktrees are listed, not inspected.'
    text = legacy.read(root / report['info']['progress_file'])
    return {'git': git, 'snapshot': legacy.split_progress(text)[0].strip() if text else None,
            'remote': {'status': 'not_checked', 'detail': 'No remote refs, PRs, CI or deployments were queried.'},
            'providers': {'status': 'not_checked', 'detail': 'BRAIN routes were validated locally; originals, accounts and permissions were not verified.'}}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # Preserve established spellings and their JSON/exit contracts, but keep the
    # main menu task-oriented. No legacy caller acquires write behavior.
    compatibility = bool(argv and argv[0] in ('help', 'init', 'update', 'upgrade', 'export-patch'))
    if argv and argv[0] == 'help':
        argv = ['--help', *argv[1:]]
        compatibility = False
    if argv and argv[0] == 'plan':
        argv = argv[1:]
        if not argv or argv[0] in ('-h', '--help'):
            print('usage: horsemen plan {init,update,upgrade,export-patch} [PATH] [options]\n'
                  'Read-only setup, edit and migration proposals. Nothing is applied.\n'
                  'update needs --changes FILE; export-patch needs --plan-file FILE.\n'
                  'Use horsemen plan COMMAND --help for details.')
            return 0
        if argv[0] not in ('init', 'update', 'upgrade', 'export-patch'):
            print('Unknown plan command.', file=sys.stderr)
            return 2
        if argv[0] != 'export-patch' and '--plan' not in argv:
            argv.append('--plan')
        compatibility = True
    parser = argparse.ArgumentParser(prog='horsemen', description='Check one record, inspect a project, or explicitly update one local record.')
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name, filename in documents.NAMES.items():
        cmd = sub.add_parser(name, help=f'Read/check {filename}; update explicitly')
        cmd.add_argument('action', nargs='?', choices=('update',), help='Save one exact edit; default only reads')
        cmd.add_argument('--path', default='.', help='Project directory (default: current project)')
        cmd.add_argument('--json', action='store_true')
        cmd.add_argument('--changes', help='One JSON edit with source_sha256, before, after and evidence')
        cmd.add_argument('--exclusive', action='store_true', help='Promise no other editor writes this record during save')
        cmd.add_argument('--dry-run', action='store_true', help='Validate and show the proposed content without writing')
        cmd.add_argument('--provider', default='local', help='local only; other providers require the authorized host workflow')
    sub.add_parser('plan', help='Prepare setup, migration or edit proposals; never apply')
    export=sub.add_parser('export-patch',help='Validate an update plan and print a review patch; never apply')
    export.add_argument('path',nargs='?',default='.')
    export.add_argument('--plan-file',required=True)
    for name in ('check', 'inspect', 'init', 'update', 'upgrade'):
        command = sub.add_parser(name, help={'check':'Validate local records','inspect':'Read local records and Git state; no remote queries'}.get(name,'Plan local '+name+' only; never write'))
        command.add_argument('path', nargs='?', default='.')
        command.add_argument('--json', action='store_true')
        if name in ('init','update','upgrade'):
            command.add_argument('--plan', action='store_true', required=True, help='Produce a read-only proposal; never apply it')
        if name=='update':
            command.add_argument('--changes', help='Local JSON file with proposed edits and evidence references')
    if not compatibility:
        hidden = {'export-patch', 'init', 'update', 'upgrade'}
        sub._choices_actions[:] = [a for a in sub._choices_actions if a.dest not in hidden]
        sub.metavar = '{brain,vision,structure,status,check,inspect,plan}'
    args = parser.parse_args(argv)
    legacy.git = git_read  # This CLI process only; compatibility scripts stay unchanged.
    try:
        path = Path(args.path).expanduser().resolve()
        if not path.is_dir():
            raise ValueError('Target must be an existing directory.')
        if args.command in documents.NAMES:
            root = legacy.find_root(path)[0] or path
            result = documents.run(root, args.command, action=args.action, changes=args.changes,
                                   exclusive=args.exclusive, dry_run=args.dry_run, provider=args.provider)
            if args.json:
                print(json.dumps(result, ensure_ascii=False))
            else:
                print(f"{result['document']}: {result['status']} ({result['mode']})")
                print(result.get('proposed_content', result['content']) or 'Document missing.')
                for level in ('errors', 'warnings'):
                    for item in result['report'][level]:
                        print(f"{level}: {item['message']}")
                print('Provider originals: not checked or changed.')
            return 1 if result['report']['errors'] else 0
        if args.command=='export-patch':
            root=legacy.find_root(path)[0] or path
            patch=export_patch(root, args.plan_file)
            sys.stdout.write(patch)
            return 0
        if args.command in ('init','update','upgrade'):
            target=path if args.command=='init' else (legacy.find_root(path)[0] or path)
            for name in (*DOCUMENTS,*MIGRATIONS):
                read_original(target,name)  # Fail on unsupported targets before checker reads.
        root, top, report = report_for(path,exact=args.command=='init')
        result = {'schema_version': 1, 'command': args.command,
                  'status': 'failed' if report['errors'] else 'ok', 'report': report}
        if args.command in ('init','update','upgrade'):
            result['plan']=lifecycle_plan(args.command,root,report,getattr(args,'changes',None))
            result['status']=result['plan']['status']
        if args.command == 'inspect':
            result.update(inspect_local(root, top, report))
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            legacy.print_report(report)
            if 'plan' in result:
                print('\nRead-only plan:\n'+json.dumps(result['plan'],ensure_ascii=False,indent=2))
            if args.command == 'inspect':
                print('\nLocal Git:', json.dumps(result['git'], ensure_ascii=False))
                print('\nProgress snapshot:\n' + (result['snapshot'] or 'Unavailable'))
                print('\nRemote services: not checked. Provider originals: not checked.')
        if 'plan' in result:
            return 0  # Valid proposal, including explicit gaps/conflicts; nothing was applied.
        return 1 if report['errors'] else 0
    except (OSError, ValueError) as error:
        if getattr(args,'json',False):
            print(json.dumps({'schema_version': 1, 'command': args.command, 'status': 'error', 'error': str(error)}))
        else:
            print(f'Cannot {args.command}: {error}', file=sys.stderr)
        return 2
