# Feedback Widgets

## Goal

Authors write per-section feedback as a MyST directive instead of the
hand-written vibecheck code cells. One source produces:

- **Site**: a 🙂/😐/🙁 widget, rendered at build time as a pure-JS
  `anywidget` node. It posts straight to the datatops API from the browser and
  works with no kernel, before or after JupyterLite starts.
- **Notebooks** (student and instructor, Colab/Kaggle): the standard NMA hidden
  `# @title Submit your feedback` code cells, plus one injected
  "Import feedback gadget" cell.

## Problems with the current approach

- In `W2D1_Tutorial1.md`, each feedback point is a `hide-input` code cell
  `content_review(f"{feedback_prefix}_<Section>")`. It depends on an
  "Import feedback gadget" setup cell and on micropip-installing `ipywidgets`,
  `vibecheck` and `datatops` (from `_wheels/`).
- On the static site the widget doesn't render at all. Readers only see it
  after starting JupyterLite and running the setup cells plus each feedback cell.
- Authors copy the same boilerplate (gadget cell, setup install, feedback cells)
  onto every page.

## Findings

- vibecheck is a thin UI over one HTTP call:
  `POST {url}/api/v1/projects/{project}` with header `X-User-Key: {user_key}`
  and JSON body `{button_name, feedback, section_id, timestamp_utc}`. The
  response is `{"status": "success"}` or `{"status": ..., "message": ...}`.
  `button_name` is `happy` (sent immediately), or `medium`/`sad` (sent with
  the textarea text).
- The endpoint (`https://pmyvdlilci.execute-api.us-east-1.amazonaws.com/klab`,
  project `neuromatch_cn`, user key `y1x3mpx5`) answers CORS preflight with
  the origin reflected and `content-type, x-user-key` allowed. A browser `fetch`
  works with no Python.
- mystmd 1.11 ships an `anywidget` node (`{type, esm, model, css, class, id}`).
  The CLI copies or hashes the `esm`/`css` assets into the site, and the theme
  loads the module client-side with no kernel.

## Decisions

- Keep the same datatops backend and the same `section_id` scheme, so existing
  analysis and dashboards keep working across site, Colab and Kaggle.
- `section_id = {prefix}_{arg}`. The prefix comes from the page frontmatter
  `feedback_prefix:`, or by default from the filename
  (`W2D1_Tutorial1` -> `W2D1_T1`). W2D1 sets `feedback_prefix: W2D2_T1` to
  keep its legacy ids.
- The directive is the only supported form. CI rejects hand-written feedback
  cells.
- The site no longer installs `vibecheck`/`datatops`. Notebooks install them
  through the injected gadget cell.
- The datatops keys (url, project, user_key) are defined once, in a top-level
  `nma:` block in `myst.yml` (see "Configuration"). Both `plugins/nma.mjs`
  and `scripts/nma_feedback.py` read them from there. Nothing is hard-coded.

## Configuration

`myst.yml` stays the only config file. NMA-specific settings go in a new
top-level `nma:` block, next to `version`/`project`/`site`:

```yaml
version: 1
project:
  ...
site:
  ...

# Neuromatch settings, read by plugins/nma.mjs and scripts/ (not by MyST).
nma:
  feedback:
    url: https://pmyvdlilci.execute-api.us-east-1.amazonaws.com/klab
    project: neuromatch_cn
    user_key: y1x3mpx5
```

- **Why the top level:** `project.*` and `site.*` are validated by MyST and
  belong to it. A separate top-level block makes it obvious which settings are
  ours, and gives later NMA settings (the notebooks branch name, the wheel
  base URL) the same home.
- **MyST warning:** mystmd 1.11 validates the top-level keys of `myst.yml`
  (`version`, `project`, `site`, `extends`) and logs
  `extra key ignored: nma` as a *warning*. The build doesn't fail. Step 1 of
  the plan confirms this on a real build. If the warning turns out to be an
  error, or too noisy, the fallback is the same block in a separate
  `nma.yml`, with no other changes to the design.
