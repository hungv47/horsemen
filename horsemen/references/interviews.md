# Interviews

Both interviews follow the same loop: extract what exists, score the gaps,
ask only about the gaps, write, and confirm. Use the host's question tool when
it has one (for example `AskUserQuestion` or `request_user_input`); otherwise
ask in chat. Ask at most three questions per round, and offer concrete
options drawn from the evidence wherever possible. When there is no evidence,
offer two or three common answers for the project type as examples, plus
"Not decided yet", which records the element as an open question.

Reuse answers already given. If nobody answers a required setup question,
leave only the dependent choice unresolved; continue work that does not
need it. Do not invent intent, a provider, or permission. See SKILL.md
(Initialize) for a new record's draft rule. A missing filing detail in an
existing setup does not reopen the whole interview.

## Vision discovery

### 1. Extract

Read the request, the conversation, README, existing VISION, PROGRESS, docs,
issues, and documents that BRAIN links. For each element below, write a draft
answer with its source and a score:

| Score | Meaning |
| --- | --- |
| Solid | Specific, and stated or confirmed by the owner |
| Weak | Vague, generic, or inferred by you |
| Conflicting | Two sources disagree |
| Missing | No evidence |

Elements, in priority order:

1. The declaration: what the owner believes should be true, and what the
   project builds to make it true, in two or three sentences
2. Why we exist: the problem, what it costs people today, and why now
3. The world we are building: the end state, told as if it already happened
4. Who we build for: the exact people, why they choose this, and who it is not for
5. What we believe: the convictions that decide trade-offs
6. How we get there: Now, Next, and Later, each with a signal
7. What we will never become
8. How it sustains itself (only when money or time is a real constraint)

The goal is a manifesto the owner would read out loud: the root of the
project and the grand picture, not a feature plan. Dig until you reach the
reason behind the first answer. "A notes app for consultants" is a product;
"no consultant should lose an evening to paperwork" is a mission.

If every element is Solid, skip the interview. Show the draft and ask for one
confirmation.

### 2. Ask

