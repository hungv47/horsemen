#!/usr/bin/env python3
"""Compatibility entrypoint for existing scripts and host hooks."""
import sys
from horsemen_core import legacy
if __name__ == '__main__':
    raise SystemExit(legacy.main(sys.argv[1:]))
sys.modules[__name__] = legacy
