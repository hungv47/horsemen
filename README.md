# Horsemen

**Pick up a project without reconstructing it from old chats.**

Horsemen keeps four Markdown records useful: why the project exists, what has
shipped, where its knowledge lives, and where to find its parts. It works for
software, business, research, and personal projects.

One project, two ways to use it:

| Use the agent skill to… | Use the CLI to… |
| --- | --- |
| Gather context and maintain records with your agent | Check records and inspect a local project |
| Review connected sources within your existing access | Prepare a change plan and export a review patch |
| Preserve your direction and update the right originals | Get repeatable results without an AI model or account |

Both use the same checker. The CLI has no runtime dependencies beyond Python
3.10+ and optional Git. It does **not** change project documents or contact
outside services. Agent workflows can make changes within your instructions.

## Install the agent skill

Install the skill from this repository using a compatible skills installer:

```sh
bunx skills@1.7.0 add hungv47/horsemen --skill horsemen --copy
```

Select the intended agent and installation scope. In a fresh agent session:

```text
Use Horsemen to inspect this project. Keep this review read-only.
```

For a new project, ask: `Use Horsemen to initialize this project.` Your agent
uses existing evidence and asks for missing direction and knowledge locations.
It must not invent them. [Skill instructions](horsemen/SKILL.md).

## Install the CLI

Clone this repository and install into an isolated environment:

```sh
git clone https://github.com/hungv47/horsemen.git
cd horsemen
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/horsemen inspect /path/to/project
.venv/bin/horsemen check /path/to/project --json
```

This does not install the agent skill or change host hooks. To run without
installation: `PYTHONPATH=horsemen/scripts python3 -B -m horsemen_core --help`.

## What stays with your project

| Record | Question |
| --- | --- |
| VISION.md | Why does this project exist? |
| PROGRESS.md | What shipped, what waits, and what comes next? |
| BRAIN.md | Where is outside knowledge, and how may we use it? |
| STRUCTURE.md | Where is everything? |

README, CHANGELOG, and TECHSTACK support these records. Existing provider
originals remain the source of truth; Horsemen does not create a second store.

## Status and limits

This is an **alpha**. Plans and exported patches are for review; they do not
authorize or apply changes. Local inspection does not check remote pull
requests, releases, or provider contents. Automatic Drive saves and automatic
patch application are not available. Linux and macOS are the test targets;
Windows planning and patch export are unsupported.

- [CLI commands and examples](horsemen/CLI.md)
- [Skill and CLI differences](horsemen/references/cli.md)
- [Develop and verify both interfaces](CONTRIBUTING.md)
- [Current progress](PROGRESS.md) · [MIT license](LICENSE)
