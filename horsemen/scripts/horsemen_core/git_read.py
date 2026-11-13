"""Disable configured executable helpers for standalone local Git inspection."""
import re
from . import legacy

_run = legacy.git
_BASE = ('-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null')


def git_read(root,*args,ok_codes=(0,)):
    # Query effective configuration without invoking status/diff helpers first.
    config=_run(root,*_BASE,'config','--null','--get-regexp',
                r'^filter\..*\.(clean|smudge|process|required)$',ok_codes=(0,1))
    if config is None:
        return None  # Do not inspect through unknown executable helper config.
    options=list(_BASE)
    for entry in config.split('\0'):
        key=entry.split('\n',1)[0]
        if not key: continue
        if not re.fullmatch(r'filter\..+\.(clean|smudge|process|required)',key,re.I):
            return None
        value='false' if key.lower().endswith('.required') else ''
        options.extend(('-c',key+'='+value))
    return _run(root,*options,*args,ok_codes=ok_codes)
