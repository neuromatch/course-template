from convert_to_notebooks import add_badge_cell, prepare_site_md
from nma_solutions import FALLBACK_SENTINEL

PAGE = """---
title: T
kernelspec:
  name: python3
  display_name: Python 3
---

# Title

```{code-cell} python
def f(x):
  raise NotImplementedError("Student exercise")
```

::::{nma-solution}
```python
def f(x):
  return 2 * x
```
::::
"""


def prepare(path, times=1):
    for _ in range(times):
        prepare_site_md(path, "notebooks/D/T.ipynb", "org/repo", dry_run=False)
    return path.read_text()


def test_prepare_site_adds_badges_and_fallback(tmp_path):
    page = tmp_path / "T.md"
    page.write_text(PAGE)
    text = prepare(page)
    body = text.split("---\n", 2)[2]
    assert body.startswith("<a href=\"https://colab.research.google.com/github/org/repo/")
    assert text.count(FALLBACK_SENTINEL) == 1
    assert body.index("colab") < body.index(FALLBACK_SENTINEL) < body.index("# Title")
    assert "return 2 * x" in text.split("# Title")[0]  # solution is in the setup cell


def test_prepare_site_is_idempotent(tmp_path):
    page = tmp_path / "T.md"
    page.write_text(PAGE)
    once = prepare(page)
    assert prepare(page, times=2) == once


def test_prepare_site_without_exercises_adds_only_badges(tmp_path):
    page = tmp_path / "T.md"
    page.write_text(PAGE.split("```{code-cell}")[0])
    text = prepare(page, times=2)
    assert FALLBACK_SENTINEL not in text
    assert text.count("colab-badge.svg") == 1


def test_add_badge_cell_is_idempotent():
    nb = {"cells": [{"cell_type": "markdown", "id": "a", "metadata": {}, "source": ["# T"]}]}
    once = add_badge_cell(nb, "notebooks/D/T.ipynb", "org/repo")
    twice = add_badge_cell(once, "notebooks/D/T.ipynb", "org/repo")
    assert twice == once
    assert len(once["cells"]) == 2 and once["cells"][0]["id"] == "badges"
    assert len(nb["cells"]) == 1
