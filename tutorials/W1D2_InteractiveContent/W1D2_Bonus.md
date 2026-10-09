---
title: "Bonus: Working Within JupyterLite's Limits"
---

# Bonus: Working Within JupyterLite's Limits

JupyterLite runs Python in the browser through Pyodide (WebAssembly). It needs no
server, but not every package or workload can run there. This page covers how to
get dependencies into the browser and what to do when something can't run there.

## Packages bundled with Pyodide

These import directly, with no install step:

- `numpy`, `scipy`, `pandas`, `matplotlib`, `altair`

Many other packages with compiled code are also pre-built for Pyodide. See the
[Pyodide package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).

## Installing other packages with micropip

Pure-Python packages can be installed at runtime with `micropip`. Put the install
in a setup cell at the top of the tutorial and tag it `remove-cell` so students
don't see it:

````markdown
```{code-cell} python
:tags: [remove-cell]
import sys
if sys.platform == "emscripten":  # only true in JupyterLite/Pyodide
    import micropip
    await micropip.install(["ipywidgets"])
```
````

The `sys.platform` check makes the cell do nothing in Colab, Kaggle, or a local
Jupyter session, where packages come from `requirements.txt` instead.

## Packages without a wheel on PyPI

micropip can only install wheels (`.whl`). If a package only publishes a source
distribution:

1. Build a pure-Python wheel with the `build-pyodide-wheels.yml` workflow (manual
   trigger) and commit it to `_wheels/`.
2. Install it from `raw.githubusercontent.com`, which sends the CORS headers the
   browser needs. GitHub Release URLs do **not**, so they fail in the browser.

```python
_whl = "https://raw.githubusercontent.com/<org>/<repo>/main/_wheels"
await micropip.install([f"{_whl}/vibecheck-0.0.5-py3-none-any.whl"])
```

Remove the workaround once the package publishes wheels upstream.

## What doesn't work in the browser

- **GPUs**: no CUDA, so no GPU-backed PyTorch or JAX
- **Packages with C extensions that aren't pre-built for Pyodide**: they can't be
  installed with micropip
- **Threads and subprocesses**: limited or unavailable
- **Large datasets and long computations**: limited by browser memory, and run
  on a single core

## The fallback: Colab and Kaggle

Every executable tutorial automatically gets **Colab** and **Kaggle** badges that
open the generated notebook (see Day 3, Tutorial 2). When a tutorial needs a GPU,
heavy compute, or an unsupported package, point students to those badges. The
tutorial is still written in `.md` like any other.
