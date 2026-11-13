import unittest
from dataclasses import replace
from brain import Brain, Document, Patch, BrainError
from records import Change, prepare_record, apply_record, should_report
from test_brain import Provider

class Tests(unittest.TestCase):
    def setUp(self): self.p = Provider(); self.b = Brain(self.p)
    def plan(self, record, event, evidence=(), agreement=''):
        return prepare_record(self.b, 'one', Patch('Old decision','New decision'), Change(record,event,evidence,agreement))
    def test_all_require_evidence(self):
        for r,e in [('VISION','direction'),('PROGRESS','status'),('BRAIN','navigation'),('STRUCTURE','location')]:
            with self.subTest(r=r), self.assertRaises(BrainError): self.plan(r,e)
    def test_vision_agreement_required(self):
        with self.assertRaises(BrainError): self.plan('VISION','direction',('source',))
    def test_brain_choices_require_agreement(self):
        with self.assertRaises(BrainError): self.plan('BRAIN','provider',('source',))
    def test_progress_priority_requires_agreement(self):
        with self.assertRaises(BrainError): self.plan('PROGRESS','priority',('source',))
    def test_distinct_events(self):
        with self.assertRaises(BrainError): self.plan('STRUCTURE','direction',('source',))
    def test_direction_dependencies(self):
        self.assertEqual(self.plan('VISION','direction',('source',),'owner message').review, ('README','PROGRESS','BRAIN'))
    def test_shipped_dependencies(self):
        self.assertEqual(self.plan('PROGRESS','delivered',('release',)).review, ('CHANGELOG','README'))
    def test_brain_dependencies(self):
        self.assertEqual(self.plan('BRAIN','provider',('source',),'owner').review, ('STRUCTURE',))
    def test_all_deny_without_writes(self):
        for r,e in [('VISION','direction'),('PROGRESS','status'),('BRAIN','navigation'),('STRUCTURE','location')]:
            self.assertEqual(apply_record(self.b,self.plan(r,e,('source',),'owner'),lambda p: False).status,'denied')
        self.assertEqual(self.p.writes,0)
    def test_all_drift(self):
        for r,e in [('VISION','direction'),('PROGRESS','status'),('BRAIN','navigation'),('STRUCTURE','location')]:
            plan=self.plan(r,e,('source',),'owner'); self.p.doc=replace(self.p.doc,revision=self.p.doc.revision+'x')
            self.assertEqual(apply_record(self.b,plan,lambda p: True).status,'conflict')
    def test_all_no_change_needs_no_new_agreement(self):
        for r,e in [('VISION','direction'),('PROGRESS','status'),('BRAIN','provider'),('STRUCTURE','location')]:
            plan=prepare_record(self.b,'one',Patch('Old decision','Old decision'),Change(r,e))
            self.assertEqual(apply_record(self.b,plan,lambda p: self.fail()).status,'no_change')
            self.assertEqual(plan.review,())
    def test_review_is_not_cascade_write(self):
        p=self.plan('VISION','direction',('source',),'owner')
        result=apply_record(self.b,p,lambda offered: offered.change.record=='VISION')
        self.assertEqual(result.status,'verified'); self.assertEqual(self.p.writes,1)

class ReportingTests(unittest.TestCase):
    def test_hook_keeps_task_report_primary(self):
        from horsemen import completion_reminder
        reason=completion_reminder([])['reason']
        self.assertIn('silently',reason)
        self.assertIn('unless asked',reason)
        self.assertIn('permission questions',reason)

    def test_silent_by_default(self): self.assertFalse(should_report())
    def test_requested_update(self): self.assertTrue(should_report(requested=True))
    def test_permission_visible(self): self.assertTrue(should_report(permission_needed=True))
    def test_actionable_blocker_visible(self): self.assertTrue(should_report(actionable_blocker=True))

if __name__=='__main__': unittest.main()
