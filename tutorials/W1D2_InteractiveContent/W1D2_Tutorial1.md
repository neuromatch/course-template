---
title: "Tutorial 1: In-Browser Execution with JupyterLite"
kernelspec:
  name: python3
  display_name: Python 3
---
<a href="https://colab.research.google.com/github/neuromatch/course-template/blob/main/notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a> <a href="https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/neuromatch/course-template/main/notebooks/W1D2_InteractiveContent/W1D2_Tutorial1.ipynb" target="_blank"><img src="https://kaggle.com/static/images/open-in-kaggle.svg" alt="Open In Kaggle"/></a>




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
JupyterLite supports most pure-Python packages. Packages with compiled C extensions
(like `scipy` or `torch`) may load slowly or not be available.
For compute-heavy days, point students to Colab or Kaggle instead —
badges are injected automatically by CI. See Day 3, Tutorial 2.
```

## For students: running in Colab or Kaggle

Every tutorial page with executable code also has **Colab** and **Kaggle** badges
at the top of its generated notebook. These are injected automatically by CI —
you do not add them manually. See Day 3, Tutorial 2 for how this works.
