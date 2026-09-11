#!/usr/bin/env python3
"""Build a deterministic ZIP of the whole repository skills directory."""

from __future__ import annotations

import argparse
import hashlib
import stat
import zipfile
from pathlib import Path

FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def build_zip(repo_root: Path, output: Path) -> tuple[str, int]:
    skill_root = repo_root / "skills" / "shortx-rule-creator"
    required = skill_root / "SKILL.md"
    if not required.is_file():
        raise SystemExit(f"missing skill entry: {required}")

    files = [
        path
        for path in sorted(skill_root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
        and path.name != ".DS_Store"
        and not path.is_symlink()
    ]
    if not files:
        raise SystemExit(f"no files found under {skill_root}")

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    if temp.exists():
        temp.unlink()

    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            # Archive the complete skill directory at the archive root so
            # extraction into the configured private skills root yields
            # <root>/shortx-rule-creator/SKILL.md.
            relative = (Path("shortx-rule-creator") / path.relative_to(skill_root)).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )

    temp.replace(output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return digest, len(files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output = (args.output or repo_root / "skills" / "shortx-rule-creator.zip").resolve()
    digest, file_count = build_zip(repo_root, output)
    print(f"built {output} ({file_count} files, sha256={digest})")


if __name__ == "__main__":
    main()
