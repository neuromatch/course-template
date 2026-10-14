---
title: "Tutorial 5: Exercises and Solutions"
kernelspec:
  name: python3
  display_name: Python 3
---
<a href="https://colab.research.google.com/github/neuromatch/course-template/blob/notebooks-branch/notebooks/W1D2_InteractiveContent/W1D2_Tutorial5.ipynb" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a> <a href="https://kaggle.com/kernels/welcome?src=https://raw.githubusercontent.com/neuromatch/course-template/notebooks-branch/notebooks/W1D2_InteractiveContent/W1D2_Tutorial5.ipynb" target="_blank"><img src="https://kaggle.com/static/images/open-in-kaggle.svg" alt="Open In Kaggle"/></a>

```{code-cell} python
:tags: [remove-cell]
# nma-exercise-fallback (generated, do not edit)
# Runs the reference solution when an unfinished exercise is executed,
# so "Run all" doesn't stop at the first exercise.
def _nma_install_fallback(exercises):
    import difflib
    import re
    from IPython import get_ipython

    shell = get_ipython()
    if shell is None:
        return
    unfinished = re.compile(r"^[ \t]*raise NotImplementedError", re.MULTILINE)

    def nma_exercise_fallback(lines):
        source = "".join(lines)
        if not unfinished.search(source) or "nma-exercise-fallback" in source:
            return lines
        best, best_score = None, 0.6
        for exercise, solution in exercises:
            if source.strip() == exercise.strip():
                best = solution
                break
            score = difflib.SequenceMatcher(None, source, exercise).ratio()
            if score >= best_score:
                best, best_score = solution, score
        if best is None:
            return lines
        return ["print('Exercise not completed yet, so the reference solution was run.')\n"] + (best + "\n").splitlines(keepends=True)

    transformers = shell.input_transformers_post
    transformers[:] = [t for t in transformers
                       if getattr(t, "__name__", "") != "nma_exercise_fallback"]
    transformers.append(nma_exercise_fallback)


_nma_install_fallback([
    ('def double(x):\n  ###################################################################\n  ## Fill out the following then remove\n  raise NotImplementedError("Student exercise: double x")\n  ###################################################################\n  return ...\n\nprint(double(21))', 'def double(x):\n  return 2 * x\n\nprint(double(21))'),
])
del _nma_install_fallback
```

# Tutorial 5: Exercises and Solutions

Exercises are ordinary code cells that `raise NotImplementedError` until the
student fills them in. Their answers go in two MyST directives:

- `{nma-solution}` for the code that solves an exercise
- `{nma-explanation}` for the answer to a discussion question or interactive demo

You write each answer once, and the build produces three versions of the page.

| Where | What readers see |
|---|---|
| Website | A *Click for solution* / *Click for explanation* link. The answer is not shown on the page. |
| Student notebook (Colab/Kaggle) | The same link, in its own markdown cell. The `.ipynb` holds no answers. |
| Instructor notebook | The solution as a code cell (starting `# Solution`) and the explanation as markdown. |

The links point to files that CI writes next to the notebooks on
`notebooks-branch`:

```text
notebooks/<Day>/<Tutorial>.ipynb               student notebook
notebooks/<Day>/instructor/<Tutorial>.ipynb    instructor notebook
notebooks/<Day>/solutions/<Tutorial>_Solution_<n>.py
notebooks/<Day>/solutions/<Tutorial>_Explanation_<n>.md
```

`n` counts each directive type separately, from the top of the page.

## Solutions

Put the exercise in a normal `{code-cell}` with no tags, so students can see and
edit it. Put the `{nma-solution}` directly after it, with only blank lines in
between. Its body is a single ```` ```python ```` fence:

`````markdown
```{code-cell} python
def double(x):
  ###################################################################
  ## Fill out the following then remove
  raise NotImplementedError("Student exercise: double x")
  ###################################################################
  return ...

print(double(21))
```

::::{nma-solution}
```python
def double(x):
  return 2 * x

print(double(21))
```
::::
`````

The outer fence needs more colons (`::::`) than any fence inside it. That
example renders as:

```{code-cell} python
def double(x):
  ###################################################################
  ## Fill out the following then remove
  raise NotImplementedError("Student exercise: double x")
  ###################################################################
  return ...

print(double(21))
```

::::{nma-solution}
```python
def double(x):
  return 2 * x

print(double(21))
```
::::

## Explanations

An `{nma-explanation}` stands on its own and takes ordinary Markdown, including
math:

````markdown
:::{nma-explanation}
Doubling is linear: $f(a + b) = f(a) + f(b)$.
:::
````

renders as:

:::{nma-explanation}
Doubling is linear: $f(a + b) = f(a) + f(b)$.
:::

## "Run all" on the website

Normally "Run all" would stop at the first unfinished exercise, so nothing
below it would run. To prevent that, the published site adds a hidden setup cell
to every page that has exercises. When a cell still has an uncommented
`raise NotImplementedError` line, the setup cell runs the matching reference
solution instead and prints a note saying so. Once the student deletes or
comments out that line, their own code runs.

Try it: start the kernel on this page and run the exercise above without
changing it.

Notes:

- The setup cell is added at build time (`convert_to_notebooks.py
  --prepare-site` in `publish-book.yml`), so local `myst start` previews don't
  have it.
- The solutions are hidden, not secret. The setup cell and the page source
  are both downloadable from the site.
- Colab/Kaggle notebooks don't get the fallback. There the exercise raises,
  as in NMA notebooks.

## Rules checked by CI

`convert_to_notebooks.py` stops with an error, giving the file and line, if:

- a code cell still has a `# to_remove solution` / `# to_remove explanation`
  marker (the old convention)
- an exercise has no `{nma-solution}` directly after it, or a solution isn't
  directly after an exercise
- a solution body isn't a single ```` ```python ```` fence, or an explanation
  is empty
- either directive is nested inside another directive, has options, or is
  never closed
