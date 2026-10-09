---
title: "Tutorial 1: GitHub Actions — Build and Publish Pipeline"
---

# Tutorial 1: GitHub Actions — Build and Publish Pipeline

This template ships with two GitHub Actions workflows that run automatically
on every push to `main`. The workflow files below are included directly from
`.github/workflows/`, so this page always shows what actually runs.

## Workflow 1: `generate-notebooks.yml`

1. Checks the content rules: no `.ipynb` files in `tutorials/`, and every page
   with code cells has a `kernelspec`.
2. Converts each executable `.md` tutorial to `.ipynb` and adds a Colab/Kaggle
   badge cell.
3. Pushes the notebooks to the separate `notebooks-branch`.

Generated notebooks are never committed to `main`, which keeps `main` free of
generated files and avoids CI commit loops.

```{literalinclude} ../../.github/workflows/generate-notebooks.yml
:language: yaml
```

## Workflow 2: `publish-book.yml`

Runs after notebook generation finishes, or directly when config or static files
change. It adds Colab/Kaggle badges to the executable pages in its temporary
checkout, builds the MyST book, and deploys it to GitHub Pages.

```{literalinclude} ../../.github/workflows/publish-book.yml
:language: yaml
```

## Setting up GitHub Pages

1. Go to your repo **Settings → Pages**
2. Set **Source** to `GitHub Actions`
3. Push any change to `main` to trigger the first build

Your book will be live at `https://<your-org>.github.io/<your-repo>/`, or at your
custom domain if you add a `CNAME` file.