Work down the list, Conflicting and Missing first, then Weak. Prefer a
confirmation question with your draft ("I read the main outcome as X, based
on Y. Correct?") over an open question.

Challenge an answer when it shows one of these signs:

| Sign | Follow-up |
| --- | --- |
| Generic audience ("users", "everyone", "businesses") | "Name one real person or segment who has this problem today." |
| No current behavior | "What do they do today instead? What does that cost them?" |
| Solution stated as the problem ("we need an app") | "What problem would the app solve? How would you know it is solved?" |
| Several equal priorities | "If only one of these happens in six months, which one?" |
| A feature list instead of a picture | "When this works, what is different for the people you serve? What is the business then?" |
| A product, not a mission | "Why does this need to exist? What would be wrong with the world if nobody built it?" |
| No conviction | "What do you believe about this problem that most people in the space get wrong?" |
| No money or time model | "Who pays, how much, and what does it cost to run? If nobody pays, whose time keeps it alive?" |
| No route to people | "How do the first ten users find it? How do the next thousand?" |
| Buzzwords ("seamless", "scalable", "AI-powered", "best") | "What would a user see or measure that proves that?" |
| No boundary | "What will you refuse to do, even if a customer asks?" |
| Idea or commitment unclear | "Is this decided, or an idea you want to test?" |
| No signal | "What would tell you in 30 days that this direction is wrong?" |

Add the questions for the project type:

| Type | Ask about |
| --- | --- |
| Software product | Who pays or decides, the main job to be done, pricing, the first proving horizon |
| Business initiative | The business result, the owner, the budget and deadline |
| Growth experiment | Hypothesis, metric, success threshold, duration, kill criteria |
| Research | The question, the decision it informs, the evidence standard |
| Personal | Why it matters to you, constraints (time, money), what "enough" looks like |

### 3. Stop

Stop when each element is Solid or recorded as an Open question with a
decider. Usually one to three rounds. If the user says "enough", stop at once
and record the remaining gaps as open questions. Never fill a gap with a
plausible guess.

### 4. Write and confirm

Write VISION from the template. Confirmed answers go in the main sections,
inferences in Bets, unknowns in Open questions. Read the declaration back to
the owner in their own words and ask: "Is this what you would say to a
partner?" Show the user a short
summary of each class. After the owner agrees, set `Confirmed:` to today. An
agent-drafted VISION without agreement says `Confirmed: not yet`.

### Direction changes later

When the user requests a VISION revision or agrees to a direction change:
reuse that agreement, state the old and new direction in one line each,
ask only if intent is still unclear, update VISION, add a dated Direction changes
line, then review README, PROGRESS (`Up next`, Roadmap), and BRAIN for items that
the new direction makes wrong. Ask before you drop a committed item.

## Providers

A provider is an outside service that plays a role for the project. Every
project answers two roles; add others only when the project needs them.

| Role | Holds | Examples |
| --- | --- | --- |
| Brain | Knowledge outside the repository: research, decks, media, decisions | Google Drive, Notion, Confluence, an Obsidian vault |
| Task tracking | Task-level work below PROGRESS | Linear, Jira, GitHub Issues |
| Other (only if needed) | Design files, data, CRM, analytics | Figma, a warehouse, HubSpot |

PROGRESS stays the project-level view for stakeholders; the task tracker holds
the task detail, and PROGRESS links it in a Technical details toggle.

### 1. Inspect

Before you ask anything, find what already exists:

- The user's global instructions: default providers (for example "Drive for
  the brain, Linear for tasks") and any private project registry.
- BRAIN.md, `docs/`, notes folders, decision records.
- Saved setup answers and permissions, including exact filing destinations
  and an existing bin or archive. Treat a prior verified access date as
  dated evidence, not proof that access still works.
- Links in the records and README to Drive, Notion, Confluence, Linear, Jira,
  or other tools.
- The tools available in this session (connectors, MCP servers, CLIs) and
  whether each can read and write.
- Whether the repository is public or private.

If a working setup exists, describe it back and ask only what is unclear.
Do not recommend a migration without a concrete problem to solve.

### 2. Ask

Ask per role, and only what the inspection did not answer. When the global
instructions name a default provider, ask only the questions it leaves open
(usually 3 and 4).

1. Which provider plays this role? (recommended: the user's default)
2. Who reads and edits it? (you and agents / a team / clients / the public)
3. Which folder, space, or tracker project belongs to this project? Offer the
   candidates you found.
4. May agents save or create items automatically, only after asking, or never?
5. What privacy limits apply? (employer data, personal data, a public repository)
6. For the brain only: what kinds of knowledge, and how much? (decisions,
   research, meeting notes, specs, large binary files)
7. For each kind that needs saving, which exact document and section, folder,
   or parent page should agents update? When may they create a new document?
   Offer the originals and filing map found during inspection.
8. Where is the project's `bin`, and may agents move confirmed stale copies
   there automatically? Use the existing recovery archive if one is already
   agreed; do not create a second one. Keep deletion as a separate choice.

Ask these in rounds only when their answers change the work. Record the
answers in BRAIN, including the source or date of the user's choice. Do not
leave filing or cleanup permissions only in the interview transcript.

### 3. Recommend

When the user has no default, score the candidates against the answers and
recommend one provider per role, with a short reason. One kind of knowledge
has one canonical home.

| Criterion | Question |
| --- | --- |
| Human access | Can every reader open and edit it easily? |
| Agent access | Is there a working connector, CLI, API, or local file path in this environment? |
| Discoverability | Can people and agents search it? |
| Maintenance | Who keeps it organized? |
| Cost | Is it already paid for? |
| Privacy | Does it keep data in the right account and scope? |
| Binary files | Does it store large media and exports? (brain) |

Common fits:

| Profile | Brain | Task tracking |
| --- | --- | --- |
| Solo software project, private repository | The repository itself (`Brain: None`), or a drive for large files | GitHub Issues or the user's tracker |
| Public repository | Private backend, referenced by a neutral key | Private tracker |
| Team with non-technical members | Google Drive, Notion, or Confluence | Linear, Jira, or Asana |
| Personal, note-heavy work | A local Markdown vault (for example Obsidian) | PROGRESS alone, or a light tracker |
| Organization on Atlassian | Confluence | Jira |

Memory and recall tools (for example GBrain or Mem0) are search aids. They are
never the canonical home: an agent opens the original before it relies on a
recalled fact.

### 4. Record and verify

1. Write BRAIN: the `Brain:` line, one Providers row per role (role,
   provider, root or tracker project, access route, account and scope,
   verified date), what lives in the brain, save rules, and access-problem
   rules. In Save, name each kind's exact destination and when a new item is
   allowed. Record write permission and the bin location, recovery index,
   and move permission. Mark unknown choices `Not decided`, with what they
   prevent. List nothing that lives in the repository.
2. Write the STRUCTURE brain map: one subsection per brain provider, with its
   folder tree, the key documents, and the command or link that opens it.
   Link the tracker project from PROGRESS.
3. Verify access per provider: read one existing item (a file, a page, an
   issue in the tracker project). Only then fill its Verified date. A read
   does not prove write permission or cloud sync; do not test by creating
   throwaway documents in the brain.
4. If access fails, record the provider with `access not verified` and stop.
   Do not switch to another account or provider.

## Quick interview

Use this for an ambiguous update along the way (triggers in SKILL.md, "When
to interview"). It is one round, not a full interview.

1. State what you found and why it is ambiguous, in one or two sentences,
   with the evidence.
2. Ask at most three questions, each with options: the recommended answer
   first, one or two alternatives, and "Not decided yet".
3. Write the answer into the owning record with today's date. VISION changes
   also get a Direction changes line. "Not decided yet" becomes an Open
   question with who decides.

Example: a migration finds that Drive holds only an archive, but BRAIN says it
holds research.

> BRAIN says the research for this project is in Drive, but the Drive folder
> holds only an archive (checked today). Where does the research live?
> - It never existed; remove the claim (recommended)
> - It lives elsewhere: I will name the place
> - Not decided yet
