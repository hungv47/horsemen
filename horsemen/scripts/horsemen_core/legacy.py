#!/usr/bin/env python3
"""Horsemen project records: health check, agent hooks, and hook installer.

usage:
  horsemen.py check [DIR] [--json]
  horsemen.py hook session-start|stop          (reads hook JSON on stdin)
  horsemen.py hooks install|uninstall|status [--claude-settings P] [--codex-hooks P] [--script-path P]

No dependencies. Git is optional. See references/hooks.md for the contract.
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta
from urllib.parse import unquote
from pathlib import Path

RECORDS = ["VISION.md", "BRAIN.md", "PROGRESS.md", "STRUCTURE.md"]
LEGACY_PROGRESS = "STATUS.md"
SUPPORTING = ["README.md", "CHANGELOG.md", "TECHSTACK.md", "TECH.md", "AGENTS.md", "CLAUDE.md", "ROADMAP.md"]
MARKERS = RECORDS + [LEGACY_PROGRESS]
RECORD_FILES = set(MARKERS + SUPPORTING)
STATES = {"shipped", "partly shipped", "ready to ship", "in progress", "up next", "blocked", "needs decision"}
SHIPPED = {"shipped", "partly shipped"}
LEGACY_STATES = {"built not shipped": "ready to ship", "next": "up next"}
STATE_LABELS = "Shipped, Partly shipped, Ready to ship, In progress, Up next, Blocked, Needs decision"
EMPTY = {"", "-", "—", "–", "n/a", "na", "none", "tbd", "unknown", "?"}
VISION_CORE = {"why": "Why we exist", "world": "The world we are building", "build for": "Who we build for",
               "believe": "What we believe", "get there": "How we get there", "never": "What we will never become"}
VISION_LEGACY = ("purpose", "picture", "serves", "creates value", "reaches", "runs", "plays out")
STATUS_HEADINGS = {"shipped": "Shipped", "recently shipped": "Shipped", "ready to ship": "Ready to ship",
                   "in progress": "In progress", "up next": "Up next", "blocked": "Blocked",
                   "needs decision": "Needs decision", "needs a decision": "Needs decision"}
SHIPPED_LIST_LIMIT = 10
TECHNICAL = [r"`[^`\n]+`", r"\bPRs?\s*#?\d+", r"(?<![\w/&])#\d+\b", r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b"]
SNAPSHOT_LINES = 60
SNAPSHOT_CHARS = 3000
READ_FIRST_CHARS = 600
HOOK_BUDGET = 3.5  # seconds for all Git calls in one hook run; hosts allow 5
DEADLINE = None
REQUIRED_COLUMNS = ["item", "date"]
PRIVATE_LOCATORS = [r"drive\.google\.com/(?:drive/(?:u/\d+/)?folders|file/d)/", r"docs\.google\.com/(?:document|spreadsheets|presentation)/d/",
                    r"[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b", r"/Users/[^/\s]+/", r"GoogleDrive-"]
LOG_LIMIT = 30
IGNORED_TOP = {"node_modules", "__pycache__", "LICENSE", "LICENSE.md", "LICENSE.txt", "package-lock.json",
               "bun.lock", "bun.lockb", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Cargo.lock",
               "Gemfile.lock", "go.sum", "skills-lock.json"}
DATE = r"\d{4}-\d{2}-\d{2}"
HOOK_MARK = "horsemen.py"
CACHE_VERSION = 1


def today():
    return os.environ.get("HORSEMEN_TODAY") or date.today().isoformat()


def read(path):
    try:
        return Path(path).read_bytes().decode("utf-8", "replace")
    except OSError:
        return None


def digest(text):
    return None if text is None else hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def git(root, *args, ok_codes=(0,)):
    timeout = 10
    if DEADLINE is not None:
        timeout = min(2.0, DEADLINE - time.monotonic())
        if timeout < 0.25:
            return None  # Out of budget: skip optional Git work rather than miss the host deadline.
    try:
        proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=timeout,
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode in ok_codes else None


def git_top(start):
    out = git(start, "rev-parse", "--show-toplevel")
    return Path(out.strip()).resolve() if out and out.strip() else None


def find_root(start):
    """Nearest folder with a record, searching up to the Git top level or home."""
    start = Path(start).resolve()
    top = git_top(start)
    home = Path.home().resolve()
    current = start
    for _ in range(12):
        if any((current / name).is_file() for name in MARKERS):
            return current, top
        if (top and current == top) or current == home or current.parent == current:
            break
        current = current.parent
    return None, top


def strip_code(text):
    text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
    return re.sub(r"`[^`\n]*`", "", text)


def sections(text):
    """Map lowercased H2 title to its body."""
    out, title, body = {}, None, []
    for line in text.splitlines():
        match = re.match(r"^##\s+(.*?)\s*$", line)
        if match:
            if title is not None:
                out[title] = "\n".join(body)
            title, body = match.group(1).lower(), []
        elif title is not None:
            body.append(line)
    if title is not None:
        out[title] = "\n".join(body)
    return out


# ---------------------------------------------------------------- PROGRESS

def split_progress(text):
    if re.search(r"(?m)^## Latest day\s*$", text):
        boundary = re.search(r"(?m)^## (?:Historical ships|Upcoming roadmap)\s*$", text)
        if boundary:
            return text[:boundary.start()], text[boundary.start():]
    match = re.search(rf"(?m)^##\s+{DATE}\b", text)
    return (text[:match.start()], text[match.start():]) if match else (text, "")


def tables(text):
    """Every Markdown table in text, as (header, rows). Header cells are lowercased; rows keep cell text."""
    found, header = [], None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip().replace("\x00", "|") for c in line.replace("\\|", "\x00").strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        if header is None:
            header = [c.strip("*` ").lower() for c in cells]
            found.append((header, []))
        else:
            found[-1][1].append(cells)
    return found


def item_key(value):
    return re.sub(r"\s+", " ", re.sub(r"[*`_]", "", value)).strip().lower()


def parse_table(snapshot):
    """Return (header, rows, legacy) for the status table. Evidence comes from the row (old format) or from
    the Technical details table whose columns are Item and Evidence."""
    all_tables = tables(snapshot)
    status = next(((h, r) for h, r in all_tables if h and h[0] in ("status", "state")), None)
    if status is None:
        return None, [], False
    header, cells = status
    evidence = {}
    for h, r in all_tables:
        if h and h[0] == "item" and "evidence" in h:
            for row in r:
                values = dict(zip(h, row))
                evidence[item_key(values.get("item", ""))] = values.get("evidence", "")
    legacy = header[0] == "state" or "evidence" in header
    rows = []
    for row in cells:
        values = dict(zip(header, row))
        item = values.get("item", "")
        rows.append({"state": values.get(header[0], ""), "item": item,
                     "evidence": values["evidence"] if "evidence" in values else evidence.get(item_key(item), ""),
                     "date": values.get("date", ""), "width_ok": len(row) == len(header)})
    return header, rows, legacy


def strip_details(text):
    return re.sub(r"(?is)<details\b.*?</details>", "", text)


def latest_status_text(snapshot):
    if re.search(r"(?m)^## Latest day\s*$", snapshot):
        # Unwrap only the outer latest-day toggle. Existing inner technical
        # toggles still remain excluded by strip_details below.
        match = re.search(r"(?is)<details\b[^>]*>\s*<summary>.*?</summary>", snapshot)
        if match:
            closing = snapshot.rfind("</details>")
            if closing >= match.end():
                snapshot = snapshot[:closing] + snapshot[closing + len("</details>"):]
                snapshot = snapshot[:match.start()] + snapshot[match.end():]
    return strip_details(snapshot)


def historical_ships(text):
    match = re.search(r"(?ms)^## Historical ships\s*$(.*?)(?=^## Upcoming roadmap\s*$|\Z)", text)
    if not match:
        return []
    rows=[]
    for header, values in tables(match.group(1)):
        if header == ['date','shipped','proof']:
            rows.extend(dict(zip(header,row)) for row in values)
    return rows


def bullet_items(snapshot):
    """Return (found, rows, unnamed) from status sections (`## Shipped`, `## In progress`, ...).
    Each top-level bullet `- **Item** (date or note): what it means` is one item."""
    evidence = {}
    for h, r in tables(snapshot):
        if h and h[0] == "item" and "evidence" in h:
            for row in r:
                values = dict(zip(h, row))
                evidence[item_key(values.get("item", ""))] = values.get("evidence", "")
    found, rows, unnamed = False, [], []
    for title, body in sections(latest_status_text(snapshot)).items():
        state = STATUS_HEADINGS.get(re.sub(r"[^a-z ]", "", title).strip())
        if state is None:
            continue
        found = True
        for line in body.splitlines():
            bullet = re.match(r"^[-*]\s+(.*\S)", line)
            if not bullet:
                continue
            text = bullet.group(1)
            named = re.match(r"\*\*(.+?)\*\*\s*(?:\(([^)]*)\))?", text)
            if not named:
                if not re.match(r"(?i)(nothing|none)\b", text):
                    unnamed.append(text)
                continue
            note = named.group(2) or ""
            when = re.search(DATE, note)
            label = "Partly shipped" if state == "Shipped" and "partly" in note.lower() else state
            rows.append({"state": label, "item": named.group(1), "evidence": evidence.get(item_key(named.group(1)), ""),
                         "date": when.group(0) if when else "", "width_ok": True})
    return found, rows, unnamed


def progress_items(snapshot):
    """Return (format, rows): "bullets" for status sections, "table" for a status table, None when neither exists."""
    found, rows, _ = bullet_items(snapshot)
    if found:
        return "bullets", rows
    header, rows, _ = parse_table(snapshot)
    return ("table" if header is not None else None), rows


def table_rows(snapshot):
    return progress_items(snapshot)[1]


def norm_state(value):
    state = re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", value.lower())).strip()
    return LEGACY_STATES.get(state, state)


def shipped_items(text):
    if not text:
        return set()
    snapshot, _ = split_progress(text)
    return {r["item"] for r in table_rows(snapshot) if norm_state(r["state"]) in SHIPPED} | {r.get("shipped", "") for r in historical_ships(text) if r.get("shipped")}


def check_details(text, add):
    body = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
    if len(re.findall(r"(?i)<details\b", body)) != len(re.findall(r"(?i)</details>", body)):
        add("error", "progress-details-unclosed", "PROGRESS.md",
            "A `<details>` toggle is not closed. GitHub hides everything after it.")
    if re.search(r"(?i)</summary>[ \t]*\n[ \t]*[^\s<]", body):
        add("warning", "progress-details-markdown", "PROGRESS.md",
            "Add a blank line after `</summary>`. Without it GitHub does not render the Markdown inside the toggle.")


def check_progress(text, add):
    snapshot, log = split_progress(text)
    updated = re.search(rf"(?m)^\**Updated:?\**:?\s*({DATE})", snapshot)
    if not updated:
        add("error", "progress-updated-missing", "PROGRESS.md", "No `Updated: YYYY-MM-DD` line at the top.")
    elif updated.group(1) > today():
        add("error", "progress-updated-future", "PROGRESS.md", f"Updated date {updated.group(1)} is in the future.")
    check_details(text, add)
    history = historical_ships(text)
    for item in history:
        if item.get('proof','').strip().lower() in EMPTY:
            add('error','progress-history-no-evidence','PROGRESS.md',
                'Historical ship '+item.get('shipped','Unnamed')+' needs a delivery proof link or dated owner confirmation.')
        when=item.get('date','')
        if re.fullmatch(DATE,when) and when > today():
            add('error','progress-history-future','PROGRESS.md','A historical ship is dated in the future.')
    found, rows, unnamed = bullet_items(snapshot)
    header, legacy = None, False
    if not found:
        header, rows, legacy = parse_table(snapshot)
    if not found and header is None:
        add("warning", "progress-no-state-table", "PROGRESS.md",
            "No status sections (`## Shipped`, `## In progress`, `## Up next`, ...). Rebuild the snapshot from the template.")
    elif header is not None:
        add("warning", "progress-legacy-format", "PROGRESS.md",
            "Status table format. Rewrite the snapshot as status sections with one bullet per item "
            "(`## Shipped`, `## In progress`, `## Up next`, ...); keep evidence in the Technical details toggle (references/adopt.md).")
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            add("error", "progress-table-columns", "PROGRESS.md", "Status table lacks column(s): " + ", ".join(missing) + ".")
        if any(not r["width_ok"] for r in rows):
            add("error", "progress-table-columns", "PROGRESS.md", "A status-table row has the wrong number of cells.")
    if unnamed:
        add("warning", "progress-item-unnamed", "PROGRESS.md",
            f"Status bullet \"{unnamed[0][:60]}\" has no bold item name. Write `- **Item** (date): what it means for people`.")
    body = strip_details(re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text))
    technical = next((m.group(0) for pattern in TECHNICAL for m in [re.search(pattern, body)] if m), None)
    if technical:
        add("warning", "progress-technical-in-body", "PROGRESS.md",
            f"\"{technical[:40]}\" is technical detail in the stakeholder text. Say what it means for people; "
            "move code, paths, PRs, and commits into a Technical details toggle.")
    if not re.search(r"(?m)^\**Next action:?\**:?\s*\S", snapshot):
        add("warning", "progress-next-action-missing", "PROGRESS.md", "No `Next action:` line under the summary.")
    stale_before = (date.fromisoformat(today()) - timedelta(days=14)).isoformat()
    for row in rows:
        state = norm_state(row["state"])
        if "{{" in row["state"] + row["item"]:
            continue
        if state not in STATES:
            add("error", "progress-state-unknown", "PROGRESS.md",
                f"Row \"{row['item'][:60]}\" has status \"{row['state']}\". Use: {STATE_LABELS}.")
        elif state in SHIPPED and row["evidence"].strip("*` ").lower() in EMPTY:
            add("error", "progress-shipped-no-evidence", "PROGRESS.md",
                f"{row['state'].strip('*` ')} item \"{row['item'][:60]}\" has no evidence (release, deploy, URL, or owner confirmation) "
                "in the Technical details table.")
        if state in {"in progress", "ready to ship"} and row["evidence"].strip("*` ").lower() in EMPTY:
            add("warning", "progress-row-no-link", "PROGRESS.md",
                f"Item \"{row['item'][:60]}\" needs a link or next step in the Technical details table.")
        if header is not None and state == "shipped" and re.fullmatch(DATE, row["date"]) and row["date"] < stale_before:
            add("warning", "shipped-row-stale", "PROGRESS.md",
                f"Shipped row \"{row['item'][:60]}\" is older than 14 days. Remove it; the log and CHANGELOG keep it.")
        if row["date"] and re.fullmatch(DATE, row["date"]) and row["date"] > today() and state in {"shipped", "ready to ship"}:
            add("error", "progress-row-future", "PROGRESS.md", f"Row \"{row['item'][:60]}\" is dated in the future.")
    shipped_count = len([r for r in rows if norm_state(r["state"]) in SHIPPED])
    if found and shipped_count > SHIPPED_LIST_LIMIT:
        add("warning", "shipped-list-long", "PROGRESS.md", f"{shipped_count} Shipped items. Keep the latest "
            f"{SHIPPED_LIST_LIMIT}; CHANGELOG and the dated updates keep the rest.")
    if len(rows) - shipped_count > 15:
        add("warning", "too-many-rows", "PROGRESS.md", f"{len(rows) - shipped_count} open items. Keep under 15; move ideas to Roadmap.")
    if snapshot.count("\n") > 70:
        add("warning", "snapshot-too-long", "PROGRESS.md", f"Snapshot is {snapshot.count(chr(10))} lines. Target: under 50.")
    dates = re.findall(rf"(?m)^##\s+({DATE})\b", log)
    if len(set(dates)) != len(dates):
        add("warning", "log-duplicate", "PROGRESS.md", "A log date appears twice. Merge the entries.")
    if any(a < b for a, b in zip(dates, dates[1:])):
        add("warning", "log-order", "PROGRESS.md", "Log dates are not newest first.")
    future = [d for d in dates if d > today()]
    if future:
        add("warning", "log-future", "PROGRESS.md", f"Log date {future[0]} is in the future.")
    if len(dates) > LOG_LIMIT:
        add("warning", "log-too-long", "PROGRESS.md",
            f"{len(dates)} log entries. Move entries after the newest {LOG_LIMIT} to docs/progress-log.md.")
    return updated.group(1) if updated else None


# ---------------------------------------------------------------- other records

TREE_PREFIX = re.compile(r"^((?:[ \t│├└┬┼─|`+]|--)*)")
TREE_NAME = r"[A-Za-z0-9_.@\[\]-][A-Za-z0-9_.@/\[\]-]*"


def tree_tokens(text, root=None):
    """Paths from trees in untagged or text fences. Box-drawing and indentation trees resolve each node
    against the nearest directory above it. The first line may name the project folder itself: it is the
    root when it matches the folder name, or when it does not exist here and every other line sits under it."""
    for match in re.finditer(r"(?ms)^(```|~~~)(?:text|plain|)[ \t]*\n(.*?)^\1", text):
        stack, first = [], True
        lines = [l for l in match.group(2).splitlines() if l.strip()]
        nested = len(lines) > 1 and all(len(TREE_PREFIX.match(l).group(1)) > 0 for l in lines[1:])
        for line in lines:
            prefix = TREE_PREFIX.match(line).group(1)
            col = len(prefix.expandtabs(4))
            rest = line[len(prefix):]
            token = rest.split(None, 1)[0] if rest.split() else ""
            described = re.match(rf"^({TREE_NAME})\s{{2,}}\S", rest)
            bare = re.fullmatch(rf"({TREE_NAME}(?:/|\.[A-Za-z0-9]{{1,8}}))\s*", rest)
            pattern = bool(token) and not re.fullmatch(TREE_NAME, token) and (token.endswith("/") or "*" in token
                                                                                or token.startswith(("<", "...", "…")))
            if not (described or bare or pattern):
                continue
            is_root = first and col == 0 and token.endswith("/") and (
                token.rstrip("/") in {getattr(root, "name", ""), "."}
                or (nested and root is not None and not (root / token).exists()))
            first = False
            while stack and stack[-1][0] >= col:
                stack.pop()
            if is_root:
                stack.append((col, ""))
                continue
            skip = pattern or any(name is None for _, name in stack)
            if token.endswith("/"):
                stack.append((col, None if skip else token))
            if not skip:
                yield "".join(name for _, name in stack[:-1] if name) + token if token.endswith("/") \
                    else "".join(name for _, name in stack if name) + token


def path_tokens(text, trees=False, root=None):
    body = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
    for token in re.findall(r"`([^`\n]+)`", body):
        token = token.strip()
        if "/" in token and re.fullmatch(r"[A-Za-z0-9_.@\-/\[\]]+", token) and not token.startswith(("/", "~", "-")):
            yield token
    if trees:
        yield from tree_tokens(text, root)


def is_path_like(root, token, strict):
    """STRUCTURE claims every path is local. BRAIN mixes local and backend paths,
    so only check BRAIN paths that clearly point inside the project."""
    first = token.split("/", 1)[0]
    has_file = re.search(r"\.[A-Za-z0-9]{1,8}$", token) and not token.endswith("/")
    if strict:
        return token.endswith("/") or has_file or (root / first).exists()
    return (root / first).exists() or has_file


def check_paths(root, name, text, add):
    for count, token in enumerate(path_tokens(text, trees=name == "STRUCTURE.md", root=root)):
        if count > 200:
            break
        if is_path_like(root, token, name == "STRUCTURE.md") and not (root / token).exists():
            add("error", "structure-missing-path", name, f"Path `{token}` does not exist.")


def check_links(root, name, text, add):
    for target in re.findall(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", strip_code(text)):
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith(("#", "<", "/")):
            continue
        clean = unquote(target.split("#", 1)[0])
        if clean and not (root / clean).exists():
            add("error", "broken-link", name, f"Link target `{clean}` does not exist.")


def top_level(root, top):
    names = set()
    if top:
        out = git(root, "ls-files", "-co", "--exclude-standard")
        if out is not None:
            names = {p.split("/", 1)[0] for p in out.splitlines() if p}
    if not names:
        try:
            names = set(os.listdir(root))
        except OSError:
            names = set()
    return sorted(n for n in names if not n.startswith(".") and n not in RECORD_FILES and n not in IGNORED_TOP)


def is_pointer(text):
    """A retired record kept only so existing links resolve: short, links PROGRESS.md, no table or log."""
    body = "\n".join(l for l in text.splitlines() if not l.startswith("#")).strip()
    return len(body) <= 400 and "PROGRESS.md" in body and "|" not in body and not re.search(rf"(?m)^##\s+{DATE}", text)


def codes_of(report):
    return {i["code"] for i in report["errors"] + report["warnings"]}


def check(root, top=None, fast=False, only=None, selected_text=None):
    root = Path(root).resolve()
    report = {"root": str(root), "records": [], "errors": [], "warnings": [], "info": {}}

    def add(level, code, file, message):
        report["errors" if level == "error" else "warnings"].append({"code": code, "file": file, "message": message})

    texts = {name: (read(root / name) if only is None else selected_text if name == only else None)
             for name in RECORDS + [LEGACY_PROGRESS] + SUPPORTING}
    report["records"] = [n for n in MARKERS if texts[n] is not None]
    progress_name = "PROGRESS.md"
    if texts["PROGRESS.md"] is not None and texts[LEGACY_PROGRESS] is not None:
        if is_pointer(texts[LEGACY_PROGRESS]):
            add("warning", "legacy-pointer", "STATUS.md",
                "STATUS.md only points to PROGRESS.md. Delete it once nothing links to it.")
        else:
            add("error", "two-progress-owners", "STATUS.md",
                "STATUS.md and PROGRESS.md both exist. Merge STATUS.md into PROGRESS.md, then delete it.")
    elif texts[LEGACY_PROGRESS] is not None:
        progress_name = LEGACY_PROGRESS
        add("warning", "legacy-status", "STATUS.md", "Legacy name. Migrate STATUS.md to PROGRESS.md (references/adopt.md).")
    report["info"]["progress_file"] = progress_name
    for name in RECORDS:
        if texts[name] is None and not (name == "PROGRESS.md" and progress_name == LEGACY_PROGRESS):
            add("error", "missing-record", name, f"{name} is missing.")
    if texts["ROADMAP.md"] is not None:
        add("warning", "legacy-roadmap", "ROADMAP.md", "Legacy file. Move live items to PROGRESS (Next or Later), then delete it.")

    for name, text in texts.items():
        if text is None:
            continue
        if "{{" in text and "}}" in text:
            add("warning", "placeholder", name, f"{text.count('{{')} template prompt(s) `{{{{...}}}}` remain.")
        if re.search(r"Working authority: this file must|Intended providers? \(cutover not verified\)", text):
            add("warning", "legacy-preamble", name, "Old provider-binding preamble. Remove it; keep only the substance.")
        if not fast:
            check_links(root, name, text, add)

    if texts["PROGRESS.md"] is not None:
        report["info"]["progress_updated"] = check_progress(texts["PROGRESS.md"], add)

    vision = texts["VISION.md"]
    if vision is not None:
        titles = list(sections(vision))
        missing = [label for key, label in VISION_CORE.items() if not any(key in t for t in titles)]
        legacy_hits = [key for key in VISION_LEGACY if any(key in t for t in titles)]
        if missing and len(legacy_hits) >= 3:
            add("warning", "vision-legacy-format", "VISION.md", "Older VISION format. Preserve it during routine maintenance. "
                "Revise only when the owner asks or agrees to a direction change (references/adopt.md).")
        elif missing:
            add("warning", "vision-section-missing", "VISION.md", "Missing core section(s): " + ", ".join(missing) + ".")
        prose = re.sub(r"(?m)^##\s+Direction changes.*?(?=^##\s|\Z)", "", vision, flags=re.S)
        if re.search(r"(?m)^(```|~~~)", prose) or any("/" in tok or re.search(r"\.[a-z]{1,5}$", tok)
                                                         for tok in re.findall(r"`([^`\n]+)`", prose)):
            add("warning", "vision-engineering-content", "VISION.md", "VISION holds code or file paths. It is a business and "
                "operating document; move engineering detail to STRUCTURE or a spec that BRAIN points to.")
        if not re.search(rf"Confirmed:\**\s*{DATE}", vision):
            add("warning", "vision-unconfirmed", "VISION.md", "No `Confirmed: YYYY-MM-DD`. The owner has not confirmed this vision.")
        questions = sections(vision).get("open questions", "")
        report["info"]["open_questions"] = len([l for l in questions.splitlines() if re.match(r"\s*[-*]\s+\S", l) and "{{" not in l
                                                    and not re.match(r"\s*[-*]\s+(none|n/a)\b", l, re.I)])

    brain = texts["BRAIN.md"]
    if brain is not None:
        home = re.search(r"(?m)^\**(?:Brain|Knowledge home)(?::\**|\**:)\s*(.*?)\s*(?:·|\||$)", brain)
        value = home.group(1).strip("*` ").lower() if home else ""
        report["info"]["knowledge_home"] = home.group(1).strip() if home else None
        has_none = value.startswith("none")
        if not home or (value in EMPTY and not has_none) or value.startswith("undefined") or "{{" in value:
            add("warning", "brain-home-undefined", "BRAIN.md", "No defined `Brain:` line (the knowledge home outside the "
                "repository). Add it from existing content; if none exists, run the knowledge-backend interview.")
        report["info"]["brain_providers"] = bool(home) and not has_none and "brain-home-undefined" not in codes_of(report)
        brain_sections = sections(brain)
        providers = next((b for k, b in brain_sections.items() if k.startswith("providers")), "")
        if report["info"]["brain_providers"] and not any(rows for _, rows in tables(providers)):
            add("warning", "brain-no-providers", "BRAIN.md", "BRAIN names a provider but has no Providers table "
                "(provider, root, access route, account and scope, verified).")
        inventory = next((b for k, b in brain_sections.items() if k.startswith("what lives")), "")
        local = [tok for tok in path_tokens(inventory) if (root / tok.split("/", 1)[0]).exists()]
        local += [l for l in re.findall(r"\]\(([^)\s:#]+)\)", inventory) if (root / unquote(l)).exists()]
        if local:
            add("warning", "brain-repo-item", "BRAIN.md", f"`{local[0]}` is in the repository. BRAIN lists knowledge "
                "outside the repository; map repository files in STRUCTURE.")

    if brain is not None:
        visibility = re.search(r"(?mi)^\**Visibility:?\**:?\s*(public|private)\b", brain)
        report["info"]["visibility"] = visibility.group(1).lower() if visibility else None
        if not visibility:
            add("warning", "brain-visibility-missing", "BRAIN.md", "No `Visibility: public|private` line.")
        elif visibility.group(1).lower() == "public":
            for name, text in texts.items():
                hits = [m.group(0) for pattern in PRIVATE_LOCATORS for m in re.finditer(pattern, text or "")]
                if hits:
                    add("error", "private-locator", name, f"Public repository exposes a private locator: {hits[0][:60]}")

    for name in ("STRUCTURE.md", "BRAIN.md"):
        if texts[name] is not None:
            text = texts[name]
            if name == "STRUCTURE.md":
                text = re.sub(r"(?ms)^##\s+Brain\b.*?(?=^##\s|\Z)", "", text)
            check_paths(root, name, text, add)
    if texts["STRUCTURE.md"] is not None and report["info"].get("brain_providers") \
            and not any(k.startswith("brain") for k in sections(texts["STRUCTURE.md"])):
        add("warning", "structure-no-brain-map", "STRUCTURE.md", "BRAIN names a provider, but STRUCTURE has no `## Brain` "
            "section mapping its folders and key documents.")
    if texts["STRUCTURE.md"] is not None and not fast:
        structure = texts["STRUCTURE.md"]
        for entry in top_level(root, top if top is not None else git_top(root)):
            if not re.search(r"(?<![\w.-])" + re.escape(entry) + r"(?![\w-])", structure):
                add("warning", "structure-unmentioned", "STRUCTURE.md", f"Top-level entry `{entry}` is not mentioned.")

    if texts["TECHSTACK.md"] is None and report["records"]:
        add("warning", "techstack-missing", "TECHSTACK.md", "No TECHSTACK.md. Inventory tools, stack, resources and integrations from evidence; mark unknowns.")

    readme = texts["README.md"]
    if readme is None and report["records"]:
        add("warning", "readme-missing", "README.md", "No README.md. Write it from VISION (a cut-down pitch) and the install steps.")
    elif readme is not None and not any(re.match(r"(install|get(ting)? started|set ?up|use|usage|access|quick ?start|run)", k)
                                        for k in sections(readme)):
        add("warning", "readme-no-install", "README.md", "README has no Install, Get started, Setup, Use, or Access section.")
    progress_text = texts.get(progress_name)
    if texts["CHANGELOG.md"] is None and progress_text and shipped_items(progress_text):
        add("warning", "changelog-missing", "CHANGELOG.md", "PROGRESS records shipped work, but there is no CHANGELOG.md. "
            "Create it with what reached people.")

    for name, label in (("README.md", "README"), ("AGENTS.md", "AGENTS")):
        text = texts[name]
        if text is None or (name == "AGENTS.md" and root == Path.home()):
            continue
        wanted = [n if n != "PROGRESS.md" else progress_name for n in RECORDS]
        absent = [n for n in wanted if n not in text]
        if absent:
            add("warning", "entry-links", name, f"{label} does not link: " + ", ".join(absent) + ".")

    if texts["PROGRESS.md"] is None:
        # Legacy records predate the "backticked paths are root-relative" rule. Report their path and link
        # problems as warnings so orientation stays accurate; migration turns them into errors to fix.
        for item in [e for e in report["errors"] if e["code"] in ("structure-missing-path", "broken-link")]:
            report["errors"].remove(item)
            report["warnings"].append(dict(item, message=item["message"] + " (legacy record; fix during migration)"))

    changelog = texts["CHANGELOG.md"]
    if changelog is not None:
        for heading in re.findall(r"(?m)^##\s+(.*)$", changelog):
            for found in re.findall(DATE, heading):
                if found > today():
                    add("error", "changelog-future-date", "CHANGELOG.md", f"Entry dated {found} is in the future.")
            if "unreleased" in heading.lower():
                add("warning", "changelog-planned-words", "CHANGELOG.md", "Unreleased section. Unshipped work belongs in PROGRESS.")
        for line in changelog.splitlines():
            if not line.startswith("#") and re.search(r"(?i)\b(planned|upcoming|coming soon|will (add|ship|support)|wip|todo|in progress)\b", line):
                add("warning", "changelog-planned-words", "CHANGELOG.md", f"Possible unshipped work: \"{line.strip()[:80]}\".")
                break
    if only is not None:
        report['errors'] = [item for item in report['errors'] if item['file'] == only]
        report['warnings'] = [item for item in report['warnings'] if item['file'] == only]
    return report


def commits_since(root, name):
    """Work commits after the last commit that changed the PROGRESS record.
    Uncommitted PROGRESS edits count as current."""
    if (git(root, "status", "--porcelain", "--", name) or "").strip():
        return 0, today()
    last = git(root, "log", "-1", "--format=%H %cs", "--", name)
    if not last or not last.strip():
        return None
    sha, when = last.split()
    out = git(root, "log", "--no-merges", "--relative", "--name-only", "--format=@@%H", f"{sha}..HEAD", "--", ".")
    if out is None:
        return None
    count = 0
    for block in out.split("@@")[1:]:
        files = block.split("\n")[1:]
        if any(f and f not in RECORD_FILES for f in files):
            count += 1
    return count, when


# ---------------------------------------------------------------- hooks

def state_dir():
    path = Path(os.environ.get("HORSEMEN_STATE_DIR") or Path(tempfile.gettempdir()) / "horsemen-hooks")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def state_path(payload, root):
    identity = payload.get("session_id") or payload.get("transcript_path") or "project-fallback"
    key = json.dumps([str(root), str(identity)])
    return state_dir() / (hashlib.sha256(key.encode()).hexdigest() + ".json")


def load_state(path, root):
    try:
        state = json.loads(read(path) or "null")
    except ValueError:
        return None
    if not isinstance(state, dict) or state.get("version") != CACHE_VERSION or state.get("root") != str(root):
        return None
    if not isinstance(state.get("hashes"), dict) or type(state.get("time")) is not int \
            or not isinstance(state.get("reminded"), dict) or not isinstance(state.get("shipped"), list):
        return None
    if type(state.get("git")) is not bool or any(value is not None and not isinstance(value, str)
                                                for value in state["hashes"].values()):
        return None
    if any(state.get(name) is not None and not isinstance(state[name], str)
           for name in ("head", "structure_hash", "changelog_hash")):
        return None
    if any(not isinstance(item, str) for item in state["shipped"]):
        return None
    dirs = state.get("dirs")
    if dirs is not None and (not isinstance(dirs, list) or any(not isinstance(item, str) for item in dirs)):
        return None
    return state


def save_state(path, state):
    """Replace a disposable cache atomically; never block the workflow on it."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".horsemen-", delete=False) as handle:
            temporary = Path(handle.name)  # NamedTemporaryFile creates mode 0600.
            json.dump(state, handle)
        os.replace(temporary, path)
    except OSError:
        pass
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def record_hashes(root):
    return {name: digest(read(root / name)) for name in sorted(RECORD_FILES)}


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def clip(lines, budget):
    """Keep whole lines within a character budget. Returns (kept, complete)."""
    kept, size = [], 0
    for line in lines:
        if size + len(line) + 1 > budget:
            return kept, False
        kept.append(line)
        size += len(line) + 1
    return kept, True


