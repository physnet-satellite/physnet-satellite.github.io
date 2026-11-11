#!/usr/bin/env python3
"""Generate Quarto pages from PhysNet YAML data."""
from __future__ import annotations

from pathlib import Path
import os
import re
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EDITION_DIR = DATA_DIR / "editions"
TEMPLATE_DIR = ROOT / "templates"
GENERATED_NOTICE = "Generated file. Do not edit directly."


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_series() -> dict[str, Any]:
    return load_yaml(DATA_DIR / "series.yml")


def load_editions() -> list[dict[str, Any]]:
    editions = []
    for path in sorted(EDITION_DIR.glob("*.yml"), reverse=True):
        data = load_yaml(path)
        data.setdefault("year", int(path.stem))
        data.setdefault("urls", {})
        data.setdefault("assets", {})
        data["urls"].setdefault("archive_page", f"editions/{data['year']}/index.qmd")
        data["assets"].setdefault("speaker_placeholder", "assets/img/speaker-placeholder.svg")
        data["assets"].setdefault("landing_image", f"assets/img/common/landing/{data['year']}_landing-title-logo-right-transparent.png")
        editions.append(data)
    editions.sort(key=lambda x: int(x["year"]), reverse=True)
    return editions


def relpath_filter(path: str, output_path: Path) -> str:
    """Return path relative to the parent directory of output_path.

    YAML stores repository-root-relative local paths, e.g. assets/img/...
    External URLs, anchors, and mailto links are returned unchanged.
    """
    if path is None:
        return ""
    path = str(path)
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", path) or path.startswith("#"):
        return path
    src = (ROOT / path).resolve()
    dest_dir = output_path.parent.resolve()
    try:
        return os.path.relpath(src, dest_dir)
    except ValueError:
        return path


def make_env(output_path: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
        autoescape=False,
    )
    env.filters["rel"] = lambda p: relpath_filter(p, output_path)
    return env


def render(template_name: str, output_path: Path, **context: Any) -> None:
    env = make_env(output_path)
    template = env.get_template(template_name)
    text = template.render(**context).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"wrote {output_path.relative_to(ROOT)}")


def main() -> None:
    series = load_series()
    editions = load_editions()
    years = {int(e["year"]): e for e in editions}

    # Generate edition pages.
    for edition in editions:
        out = ROOT / "editions" / str(edition["year"]) / "index.qmd"
        render("edition.qmd.j2", out, series=series, edition=edition, editions=editions)

    # Generate homepage.
    mode = series.get("home", {}).get("mode", "archive")
    if mode == "current":
        year = int(series.get("home", {}).get("current_year"))
        render("home_current.qmd.j2", ROOT / "index.qmd", series=series, edition=years[year], editions=editions)
    elif mode == "archive":
        render("home_archive.qmd.j2", ROOT / "index.qmd", series=series, editions=editions)
    else:
        raise ValueError("data/series.yml home.mode must be 'current' or 'archive'")

    render("archive.qmd.j2", ROOT / "archive.qmd", series=series, editions=editions)
    render("program_pointer.qmd.j2", ROOT / "program.qmd", series=series, editions=editions)
    render("links.qmd.j2", ROOT / "links.qmd", series=series, editions=editions)


if __name__ == "__main__":
    main()
