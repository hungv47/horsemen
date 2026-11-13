"""Subprocess tests: source CLI or HORSEMEN_CLI executable from a built wheel."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from e2e import Env,healthy_project
from horsemen_core import __version__
SCRIPTS=Path(__file__).resolve().parent
class CLI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.env=Env(self.tmp.name)
        self.root=healthy_project(self.env,Path(self.tmp.name)/'project with spaces')
    def tearDown(self): self.tmp.cleanup()
    def run_cli(self,*args,cwd=None,binary=False):
        cmd=[os.environ['HORSEMEN_CLI']] if os.environ.get('HORSEMEN_CLI') else [sys.executable,'-B','-m','horsemen_core']
        env=dict(self.env.env, PYTHONPATH=str(SCRIPTS),PYTHONDONTWRITEBYTECODE='1')
        if os.environ.get('HORSEMEN_CLI'): env.pop('PYTHONPATH',None)
        return subprocess.run(cmd+list(args),cwd=cwd or self.root,env=env,text=not binary,capture_output=True)
    def document_edit(self, command, **overrides):
        import hashlib
        names={'brain':'BRAIN.md','vision':'VISION.md','structure':'STRUCTURE.md','status':'PROGRESS.md'}
        name=names[command]; source=(self.root/name).read_text()
        edit={'file':name,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
              'before':source.splitlines()[0], 'after':source.splitlines()[0]+' revised',
              'evidence':['Owner supplied correction'], 'owner_agreement':'Owner requested this exact edit'}
        edit.update(overrides)
        path=Path(self.tmp.name)/'edit.json'; path.write_text(json.dumps(edit))
        return str(path)
    def test_document_default_is_scoped_read_only(self):
        before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.glob('*.md')}
        for command,name in [('brain','BRAIN.md'),('vision','VISION.md'),('structure','STRUCTURE.md'),('status','PROGRESS.md')]:
            p=self.run_cli(command,'--json'); self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            d=json.loads(p.stdout); self.assertEqual(d['document'],name)
            self.assertEqual(d['mode'],'read_only'); self.assertIn('content',d)
            self.assertTrue(all(x['file']==name for x in d['report']['errors']+d['report']['warnings']))
        self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.glob('*.md')})
    def test_document_ignores_unrelated_broken_record(self):
        (self.root/'VISION.md').unlink(); (self.root/'VISION.md').symlink_to('/does/not/exist')
        self.assertEqual(self.run_cli('brain','--json').returncode,0)
    def test_document_update_isolated_for_every_record(self):
        for command,name in [('brain','BRAIN.md'),('vision','VISION.md'),('structure','STRUCTURE.md'),('status','PROGRESS.md')]:
            before={p.name:p.read_bytes() for p in self.root.glob('*.md')}
            edit=self.document_edit(command)
            p=self.run_cli(command,'update','--changes',edit,'--exclusive','--json')
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertEqual(json.loads(p.stdout)['status'],'updated')
            after={p.name:p.read_bytes() for p in self.root.glob('*.md')}
            self.assertEqual([k for k in before if before[k]!=after[k]],[name])
    def test_document_update_missing_input_or_exclusive_fails(self):
        before=(self.root/'BRAIN.md').read_bytes()
        for args in [(),('--exclusive',),('--changes',self.document_edit('brain'))]:
            self.assertEqual(self.run_cli('brain','update',*args,'--json').returncode,2)
        self.assertEqual(before,(self.root/'BRAIN.md').read_bytes())
    def test_document_update_rejects_invalid_or_stale_edits(self):
        before=(self.root/'BRAIN.md').read_bytes()
        for override in [{'file':'VISION.md'},{'file':'../BRAIN.md'},{'source_sha256':'0'*64},
                         {'before':'absent anchor'},{'evidence':[]},{'owner_agreement':''},
                         {'extra':True},{'after':None}]:
            p=self.run_cli('brain','update','--changes',self.document_edit('brain',**override),'--exclusive','--json')
            self.assertEqual(p.returncode,2,p.stdout+p.stderr)
            self.assertEqual(before,(self.root/'BRAIN.md').read_bytes())
    def test_document_update_dry_run_and_noop(self):
        path=self.root/'STRUCTURE.md'; before=(path.read_bytes(),path.stat().st_mtime_ns)
        p=self.run_cli('structure','update','--changes',self.document_edit('structure'),'--dry-run','--json')
        self.assertEqual(p.returncode,0,p.stderr); self.assertEqual(json.loads(p.stdout)['status'],'planned')
        self.assertEqual(before,(path.read_bytes(),path.stat().st_mtime_ns))
        edit=self.document_edit('structure',after=path.read_text().splitlines()[0])
        p=self.run_cli('structure','update','--changes',edit,'--exclusive','--json')
        self.assertEqual(p.returncode,0,p.stderr); self.assertEqual(json.loads(p.stdout)['status'],'no_change')
        self.assertEqual(before,(path.read_bytes(),path.stat().st_mtime_ns))
    def test_document_configured_knowledge_is_not_bulk_sync(self):
        path=self.root/'BRAIN.md'; path.write_text(path.read_text().replace('Brain: None','Brain: Google Drive'))
        p=self.run_cli('brain','--json'); self.assertEqual(p.returncode,0,p.stdout)
        self.assertEqual(json.loads(p.stdout)['providers']['status'],'not_checked')
        edit=self.document_edit('brain')
        p=self.run_cli('brain','update','--changes',edit,'--exclusive','--provider','drive','--json')
        self.assertEqual(p.returncode,2); self.assertIn('host',p.stdout)
        p=self.run_cli('brain','update','--changes',edit,'--exclusive','--json')
        self.assertEqual(p.returncode,0,p.stdout)
    def test_document_missing_and_symlink_fail(self):
        path=self.root/'VISION.md'; path.unlink()
        self.assertEqual(self.run_cli('vision','--json').returncode,1)
        path.symlink_to(self.root/'BRAIN.md')
        self.assertEqual(self.run_cli('vision','--json').returncode,2)
    def test_status_preserves_legacy_filename(self):
        (self.root/'PROGRESS.md').rename(self.root/'STATUS.md')
        p=self.run_cli('status','--json'); self.assertEqual(p.returncode,0,p.stdout)
        self.assertEqual(json.loads(p.stdout)['document'],'STATUS.md')
        self.assertFalse((self.root/'PROGRESS.md').exists())
    def test_document_preserves_crlf_mode_and_other_content(self):
        import hashlib
        path=self.root/'STRUCTURE.md'
        source=path.read_text().replace('\n','\r\n').rstrip('\r\n')
        path.write_bytes(source.encode()); path.chmod(0o640)
        edit={'file':'STRUCTURE.md','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
              'before':'# Structure','after':'# Structure revised','evidence':['test']}
        data=Path(self.tmp.name)/'crlf.json'; data.write_text(json.dumps(edit))
        p=self.run_cli('structure','update','--changes',str(data),'--exclusive','--json')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(path.read_bytes(),source.replace('# Structure','# Structure revised',1).encode())
        self.assertEqual(path.stat().st_mode & 0o777,0o640)
    def test_document_rejects_duplicate_json_and_repeat_save(self):
        edit=Path(self.document_edit('structure')); original=edit.read_text()
        edit.write_text(original.replace('"file":', '"file":"VISION.md", "file":',1))
        p=self.run_cli('structure','update','--changes',str(edit),'--exclusive','--json')
        self.assertEqual(p.returncode,2)
        edit.write_text(original)
        self.assertEqual(self.run_cli('structure','update','--changes',str(edit),'--exclusive').returncode,0)
        self.assertEqual(self.run_cli('structure','update','--changes',str(edit),'--exclusive').returncode,2)
    def test_document_existing_lock_and_hardlink_fail(self):
        edit=self.document_edit('structure'); path=self.root/'STRUCTURE.md'; before=path.read_bytes()
        lock=self.root/'.horsemen-STRUCTURE.md.lock'; lock.write_text('other writer')
        self.assertEqual(self.run_cli('structure','update','--changes',edit,'--exclusive').returncode,2)
        self.assertEqual(lock.read_text(),'other writer'); lock.unlink()
        os.link(path,self.root/'linked.md')
        self.assertEqual(self.run_cli('structure','update','--changes',edit,'--exclusive').returncode,2)
        self.assertEqual(before,path.read_bytes()); self.assertFalse(lock.exists())
    def test_document_read_rejects_update_flags(self):
        self.assertEqual(self.run_cli('brain','--exclusive','--json').returncode,2)
    def test_document_both_status_files_fail_without_writes(self):
        (self.root/'STATUS.md').write_text('Unique old content')
        self.assertEqual(self.run_cli('status','--json').returncode,2)

    def test_grouped_plan_commands_preserve_legacy_results(self):
        source=(self.root/'TECHSTACK.md').read_text()
        changes=self.changes_file(source,source+'\nExtra verified context.\n')
        for command,args in [('init',()),('upgrade',()),('update',('--changes',changes))]:
            grouped=self.run_cli('plan',command,*args,'--json')
            old=self.run_cli(command,'--plan',*args,'--json')
            self.assertEqual(grouped.returncode,old.returncode)
            self.assertEqual(json.loads(grouped.stdout),json.loads(old.stdout))
        plan=Path(self.tmp.name)/'grouped-plan.json'; plan.write_text(grouped.stdout)
        grouped_patch=self.run_cli('plan','export-patch','--plan-file',str(plan))
        old_patch=self.run_cli('export-patch','--plan-file',str(plan))
        self.assertEqual(grouped_patch.returncode,0,grouped_patch.stderr)
        self.assertEqual(grouped_patch.stdout,old_patch.stdout)
    def test_status_update_uses_existing_legacy_original(self):
        edit=Path(self.document_edit('status')); data=json.loads(edit.read_text())
        data['file']='STATUS.md'; edit.write_text(json.dumps(data))
        (self.root/'PROGRESS.md').rename(self.root/'STATUS.md')
        p=self.run_cli('status','update','--changes',str(edit),'--exclusive','--json')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)['document'],'STATUS.md')
        self.assertFalse((self.root/'PROGRESS.md').exists())
    def test_named_record_works_without_git(self):
        self.root=healthy_project(self.env,Path(self.tmp.name)/'standalone',git=False)
        self.assertEqual(self.run_cli('brain','--json').returncode,0)
        p=self.run_cli('brain','update','--changes',self.document_edit('brain'),'--exclusive','--json')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_document_update_symlink_and_ambiguous_anchor_fail(self):
        edit=self.document_edit('structure'); original=self.root/'STRUCTURE.md'
        original.rename(self.root/'source.md'); original.symlink_to(self.root/'source.md')
        p=self.run_cli('structure','update','--changes',edit,'--exclusive','--json')
        self.assertEqual(p.returncode,2)
        original.unlink(); (self.root/'source.md').rename(original)
        original.write_text('Repeated\nRepeated\n')
        p=self.run_cli('structure','update','--changes',self.document_edit('structure'),'--exclusive','--json')
        self.assertEqual(p.returncode,2)
        self.assertEqual(original.read_text(),'Repeated\nRepeated\n')

    def test_public_help_and_plan_compatibility(self):
        helptext=self.run_cli('--help').stdout
        self.assertIn('brain',helptext); self.assertIn('plan',helptext)
        self.assertNotIn('export-patch',helptext); self.assertNotIn('upgrade',helptext)
        p=self.run_cli('plan','init','--json'); self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['plan'],self.plan('init'))

    def test_detached_head_is_explicit(self):
        self.env.git(self.root,'checkout','--detach','-q')
        d=json.loads(self.run_cli('inspect','--json').stdout)
        self.assertIsNone(d['git']['branch'])
        self.assertTrue(d['git']['head'])
    def test_subdirectory_resolves_project(self):
        d=json.loads(self.run_cli('inspect',str(self.root/'src'),'--json').stdout)
        self.assertEqual(Path(d['report']['root']),self.root.resolve())
    def test_version(self):
        p=self.run_cli('--version'); self.assertEqual(p.returncode,0)
        self.assertEqual(p.stdout.strip(),__version__)
    def test_help(self):
        for args in (('--help',),('help',)):
            p=self.run_cli(*args); self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('inspect',p.stdout)
    def test_check_matches_legacy(self):
        p=self.run_cli('check',str(self.root),'--json'); self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads(p.stdout); self.assertEqual(data['schema_version'],1)
        _,old=self.env.check(self.root); self.assertEqual(data['report'],old)
    def test_inspect_is_read_only_and_explicit_about_remote(self):
        before={str(p.relative_to(self.root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        p=self.run_cli('inspect','--json'); self.assertEqual(p.returncode,0,p.stderr)
        d=json.loads(p.stdout); self.assertEqual(d['remote']['status'],'not_checked')
        self.assertEqual(d['providers']['status'],'not_checked'); self.assertTrue(d['git']['available'])
        self.assertIn('branch',d['git']); self.assertIn('snapshot',d)
        self.assertEqual(before,{str(p.relative_to(self.root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()})
    def test_invalid_target(self):
        p=self.run_cli('check',str(self.root/'missing'),'--json'); self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)['status'],'error')
    def test_file_target_rejected(self):
        self.assertEqual(self.run_cli('inspect',str(self.root/'README.md'),'--json').returncode,2)
    def test_unknown_and_unimplemented_commands_do_not_write(self):
        for command in ('inspect-and-update','diagram','garbage'):
            p=self.run_cli(command); self.assertEqual(p.returncode,2)
    def plan(self, command, *args):
        p=self.run_cli(command,'--plan','--json',*args)
        self.assertEqual(p.returncode,0,p.stderr)
        return json.loads(p.stdout)['plan']
    def test_lifecycle_requires_plan_flag(self):
        for name in ('init','update','upgrade'):
            self.assertEqual(self.run_cli(name).returncode,2)
    def test_init_nested_target_does_not_select_parent_project(self):
        nested=self.root/'new-project'; nested.mkdir()
        p=self.run_cli('init',str(nested),'--plan','--json')
        d=json.loads(p.stdout); self.assertEqual(Path(d['report']['root']),nested.resolve())
        self.assertEqual(d['plan']['status'],'needs_input')
    def test_plan_rejects_symlink_before_reading_target(self):
        (self.root/'TECHSTACK.md').unlink()
        (self.root/'TECHSTACK.md').symlink_to(Path(self.tmp.name)/'absent-private-file')
        self.assertEqual(self.run_cli('init','--plan','--json').returncode,2)
    def test_noop_upgrade(self):
        self.assertEqual(self.plan('upgrade')['status'],'no_change')
    def test_update_requires_evidence_and_rejects_duplicates(self):
        text=(self.root/'TECHSTACK.md').read_text()
        path=Path(self.changes_file(text,text+'extra'))
        data=json.loads(path.read_text()); data['changes'][0]['evidence']=[]
        path.write_text(json.dumps(data))
        self.assertEqual(self.run_cli('update','--plan','--json','--changes',str(path)).returncode,2)
        data['changes'][0]['evidence']=['reference']; data['changes']*=2; path.write_text(json.dumps(data))
        self.assertEqual(self.run_cli('update','--plan','--json','--changes',str(path)).returncode,2)
    def test_init_existing_is_noop(self):
        self.assertEqual(self.plan('init')['status'],'no_change')
    def test_init_missing_owner_intent_not_invented(self):
        (self.root/'VISION.md').unlink(); (self.root/'BRAIN.md').unlink()
        p=self.plan('init'); self.assertEqual(p['status'],'needs_input')
        self.assertTrue(p['gaps']); self.assertFalse((self.root/'VISION.md').exists())
    def test_update_without_changes_does_not_claim_freshness(self):
        p=self.plan('update'); self.assertEqual(p['status'],'needs_input')
        self.assertFalse(p['changes'])
    def test_upgrade_legacy_preserves_both(self):
        (self.root/'TECH.md').write_text('Unique old facts')
        before=(self.root/'TECHSTACK.md').read_bytes()
        p=self.plan('upgrade'); self.assertEqual(p['status'],'needs_input')
        self.assertEqual(p['changes'][0]['action'],'reconcile')
        self.assertEqual(before,(self.root/'TECHSTACK.md').read_bytes())
        self.assertEqual((self.root/'TECH.md').read_text(),'Unique old facts')
    def test_upgrade_old_name_only(self):
        (self.root/'TECHSTACK.md').rename(self.root/'TECH.md')
        p=self.plan('upgrade'); self.assertEqual(p['changes'][0]['action'],'migration_review')
        self.assertFalse((self.root/'TECHSTACK.md').exists())
    def test_repeated_plans_leave_bytes_and_dates(self):
        before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.glob('*.md')}
        for command in ('init','update','upgrade'):
            self.assertEqual(self.plan(command),self.plan(command))
        self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.glob('*.md')})
    def changes_file(self, before,after,evidence=None,file='TECHSTACK.md'):
        path=Path(self.tmp.name)/'changes.json'
        path.write_text(json.dumps({'changes':[{'file':file,'before':before,'after':after,'evidence':evidence or ['owner supplied reference']}]}))
        return str(path)
    def test_update_exact_patch_and_noop(self):
        text=(self.root/'TECHSTACK.md').read_text()
        for after,status in ((text,'no_change'),(text+'\nNew fact.\n','planned')):
            p=self.plan('update','--changes',self.changes_file(text,after))
            self.assertEqual(p['status'],status)
            self.assertEqual((self.root/'TECHSTACK.md').read_text(),text)
    def test_update_conflict_and_owner_gap(self):
        p=self.plan('update','--changes',self.changes_file('missing anchor','new'))
        self.assertEqual(p['status'],'conflict')
        text=(self.root/'VISION.md').read_text()
        p=self.plan('update','--changes',self.changes_file(text,text+'\nChanged intent',file='VISION.md'))
        self.assertEqual(p['status'],'needs_input'); self.assertTrue(p['gaps'])
    def test_update_rejects_path_escape(self):
        p=self.run_cli('update','--plan','--json','--changes',self.changes_file('a','b',file='../outside.md'))
        self.assertEqual(p.returncode,2)
    def originals(self):
        return {p.name:(p.read_bytes(),p.stat().st_mtime_ns,p.stat().st_mode) for p in self.root.glob('*.md')}
    def test_apply_and_yes_cannot_authorize_writes(self):
        before=self.originals()
        for args in (('apply','--yes'),('update','--yes'),('update','--plan','--yes'),('upgrade','--apply')):
            self.assertEqual(self.run_cli(*args).returncode,2)
        self.assertEqual(before,self.originals())
    def test_approval_data_is_rejected_not_executed(self):
        text=(self.root/'TECHSTACK.md').read_text()
        path=Path(self.changes_file(text,text+'Changed'))
        data=json.loads(path.read_text()); data['changes'][0]['approved']=True
        path.write_text(json.dumps(data)); before=self.originals()
        self.assertEqual(self.run_cli('update','--plan','--json','--changes',str(path)).returncode,2)
        self.assertEqual(before,self.originals())
    def test_late_batch_error_never_partially_applies(self):
        text=(self.root/'TECHSTACK.md').read_text()
        path=Path(self.changes_file(text,text+'Changed'))
        data=json.loads(path.read_text()); data['changes'].append({'file':'../outside.md'})
        path.write_text(json.dumps(data)); before=self.originals()
        self.assertEqual(self.run_cli('update','--plan','--json','--changes',str(path)).returncode,2)
        self.assertEqual(before,self.originals())
    def test_mixed_conflict_preserves_valid_and_invalid_targets(self):
        text=(self.root/'TECHSTACK.md').read_text()
        path=Path(self.changes_file(text,text+'Changed'))
        data=json.loads(path.read_text()); data['changes'].append({'file':'README.md','before':'absent anchor','after':'new','evidence':['ref']})
        path.write_text(json.dumps(data)); before=self.originals()
        d=json.loads(self.run_cli('update','--plan','--json','--changes',str(path)).stdout)
        self.assertEqual(d['plan']['status'],'conflict'); self.assertEqual(before,self.originals())
    def test_replanning_after_concurrent_edit_rejects_stale_anchor(self):
        target=self.root/'TECHSTACK.md'; original=target.read_text()
        path=self.changes_file(original,original+'planned')
        self.plan('update','--changes',path)
        target.write_text('A different editor replaced this document.\n')
        before=self.originals()
        self.assertEqual(self.plan('update','--changes',path)['status'],'conflict')
        self.assertEqual(before,self.originals())
    def test_noop_preserves_readonly_file_permissions(self):
        target=self.root/'TECHSTACK.md'; text=target.read_text(); target.chmod(0o444)
        try:
            before=self.originals()
            self.assertEqual(self.plan('update','--changes',self.changes_file(text,text))['status'],'no_change')
            self.assertEqual(before,self.originals())
        finally: target.chmod(0o644)
    def test_read_check_replace_is_not_compare_and_swap(self):
        # Counterexample in disposable fixtures only: a fresh check followed
        # by atomic replacement still loses a non-cooperating editor's write.
        target=Path(self.tmp.name)/'race-proof.txt'
        staged=Path(self.tmp.name)/'race-proof-staged.txt'
        target.write_text('base'); staged.write_text('our proposed change')
        self.assertEqual(target.read_text(),'base')
        target.write_text('concurrent editor change')  # after the final check
        os.replace(staged,target)
        self.assertEqual(target.read_text(),'our proposed change')
        self.assertNotEqual(target.read_text(),'concurrent editor change')
    def saved_plan(self, after=None):
        target=self.root/'TECHSTACK.md'
        with target.open(newline='') as f: text=f.read()
        changes=self.changes_file(text,after if after is not None else text+'\nNew fact.\n')
        result=self.run_cli('update','--plan','--json','--changes',changes)
        path=Path(self.tmp.name)/'plan.json'; path.write_text(result.stdout)
        return path
    def export(self,path):
        return self.run_cli('export-patch','--plan-file',str(path))
    def test_export_valid_patch_preserves_originals(self):
        plan=self.saved_plan(); before=self.originals(); p=self.export(plan)
        self.assertEqual(p.returncode,0,p.stderr); self.assertIn('--- a/TECHSTACK.md',p.stdout)
        self.assertEqual(before,self.originals())
        patch=Path(self.tmp.name)/'review.patch'; patch.write_text(p.stdout)
        self.env.git(self.root,'apply','--check',str(patch))
    def test_export_stale_source_rejected_without_partial_patch(self):
        plan=self.saved_plan(); (self.root/'TECHSTACK.md').write_text('Other editor')
        before=self.originals(); p=self.export(plan)
        self.assertEqual(p.returncode,2); self.assertEqual(p.stdout,''); self.assertEqual(before,self.originals())
    def test_export_noop_is_empty(self):
        plan=self.saved_plan((self.root/'TECHSTACK.md').read_text())
        p=self.export(plan); self.assertEqual(p.returncode,0,p.stderr); self.assertEqual(p.stdout,'')
    def test_export_rejects_wrong_root_traversal_hash_and_symlink(self):
        for change in ('root','path','hash','symlink'):
            plan=self.saved_plan(); data=json.loads(plan.read_text())
            if change=='root': data['report']['root']=self.tmp.name
            if change=='path': data['plan']['changes'][0]['file']='../outside.md'
            if change=='hash': data['plan']['changes'][0]['proposed_sha256']='0'*64
            if change=='symlink':
                target=self.root/'TECHSTACK.md'; saved=target.read_bytes(); target.unlink()
                target.symlink_to(Path(self.tmp.name)/'outside')
            plan.write_text(json.dumps(data)); p=self.export(plan)
            self.assertEqual(p.returncode,2,change); self.assertEqual(p.stdout,'',change)
            if change=='symlink': target.unlink(); target.write_bytes(saved)
    def test_export_final_newline_and_unicode(self):
        target=self.root/'TECHSTACK.md'; target.write_text('Old café')
        plan=self.saved_plan('New café'); p=self.export(plan)
        self.assertEqual(p.returncode,0,p.stderr); self.assertIn('No newline at end of file',p.stdout)
        patch=Path(self.tmp.name)/'review.patch'; patch.write_text(p.stdout)
        self.env.git(self.root,'apply',str(patch))  # disposable fixture only
        self.assertEqual(target.read_text(),'New café')
    def test_export_crlf_preservation(self):
        target=self.root/'TECHSTACK.md'; target.write_bytes(b'Old\r\n')
        plan=self.saved_plan('New\r\n')
        data=json.loads(plan.read_text())
        import hashlib
        self.assertEqual(data['plan']['changes'][0]['source_sha256'],hashlib.sha256(b'Old\r\n').hexdigest())
        p=self.run_cli('export-patch','--plan-file',str(plan),binary=True)
        self.assertEqual(p.returncode,0,p.stderr)
        patch=Path(self.tmp.name)/'crlf.patch'; patch.write_bytes(p.stdout)
        self.env.git(self.root,'apply',str(patch))
        self.assertEqual(target.read_bytes(),b'New\r\n')
    def test_export_late_invalid_entry_returns_no_partial_output(self):
        plan=self.saved_plan(); data=json.loads(plan.read_text())
        data['plan']['changes'].append({'file':'README.md'})
        plan.write_text(json.dumps(data)); before=self.originals(); p=self.export(plan)
        self.assertEqual(p.returncode,2); self.assertEqual(p.stdout,''); self.assertEqual(before,self.originals())
    def test_export_rejects_approval_fields(self):
        plan=self.saved_plan(); data=json.loads(plan.read_text())
        data['plan']['changes'][0]['approved']=True
        plan.write_text(json.dumps(data)); p=self.export(plan)
        self.assertEqual(p.returncode,2); self.assertEqual(p.stdout,'')
    def test_export_rejects_symlink_plan(self):
        plan=self.saved_plan(); link=Path(self.tmp.name)/'plan-link.json'; link.symlink_to(plan)
        self.assertEqual(self.export(link).returncode,2)
    def test_unicode_separator_patch_is_valid(self):
        target=self.root/'TECHSTACK.md'; target.write_text('old\u2028inside\n')
        plan=self.saved_plan('new\u2028inside\n'); p=self.export(plan)
        self.assertEqual(p.returncode,0,p.stderr)
        patch=Path(self.tmp.name)/'separator.patch'; patch.write_text(p.stdout)
        self.env.git(self.root,'apply',str(patch))
        self.assertEqual(target.read_text(),'new\u2028inside\n')
    def test_inspect_does_not_run_git_helpers(self):
        marker=Path(self.tmp.name)/'helper-ran'
        helper=Path(self.tmp.name)/'helper.sh'
        helper.write_text('#!/bin/sh\nprintf ran >> "'+str(marker)+'"\ncat\n'); helper.chmod(0o755)
        (self.root/'.gitattributes').write_text('*.md filter=spy\n')
        self.env.git(self.root,'config','filter.spy.clean',str(helper))
        self.env.git(self.root,'config','filter.spy.process','')
        self.env.git(self.root,'config','core.fsmonitor',str(helper))
        with (self.root/'PROGRESS.md').open('a') as f: f.write('\nChanged bytes\n')
        p=self.run_cli('inspect','--json'); self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(marker.exists(),'Read-only inspection executed a configured helper')
    def test_inspect_three_part_progress_snapshot(self):
        from test_progress_layout import TEXT
        (self.root/'PROGRESS.md').write_text(TEXT.replace('2026-11-12','2026-10-31'))
        p=self.run_cli('inspect','--json'); data=json.loads(p.stdout)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('New export',data['snapshot'])
        self.assertNotIn('Pilot delivery',data['snapshot'])
        self.assertNotIn('wider rollout',data['snapshot'])
    def test_invalid_flag(self): self.assertEqual(self.run_cli('check','--typo').returncode,2)
    def test_failed_check_exit(self):
        (self.root/'BRAIN.md').unlink(); p=self.run_cli('check','--json')
        self.assertEqual(p.returncode,1); self.assertTrue(json.loads(p.stdout)['report']['errors'])
    def test_non_git_project(self):
        # Construct a non-Git project directly. Deleting a freshly committed
        # repository can race Git's background maintenance on older Python.
        root = healthy_project(self.env, Path(self.tmp.name) / 'non-git-project', git=False)
        p=self.run_cli('inspect','--json',cwd=root)
        d=json.loads(p.stdout); self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(d['git']['available'])
    def test_no_records(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.run_cli('check',d,'--json'); self.assertEqual(p.returncode,1)
            self.assertEqual(json.loads(p.stdout)['report']['records'],[])
    def test_legacy_progress(self):
        (self.root/'PROGRESS.md').rename(self.root/'STATUS.md'); p=self.run_cli('inspect','--json')
        d=json.loads(p.stdout); self.assertEqual(d['report']['info']['progress_file'],'STATUS.md')
    def test_dirty_state_is_local(self):
        (self.root/'untracked.txt').write_text('test')
        d=json.loads(self.run_cli('inspect','--json').stdout)
        self.assertIn('untracked.txt',d['git']['status_porcelain'])
if __name__=='__main__': unittest.main()
