# JupyterBook 2 Course Template — Design Document

**Date:** 2026-09-22
**Status:** Approved

---

## Overview

A ground-up rewrite of the Neuromatch course template using JupyterBook v2 (MyST). The template is self-referential: it looks, builds, and deploys exactly like a real Neuromatch course, and the content of each tutorial teaches course authors how to use the template.

---

## Philosophy

**MyST is the single source of truth.** Course authors write everything in `.md` (MyST Markdown). Jupyter notebooks (`.ipynb`) are a derivative artifact produced by CI via `jupytext`, not files authors edit directly.

The published book renders MyST natively via `myst build`. Colab and Kaggle badges point to CI-generated `.ipynb` files committed back to the repo under `notebooks/`. The template itself is copied wholesale when starting a new course — there is no separate scaffolding tool.

---

## Repository Structure

```
course-template/
├── myst.yml                              ← single config: metadata, TOC, jupyter settings
├── requirements.txt                      ← mystmd, jupytext, altair, matplotlib, etc.
├── README.md                             ← short repo README linking to the live book
│
├── tutorials/
│   ├── intro.md                          ← course landing page
│   │
│   ├── W1D1_GettingStarted/
│   │   ├── chapter_intro.md              ← day overview: objectives, schedule
│   │   ├── W1D1_Tutorial1.md             ← "Writing content in MyST Markdown"
│   │   ├── W1D1_Tutorial2.md             ← "Structuring your table of contents"
│   │   ├── W1D1_Tutorial3.md             ← "Rich outputs: figures, math, cross-refs"
│   │   ├── W1D1_Bonus.md                 ← "Advanced MyST: tabs, dropdowns, proofs"
│   │   └── further_reading.md            ← static, no kernelspec, jupyter: false
│   │
│   ├── W1D2_InteractiveContent/
│   │   ├── chapter_intro.md
│   │   ├── W1D2_Tutorial1.md             ← "In-browser execution with JupyterLite/Pyodide"
│   │   ├── W1D2_Tutorial2.md             ← "Rich interactive outputs (Altair, widgets)"
│   │   ├── W1D2_Tutorial3.md             ← "When to use .ipynb vs .md"
│   │   ├── W1D2_Bonus.md                 ← "Binder and remote kernel options"
│   │   └── further_reading.md
│   │
│   └── W1D3_PublishingAndCI/
│       ├── chapter_intro.md
│       ├── W1D3_Tutorial1.md             ← "GitHub Actions: build and publish pipeline"
│       ├── W1D3_Tutorial2.md             ← "Colab and Kaggle badges: how they work"
│       ├── W1D3_Tutorial3.md             ← "Customizing: themes, logos, CSS"
│       ├── W1D3_Bonus.md                 ← "Scaling to multi-week courses"
│       └── further_reading.md
│
├── projects/
│   └── README.md                         ← stub: how to structure a project booklet
│
├── notebooks/                            ← CI-generated .ipynb files (committed to repo)
│   ├── W1D2_InteractiveContent/
│   │   ├── W1D2_Tutorial1.ipynb
│   │   ├── W1D2_Tutorial2.ipynb
│   │   └── W1D2_Tutorial3.ipynb
│   └── W1D3_PublishingAndCI/
│       └── W1D3_Tutorial2.ipynb
│
├── scripts/
│   ├── convert_to_notebooks.py           ← jupytext .md→.ipynb + Colab/Kaggle badge injection
│   └── check_links.py                    ← optional: validates badge URLs resolve
│
├── _static/
│   └── custom.css                        ← Neuromatch branding tweaks
│
└── .github/
    └── workflows/
        ├── publish-book.yml              ← myst build --html + deploy to GitHub Pages
        └── generate-notebooks.yml        ← convert .md→.ipynb, commit notebooks/ to main
```

---

## Configuration (`myst.yml`)

```yaml
version: 1
project:
  title: Neuromatch Course Template
  authors:
    - name: Neuromatch
      github: neuromatch
  github: https://github.com/neuromatch/course-template
  license:
    code: BSD-3-Clause
    content: CC-BY-4.0
  jupyter:
    lite: true          # JupyterLite in-browser kernel on all pages by default
  toc:
    - file: tutorials/intro.md
    - title: "Day 1: Getting Started"
      children:
        - file: tutorials/W1D1_GettingStarted/chapter_intro.md
          children:
            - file: tutorials/W1D1_GettingStarted/W1D1_Tutorial1.md
            - file: tutorials/W1D1_GettingStarted/W1D1_Tutorial2.md
            - file: tutorials/W1D1_GettingStarted/W1D1_Tutorial3.md
            - file: tutorials/W1D1_GettingStarted/W1D1_Bonus.md
            - file: tutorials/W1D1_GettingStarted/further_reading.md
    - title: "Day 2: Interactive Content"
      children:
        - file: tutorials/W1D2_InteractiveContent/chapter_intro.md
          children:
            - file: tutorials/W1D2_InteractiveContent/W1D2_Tutorial1.md
            - file: tutorials/W1D2_InteractiveContent/W1D2_Tutorial2.md
            - file: tutorials/W1D2_InteractiveContent/W1D2_Tutorial3.md
            - file: tutorials/W1D2_InteractiveContent/W1D2_Bonus.md
            - file: tutorials/W1D2_InteractiveContent/further_reading.md
    - title: "Day 3: Publishing and CI"
      children:
        - file: tutorials/W1D3_PublishingAndCI/chapter_intro.md
          children:
            - file: tutorials/W1D3_PublishingAndCI/W1D3_Tutorial1.md
            - file: tutorials/W1D3_PublishingAndCI/W1D3_Tutorial2.md
            - file: tutorials/W1D3_PublishingAndCI/W1D3_Tutorial3.md
            - file: tutorials/W1D3_PublishingAndCI/W1D3_Bonus.md
            - file: tutorials/W1D3_PublishingAndCI/further_reading.md
    - file: projects/README.md

site:
  template: book-theme
  options:
    logo: _static/neuromatch_logo.png
    folders: true
```

