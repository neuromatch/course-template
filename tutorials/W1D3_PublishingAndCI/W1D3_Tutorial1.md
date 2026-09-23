---
title: "Tutorial 1: GitHub Actions — Build and Publish Pipeline"
---

# Tutorial 1: GitHub Actions — Build and Publish Pipeline

This template ships with two GitHub Actions workflows that run automatically
on every push to `main`.

## Workflow 1: `generate-notebooks.yml`

Converts MyST `.md` tutorials to `.ipynb` and commits them back to the repo.
This runs first so that the published book always links to up-to-date notebooks.

```yaml
name: Generate Notebooks

on:
  push:
    branches: [main]
    paths:
      - "tutorials/**"
      - "scripts/convert_to_notebooks.py"
      - "myst.yml"
      - "requirements.txt"

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Convert tutorials to notebooks
        run: python scripts/convert_to_notebooks.py

      - name: Commit generated notebooks
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add notebooks/
          if git diff --cached --quiet; then
            echo "No notebook changes to commit."
          else
            git commit -m "chore: regenerate notebooks [skip ci]"
            git push
          fi
```

## Workflow 2: `publish-book.yml`

Builds the MyST book and deploys it to GitHub Pages.

```yaml
name: Publish Book

on:
  push:
    branches: [main]
  workflow_run:
    workflows: ["Generate Notebooks"]
    types: [completed]
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Build MyST book
        run: myst build --html

      - uses: actions/upload-pages-artifact@v3
        with:
          path: _build/html

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

## Setting up GitHub Pages

1. Go to your repo **Settings → Pages**
2. Set **Source** to `GitHub Actions`
3. Push any change to `main` to trigger the first build

Your book will be live at `https://<your-org>.github.io/<your-repo>/`.

## The `[skip ci]` commit message

The notebook generation workflow commits back to `main`. The `[skip ci]` tag in
the commit message prevents GitHub Actions from triggering another build loop.
