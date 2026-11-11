# Website images

Public edition portraits are stored at `YYYY/speakers/YYYY_speaker_name_headshot.jpg`. Preserve these paths when replacing portraits. Square images work best; the website crops them to fit the portrait cards. `speaker-placeholder.svg` is the fallback for missing portraits.

`common/logos/common_logo_physnet-mark.png` is the website icon. The landing-image generator reads `common/logos/common_logo_physnet-mark-transparent.png` as its source logo.

Landing images use `common/landing/YYYY_landing-title-logo-right-transparent.png`, with `series` in place of the year for the homepage. Generate a public edition's image with:

```bash
python scripts/generate_landing_images.py --year 2026
```

Only assets explicitly listed in `_quarto.yml` are intended for publication. The 2027 landing image and generator source logo stay in the repository for editing without being published as website assets.
