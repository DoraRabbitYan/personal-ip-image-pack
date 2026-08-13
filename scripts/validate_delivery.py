#!/usr/bin/env python3
"""Validate the machine-checkable parts of a personal IP delivery package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit(
        "Pillow is required to inspect PNG dimensions and alpha. "
        "Install it with: python -m pip install Pillow"
    ) from exc


ALLOWED_DELIVERY_STATUS = {"draft", "qa_passed", "accepted", "superseded"}
ALLOWED_ASSET_ROLE = {"source_asset", "preview"}
ALLOWED_QA_STATUS = {"pending", "pass", "fail", "rework"}
ASSET_FILENAME = re.compile(r"-v\d+-r\d+\.png$", re.IGNORECASE)


def safe_child(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_details(path: Path) -> tuple[str | None, list[int], bool]:
    with Image.open(path) as image:
        image.load()
        actual_format = image.format
        pixel_size = [image.width, image.height]
        transparent_pixels = False
        if "A" in image.getbands():
            alpha_min, _ = image.getchannel("A").getextrema()
            transparent_pixels = alpha_min < 255
        elif "transparency" in image.info:
            transparent_pixels = True
    return actual_format, pixel_size, transparent_pixels


def validate(manifest_path: Path, output_root: Path, ready: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot read manifest: {exc}"], warnings

    if manifest.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'.")

    status = manifest.get("status")
    if status not in ALLOWED_DELIVERY_STATUS:
        errors.append(f"status must be one of {sorted(ALLOWED_DELIVERY_STATUS)}.")
    elif ready and status not in {"qa_passed", "accepted"}:
        errors.append("--ready requires delivery status qa_passed or accepted.")

    for field in ("character_spec", "acceptance_qa"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"{field} must be a non-empty relative path.")
            continue
        resolved = safe_child(output_root, value)
        if resolved is None:
            errors.append(f"{field} escapes delivery root.")
        elif not resolved.is_file():
            errors.append(f"{field} does not exist: {value}")

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        return errors + ["assets must be a non-empty list."], warnings

    seen_ids: set[str] = set()
    source_assets = 0

    for index, asset in enumerate(assets):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{label} must be an object.")
            continue

        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not asset_id:
            errors.append(f"{label}.id must be a non-empty string.")
        elif asset_id in seen_ids:
            errors.append(f"Duplicate asset id: {asset_id}")
        else:
            seen_ids.add(asset_id)

        role = asset.get("role")
        if role not in ALLOWED_ASSET_ROLE:
            errors.append(f"{label}.role must be one of {sorted(ALLOWED_ASSET_ROLE)}.")
        elif role == "source_asset":
            source_assets += 1

        relative_file = asset.get("file")
        if not isinstance(relative_file, str) or not relative_file:
            errors.append(f"{label}.file must be a non-empty relative path.")
            continue
        file_path = safe_child(output_root, relative_file)
        if file_path is None:
            errors.append(f"{label}.file escapes delivery root.")
            continue
        if not file_path.is_file():
            errors.append(f"{label}.file does not exist: {relative_file}")
            continue

        if role == "source_asset" and not ASSET_FILENAME.search(file_path.name):
            errors.append(f"{label}.file must end with -v<N>-r<N>.png.")

        try:
            actual_format, actual_size, actual_alpha = image_details(file_path)
        except (OSError, ValueError) as exc:
            errors.append(f"{label}.file is not a readable image: {exc}")
            continue

        expected_format = asset.get("format")
        if expected_format != "png" or actual_format != "PNG":
            errors.append(f"{label}.format must be png and the actual file must be PNG.")

        expected_size = asset.get("pixel_size")
        if expected_size != actual_size:
            errors.append(
                f"{label}.pixel_size {expected_size!r} does not match actual {actual_size!r}."
            )

        alpha = asset.get("alpha")
        if not isinstance(alpha, dict):
            errors.append(f"{label}.alpha must be an object with required and actual fields.")
        else:
            if not isinstance(alpha.get("required"), bool):
                errors.append(f"{label}.alpha.required must be boolean.")
            if alpha.get("actual") is not actual_alpha:
                errors.append(
                    f"{label}.alpha.actual must be {actual_alpha} for the delivered file."
                )
            if alpha.get("required") is True and not actual_alpha:
                errors.append(f"{label} requires real transparent pixels but has none.")

        qa_status = asset.get("qa_status")
        if qa_status not in ALLOWED_QA_STATUS:
            errors.append(f"{label}.qa_status must be one of {sorted(ALLOWED_QA_STATUS)}.")
        elif ready and role == "source_asset" and qa_status != "pass":
            errors.append(f"{label} is a source asset but has not passed QA.")

        supplied_hash = asset.get("sha256", "")
        actual_hash = sha256_file(file_path)
        if supplied_hash and supplied_hash != actual_hash:
            errors.append(f"{label}.sha256 does not match the file.")
        elif ready and role == "source_asset" and not supplied_hash:
            errors.append(f"{label}.sha256 is required for a ready source asset.")
        elif not supplied_hash:
            warnings.append(f"{label}.sha256 is empty; computed value: {actual_hash}")

    if source_assets == 0:
        errors.append("At least one source_asset is required; preview assets cannot be delivery sources.")

    rights = manifest.get("rights_gate")
    if not isinstance(rights, dict):
        errors.append("rights_gate must be an object.")
    elif ready and rights.get("likeness_consent") != "confirmed":
        errors.append("--ready requires rights_gate.likeness_consent to be confirmed.")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the file, image, alpha, hash, and QA fields of a delivery manifest."
    )
    parser.add_argument("delivery_root", type=Path, help="Root directory of one character delivery.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest path, relative to delivery_root unless absolute. Defaults to contracts/delivery-manifest-r1.json.",
    )
    parser.add_argument(
        "--ready",
        action="store_true",
        help="Require QA-passed source assets, hashes, rights confirmation, and publishable status.",
    )
    args = parser.parse_args()

    output_root = args.delivery_root.resolve()
    manifest_path = args.manifest or Path("contracts/delivery-manifest-r1.json")
    if not manifest_path.is_absolute():
        manifest_path = output_root / manifest_path

    errors, warnings = validate(manifest_path, output_root, args.ready)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Delivery manifest is valid: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