def orient(root, top):
    report = check(root, top, fast=True)
    progress_name = report["info"]["progress_file"]
    present = report["records"]
    lines = [f"Horsemen records for {root}: " + ", ".join(present) + "."]
    lines.append("Before acting, respect the gates and constraints below. Read VISION.md, BRAIN.md, or the rest of "
                 "STRUCTURE.md when the task needs direction, knowledge, or locations. Before finishing each task, use horsemen "
                 "to review all four records silently, including work outside Git. Keep unchanged records and dates unchanged. "
                 "Do not replace the actual task report with skill maintenance; report it only if asked, or for necessary permission questions and actionable blockers.")
    incomplete = []
    text = read(root / "PROGRESS.md")
    if text is not None:
        snapshot, _ = split_progress(text)
        rows = snapshot.strip().splitlines()
        shown, complete = clip(rows[:SNAPSHOT_LINES], SNAPSHOT_CHARS)
        lines += ["", "PROGRESS.md snapshot:", *shown]
        if not complete or len(rows) > SNAPSHOT_LINES:
            incomplete.append("PROGRESS.md snapshot (latest day, or legacy content above the first dated heading)")
    elif progress_name == LEGACY_PROGRESS:
        lines += ["", "Status lives in legacy STATUS.md (old format, not injected). Read it before project work: it holds "
                      "the current gates, blockers, and next actions. Migrate it to PROGRESS.md with the horsemen skill when status next changes."]
    structure = read(root / "STRUCTURE.md")
    if structure is not None:
        first = next((body for title, body in sections(structure).items() if title.startswith("read before")), None)
        if first and first.strip():
            body = first.strip().splitlines()
            kept, complete = clip(body, READ_FIRST_CHARS)
            lines += ["", "STRUCTURE.md, read before changing:", *kept]
            if not complete:
                incomplete.append("the STRUCTURE.md 'Read before changing' section")
    if incomplete:
        lines.append("Injected text is incomplete. Read the rest of " + " and ".join(incomplete) + " before acting.")
    health = []
    if top:
        since = commits_since(root, progress_name)
        if since and since[0]:
            health.append(f"{plural(since[0], 'commit')} since {progress_name} last changed ({since[1]}).")
    ranked = ("two-progress-owners", "private-locator", "missing-record", "progress-details-unclosed", "progress-state-unknown",
              "progress-shipped-no-evidence", "progress-table-columns", "progress-updated-missing", "progress-no-state-table",
              "structure-missing-path", "brain-home-undefined", "vision-unconfirmed", "progress-legacy-format", "vision-legacy-format",
              "legacy-preamble", "placeholder", "legacy-roadmap")
    items = report["errors"] + report["warnings"]
    for code in ranked:
        hits = [i for i in items if i["code"] == code]
        if not hits:
            continue
        if code == "structure-missing-path":
            paths = ", ".join(re.findall(r"`([^`]+)`", " ".join(h["message"] for h in hits))[:4])
            health.append(f"{plural(len(hits), 'missing path')} named in STRUCTURE.md or BRAIN.md: {paths}.")
        elif code == "missing-record":
            health.append("Missing records: " + ", ".join(h["file"] for h in hits) + ".")
        elif code in ("legacy-preamble", "placeholder"):
            health.append(f"{hits[0]['message'].rstrip('.')} ({', '.join(sorted({h['file'] for h in hits}))}).")
        else:
            health.append(f"{hits[0]['file']}: {hits[0]['message']}")
    if report["info"].get("open_questions"):
        health.append(f"VISION.md lists {plural(report['info']['open_questions'], 'open question')}.")
    if health:
        lines += ["", "Record health:"] + [f"- {h[:240]}" for h in health[:6]]
        lines.append(f"Full report: python3 {Path(__file__).resolve()} check")
    return "\n".join(lines)


