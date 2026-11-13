"""Failure modes first: original resolution, stale writes, permissions and recovery."""
import unittest
import subprocess
import json
import sys
from pathlib import Path
from dataclasses import replace
from brain import Brain, Document, Patch, BrainError

class Provider:
    def __init__(self):
        self.doc = Document('drive', 'one', 'https://example.test/one', 'r1', 'Old decision\nKeep this.\n')
        self.writes = 0
        self.offline = False
        self.uncertain = False
        self.bad_verify = False
    def search(self, query): return [self.doc]
    def read(self, identity):
        if self.offline: raise OSError('offline')
        return self.doc
    def replace(self, identity, revision, before, after):
        if revision != self.doc.revision: raise BrainError('conflict')
        self.writes += 1
        self.doc = replace(self.doc, revision='r2', text=after)
        if self.uncertain: raise OSError('lost acknowledgement')
        if self.bad_verify: self.doc = replace(self.doc, text='unexpected')

class Tests(unittest.TestCase):
    def setUp(self):
        self.p = Provider(); self.b = Brain(self.p)
    def prepare(self): return self.b.prepare('one', Patch('Old decision', 'New decision'))
    def test_resolve_original(self):
        self.assertEqual(self.b.resolve('decision').identity, 'one')
    def test_ambiguous(self):
        self.p.search = lambda q: [self.p.doc, replace(self.p.doc, identity='two')]
        with self.assertRaisesRegex(BrainError, 'ambiguous'): self.b.resolve('decision')
    def test_missing(self):
        self.p.search = lambda q: []
        with self.assertRaisesRegex(BrainError, 'missing'): self.b.resolve('decision')
    def test_precise_prepare(self):
        plan = self.prepare()
        self.assertEqual(plan.after, 'New decision\nKeep this.\n'); self.assertEqual(self.p.writes, 0)
    def test_multiple_anchors(self):
        self.p.doc = replace(self.p.doc, text='Old decision Old decision')
        with self.assertRaisesRegex(BrainError, 'anchor'): self.prepare()
    def test_missing_anchor(self):
        with self.assertRaisesRegex(BrainError, 'anchor'): self.b.prepare('one', Patch('missing', 'new'))
    def test_empty_anchor(self):
        with self.assertRaisesRegex(BrainError, 'anchor'): self.b.prepare('one', Patch('', 'new'))
    def test_denied(self):
        result = self.b.apply(self.prepare(), lambda plan: False)
        self.assertEqual(result.status, 'denied'); self.assertEqual(self.p.writes, 0)
    def test_truthy_not_approval(self):
        self.assertEqual(self.b.apply(self.prepare(), lambda p: 'yes').status, 'denied')
    def test_no_change(self):
        plan = self.b.prepare('one', Patch('Old decision', 'Old decision'))
        self.assertEqual(self.b.apply(plan, lambda p: self.fail('No approval needed')).status, 'no_change')
        self.assertEqual(self.p.writes, 0)
    def test_revision_conflict(self):
        plan = self.prepare(); self.p.doc = replace(self.p.doc, revision='r3')
        self.assertEqual(self.b.apply(plan, lambda p: True).status, 'conflict'); self.assertEqual(self.p.writes, 0)
    def test_content_conflict(self):
        plan = self.prepare(); self.p.doc = replace(self.p.doc, text='Other')
        self.assertEqual(self.b.apply(plan, lambda p: True).status, 'conflict')
    def test_offline(self):
        plan = self.prepare(); self.p.offline = True
        self.assertEqual(self.b.apply(plan, lambda p: True).status, 'unavailable'); self.assertEqual(self.p.writes, 0)
    def test_verify_and_refresh(self):
        result = self.b.apply(self.prepare(), lambda p: True)
        self.assertEqual(result.status, 'verified'); self.assertEqual(self.b.index['one']['revision'], 'r2')
        self.assertNotIn('text', self.b.index['one'])
    def test_uncertain_no_retry(self):
        self.p.uncertain = True
        self.assertEqual(self.b.apply(self.prepare(), lambda p: True).status, 'uncertain')
        self.assertEqual(self.p.writes, 1); self.assertEqual(self.b.index, {})
    def test_verification_failure(self):
        self.p.bad_verify = True
        self.assertEqual(self.b.apply(self.prepare(), lambda p: True).status, 'uncertain')
        self.assertEqual(self.b.index, {})
    def test_identity_mismatch(self):
        self.p.doc = replace(self.p.doc, identity='other')
        with self.assertRaisesRegex(BrainError, 'identity'): self.prepare()
    def test_cache_never_authority(self):
        self.b.index['one'] = {'revision': 'invented'}
        self.assertEqual(self.prepare().source.revision, 'r1')
    def test_approval_changes_source(self):
        def approve(plan):
            self.p.doc = replace(self.p.doc, revision='r3'); return True
        self.assertEqual(self.b.apply(self.prepare(), approve).status, 'conflict')
    def test_invalid_revision(self):
        self.p.doc = replace(self.p.doc, revision='')
        with self.assertRaisesRegex(BrainError, 'revision'): self.prepare()

class CliTests(unittest.TestCase):
    def run_cli(self, payload):
        return subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('brain.py')), 'prepare'], input=json.dumps(payload), text=True, capture_output=True)
    def test_prepare_only_cli(self):
        payload = {'source': {'provider': 'drive', 'identity': 'one', 'url': 'https://example.test/one', 'revision': 'r1', 'text': 'old'}, 'patch': {'before': 'old', 'after': 'new'}}
        result = self.run_cli(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['after'], 'new')
    def test_invalid_input(self):
        self.assertNotEqual(self.run_cli({}).returncode, 0)

if __name__ == '__main__': unittest.main()
