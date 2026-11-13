"""Build a self-contained skill archive from the same source as the CLI."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import stat
import zipfile

REQUIRED = {
    "SKILL.md", "references/templates.md", "scripts/horsemen.py",
    "scripts/brain.py", "scripts/records.py", "scripts/drive_adapter.py",
    "scripts/horsemen_core/__init__.py", "scripts/horsemen_core/legacy.py",
    "scripts/horsemen_core/cli.py", "scripts/horsemen_core/__main__.py",
    "scripts/horsemen_core/plans.py", "scripts/horsemen_core/patches.py",
    "scripts/horsemen_core/git_read.py",
}


def version(root):
    source = root / "horsemen/scripts/horsemen_core/__init__.py"
    for node in ast.parse(source.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and value and all(c.isalnum() or c == '.' for c in value):
                return value
    raise ValueError("No valid literal Horsemen version")


def build_skill(root, output):
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root):
        raise ValueError("Build outside the source tree")
    files = []
    for path in sorted((root / "horsemen").rglob("*")):
        if path.is_symlink():
            raise ValueError("Skill source must not contain symlinks")
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file():
            if path.suffix not in {".py", ".md"} and path.name != "LICENSE":
                raise ValueError("Unexpected skill resource: " + str(path.relative_to(root)))
            files.append(path)
    names = {str(path.relative_to(root / "horsemen")) for path in files}
    if not REQUIRED.issubset(names):
        raise ValueError("Missing skill resources: " + ", ".join(sorted(REQUIRED - names)))
    license_path = root / "LICENSE"
    if not license_path.is_file() or license_path.is_symlink():
        raise ValueError("A regular LICENSE file is required")
    if "LICENSE" in names:
        if (root / "horsemen/LICENSE").read_bytes() != license_path.read_bytes():
            raise ValueError("Skill and project licenses differ")
    else:
        files.append(license_path)
    release = version(root)
    # Validate everything before creating the output. Existing builds are never overwritten.
    output.mkdir(parents=True, exist_ok=False)
    archive = output / f"horsemen-skill-{release}.zip"
    manifest = []
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as package:
        for path in files:
            data = path.read_bytes()
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            name = "horsemen/LICENSE" if path == license_path else str(path.relative_to(root))
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, data)
            manifest.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "mode": oct(mode)})
    (output / "skill-manifest.json").write_text(json.dumps({
        "version": release, "artifact": archive.name,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": manifest,
    }, indent=2) + "\n")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory outside the checkout")
    args = parser.parse_args()
    print(build_skill(Path(__file__).resolve().parents[1], args.output))
