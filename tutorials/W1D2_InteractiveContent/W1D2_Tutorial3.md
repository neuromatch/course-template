---
title: "Tutorial 3: When to Use .ipynb vs .md"
---

# Tutorial 3: When to Use `.ipynb` vs `.md`

## The default: write in MyST `.md`

For most Neuromatch tutorials, write in MyST `.md`. CI converts these to `.ipynb`
automatically for Colab and Kaggle. Benefits:

- **Clean git history** — no output noise, no metadata churn in diffs
- **Readable in any editor** — no need for Jupyter UI to review changes
- **Easy code review** — collaborators see plain text, not JSON
- **Re-executed at build time** — ensures reproducibility

## When to author directly in `.ipynb`

Use `.ipynb` directly when:

- **Compute-heavy tutorials** — the notebook requires a GPU or takes >5 minutes
  to run. Pre-execute it, commit the outputs, and MyST renders the stored outputs
  without re-running them.
- **Complex interactive widget state** — widgets whose state must be preserved
  across sessions.
- **External contributions** — a collaborator submits a `.ipynb` directly.
  Accept it and place it in `tutorials/<day>/` — the badge injection script
  handles it automatically alongside the `.md`-converted notebooks.

## How CI handles both sources

The `scripts/convert_to_notebooks.py` script (covered in Day 3) handles both:

1. **From `.md`** — converts with `jupytext`, then injects Colab/Kaggle badges
2. **From `.ipynb`** authored directly — injects badges only, copies to `notebooks/`

In both cases the source file in `tutorials/` is never modified.

## Practical rule

> If in doubt, write `.md`. Use `.ipynb` only when you need stored outputs
> from expensive computation or complex widget state.

## Placing `.ipynb` files in the TOC

If you author a `.ipynb` directly, place it in `tutorials/<day>/` and add it to
`myst.yml` just like a `.md` file:

```yaml
- file: tutorials/W2D1_MyTopic/W2D1_Tutorial1.ipynb
```

MyST handles both formats identically in the TOC.
