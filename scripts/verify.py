"""Verify source, built CLI, and packaged skill; leave a repeatable receipt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import venv
import zipfile
from distribution import build_skill, version

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New output directory outside checkout")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Keep artifacts outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0")
    env.pop("HORSEMEN_CLI", None)
    env.pop("PYTHONPATH", None)
    receipt = {"version": version(ROOT), "python": platform.python_version(),
               "platform": platform.system(), "status": "running", "checks": []}

    def run(label, command, cwd=ROOT, extra=None):
        print(label, flush=True)
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, env=dict(env, **(extra or {})),
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / f"{label}.log").write_text(result.stdout)
        receipt["checks"].append({"name": label, "command": command,
                                  "exit_code": result.returncode,
                                  "seconds": round(time.monotonic() - started, 2)})
        if result.returncode:
            print(result.stdout[-5000:], file=sys.stderr)
            raise RuntimeError(f"{label} failed; see its log")
        return result.stdout

    try:
        receipt["commit"] = run("revision", ["git", "rev-parse", "HEAD"]).strip()
        receipt["source_dirty"] = bool(run("source-status", ["git", "status", "--porcelain"]).strip())
        run("distribution-tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"])
        for suite in ("test_cli", "test_documents", "test_progress_layout", "test_techstack", "test_commands",
                      "test_brain", "test_records", "test_drive_adapter"):
            run(suite, [sys.executable, "-B", f"horsemen/scripts/{suite}.py"])
        run("source-hooks", [sys.executable, "-B", "horsemen/scripts/e2e.py", "--output", str(output / "source-hooks.json")])
        archive = build_skill(ROOT, output / "skill")
        with tempfile.TemporaryDirectory(prefix="horsemen-verify-") as temporary:
            temp = Path(temporary)
            # Build from the same clean copy distributed as the skill. No build debris enters source.
            with zipfile.ZipFile(archive) as package:
                package.extractall(temp / "source")
            for name in ("pyproject.toml", "README.md"):
                shutil.copy2(ROOT / name, temp / "source" / name)
            if (ROOT / "LICENSE").exists():
                shutil.copy2(ROOT / "LICENSE", temp / "source/LICENSE")
            wheels = output / "wheels"
            run("wheel-build", [sys.executable, "-m", "pip", "wheel", str(temp / "source"),
                                "--no-deps", "--no-build-isolation", "--wheel-dir", str(wheels)])
            wheel, = wheels.glob("*.whl")
            venv.EnvBuilder(with_pip=True).create(temp / "venv")
            python = temp / "venv/bin/python"
            cli = temp / "venv/bin/horsemen"
            run("wheel-install", [str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
            run("installed-cli", [sys.executable, "-B", str(ROOT / "horsemen/scripts/test_cli.py")],
                cwd=temp, extra={"HORSEMEN_CLI": str(cli)})
            installed_version = run("installed-version", [str(cli), "--version"], cwd=temp).strip()
            if installed_version != receipt["version"]:
                raise RuntimeError("CLI and skill versions differ")
            run("packaged-hooks", [sys.executable, "-B", str(temp / "source/horsemen/scripts/e2e.py"),
                                   "--output", str(output / "packaged-hooks.json")], cwd=temp)
            receipt["artifacts"] = [{"file": str(p.relative_to(output)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                    for p in (archive, wheel)]
        receipt["status"] = "passed"
        return 0
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        print(str(error), file=sys.stderr)
        return 1
    finally:
        (output / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"{receipt['status']}: {output / 'verification.json'}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
