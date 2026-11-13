"""Conservative local proposals only. No writes, provider reads or approval."""
import hashlib
import json
import os
import stat
from pathlib import Path

DOCUMENTS = ('VISION.md','PROGRESS.md','BRAIN.md','STRUCTURE.md','README.md','CHANGELOG.md','TECHSTACK.md','AGENTS.md','CLAUDE.md')
MIGRATIONS = {'STATUS.md':'PROGRESS.md','TECH.md':'TECHSTACK.md'}

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def read_original(root, name):
    # Bind the read to a directory descriptor and refuse final-component
    # symlinks at open time, rather than checking then following a new link.
    if name not in DOCUMENTS and name not in MIGRATIONS:
        raise ValueError('Unsupported root document.')
    if not hasattr(os,'O_NOFOLLOW') or not hasattr(os,'O_DIRECTORY'):
        raise ValueError('Safe local planning requires no-follow directory reads on this platform.')
    directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        try:
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        except FileNotFoundError:
            return None
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError(f'Not a regular file: {name}')
            with os.fdopen(fd,encoding='utf-8',newline='') as handle:
                fd=None
                return handle.read()
        finally:
            if fd is not None: os.close(fd)
    finally:
        os.close(directory)

def base(command):
    return {'mode':'plan_only','command':command,'status':'no_change','changes':[], 'gaps':[],
            'limits':['No files or dates changed. No plan is executable approval.',
                      'Local evidence only; providers, live delivery and owner agreement are not verified.']}

def lifecycle_plan(command, root, report, changes_path=None):
    result=base(command)
    originals={name:read_original(root,name) for name in DOCUMENTS}
    legacy={name:read_original(root,name) for name in MIGRATIONS}
    if command=='init':
        for name,text in originals.items():
            if text is not None:
                continue
            older=next((old for old,target in MIGRATIONS.items() if target==name and legacy[old] is not None),None)
            gap = (f'Use upgrade to preserve existing {older}.' if older else
                   'Read existing owner intent; ask only for unresolved intent.' if name=='VISION.md' else
                   'Read existing provider choices, destinations and holds; ask only for unresolved scope.' if name=='BRAIN.md' else
                   'Collect verified project facts; preserve all existing content.')
            result['changes'].append({'file':name,'action':'draft_needed','evidence':{'observation':'file absent'},'requires':gap})
            result['gaps'].append({'file':name,'need':gap})
        if result['gaps']: result['status']='needs_input'
    elif command=='upgrade':
        for old,new in MIGRATIONS.items():
            if legacy[old] is None: continue
            both=originals[new] is not None
            result['changes'].append({'file':new,'source':old,'action':'reconcile' if both else 'migration_review',
                                      'source_sha256':digest(legacy[old]),
                                      'target_sha256':digest(originals[new]) if both else None,
                                      'evidence':{'observation':'both files exist' if both else 'legacy file exists'},
                                      'requires':'Preserve unique content and dates; review inbound links before any authorized move. No rename/delete is performed.'})
            result['gaps'].append({'file':new,'need':'Review legacy content and incoming links; migration does not verify facts.'})
        for item in report['errors']+report['warnings']:
            result['gaps'].append({'file':item['file'],'need':item['message'],'code':item['code']})
        if result['gaps']: result['status']='needs_input'
    else:
        if changes_path is None:
            result['status']='needs_input'
            result['gaps'].append({'need':'Supply explicit proposed changes and evidence references with --changes. No changes supplied is not proof the project is current.'})
            return result
        data=json.loads(Path(changes_path).read_text())
        if not isinstance(data,dict) or set(data)!={'changes'} or not isinstance(data['changes'],list):
            raise ValueError('Expected an object containing only a changes array.')
        seen=set()
        for change in data['changes']:
            if not isinstance(change,dict) or set(change)-{'file','before','after','evidence','owner_agreement'}:
                raise ValueError('Invalid change object or unsupported fields.')
            name=change.get('file')
            if name not in DOCUMENTS or name in seen:
                raise ValueError('Each change must name a unique supported root document.')
            seen.add(name)
            before,after,evidence=change.get('before'),change.get('after'),change.get('evidence')
            if not isinstance(before,str) or not before or not isinstance(after,str):
                raise ValueError('before must be nonempty text and after must be text.')
            if not isinstance(evidence,list) or not evidence or any(not isinstance(e,str) or not e.strip() for e in evidence):
                raise ValueError('Evidence references are required; they are not verified or authorization.')
            source=originals[name]
            if source is None or source.count(before)!=1:
                result['changes'].append({'file':name,'action':'conflict','reason':'Original absent or anchor does not match exactly once.'})
                result['status']='conflict'
                continue
            proposed=source.replace(before,after,1)
            item={'file':name,'action':'no_change' if proposed==source else 'replace_span',
                  'source_sha256':digest(source),'proposed_sha256':digest(proposed),
                  'before':before,'after':after,'evidence_references':evidence,'evidence_verified':False}
            result['changes'].append(item)
            if proposed!=source:
                if result['status']!='conflict': result['status']='planned'
                if name in ('VISION.md','BRAIN.md','AGENTS.md','CLAUDE.md'):
                    result['gaps'].append({'file':name,'need':'Host must verify owner intent and current permissions; an input reference cannot grant approval.',
                                          'owner_agreement_reference':change.get('owner_agreement')})
        if result['gaps'] and result['status']!='conflict': result['status']='needs_input'
        result['limits'].append('An empty changes array means no supplied edits, not verified freshness. Source hashes describe a snapshot and do not prevent future concurrent edits.')
    return result
