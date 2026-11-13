"""Latest-day/history/roadmap presentation and preservation regressions."""
import unittest
import horsemen
TEXT='''# Progress

Updated: 2026-11-12 · Stage: live · Health: On track
Next action: Mai reviews the next release.

## Latest day

<details open>
<summary>Latest day · 2026-11-12</summary>

## Shipped

- **New export** (2026-11-12): People can send a report.

## Up next

- **Next view**: Make reports easier to scan.

## Needs decision

- **Timing**: Mai decides when to start.

| Item | Evidence |
| --- | --- |
| New export | [Published release](https://example.org/release) |

</details>

## Historical ships

<details>
<summary>Historical ships</summary>

| Date | Shipped | Proof |
| --- | --- | --- |
| 2026-10-10 | Pilot delivery | [Sent report](https://example.org/report) |

</details>

## Upcoming roadmap

<details>
<summary>Upcoming roadmap</summary>

- Later: a wider rollout, not committed yet.

</details>
'''
class Layout(unittest.TestCase):
    def issues(self,text):
        issues=[]; horsemen.check_progress(text,lambda level,code,file,message:issues.append((level,code)))
        return issues
    def test_latest_snapshot_excludes_history_and_roadmap(self):
        snapshot,_=horsemen.split_progress(TEXT)
        self.assertIn('New export',snapshot)
        self.assertNotIn('Pilot delivery',snapshot)
        self.assertNotIn('wider rollout',snapshot)
    def test_toggle_statuses_and_historical_ships_are_recognized(self):
        self.assertEqual(horsemen.shipped_items(TEXT),{'New export','Pilot delivery'})
        self.assertNotIn(('warning','progress-no-state-table'),self.issues(TEXT))
    def test_history_requires_proof(self):
        text=TEXT.replace('[Sent report](https://example.org/report)','')
        self.assertIn(('error','progress-history-no-evidence'),self.issues(text))
    def test_latest_requires_evidence(self):
        self.assertIn(('error','progress-shipped-no-evidence'),self.issues(TEXT.replace('[Published release](https://example.org/release)','')))
    def test_no_html_fallback_remains_readable_and_parseable(self):
        import re
        plain=re.sub(r'<[^>]+>','',TEXT)
        self.assertEqual(horsemen.shipped_items(plain),{'New export','Pilot delivery'})
    def test_moving_ship_to_history_does_not_create_new_ship(self):
        moved=TEXT.replace('- **New export** (2026-11-12): People can send a report.','- Nothing shipped on this update day.').replace('| 2026-10-10 | Pilot delivery', '| 2026-11-12 | New export | [Release](https://example.org/release) |\n| 2026-10-10 | Pilot delivery')
        self.assertEqual(horsemen.shipped_items(TEXT),horsemen.shipped_items(moved))
    def test_templates_keep_owner_intent_and_nonprofit_scope(self):
        from pathlib import Path
        refs=Path(__file__).resolve().parents[1]/'references'
        text=(refs/'templates.md').read_text()
        for phrase in ('nonprofit','Never invent','## What it does','## Historical ships','## Upcoming roadmap'):
            self.assertIn(phrase,text)
    def test_legacy_layout_still_works(self):
        text='## Shipped\n\n- **Old release** (2026-10-10): Delivered.\n\n## 2026-10-10 · Release\n'
        self.assertEqual(horsemen.shipped_items(text),{'Old release'})
    def test_history_not_counted_as_latest_overflow(self):
        row='| 2026-10-10 | Pilot delivery | [Sent report](https://example.org/report) |'
        text=TEXT.replace(row,'\n'.join(row.replace('Pilot delivery',f'Delivery {i}') for i in range(40)))
        self.assertNotIn(('warning','snapshot-too-long'),self.issues(text))
        self.assertNotIn(('warning','shipped-list-long'),self.issues(text))
if __name__=='__main__': unittest.main()
