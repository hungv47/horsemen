"""Validate an update plan against local originals and return a review diff."""
import difflib
import json
import os
import stat
from pathlib import Path
from .plans import DOCUMENTS, digest, read_original


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key in plan.')
        result[key]=value
    return result


def patch_lines(text):
    # Unified diffs count LF-delimited lines, not Unicode separators or lone CR.
    chunks=text.split('\n')
    return [line+'\n' for line in chunks[:-1]]+([chunks[-1]] if chunks[-1] else [])


def export_patch(root, plan_path):
    path=Path(plan_path)
    if not hasattr(os,'O_NOFOLLOW'):
        raise ValueError('Safe patch export needs no-follow reads on this platform.')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('Plan must be a regular, non-symlink file.')
        with os.fdopen(fd,encoding='utf-8') as handle:
            fd=None
            data=json.load(handle,object_pairs_hook=unique_object)
    finally:
        if fd is not None: os.close(fd)
    if not isinstance(data,dict) or type(data.get('schema_version')) is not int or data.get('schema_version')!=1 or data.get('command')!='update':
        raise ValueError('Expected a version 1 update-plan result.')
    report=data.get('report'); plan=data.get('plan')
    if not isinstance(report,dict) or not isinstance(report.get('root'),str) or Path(report['root']).resolve()!=root.resolve():
        raise ValueError('Plan belongs to a different project root.')
    if not isinstance(plan,dict) or plan.get('mode')!='plan_only' or plan.get('command')!='update' or plan.get('status') not in ('planned','no_change','needs_input'):
        raise ValueError('Only nonconflicting update proposals can be exported.')
    changes=plan.get('changes')
    if not isinstance(changes,list): raise ValueError('Invalid plan changes.')
    seen=set(); diffs=[]
    for item in changes:
        allowed={'file','action','source_sha256','proposed_sha256','before','after','evidence_references','evidence_verified'}
        if not isinstance(item,dict) or set(item)!=allowed:
            raise ValueError('Invalid plan change fields; approval data is not accepted.')
        name=item['file']
        if not isinstance(name,str) or name not in DOCUMENTS or name in seen:
            raise ValueError('Invalid or duplicate document target.')
        seen.add(name)
        before,after=item['before'],item['after']
        evidence=item['evidence_references']
        if not isinstance(before,str) or not before or not isinstance(after,str):
            raise ValueError('Invalid patch anchor or replacement.')
        if not isinstance(evidence,list) or not evidence or any(not isinstance(e,str) or not e.strip() for e in evidence) or item['evidence_verified'] is not False:
            raise ValueError('Evidence must remain unverified references, not authorization.')
        source=read_original(root,name)
        if source is None or digest(source)!=item['source_sha256'] or source.count(before)!=1:
            raise ValueError(f'Source changed or anchor is ambiguous: {name}')
        proposed=source.replace(before,after,1)
        action='no_change' if proposed==source else 'replace_span'
        if digest(proposed)!=item['proposed_sha256'] or item['action']!=action:
            raise ValueError(f'Proposed result does not match the plan: {name}')
        # Validate the whole batch before returning any output.
        for line in difflib.unified_diff(patch_lines(source),patch_lines(proposed),fromfile='a/'+name,tofile='b/'+name):
            diffs.append(line)
            if not line.endswith('\n'):
                diffs.append('\n\\ No newline at end of file\n')
    return ''.join(diffs)