def session_start(payload):
    cwd = Path(payload.get("cwd") or os.getcwd())
    root, top = find_root(cwd)
    if root is None:
        if top:
            return emit_context("No horsemen records (VISION, BRAIN, PROGRESS, STRUCTURE) in this repository. "
                                "If the user starts substantial project work, offer to set them up with the horsemen skill; do not create them unasked.")
        return None
    try:
        path = state_path(payload, root)
        if load_state(path, root) is None or payload.get("source") in ("startup", "clear"):
            head = git(root, "rev-parse", "HEAD") if top else None
            state = {"version": CACHE_VERSION, "root": str(root), "git": bool(top), "head": head.strip() if head else None,
                     "time": int(time.time()), "hashes": record_hashes(root),
                     "shipped": sorted(shipped_items(read(root / "PROGRESS.md"))), "reminded": {}}
            if top and state["head"]:
                listing = git(root, "ls-files", "-co", "--exclude-standard")
                if listing is not None:
                    state["dirs"] = sorted(dirs_of(listing.splitlines()))
            save_state(path, state)
        prune_state()
    except OSError:
        pass  # Orientation and task review do not depend on a writable cache.
    return emit_context(orient(root, top))


def emit_context(text):
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}


def prune_state():
    cutoff = time.time() - 7 * 86400
    for item in state_dir().glob("*.json"):
        try:
            if item.stat().st_mtime < cutoff:
                item.unlink()
        except OSError:
            pass


