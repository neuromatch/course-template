---
title: "Tutorial 1: GitHub Actions — Build and Publish Pipeline"
---

# Tutorial 1: GitHub Actions — Build and Publish Pipeline

The build tooling (the MyST plugin, the `nma-kit` command and the GitHub
Actions workflows) lives in the **Neuromatch course kit**, a separately
versioned project, published as `@neuromatch/course-kit` on npm and
`neuromatch-course-kit` on PyPI. Every course calls the kit's reusable
workflows instead of carrying its own copy, and picks up kit fixes on its next
build. The `@v0.1` in the workflow is the only version knob: the newest 0.1.x
(compatible updates), or an exact tag such as `@v0.1.3` to freeze a finished course.

This template has one workflow, `.github/workflows/course.yml`, included below
so this page always shows what actually runs.

## What runs, and when

**On a pull request**, the workflow checks your changes without publishing anything:

1. `nma-kit check` validates the content rules: no `.ipynb` files in
   `tutorials/`, every page with code cells has a `kernelspec`, every
   `{nma-video}`/`{nma-slides}` directive is valid, every exercise has an
   `{nma-solution}`, and the `nma:` settings in `myst.yml` are well formed.
2. `nma-kit notebooks --dry-run` checks that every executable page converts.
3. `nma-kit render-scrolly` runs every scrollytelling page
   (`layout: scrolly`, see [W1D2 Tutorial 6](../W1D2_InteractiveContent/W1D2_Tutorial6.md))
   headless. A cell that raises fails the check.
4. The whole site is built, so a broken page fails the check too.

**On a push to `main`**, the same steps run for real, in order, each one only if
the previous one passed:

1. `nma-kit check`
2. `nma-kit notebooks` converts each executable `.md` tutorial to `.ipynb`,
   adds a Colab/Kaggle badge cell, turns `{nma-video}`/`{nma-slides}` and
   `{nma-feedback}` into notebook cells, and splits `{nma-solution}`/
   `{nma-explanation}` into a student notebook (links) and an instructor
   notebook (answers inline), plus the solution files.
3. `nma-kit publish-notebooks` pushes `notebooks/` to the separate
   `notebooks-branch`. The branch is created the first time, so a fresh fork
   works on its first push.
4. `nma-kit render-scrolly` pre-renders the scrollytelling pages, so readers
   see real figures before they start Python.
5. `nma-kit prepare-site` adds Colab/Kaggle badges to the executable pages and,
   on pages with exercises, a hidden setup cell so "Run all" doesn't stop at an
   unfinished exercise. This only happens in CI's temporary checkout.
6. `myst build --html` builds the book, and the next job deploys it to GitHub Pages.

Generated notebooks are never committed to `main`, which keeps `main` free of
generated files and avoids CI commit loops. Videos, slides, solution links and
feedback widgets need no extra step: the course kit's MyST plugin renders them
during `myst build`.

```{literalinclude} ../../.github/workflows/course.yml
:language: yaml
```

## Running the same steps locally

```bash
uv venv && uv pip install -r requirements.txt neuromatch-course-kit
uv run nma-kit check
uv run nma-kit notebooks --dry-run
uv run myst start
```

## Setting up GitHub Pages

1. Go to your repo **Settings → Pages**
2. Set **Source** to `GitHub Actions`
3. Push any change to `main` to trigger the first build

Your book will be live at `https://<your-org>.github.io/<your-repo>/`. To use a
custom domain, set it under **Settings → Pages → Custom domain**; with the
GitHub Actions source no `CNAME` file is needed.
