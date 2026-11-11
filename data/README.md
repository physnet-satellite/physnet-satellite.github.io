# Website data

- `series.yml` controls the series description and homepage mode.
- `editions/YYYY.yml` provides the metadata for each public edition.
- `drafts/YYYY.yml` holds metadata for editions still being prepared.

After editing public metadata, validate and regenerate the pages:

```bash
python scripts/validate_data.py
python scripts/build_pages.py
```

Commit the generated pages together with the metadata. These data files are available in the public repository but are not copied into the published website.
