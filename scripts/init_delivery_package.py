#!/usr/bin/env python3
"""Create a private, versioned delivery-package skeleton from bundled templates."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path


CHARACTER_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


def replace_tokens(path: Path, character_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    replacements = {
        "<character-id>": character_id,
        "<yyyy-mm-dd>": date.today().isoformat(),
        "<delivery-id>": f"ip-{character_id}-r1",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a private personal-IP delivery package from bundled templates."
    )
    parser.add_argument("character_id", help="Lowercase letters, digits, and hyphens only.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs"),
        help="Private parent directory. The character folder is created inside it.",
    )
    args = parser.parse_args()

    if not CHARACTER_ID.fullmatch(args.character_id):
        parser.error("character_id must use lowercase letters, digits, and hyphens (max 63 chars).")

    skill_root = Path(__file__).resolve().parents[1]
    templates = skill_root / "assets" / "templates"
    destination = (args.output_root / args.character_id).resolve()
    if destination.exists():
        parser.error(f"Refusing to overwrite existing delivery package: {destination}")

    try:
        (destination / "contracts").mkdir(parents=True)
        (destination / "assets" / "stickers").mkdir(parents=True)
        (destination / "previews").mkdir(parents=True)

        copies = {
            templates / "input-brief.yaml": destination / "contracts" / "input-brief.yaml",
            templates / "character-spec.yaml": destination / "contracts" / "character-spec-d1.yaml",
            templates / "delivery-manifest.json": destination / "contracts" / "delivery-manifest-r1.json",
            templates / "acceptance-qa.md": destination / "contracts" / "acceptance-qa-r1.md",
        }
        for source, target in copies.items():
            if not source.is_file():
                raise FileNotFoundError(f"Missing bundled template: {source}")
            shutil.copyfile(source, target)
            replace_tokens(target, args.character_id)
    except Exception as exc:
        print(f"ERROR: Could not create delivery package: {exc}", file=sys.stderr)
        return 1

    print(f"Created private delivery package: {destination}")
    print("Next: complete input-brief.yaml, then generate character-spec-d1 and the prototype.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
