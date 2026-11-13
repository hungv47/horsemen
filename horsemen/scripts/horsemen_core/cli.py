"""Read-only standalone CLI; no remote calls or lifecycle writes."""
import argparse
import json
import sys
from pathlib import Path
from . import __version__, legacy
from .plans import lifecycle_plan, read_original, DOCUMENTS, MIGRATIONS
from .patches import export_patch
from .git_read import git_read


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
    parser = argparse.ArgumentParser(prog='horsemen', description='Local read-only checks and inspection. Lifecycle writing remains an agent workflow.')
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('help', help='Show commands without reading a project')
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
    args = parser.parse_args(argv)
    legacy.git = git_read  # This CLI process only; compatibility scripts stay unchanged.
    if args.command == 'help':
        parser.print_help()
        return 0
    try:
        path = Path(args.path).expanduser().resolve()
        if not path.is_dir():
            raise ValueError('Target must be an existing directory.')
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
