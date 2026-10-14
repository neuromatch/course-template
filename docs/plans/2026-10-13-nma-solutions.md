# Exercise Solutions and Explanations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `{nma-solution}` / `{nma-explanation}` directives produce site links,
student and instructor notebooks, solution files on `notebooks-branch`, and a
hidden "Run all" fallback on the site.

**Architecture:** A new `scripts/nma_solutions.py` handles the Python side:
scanning, validation, notebook splitting, solution files, and the fallback
setup cell. `convert_to_notebooks.py` calls it. `plugins/nma.mjs` gets the two
directives, which emit placeholders, and a document transform that numbers them
and turns them into GitHub links. Design: `2026-10-13-nma-solutions-design.md`.

**Tech Stack:** Python 3 + pytest, jupytext, IPython (for testing the
transformer), and MyST JS plugins (mystmd 1.11).

---

## Spike findings (done)

- `remove-cell` blocks stay in the page AST as executable code, hidden only by
  CSS, so the fallback setup cell can be `remove-cell`.
- pyodide-kernel 0.4.7 `PyodideKernel.run` calls `interpreter.transform_cell`
  (to detect imports) and then `run_cell_async`, which applies
  `input_transformers_post`. The transformer therefore runs twice and must be
  pure: the "reference solution was run" print goes *into* the returned source.
- In a plugin `document` transform, the `mystDirective` wrapper is gone. A
  top-level placeholder's ancestors are `root > block`, and a nested one has
  more ancestors (for example `admonition`). `vfile.path` is absolute.
- A directive body declared as `String` and not emitted does not appear in the
  page JSON. MyST still publishes the source `.md` under `_build/site/public/`,
  so solutions are hidden but not secret, as the design already accepts.

## Task 1: Fence scanner and directive model

**Files:** create `scripts/nma_solutions.py` and `tests/test_nma_solutions.py`.

- `scan_fences(text) -> list[Fence]`: a stack-based scanner.
  - `Fence(char, length, info, start, end, depth, literal)`.
  - A fence is *literal* (its contents are opaque) unless it is a colon fence or
    a backtick/tilde fence whose info starts with `{` and isn't
    `{code-cell}` / `{code}` / `{code-block}`.
  - A close is the same char, length ≥ the opener, and no info.
  - Unclosed fences get `end = -1`.
- `find_blocks(text) -> list[Block]`: the solution, explanation, and exercise
  blocks.
  - `Block(kind, start, end, nested, arg, options, body_lines)`, where kind is
    one of `nma-solution`, `nma-explanation`, `exercise`, `code-cell`.
  - `nested` is True when the block is inside a parsed container (depth > 0).
  - Options are the leading `:key: value` lines of the body.
  - An `exercise` is a top-level `{code-cell}` whose body contains
    `raise NotImplementedError`.

Tests: top-level detection, ignoring blocks inside a `` ````markdown `` example,
flagging nesting inside `:::{note}`, backtick-form directives, unclosed blocks,
and exercise detection. Commit.

## Task 2: Validation

`validate(text) -> list[str]`, with each message prefixed by `line N:`. Errors:
- a top-level code cell with a line starting `# to_remove`
- a nested solution or explanation
- an unclosed block
- unknown options or an argument
- a solution body that isn't exactly one fence with info `python` and
  non-empty code
- an empty explanation body
- a solution not directly after an exercise (only blank lines allowed between)
- an exercise not directly followed by a solution

Tests: one per error, plus a valid page that returns `[]`. Wire it into
`convert_to_notebooks.validate_content`. Commit.

## Task 3: Naming and URLs

- `solution_filename(stem, kind, n)` returns `<stem>_Solution_<n>.py` or
  `<stem>_Explanation_<n>.md`.
- `solution_url(repo, rel_dir, filename)` returns
  `https://github.com/<repo>/blob/notebooks-branch/notebooks/<rel_dir>/solutions/<filename>`.
- `extract(text, stem) -> list[Item]` returns, per top-level directive in
  order, `Item(kind, n, filename, content)`. A solution's content is the code
  inside the fence, and an explanation's content is the Markdown body. Both
  end with a single trailing newline.
- `exercise_pairs(text) -> list[(exercise_source, solution_source)]`. The
  exercise source has its option lines stripped.

Tests. Commit.

## Task 4: Notebook splitting

