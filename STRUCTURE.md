# Structure

One repository owns the agent skill, CLI, shared checks, and release verification.

## Map

```text
horsemen/
├── assets/                 README cover and provenance notes
├── horsemen/               Installable agent skill
│   ├── SKILL.md            Agent entry point
│   ├── CLI.md              Executable usage and limits
│   ├── REVIEW.md           Design decisions and remaining boundaries
│   ├── references/         Templates and focused workflows
│   └── scripts/            Compatibility hooks, provider helpers, tests
│       └── horsemen_core/  Shared checker and CLI implementation
├── scripts/                Build and end-to-end verification
├── tests/                  Distribution regression tests
├── pyproject.toml          CLI packaging; version comes from shared source
├── CONTRIBUTING.md         Setup, verification, and release procedure
└── .github/workflows/      Linux and macOS verification
```

## Read before changing

- [CONTRIBUTING.md](CONTRIBUTING.md) for tests and artifacts.
- [horsemen/SKILL.md](horsemen/SKILL.md) for the record contract.
- [horsemen/references/cli.md](horsemen/references/cli.md) for interface limits.

## Commands

- Verify: `.venv/bin/python -B scripts/verify.py --output /tmp/horsemen-verification`.
- Check records: `python3 -B horsemen/scripts/horsemen.py check .`.
- Run CLI: `PYTHONPATH=horsemen/scripts python3 -B -m horsemen_core --help`.

Installed skills and virtual environments are outputs, not authoring sources.
The prior private collection retains its history; it points here for future work.

## Brain map

No external provider is configured. [BRAIN.md](BRAIN.md) owns that boundary.