def dirs_of(paths):
    found = set()
    for p in paths:
        parts = p.split("/")[:-1]
        if parts:
            found.add(parts[0])
        if len(parts) >= 2:
            found.add(parts[0] + "/" + parts[1])
    return found


def stop(payload):
    if payload.get("stop_hook_active"):
        return None
    cwd = Path(payload.get("cwd") or os.getcwd())
    root, top = find_root(cwd)
    if root is None:
        return None
    try:
        path = state_path(payload, root)
        state = load_state(path, root)
    except OSError:
        state = None
    if state is None:
        return completion_reminder([])
    base_hashes = state["hashes"]
    now = record_hashes(root)
    reminded = state.setdefault("reminded", {})
    notes = []
    progress_name = "PROGRESS.md" if (root / "PROGRESS.md").exists() or not (root / LEGACY_PROGRESS).exists() else LEGACY_PROGRESS
    changed = [n for n in now if now[n] != base_hashes.get(n)]

    if state.get("git") and state.get("head") and top:
        base = state["head"]
        is_ancestor = git(root, "merge-base", "--is-ancestor", base, "HEAD") is not None
        if is_ancestor:
            count = work_commits(root, base, progress_name, state["time"] - 120)
            dirty = (git(root, "status", "--porcelain", "--", progress_name) or "").strip()
            fingerprint = f"{count}:{now.get(progress_name)}"
            if count and not dirty and reminded.get("progress") != fingerprint:
                reminded["progress"] = fingerprint
                notes.append(f"Progress: {plural(count, 'work commit')} since {progress_name} last changed. Update {progress_name} "
                             "from evidence; leave it unchanged when no update is needed.")
        if state.get("dirs") is not None:
            current = git(root, "ls-files", "-co", "--exclude-standard")
            if current is not None:
                after = dirs_of(current.splitlines())
                before = set(state["dirs"])
                added, removed = sorted(after - before), sorted(before - after)
                fingerprint = "|".join(added) + "/" + "|".join(removed)
                if now.get("STRUCTURE.md") != state.get("structure_hash", base_hashes.get("STRUCTURE.md")):
                    # STRUCTURE was repaired: the current tree becomes the new baseline, so later moves re-arm the rule.
                    state["structure_hash"], state["dirs"] = now.get("STRUCTURE.md"), sorted(after)
                elif (added or removed) and reminded.get("structure") != fingerprint:
                    reminded["structure"] = fingerprint
                    parts = []
                    if added:
                        parts.append("added " + ", ".join(added[:6]))
                    if removed:
                        parts.append("removed " + ", ".join(removed[:6]))
                    notes.append(f"Structure: folders {'; '.join(parts)} since session start, but STRUCTURE.md did not change. "
                                 "Update its map and any moved knowledge locations in BRAIN.md.")

    shipped_now = shipped_items(read(root / "PROGRESS.md"))
    new_shipped = sorted(shipped_now - set(state.get("shipped", [])))
    if now.get("CHANGELOG.md") != state.get("changelog_hash", base_hashes.get("CHANGELOG.md")):
        # CHANGELOG was updated: everything shipped so far is covered; a later Shipped row re-arms the rule.
        state["changelog_hash"], state["shipped"] = now.get("CHANGELOG.md"), sorted(shipped_now)
    elif new_shipped and reminded.get("changelog") != new_shipped:
        reminded["changelog"] = new_shipped
        action = "did not change. Add" if now.get("CHANGELOG.md") else "does not exist. Create it and add"
        notes.append("Changelog: PROGRESS.md marks " + ", ".join(f'"{s[:50]}"' for s in new_shipped[:3]) +
                     f" as shipped, but CHANGELOG.md {action} what reached people (only the shipped part of a partly shipped item), "
                     "or correct the status if it has not reached them.")

    if "VISION.md" in changed and ("vision" not in reminded or reminded["vision"] != now.get("VISION.md")):
        reminded["vision"] = now.get("VISION.md")
        notes.append("Vision: VISION.md changed. Check README.md, PROGRESS.md (Next, Later), and BRAIN.md for conflicts, "
                     "and log the agreed direction change. Ask only if the owner's intent is unclear.")

    if changed:
        report = check(root, top, fast=True)
        errors = [f"{e['file']}: {e['message']}" for e in report["errors"] if e["file"] in changed]
        fingerprint = digest("\n".join(errors))
        if errors and reminded.get("lint") != fingerprint:
            reminded["lint"] = fingerprint
            notes.append("Record errors: " + " ".join(errors[:5]))

    save_state(path, state)
    return completion_reminder(notes)


