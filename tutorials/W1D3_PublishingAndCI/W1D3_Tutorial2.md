---
title: "Tutorial 2: Colab and Kaggle Badges"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 2: Colab and Kaggle Badges

This tutorial is itself an example of a page that gets converted to `.ipynb` by CI
and receives Colab and Kaggle badges. Look for them at the top of the notebook version.

## Why `.ipynb` files are committed to the repo

Colab and Kaggle fetch notebooks from **raw GitHub URLs**. They cannot open `.md`
files — only `.ipynb`. The `notebooks/` directory holds the CI-generated notebooks
that Colab and Kaggle link to.

The `.md` files in `tutorials/` remain the canonical source. The `.ipynb` files
in `notebooks/` are derived artifacts — never edit them by hand.

## How badge injection works

The `scripts/convert_to_notebooks.py` script:

1. Scans `tutorials/` for `.md` files with a `kernelspec` in their frontmatter
2. Converts each to `.ipynb` via `jupytext --from md:myst --to notebook`
3. Inserts a markdown cell at position 0 containing Colab and Kaggle badge HTML
4. Writes the result to `notebooks/<day_folder>/<tutorial_name>.ipynb`

The badge URLs are derived from `project.github` in `myst.yml`, so they update
automatically when you fork the template — no hardcoded repo paths.

## Badge URL format

**Colab:**

    https://colab.research.google.com/github/<org>/<repo>/blob/main/notebooks/<path>.ipynb

**Kaggle:**

    https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/<org>/<repo>/main/notebooks/<path>.ipynb

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
<a href="https://colab.research.google.com/github/neuromatch/course-template/blob/main/notebooks/W1D3_PublishingAndCI/W1D3_Tutorial2.ipynb" target="_blank">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>
<a href="https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/neuromatch/course-template/main/notebooks/W1D3_PublishingAndCI/W1D3_Tutorial2.ipynb" target="_blank">
  <img src="https://kaggle.com/static/images/open-in-kaggle.svg" alt="Open In Kaggle"/>
</a>
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

Pages with `jupyter: false` (like `further_reading.md` and `chapter_intro.md`)
are skipped — no notebook is generated for them.
