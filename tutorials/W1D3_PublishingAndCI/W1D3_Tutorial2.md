---
title: "Tutorial 2: Colab and Kaggle Badges"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 2: Colab and Kaggle Badges

This tutorial is itself an example of a page that gets converted to `.ipynb` by CI
and receives Colab and Kaggle badges. Look for them at the top of this page and of
the notebook version.

## Where the notebooks live

Colab and Kaggle fetch notebooks from **raw GitHub URLs**. They cannot open `.md`
files, only `.ipynb`. CI generates the notebooks and pushes them to a separate
`notebooks-branch`, under `notebooks/`. They are never committed to `main`.

The `.md` files in `tutorials/` are the only source. The generated `.ipynb` files
are derived artifacts, so never edit them by hand.

## How badge injection works

Badges are added at build time in two places, and never committed to `main`.

**In the generated notebooks** (`generate-notebooks.yml`), `scripts/convert_to_notebooks.py`:

1. Scans `tutorials/` for `.md` files with a `kernelspec` in their frontmatter
2. Converts each to `.ipynb` via `jupytext --from md:myst --to notebook`
3. Inserts a markdown cell at position 0 containing Colab and Kaggle badge HTML
4. Writes the result to `notebooks/<day_folder>/<tutorial_name>.ipynb`

**On the rendered site** (`publish-book.yml`), CI runs
`convert_to_notebooks.py --inject-md-badges` right before `myst build`. This adds
the badge HTML to the top of each executable page in CI's temporary checkout only.
That's why badges don't appear in a local `myst start` preview, and why you should
never add badge HTML to a `.md` file yourself.

The badge URLs are derived from `project.github` in `myst.yml`, so they update
automatically when you fork the template. No repo paths are hardcoded.

## Badge URL format

**Colab:**

    https://colab.research.google.com/github/<org>/<repo>/blob/notebooks-branch/notebooks/<path>.ipynb

**Kaggle:**

    https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/<org>/<repo>/notebooks-branch/notebooks/<path>.ipynb

## Running the conversion script locally

```{code-cell} python
import subprocess

result = subprocess.run(
    ["python", "scripts/convert_to_notebooks.py", "--dry-run"],
    capture_output=True,
    text=True,
    cwd="../..",   # run from repo root
)
print(result.stdout or "(no output — run from the repo root)")
print(result.stderr or "")
```

## What the injected badge cell looks like

The first cell of every generated notebook contains HTML like this:

```html
<a href="https://colab.research.google.com/github/<org>/<repo>/blob/notebooks-branch/notebooks/<path>.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a> <a href="https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/<org>/<repo>/notebooks-branch/notebooks/<path>.ipynb" target="_blank"><img src="https://kaggle.com/static/images/open-in-kaggle.svg" alt="Open In Kaggle"/></a>
```

## Which pages get notebooks generated?

Only pages with a `kernelspec` in their frontmatter:

```yaml
---
kernelspec:
  name: python3
  display_name: Python 3
---
```

Pages without a `kernelspec` (like `further_reading.md` and `chapter_intro.md`)
are skipped, and no notebook is generated for them.

If a page contains `{code-cell}` blocks but no `kernelspec`, the script fails CI
with an error. Otherwise the page would silently get no notebook and no badges.
