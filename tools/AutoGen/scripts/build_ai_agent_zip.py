#!/usr/bin/env python3
"""Build a deterministic archive for the local ShortX AI agent."""
from __future__ import annotations

import argparse
import hashlib
import stat
import zipfile
from pathlib import Path

STAMP = (1980, 1, 1, 0, 0, 0)


def build(repo_root: Path, output: Path) -> str:
    entries: list[tuple[Path, str]] = []
    for source in (repo_root / "app", repo_root / "skills" / "shortx-rule-creator"):
        if not source.is_dir():
            raise SystemExit(f"missing directory: {source}")
        for path in sorted(source.rglob("*"), key=lambda p: p.as_posix()):
            if not path.is_file() or path.is_symlink() or path.name == ".DS_Store" or path == output or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if source.name == "app":
                relative = Path("app") / path.relative_to(source)
            else:
                relative = Path("skills") / "shortx-rule-creator" / path.relative_to(source)
            entries.append((path, (Path("shortx-local-ai-agent") / relative).as_posix()))
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    if temp.exists():
        temp.unlink()
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in entries:
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    temp.replace(output)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = (args.output or root / "app" / "shortx-local-ai-agent.zip").resolve()
    print(f"built {output} sha256={build(root, output)}")


if __name__ == "__main__":
    main()