def completion_reminder(notes):
    reason = ("Horsemen: before finishing this task, review VISION, BRAIN, PROGRESS, and STRUCTURE, including work outside Git. "
              "Honor read-only commands: plain inspect and check report proposed changes without writing. Keep VISION unless the user requested or agreed to a direction change. Use BRAIN's saved destinations and "
              "permissions: update originals; bin stale copies only when authorized. Write PROGRESS in plain words; fix "
              "STRUCTURE when locations change. Check README, CHANGELOG, and TECHSTACK if affected. Proactively open relevant brain originals; check freshness, "
              "links, and duplicates. Update or archive only when authorized; preserve history and report unsaved blockers. If nothing changed, leave files and "
              "dates alone. Shipped needs delivery evidence. Do this silently; do not narrate the review or add a Horsemen "
              "section to the task report unless asked. Still surface necessary permission questions and actionable blockers.")
    if notes:
        budget = (1180 - len(reason) - len(notes) * 3) // len(notes)
        reason += "\n" + "\n".join("- " + (note if len(note) <= budget else note[:budget - 1] + "…") for note in notes)
    return {"decision": "block", "reason": reason}


def work_commits(root, base, progress_name, since):
    out = git(root, "log", "--no-merges", "--relative", "--name-only", "--format=@@%H %ct", f"{base}..HEAD", "--", ".")
    if not out:
        return 0
    count = 0
    for block in out.split("@@")[1:]:
        lines = block.split("\n")
        header, files = lines[0].split(), [f for f in lines[1:] if f]
        if progress_name in files:
            break
        if len(header) == 2 and int(header[1]) >= since and any(f not in RECORD_FILES for f in files):
            count += 1
    return count