`split_notebook(nb, stem, rel_dir, repo) -> (student_nb, instructor_nb, files)`:
- Markdown cells containing top-level directives are split like
  `nma_media.expand_markdown_cell`, with empty fragments dropped.
- Student cells:
  - solution: `[*Click for solution*](url)`
  - explanation: `[*Click for explanation*](url)`
- Instructor cells:
  - solution: a code cell with `# to_remove solution\n` + code and metadata `{"cellView": "form"}`
  - explanation: a markdown cell with `**Explanation**\n\n` + body
- `files` is a dict mapping filename to content.
- Numbering is counted across the whole notebook, so it matches the JS plugin
  and `extract`.

Tests: student cells contain no solution code, the instructor cells, numbering
across several cells, and notebooks without directives pass through unchanged.
Commit.

## Task 5: Run-all fallback setup cell

- `fallback_cell_source(pairs) -> str`: a self-contained Python source starting
  with the sentinel `# nma-exercise-fallback (generated, do not edit)`.
  - It registers an `input_transformers_post` function. The function:
    - skips sources with no `raise NotImplementedError`
    - skips the setup cell itself (it contains the sentinel)
    - picks an exact match, otherwise the best `difflib` ratio ≥ 0.6
    - returns `print(<note>)` followed by the solution
  - Re-running the cell replaces the transformer rather than stacking another.
- `fallback_md_block(pairs)` wraps it as a `{code-cell} python` with
  `:tags: [remove-cell]`.

Tests: run inside a real `IPython.core.interactiveshell.InteractiveShell`.
Running the exercise prints the note and defines the solved function. A
finished exercise runs unchanged. Fuzzy matching works after a small edit.
Re-running the setup cell keeps one transformer. Commit.

## Task 6: Wire into `convert_to_notebooks.py`

- Default mode:
  - jupytext produces the student path
  - load it, `expand_notebook` (media), `split_notebook`
  - add a badge cell to each notebook
  - write the student nb, `instructor/<stem>.ipynb`, and `solutions/*`
- `--prepare-site` (with `--inject-md-badges` as an alias):
  - after the frontmatter, write the badges, then the fallback block when the
    page has exercises
  - idempotent: strip any existing badge line and existing fallback block first
- Update the module docstring and print summaries.

Verify:
- `uv run python scripts/convert_to_notebooks.py`
- `uv run python scripts/convert_to_notebooks.py --prepare-site` twice, then
  `git diff --stat`, then `git checkout -- tutorials/`

Commit.

## Task 7: MyST plugin

`plugins/nma.mjs`:
- Directives `nma-solution` and `nma-explanation`
  (`body: {type: String, required: true}`) return `{type: 'nmaSolutionRef', kind}`.
- The transform `nma-solution-links` (stage `document`):
  - Walk the tree with ancestors. A placeholder whose ancestors aren't exactly
    `root > block` gets a fatal "must be at the top level" error.
  - Number the placeholders per kind.
  - Derive `rel_dir` and `stem` from `vfile.path`, taking the part after
    `/tutorials/`.
  - Read `project.github` from `myst.yml` in `process.cwd()` with a regex that
    matches a github.com URL.
  - Replace each placeholder with a `div.nma-solution-link` containing a
    paragraph, link, emphasis, and text.
- Add a "keep in sync with scripts/nma_solutions.py" comment next to the naming rule.

Commit.

## Task 8: Migrate W2D1

Convert the 2 `# to_remove solution` cells into `{nma-solution}`. Convert the
5 `# to_remove explanation` cells into `{nma-explanation}`, turning each
docstring into a Markdown list or paragraphs. Verify with the converter and
pytest. Commit.

## Task 9: Docs

- Update `AGENTS.md` (architecture, conventions, tags, conversion table and
  checklist, CI).
- Add `W1D2_Tutorial5.md` "Exercises and Solutions", with a live example, and
  add it to the TOC.
- Update the badge step name and flag in `publish-book.yml`.

Commit.

## Task 10: End-to-end verification

1. `uv run pytest -q`
2. Run the converter. Expect 2 `.py` and 5 `.md` files under
   `notebooks/W2D1_Examples/solutions/`. The student notebook should contain no
   solution code, and the instructor notebook should contain it.
3. `--prepare-site`, then `myst build --html`, with no `⛔`. The W2D1 page
   should have the links and no solution code in the visible blocks, and the
   fallback cell should be a `remove` block.
4. Run `git checkout -- tutorials/`.
