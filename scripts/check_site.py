#!/usr/bin/env python3
"""Check that the rendered website contains only its intended public files."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import json
import re
import xml.etree.ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parents[1]
CSS_URL = re.compile(r"url\(\s*['\"]?([^)'\"\s]+)")
FALLBACK_URL = re.compile(r"this\.src\s*=\s*['\"]([^'\"]+)")


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if not value:
                continue
            if key in {"href", "src", "poster"}:
                self.urls.append(value)
            elif key == "onerror":
                self.urls.extend(FALLBACK_URL.findall(value))
            elif key == "style":
                self.urls.extend(CSS_URL.findall(value))
            elif key == "srcset":
                self.urls.extend(item.strip().split()[0] for item in value.split(",") if item.strip())


def main() -> None:
    config = yaml.safe_load((ROOT / "_quarto.yml").read_text())
    project = config["project"]
    output = (ROOT / project["output-dir"]).resolve()
    site_url = config["website"]["site-url"]
    errors: list[str] = []

    def explicit_files(key: str) -> set[str]:
        values = project[key]
        if not isinstance(values, list):
            raise ValueError(f"project.{key} must list individual files")
        for value in values:
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or not (ROOT / path).is_file():
                raise ValueError(f"project.{key} must list existing individual files: {value}")
        return set(values)

    pages = {str(Path(p).with_suffix(".html")) for p in explicit_files("render")}
    resources = explicit_files("resources")
    metadata = {"search.json", "sitemap.xml", "robots.txt"}
    required = pages | resources | metadata
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            errors.append(f"Symlink in output: {path.relative_to(output)}")
        elif path.is_file():
            actual.add(path.relative_to(output).as_posix())
    for name in sorted(required - actual):
        errors.append(f"Missing output: {name}")
    for name in sorted(actual - required):
        if not name.startswith("site_libs/"):
            errors.append(f"Unexpected output: {name}")

    def local_path(value: str, origin: str) -> str | None:
        absolute = urljoin(urljoin(site_url, origin), value)
        parts = urlsplit(absolute)
        if parts.scheme not in {"http", "https"} or parts.netloc != urlsplit(site_url).netloc:
            return None
        path = unquote(parts.path).lstrip("/")
        if not path or path.endswith("/"):
            path += "index.html"
        return path

    for name in sorted(actual):
        path = output / name
        if path.suffix == ".html":
            parser = References()
            parser.feed(path.read_text())
            links = parser.urls
        elif path.suffix == ".css":
            links = CSS_URL.findall(path.read_text())
        else:
            continue
        for link in links:
            local = local_path(link, name)
            if local is not None and local not in actual:
                errors.append(f"Broken local reference in {name}: {link}")

    if "search.json" in actual:
        records = json.loads((output / "search.json").read_text())
        if not records:
            errors.append("Search index is empty")
        for record in records:
            if local_path(record["href"], "index.html") not in pages:
                errors.append(f"Search result outside public pages: {record['href']}")
    if "sitemap.xml" in actual:
        sitemap = ET.parse(output / "sitemap.xml")
        urls = [node.text or "" for node in sitemap.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        if not urls:
            errors.append("Sitemap is empty")
        for url in urls:
            if not url.startswith(site_url) or local_path(url, "index.html") not in pages:
                errors.append(f"Sitemap entry outside public pages: {url}")

    if errors:
        raise SystemExit("Publication check failed:\n" + "\n".join(f"- {error}" for error in errors))
    print(f"Publication check passed: {len(pages)} pages, {len(resources)} assets, and {len(actual)} total files.")


if __name__ == "__main__":
    main()
