# AGENTS.md

Context for AI agents working on this repository.

## Project Overview

Neuromatch course template built with MyST (Markedly Structured Text). MyST `.md` files in `tutorials/` are the single source of truth. Jupyter notebooks (`.ipynb`) are generated artifacts, never authored directly. The rendered book deploys to GitHub Pages via CI.

## Architecture

```
myst.yml                    # Single config: metadata, TOC, JupyterLite, site theme
tutorials/
  intro.md                  # Landing page
  W{week}D{day}_{Topic}/    # One directory per day
    chapter_intro.md         # Day overview, learning objectives, schedule table
    W{w}D{d}_Tutorial1.md   # Tutorial pages (may have kernelspec)
    W{w}D{d}_Tutorial2.md
    W{w}D{d}_Bonus.md       # Open-ended bonus
    further_reading.md       # Static links page
scripts/
  convert_to_notebooks.py   # Converts .md -> .ipynb, injects Colab/Kaggle badges
_wheels/                     # Pre-built .whl files for Pyodide (CORS-friendly hosting)
_static/
  custom.css                 # Custom CSS for the book theme
projects/
  README.md                  # Project booklet placeholder
notebooks/                   # Generated .ipynb files (gitignored, lives on notebooks-branch)
.github/workflows/
  generate-notebooks.yml     # Converts tutorials, pushes to notebooks-branch
  publish-book.yml           # Builds MyST book, deploys to GitHub Pages
  build-pyodide-wheels.yml   # Builds wheels for packages missing them on PyPI
```

### Key files

- **`myst.yml`** -- the only config file. Contains project metadata, hand-authored TOC, JupyterLite settings (`project.jupyter.lite: true`), and site theme. There is no `_toc.yml` or `_config.yml`.
- **`scripts/convert_to_notebooks.py`** -- reads `project.github` from `myst.yml` to generate fork-friendly badge URLs. Idempotent.
- **`requirements.txt`** -- Python dependencies: mystmd, jupytext, numpy, matplotlib, etc.
- **`.nvmrc`** -- Node.js version (22). MyST requires Node >= 20.

## Key Conventions

### Executable vs static pages

A page with `kernelspec` in its YAML frontmatter is executable:

```yaml
---
title: "Tutorial 1: Some Topic"
kernelspec:
  name: python3
  display_name: Python 3
---
```

This means:
- JupyterLite power button appears (in-browser execution)
- `convert_to_notebooks.py` generates a `.ipynb` from it
- CI injects Colab/Kaggle badges

A page without `kernelspec` is static (chapter intros, further reading, bonus pages without code).

### Badges

Never add badge HTML to `.md` files manually. The `convert_to_notebooks.py` script injects them automatically. Badge injection is idempotent but adds a blank line on each re-run -- if you run the script locally, revert changes to existing tutorials before committing.

### Code cell tags

```markdown
```{code-cell} python
# Regular cell -- fully visible, editable in JupyterLite
```

```{code-cell} python
:tags: [hide-input]
# Code hidden behind toggle, output visible. Used for:
# - Solutions (# to_remove solution)
# - Explanations (# to_remove explanation)
# - Infrastructure (video players, plotting functions, feedback widgets)
# - Interactive widgets (@widgets.interact)
```

```{code-cell} python
:tags: [remove-cell]
# Completely hidden. Used for setup code (e.g., micropip installs)
```
```

Exercise cells (containing `raise NotImplementedError`) must have NO tags so students can see and edit them.

### LaTeX

MyST uses KaTeX, not MathJax. Common incompatibilities:

| Does NOT work (LaTeX) | Use instead (KaTeX) |
|---|---|
| `\begin{eqnarray}` | `\begin{aligned}` wrapped in `$$` |
| `\begin{array} & a & b` | `\begin{bmatrix} a & b` |
| `\\\\` (double backslash) in `eqnarray` | `\\` in `aligned` |

Always test math rendering with `myst build --html`.

## Build & CI

### Local preview

```bash
# Requires Node >= 20 (use nvm if needed)
export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh" && nvm use 22
uv run myst start          # Dev server at localhost:3000
uv run myst build --html   # Full build to _build/html/
```

