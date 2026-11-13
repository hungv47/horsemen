#!/usr/bin/env python3
"""Scenario validation for the horsemen script and hooks.

Builds throwaway projects in a temp folder, drives `horsemen.py` the same way
Claude Code and Codex do (hook JSON on stdin), and writes a JSON receipt.
Failure-mode IDs refer to references/hooks.md.

usage: e2e.py [--output FILE] [--keep]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "horsemen.py"
TODAY = "2026-11-01"

VISION = """# Vision

Owner: Hung · Confirmed: 2026-10-20

Every solo consultant leaves a client meeting with the summary already sent.

## Why we exist

Consultants spend an hour per meeting rewriting notes. Most send the summary a day late, and clients notice.

## The world we are building

Two thousand consultants send every summary within ten minutes. Clients expect it.

## Who we build for

Independent consultants who bill by the hour. Not for teams.

## What we believe

- The meeting is the product; the summary is how the client remembers it.

## How we get there

- Now: 20 paying consultants by 2027-03-31.
- Later: the default way consultants close a meeting.

## What we will never become

- Team workspaces.

## Open questions

- Pricing model. Hung decides.
"""

LEGACY_VISION = """# Vision

Owner: Hung · Confirmed: 2026-10-20

Tiny Notes becomes how solo consultants close every client meeting.

## Purpose

Consultants spend an hour per meeting rewriting notes.

## The picture when it works

Two thousand consultants send every summary within ten minutes.

## Who it serves

Independent consultants who bill by the hour.

## How it creates value

Five hours saved a week.

## How it reaches people

Consultant communities.

## How it runs

One owner, a monthly subscription.

## How it plays out

- Now: 20 paying consultants.

## What it will never become

- Team workspaces.
"""

BRAIN = """# Brain

Brain: Google Drive · Access verified: 2026-10-20

Visibility: private

## Providers

| Provider | Root | Access route | Account and scope | Verified |
| --- | --- | --- | --- | --- |
| Google Drive | drive:Tiny Notes | Drive connector | Owner account | 2026-10-20 |

## What lives in the brain

| Knowledge | Provider › location | Why it is not in the repo |
| --- | --- | --- |
| Interviews | Drive › Research | Private notes |
"""

ROW_EDITOR = "## In progress\n\n- **Note editor** (started 2026-10-28): Consultants can write notes in the app.\n\n"
ROW_EXPORT = "## Up next\n\n- **Export to PDF**: Consultants send a summary as a PDF.\n\n"
EV_EDITOR = "| Note editor | branch editor |\n"


def progress(rows=ROW_EDITOR + ROW_EXPORT, evidence=EV_EDITOR, extra=""):
    return f"""# Progress

Updated: 2026-10-30 · Stage: building · Health: On track

The editor works for early testers. Export is next.

Next action: Hung finishes the editor.

{rows}## Roadmap

- Idea: calendar import.

<details>
<summary>Technical details</summary>

| Item | Evidence |
| --- | --- |
{evidence}{extra}
</details>

## 2026-10-30 · Editor in testers' hands

Testers can now write notes in the app.

<details>
<summary>Technical details</summary>

- Started the note editor on branch editor.

</details>
"""


PROGRESS = progress()

TABLE_PROGRESS = """# Progress

Updated: 2026-10-30 · Stage: building · Health: On track

The editor works for early testers. Export is next.

Next action: Hung finishes the editor.

## Where things stand

| Status | Item | What it means | Date |
| --- | --- | --- | --- |
| In progress | Note editor | Consultants can write notes in the app | 2026-10-28 |
| Up next | Export to PDF | Consultants send a summary as a PDF | - |

<details>
<summary>Technical details</summary>

| Item | Evidence |
| --- | --- |
| Note editor | branch editor |

</details>
"""


def shipped_section(*items):
    return "## Shipped\n\n" + "".join(f"- **{name}** ({when}): {text}\n" for name, when, text in items) + "\n"

LEGACY_PROGRESS = """# Progress

Updated: 2026-10-30 · Stage: building · Health: On track

The editor works locally. Export is next.

Next action: Hung finishes the editor.

## Current state

| State | Item | Evidence | Date |
| --- | --- | --- | --- |
| Shipped | Landing page | live at example.invalid | 2026-10-29 |
| Built, not shipped | Note editor | branch editor | 2026-10-28 |
| Next | Export to PDF | - | - |

## Later

- Calendar import.

## 2026-10-30

- Started the note editor.
"""

STRUCTURE = """# Structure

A small web app. Research lives in Google Drive.

## At a glance

```text
src/      application code
docs/     decisions
```

## Repository

| Path | Responsibility |
| --- | --- |
| `src/app/` | UI |
| `src/api/` | HTTP handlers |
| `docs/decisions.md` | Decisions |

## Brain

### Google Drive: drive:Tiny Notes

Open with: Drive connector.

```text
Tiny Notes/
  Research/       interview notes
Sales/            pitch decks
```

## Other documents

- README.md, CHANGELOG.md, TECHSTACK.md, AGENTS.md, CLAUDE.md
"""

README = """# Tiny Notes

Tiny Notes turns a solo consultant's meeting notes into a client-ready summary in minutes.

## Install

Run `bun install`, then `bun dev`.

## Project records

- [VISION.md](VISION.md)
- [BRAIN.md](BRAIN.md)
- [PROGRESS.md](PROGRESS.md)
- [STRUCTURE.md](STRUCTURE.md)
"""

AGENTS = """# Project context

- [VISION.md](VISION.md)
- [BRAIN.md](BRAIN.md)
- [PROGRESS.md](PROGRESS.md)
- [STRUCTURE.md](STRUCTURE.md)
"""

CHANGELOG = """# Changelog

## 2026-10-01

- Shipped the landing page.
"""

LEGACY_STATUS = """# Status navigation

Working authority: this file must preserve or retrieve the substantive role content. The intended provider below is a target binding, not a completed cutover.

Intended provider (cutover not verified): **Linear**.

### Status

