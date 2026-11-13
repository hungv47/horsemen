"""TECHSTACK companion and proactive brain maintenance regressions."""
import json
import tempfile
import unittest
from pathlib import Path
import horsemen
from e2e import Env, healthy_project, context, review_requested

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'PROGRESS.md').write_text('# Progress\n')
    def tearDown(self): self.temp.cleanup()
    def codes(self): return {(x['file'],x['code']) for k in ('errors','warnings') for x in horsemen.check(self.root)[k]}
    def test_missing_companion_warns(self): self.assertIn(('TECHSTACK.md','techstack-missing'),self.codes())
    def test_legacy_name_needs_migration_without_mutation(self):
        old=self.root/'TECH.md'; old.write_text('# Owner inventory\nKeep this.\n')
        before=old.read_bytes()
        self.assertIn(('TECHSTACK.md','techstack-missing'), self.codes())
        self.assertEqual(old.read_bytes(), before)
        self.assertFalse((self.root/'TECHSTACK.md').exists())
    def test_both_names_preserve_owner_content(self):
        (self.root/'TECH.md').write_text('Legacy owner notes\n')
        (self.root/'TECHSTACK.md').write_text('# Stack\nCurrent owner notes\n')
        before={p.name:p.read_bytes() for p in self.root.iterdir()}
        self.assertNotIn(('TECHSTACK.md','techstack-missing'), self.codes())
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
    def test_template_covers_full_stack(self):
        template=(Path(__file__).resolve().parents[1]/'references/templates.md').read_text()
        section=template.split('### TECHSTACK.md')[1]
        for term in ('Frontend', 'Backend', 'Data', 'Infrastructure', 'Testing', 'Integrations and resources'):
            self.assertIn(term,section)
    def test_template_and_examples_explain_needs_and_help(self):
        refs=Path(__file__).resolve().parents[1]/'references'
        for name in ('templates.md','examples.md'):
            for section in (refs/name).read_text().split('### TECHSTACK.md')[1:]:
                section=section.split('```')[1] if name=='templates.md' else section.split('````')[1]
                self.assertIn('What it needs',section)
                self.assertIn('How it helps',section)
        self.assertIn('junior', (refs/'templates.md').read_text())
    def test_not_fifth_record(self): self.assertNotIn('TECHSTACK.md',horsemen.RECORDS)
    def test_tracks_companion_hash(self): self.assertIn('TECHSTACK.md',horsemen.record_hashes(self.root))
    def test_existing_companion_not_missing(self):
        (self.root/'TECHSTACK.md').write_text('# Technology\nTools: Python.\n')
        self.assertNotIn(('TECHSTACK.md','techstack-missing'),self.codes())
    def test_links_checked(self):
        (self.root/'TECHSTACK.md').write_text('[Setup](missing.md)\n')
        self.assertIn(('TECHSTACK.md','broken-link'),self.codes())
    def test_private_locators_checked(self):
        (self.root/'BRAIN.md').write_text('# Brain\nVisibility: public\n')
        (self.root/'TECHSTACK.md').write_text('https://drive.google.com/file/d/private-id/view\n')
        self.assertIn(('TECHSTACK.md','private-locator'),self.codes())
    def test_no_change_does_not_touch_sources(self):
        (self.root/'TECHSTACK.md').write_text('# Technology\nTools: Python.\n')
        before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.iterdir()}
        self.codes(); horsemen.completion_reminder([])
        self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.iterdir()})
    def test_stop_reviews_real_brain_and_techstack(self):
        reason=horsemen.completion_reminder([])['reason']
        self.assertIn('TECHSTACK',reason); self.assertIn('open relevant brain originals',reason)
        self.assertIn('authorized',reason); self.assertIn('silently',reason)
    def test_no_project_not_inferred_from_companion(self):
        (self.root/'PROGRESS.md').unlink(); (self.root/'TECHSTACK.md').write_text('# Technology\n')
        self.assertIsNone(horsemen.find_root(self.root)[0])

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = Env(self.temp.name)
        self.root = healthy_project(self.env, Path(self.temp.name) / 'project')
    def tearDown(self): self.temp.cleanup()
    def snapshot(self):
        return {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.glob('*.md')}
    def test_initialized_project_has_four_records_and_three_companions(self):
        for name in ('VISION','PROGRESS','BRAIN','STRUCTURE','README','CHANGELOG','TECHSTACK'):
            self.assertTrue((self.root / (name+'.md')).is_file(), name)
        code, report = self.env.check(self.root)
        self.assertEqual(code, 0, report)
        self.assertEqual(report['warnings'], [], report)
    def test_adoption_reports_missing_techstack_without_rewriting_owner_records(self):
        (self.root/'TECHSTACK.md').unlink()
        before = self.snapshot()
        code, report = self.env.check(self.root)
        self.assertEqual(code, 0, report)
        self.assertIn('techstack-missing', {r['code'] for r in report['warnings']})
        self.assertEqual(before, self.snapshot())
    def test_add_companion_clears_warning_without_touching_four_records(self):
        originals = {n: (self.root/n).read_bytes() for n in horsemen.RECORDS}
        (self.root/'TECHSTACK.md').write_text('# Technology\n\nPython: local scripts, version unknown.\n')
        code, report = self.env.check(self.root)
        self.assertEqual(code, 0, report)
        self.assertNotIn('techstack-missing', {r['code'] for r in report['warnings']})
        self.assertEqual(originals, {n: (self.root/n).read_bytes() for n in horsemen.RECORDS})
    def test_repeated_hooks_do_not_write_or_refresh_record_dates(self):
        before = self.snapshot()
        self.env.hook('SessionStart', self.root)
        for _ in range(2):
            code, out, _, _ = self.env.hook('Stop', self.root)
            self.assertEqual(code, 0)
            self.assertTrue(review_requested(out))
            self.assertIn('silently', out['reason'])
            self.assertIn('TECHSTACK', out['reason'])
        self.assertEqual(before, self.snapshot())
    def test_techstack_only_commit_does_not_claim_product_progress(self):
        self.env.hook('SessionStart', self.root)
        with (self.root/'TECHSTACK.md').open('a') as f: f.write('\nTool version verified.\n')
        self.env.git(self.root, 'add', 'TECHSTACK.md')
        self.env.git(self.root, 'commit', '-qm', 'Update tool inventory')
        _, out, _, _ = self.env.hook('Stop', self.root)
        self.assertTrue(review_requested(out))
        self.assertNotIn('work commit', out['reason'])
    def test_legacy_name_never_becomes_project_marker(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'TECH.md').write_text('# Legacy tools\n')
            self.assertIsNone(horsemen.find_root(root)[0])
    def test_legacy_inventory_migration_is_not_product_work(self):
        self.env.git(self.root, 'mv', 'TECHSTACK.md', 'TECH.md')
        self.env.git(self.root, 'commit', '-qm', 'Legacy inventory')
        self.env.hook('SessionStart', self.root)
        self.env.git(self.root, 'mv', 'TECH.md', 'TECHSTACK.md')
        self.env.git(self.root, 'commit', '-qm', 'Migrate inventory name')
        _, out, _, _ = self.env.hook('Stop', self.root)
        self.assertNotIn('work commit', out['reason'])
        self.assertEqual(horsemen.commits_since(self.root, "PROGRESS.md")[0], 0)
    def test_legacy_companion_privacy_is_still_checked(self):
        (self.root/'TECH.md').write_text('https://drive.google.com/file/d/private-id/view\n')
        (self.root/'BRAIN.md').write_text('# Brain\nVisibility: public\n')
        _, report=self.env.check(self.root)
        self.assertIn(('TECH.md','private-locator'), {(x['file'],x['code']) for x in report['errors']})
    def test_resume_with_pre_techstack_cache_still_reviews(self):
        self.env.hook('SessionStart', self.root)
        files=list(self.env.state.rglob('*.json'))
        self.assertTrue(files)
        for path in files:
            data=json.loads(path.read_text())
            data['hashes'].pop('TECHSTACK.md',None)
            path.write_text(json.dumps(data))
        _, out, _, _ = self.env.hook('Stop', self.root)
        self.assertTrue(review_requested(out))
        self.assertIn('TECHSTACK',out['reason'])

if __name__=='__main__': unittest.main()
