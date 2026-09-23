# JupyterBook 2 Course Template Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a self-referential Neuromatch course template in JupyterBook v2 (MyST), where the content teaches authors how to use the template, with in-browser Pyodide interactivity, rich outputs, Colab/Kaggle badge injection via CI, and GitHub Pages deployment.

**Architecture:** MyST `.md` files are the source of truth. A CI script uses `jupytext` to convert executable tutorials to `.ipynb`, injects Colab/Kaggle badges, and commits the notebooks back to the repo. A second CI workflow builds the MyST book and deploys it to GitHub Pages.

**Tech Stack:** `mystmd`, `jupytext`, `altair`, `matplotlib`, `numpy`, `pandas`, GitHub Actions, JupyterLite (in-browser via `project.jupyter.lite: true`)

**Design doc:** `docs/plans/2026-09-22-jupyterbook2-course-template-design.md`

---

## Task 1: Project scaffolding and `myst.yml`

**Files:**
- Create: `myst.yml`
- Create: `requirements.txt`
- Modify: `README.md`
- Create: `_static/custom.css`
- Create: `.gitignore`

**Step 1: Create `requirements.txt`**

```
mystmd>=1.3
jupytext>=1.16
altair>=5
vega_datasets
matplotlib
numpy
pandas
ipywidgets
```

**Step 2: Create `myst.yml`**

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
    lite: true
  toc:
    - file: tutorials/intro.md
    - title: "Day 1: Getting Started with MyST"
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
    folders: true
```

**Step 3: Create `_static/custom.css`**

Empty file for now — placeholder for future Neuromatch branding:

```css
/* Neuromatch course template custom styles */
```

**Step 4: Update `.gitignore`**

```
_build/
.jupyter_cache/
__pycache__/
*.pyc
.DS_Store
node_modules/
```

**Step 5: Update `README.md`**

```markdown
# Neuromatch Course Template

