# NMA Tutorial Conversion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the NMA W2D3_Tutorial1 (Linear Dynamical Systems) `.ipynb` into a MyST `.md` file and add it as a new example day (`W2D1_Examples`) in the course-template.

**Architecture:** Create three new `.md` files in `tutorials/W2D1_Examples/` and register them in the `myst.yml` TOC. The tutorial `.md` file is the bulk of the work -- converting every notebook cell into the equivalent MyST `{code-cell}` or markdown block. No scripts, CI workflows, or existing files are modified (except `myst.yml` for the TOC entry).

**Tech Stack:** MyST Markdown, jupytext (for conversion verification)

**Design doc:** `docs/plans/2026-09-27-nma-tutorial-conversion-design.md`

---

### Task 1: Create directory and chapter_intro.md

**Files:**
- Create: `tutorials/W2D1_Examples/chapter_intro.md`

**Step 1: Create the directory and file**

Create `tutorials/W2D1_Examples/chapter_intro.md` with this exact content:

```markdown
---
title: "Day 4: Real Content Example"
---

# Day 4: Real Content Example

This day contains a real Neuromatch Academy tutorial converted from its original
Jupyter notebook format into MyST Markdown. It demonstrates what production
course content looks like in the new template.

The tutorial below was originally **W2D3_Tutorial1: Linear Dynamical Systems**
from the NMA Computational Neuroscience course. All elements -- videos, exercises,
solutions, interactive widgets, and feedback cells -- have been preserved and
reformatted into MyST syntax.

## Learning objectives

By the end of this tutorial you will be able to:

- Simulate the trajectory of a dynamical system using forward Euler integration
- Understand the behavior of one-dimensional linear dynamical systems
- Understand the dynamics of two-dimensional linear systems using eigenvalues
  and eigenvectors
- Interpret stream plots of two-dimensional systems

## Schedule

| Tutorial | Topic | Duration |
|----------|-------|----------|
| Tutorial 1 | Linear dynamical systems | 1 hour |
```

**Step 2: Verify the file exists**

Run: `ls tutorials/W2D1_Examples/`
Expected: `chapter_intro.md`

**Step 3: Commit**

```bash
git add tutorials/W2D1_Examples/chapter_intro.md
git commit -m "feat: add W2D1_Examples chapter intro for NMA tutorial conversion"
```

---

### Task 2: Create further_reading.md

**Files:**
- Create: `tutorials/W2D1_Examples/further_reading.md`

**Step 1: Create the file**

Create `tutorials/W2D1_Examples/further_reading.md` with this exact content:

```markdown
---
title: Further Reading
---

# Further Reading

## Original course material

- [NMA Computational Neuroscience course](https://compneuro.neuromatch.io)
- [Original W2D3 Linear Systems tutorials](https://compneuro.neuromatch.io/tutorials/W2D3_LinearSystems/student/W2D3_Tutorial1.html)

## Prerequisites referenced in this tutorial

- [W0D4 Tutorial 2: Differentiation and Integration](https://compneuro.neuromatch.io/tutorials/W0D4_Calculus/student/W0D4_Tutorial2.html)
- [W0D4 Tutorial 3: Differential Equations](https://compneuro.neuromatch.io/tutorials/W0D4_Calculus/student/W0D4_Tutorial3.html)

## Linear algebra background

- [3Blue1Brown: Eigenvectors and eigenvalues](https://www.youtube.com/watch?v=PFDu9oVAE-g&list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab&index=15)
- [3Blue1Brown: Essence of Linear Algebra (full series)](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab)

## Dynamical systems

- [Steven Strogatz, *Nonlinear Dynamics and Chaos*](https://www.stevenstrogatz.com/books/nonlinear-dynamics-and-chaos-with-applications-to-physics-biology-chemistry-and-engineering)
```

**Step 2: Commit**

```bash
git add tutorials/W2D1_Examples/further_reading.md
git commit -m "feat: add further reading for NMA example day"
```

---

### Task 3: Convert the tutorial notebook to MyST Markdown

