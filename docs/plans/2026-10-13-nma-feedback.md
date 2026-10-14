# Feedback Widgets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace hand-written vibecheck feedback cells with a `{nma-feedback}`
directive: a pure-JS widget on the site, standard NMA cells in notebooks.

**Architecture:** Settings live in a top-level `nma.feedback` block in
`myst.yml`. `plugins/nma.mjs` turns the directive into MyST's `anywidget` node
backed by `plugins/nma-feedback.mjs`, which posts to datatops with `fetch`.
`scripts/nma_feedback.py` validates the directive and expands it into notebook
cells, plus one injected gadget cell. Design: `2026-10-13-nma-feedback-design.md`.

**Tech Stack:** mystmd 1.11 plugin API (anywidget node), plain ESM, Python 3 +
PyYAML, pytest, `node --test`.

**Spike results (done):** anywidget nodes survive `myst build --html` and the
ESM is copied (`esm: '/plugins/...'` resolves from the project root). The
top-level `nma:` key and the `feedback_prefix` frontmatter key each log an
"extra key ignored" warning, not an error. The user checks rendering in the
browser.

---

### Task 1: `scripts/nma_feedback.py`: config, parsing, validation (TDD)

- `load_config(config: dict) -> (FeedbackConfig | None, errors)`. The shape is a
  mapping of non-empty plain string scalars `url`, `project`, `user_key`.
- `find_directives(text)` (top-level only; reuses the fence scanner style from
  `nma_media`), `validate(text)` with line numbers, `legacy_cell_errors(text)`.
- `page_prefix(text, stem)`: frontmatter `feedback_prefix`, else
  `W2D1_Tutorial1 -> W2D1_T1`, else the stem.
- Tests: `tests/test_nma_feedback.py`.

### Task 2: notebook expansion (TDD)

- `expand_notebook(nb, prefix, config) -> int`: directive -> hidden
  `# @title Submit your feedback` cell. Inject the gadget cell once at index 0.
- Wire into `convert_to_notebooks.py`: validation (directives, legacy cells,
  config needed only if directives exist) and the `build_notebooks` call.

### Task 3: JS config reader + plugin directive

- `readNmaConfig(text)` in `plugins/nma.mjs`, exported for tests. It is tested
  with `node --test tests/js/` against shared fixtures in
  `tests/fixtures/nma_config/*.yml` + `.json`, which Python also checks.
- `nma-feedback` directive -> placeholder; a document transform resolves the
  prefix and config and emits an `anywidget` node, with fatal errors for bad
  args, nesting or missing config.

### Task 4: `plugins/nma-feedback.mjs` widget + CSS

### Task 5: config + content migration

- `myst.yml` `nma:` block; W2D1 Tutorial 1 (prefix, 10 directives, setup cell);
  W1D2 Bonus setup cell.

### Task 6: docs

- AGENTS.md and the W1D2 docs tutorial.

### Task 7: remove the vibecheck/datatops wheels (separate commit)

### Verification

- `uv run pytest -q`, `node --test tests/js`, `convert_to_notebooks.py` on the
  real tree (check the W2D1 notebook cells), `myst build --html` (no errors;
  10 anywidget nodes with the expected `section_id`s).
