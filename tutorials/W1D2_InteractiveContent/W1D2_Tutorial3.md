---
title: "Tutorial 3: Markdown Is the Only Source"
---

# Tutorial 3: Markdown Is the Only Source

All course content in this template is written in MyST Markdown (`.md`).
Jupyter notebooks are still produced for Colab and Kaggle, but CI generates them.
They are never written or edited by hand, and never committed to `main`.

## How content flows

```
tutorials/W1D2_.../W1D2_Tutorial1.md     <- you edit this
        │
        ├── myst build ──────────────►  the website (with Colab/Kaggle badges)
        │
        └── jupytext (CI) ───────────►  notebooks-branch:
                                          notebooks/W1D2_.../W1D2_Tutorial1.ipynb
                                          (opened by the Colab/Kaggle badges)
```

Every page that has a `kernelspec` in its frontmatter goes down both paths. See
Day 3, Tutorial 2 for the details of notebook generation and badges.

## Why not commit `.ipynb` files?

- **Clean git history**: no output blobs or metadata churn in diffs
- **Easy review**: collaborators read plain text, not JSON
- **One source of truth**: the website and the notebooks can't drift apart,
  because both come from the same `.md` file

## Rules enforced by CI

`scripts/convert_to_notebooks.py` runs in CI and fails the build if either rule
is broken:

1. **No `.ipynb` files in `tutorials/`.** Content must be `.md`.
2. **Pages with code need a `kernelspec`.** If a page contains a
   `` ```{code-cell} `` block, its frontmatter must declare:

   ```yaml
   kernelspec:
     name: python3
     display_name: Python 3
   ```

   Without it the page would get no notebook, no badges, and no JupyterLite power
   button. Pages without code cells (intros, further reading) stay static.

## Bringing in an existing notebook

If you receive a `.ipynb`, from an older course or a collaborator, convert it once
and delete the original:

```bash
uv run jupytext --to md:myst path/to/Notebook.ipynb -o tutorials/W2D1_MyTopic/W2D1_Tutorial1.md
```

Then tidy up the result: clean frontmatter, cell tags such as `hide-input` for
solutions, and KaTeX-compatible math. The full checklist is in `AGENTS.md` under
"Converting .ipynb to MyST .md". Commit only the `.md`.