**Key decisions:**
- `jupyter.lite: true` globally — every page with a `kernelspec` gets the in-browser power button
- Pages without `kernelspec` (e.g. `further_reading.md`) set `jupyter: false` in their own frontmatter to suppress the button
- TOC is hand-authored — no generation script; course creators fork and edit directly

---

## Content Authoring Patterns

### Standard tutorial page (MyST `.md`)

```markdown
---
title: "Tutorial 1: Writing in MyST Markdown"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 1: Writing in MyST Markdown

## Learning objectives

...

## Section

Prose explanation.

```{code-cell} python
import numpy as np
x = np.linspace(0, 2 * np.pi, 100)
```

```{admonition} Exercise 1
Modify the code above to plot a cosine wave.
```
```

### Static page (no execution)

```markdown
---
title: Further Reading
jupyter: false
---

# Further Reading

- Link 1
- Link 2
```

### Rich interactive page (W1D2 tutorials)

Same as standard, but code cells produce Altair charts or ipywidgets that render interactively via JupyterLite. One dedicated page (W1D2_Tutorial1) also demonstrates `pyodide-cell` directives for zero-click in-browser editing.

---

## Notebook Generation Pipeline

### How `.md` → `.ipynb` works

`jupytext --from md:myst --to notebook <file.md>` converts any MyST file with a `kernelspec` frontmatter to a valid `.ipynb`. Only files with `kernelspec` are converted. Files without it (static pages) are skipped.

Colab requires `.ipynb` files — it cannot open `.md` files natively. The generated notebooks are committed back to `notebooks/` in `main`, giving Colab/Kaggle a stable raw GitHub URL to reference.

### `scripts/convert_to_notebooks.py`

Responsibilities:
1. Walk `tutorials/` recursively, find all `.md` files
2. Parse frontmatter — skip any file without `kernelspec`
3. Run `jupytext --from md:myst --to notebook` on each qualifying file
4. Write output to `notebooks/<day_folder>/<tutorial_name>.ipynb`
5. Inject a badge cell (first cell, markdown type) into each notebook containing:
   - Colab badge linking to `https://colab.research.google.com/github/<org>/<repo>/blob/main/notebooks/<path>.ipynb`
   - Kaggle badge linking to `https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/<org>/<repo>/main/notebooks/<path>.ipynb`

The `<org>/<repo>` values are read from `myst.yml` `project.github` at runtime so the script is repo-agnostic when the template is forked.

### GitHub Actions Workflows

**`generate-notebooks.yml`** — triggers on push to `main`:
```
1. pip install -r requirements.txt
2. python scripts/convert_to_notebooks.py
3. git add notebooks/
4. git commit -m "chore: regenerate notebooks from MyST sources" (if changed)
5. git push
```

**`publish-book.yml`** — triggers after `generate-notebooks.yml` succeeds (via `workflow_run`):
```
1. pip install -r requirements.txt
2. myst build --html
3. actions/upload-pages-artifact (_build/html)
4. actions/deploy-pages
```

The two-workflow split ensures the book is always built from the latest committed notebooks (which have the correct badge URLs).

---

## GitHub Pages Deployment

- Pages source: GitHub Actions (not `gh-pages` branch)
- Published URL: `https://neuromatch.github.io/course-template/`
- `myst.yml` sets `site.options.base_url` to match, ensuring JupyterLite kernel assets resolve correctly at the deployed URL
- Local preview: `myst start` (no base URL needed locally)

---

## Decisions and Rationale

| Decision | Rationale |
|---|---|
| MyST `.md` as source of truth | Clean diffs, no output noise in version control, human-readable |
| `notebooks/` committed to repo | Colab/Kaggle require stable raw GitHub URLs; no external artifact store needed |
| `jupyter.lite: true` globally | Every tutorial page gets in-browser execution; no extra per-page config |
| `further_reading.md` opts out | Static pages don't need the kernel button cluttering the UI |
| Hand-authored TOC in `myst.yml` | Eliminates the complex `generate_book.py` script from the old template |
| Two-workflow CI split | Decouples notebook generation from publishing; both steps are individually re-runnable |
| Badge URLs read from `myst.yml` | Fork-friendly; no hardcoded `neuromatch/course-template` strings in the script |