A course template built with [JupyterBook v2 (MyST)](https://mystmd.org).

**Live book:** https://neuromatch.github.io/course-template/

## For course authors

Fork this repository and follow the instructions in the book itself.
Each day of this template teaches you how to build and publish your course.

## Local preview

```bash
pip install -r requirements.txt
myst start
```

The book will be available at http://localhost:3000.
```

**Step 6: Verify MyST can initialise**

```bash
pip install mystmd jupytext
myst --version
```

Expected: version string printed, no errors.

**Step 7: Commit**

```bash
git add myst.yml requirements.txt README.md _static/custom.css .gitignore
git commit -m "feat: add myst.yml config, requirements, and project scaffolding"
```

---

## Task 2: Course landing page (`tutorials/intro.md`)

**Files:**
- Create: `tutorials/intro.md`

**Step 1: Create `tutorials/intro.md`**

This is the home page of the book. It explains what the template is and how to use it as a course author.

```markdown
---
title: Welcome to the Neuromatch Course Template
---

# Welcome to the Neuromatch Course Template

This book is both a **working example** of a Neuromatch course and a **guide for course authors**.
Every page you see here demonstrates a real authoring pattern — the content explains the pattern
while the page itself demonstrates it.

## How to use this template

1. **Fork** this repository on GitHub
2. **Replace** the tutorial content with your course material, keeping the file structure
3. **Push** to `main` — GitHub Actions builds and publishes automatically

## What you will learn

| Day | Topic |
|-----|-------|
| Day 1 | Writing course content in MyST Markdown |
| Day 2 | Adding interactive and rich outputs |
| Day 3 | Publishing to GitHub Pages with CI |

## Prerequisites

- A GitHub account
- Basic familiarity with Markdown
- Python (for running notebooks locally)

## Licensing

Content is licensed [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
Code is licensed [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause).
```

**Step 2: Commit**

```bash
git add tutorials/intro.md
git commit -m "feat: add course landing page"
```

---

## Task 3: Day 1 content — Getting Started with MyST

**Files:**
- Create: `tutorials/W1D1_GettingStarted/chapter_intro.md`
- Create: `tutorials/W1D1_GettingStarted/W1D1_Tutorial1.md`
- Create: `tutorials/W1D1_GettingStarted/W1D1_Tutorial2.md`
- Create: `tutorials/W1D1_GettingStarted/W1D1_Tutorial3.md`
- Create: `tutorials/W1D1_GettingStarted/W1D1_Bonus.md`
- Create: `tutorials/W1D1_GettingStarted/further_reading.md`

**Note:** Day 1 tutorials are predominantly prose with minimal code cells — they teach MyST syntax itself. They still have `kernelspec` so authors can run them, but the JupyterLite button is present mainly for demonstration.

**Step 1: Create `chapter_intro.md`**

```markdown
---
title: "Day 1: Getting Started with MyST"
jupyter: false
---

# Day 1: Getting Started with MyST

## Learning objectives

By the end of Day 1 you will be able to:

- Write course content in MyST Markdown
- Understand the structure of a Neuromatch course book
- Use figures, math, admonitions, and cross-references
- Organise your table of contents

## Schedule

| Tutorial | Topic | Duration |
|----------|-------|----------|
| Tutorial 1 | Writing content in MyST Markdown | 30 min |
| Tutorial 2 | Structuring your table of contents | 20 min |
| Tutorial 3 | Rich outputs: figures, math, cross-refs | 30 min |
| Bonus | Advanced MyST: tabs, dropdowns, proofs | open-ended |
```

**Step 2: Create `W1D1_Tutorial1.md` — Writing content in MyST Markdown**

````markdown
---
title: "Tutorial 1: Writing Content in MyST Markdown"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 1: Writing Content in MyST Markdown

MyST (Markedly Structured Text) is the markup language powering this book.
It extends standard Markdown with directives and roles that produce rich,
structured scientific content.

## Why MyST instead of notebooks?

MyST `.md` files are the **source of truth** for this template. Jupyter notebooks
(`.ipynb`) are generated automatically by CI — you never edit them by hand.

Benefits:
- Clean git diffs (no output noise, no cell metadata churn)
- Human-readable in any text editor
- Full Jupyter execution support at build time and in-browser via JupyterLite

## Basic Markdown

Everything standard Markdown supports works in MyST:

- **Bold**, *italic*, `inline code`
- [Links](https://mystmd.org)
- Images: `![alt text](path/to/image.png)`

## Admonitions

Use admonitions to call out notes, warnings, and exercises:

```{note}
This is a note admonition. Use it for supplementary information.
```

```{warning}
This is a warning. Use it to flag common mistakes.
```

```{admonition} Exercise 1.1
Replace the text in this admonition with your own exercise prompt.
Your students will see this highlighted block in the rendered book.
```

## Code cells

Add executable code with the `{code-cell}` directive:

```{code-cell} python
# This cell runs in JupyterLite (in the browser) or via myst build --execute
message = "Hello from MyST!"
print(message)
```

## Hiding cells

Tag cells to control visibility:

```{code-cell} python
:tags: [hide-input]
# Students see the output but not this code
import numpy as np
print(np.pi)
```

```{code-cell} python
:tags: [remove-cell]
# This cell is completely hidden in the rendered book
secret = "only for authors"
```

## Summary

- Write prose in plain Markdown
- Use `{code-cell}` for executable code
- Use admonitions to structure exercises and notes
- Tag cells with `hide-input` or `remove-cell` to control what students see
````

**Step 3: Create `W1D1_Tutorial2.md` — Structuring your TOC**

```markdown
---
title: "Tutorial 2: Structuring Your Table of Contents"
jupyter: false
---

# Tutorial 2: Structuring Your Table of Contents

The table of contents for your book lives entirely in `myst.yml` under `project.toc`.
There is no auto-generation script — you edit it directly.

## The `myst.yml` TOC format

```yaml
project:
  toc:
    - file: tutorials/intro.md          # top-level page
    - title: "Day 1: My Topic"          # section header
      children:
        - file: tutorials/W1D1_MyTopic/chapter_intro.md
          children:                     # nested pages under chapter
            - file: tutorials/W1D1_MyTopic/W1D1_Tutorial1.md
            - file: tutorials/W1D1_MyTopic/further_reading.md
```

## Naming convention

Follow the Neuromatch naming convention for all tutorial files:

```
tutorials/
  W{week}D{day}_{TopicName}/
    chapter_intro.md
    W{week}D{day}_Tutorial1.md
    W{week}D{day}_Tutorial2.md
    W{week}D{day}_Tutorial3.md
    W{week}D{day}_Bonus.md
    further_reading.md
```

For example: `tutorials/W2D3_ReinforcementLearning/W2D3_Tutorial1.md`

## Adding a new day

1. Create the folder: `tutorials/W2D1_MyNewTopic/`
2. Create the files following the naming convention above
3. Add an entry to `project.toc` in `myst.yml`
4. Push to `main` — CI handles the rest

## `further_reading.md` pages

These are always static — no code execution. Add `jupyter: false` to their frontmatter
so the JupyterLite power button does not appear.
```

**Step 4: Create `W1D1_Tutorial3.md` — Rich outputs**

````markdown
---
title: "Tutorial 3: Rich Outputs — Figures, Math, Cross-References"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 3: Rich Outputs

MyST supports a full range of scientific publishing features natively.

## Figures with captions

```{figure} https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/24701-nature-natural-beauty.jpg/320px-24701-nature-natural-beauty.jpg
:label: fig-example
:alt: A nature photograph used as a placeholder figure
:width: 60%

A figure with a caption and a label. Reference it elsewhere as {numref}`fig-example`.
```

## Math

Inline math: $E = mc^2$

Display math:

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$ (eq-gaussian)

Reference equations: see {eq}`eq-gaussian`.

## Cross-references

Label any heading, figure, or equation with `(label)=` and reference it with `{ref}`:

(sec-crossref)=
## This section has a label

Refer back to it: {ref}`sec-crossref`.

## Matplotlib figures from code

```{code-cell} python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(6, 3))
x = np.linspace(0, 2 * np.pi, 200)
ax.plot(x, np.sin(x), label="sin(x)")
ax.plot(x, np.cos(x), label="cos(x)")
ax.legend()
ax.set_xlabel("x")
ax.set_title("Trigonometric functions")
plt.tight_layout()
```

## Tables

| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

## Summary

- Use `{figure}` for captioned images
- Use `$$` for display math with optional labels
- Use `(label)=` syntax to label headings and cross-reference them
- Code cells produce embedded figures automatically
````

**Step 5: Create `W1D1_Bonus.md` — Advanced MyST**

````markdown
---
title: "Bonus: Advanced MyST — Tabs, Dropdowns, Proofs"
jupyter: false
---

# Bonus: Advanced MyST

## Tabbed content

````{tab-set}
```{tab-item} Python
print("Hello from Python")
```
```{tab-item} Julia
println("Hello from Julia")
```
````

## Dropdown (collapsible) blocks

```{dropdown} Click to reveal the solution
Here is the solution to the exercise. Use dropdowns to hide answers.
```

## Proof environments

```{prf:theorem} Bayes' Theorem
:label: thm-bayes

$$P(A|B) = \frac{P(B|A) P(A)}{P(B)}$$
```

```{prf:proof}
Follows directly from the definition of conditional probability.
```

## Margin notes

```{margin}
Margin notes appear in the right gutter on wide screens.
```

Main content continues here.

## Footnotes

Use standard Markdown footnotes[^1].

[^1]: This appears at the bottom of the page.
````

**Step 6: Create `further_reading.md`**

```markdown
---
title: Further Reading
jupyter: false
---

# Further Reading

## MyST documentation

- [MyST Markdown Guide](https://mystmd.org/guide)
- [MyST Syntax Reference](https://mystmd.org/spec)
- [JupyterBook documentation](https://jupyterbook.org)

## Neuromatch resources

- [Neuromatch Academy](https://neuromatch.io)
- [Existing course content (JupyterBook v1)](https://compneuro.neuromatch.io)
```

**Step 7: Commit**

```bash
git add tutorials/W1D1_GettingStarted/
git commit -m "feat: add Day 1 Getting Started tutorials"
```

---

## Task 4: Day 2 content — Interactive Content

**Files:**
- Create: `tutorials/W1D2_InteractiveContent/chapter_intro.md`
- Create: `tutorials/W1D2_InteractiveContent/W1D2_Tutorial1.md`
- Create: `tutorials/W1D2_InteractiveContent/W1D2_Tutorial2.md`
- Create: `tutorials/W1D2_InteractiveContent/W1D2_Tutorial3.md`
- Create: `tutorials/W1D2_InteractiveContent/W1D2_Bonus.md`
- Create: `tutorials/W1D2_InteractiveContent/further_reading.md`

**Note:** Day 2 tutorials have `kernelspec` and contain rich interactive outputs (Altair charts, widgets). These get converted to `.ipynb` by CI.

**Step 1: Create `chapter_intro.md`**

```markdown
---
title: "Day 2: Interactive Content"
jupyter: false
---

# Day 2: Interactive Content

## Learning objectives

- Use JupyterLite for in-browser code execution (no server needed)
- Produce interactive Altair visualisations
- Use ipywidgets for interactive controls
- Understand when to use `.ipynb` vs `.md`

## Schedule

| Tutorial | Topic | Duration |
|----------|-------|----------|
| Tutorial 1 | In-browser execution with JupyterLite | 30 min |
| Tutorial 2 | Rich interactive outputs | 30 min |
| Tutorial 3 | When to use `.ipynb` vs `.md` | 20 min |
| Bonus | Binder and remote kernel options | open-ended |
```

**Step 2: Create `W1D2_Tutorial1.md` — JupyterLite / Pyodide**

````markdown
---
title: "Tutorial 1: In-Browser Execution with JupyterLite"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 1: In-Browser Execution with JupyterLite

This book uses **JupyterLite** to run Python directly in your browser.
No server, no installation required — everything runs via WebAssembly (WASM).

## How to activate in-browser execution

Click the **power button** (⚡) at the top right of this page.
After ~10 seconds of initialisation, all code cells become live and editable.

## Try it: basic computation

```{code-cell} python
# Click the power button, then run this cell
result = sum(range(1, 101))
print(f"Sum of 1 to 100: {result}")
```

## Try it: NumPy in the browser

```{code-cell} python
import numpy as np

arr = np.random.randn(1000)
print(f"Mean: {arr.mean():.4f}")
print(f"Std:  {arr.std():.4f}")
```

## Try it: matplotlib in the browser

```{code-cell} python
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(8, 3))

x = np.linspace(-3, 3, 300)
axes[0].plot(x, np.tanh(x))
axes[0].set_title("tanh(x)")

axes[1].hist(np.random.randn(500), bins=30)
axes[1].set_title("Random normal")

plt.tight_layout()
```

## How JupyterLite works in this template

In `myst.yml`, the setting `project.jupyter.lite: true` enables the in-browser
kernel for all pages that have a `kernelspec` in their frontmatter.

Pages without `kernelspec` (like `further_reading.md`) set `jupyter: false` to
suppress the power button.

```{note}
JupyterLite supports most pure-Python packages. Packages with C extensions
(like `scipy`, `torch`) may not be available or may be slow to load.
For compute-heavy days, use Colab or Kaggle instead.
```

## For students: opening in Colab

Every tutorial page that has executable code also has **Colab** and **Kaggle** badges
at the top of its notebook. These are injected automatically by CI — you do not add
them manually. See Day 3, Tutorial 2 for how this works.
````

**Step 3: Create `W1D2_Tutorial2.md` — Rich interactive outputs**

````markdown
---
title: "Tutorial 2: Rich Interactive Outputs"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 2: Rich Interactive Outputs

MyST renders interactive outputs from Altair, Plotly, and ipywidgets natively.
These work both in the static build (pre-rendered) and live via JupyterLite.

## Interactive Altair chart

Altair charts are fully interactive in the rendered book — no kernel required.
Drag to select points; the bar chart updates in real time.

```{code-cell} python
import altair as alt
from vega_datasets import data

source = data.cars()
brush = alt.selection_interval(encodings=["x"])

points = alt.Chart(source).mark_point().encode(
    x="Horsepower:Q",
    y="Miles_per_Gallon:Q",
    color=alt.condition(brush, "Origin:N", alt.value("lightgray")),
).add_params(brush)

bars = alt.Chart(source).mark_bar().encode(
    y="Origin:N",
    color="Origin:N",
    x="count(Origin):Q",
).transform_filter(brush)

points & bars
```

## ipywidgets slider

With the JupyterLite kernel active, this slider is live:

```{code-cell} python
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

def plot_wave(frequency=1.0):
    x = np.linspace(0, 2 * np.pi, 300)
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(x, np.sin(frequency * x))
    ax.set_title(f"sin({frequency}x)")
    plt.tight_layout()
    plt.show()

widgets.interact(plot_wave, frequency=(0.5, 5.0, 0.5))
```

## Pandas DataFrame output

```{code-cell} python
import pandas as pd
from vega_datasets import data

df = data.cars().iloc[:5, :5]
df
```

## Embedding outputs across pages

Label a cell output to reuse it elsewhere in the book:

```{code-cell} python
#| label: fig-cars-scatter
import matplotlib.pyplot as plt
from vega_datasets import data

df = data.cars()
fig, ax = plt.subplots(figsize=(5, 3))
ax.scatter(df["Horsepower"], df["Miles_per_Gallon"], alpha=0.4)
ax.set_xlabel("Horsepower")
ax.set_ylabel("Miles per gallon")
plt.tight_layout()
```

Reference it on another page with:
```
{embed}`fig-cars-scatter`
```
````

**Step 4: Create `W1D2_Tutorial3.md` — `.ipynb` vs `.md`**

```markdown
---
title: "Tutorial 3: When to Use .ipynb vs .md"
jupyter: false
---

# Tutorial 3: When to Use `.ipynb` vs `.md`

## The default: write in MyST `.md`

For most Neuromatch tutorials, write in MyST `.md`. CI converts these to `.ipynb`
automatically for Colab/Kaggle. Benefits:

- Clean git history — no output noise, no metadata churn
- Readable in any text editor
- Easy code review
- Re-executed at build time to ensure reproducibility

## When to author directly in `.ipynb`

Use `.ipynb` directly when:

- **Compute-heavy tutorials**: the notebook requires a GPU or takes >5 minutes to run.
  Pre-execute it, commit the outputs, and let MyST render the stored outputs.
- **Complex widget state**: interactive widgets whose state must be preserved between sessions.
- **External contribution**: a collaborator submits a notebook; accept it as `.ipynb`
  and the badge injection script handles it automatically.

## How CI handles `.ipynb` files

The `scripts/convert_to_notebooks.py` script handles both sources:

1. **From `.md`**: converts with `jupytext`, then injects badges
2. **From `.ipynb`** (authored directly): injects badges only, writes to `notebooks/`

In both cases, the source file in `tutorials/` is never modified.

## Practical rule

> If in doubt, write `.md`. Use `.ipynb` only when you need stored outputs.
```

**Step 5: Create `W1D2_Bonus.md` — Binder and remote kernels**

```markdown
---
title: "Bonus: Binder and Remote Kernel Options"
jupyter: false
---

# Bonus: Binder and Remote Kernel Options

JupyterLite (in-browser) is the default for this template. For compute-heavy content
or packages not supported by WASM, you can switch to a remote kernel.

## Using Binder

Add to `myst.yml`:

```yaml
project:
  jupyter:
    binder:
      repo: your-org/your-repo
      ref: main
```

This replaces JupyterLite with a Binder-backed kernel. Students click the power button
and a mybinder.org session launches (~30–60 seconds cold start).

## Using a custom BinderHub

```yaml
project:
  jupyter:
    binder:
      url: https://binder.myorganisation.com/services/binder/
      repo: your-org/your-repo
```

## Using JupyterHub

If your institution runs JupyterHub, students can launch sessions there:

```yaml
project:
  jupyter:
    server:
      url: https://hub.myuniversity.edu
```

## Mixing strategies

You can override the project default on individual pages using frontmatter:

```yaml
---
jupyter:
  binder:
    repo: your-org/compute-heavy-repo
---
```

Or disable execution entirely on a page:

```yaml
---
jupyter: false
---
```
```

**Step 6: Create `further_reading.md`**

```markdown
---
title: Further Reading
jupyter: false
---

# Further Reading

## JupyterLite and Pyodide

- [JupyterLite documentation](https://jupyterlite.readthedocs.io)
- [Pyodide — Python in the browser](https://pyodide.org)
- [MyST in-page execution guide](https://mystmd.org/guide/in-page-execution)

## Rich outputs

- [MyST interactive notebooks guide](https://mystmd.org/guide/interactive-notebooks)
- [Altair documentation](https://altair-viz.github.io)
- [ipywidgets documentation](https://ipywidgets.readthedocs.io)
```

**Step 7: Commit**

```bash
git add tutorials/W1D2_InteractiveContent/
git commit -m "feat: add Day 2 Interactive Content tutorials"
```

---

## Task 5: Day 3 content — Publishing and CI

**Files:**
- Create: `tutorials/W1D3_PublishingAndCI/chapter_intro.md`
- Create: `tutorials/W1D3_PublishingAndCI/W1D3_Tutorial1.md`
- Create: `tutorials/W1D3_PublishingAndCI/W1D3_Tutorial2.md`
- Create: `tutorials/W1D3_PublishingAndCI/W1D3_Tutorial3.md`
- Create: `tutorials/W1D3_PublishingAndCI/W1D3_Bonus.md`
- Create: `tutorials/W1D3_PublishingAndCI/further_reading.md`

**Step 1: Create `chapter_intro.md`**

```markdown
---
title: "Day 3: Publishing and CI"
jupyter: false
---

# Day 3: Publishing and CI

## Learning objectives

- Set up GitHub Actions to build and publish your book automatically
- Understand how Colab and Kaggle badges are injected at build time
- Customise your book's theme, logo, and CSS

## Schedule

| Tutorial | Topic | Duration |
|----------|-------|----------|
| Tutorial 1 | GitHub Actions: build and publish pipeline | 30 min |
| Tutorial 2 | Colab and Kaggle badges: how they work | 20 min |
| Tutorial 3 | Customising your book | 20 min |
| Bonus | Scaling to multi-week courses | open-ended |
```

**Step 2: Create `W1D3_Tutorial1.md` — GitHub Actions**

````markdown
---
title: "Tutorial 1: GitHub Actions — Build and Publish Pipeline"
jupyter: false
---

# Tutorial 1: GitHub Actions — Build and Publish Pipeline

This template ships with two GitHub Actions workflows that run automatically on every
push to `main`.

## Workflow 1: `generate-notebooks.yml`

Converts MyST `.md` tutorials to `.ipynb` and commits them back to the repo.

```yaml
# .github/workflows/generate-notebooks.yml
name: Generate Notebooks

on:
  push:
    branches: [main]
    paths:
      - "tutorials/**"
      - "scripts/convert_to_notebooks.py"

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python scripts/convert_to_notebooks.py
      - name: Commit notebooks
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add notebooks/
          git diff --cached --quiet || git commit -m "chore: regenerate notebooks [skip ci]"
          git push
```

## Workflow 2: `publish-book.yml`

Builds the MyST book and deploys it to GitHub Pages.

```yaml
# .github/workflows/publish-book.yml
name: Publish Book

on:
  push:
    branches: [main]
  workflow_run:
    workflows: ["Generate Notebooks"]
    types: [completed]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: myst build --html
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

The notebook generation workflow commits back to `main`. To prevent this from
triggering an infinite loop, the commit message includes `[skip ci]` — GitHub
Actions ignores pushes with this tag.
````

**Step 3: Create `W1D3_Tutorial2.md` — Colab and Kaggle badges**

````markdown
---
title: "Tutorial 2: Colab and Kaggle Badges"
kernelspec:
  name: python3
  display_name: Python 3
---

# Tutorial 2: Colab and Kaggle Badges

This tutorial is itself an example of a page that gets converted to `.ipynb` and
receives Colab and Kaggle badges. Look for them at the top of the notebook version.

## How badge injection works

The `scripts/convert_to_notebooks.py` script:

1. Scans `tutorials/` for `.md` files with a `kernelspec` frontmatter
2. Converts each to `.ipynb` via `jupytext`
3. Inserts a markdown cell at position 0 containing badge HTML
4. Writes the result to `notebooks/<day>/<tutorial>.ipynb`

The badge URLs are derived from `project.github` in `myst.yml`, so they update
automatically when you fork the template.

## Badge URL format

**Colab:**
```
https://colab.research.google.com/github/<org>/<repo>/blob/main/notebooks/<path>.ipynb
```

**Kaggle:**
```
https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/<org>/<repo>/main/notebooks/<path>.ipynb
```

## Why `.ipynb` files are committed to the repo

Colab and Kaggle fetch notebooks from **raw GitHub URLs**. They cannot open `.md` files.
The generated `.ipynb` files in `notebooks/` provide the stable URLs these services need.

The `.md` files remain the canonical source — the `.ipynb` files are derived artifacts.

## Running the script locally

```{code-cell} python
import subprocess
result = subprocess.run(
    ["python", "scripts/convert_to_notebooks.py", "--dry-run"],
    capture_output=True, text=True
)
print(result.stdout)
```

## What the badge cell looks like

The injected markdown cell contains:

```html
<a href="https://colab.research.google.com/github/..."><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
<a href="https://kaggle.com/kernels/welcome?src=..."><img src="https://kaggle.com/static/images/open-in-kaggle.svg" alt="Open In Kaggle"/></a>
```
````

**Step 4: Create `W1D3_Tutorial3.md` — Customising your book**

```markdown
---
title: "Tutorial 3: Customising Your Book"
jupyter: false
---

# Tutorial 3: Customising Your Book

## Changing the title and metadata

Edit `myst.yml`:

```yaml
project:
  title: Computational Neuroscience 2027
  authors:
    - name: Your Name
      github: your-github-username
  github: https://github.com/your-org/your-course-repo
```

## Adding a logo

Place your logo at `_static/your_logo.png` and update `myst.yml`:

```yaml
site:
  options:
    logo: _static/your_logo.png
```

## Custom CSS

Edit `_static/custom.css` to override any book styles:

```css
/* Change the primary colour */
:root {
  --color-primary: #FF6B6B;
}

/* Style exercise admonitions */
.admonition.exercise {
  border-left-color: #4ECDC4;
}
```

## Choosing a different theme

MyST ships with `book-theme` by default. To list available themes:

```bash
myst templates list --site
```

Set a theme in `myst.yml`:

```yaml
site:
  template: book-theme   # the only stable option as of 2026
```

## Enabling Binder launch buttons

Add a `project.binder` URL to show a Binder badge on every page:

```yaml
project:
  binder: https://mybinder.org/v2/gh/your-org/your-repo/HEAD
```
```

**Step 5: Create `W1D3_Bonus.md` — Scaling to multi-week courses**

```markdown
---
title: "Bonus: Scaling to Multi-Week Courses"
jupyter: false
---

# Bonus: Scaling to Multi-Week Courses

The template ships with one week (W1D1–W1D3). Here is how to extend it.

## Adding more days

1. Create `tutorials/W1D4_NewTopic/` with the standard file structure
2. Add the entries to `project.toc` in `myst.yml`
3. Push — CI handles the rest

## Adding more weeks

Same pattern — just increment the week number:

```
tutorials/
  W2D1_AdvancedTopic/
  W2D2_AnotherTopic/
  ...
```

Update `myst.yml` accordingly. There is no limit on depth.

## Projects section

The `projects/` directory holds the project booklet. Add markdown files there
and register them in the TOC under a "Project Booklet" section.

## Precourse content

Create a `W0D1_Precourse/` directory for prerequisite material. Register it as the
first section in the TOC.

## Splitting content across repos

For large courses where content lives in separate repos, the recommended approach is
to use git submodules or GitHub Actions to fetch content into `tutorials/` at build
time. Document the fetch step in your `publish-book.yml`.
```

**Step 6: Create `further_reading.md`**

```markdown
---
title: Further Reading
jupyter: false
---

# Further Reading

## GitHub Actions

- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [actions/deploy-pages](https://github.com/actions/deploy-pages)

## MyST deployment

- [MyST deployment guide](https://mystmd.org/guide/deployment)
- [MyST GitHub Pages deployment](https://mystmd.org/guide/deployment-github-pages)

## Jupytext

- [Jupytext documentation](https://jupytext.readthedocs.io)
- [MyST Markdown format in Jupytext](https://jupytext.readthedocs.io/en/latest/formats-myst.html)
```

**Step 7: Commit**

```bash
git add tutorials/W1D3_PublishingAndCI/
git commit -m "feat: add Day 3 Publishing and CI tutorials"
```

---

## Task 6: Projects stub

**Files:**
- Create: `projects/README.md`

**Step 1: Create `projects/README.md`**

```markdown
---
title: Project Booklet
jupyter: false
---

# Project Booklet

This section contains the project materials for the course.

## How to structure your project booklet

Add your project guidance documents to the `projects/` directory and register
them in `project.toc` in `myst.yml` under a "Project Booklet" section:

```yaml
- title: Project Booklet
  children:
    - file: projects/README.md
    - file: projects/project_guidance.md
    - file: projects/datasets.md
```

## Template placeholder

Replace this file with your actual project introduction. Include:

- Overview of the project format
- Timeline and milestones
- Links to datasets
- Guidance on the modelling workflow
```

**Step 2: Commit**

```bash
git add projects/README.md
git commit -m "feat: add projects booklet stub"
```

---

## Task 7: Notebook conversion script

**Files:**
- Create: `scripts/convert_to_notebooks.py`

**Step 1: Create `scripts/convert_to_notebooks.py`**

```python
"""
Convert MyST Markdown tutorials to Jupyter notebooks and inject Colab/Kaggle badges.

Usage:
    python scripts/convert_to_notebooks.py [--dry-run]

For each .md file in tutorials/ that has a kernelspec frontmatter:
  1. Convert to .ipynb via jupytext
  2. Inject a Colab + Kaggle badge cell at position 0
  3. Write to notebooks/<day_folder>/<tutorial_name>.ipynb

The GitHub repo URL is read from myst.yml (project.github) so this script
works correctly when the template is forked.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


TUTORIALS_DIR = Path("tutorials")
NOTEBOOKS_DIR = Path("notebooks")
MYST_CONFIG = Path("myst.yml")


def load_github_repo(myst_config: Path) -> str:
    """
    Read project.github from myst.yml and return 'org/repo' string.

    Example: 'https://github.com/neuromatch/course-template' -> 'neuromatch/course-template'
    """
    with myst_config.open() as fh:
        config = yaml.safe_load(fh)

    github_url = config.get("project", {}).get("github", "")
    if not github_url:
        raise ValueError("project.github is not set in myst.yml")

    # Strip trailing slash then extract org/repo
    github_url = github_url.rstrip("/")
    match = re.search(r"github\.com/(.+)", github_url)
    if not match:
        raise ValueError(f"Cannot parse GitHub repo from: {github_url}")

    return match.group(1)  # e.g. 'neuromatch/course-template'


def has_kernelspec(md_file: Path) -> bool:
    """Return True if the file has a kernelspec key in its YAML frontmatter."""
    content = md_file.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False

    # Extract frontmatter block
    end = content.find("---", 3)
    if end == -1:
        return False

    frontmatter_text = content[3:end]
    try:
        fm = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return False

    return isinstance(fm, dict) and "kernelspec" in fm


def make_badge_cell(notebook_rel_path: str, github_repo: str) -> dict:
    """
    Return a Jupyter markdown cell containing Colab and Kaggle badge links.

    notebook_rel_path: path relative to repo root, e.g.
        'notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb'
    github_repo: 'org/repo' string, e.g. 'neuromatch/course-template'
    """
    colab_url = (
        f"https://colab.research.google.com/github/{github_repo}"
        f"/blob/main/{notebook_rel_path}"
    )
    kaggle_url = (
        f"https://kaggle.com/kernels/welcome?src="
        f"https://raw.githubusercontent.com/{github_repo}/main/{notebook_rel_path}"
    )

    badge_html = (
        f'<a href="{colab_url}" target="_blank">'
        f'<img src="https://colab.research.google.com/assets/colab-badge.svg" '
        f'alt="Open In Colab"/></a>\n'
        f'<a href="{kaggle_url}" target="_blank">'
        f'<img src="https://kaggle.com/static/images/open-in-kaggle.svg" '
        f'alt="Open In Kaggle"/></a>'
    )

    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [badge_html],
    }


def convert_md_to_notebook(md_file: Path, out_path: Path, dry_run: bool) -> None:
    """Convert a MyST .md file to .ipynb using jupytext."""
    print(f"  Converting: {md_file} -> {out_path}")
    if dry_run:
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "jupytext",
            "--from", "md:myst",
            "--to", "notebook",
            "--output", str(out_path),
            str(md_file),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: jupytext failed for {md_file}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)


def inject_badges(notebook_path: Path, github_repo: str, dry_run: bool) -> None:
    """Insert Colab/Kaggle badge cell at position 0 in the notebook."""
    notebook_rel = str(notebook_path).replace("\\", "/")
    badge_cell = make_badge_cell(notebook_rel, github_repo)

    print(f"  Injecting badges: {notebook_path}")
    if dry_run:
        return

    with notebook_path.open(encoding="utf-8") as fh:
        nb = json.load(fh)

    # Remove any existing badge cell (idempotency)
    nb["cells"] = [
        c for c in nb["cells"]
        if "colab-badge.svg" not in "".join(c.get("source", []))
    ]

    nb["cells"].insert(0, badge_cell)

    with notebook_path.open("w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)


def process_md_files(github_repo: str, dry_run: bool) -> int:
    """Walk tutorials/ and process all qualifying .md files. Returns count processed."""
    count = 0
    for md_file in sorted(TUTORIALS_DIR.rglob("*.md")):
        if not has_kernelspec(md_file):
            continue

        # Determine output path: notebooks/<day_folder>/<tutorial>.ipynb
        # md_file = tutorials/W1D2_InteractiveContent/W1D2_Tutorial1.md
        # out_path = notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb
        relative_to_tutorials = md_file.relative_to(TUTORIALS_DIR)
        out_path = NOTEBOOKS_DIR / relative_to_tutorials.with_suffix(".ipynb")

        convert_md_to_notebook(md_file, out_path, dry_run)
        inject_badges(out_path, github_repo, dry_run)
        count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert MyST tutorials to notebooks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no files will be written\n")

    github_repo = load_github_repo(MYST_CONFIG)
    print(f"GitHub repo: {github_repo}")

    count = process_md_files(github_repo, args.dry_run)
    print(f"\nDone. Processed {count} tutorial(s).")


if __name__ == "__main__":
    main()
```

**Step 2: Make it executable and verify syntax**

```bash
python -c "import ast; ast.parse(open('scripts/convert_to_notebooks.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

**Step 3: Run a dry-run locally**

```bash
pip install -r requirements.txt
python scripts/convert_to_notebooks.py --dry-run
```

Expected: lists the tutorials that would be processed with no errors.

**Step 4: Run for real and inspect output**

```bash
python scripts/convert_to_notebooks.py
ls notebooks/
```

Expected: `notebooks/W1D2_InteractiveContent/` and `notebooks/W1D3_PublishingAndCI/` directories with `.ipynb` files.

**Step 5: Verify badge cell is present in a generated notebook**

```bash
python -c "
import json
nb = json.load(open('notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb'))
print(nb['cells'][0]['source'])
"
```

Expected: HTML containing `colab-badge.svg` and `open-in-kaggle.svg`.

**Step 6: Commit**

```bash
git add scripts/convert_to_notebooks.py notebooks/
git commit -m "feat: add notebook conversion script and generated notebooks"
```

---

## Task 8: GitHub Actions workflows

**Files:**
- Create: `.github/workflows/generate-notebooks.yml`
- Create: `.github/workflows/publish-book.yml`

**Step 1: Create `.github/workflows/generate-notebooks.yml`**

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
            git commit -m "chore: regenerate notebooks from MyST sources [skip ci]"
            git push
          fi
```

**Step 2: Create `.github/workflows/publish-book.yml`**

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

      - name: Upload pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: _build/html

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**Step 3: Commit**

```bash
git add .github/workflows/
git commit -m "feat: add GitHub Actions workflows for notebook generation and book publishing"
```

---

## Task 9: Local build verification

**Step 1: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 2: Run notebook conversion**

```bash
python scripts/convert_to_notebooks.py
```

Expected: no errors; `notebooks/` populated.

**Step 3: Build the book**

```bash
myst build --html
```

Expected: completes without errors. Check `_build/html/index.html` exists.

**Step 4: Preview locally**

```bash
myst start
```

Open `http://localhost:3000`. Verify:
- [ ] Landing page renders
- [ ] All three days appear in the sidebar
- [ ] Code cells render (static outputs or execution)
- [ ] Altair chart on W1D2_Tutorial2 is interactive
- [ ] JupyterLite power button appears on pages with `kernelspec`
- [ ] Power button does NOT appear on `further_reading.md` pages
- [ ] Math renders correctly on W1D1_Tutorial3

**Step 5: Commit any fixes found during preview**

```bash
git add -A
git commit -m "fix: local build verification fixes"
```

---

## Task 10: GitHub Pages setup and final push

**Step 1: Push all commits to `main`**

```bash
git push origin main
```

**Step 2: Configure GitHub Pages**

In the GitHub repo:
1. Go to **Settings → Pages**
2. Set **Source** to `GitHub Actions`
3. Save

**Step 3: Monitor the Actions tab**

Watch both workflows run:
- `Generate Notebooks` runs first, commits `notebooks/` if anything changed
- `Publish Book` runs after, deploys to GitHub Pages

Expected: both workflows show green checkmarks.

**Step 4: Verify the live site**

Open `https://neuromatch.github.io/course-template/` and verify:
- [ ] Book loads correctly
- [ ] All pages accessible from sidebar
- [ ] Altair charts interactive
- [ ] JupyterLite power button functional (may take ~10s to initialise)
- [ ] Colab and Kaggle badges visible on notebook pages

**Step 5: Final commit if any adjustments needed**

```bash
git add -A
git commit -m "fix: post-deployment adjustments"
git push origin main
```

---

## Appendix: How course authors fork and use this template

1. Click **Use this template** on GitHub (or fork)
2. Clone the new repo
3. Edit `myst.yml`: update `project.title`, `project.authors`, `project.github`
4. Replace tutorial content in `tutorials/` — keep the folder and file naming convention
5. Delete days you don't need; add new ones following the `W#D#_TopicName` pattern
6. Push to `main` — GitHub Actions generates notebooks and publishes the book automatically

The Colab/Kaggle badge URLs update automatically because `convert_to_notebooks.py`
reads `project.github` from `myst.yml`.
