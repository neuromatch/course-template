# Exercise Solutions and Explanations

## Goal

Authors write exercise solutions and discussion explanations as MyST
directives instead of `# to_remove solution` / `# to_remove explanation` code
cells. One source produces:

- **Site**: a "Click for solution/explanation" link. The solution text is not
  shown. "Run all" in JupyterLite still completes, because a hidden fallback
  runs the reference solution for unfinished exercises.
- **Student notebook** (Colab/Kaggle): link cells, with no solution code in the file.
- **Instructor notebook**: the exercise cell followed by the solution as a real
  code cell, and explanations as markdown cells.
- **Solution files** on `notebooks-branch`, which are the targets of the links.

## Problems with the current approach

- In `W2D1_Tutorial1.md`, solutions and explanations are `hide-input` code
  cells marked by a first-line comment. A typo in the marker leaks the solution,
  and explanations are docstrings, so they have no Markdown or math.
- Exercises `raise NotImplementedError`. MyST's book theme runs "Run all" with
  `executeAll(stopOnError = true)` (thebe-core), so execution stops at the first
  exercise and later demos never run.

## Decisions

- Use custom directives (same family as `{nma-video}`), not cell tags or comment markers.
- The exercise stays a normal top-level `{code-cell}`. Nesting it inside the
  directive would break MyST/JupyterLite executable cells and jupytext.
  The solution is paired with the code cell directly before it.
- The site shows a link only. Solution files are hosted on GitHub
  `notebooks-branch` under `solutions/`.
- No example output images for now.
- The run-all fallback is site-only. Colab notebooks keep the NMA behaviour
  (the exercise raises).

## Authoring syntax

`````markdown
```{code-cell} python
def integrate_exponential(a, x0, dt, T):
  ...
  raise NotImplementedError("Student exercise: need to implement simulation")
```

::::{nma-solution}
```python
def integrate_exponential(a, x0, dt, T):
  ...
```
::::

:::{nma-explanation}
1. For $a<0$ the solution decays in time ...
:::
`````

- `nma-solution`: the body is exactly one `python` fence. It must directly
  follow a `{code-cell}` containing `raise NotImplementedError`.
- `nma-explanation`: Markdown body. It stands alone.
- Both must be at the top level of the page.
- Naming: `<Tutorial>_Solution_<n>.py` and `<Tutorial>_Explanation_<n>.md`,
  where `n` is the 1-based position among that directive kind on the page.
  The same rule is implemented in JS and Python, with "keep in sync" comments.

### Validation (`validate_content`, both script modes)

Each of these is an error, reported with the file and line:

- a `# to_remove` marker left in a code cell
- an `nma-solution` that is not directly after an exercise code cell
- an exercise code cell (`raise NotImplementedError`) with no `nma-solution` after it
- an empty body, or an `nma-solution` body that is not a single python fence
- an unclosed directive, or unknown options
- a directive nested inside another directive (the JS side also reports this as a fatal error)

## Site rendering: `plugins/nma.mjs`

- Each directive renders as one paragraph: an italic link "Click for
  solution" / "Click for explanation" pointing to
  `https://github.com/<org/repo>/blob/notebooks-branch/notebooks/<Day>/solutions/<file>`.
- `<org/repo>` comes from `project.github` in `myst.yml`, which the plugin reads at build time.
- A plugin transform numbers the nodes per page in document order. The day
  folder and tutorial name come from the page path.

## Site run-all fallback

The `--inject-md-badges` step in `convert_to_notebooks.py` (renamed to
`--prepare-site`, with the old flag kept as an alias) runs only on CI's
throwaway checkout. For each page with exercises, it also injects one hidden
setup `{code-cell}` after the badges. That cell:

- defines `_NMA_EXERCISES = [(exercise_source, solution_source), ...]`
- registers an IPython `input_transformers_post` hook. If the incoming cell
  still contains `raise NotImplementedError(`, the hook matches it to an
  exercise and replaces the source with the solution, plus a printed note:
  "Exercise not completed yet, so the reference solution was run."
  - Matching tries an exact match on the original exercise source first,
    then the best `difflib.SequenceMatcher` ratio of at least 0.6.
    With no match, the cell runs unchanged.

Caveats: the solution source is in the page data, so it is hidden but not secret.
Local `myst start` has no fallback, the same as badges.

**Spike before implementing:**
1. Is a `remove-cell` tagged cell still executed by JupyterLite/thebe? If not,
   use `hide-cell`.
2. Does pyodide-kernel honour `input_transformers_post`?

## Notebook generation: `scripts/nma_solutions.py`

This runs in `convert_to_notebooks.py` after jupytext and the media expansion.

| Output | Path | `nma-solution` | `nma-explanation` |
|---|---|---|---|
| Student nb | `notebooks/<Day>/<T>.ipynb` | markdown link cell | markdown link cell |
| Instructor nb | `notebooks/<Day>/instructor/<T>.ipynb` | code cell, `# Solution` first line | markdown cell with the text |
| Files | `notebooks/<Day>/solutions/` | `<T>_Solution_<n>.py` | `<T>_Explanation_<n>.md` |

- Both notebooks get the badge cell, each pointing to its own path.
- Directive splitting reuses the markdown-cell split approach from `nma_media.py`.
- `generate-notebooks.yml` is unchanged, because `rsync --delete notebooks/` carries the new folders.

## Migration

`W2D1_Tutorial1.md` has 2 solution cells and 5 explanation cells. Convert them
to directives by hand, and turn the explanation docstrings into Markdown.

## Documentation

- `AGENTS.md`:
  - architecture: add `nma_solutions.py`
  - Key Conventions: add a section on the directives, and update the cell-tag notes
  - conversion mapping and checklist: `# to_remove` maps to the directives
  - CI: describe the fallback and the renamed flag
- New page `tutorials/W1D2_InteractiveContent/W1D2_Tutorial5.md` "Exercises
  and Solutions", added to the TOC. It covers the syntax (inside a markdown
  fence), a live example, what each audience sees, and the fallback.

## Testing

- `tests/test_nma_solutions.py`:
  - parsing and pairing
  - each validation error
  - student and instructor cell output
  - file naming
  - transformer matching (exact, fuzzy, no match, finished exercise)
  - setup-cell injection is idempotent
- End-to-end:
  - the converter writes 2 `.py` and 5 `.md` files for W2D1
  - the student notebook contains no solution code
  - the instructor notebook contains it
  - `myst build --html`: no `⛔`, the links are present, and no solution code is in the HTML body
  - manual "Run all" of W2D1 in JupyterLite completes

## Out of scope

- Example output images and executing notebooks in CI.
- A bulk `# to_remove` migration script.
- The fallback in Colab/Kaggle notebooks.