def run_hook(event):
    global DEADLINE
    DEADLINE = time.monotonic() + HOOK_BUDGET
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        result = session_start(payload) if event == "session-start" else stop(payload) if event == "stop" else None
        if result:
            sys.stdout.write(json.dumps(result))
    except Exception:  # A hook must never break the host session.
        if os.environ.get("HORSEMEN_DEBUG"):
            raise
    return 0


# ---------------------------------------------------------------- installer

def find_python():
    """An absolute python3 that is not the macOS /usr/bin stub (which can open an install dialog)."""
    for candidate in (shutil.which("python3"), "/opt/homebrew/bin/python3", "/usr/local/bin/python3",
                      "/Library/Developer/CommandLineTools/usr/bin/python3"):
        if candidate and candidate != "/usr/bin/python3" and os.access(candidate, os.X_OK):
            return candidate
    return "/usr/bin/python3" if sys.platform != "darwin" else ""


def hook_command(script, event, python=None):
    python = python if python is not None else find_python()
    if "'" in str(script) + python:
        raise SystemExit("The script and python paths must not contain a single quote.")
    order = dict.fromkeys(p for p in [python, "/opt/homebrew/bin/python3", "/usr/local/bin/python3",
                                      "/Library/Developer/CommandLineTools/usr/bin/python3"] if p)
    candidates = " ".join(f'"{p}"' for p in order)
    return (f"/bin/sh -c 'f=\"{script}\"; [ -f \"$f\" ] || exit 0; for p in {candidates}; do "
            f"[ -x \"$p\" ] && exec \"$p\" \"$f\" hook {event}; done; exit 0'")


