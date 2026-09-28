# Design: Convert NMA Tutorial to MyST Example Day

**Date:** 2026-09-27
**Status:** Approved

## Goal

Convert the NMA W2D3_Tutorial1 (Linear Dynamical Systems) from its original `.ipynb` format into a MyST `.md` file and add it to the course-template as a new example day. This gives template users a reference showing what real, production NMA content looks like in the new format.

## File Structure

```
tutorials/
  W2D1_Examples/
    chapter_intro.md          # Day overview: what this example day is, learning objectives
    W2D1_Tutorial1.md         # Converted Linear Dynamical Systems tutorial
    further_reading.md        # Links to original NMA course, prerequisites, references
```

TOC entry in `myst.yml` (inserted after Day 3, before projects):

```yaml
- title: "Day 4: Real Content Example"
  children:
    - file: tutorials/W2D1_Examples/chapter_intro.md
      children:
        - file: tutorials/W2D1_Examples/W2D1_Tutorial1.md
        - file: tutorials/W2D1_Examples/further_reading.md
```

## Content Conversion Mapping

### Frontmatter

Old notebook metadata (colab-specific fields, `colab_type`, `id`, etc.) is replaced with clean MyST frontmatter:

```yaml
---
title: "Tutorial 1: Linear Dynamical Systems"
kernelspec:
  name: python3
  display_name: Python 3
---
```

### Badges

Omitted from the `.md` source. The existing `convert_to_notebooks.py` script injects Colab/Kaggle badges automatically during CI.

### Header/Attribution Block

The original title, "Week 2, Day 3: Linear Systems", author credits, reviewer credits, and production editor credits are preserved as a markdown section immediately after the frontmatter.

### Prose / Math

All markdown content (explanations, LaTeX equations, section headers) is kept as-is. MyST supports:
- Inline math: `$x_0$`
- Display math: `$$...$$` and `\begin{equation}...\end{equation}`
- HTML `<details><summary>` blocks (rendered natively)
- Horizontal rules via `---`

### Code Cells

Each notebook code cell maps to a `{code-cell}` directive:

```markdown
```{code-cell} python
import numpy as np
```
```

### Hidden Infrastructure Cells (`cellView: "form"`, `@title`)

Video player cells, figure settings, plotting functions, and feedback widgets use `:tags: [hide-input]` to preserve the code while hiding it from view by default:

```markdown
```{code-cell} python
:tags: [hide-input]
# @title Video 1: Linear Dynamical Systems
...
```
```

### Solution Cells (`# to_remove solution`)

Converted to `{code-cell}` blocks with `:tags: [hide-input]` so students can reveal answers:

```markdown
```{code-cell} python
:tags: [hide-input]
# Solution
def integrate_exponential(a, x0, dt, T):
  ...
```
```

### Explanation Cells (`# to_remove explanation`)

Same treatment as solutions -- `:tags: [hide-input]` code cells containing the explanation docstrings.

### Interactive Widgets (`@widgets.interact`)

Preserved as regular `{code-cell}` blocks. A hidden setup cell at the top handles Pyodide compatibility (see below).

### Feedback/Vibecheck Cells

Preserved as `{code-cell}` blocks with `:tags: [hide-input]`. The `!pip3 install vibecheck datatops` shell command is kept as-is.

## Pyodide/JupyterLite Compatibility

### Dependencies

| Package | Pyodide Status |
|---------|---------------|
| numpy | Bundled |
| matplotlib | Bundled |
| scipy | Bundled |
| ipywidgets | Needs micropip |
| logging | Stdlib |
| vibecheck/datatops | Not available (NMA infra, non-essential) |

### Setup Cell

A hidden cell at the very top installs ipywidgets when running in Pyodide:

```markdown
```{code-cell} python
:tags: [remove-cell]
import sys
if sys.platform == "emscripten":
    import micropip
    await micropip.install(["ipywidgets"])
```
```

This follows the pattern already documented in W1D2_Tutorial1.

## Supporting Files

### `chapter_intro.md`

- Explains this day contains a real NMA tutorial converted to MyST
- States learning objectives (from original tutorial objectives)
- One-row schedule table

### `further_reading.md`

Links to:
- Original NMA Computational Neuroscience course
- W0D4 Calculus prerequisite tutorials (referenced in content)
- 3Blue1Brown linear algebra series (referenced in content)

### `myst.yml`

Add the new TOC section after Day 3 and before projects.

## What Is NOT Changed

- No modifications to existing Days 1-3
- No changes to `convert_to_notebooks.py` (it already handles MyST `.md` -> `.ipynb`)
- No changes to CI workflows
- No changes to `requirements.txt` (all deps already listed)