**Files:**
- Create: `tutorials/W2D1_Examples/W2D1_Tutorial1.md`

This is the main task. The source is the W2D3_Tutorial1.ipynb content provided in the user's original message. Convert every cell following these rules:

1. **Frontmatter:** Clean MyST YAML with title and kernelspec
2. **First code cell:** Hidden Pyodide setup (`:tags: [remove-cell]`)
3. **Markdown cells:** Verbatim content (math, HTML details blocks, prose)
4. **Regular code cells** (no special metadata): `{code-cell} python` with no tags
5. **Cells with `cellView: "form"` or `# @title`/`# @markdown`:** `{code-cell} python` with `:tags: [hide-input]`
6. **Cells with `# to_remove solution`:** `{code-cell} python` with `:tags: [hide-input]`
7. **Cells with `# to_remove explanation`:** `{code-cell} python` with `:tags: [hide-input]`
8. **Badge cell (position 0):** OMIT entirely (CI injects badges)
9. **Exercise code cells** (contain `raise NotImplementedError`): Regular `{code-cell} python` with no tags (students need to see and edit these)

**Step 1: Create the file**

Create `tutorials/W2D1_Examples/W2D1_Tutorial1.md` with the complete converted content. The file structure is:

```
---
title: "Tutorial 1: Linear Dynamical Systems"
kernelspec:
  name: python3
  display_name: Python 3
---

[remove-cell: Pyodide setup]
[Title heading + attribution block]
[Tutorial Objectives section]
[hide-input: Tutorial slides cell]
[Setup heading]
[hide-input: vibecheck install cell]
[Regular: Imports cell]
[hide-input: Figure settings cell]
[hide-input: Plotting functions cell]
[Section 1 heading]
[hide-input: Video 1 cell]
[hide-input: Feedback cell]
[Video 1 description prose]
[Coding Exercise 1 heading + description]
[Regular: Exercise 1 code cell (has raise NotImplementedError)]
[hide-input: Exercise 1 solution cell]
[hide-input: Feedback cell]
[Interactive Demo 1 heading + description]
[hide-input: Interactive Demo 1 widget cell]
[hide-input: Demo 1 explanation cell]
[hide-input: Feedback cell]
[Section 2 heading]
[hide-input: Video 2 cell]
[hide-input: Feedback cell]
[Oscillatory dynamics prose]
[Interactive Demo 2 heading + description]
[hide-input: Interactive Demo 2 widget cell]
[hide-input: Demo 2 explanation cell]
[hide-input: Feedback cell]
[Section 3 heading]
[hide-input: Video 3 cell]
[hide-input: Feedback cell]
[Multi-dimensional dynamics prose]
[Coding Exercise 3 heading + description]
[Regular: Exercise 3 code cell (has raise NotImplementedError)]
[hide-input: Exercise 3 solution cell]
[hide-input: Feedback cell]
[Interactive Demo 3A heading + description]
[hide-input: Demo 3A widget cell]
[hide-input: Demo 3A explanation cell]
[hide-input: Feedback cell]
[Interactive Demo 3B heading + description]
[hide-input: Demo 3B widget cell]
[hide-input: Demo 3B explanation cell]
[hide-input: Feedback cell]
[Section 4 heading + stream plots prose]
[Think! 4 heading + description]
[hide-input: Stream plots execution cell]
[hide-input: Think 4 explanation cell]
[hide-input: Feedback cell]
[Summary section]
```

The full file content must be produced by converting every cell from the original notebook. Every line of code and every line of prose must be preserved. The only structural changes are:

- Notebook JSON -> MyST markdown syntax
- `"cell_type": "code"` -> `` ```{code-cell} python `` / `` ``` ``
- `"cell_type": "markdown"` -> raw markdown content
- Cell metadata `cellView: "form"` -> `:tags: [hide-input]`
- `# to_remove solution` / `# to_remove explanation` comments -> `:tags: [hide-input]`
- Badge cell at position 0 -> omitted
- Source arrays `["line1\n", "line2\n"]` -> joined into plain text