- **`user_key` is not a secret.** It's a write-only key that's already
  published in every NMA notebook. Committing it is fine. This gets a one-line
  comment in `myst.yml`.
- **Required only when used.** If any page uses `{nma-feedback}` and
  `nma.feedback` is missing or incomplete, both CI (`convert_to_notebooks.py`)
  and `myst build` fail with
  `nma-feedback needs nma.feedback.{url,project,user_key} in myst.yml`.
  Forks of the template keep the block (and so post to the neuromatch
  project) until they change it. Deleting the block plus every directive is
  how a course opts out.
- **Shape is restricted:** `nma.feedback` is a mapping of plain string
  scalars. The JS plugin has no YAML library: plugins load as standalone ESM
  with no `node_modules`, and today's `githubRepo()` already regex-parses
  `myst.yml`. So `nma.mjs` gets a small reader, `readNmaConfig()`, that
  pulls the `nma:` block out by indentation and reads `key: value` lines
  (quoted or unquoted) at two levels. Python reads it with `yaml.safe_load`.
  The CI check rejects anything outside the supported shape (non-string
  values, flow style `{...}`, anchors, multi-line strings). That keeps the two
  readers from silently disagreeing.
- **Placement in AGENTS.md:** the "Key files → `myst.yml`" entry is updated to
  "project metadata, TOC, JupyterLite, site theme, and the `nma:` block".

## Authoring syntax

```markdown
---
title: "Tutorial 1: Linear Dynamical Systems"
feedback_prefix: W2D2_T1
kernelspec:
  name: python3
  display_name: Python 3
---

:::{nma-feedback} Linear_Dynamical_Systems_Video
:::
```

Rules (enforced in Python by `convert_to_notebooks.py`, and in JS at build
time where possible):

- Top level of the page only, not nested in another directive or fence.
- The argument is required and matches `[A-Za-z0-9_]+`.
- No options, no body, must be closed.
- `feedback_prefix`, if set, matches `[A-Za-z0-9_]+`.
- Code cells may not contain `content_review(`, `import vibecheck` /
  `from vibecheck`, or `# @title Import feedback gadget`. The error tells
  the author to use `{nma-feedback}`.

## Site rendering

- `plugins/nma.mjs` adds an `nma-feedback` directive. It emits a placeholder
  node. A document-stage transform resolves the prefix by reading the page's
  raw frontmatter, reads the keys with `readNmaConfig().feedback` (cached,
  like `githubRepo()`), and replaces the placeholder with:

  ```js
  { type: 'anywidget', esm: 'plugins/nma-feedback.mjs',
    model: { section_id, url, project, user_key }, class: 'nma-feedback', id }
  ```

- `plugins/nma-feedback.mjs` (anywidget ESM, `export default { render }`):
  - Draws the three buttons. 🙂 submits right away. 😐/🙁 highlight the button
    and open a textarea with a Submit button.
  - Posts the vibecheck payload with `fetch`, with `timestamp_utc` set to
    `new Date().toISOString()`.
  - Success: hide the inputs and show "Thanks for your feedback!".
  - Failure (network error, or response without `status: "success"`): show
    "Couldn't send feedback, please try again". Keep the selection and text and
    leave Submit enabled.
- Styling: a small CSS block (in `_static/custom.css` or as the anywidget `css`
  asset). It must look right in light and dark themes.

## Notebook generation

New `scripts/nma_feedback.py`, built like `nma_media.py`:

- `find_directives` / `validate` (with line numbers) / `legacy_cell_errors`.
- `load_config(myst_yml) -> FeedbackConfig | None`, plus `config_errors(...)`
  for the shape rules in "Configuration". `convert_to_notebooks.py` already
  loads `myst.yml` for `project.github`, so it reads the `nma:` block in the
  same place.
