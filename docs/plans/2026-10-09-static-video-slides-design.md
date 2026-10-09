# Static Video and Slide Embeds

## Goal

Videos and slides render on the published site as static HTML, so readers don't
need to start Pyodide to see them. Generated Colab/Kaggle notebooks still get
the familiar NMA `# @title Video …` code cells.

## Problem

In `tutorials/W2D1_Examples/W2D1_Tutorial1.md` the slides (line 54) and the
three videos (lines 271, 546, 664) are `hide-input` code cells. Each video cell
is about 45 lines that build an ipywidgets `Tab` of `YouTubeVideo`/`IFrame`.
`publish-book.yml` runs `myst build --html` without `--execute`, so these cells
have no output. The page shows a collapsed code toggle and no player. Executing
at build time wouldn't fully fix this either, because widget Tabs don't render
statically.

## Decisions

- Authors write MyST directives in the `.md` source, not code cells.
- Notebooks get a hidden code cell that embeds the player, the same as current
  NMA notebooks.
- The directives are custom and come from a small MyST JavaScript plugin. We
  rejected the alternatives: native `tab-set` + `iframe` is verbose and the
  converter would have to parse embed URLs back into IDs, and build-time
  execution needs a kernel and still can't render widgets.

## Authoring syntax

```markdown
:::{nma-video} Video 1: Linear Dynamical Systems
:youtube: 87z6OR7-DBI
:bilibili: BV1up4y1S7wj
:osf: abc12
:::

:::{nma-slides} snv4m
:title: Tutorial slides
:::
```

- `nma-video`: the argument is the title. `youtube`, `bilibili` and `osf` are
  each optional, but at least one is required.
- `nma-slides`: the argument is the OSF id (required). `title` defaults to
  "Tutorial slides".

## Site rendering: `plugins/nma.mjs`

Registered in `myst.yml` under `project.plugins`.

- `nma-video` renders the title in bold, then a `tabSet` with one `tabItem` per
  source in the order YouTube, Bilibili, OSF. Each tab holds an `iframe` node.
  With a single source it renders a bare iframe and no tabs. Below the player is
  a "Video available at <link>" line for each source.
  - YouTube: `https://www.youtube.com/embed/{id}?rel=0`
  - Bilibili: `https://player.bilibili.com/player.html?bvid={id}&page=1&autoplay=0`
  - OSF: `https://mfr.ca-1.osf.io/render?url=https://osf.io/download/{id}/?direct%26mode=render`
- `nma-slides` renders the title, an OSF render iframe
  (`https://mfr.ca-1.osf.io/render?url=https://osf.io/{id}/?direct%26mode=render%26action=download%26mode=render`)
  and a "Download the slides" link to `https://osf.io/download/{id}/`.
- An `nma-video` with no source raises a MyST error, which shows as `⛔` in the
  build output.

## Notebook generation: `scripts/nma_media.py`

This module is the single Python source for parsing the directives, building
URLs and producing code cells. `convert_to_notebooks.py` imports it.

1. **Parse.** A fence-aware scanner (same logic as `has_code_cells`) finds
   top-level `:::{nma-video}` / `:::{nma-slides}` blocks, in both the colon and
   backtick fence forms. Blocks nested inside other fences are examples and are
   ignored.
2. **Split.** After jupytext writes the `.ipynb`, every markdown cell that
   contains a directive is split into: markdown before, then a generated code
   cell, then markdown after. Empty fragments are dropped.
3. **Code cell.** The cell comes from a template that reproduces the current
   NMA cell: `# @title <title>`, self-contained `PlayVideo`/`display_videos`,
   `video_ids = [...]`, and the `widgets.Tab` display. Slides become the
   existing `IFrame` cell plus the download `print`. Cell metadata is
   `cellView: "form"` and `tags: ["hide-input"]`.
4. **Validate.** `validate_content()` reports these, with file and line, in
   both script modes: an `nma-video` with no source, unknown options, or an
   `nma-slides` with no id.

## CI

- `publish-book.yml`: add `plugins/**` to `push.paths`. No new step is needed
  because the plugin renders during `myst build`.
- `generate-notebooks.yml`: widen the `scripts/convert_to_notebooks.py` path
  filter to `scripts/**`.

## Migration

In `W2D1_Tutorial1.md`, replace the slides cell and the three video cells with
directives. The "Submit your feedback" `content_review` cells and the
interactive widget demos stay as code cells.

## Documentation

- `AGENTS.md`:
  - Architecture section: add `plugins/nma.mjs` and `scripts/nma_media.py`.
  - Key Conventions: add a section on the directives.
  - Conversion mapping table: video and slide cells map to
    `{nma-video}`/`{nma-slides}`.
  - Conversion checklist: add a step for converting media cells.
  - Update the CI trigger paths.
- New page `tutorials/W1D2_InteractiveContent/W1D2_Tutorial4.md`, "Videos and
  Slides", added to the `myst.yml` TOC. It covers:
  - the syntax, shown inside a markdown fence
  - a live rendered example of each directive
  - what the generated Colab cell looks like
  - how to add a new video host (update the JS and the Python side together)
- `W1D3_Tutorial1`: a short note that the plugin renders media at build time
  and that changes under `plugins/**` trigger a publish.

## Testing

- `tests/test_nma_media.py` (pytest, with `pytest` added to
  `requirements.txt`). It covers:
  - option parsing
  - ignoring directives nested inside fences
  - splitting a markdown cell into before, code and after
  - the code cells for one source and for several sources
  - validation errors
- End-to-end checks:
  - `convert_to_notebooks.py`: `W2D1_Tutorial1.ipynb` has four generated
    media cells and no leftover directive text.
  - `myst build --html`: no `⛔`, and the built HTML contains the YouTube,
    Bilibili and OSF iframe `src` URLs.
  - A visual check in `myst start`.

## Out of scope

- Executing notebooks at build time.
- Static rendering of the feedback widget or of `@widgets.interact` demos.
