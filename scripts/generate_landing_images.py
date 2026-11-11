#!/usr/bin/env python3
"""Generate PhysNet landing title images from YAML metadata.

Creates the transparent image used by each edition and the series homepage.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import argparse
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EDITION_DIR = DATA_DIR / "editions"
LANDING_DIR = ROOT / "assets/img/common/landing"
LOGO_PATHS = [
    ROOT / "assets/img/common/logos/common_logo_physnet-mark-transparent.png",
    ROOT / "assets/img/common/logos/common_logo_physnet-mark.png",
]

BLUE = "#1f4e79"
DARK = "#1f2933"


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_logo() -> Image.Image:
    logo_path = next((p for p in LOGO_PATHS if p.exists()), None)
    if logo_path is None:
        raise FileNotFoundError("No PhysNet logo found under assets/img/common/logos/")
    logo = Image.open(logo_path).convert("RGBA")
    arr = np.array(logo)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    black_mask = (rgb[:, :, 0] < 8) & (rgb[:, :, 1] < 8) & (rgb[:, :, 2] < 8) & (alpha > 0)
    h, w = black_mask.shape
    visited = np.zeros_like(black_mask, dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if black_mask[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if black_mask[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and black_mask[yy, xx] and not visited[yy, xx]:
                visited[yy, xx] = True
                q.append((yy, xx))
    arr[visited, 3] = 0
    logo = Image.fromarray(arr, "RGBA")
    bbox = logo.getbbox()
    return logo.crop(bbox) if bbox else logo


def find_font(candidates: list[str]) -> str:
    for c in candidates:
        if Path(c).exists():
            return c
    raise FileNotFoundError("No usable font found. Install DejaVu Sans or set font paths in the script.")


def make_asset(kicker: str, line1: str, line2: str | None, logo: Image.Image) -> Image.Image:
    font_regular = find_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ])
    font_bold = find_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ])
    kicker_font = ImageFont.truetype(font_regular, 42)
    h1_font = ImageFont.truetype(font_bold, 118)
    h2_font = ImageFont.truetype(font_bold, 100)

    logo_max_h = 355 if line2 else 255
    scale = logo_max_h / logo.height
    logo_resized = logo.resize((int(logo.width * scale), int(logo.height * scale)), Image.Resampling.LANCZOS)

    temp = Image.new("RGBA", (10, 10), (255, 255, 255, 0))
    draw = ImageDraw.Draw(temp)
    lines = [(kicker, kicker_font, BLUE), (line1, h1_font, DARK)]
    if line2:
        lines.append((line2, h2_font, BLUE))
    widths = []
    heights = []
    for text, font, _ in lines:
        b = draw.textbbox((0, 0), text, font=font)
        widths.append(b[2] - b[0])
        heights.append(b[3] - b[1])
    gaps = [24] + ([16] if line2 else [])
    text_w = max(widths)
    text_h = sum(heights) + sum(gaps)

    left_pad = 4
    right_pad = 8
    vert_pad = 8
    gap = 72
    H = max(text_h, logo_resized.height) + 2 * vert_pad
    W = left_pad + text_w + gap + logo_resized.width + right_pad
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    text_x = left_pad
    logo_x = left_pad + text_w + gap

    y = (H - text_h) // 2
    for i, (text, font, color) in enumerate(lines):
        d.text((text_x, y), text, font=font, fill=color)
        y += heights[i]
        if i < len(gaps):
            y += gaps[i]
    img.alpha_composite(logo_resized, (logo_x, (H - logo_resized.height) // 2))

    bbox = img.getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        img = img.crop((max(0, x0 - 2), max(0, y0 - 2), min(img.width, x1 + 2), min(img.height, y1 + 2)))
    return img


def save_asset(img: Image.Image, prefix: str) -> None:
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    transparent = LANDING_DIR / f"{prefix}_landing-title-logo-right-transparent.png"
    img.save(transparent)
    print(f"wrote {transparent.relative_to(ROOT)}")


def generate_edition(year: int, logo: Image.Image) -> None:
    data = load_yaml(EDITION_DIR / f"{year}.yml")
    kicker = data.get("kicker", f"NetSci{str(year)[-2:]} Satellite")
    line1 = data.get("title", f"Physical Networks {data.get('roman', '')}")
    line2 = f"@ {data.get('conference', f'NetSci {year}')}"
    save_asset(make_asset(kicker, line1, line2, logo), str(year))


def generate_series(logo: Image.Image) -> None:
    series = load_yaml(DATA_DIR / "series.yml")
    kicker = series.get("subtitle", "NetSci Satellite Series")
    title = series.get("title", "Physical Networks")
    save_asset(make_asset(kicker, title, None, logo), "series")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--year", type=int)
    group.add_argument("--series", action="store_true")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    logo = load_logo()
    if args.year:
        generate_edition(args.year, logo)
    elif args.series:
        generate_series(logo)
    else:
        generate_series(logo)
        for path in sorted(EDITION_DIR.glob("*.yml")):
            generate_edition(int(path.stem), logo)


if __name__ == "__main__":
    main()
