# Physical Networks Satellite Archive

Website: **https://physnet-satellite.github.io/**

Repository: [physnet-satellite/physnet-satellite.github.io](https://github.com/physnet-satellite/physnet-satellite.github.io)

The public website and archive for the **Physical Networks** NetSci satellite series is built with [Quarto](https://quarto.org/). Edition pages are generated from YAML metadata and Jinja templates.

## Contents

| Location | Purpose |
|---|---|
| Root `.qmd` files | Homepage, archive, program, links, and error page |
| `editions/2023/` through `editions/2026/` | Generated public edition pages |
| `editions/2027/` | Draft edition page, excluded from publication |
| `data/series.yml` | Series settings and homepage mode |
| `data/editions/` | Published-edition metadata |
| `data/drafts/` | Draft metadata |
| `templates/` | Page templates |
| `scripts/` | Generation, validation, and publication checks |
| `assets/` | Styles, portraits, logos, and landing images |

## Editing and validation

Install Quarto and the Python dependencies, then edit metadata or templates and regenerate the pages:

```bash
python -m pip install -r requirements.txt
python scripts/validate_data.py
python scripts/build_pages.py
quarto render
python scripts/check_site.py
```

Use `quarto preview` for local preview. Generated pages identify their data and template in a comment at the top; edit those inputs instead of the generated pages. Commit the regenerated pages with their inputs.

Landing images are maintained separately. When a title or logo changes, regenerate the relevant images and review them before committing:

```bash
python scripts/generate_landing_images.py --year 2026
python scripts/generate_landing_images.py --series
```

The `--all` option generates the series image and all editions in `data/editions/`. Each image has a transparent background and its logo on the right. Font availability can affect the generated appearance.

`make build` validates data, regenerates pages, renders the website, and checks the publication output. `make landing` explicitly regenerates landing images.

## Homepage mode

Configure `data/series.yml`:

```yaml
home:
  mode: archive
  current_year: null
  latest_year: 2026
```

Use `mode: current` with `current_year` set to a year in `data/editions/` to promote that edition. Use `mode: archive` to show the series archive.

## Publishing

Push to `main` to run **Render and publish Quarto site**. The workflow validates the data and committed generated pages, renders into `docs/`, checks the publication contents, and deploys a Pages artifact. Do not commit local build output.

Repository settings:

- **Settings → Pages → Build and deployment → Source:** **GitHub Actions**.
- Enable **Enforce HTTPS** and leave the custom domain empty.
- Allow the actions declared in `.github/workflows/publish.yml`. Deployment uses the `github-pages` environment with `pages: write` and `id-token: write` permissions.

Both the build and deployment jobs must succeed. To republish without a commit, use **Run workflow** with `main` selected.

The explicit `project.render` and `project.resources` lists in `_quarto.yml` define the public pages and assets. The publication check rejects unexpected files and broken local links, including fallback images, and validates search and sitemap entries.

## Drafts and new editions

The 2027 metadata, page, and landing image remain available for editing in this public repository. They are excluded from the published website. Repository visibility is separate from website publication.

When an edition is ready, put its metadata in `data/editions/`, regenerate its page, and add the page, required images, and navigation entry to `_quarto.yml`. Run the build and publication checks before pushing.

Private organizing material and personal contact information should not be stored in this public repository.