Updated 2026-10-23. Things happened.
"""

results = []


class Env:
    def __init__(self, base):
        self.base = Path(base).resolve()
        self.state = self.base / "state"
        self.state.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ, HORSEMEN_STATE_DIR=str(self.state), HORSEMEN_TODAY=TODAY,
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid",
                        GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")

    def run(self, args, stdin="", cwd=None):
        started = time.monotonic()
        proc = subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True,
                              text=True, cwd=cwd or self.base, env=self.env, timeout=30)
        return proc, time.monotonic() - started

    def hook(self, event, cwd, session="s1", **extra):
        payload = {"session_id": session, "cwd": str(cwd), "hook_event_name": event, **extra}
        proc, elapsed = self.run(["hook", "session-start" if event == "SessionStart" else "stop"],
                                 json.dumps(payload), cwd=cwd)
        out = proc.stdout.strip()
        return proc.returncode, (json.loads(out) if out else None), elapsed, proc

    def check(self, root):
        proc, _ = self.run(["check", str(root), "--json"], cwd=root)
        return proc.returncode, json.loads(proc.stdout)

    def git(self, root, *args):
        subprocess.run(["git", *args], cwd=root, env=self.env, check=True, capture_output=True, text=True)


def record(name, ok, detail=""):
    results.append({"scenario": name, "passed": bool(ok), "detail": detail})


def codes(report, kind):
    return {item["code"] for item in report[kind]}


def context(out):
    return (out or {}).get("hookSpecificOutput", {}).get("additionalContext", "")


def review_requested(out):
    reason = (out or {}).get("reason", "")
    return (out or {}).get("decision") == "block" and all(name in reason for name in ("VISION", "BRAIN", "PROGRESS", "STRUCTURE"))


def write(root, files):
    for name, text in files.items():
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def healthy_project(env, root, git=True):
    root.mkdir(parents=True)
    write(root, {"VISION.md": VISION, "BRAIN.md": BRAIN, "PROGRESS.md": PROGRESS, "STRUCTURE.md": STRUCTURE,
                 "README.md": README, "TECHSTACK.md": "# Technology\n\nBun: local setup; version in package manifest.\n", "AGENTS.md": AGENTS, "CLAUDE.md": "@AGENTS.md\n", "CHANGELOG.md": CHANGELOG,
                 "src/app/main.js": "x\n", "src/api/routes.js": "x\n", "docs/decisions.md": "# Decisions\n"})
    if git:
        env.git(root, "init", "-q", "-b", "main")
        # These repositories are disposable. Background housekeeping would
        # race byte-for-byte inspection assertions and fixture cleanup.
        env.git(root, "config", "maintenance.auto", "false")
        env.git(root, "config", "gc.auto", "0")
        env.git(root, "add", "-A")
        env.git(root, "commit", "-q", "-m", "init", "--date", "2026-10-01T00:00:00")
    return root


def scenario_noise(env):
    home = env.base / "home"
    (home / "workspace").mkdir(parents=True)
    write(home, {"workspace/AGENTS.md": "# Rules\n"})
    code, out, elapsed, _ = env.hook("SessionStart", home)
    record("F1 non-project folder prints nothing", code == 0 and out is None, f"{elapsed:.2f}s")
    code, out, _, _ = env.hook("SessionStart", home / "workspace")
    record("F2 workspace root with only AGENTS.md is not a project", code == 0 and out is None)
    proc, _ = env.run(["hook", "session-start"], "not json", cwd=home)
    record("F11 malformed stdin exits 0 silently", proc.returncode == 0 and not proc.stdout.strip(), proc.stderr[-200:])
    proc, _ = env.run(["hook", "stop"], "", cwd=home)
    record("S17/F11 empty stdin on stop exits 0 silently", proc.returncode == 0 and not proc.stdout.strip())


def scenario_initialization(env):
    root = env.base / "init"
    root.mkdir()
    env.git(root, "init", "-q", "-b", "main")
    code, out, _, _ = env.hook("SessionStart", root)
    text = context(out)
    record("F8 git repo without records gets a one-line offer", code == 0 and "horsemen" in text and text.count("\n") <= 1, text)
    code, report = env.check(root)
    record("C1 check reports all four records missing", code == 1 and "missing-record" in codes(report, "errors"))
    template = (Path(__file__).resolve().parents[1] / "references" / "templates.md").read_text()
    vision_block = template.split("```markdown\n# Vision", 1)[1].split("\n```", 1)[0]
    write(root, {"VISION.md": "# Vision" + vision_block, "BRAIN.md": BRAIN, "PROGRESS.md": PROGRESS,
                 "STRUCTURE.md": "# Structure\n\nNo code.\n", "README.md": README, "AGENTS.md": AGENTS})
    code, report = env.check(root)
    record("C7 unfilled template prompts are flagged", "placeholder" in codes(report, "warnings"))
    write(root, {"VISION.md": VISION, "docs/decisions.md": "# Decisions\n"})
    code, report = env.check(root)
    record("init: filled records pass check", code == 0, json.dumps(report["errors"]))


def scenario_adoption(env):
    root = env.base / "legacy"
    healthy_project(env, root)
    (root / "PROGRESS.md").unlink()
    write(root, {"STATUS.md": LEGACY_STATUS, "AGENTS.md": AGENTS.replace("PROGRESS", "STATUS")})
    env.git(root, "add", "-A")
    env.git(root, "commit", "-q", "-m", "legacy")
    code, out, _, _ = env.hook("SessionStart", root)
    text = context(out)
    record("F5 legacy STATUS.md flagged, body not injected", "STATUS.md" in text and "Working authority" not in text, text[:400])
    code, report = env.check(root)
    warns = codes(report, "warnings")
    record("C2 legacy name and binding preamble are warnings", {"legacy-status", "legacy-preamble"} <= warns, str(warns))
    write(root, {"PROGRESS.md": PROGRESS})
    code, report = env.check(root)
    record("F6/C2 STATUS.md plus PROGRESS.md is an error", "two-progress-owners" in codes(report, "errors"))
    write(root, {"STATUS.md": "# Status\n\nMoved to [PROGRESS.md](PROGRESS.md). README links here and is release-locked.\n"})
    code, report = env.check(root)
    record("C2b a pure pointer STATUS.md beside PROGRESS.md is a warning, not a second owner",
           "two-progress-owners" not in codes(report, "errors") and "legacy-pointer" in codes(report, "warnings"), json.dumps(report["errors"]))
    write(root, {"STATUS.md": LEGACY_STATUS})
    (root / "PROGRESS.md").unlink()
    write(root, {"STRUCTURE.md": STRUCTURE + "\n| Path under a job | Contents |\n| --- | --- |\n| `executor/` | app |\n"})
    code, report = env.check(root)
    record("C14 legacy project: contextual STRUCTURE paths are warnings, not errors",
           "structure-missing-path" not in codes(report, "errors") and "structure-missing-path" in codes(report, "warnings"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": PROGRESS, "STRUCTURE.md": STRUCTURE})
    (root / "STATUS.md").unlink()
    write(root, {"AGENTS.md": AGENTS})
    code, report = env.check(root)
    record("adoption: migrated project passes check", code == 0, json.dumps(report["errors"]))


def scenario_shipping(env):
    root = healthy_project(env, env.base / "ship")
    sid = "ship"
    code, out, _, _ = env.hook("SessionStart", root, session=sid, source="startup")
    snapshot = context(out)
    record("orient injects the PROGRESS snapshot, not the log", "Export to PDF" in snapshot and "Started the note editor" not in snapshot, snapshot[:300])
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=False)
    record("T1 no local changes still request a four-record review", review_requested(out), json.dumps(out))
    write(root, {"src/app/export.js": "pdf\n"})
    env.git(root, "add", "-A")
    env.git(root, "commit", "-q", "-m", "export")
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=True)
    record("S1 stop_hook_active never blocks", out is None)
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=False)
    reason = (out or {}).get("reason", "")
    record("S4 work commit without PROGRESS update blocks once", (out or {}).get("decision") == "block" and "PROGRESS" in reason, reason)
    record("S16 reason is short", 0 < len(reason) < 1200, str(len(reason)))
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=False)
    record("S10 same drift detail does not repeat; task review remains", review_requested(out) and "work commit" not in out.get("reason", ""))
    ship_row = shipped_section(("PDF export", "2026-11-01", "Consultants send summaries as PDF."))
    shipped = progress(ship_row + ROW_EXPORT, "| PDF export | v0.2.0 deployed, https://example.invalid |\n")
    shipped = shipped.replace("Updated: 2026-10-30", "Updated: 2026-11-01")
    write(root, {"PROGRESS.md": shipped})
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=False)
    reason = (out or {}).get("reason", "")
    record("S7 new Shipped row without CHANGELOG reminds", "CHANGELOG" in reason and "PROGRESS.md:" not in reason, reason)
    write(root, {"CHANGELOG.md": CHANGELOG.replace("# Changelog\n", "# Changelog\n\n## 0.2.0 - 2026-11-01\n\n- PDF export.\n")})
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=False)
    record("shipping: updated records still get the task review, without a stale changelog alert",
           review_requested(out) and "Changelog:" not in out.get("reason", ""), json.dumps(out))
    bad = shipped.replace("v0.2.0 deployed, https://example.invalid", " ")
    write(root, {"PROGRESS.md": bad})
    code, out, _, _ = env.hook("Stop", root, session=sid, stop_hook_active=False)
    reason = (out or {}).get("reason", "")
    record("S8 lint errors in an edited record are reported", "evidence" in reason.lower() and "PDF export" in reason, reason)
    code, report = env.check(root)
    record("C3 Shipped bullet without evidence is an error", "progress-shipped-no-evidence" in codes(report, "errors"))
    write(root, {"PROGRESS.md": TABLE_PROGRESS.replace("| Up next |", "| Maybe |")})
    code, report = env.check(root)
    record("C3 unknown status in an old status table is still an error", "progress-state-unknown" in codes(report, "errors"))
    write(root, {"PROGRESS.md": shipped.replace("| PDF export | v0.2.0", "| Other item | v0.2.0")})
    code, report = env.check(root)
    record("C3 Shipped item missing from the Technical details table is an error",
           "progress-shipped-no-evidence" in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": shipped.replace("| PDF export | v0.2.0", "| **`pdf Export`** | v0.2.0")})
    code, report = env.check(root)
    record("C3j item names match across case, bold, and backticks", code == 0, json.dumps(report["errors"]))

    lite = healthy_project(env, env.base / "ship-no-changelog")
    (lite / "CHANGELOG.md").unlink()
    env.git(lite, "commit", "-qam", "drop changelog")
    env.hook("SessionStart", lite, session="lite")
    write(lite, {"PROGRESS.md": shipped})
    code, out, _, _ = env.hook("Stop", lite, session="lite", stop_hook_active=False)
    record("S21 no CHANGELOG.md: a new Shipped row asks to create one", "CHANGELOG" in (out or {}).get("reason", ""), json.dumps(out))
    code, report = env.check(lite)
    record("C17 shipped work without CHANGELOG.md is a warning", "changelog-missing" in codes(report, "warnings"), json.dumps(report["warnings"]))

    part = healthy_project(env, env.base / "ship-partly")
    env.hook("SessionStart", part, session="part")
    partly = progress(shipped_section(("Export", "partly shipped 2026-11-01", "PDF is live; Word export is left.")) + ROW_EXPORT,
                      "| Export | v0.3.0 deployed with PDF only |\n")
    write(part, {"PROGRESS.md": partly})
    code, out, _, _ = env.hook("Stop", part, session="part", stop_hook_active=False)
    record("S7b a new Partly shipped row asks for CHANGELOG", "CHANGELOG" in (out or {}).get("reason", ""), json.dumps(out))
    code, report = env.check(part)
    record("Partly shipped is a valid status", "progress-state-unknown" not in codes(report, "errors"), json.dumps(report["errors"]))
    write(part, {"PROGRESS.md": partly.replace("v0.3.0 deployed with PDF only", "-")})
    code, report = env.check(part)
    record("C3k Partly shipped without evidence is an error", "progress-shipped-no-evidence" in codes(report, "errors"), json.dumps(report["errors"]))


def scenario_doc_only_commits(env):
    root = healthy_project(env, env.base / "doconly")
    env.hook("SessionStart", root, session="doc")
    write(root, {"README.md": README + "\nMore.\n"})
    env.git(root, "commit", "-qam", "docs")
    code, out, _, _ = env.hook("Stop", root, session="doc", stop_hook_active=False)
    record("S5 record-only commits request review without a work-commit alert",
           review_requested(out) and "work commit" not in out.get("reason", ""), json.dumps(out))


def scenario_refactor(env):
    root = healthy_project(env, env.base / "refactor")
    env.hook("SessionStart", root, session="ref")
    env.git(root, "mv", "src/api", "src/server")
    env.git(root, "commit", "-qm", "rename api")
    code, out, _, _ = env.hook("Stop", root, session="ref", stop_hook_active=False)
    reason = (out or {}).get("reason", "")
    record("S6 folder rename without STRUCTURE update reminds", "STRUCTURE" in reason and "src/server" in reason, reason)
    code, report = env.check(root)
    missing = [w for w in report["errors"] if w["code"] == "structure-missing-path"]
    record("C5 STRUCTURE path that no longer exists is an error", any("src/api/" in w["message"] for w in missing), json.dumps(missing))
    write(root, {"STRUCTURE.md": STRUCTURE.replace("src/api/", "src/server/")})
    code, report = env.check(root)
    record("refactor: updated STRUCTURE passes check", code == 0, json.dumps(report["errors"]))
    write(root, {"newtool/run.sh": "echo\n"})
    code, report = env.check(root)
    record("C5b unmentioned top-level folder is a warning", any("newtool" in w["message"] for w in report["warnings"] if w["code"] == "structure-unmentioned"))


def scenario_knowledge_migration(env):
    root = healthy_project(env, env.base / "knowledge")
    env.hook("SessionStart", root, session="kn")
    (root / "knowledge").mkdir()
    env.git(root, "mv", "docs", "knowledge/docs")
    env.git(root, "commit", "-qm", "move knowledge")
    code, out, _, _ = env.hook("Stop", root, session="kn", stop_hook_active=False)
    reason = (out or {}).get("reason", "")
    record("knowledge move reminds STRUCTURE", "STRUCTURE" in reason, reason)
    code, report = env.check(root)
    record("knowledge move: stale location is an error", any("docs/decisions.md" in e["message"] for e in report["errors"]), json.dumps(report["errors"]))
    write(root, {"BRAIN.md": BRAIN.replace("Brain: Google Drive", "Brain: Undefined")})
    code, report = env.check(root)
    record("C6 undefined knowledge home is a warning", "brain-home-undefined" in codes(report, "warnings"))
    code, out, _, _ = env.hook("SessionStart", root, session="kn2")
    record("orient surfaces the undefined knowledge home", "knowledge home" in context(out).lower(), context(out)[-400:])


def scenario_vision_change(env):
    root = healthy_project(env, env.base / "vision")
    env.hook("SessionStart", root, session="vis")
    write(root, {"VISION.md": VISION.replace("Team workspaces.", "Team workspaces.\n- Mobile apps.")})
    code, out, _, _ = env.hook("Stop", root, session="vis", stop_hook_active=False)
    reason = (out or {}).get("reason", "")
    record("S9 VISION change asks for downstream review", "VISION" in reason and "README" in reason, reason)
    code, out, _, _ = env.hook("Stop", root, session="vis", stop_hook_active=False)
    record("S9 same vision drift detail fires once", review_requested(out) and "Vision:" not in out.get("reason", ""))
    write(root, {"VISION.md": VISION.replace("Owner: Hung · Confirmed: 2026-10-20", "Owner: Hung").replace("## What we will never become\n\n- Team workspaces.\n", "")})
    code, report = env.check(root)
    warns = codes(report, "warnings")
    record("C4 missing core section and confirmation are warnings", {"vision-section-missing", "vision-unconfirmed"} <= warns, str(warns))
    write(root, {"VISION.md": VISION})
    code, report = env.check(root)
    record("C4 a full manifesto vision has no vision warnings", not [w for w in report["warnings"] if w["code"].startswith("vision")],
           json.dumps(report["warnings"]))
    write(root, {"VISION.md": VISION + "\n## Architecture\n\nThe API lives in `src/api/routes.js`.\n\n```sh\nbun dev\n```\n"})
    code, report = env.check(root)
    record("C4b engineering content in VISION is a warning", "vision-engineering-content" in codes(report, "warnings"), json.dumps(report["warnings"]))


def scenario_non_software(env):
    root = env.base / "wedding-plan"
    root.mkdir()
    write(root, {"VISION.md": VISION, "BRAIN.md": BRAIN,
                 "PROGRESS.md": PROGRESS, "STRUCTURE.md": "# Structure\n\nPlanning notes in Drive.\n\n## Repository\n\nNo code.\n\n"
                 "## Brain\n\n### Google Drive: drive:Wedding\n\nOpen with: Drive connector.\n",
                 "README.md": README.replace("## Install\n\nRun `bun install`, then `bun dev`.", "## Access\n\nAsk Hung for the Drive folder."),
                 "TECHSTACK.md": "# Technology\n\nDrive: planning resources; access rules in BRAIN.\n",
                 "AGENTS.md": AGENTS})
    code, out, elapsed, _ = env.hook("SessionStart", root / "", session="np")
    text = context(out)
    record("F9 records without Git still orient", "Export to PDF" in text and "commits" not in text, text[:300])
    code, report = env.check(root)
    record("non-software project passes check without warnings", code == 0 and not report["warnings"],
           json.dumps(report["errors"] + report["warnings"]))
    code, out, _, _ = env.hook("Stop", root, session="np", stop_hook_active=False)
    record("T1 no-git task still gets a four-record review", review_requested(out), json.dumps(out))


def scenario_scale_and_staleness(env):
    root = healthy_project(env, env.base / "big")
    log = "".join(f"## 2026-{m:02d}-{d:02d}\n\n- Built thing {m}-{d}.\n\n" for m in range(10, 0, -1) for d in range(28, 0, -1))
    rows = "".join(f"| In progress | Item {i} | Something useful | 2026-10-01 |\n" for i in range(80))
    big = progress(ROW_EDITOR + ROW_EXPORT + rows).split("## 2026-10-30")[0] + log
    write(root, {"PROGRESS.md": big})
    (root / "VISION.md").write_bytes(VISION.encode() + b"\n\xff\xfe broken bytes\n")
    env.git(root, "commit", "-qam", "records")
    for i in range(3):
        write(root, {f"src/app/f{i}.js": str(i)})
        env.git(root, "add", "-A")
        env.git(root, "commit", "-qm", f"work {i}")
    for i in range(1500):
        p = root / "bulk" / f"d{i % 40}" / f"f{i}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    code, out, elapsed, proc = env.hook("SessionStart", root, session="big")
    text = context(out)
    record("F3 huge PROGRESS output stays bounded", code == 0 and len(text) < 4096 and "incomplete" in text and "before acting" in text, f"{len(text)} chars")
    record("F12 invalid UTF-8 does not crash", code == 0 and out is not None, proc.stderr[-300:])
    record("F13 commits since PROGRESS changed are reported", "3 commits" in text, text[-500:])
    record("F15 orient finishes under 1 second", elapsed < 1.0, f"{elapsed:.3f}s")
    code, report = env.check(root)
    record("C3b over 30 log entries is a warning", "log-too-long" in codes(report, "warnings"))


def scenario_nested(env):
    root = healthy_project(env, env.base / "mono")
    sub = root / "packages" / "web"
    sub.mkdir(parents=True)
    write(sub, {"PROGRESS.md": PROGRESS.replace("Export to PDF", "Web-only item")})
    code, out, _, _ = env.hook("SessionStart", sub / "", session="nest")
    record("F19 nearest folder with a record wins", "Web-only item" in context(out), context(out)[:200])


def scenario_branch_switch(env):
    root = healthy_project(env, env.base / "branch")
    env.git(root, "checkout", "-qb", "other")
    write(root, {"src/app/o.js": "o"})
    env.git(root, "add", "-A")
    env.git(root, "commit", "-qm", "other work")
    env.hook("SessionStart", root, session="br")
    env.git(root, "checkout", "-q", "main")
    write(root, {"src/app/m.js": "m"})
    env.git(root, "add", "-A")
    env.git(root, "commit", "-qm", "main work", "--date", "2026-10-02T00:00:00")
    code, out, _, _ = env.hook("Stop", root, session="br", stop_hook_active=False)
    record("S12 baseline not an ancestor: commit rules skipped, review remains",
           review_requested(out) and "work commit" not in out.get("reason", ""), json.dumps(out))


def scenario_changelog_and_links(env):
    root = healthy_project(env, env.base / "links")
    write(root, {"CHANGELOG.md": CHANGELOG + "\n## 2027-01-01\n\n- Will add planned dark mode.\n",
                 "BRAIN.md": BRAIN + "\nSee [the guide](docs/missing-guide.md).\n"})
    code, report = env.check(root)
    record("C10 future CHANGELOG date is an error", "changelog-future-date" in codes(report, "errors"))
    record("C10 planned-work words are a warning", "changelog-planned-words" in codes(report, "warnings"))
    record("C11 broken relative link is an error", "broken-link" in codes(report, "errors"))
    write(root, {"README.md": "# Tiny\n\nNo links.\n"})
    code, report = env.check(root)
    record("C9 README without record links is a warning", "entry-links" in codes(report, "warnings"))
    record("C16 README without an install or use section is a warning", "readme-no-install" in codes(report, "warnings"))
    write(root, {"README.md": README.replace("## Install", "## Get started")})
    code, report = env.check(root)
    record("C16 a Get started section counts", "readme-no-install" not in codes(report, "warnings"))
    (root / "README.md").unlink()
    code, report = env.check(root)
    record("C15 missing README is a warning", "readme-missing" in codes(report, "warnings"))


def scenario_no_baseline(env):
    root = healthy_project(env, env.base / "nobase")
    write(root, {"src/app/z.js": "z"})
    env.git(root, "add", "-A")
    env.git(root, "commit", "-qm", "z")
    code, out, _, _ = env.hook("Stop", root, session="never-started", stop_hook_active=False)
    record("T2 no baseline still gets a four-record review", code == 0 and review_requested(out), json.dumps(out))


def scenario_install(env):
    claude = env.base / "cfg" / "settings.json"
    codex = env.base / "cfg" / "hooks.json"
    claude.parent.mkdir()
    claude.write_text(json.dumps({"model": "x", "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "other-tool"}]}]}}))
    args = ["hooks", "install", "--claude-settings", str(claude), "--codex-hooks", str(codex), "--script-path", str(SCRIPT)]
    first, _ = env.run(args)
    second, _ = env.run(args)
    data = json.loads(claude.read_text())
    starts = data["hooks"]["SessionStart"]
    ours = [h for e in starts for h in e["hooks"] if "horsemen.py" in h["command"]]
    record("install keeps other hooks and settings", data["model"] == "x" and any(h["command"] == "other-tool" for e in starts for h in e["hooks"]))
    record("install is idempotent", first.returncode == 0 and second.returncode == 0 and len(ours) == 1 and len(data["hooks"]["Stop"]) == 1, first.stderr + second.stderr)
    record("install writes Codex hooks too", "horsemen.py" in codex.read_text())
    cmd = ours[0]["command"]
    root = healthy_project(env, env.base / "installed")
    proc = subprocess.run(["/bin/sh", "-c", cmd], input=json.dumps({"session_id": "i", "cwd": str(root)}),
                          capture_output=True, text=True, cwd=root, env=env.env, timeout=10)
    record("installed command runs and orients", "Export to PDF" in proc.stdout, proc.stdout[:200] + proc.stderr[:200])
    missing = subprocess.run(["/bin/sh", "-c", cmd.replace(str(SCRIPT), "/nonexistent/horsemen.py")], input="{}",
                             capture_output=True, text=True, env=env.env, timeout=10)
    record("installed command is silent when the skill is removed", missing.returncode == 0 and not missing.stdout)
    env.run(["hooks", "uninstall", "--claude-settings", str(claude), "--codex-hooks", str(codex)])
    data = json.loads(claude.read_text())
    record("uninstall removes only horsemen hooks", "horsemen" not in json.dumps(data) and "other-tool" in json.dumps(data))


def scenario_examples(env):
    """The documented examples must satisfy the format the script enforces."""
    import re
    text = (Path(__file__).resolve().parents[1] / "references" / "examples.md").read_text()
    software, studio = text.split("## Non-software", 1)
    for label, chunk, stubs in (("software", software, ["app/layout.tsx", "app/api/x.ts", "lib/summary/export/x.ts", "lib/billing/x.ts", "lib/billing/README.md", "docs/decisions.md"]),
                                ("non-software", studio, [])):
        root = env.base / {"software": "tiny-notes", "non-software": "studio-pilot"}[label]
        root.mkdir()
        for name, _, body in re.findall(r"(?ms)^### (\w+\.md)\n\n(```|~~~)markdown\n(.*?)^\2$", chunk):
            write(root, {name: body})
        write(root, {stub: "x\n" for stub in stubs})
        code, report = env.check(root)
        errors = [e for e in report["errors"] if e["code"] != "missing-record"]
        record(f"examples: {label} example passes check", not errors and report["records"], json.dumps(errors))
        format_codes = {"progress-legacy-format", "vision-section-missing", "vision-engineering-content", "brain-home-undefined",
                        "brain-no-providers", "brain-repo-item", "structure-no-brain-map", "progress-details-markdown",
                        "placeholder", "progress-no-state-table", "snapshot-too-long", "progress-row-no-link",
                        "readme-missing", "readme-no-install", "changelog-missing", "entry-links", "vision-legacy-format",
                        "progress-technical-in-body", "progress-item-unnamed", "shipped-list-long"}
        drift = [w for w in report["warnings"] if w["code"] in format_codes]
        record(f"examples: {label} example follows the current format", not drift, json.dumps(drift))


def scenario_preexisting_untracked(env):
    """S18: an untracked folder that existed before the session is not drift."""
    root = healthy_project(env, env.base / "untracked")
    write(root, {"public/gifts/a.png": "x"})
    env.hook("SessionStart", root, session="unt")
    code, out, _, _ = env.hook("Stop", root, session="unt", stop_hook_active=False)
    record("S18 pre-existing untracked folder is not structure drift",
           review_requested(out) and "Structure:" not in out.get("reason", ""), json.dumps(out))


def scenario_rearm(env):
    """S19/S20: reminders re-arm after the record is repaired and new drift appears."""
    root = healthy_project(env, env.base / "rearm")
    env.hook("SessionStart", root, session="re")
    write(root, {"lib/a.js": "a"})
    code, out, _, _ = env.hook("Stop", root, session="re", stop_hook_active=False)
    first = "lib" in (out or {}).get("reason", "")
    write(root, {"STRUCTURE.md": STRUCTURE + "\n`lib/`: helpers\n"})
    env.hook("Stop", root, session="re", stop_hook_active=False)
    write(root, {"tools/b.js": "b"})
    code, out, _, _ = env.hook("Stop", root, session="re", stop_hook_active=False)
    record("S19 structure reminder re-arms after STRUCTURE was updated", first and "tools" in (out or {}).get("reason", ""), json.dumps(out))
    rel = lambda n: (f"Release {n}", "2026-11-01", f"People get release {n}.")
    ev = "| Release {n} | v{n} deployed |\n"
    p1 = progress(shipped_section(rel(1)) + ROW_EDITOR + ROW_EXPORT, EV_EDITOR + ev.format(n=1))
    write(root, {"PROGRESS.md": p1, "STRUCTURE.md": STRUCTURE + "\n`lib/` and `tools/`\n"})
    code, out, _, _ = env.hook("Stop", root, session="re", stop_hook_active=False)
    a = "Release 1" in (out or {}).get("reason", "")
    write(root, {"CHANGELOG.md": CHANGELOG + "\n## 1 - 2026-11-01\n\n- Release 1.\n"})
    env.hook("Stop", root, session="re", stop_hook_active=False)
    write(root, {"PROGRESS.md": progress(shipped_section(rel(2), rel(1)) + ROW_EDITOR + ROW_EXPORT,
                                         EV_EDITOR + ev.format(n=1) + ev.format(n=2))})
    code, out, _, _ = env.hook("Stop", root, session="re", stop_hook_active=False)
    record("S20 changelog reminder re-arms for a second release", a and "Release 2" in (out or {}).get("reason", ""), json.dumps(out))


def scenario_slow_git(env):
    """F20: a slow Git still lets session start finish inside the host deadline."""
    root = healthy_project(env, env.base / "slowgit")
    fake = env.base / "slowbin"
    fake.mkdir(exist_ok=True)
    real = shutil.which("git")
    (fake / "git").write_text(f"#!/bin/sh\nsleep 1.2\nexec {real} \"$@\"\n")
    (fake / "git").chmod(0o755)
    saved = env.env["PATH"]
    env.env["PATH"] = f"{fake}:{saved}"
    try:
        code, out, elapsed, _ = env.hook("SessionStart", root, session="slow")
    finally:
        env.env["PATH"] = saved
    record("F20 slow Git: session start finishes under 4.5 s with output", elapsed < 4.5 and "Export to PDF" in context(out), f"{elapsed:.2f}s")


def scenario_install_permissions(env):
    """I1: install keeps a private config private."""
    cfg = env.base / "perm" / "settings.json"
    cfg.parent.mkdir()
    cfg.write_text(json.dumps({"env": {"TOKEN": "secret"}}))
    cfg.chmod(0o600)
    new = env.base / "perm" / "new-hooks.json"
    env.run(["hooks", "install", "--claude-settings", str(cfg), "--codex-hooks", str(new), "--script-path", str(SCRIPT)])
    record("I1 install preserves 0600 and creates new configs as 0600",
           (cfg.stat().st_mode & 0o777) == 0o600 and (new.stat().st_mode & 0o777) == 0o600,
           f"{oct(cfg.stat().st_mode & 0o777)} {oct(new.stat().st_mode & 0o777) if new.exists() else 'missing'}")
    data = json.loads(cfg.read_text())
    cmd = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]][0]
    record("I2 hook command prefers an absolute python3 over PATH lookup", "/python3" in cmd.split("exec")[0], cmd[:160])


def scenario_orientation_safety(env):
    """F5b/F21/F3b: orientation keeps gates, mandatory reading, and marks truncation."""
    root = healthy_project(env, env.base / "gates")
    long_gate = "Physical phone and bank-app QR rehearsal must pass before release " + "x" * 300 + " FINAL-GATE"
    write(root, {"PROGRESS.md": progress(extra=f"\nGates:\n\n- {long_gate}\n"),
                 "STRUCTURE.md": STRUCTURE.replace("## Brain", "## Read before changing\n\n- `docs/decisions.md` before any API change.\n\n## Brain")})
    code, out, _, _ = env.hook("SessionStart", root, session="g")
    text = context(out)
    record("F3b long line is not cut silently", "FINAL-GATE" in text or "incomplete" in text.lower(), text[-400:])
    record("F21 STRUCTURE 'Read before changing' is injected", "before any API change" in text, text[-400:])
    legacy = healthy_project(env, env.base / "gates-legacy")
    (legacy / "PROGRESS.md").unlink()
    write(legacy, {"STATUS.md": LEGACY_STATUS})
    code, out, _, _ = env.hook("SessionStart", legacy, session="gl")
    record("F5b legacy STATUS must be read before project work", "before project work" in context(out), context(out)[:400])


def scenario_check_hardening(env):
    """C3c/C3d/C5c/C11b/C12/C13: stricter checks found in review."""
    root = healthy_project(env, env.base / "hard")
    write(root, {"docs/my report.md": "x", "BRAIN.md": BRAIN + "\nSee [report](docs/my%20report.md).\n"})
    code, report = env.check(root)
    record("C11b URL-encoded local link resolves", "broken-link" not in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": TABLE_PROGRESS.replace("| Status | Item | What it means | Date |\n| --- | --- | --- | --- |", "| Status | Item |\n| --- | --- |")
                 .replace("| In progress | Note editor | Consultants can write notes in the app | 2026-10-28 |", "| In progress | Note editor |")
                 .replace("| Up next | Export to PDF | Consultants send a summary as a PDF | - |", "| Up next | Export |")})
    code, report = env.check(root)
    record("C3c status table without a Date column is an error", "progress-table-columns" in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": progress(shipped_section(("Old thing", "2026-09-01", "People got it.")) + ROW_EDITOR,
                                         EV_EDITOR + "| Old thing | v0.1 deployed |\n")})
    code, report = env.check(root)
    record("C3d an old Shipped bullet stays: the list keeps the latest ships, not the last 14 days",
           code == 0 and "shipped-row-stale" not in codes(report, "warnings"), json.dumps(report["errors"] + report["warnings"]))
    many = [(f"Thing {i}", f"2026-10-{10 + i:02d}", "People got it.") for i in range(11)]
    write(root, {"PROGRESS.md": progress(shipped_section(*many) + ROW_EDITOR, EV_EDITOR + "".join(f"| Thing {i} | v0.{i} deployed |\n" for i in range(11)))})
    code, report = env.check(root)
    record("P8 more than 10 Shipped bullets is a warning", "shipped-list-long" in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": TABLE_PROGRESS.replace("| Up next | Export to PDF |", "| In progress | Pipe \\| cell |")
                 .replace("| Note editor | branch editor |", "| Note editor | branch editor |\n| Pipe \\| cell | branch pipe |")})
    code, report = env.check(root)
    record("C3e escaped pipe in an old-table cell parses", "progress-state-unknown" not in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": PROGRESS, "STRUCTURE.md": STRUCTURE.replace("docs/     decisions", "docs/     decisions\nghost/    removed folder")})
    code, report = env.check(root)
    record("C5c path in the At-a-glance tree is verified", any("ghost/" in e["message"] for e in report["errors"]), json.dumps(report["errors"]))
    write(root, {"STRUCTURE.md": STRUCTURE.replace("docs/     decisions", "docs/     decisions\nmissing/src/")})
    code, report = env.check(root)
    record("C5d bare tree path without a description is verified", any("missing/src/" in e["message"] for e in report["errors"]), json.dumps(report["errors"]))
    write(root, {"STRUCTURE.md": STRUCTURE, "BRAIN.md": BRAIN.replace("Visibility: private", "Visibility: public") +
                 "\n[Folder](https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz012345)\n"})
    code, report = env.check(root)
    record("C12 public repository with a private Drive locator is an error", "private-locator" in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"BRAIN.md": BRAIN +
                 "\n[Folder](https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz012345)\n"})
    code, report = env.check(root)
    record("C12b private repository may keep Drive links", "private-locator" not in codes(report, "errors"))
    write(root, {"BRAIN.md": BRAIN.replace("Visibility: private", "Visibility: public") +
                 "\nInstall `conquistador@0.12.0` or `@scope/pkg@1.2.3`. Contact: owner@example.com\n"})
    code, report = env.check(root)
    hits = [e["message"] for e in report["errors"] if e["code"] == "private-locator"]
    record("C12c package@version is not an email; a real email still is",
           len(hits) == 1 and "owner@example.com" in hits[0], json.dumps(hits))
    archived = progress("## In progress\n\n- Nothing right now.\n\n", "")
    write(root, {"PROGRESS.md": archived})
    code, report = env.check(root)
    record("C13 empty status section (archived project) is not a format warning",
           not {"progress-no-state-table", "progress-item-unnamed"} & codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": progress("", "")})
    code, report = env.check(root)
    record("P10 no status section at all is a warning", "progress-no-state-table" in codes(report, "warnings"), json.dumps(report["warnings"]))


def scenario_record_formats(env):
    """C3f-C3i, C5e, C5f, C6, C6b, C6c: the stakeholder PROGRESS, the brain registry, and the two-map STRUCTURE."""
    root = healthy_project(env, env.base / "formats")
    code, report = env.check(root)
    record("formats: the healthy fixture has no errors or warnings", code == 0 and not report["warnings"],
           json.dumps(report["errors"] + report["warnings"]))
    record("C5e STRUCTURE Brain section folders are not checked as repository paths",
           "structure-missing-path" not in codes(report, "errors"), json.dumps(report["errors"]))

    write(root, {"PROGRESS.md": LEGACY_PROGRESS})
    code, report = env.check(root)
    record("C3f old PROGRESS format: no errors, one migration warning",
           code == 0 and "progress-legacy-format" in codes(report, "warnings"), json.dumps(report["errors"] + report["warnings"]))
    write(root, {"PROGRESS.md": TABLE_PROGRESS})
    code, report = env.check(root)
    record("P2 status-table PROGRESS: no errors, one migration warning to bullet sections",
           code == 0 and "progress-legacy-format" in codes(report, "warnings"), json.dumps(report["errors"] + report["warnings"]))
    write(root, {"PROGRESS.md": progress(ROW_EDITOR.replace("- **Note editor**", "- Note editor") + ROW_EXPORT)})
    code, report = env.check(root)
    record("P3 status bullet without a bold item name is a warning", "progress-item-unnamed" in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": progress(ROW_EDITOR.replace("write notes in the app.", "write notes in `src/app/editor.js` (PR #12, a1b2c3d).") + ROW_EXPORT)})
    code, report = env.check(root)
    record("P4 code, paths, PR numbers, or commits outside toggles are a warning",
           "progress-technical-in-body" in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": progress(extra="\n- PR #12, commit a1b2c3d, `src/app/editor.js`.\n")})
    code, report = env.check(root)
    record("P4b technical detail inside a toggle is fine", "progress-technical-in-body" not in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": progress(shipped_section(("Tomorrow thing", "2026-12-01", "Not yet.")) + ROW_EDITOR, EV_EDITOR + "| Tomorrow thing | v9 |\n")})
    code, report = env.check(root)
    record("P5 Shipped bullet dated in the future is an error", "progress-row-future" in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": progress(ROW_EDITOR.replace("in the app.\n", "in the app.\n  - **Autosave** detail line.\n") + ROW_EXPORT)})
    code, report = env.check(root)
    record("P6 nested bullets are details, not items", code == 0 and not report["warnings"], json.dumps(report["errors"] + report["warnings"]))
    write(root, {"PROGRESS.md": progress(ROW_EDITOR.replace("- **Note editor**", "- **Ghost item**") + ROW_EXPORT)})
    code, report = env.check(root)
    record("P7 In progress bullet without a Technical details row is a warning",
           "progress-row-no-link" in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": PROGRESS, "VISION.md": LEGACY_VISION})
    code, report = env.check(root)
    record("V2 business-plan VISION: no missing sections, one manifesto migration warning",
           "vision-section-missing" not in codes(report, "warnings") and "vision-legacy-format" in codes(report, "warnings"),
           json.dumps(report["warnings"]))
    write(root, {"VISION.md": VISION})
    write(root, {"PROGRESS.md": LEGACY_PROGRESS.replace("live at example.invalid", "-")})
    code, report = env.check(root)
    record("C3f old format still needs evidence for Shipped", "progress-shipped-no-evidence" in codes(report, "errors"))

    write(root, {"PROGRESS.md": PROGRESS.replace("| Note editor | branch editor |\n\n</details>", "| Note editor | branch editor |\n")})
    code, report = env.check(root)
    record("C3g unclosed details toggle is an error", "progress-details-unclosed" in codes(report, "errors"), json.dumps(report["errors"]))
    write(root, {"PROGRESS.md": PROGRESS.replace("<summary>Technical details</summary>\n\n| Item", "<summary>Technical details</summary>\n| Item")})
    code, report = env.check(root)
    record("C3h no blank line after summary is a warning", "progress-details-markdown" in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"PROGRESS.md": PROGRESS + "\n## 2026-10-31 · Later entry below an older one\n\nText.\n"})
    code, report = env.check(root)
    record("C3i headline log headings are parsed as dates", "log-order" in codes(report, "warnings"), json.dumps(report["warnings"]))

    write(root, {"PROGRESS.md": PROGRESS, "BRAIN.md": BRAIN.replace("Brain: Google Drive", "Knowledge home: Google Drive")})
    code, report = env.check(root)
    record("C6 legacy `Knowledge home:` line still counts", "brain-home-undefined" not in codes(report, "warnings"))
    write(root, {"BRAIN.md": "# Brain\n\nBrain: None (all knowledge is in this repository) · Access verified: 2026-10-20\n\nVisibility: private\n",
                 "STRUCTURE.md": STRUCTURE.split("## Brain")[0] + "## Other documents\n\n- README.md\n"})
    code, report = env.check(root)
    bad = {"brain-home-undefined", "brain-no-providers", "structure-no-brain-map"} & codes(report, "warnings")
    record("C6 `Brain: None` is a valid answer and needs no Brain map", not bad, str(bad))
    write(root, {"BRAIN.md": BRAIN.split("## Providers")[0], "STRUCTURE.md": STRUCTURE})
    code, report = env.check(root)
    record("C6b provider named without a Providers table is a warning", "brain-no-providers" in codes(report, "warnings"))
    write(root, {"BRAIN.md": BRAIN + "| Decisions | `docs/decisions.md` | In Git |\n"})
    code, report = env.check(root)
    record("C6c repository file listed as brain knowledge is a warning", "brain-repo-item" in codes(report, "warnings"), json.dumps(report["warnings"]))
    write(root, {"BRAIN.md": BRAIN, "STRUCTURE.md": STRUCTURE.split("## Brain")[0] + "## Other documents\n\n- README.md\n"})
    code, report = env.check(root)
    record("C5f provider in BRAIN without a STRUCTURE Brain map is a warning", "structure-no-brain-map" in codes(report, "warnings"))


def scenario_structure_trees(env):
    """C5g-C5n: nested trees in STRUCTURE resolve each node against its parent."""
    root = healthy_project(env, env.base / "trees")
    write(root, {"src/pages/[...locale]/index.astro": "x", "public/a.png": "x"})

    def tree_errors(tree, lang="text"):
        write(root, {"STRUCTURE.md": STRUCTURE.replace("## Repository", f"## Map\n\n```{lang}\n{tree}```\n\n## Repository")})
        _, report = env.check(root)
        return [e["message"] for e in report["errors"] if e["code"] == "structure-missing-path"]

    box = ("trees/\n"
           "├── src/\n"
           "│   ├── app/                 UI (start here)\n"
           "│   ├── api/                 HTTP handlers, see docs/ghost-in-description/\n"
           "│   └── pages/\n"
           "│       └── [...locale]/\n"
           "│           └── index.astro  home page\n"
           "├── public/\n"
           "│   ├── *.png                images\n"
           "│   └── <slug>/              one folder per post\n"
           "├── docs/\n"
           "│   ├── decisions.md         decisions\n"
           "│   └── ...\n"
           "└── README.md                introduction\n")
    errors = tree_errors(box)
    record("C5h/C5j/C5k/C5l/C5n valid box tree with root, brackets, patterns, and slashes in descriptions passes",
           not errors, json.dumps(errors))
    errors = tree_errors(box.replace("trees/\n", "my-app-under-another-name/\n", 1))
    record("C5j root line with a different folder name is still the root", not errors, json.dumps(errors))
    errors = tree_errors(box.replace("│   └── pages/", "│   ├── ghost/\n│   └── pages/"))
    record("C5g missing nested node is reported at its full path",
           any("src/ghost/" in e for e in errors) and not any(e.endswith("`ghost/` does not exist.") for e in errors), json.dumps(errors))
    errors = tree_errors(box.replace("index.astro  home page", "[slug].astro  case page"))
    record("C5k missing bracketed file is reported", any("src/pages/[...locale]/[slug].astro" in e for e in errors), json.dumps(errors))
    indent = "src/\n  app/        UI\n  api/        handlers\n  phantom/    missing\ndocs/\n  decisions.md\n"
    errors = tree_errors(indent)
    record("C5i indentation-only tree resolves parents",
           any("src/phantom/" in e for e in errors) and len(errors) == 1, json.dumps(errors))
    errors = tree_errors("flowchart LR\nsrc/ghost/   --> build\n", lang="mermaid")
    record("C5m mermaid block is not parsed as a tree", not errors, json.dumps(errors))


def scenario_task_review(env):
    root = healthy_project(env, env.base / "task-review")
    env.hook("SessionStart", root, session="task-review")
    before = {p.name: p.read_bytes() for p in root.glob("*.md")}
    first = env.hook("Stop", root, session="task-review")[1]
    second = env.hook("Stop", root, session="task-review")[1]
    record("T3 successive discussion or external-work tasks both get a review",
           review_requested(first) and review_requested(second), json.dumps([first, second]))
    record("T1 review hooks never edit records", before == {p.name: p.read_bytes() for p in root.glob("*.md")})
    write(root, {"src/app/main.js": "uncommitted work\n"})
    out = env.hook("Stop", root, session="task-review")[1]
    record("T4 uncommitted work gets review without a false release claim", review_requested(out), json.dumps(out))
    caches = [p for p in env.state.glob("*.json") if json.loads(p.read_text()).get("root") == str(root)]
    for p in caches:
        p.write_text("{broken")
    out = env.hook("Stop", root, session="task-review")[1]
    record("T2 corrupt cache does not disable review", review_requested(out), json.dumps(out))
    out = env.hook("SessionStart", root, session="task-review", source="compact")[1]
    record("T2 corrupt cache can be rebuilt on compaction", "Export to PDF" in context(out), json.dumps(out))
    saved = env.env["HORSEMEN_STATE_DIR"]
    blocked = env.base / "blocked-cache"
    blocked.write_text("This is a file, not a cache directory.")
    env.env["HORSEMEN_STATE_DIR"] = str(blocked)
    try:
        out = env.hook("Stop", root, session="task-review")[1]
        record("T2 unavailable cache does not disable review", review_requested(out), json.dumps(out))
        out = env.hook("SessionStart", root, session="task-review")[1]
        record("T2 unavailable cache does not disable orientation", "Export to PDF" in context(out), json.dumps(out))
    finally:
        env.env["HORSEMEN_STATE_DIR"] = saved


def scenario_state_identity(env):
    root = healthy_project(env, env.base / "cache-identity")
    for label, first, second in (("punctuation", "punct/a", "punct?a"),
                                  ("long prefix", "x" * 130 + "a", "x" * 130 + "b")):
        before = set(env.state.glob("*.json"))
        env.hook("SessionStart", root, session=first)
        env.hook("SessionStart", root, session=second)
        record("K1 cache separates IDs with " + label, len(set(env.state.glob("*.json")) - before) == 2)
    other = healthy_project(env, env.base / "cache-other")
    before = set(env.state.glob("*.json"))
    env.hook("SessionStart", root, session="shared")
    env.hook("SessionStart", other, session="shared")
    created = set(env.state.glob("*.json")) - before
    record("K2 cache separates project roots in one session", len(created) == 2)
    record("K6 cache files and directory are private",
           env.state.stat().st_mode & 0o077 == 0 and all(p.stat().st_mode & 0o077 == 0 for p in created))

    fallback = healthy_project(env, env.base / "cache-fallback")
    payload = json.dumps({"cwd": str(fallback)})
    env.run(["hook", "session-start"], payload, cwd=fallback)
    write(fallback, {"src/app/new.js": "x"})
    env.git(fallback, "add", "-A")
    env.git(fallback, "commit", "-qm", "new work")
    proc, _ = env.run(["hook", "stop"], payload, cwd=fallback)
    record("K3 absent session ID keeps a baseline across hook processes", "work commit" in proc.stdout, proc.stdout)


def scenario_state_resume(env):
    root = healthy_project(env, env.base / "cache-resume")
    env.hook("SessionStart", root, session="resume", source="startup")
    for index, source in enumerate(("compact", "resume", None)):
        write(root, {f"src/app/resume{index}.js": "x"})
        env.git(root, "add", "-A")
        env.git(root, "commit", "-qm", "work before resume")
        options = {"source": source} if source else {}
        env.hook("SessionStart", root, session="resume", **options)
        out = env.hook("Stop", root, session="resume")[1]
        record(f"K4 baseline survives {source or 'an omitted source'}",
               "work commit" in (out or {}).get("reason", ""), json.dumps(out))
    # A second intent edit must be noticed even after the first reminder.
    for index in range(2):
        write(root, {"VISION.md": VISION + f"\nOwner direction note {index}.\n"})
        out = env.hook("Stop", root, session="resume")[1]
        record(f"K5 VISION edit {index + 1} gets a new drift detail", "Vision:" in (out or {}).get("reason", ""), json.dumps(out))


def scenario_cache_shape(env):
    root = healthy_project(env, env.base / "cache-shape")
    env.hook("SessionStart", root, session="shape", source="startup")
    caches = [p for p in env.state.glob("*.json") if json.loads(p.read_text()).get("root") == str(root)]
    assert len(caches) == 1, "The scenario must corrupt the actual project cache."
    cache = caches[0]
    valid = cache.read_text()
    for label, field, value in (("scalar folders", "dirs", 1), ("nested folders", "dirs", [{}]),
                                ("nested shipped items", "shipped", [["item"]]), ("non-text Git revision", "head", ["HEAD"])):
        state = json.loads(valid)
        state[field] = value
        cache.write_text(json.dumps(state))
        code, out, _, _ = env.hook("Stop", root, session="shape")
        record("K7 review survives " + label, code == 0 and review_requested(out), json.dumps(out))


def scenario_install_health(env):
    root = env.base / "health-cfg"
    target = root / "installed/horsemen.py"
    write(root, {"installed/horsemen.py": SCRIPT.read_text()})
    claude, codex = root / "claude.json", root / "codex.json"
    opts = ["--claude-settings", str(claude), "--codex-hooks", str(codex)]
    env.run(["hooks", "install", *opts, "--script-path", str(target)])
    proc, _ = env.run(["hooks", "status", *opts])
    record("I3 status names the configured script", proc.returncode == 0 and str(target) in proc.stdout, proc.stdout)
    target.unlink()
    proc, _ = env.run(["hooks", "status", *opts])
    record("I3 removed skill is reported as a broken installation",
           proc.returncode != 0 and "missing" in proc.stdout.lower(), proc.stdout + proc.stderr)
    target.write_text(SCRIPT.read_text())
    data = json.loads(codex.read_text())
    del data["hooks"]["Stop"]
    codex.write_text(json.dumps(data))
    proc, _ = env.run(["hooks", "status", *opts])
    record("I4 incomplete hook pair is unhealthy", proc.returncode != 0 and "Stop" in proc.stdout, proc.stdout + proc.stderr)


SCENARIOS = [scenario_noise, scenario_initialization, scenario_adoption, scenario_shipping, scenario_doc_only_commits,
             scenario_refactor, scenario_knowledge_migration, scenario_vision_change, scenario_non_software,
             scenario_scale_and_staleness, scenario_nested, scenario_branch_switch, scenario_changelog_and_links,
             scenario_no_baseline, scenario_install, scenario_examples, scenario_preexisting_untracked,
             scenario_rearm, scenario_slow_git, scenario_install_permissions, scenario_orientation_safety, scenario_check_hardening,
             scenario_record_formats, scenario_structure_trees, scenario_task_review, scenario_state_identity,
             scenario_state_resume, scenario_cache_shape, scenario_install_health]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, help="Write the JSON receipt here")
    parser.add_argument("--keep", action="store_true", help="Keep the temp folder for inspection")
    args = parser.parse_args()
    base = Path(tempfile.mkdtemp(prefix="horsemen-e2e-"))
    env = Env(base)
    for scenario in SCENARIOS:
        before = len(results)
        try:
            scenario(env)
        except Exception as error:  # A crash fails the scenario, not the run.
            record(scenario.__name__ + " crashed", False, repr(error))
        if len(results) == before:
            record(scenario.__name__ + " recorded nothing", False)
    failed = [r for r in results if not r["passed"]]
    receipt = {"status": "failed" if failed else "passed", "date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "script": str(SCRIPT), "python": sys.version.split()[0], "total": len(results),
               "failed": len(failed), "results": results}
    text = json.dumps(receipt, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    for r in results:
        print(("PASS " if r["passed"] else "FAIL ") + r["scenario"] + ("" if r["passed"] else f"  -- {r['detail'][:300]}"))
    print(f"{receipt['status']}: {len(results) - len(failed)}/{len(results)}")
    if not args.keep:
        shutil.rmtree(base, ignore_errors=True)
    else:
        print(f"kept {base}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
