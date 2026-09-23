---
title: "Tutorial 2: Rich Interactive Outputs"
kernelspec:
  name: python3
  display_name: Python 3
---
<a href="https://colab.research.google.com/github/neuromatch/course-template/blob/main/notebooks/W1D2_InteractiveContent/W1D2_Tutorial2.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a> <a href="https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/neuromatch/course-template/main/notebooks/W1D2_InteractiveContent/W1D2_Tutorial2.ipynb" target="_blank"><img src="https://kaggle.com/static/images/open-in-kaggle.svg" alt="Open In Kaggle"/></a>






# Tutorial 2: Rich Interactive Outputs

MyST renders interactive outputs from Altair, Plotly, and ipywidgets natively.
These work both in the static build (pre-rendered from stored outputs) and live
via JupyterLite when the power button is activated.

## Interactive Altair chart

Altair charts are fully interactive in the rendered book — no kernel required.
Drag to select points in the scatter plot; the bar chart updates in real time.

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

With the JupyterLite kernel active, this slider is live and interactive.

JupyterLite uses Pyodide (Python in WebAssembly), which requires packages to be
loaded via `micropip` before importing. The setup cell below handles this — it is
hidden from students but runs automatically when the kernel starts.

```{code-cell} python
:tags: [remove-cell]
# JupyterLite/Pyodide setup — installs packages not bundled in the default WASM environment
import sys
if sys.platform == "emscripten":
    import micropip
    await micropip.install(["ipywidgets"])
```

```{code-cell} python
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

def plot_wave(frequency=1.0):
    x = np.linspace(0, 2 * np.pi, 300)
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(x, np.sin(frequency * x))
    ax.set_title(f"sin({frequency:.1f} x)")
    ax.set_xlabel("x")
    plt.tight_layout()
    plt.show()

widgets.interact(plot_wave, frequency=(0.5, 5.0, 0.5))
```

## Pandas DataFrame output

DataFrames render as styled HTML tables in the book:

```{code-cell} python
import pandas as pd
from vega_datasets import data

df = data.cars().iloc[:5, :5]
df
```

## Labelling outputs for reuse

Label a cell to embed its output on another page:

```{code-cell} python
#| label: fig-horsepower-scatter
import matplotlib.pyplot as plt
from vega_datasets import data

df = data.cars()
fig, ax = plt.subplots(figsize=(5, 3))
scatter = ax.scatter(
    df["Horsepower"], df["Miles_per_Gallon"],
    alpha=0.4, c=df["Year"], cmap="viridis"
)
ax.set_xlabel("Horsepower")
ax.set_ylabel("Miles per gallon")
plt.colorbar(scatter, ax=ax, label="Model year")
plt.tight_layout()
```

On any other page in the book, embed this output with:

    {embed}`fig-horsepower-scatter`

## Summary

- Altair charts are interactive in the static build — no kernel needed
- ipywidgets require the JupyterLite kernel to be active
- Label outputs with `#| label: fig-name` to reuse them across pages
