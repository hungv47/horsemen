#!/usr/bin/env python3
"""Small provider-neutral original-document update engine. No credentials or daemon."""
from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
import sys
from typing import Callable, Protocol


class BrainError(ValueError):
    """A plan cannot be safely prepared."""


@dataclass(frozen=True)
class Document:
    provider: str
    identity: str
    url: str
    revision: str
    text: str


@dataclass(frozen=True)
class Patch:
    before: str
    after: str


@dataclass(frozen=True)
class Plan:
    source: Document
    after: str

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class Result:
    status: str
    detail: str


class Provider(Protocol):
    """Host adapter must enforce account/scope and atomic revision preconditions.

    search/read return originals, never cache hits. replace must atomically
    compare revision (and before where needed), then write only this document.
    Unsupported conditional writes must fail closed. Never emulate with an
    unguarded read followed by a filesystem overwrite.
    """
    def search(self, query: str) -> list[Document]: ...
    def read(self, identity: str) -> Document: ...
    def replace(self, identity: str, revision: str, before: str, after: str) -> None: ...


def validate(source):
    for key in ('provider', 'identity', 'url', 'revision'):
        if not isinstance(getattr(source, key), str) or not getattr(source, key).strip():
            raise BrainError(f'missing {key}')
    if not isinstance(source.text, str):
        raise BrainError('invalid text')


def prepare_document(source, patch):
    validate(source)
    if not isinstance(patch.before, str) or not patch.before or source.text.count(patch.before) != 1:
        raise BrainError('anchor must match exactly once in the original')
    if not isinstance(patch.after, str):
        raise BrainError('replacement must be text')
    return Plan(source, source.text.replace(patch.before, patch.after, 1))


class Brain:
    def __init__(self, provider: Provider):
        self.provider = provider
        # Disposable navigation metadata only. No permission or content store.
        self.index = {}

    def resolve(self, query):
        matches = self.provider.search(query)
        if len(matches) != 1:
            raise BrainError('missing original' if not matches else 'ambiguous originals')
        return self._read(matches[0].identity)

    def _read(self, identity):
        source = self.provider.read(identity)
        validate(source)
        if source.identity != identity:
            raise BrainError('original identity mismatch')
        return source

    def prepare(self, identity, patch):
        return prepare_document(self._read(identity), patch)

    def apply(self, plan: Plan, authorize: Callable[[Plan], bool]):
        """authorize is a trusted host policy check, never a persisted approval flag.

        It receives the complete immutable plan. Host checks current permission,
        holds, data scope, exact destination and requested content. This engine
        does not grant permission or implement the host's confirmation policy.
        """
        validate(plan.source)
        if not isinstance(plan.after, str):
            raise BrainError('replacement must be text')
        identity = plan.source.identity
        self.index.pop(identity, None)
        if plan.after != plan.source.text and authorize(plan) is not True:
            return Result('denied', 'No write was attempted.')
        try:
            current = self._read(identity)
        except Exception:
            return Result('unavailable', 'Original could not be read; no write attempted.')
        if current != plan.source:
            return Result('conflict', 'Original changed; read and prepare a new plan.')
        if plan.after == plan.source.text:
            self._refresh(current)
            return Result('no_change', 'Original already matches; no write attempted.')
        try:
            self.provider.replace(identity, current.revision, current.text, plan.after)
        except Exception:
            # Even an exception can follow a successful write. Never retry here.
            return Result('uncertain', 'Write outcome unknown; inspect the original before any retry.')
        try:
            verified = self._read(identity)
            if (verified.provider, verified.url, verified.text) != (current.provider, current.url, plan.after):
                raise BrainError('verification mismatch')
        except Exception:
            return Result('uncertain', 'Write returned but verification failed; inspect the original.')
        self._refresh(verified)
        return Result('verified', 'Original read back and navigation refreshed.')

    def _refresh(self, source):
        self.index[source.identity] = {key: getattr(source, key) for key in ('provider', 'identity', 'url', 'revision')}


def main():
    parser = argparse.ArgumentParser(description='Prepare an exact text change from a host-read original. Never writes to a provider.')
    parser.add_argument('command', choices=['prepare'])
    parser.parse_args()
    try:
        data = json.load(sys.stdin)
        plan = prepare_document(Document(**data['source']), Patch(**data['patch']))
        print(json.dumps({**asdict(plan), 'fingerprint': plan.fingerprint}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError) as error:
        print(f'Cannot prepare: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