def is_ours(hook):
    command = str(hook.get("command", ""))
    return HOOK_MARK in command and " hook " in command


def hook_target(command):
    match = re.search(r'\bf="([^"]+)"', command)
    if match:
        return Path(match.group(1)).expanduser()
    try:
        return next((Path(part).expanduser() for part in shlex.split(command) if part.endswith("horsemen.py")), None)
    except ValueError:
        return None


def strip_ours(config):
    hooks = config.setdefault("hooks", {})
    for event in list(hooks):
        kept = []
        for entry in hooks[event]:
            entry["hooks"] = [h for h in entry.get("hooks", []) if not is_ours(h)]
            if entry["hooks"]:
                kept.append(entry)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    return config


def load_json(path):
    text = read(path)
    return json.loads(text) if text and text.strip() else {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + ".horsemen-backup")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    mode = (path.stat().st_mode & 0o777) if path.exists() else 0o600  # Settings can hold tokens: never widen access.
    tmp = path.with_name(path.name + ".horsemen-tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(json.dumps(data, indent=2) + "\n")
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def hooks_cli(args):
    import argparse
    parser = argparse.ArgumentParser(prog="horsemen.py hooks")
    parser.add_argument("action", choices=["install", "uninstall", "status"])
    parser.add_argument("--claude-settings", type=Path, default=Path.home() / ".claude" / "settings.json")
    parser.add_argument("--codex-hooks", type=Path, default=Path.home() / ".codex" / "hooks.json")
    parser.add_argument("--script-path", type=Path, default=Path.home() / ".agents" / "skills" / "horsemen" / "scripts" / "horsemen.py")
    parser.add_argument("--only", choices=["claude", "codex"])
    opts = parser.parse_args(args)
    healthy = True
    targets = [("claude", opts.claude_settings), ("codex", opts.codex_hooks)]
    targets = [t for t in targets if not opts.only or t[0] == opts.only]
    if opts.action == "install" and not opts.script_path.is_file():
        print(f"Installed skill script not found: {opts.script_path}. Install the skill first or pass --script-path.", file=sys.stderr)
        return 1
    for host, path in targets:
        config = load_json(path)
        if opts.action == "status":
            events = {event: [h["command"] for entry in entries for h in entry.get("hooks", []) if is_ours(h)]
                      for event, entries in config.get("hooks", {}).items()}
            ours = [command for commands in events.values() for command in commands]
            print(f"{host}: {path} -> {len(ours)} horsemen hook(s)")
            for event in ("SessionStart", "Stop"):
                if len(events.get(event, [])) != 1:
                    print(f"  {event}: expected 1 hook, found {len(events.get(event, []))}")
                    healthy = False
            for command in dict.fromkeys(ours):
                target = hook_target(command)
                if target is None or not target.is_absolute():
                    print("  Script: cannot verify target")
                    healthy = False
                else:
                    exists = target.is_file()
                    print(f"  Script: {target} ({'present' if exists else 'missing'})")
                    healthy = healthy and exists
            continue
        if opts.action == "uninstall" and not path.exists():
            continue
        strip_ours(config)
        if opts.action == "install":
            hooks = config.setdefault("hooks", {})
            for event, name in (("SessionStart", "session-start"), ("Stop", "stop")):
                hooks.setdefault(event, []).append({"hooks": [{"type": "command", "command": hook_command(opts.script_path, name), "timeout": 5}]})
        save_json(path, config)
        print(f"{opts.action}ed horsemen hooks: {host} ({path})")
    if opts.action == "install" and any(t[0] == "codex" for t in targets):
        print("Codex asks you to trust new hooks before they run. Approve them in Codex.")
    return 0 if healthy else 1


# ---------------------------------------------------------------- CLI

def print_report(report):
    print(f"Horsemen check: {report['root']}")
    for kind in ("errors", "warnings"):
        if report[kind]:
            print(f"{kind.capitalize()} ({len(report[kind])})")
            for item in report[kind]:
                print(f"  {item['file']:<13} {item['message']}  [{item['code']}]")
    info = report["info"]
    facts = []
    if info.get("progress_updated"):
        facts.append(f"PROGRESS updated {info['progress_updated']}")
    if info.get("open_questions") is not None:
        facts.append(f"VISION open questions: {info['open_questions']}")
    if info.get("knowledge_home"):
        facts.append(f"Brain: {info['knowledge_home']}")
    if info.get("commits_since_progress") is not None:
        facts.append(f"Commits since PROGRESS changed: {info['commits_since_progress']}")
    if facts:
        print("; ".join(facts))
    print("Result: " + ("errors found" if report["errors"] else "no errors"))


def main(argv):
    if len(argv) >= 2 and argv[0] == "hook":
        return run_hook(argv[1])
    if argv and argv[0] == "hooks":
        return hooks_cli(argv[1:])
    if argv and argv[0] == "check":
        rest = [a for a in argv[1:] if a != "--json"]
        start = Path(rest[0]) if rest else Path.cwd()
        root, top = find_root(start)
        report = check(root or start, top)
        since = commits_since(root or start, report["info"]["progress_file"]) if top else None
        report["info"]["commits_since_progress"] = since[0] if since else None
        if "--json" in argv:
            print(json.dumps(report, indent=2))
        else:
            print_report(report)
        return 1 if report["errors"] else 0
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
