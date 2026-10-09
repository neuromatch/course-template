# Markdown-Only Content, No Binder

## Goal

All course content is authored as MyST `.md`. Notebooks are still generated for
Colab/Kaggle, but they are never the source. Binder and remote-kernel
instructions are removed because the template doesn't support them.

## Changes

1. **W1D2_Tutorial3**: rewritten as "Markdown Is the Only Source". It covers the
   flow from `.md` to generated notebooks on `notebooks-branch` to badges, why
   `.ipynb` files are never committed, and how to bring in an existing notebook
   (run jupytext once, then delete the `.ipynb`).
2. **W1D2_Bonus**: rewritten as "Working Within JupyterLite's Limits". It covers
   bundled packages vs micropip, CORS-friendly wheel hosting, and what can't run
   in the browser, with Colab/Kaggle as the fallback.
3. **Remove Binder** from W1D3_Tutorial3, the Day 2 further_reading page, and the
   Day 2 chapter_intro.
4. **Enforcement in `convert_to_notebooks.py`**: CI fails if any `.ipynb` file is
   in `tutorials/`, or if a `.md` file has `{code-cell}` but no `kernelspec`. All
   violations are reported, not just the first. The code path that copied
   hand-written notebooks is removed.
5. **Fix misleading claims**: Pyodide bundles scipy; badges appear on pages too;
   notebooks go to `notebooks-branch`, not `main`. AGENTS.md is updated to match.

## Out of scope

Running notebooks at build time to check that they work (tracked separately).

## Verification

- The script passes on the current tree.
- The script fails when a stray `.ipynb` is added, and when `kernelspec` is
  removed from a page that has code cells.
- `myst build --html` produces no new errors.
