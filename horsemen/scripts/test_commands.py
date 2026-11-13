"""Agent command contract checks; these do not execute an autonomous host."""
import unittest
import io
from contextlib import redirect_stdout
from pathlib import Path
import horsemen
ROOT=Path(__file__).resolve().parents[1]
class Commands(unittest.TestCase):
    def commands(self): return (ROOT/'references/commands.md').read_text()
    def test_help_routes_before_private_project_reads(self):
        self.assertIn('Route `help` and unknown commands before project discovery',self.commands())
        self.assertIn('`check` only reads local records',self.commands())
    def test_all_commands_have_routes(self):
        for name in ('init','update','upgrade','inspect','inspect-and-update','check','diagram','help'):
            self.assertIn('### '+name, self.commands())
    def test_agent_not_fake_cli(self):
        self.assertIn('agent commands, not shell commands',self.commands())
        for name in ('init','update','upgrade','inspect','diagram','help'):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(horsemen.main([name]),2)
    def test_read_only_inspect_overrides_maintenance(self):
        s=(ROOT/'references/inspect-and-proceed.md').read_text()
        self.assertIn('read-only',s)
        self.assertIn('Do not write records or provider originals',s)
        self.assertNotIn('Correct maintainable facts',s)
        self.assertNotIn('Reconcile authorized changes',s)
    def test_compound_mode_preserves_legacy_maintenance(self):
        s=self.commands()
        self.assertIn('### inspect-and-update',s)
        self.assertIn('`inspect and update` and legacy `inspect and proceed`',s)
        section=s.split('### inspect-and-update')[1].split('### check')[0]
        for phrase in ('record maintenance', 'existing permissions', 'No code changes', 'proposed priorities'):
            self.assertIn(phrase,section)
        self.assertIn('plain inspect and check', horsemen.completion_reminder([])['reason'])
    def test_hook_respects_read_only_commands(self):
        self.assertIn('read-only commands',horsemen.completion_reminder([])['reason'])
    def test_preservation_and_uncertainty(self):
        s=self.commands()
        for phrase in ('unchanged dates','both files exist','VISION','Unknown commands','uncertain write','no new permission'):
            self.assertIn(phrase,s)
    def test_visual_reuse_and_no_publish(self):
        s=self.commands()
        for phrase in ('show-me-bro','Mermaid','Excalidraw','existing format','Do not publish','pele.run','read-back'):
            self.assertIn(phrase,s)
    def test_techstack_versions_and_connections(self):
        s=(ROOT/'references/templates.md').read_text().split('### TECHSTACK.md')[1]
        for phrase in ('Tool and version','Runtime connections','Development and release','How it helps'):
            self.assertIn(phrase,s)
if __name__=='__main__': unittest.main()