### Notebook conversion (local, optional)

```bash
uv run python scripts/convert_to_notebooks.py           # Convert all
uv run python scripts/convert_to_notebooks.py --dry-run  # Preview only
```

Warning: this modifies `.md` files in-place (badge injection). Revert unintended changes to existing tutorials with `git checkout origin/main -- tutorials/W1D*/`.

### CI pipelines

1. **`generate-notebooks.yml`** -- triggers on push to `main` when `tutorials/`, `scripts/`, `myst.yml`, or `requirements.txt` change. Converts `.md` -> `.ipynb`, pushes to `notebooks-branch`.
2. **`publish-book.yml`** -- triggers after `generate-notebooks.yml` completes or on push to `main`. Builds MyST book, deploys to GitHub Pages.
3. **`build-pyodide-wheels.yml`** -- manual trigger (`workflow_dispatch`). Builds pure-Python wheels for packages that lack them on PyPI, uploads as GitHub Release assets.

### Adding a new day

1. Create `tutorials/W{w}D{d}_{Topic}/` with `chapter_intro.md`, tutorial `.md` files, `further_reading.md`
2. Add the TOC entry in `myst.yml` under `project.toc`. Make `- file: tutorials/W{w}D{d}_{Topic}/chapter_intro.md` the top-level entry and list the tutorials under it as `children`. Don't wrap it in a `title:` group, because that makes the day appear twice in the sidebar.
3. Validate: `python3 -c "import yaml; yaml.safe_load(open('myst.yml'))"`

## Pyodide / JupyterLite

### Bundled packages

numpy, matplotlib, scipy, pandas, altair -- available in Pyodide out of the box.

### Packages needing micropip

ipywidgets, vibecheck, datatops -- install via micropip in a setup cell.

### Wheel hosting (CORS)

Micropip fetches wheels from URLs in the browser. **GitHub Releases URLs are NOT CORS-friendly** -- they block `Access-Control-Allow-Origin`. Use `raw.githubusercontent.com` instead, which sends proper CORS headers.

Pre-built wheels live in `_wheels/` and are served via:
```
https://raw.githubusercontent.com/neuromatch/course-template/main/_wheels/<package>.whl
```

This is a temporary workaround. Once upstream maintainers publish wheels to PyPI, remove the URL workaround and install by package name.

### Setup cell pattern

```python
import sys
if sys.platform == "emscripten":
    import micropip
    _whl = "https://raw.githubusercontent.com/neuromatch/course-template/main/_wheels"
    await micropip.install([
        "ipywidgets",
        f"{_whl}/vibecheck-0.0.5-py3-none-any.whl",
        f"{_whl}/datatops-0.3.1-py3-none-any.whl",
    ])
```

## Converting .ipynb to MyST .md

### Cell mapping

| Notebook cell type | MyST equivalent |
|---|---|
| `"cell_type": "markdown"` | Raw markdown content |
| `"cell_type": "code"` | `` ```{code-cell} python `` |
| Badge cell (position 0) | Omit -- CI injects badges |
| `cellView: "form"` / `# @title` | `:tags: [hide-input]` |
| `# to_remove solution` | `:tags: [hide-input]` |
| `# to_remove explanation` | `:tags: [hide-input]` |
| `raise NotImplementedError` (exercise) | No tags (students must see/edit) |
| `# @markdown` / `@widgets.interact` | `:tags: [hide-input]` |

### Frontmatter

Replace all notebook metadata with clean MyST frontmatter:

```yaml
---
title: "Tutorial N: Title Here"
kernelspec:
  name: python3
  display_name: Python 3
---
```

### Checklist for conversion

1. Strip badge cell (position 0)
2. Add clean frontmatter with `kernelspec`
3. Add Pyodide setup cell if needed (micropip installs)
4. Convert all code cells to `{code-cell}` directives with appropriate tags
5. Normalize LaTeX for KaTeX compatibility
6. Preserve all prose, math, `<details>` blocks, HTML as-is
7. Add day directory, `chapter_intro.md`, `further_reading.md`
8. Register in `myst.yml` TOC
9. Test: `myst build --html` -- check for `⛔` errors
