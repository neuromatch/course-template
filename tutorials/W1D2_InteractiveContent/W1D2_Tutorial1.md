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
result = sum(range(1, 101))
print(f"Sum of 1 to 100: {result}")
```

## Try it: NumPy in the browser

```{code-cell} python
import numpy as np

rng = np.random.default_rng(seed=42)
arr = rng.standard_normal(1000)
print(f"Mean: {arr.mean():.4f}")
print(f"Std:  {arr.std():.4f}")
```

## Try it: matplotlib in the browser

```{code-cell} python
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(seed=0)

fig, axes = plt.subplots(1, 2, figsize=(8, 3))

x = np.linspace(-3, 3, 300)
axes[0].plot(x, np.tanh(x))
axes[0].set_title("tanh(x)")
axes[0].set_xlabel("x")

axes[1].hist(rng.standard_normal(500), bins=30)
axes[1].set_title("Random normal samples")

plt.tight_layout()
```

## How JupyterLite is configured

In `myst.yml`, the setting `project.jupyter.lite: true` enables the in-browser
kernel for all pages that have a `kernelspec` in their frontmatter:

```yaml
project:
  jupyter:
    lite: true
```

Pages without `kernelspec` (like `further_reading.md`) show no power button —
the JupyterLite kernel is only activated for pages that declare a `kernelspec`.

```{note}
JupyterLite runs Python via Pyodide (WebAssembly). Core scientific packages
(`numpy`, `scipy`, `pandas`, `matplotlib`, `altair`) are bundled and work out of
the box. Others, like `ipywidgets`, are installed at runtime with `micropip`.
Some packages, like GPU-backed `torch`, can't run in the browser at all.
The Day 2 Bonus covers these limits and how to work around them.
```

## For students: running in Colab or Kaggle

Every tutorial page with executable code has **Colab** and **Kaggle** badges at
the top of the page and of its generated notebook. CI adds them automatically,
so you never add them by hand. See Day 3, Tutorial 2 for how this works.
