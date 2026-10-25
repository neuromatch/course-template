---
title: "Tutorial 4: Page Types and Frontmatter"
---

# Tutorial 4: Page Types and Frontmatter

Every page in this book starts with a block of YAML between two `---` lines, called the **frontmatter**. A few keys in it decide what kind of page you get: static or executable, editable in the browser or Colab-only, ordinary or scrollytelling. This page is the reference for all of them.

## The short version

| I want… | Frontmatter | Notebook generated? | Code on the page |
|---|---|---|---|
| A text page (intro, further reading) | `title` only | no | none, or static |
| A normal tutorial | `title` + `kernelspec` | yes | editable, runs in the browser |
| A tutorial that is too heavy for the browser | `title` + `kernelspec` + `runtime: colab` | yes | read-only, with a banner linking to Colab and Kaggle |
| A scrollytelling tutorial | `title` + `kernelspec` + `layout: scrolly` (+ `site.hide_outline`) | yes | live panels pinned beside the text |

## Keys

### `title` (always)

The page title in the sidebar, the browser tab and the notebook.

```yaml
---
title: "Tutorial 1: Linear Dynamical Systems"
---
```

### `kernelspec` (makes a page executable)

Declare it on every page that has a `{code-cell}`. CI rejects a page with code and no `kernelspec`.

```yaml
kernelspec:
  name: python3
  display_name: Python 3
```

A page **with** `kernelspec`:

- gets editable, runnable code cells on the site,
- is converted to student and instructor notebooks on `notebooks-branch`,
- gets Colab and Kaggle badges at build time (never write them yourself).

A page **without** it is static: nothing is run, converted or badged.

### `runtime` (`browser` or `colab`)

Where the page's code runs. The default is `browser`, so you normally leave the key out.

```yaml
runtime: colab
```

- `browser` — each cell is an editor with a **▶ Run** button, running Python in the reader's browser (Pyodide). Good for numpy, scipy, matplotlib, pandas and small demos.
- `colab` — the code is shown read-only and a banner, *Do this tutorial in Colab*, links to the generated notebook on Colab and Kaggle. Use it for PyTorch, GPUs, big datasets or long training runs.

Any other value is an error, and `runtime: colab` can't be combined with `layout: scrolly`. MyST prints `extra key ignored: runtime`, which is expected: the key is read by the course kit, not by MyST. See [Tutorial 3 of Week 2 Day 1](../W2D1_Examples/W2D1_Tutorial3.md) for a Colab page.

### `layout: scrolly` and `site` (scrollytelling)

Turns the page into a story of **steps**: a card of text on one side, a pinned stage with figures and live code on the other.

```yaml
layout: scrolly
site:
  hide_outline: true
```

`hide_outline` gives the story the width of the "On this page" column. Don't use `hide_toc`, because readers could no longer leave the page. The `{step}` and `{stage}` markers are covered in [Day 2, Tutorial 6](../W1D2_InteractiveContent/W1D2_Tutorial6.md). MyST warns `extra key ignored: layout`, which is expected.

### `feedback_prefix` (keep ids of an existing notebook)

The section id sent by a `{nma-feedback}` widget is `<prefix>_<name>`. The prefix is derived from the file name (`W2D1_Tutorial1` becomes `W2D1_T1`). Set it only when converting a notebook whose ids must not change:

```yaml
feedback_prefix: W2D2_T1
```

See [Day 2, Tutorial 4](../W1D2_InteractiveContent/W1D2_Tutorial4.md). MyST warns `extra key ignored: feedback_prefix`, which is expected.

## A complete example

```yaml
---
title: "Tutorial 3: Training a CNN"
runtime: colab
feedback_prefix: W3D2_T3
kernelspec:
  name: python3
  display_name: Python 3
---
```

## Warnings you can ignore

MyST only knows its own keys, so it logs `extra key ignored: <key>` for `runtime`, `layout` and `feedback_prefix`. Nothing is wrong. The same goes for the `nma:` block in `myst.yml`.

## What CI checks

`nma-kit check` (from the course kit, run by CI) validates frontmatter and fails with the file name and line:

- `runtime` is `browser` or `colab`.
- `runtime: colab` and `layout: scrolly` are not combined.
- A page with a `{code-cell}` has `kernelspec`.
- A `layout: scrolly` page has at least one `{step}`.

## Related, but not frontmatter

Per-cell options go on the code cell, not in the frontmatter. For example `:tags: [hide-input]` collapses the code, `remove-input` shows only the output and `remove-cell` hides the cell entirely. A cell with an unfinished `raise NotImplementedError` is an exercise and must be followed by an `{nma-solution}`. See [Day 2, Tutorial 1](../W1D2_InteractiveContent/W1D2_Tutorial1.md) and [Tutorial 3](../W1D2_InteractiveContent/W1D2_Tutorial3.md).