- `resolve_prefix(frontmatter, stem)`.
- `expand_notebook(nb, prefix)` replaces each directive in markdown cells with:

  ```python
  # @title Submit your feedback
  content_review(f"{feedback_prefix}_Linear_Dynamical_Systems_Video")
  ```

  (`cellView: form`, `hide-input`). If at least one was expanded, it inserts
  one hidden gadget cell at the top of the notebook (before the solutions split,
  so the badge still ends up at position 0):

  ```python
  # @title Import feedback gadget
  %pip install -q vibecheck datatops
  from vibecheck import DatatopsContentReviewContainer
  def content_review(notebook_section: str): ...   # url/name/user_key filled in from myst.yml
  feedback_prefix = "W2D2_T1"
  ```

  No `sys.platform == "emscripten"` branch is needed. Generated notebooks
  only run on Colab, Kaggle or a local Jupyter, where pip works and
  vibecheck/datatops install from PyPI. The site's JupyterLite runs the `.md`
  pages, not these notebooks, and on those pages `{nma-feedback}` is the JS
  widget, so no Python feedback code ever runs under Pyodide.

  The generated notebook carries literal values. It never reads `myst.yml` at
  runtime, so it still works stand-alone on Colab/Kaggle.

- `convert_to_notebooks.py` calls it next to `nma_media.expand_notebook`, and
  adds its validation to `validate_content`. Student and instructor notebooks
  get the same cells.

## Migration

- `myst.yml`: add the `nma.feedback` block with today's values.
- `W2D1_Tutorial1.md`: add `feedback_prefix: W2D2_T1`, replace the 10 feedback
  cells with directives, delete the gadget cell, and drop
  `vibecheck`/`datatops` (and the Colab `!pip install`) from the setup cell.
- `W1D2_Bonus.md`: drop the vibecheck micropip install.
- Docs: AGENTS.md (directive convention, conversion table row
  "Submit your feedback cell -> `{nma-feedback}`", setup-cell pattern,
  micropip package list), plus a "Feedback" section in the W1D2 interactive
  content tutorial.
- Delete `_wheels/vibecheck*`/`datatops*` and drop them from the
  `build-pyodide-wheels.yml` loop. After the steps above nothing references
  them: the site uses the JS widget and notebooks pip-install from PyPI.
  This is a separate final commit so it's easy to revert. Remove them from
  the AGENTS.md "Packages needing micropip" list and the setup-cell example,
  leaving `ipywidgets`.

## Testing

- pytest (`tests/test_nma_feedback.py`): parsing, nested and fenced examples
  ignored, validation messages with line numbers, prefix override and default,
  expansion output, gadget cell injected exactly once (and not at all without
  directives), legacy-cell rejection, and an end-to-end conversion of a fixture
  page. Config: values are loaded, a missing block with no directives is fine,
  a missing block or key with directives is an error, and unsupported shapes
  are rejected.
- JS config reader: `node --test` on `readNmaConfig()` over a few `myst.yml`
  fixtures, including the real one, comments, quoted values, and a following
  top-level key. Its result must match what PyYAML gives for the same
  fixtures (the expected values are stored as JSON next to each fixture and
  used by both test suites).
- `myst build --html`: no errors, and the W2D1 page JSON has 10 `anywidget`
  nodes with the expected `section_id`s.
- Manual: in the browser, the widget renders before JupyterLite starts. One
  real submission with a `TEMPLATE_TEST_*` section id succeeds, and a forced
  failure (offline) shows the retry message.

## Risks (check first)

1. **The book-theme may not render `anywidget` nodes.** Check with a minimal
   page before anything else. Fallback: render a static link-out instead, and
   revisit.
2. **The unknown `feedback_prefix` frontmatter key may warn or fail.** Check
   the `myst build` output. Fallback: a per-page prefix map under
   `nma.feedback.prefixes` in `myst.yml`, or an optional `:prefix:` directive
   option.
3. **The top-level `nma:` key in `myst.yml` warns ("extra key ignored") or
   fails.** The source says it's a warning. Confirm on a real build. Fallback:
   move the block to `nma.yml`, with the same shape and readers.

## Out of scope

- Porting the vibecheck admin results view.
- Changing the datatops backend. (It's now configurable per course through
  `nma.feedback`, but provisioning new datatops projects isn't covered.)
- Moving other existing constants (notebooks branch, wheel URL) into `nma:`.
  The block is designed to hold them later.
- Feedback in non-tutorial pages (allowed, but not migrated).
