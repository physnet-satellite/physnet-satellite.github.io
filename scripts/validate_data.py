#!/usr/bin/env python3
"""Validate PhysNet YAML files and check for accidental personal contact data."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EDITION_DIR = DATA_DIR / "editions"
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

REQUIRED_EDITION_KEYS = [
    "year", "roman", "title", "short_title", "kicker", "conference", "status",
    "date", "time", "location", "venue", "urls", "assets", "description",
    "speakers", "program", "keywords", "organizers", "call_for_contributions",
]


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_no_email(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path.relative_to(ROOT)} contains email-like string: {m.group(0)}" for m in EMAIL_RE.finditer(text)]


def main() -> None:
    errors: list[str] = []

    series_path = DATA_DIR / "series.yml"
    if not series_path.exists():
        errors.append("Missing data/series.yml")
    else:
        series = load_yaml(series_path)
        if series.get("home", {}).get("mode") not in {"current", "archive"}:
            errors.append("data/series.yml home.mode must be 'current' or 'archive'")
        errors.extend(check_no_email(series_path))

    for path in sorted(EDITION_DIR.glob("*.yml")):
        data = load_yaml(path)
        for key in REQUIRED_EDITION_KEYS:
            if key not in data:
                errors.append(f"{path.relative_to(ROOT)} missing required key: {key}")
        if int(data.get("year", path.stem)) != int(path.stem):
            errors.append(f"{path.relative_to(ROOT)} year does not match filename")
        if not data.get("speakers"):
            errors.append(f"{path.relative_to(ROOT)} has no speakers")
        if not data.get("program"):
            errors.append(f"{path.relative_to(ROOT)} has no program entries")
        errors.extend(check_no_email(path))

    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("YAML validation passed.")


if __name__ == "__main__":
    main()