**Step 2: Verify the file has a kernelspec and can be parsed**

Run: `head -10 tutorials/W2D1_Examples/W2D1_Tutorial1.md`
Expected: YAML frontmatter with `kernelspec` key

Run: `grep -c 'code-cell' tutorials/W2D1_Examples/W2D1_Tutorial1.md`
Expected: A count matching the number of code cells in the original notebook (approximately 25-30)

**Step 3: Verify jupytext can convert it**

Run: `uv run jupytext --from md:myst --to notebook --output /tmp/opencode/test_convert.ipynb tutorials/W2D1_Examples/W2D1_Tutorial1.md`
Expected: Successful conversion with no errors

**Step 4: Commit**

```bash
git add tutorials/W2D1_Examples/W2D1_Tutorial1.md
git commit -m "feat: add converted NMA Linear Dynamical Systems tutorial in MyST format"
```

---

### Task 4: Update myst.yml TOC

**Files:**
- Modify: `myst.yml:42-43` (insert new TOC section before the projects line)

**Step 1: Add TOC entry**

Insert the following YAML block in `myst.yml` between the Day 3 closing and the `projects/README.md` entry:

```yaml
    - title: "Day 4: Real Content Example"
      children:
        - file: tutorials/W2D1_Examples/chapter_intro.md
          children:
            - file: tutorials/W2D1_Examples/W2D1_Tutorial1.md
            - file: tutorials/W2D1_Examples/further_reading.md
```

The resulting TOC should have four day sections plus the projects entry.

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('myst.yml'))"`
Expected: No errors

**Step 3: Commit**

```bash
git add myst.yml
git commit -m "feat: add W2D1_Examples to myst.yml TOC"
```

---

### Task 5: Verify the full build

**Step 1: Run the notebook conversion script**

Run: `uv run python scripts/convert_to_notebooks.py --dry-run`
Expected: Output includes `W2D1_Tutorial1` in the list of files to process

**Step 2: Run actual conversion**

Run: `uv run python scripts/convert_to_notebooks.py`
Expected: Successfully generates `notebooks/W2D1_Examples/W2D1_Tutorial1.ipynb` with badge cell injected

**Step 3: Verify the generated notebook**

Run: `python3 -c "import json; nb=json.load(open('notebooks/W2D1_Examples/W2D1_Tutorial1.ipynb')); print(f'Cells: {len(nb[\"cells\"])}'); print(f'Badge: {\"colab-badge\" in nb[\"cells\"][0][\"source\"][0]}')" `
Expected: Cell count > 25, Badge: True

**Step 4: Build the MyST book**

Run: `uv run myst build --html`
Expected: Successful build with the new day appearing in the sidebar

**Step 5: Commit generated notebook (if on notebooks-branch) or note that CI handles this**

No commit needed -- CI pushes generated notebooks to `notebooks-branch` automatically.

---

### Task 6: Final review

**Step 1: Check no existing files were accidentally modified**

Run: `git diff HEAD~4 --name-only`
Expected: Only these files appear:
- `tutorials/W2D1_Examples/chapter_intro.md` (new)
- `tutorials/W2D1_Examples/further_reading.md` (new)
- `tutorials/W2D1_Examples/W2D1_Tutorial1.md` (new)
- `myst.yml` (modified)
- `docs/plans/2026-09-27-nma-tutorial-conversion-design.md` (new, from brainstorming)
- `docs/plans/2026-09-27-nma-tutorial-conversion-plan.md` (new, this plan)

**Step 2: Spot-check converted tutorial content**

Verify these elements are present in `W2D1_Tutorial1.md`:
- LaTeX equations (`\begin{equation}`, `\frac{dx}{dt}`)
- `<details><summary>` blocks
- `@widgets.interact` code
- `# to_remove solution` cells with `:tags: [hide-input]`
- `solve_ivp` import
- All 4 sections (1D ODEs, Oscillatory, 2D, Stream Plots) + Summary
