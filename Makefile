PYTHON ?= python
PIP ?= $(PYTHON) -m pip
QUARTO ?= quarto
YEAR ?= 2026

.PHONY: help install validate landing pages generate preview render build clean clean-docs clean-generated home-current home-archive check

help:
	@echo "PhysNet Quarto site workflow"
	@echo ""
	@echo "Common targets:"
	@echo "  make install              Install Python dependencies"
	@echo "  make validate             Validate YAML data"
	@echo "  make landing              Generate landing images"
	@echo "  make pages                Generate Quarto pages from YAML/templates"
	@echo "  make generate             Validate data and generate pages"
	@echo "  make preview              Generate site and run quarto preview"
	@echo "  make render               Generate site and run quarto render"
	@echo "  make build                Alias for render"
	@echo ""
	@echo "Homepage mode:"
	@echo "  make home-current YEAR=2026   Set homepage to current edition mode"
	@echo "  make home-archive YEAR=2026   Set homepage to archive mode"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean-docs           Remove rendered docs/"
	@echo "  make clean-generated      Remove generated qmd pages"
	@echo "  make clean                Remove rendered docs/"

install:
	$(PIP) install -r requirements.txt

validate:
	$(PYTHON) scripts/validate_data.py

landing:
	$(PYTHON) scripts/generate_landing_images.py --all

pages:
	$(PYTHON) scripts/build_pages.py

generate: validate pages

preview: generate
	$(QUARTO) preview

render: generate
	$(QUARTO) render
	$(PYTHON) scripts/check_site.py

build: render

check: generate
	@echo "Checking generated files..."
	@test -f index.qmd
	@test -f archive.qmd
	@test -f links.qmd
	@test -f program.qmd
	@test -f editions/$(YEAR)/index.qmd
	@echo "OK"

home-current:
	$(PYTHON) -c "import yaml; p='data/series.yml'; d=yaml.safe_load(open(p, encoding='utf-8')); d.setdefault('home', {}); d['home']['mode']='current'; d['home']['current_year']=$(YEAR); d['home']['latest_year']=$(YEAR); open(p, 'w', encoding='utf-8').write(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))"
	$(PYTHON) scripts/build_pages.py
	@echo "Homepage mode set to current edition: $(YEAR)"

home-archive:
	$(PYTHON) -c "import yaml; p='data/series.yml'; d=yaml.safe_load(open(p, encoding='utf-8')); d.setdefault('home', {}); d['home']['mode']='archive'; d['home']['current_year']=None; d['home']['latest_year']=$(YEAR); open(p, 'w', encoding='utf-8').write(yaml.safe_dump(d, sort_keys=False, allow_unicode=True))"
	$(PYTHON) scripts/build_pages.py
	@echo "Homepage mode set to archive. Latest archived edition: $(YEAR)"

clean-docs:
	rm -rf docs

clean-generated:
	rm -f index.qmd archive.qmd links.qmd program.qmd
	$(PYTHON) -c "from pathlib import Path; [(Path('editions') / p.stem / 'index.qmd').unlink(missing_ok=True) for p in Path('data/editions').glob('*.yml')]"

clean: clean-docs
