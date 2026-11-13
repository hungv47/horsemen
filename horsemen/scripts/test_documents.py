"""Empirical single-record I/O failures; no live providers or user records."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from horsemen_core import documents


class Documents(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / 'BRAIN.md'
        self.source = '# Brain\nBrain: None\nVisibility: private\n'
        self.path.write_text(self.source)
    def tearDown(self):
        self.temp.cleanup()
    def test_scoped_report_never_reads_another_record(self):
        real = documents.read_original
        reads = []
        def read(root, name):
            reads.append(name)
            return real(root, name)
        with patch.object(documents, 'read_original', side_effect=read), patch.object(documents.legacy, 'read', side_effect=AssertionError('unscoped read')):
            documents.run(self.root, 'brain')
        self.assertEqual(set(reads), {'BRAIN.md'})
    def test_replace_failure_preserves_original_and_cleans_own_files(self):
        with patch.object(documents.os, 'replace', side_effect=OSError('simulated storage failure')):
            with self.assertRaisesRegex(OSError, 'storage failure'):
                documents.save_exclusive(self.root, 'BRAIN.md', self.source, self.source+'new')
        self.assertEqual(self.path.read_text(), self.source)
        self.assertEqual([p.name for p in self.root.iterdir()], ['BRAIN.md'])
    def test_changed_source_before_replace_is_not_overwritten(self):
        real = documents.os.fsync
        def editor(fd):
            real(fd)
            self.path.write_text('concurrent edit')
        with patch.object(documents.os, 'fsync', side_effect=editor):
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                documents.save_exclusive(self.root, 'BRAIN.md', self.source, self.source+'new')
        self.assertEqual(self.path.read_text(), 'concurrent edit')
        self.assertEqual([p.name for p in self.root.iterdir()], ['BRAIN.md'])
    def test_after_replace_readback_failure_reports_save_occurred(self):
        real = documents.read_original
        calls = 0
        def read(root, name):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError('simulated read-back failure')
            return real(root, name)
        with patch.object(documents, 'read_original', side_effect=read):
            with self.assertRaisesRegex(ValueError, 'Save occurred but verification failed'):
                documents.save_exclusive(self.root, 'BRAIN.md', self.source, self.source+'new')
        self.assertEqual(self.path.read_text(), self.source+'new')
    def test_provider_route_fails_before_any_local_read_or_write(self):
        with patch.object(documents, 'read_original', side_effect=AssertionError('local fallback')), patch.object(documents, 'save_exclusive', side_effect=AssertionError('write')):
            with self.assertRaisesRegex(ValueError, 'authorized host'):
                documents.run(self.root, 'brain', action='update', provider='drive', exclusive=True)


if __name__ == '__main__':
    unittest.main()
