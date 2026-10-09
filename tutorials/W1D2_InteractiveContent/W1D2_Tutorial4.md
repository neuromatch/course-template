---
title: "Tutorial 4: Videos and Slides"
---

# Tutorial 4: Videos and Slides

Lecture videos and slide decks are written as two MyST directives,
`{nma-video}` and `{nma-slides}`. They render as plain embeds on the website,
so readers see them right away without starting the in-browser kernel. In the
Colab/Kaggle notebooks they become the usual hidden `# @title Video …` cells.

## Videos

````markdown
:::{nma-video} Video 1: Linear Dynamical Systems
:youtube: 87z6OR7-DBI
:bilibili: BV1up4y1S7wj
:::
````

renders as:

:::{nma-video} Video 1: Linear Dynamical Systems
:youtube: 87z6OR7-DBI
:bilibili: BV1up4y1S7wj
:::

- The argument is the title.
- `:youtube:`, `:bilibili:` and `:osf:` are each optional, but you need at
  least one. Tabs always appear in that order. With only one host, the player
  is shown without tabs.

## Slides

````markdown
:::{nma-slides} snv4m
:::
````

renders as:

:::{nma-slides} snv4m
:::

The argument is the OSF file id. `:title:` overrides the default heading
"Tutorial slides".

## Rules

- Put the directives at the top level of the page, not inside another
  directive such as `{note}` or `{tab-set}`.
- Don't add body text inside them, only options.
- CI checks every directive. Missing ids, unknown options and unclosed blocks
  fail the build with the file and line number.

## What the notebook gets

`scripts/convert_to_notebooks.py` replaces each directive with a hidden code
cell (`cellView: form`, `hide-input`). For videos, that cell builds the
YouTube/Bilibili `ipywidgets` Tab used in all Neuromatch notebooks. For
slides, it shows an OSF `IFrame` and prints the download link.

## How it works

| Where | File | Job |
|---|---|---|
| Website | `plugins/nma.mjs` (registered in `myst.yml` under `project.plugins`) | Turns directives into iframes and tabs during `myst build` |
| Notebooks | `scripts/nma_media.py` | Validates directives and replaces them with code cells |

Adding a new video host means editing both files. Add the embed and page URL
in `VIDEO_SOURCES` in `nma.mjs`, and add the option and label in
`VIDEO_SOURCES` in `nma_media.py`, plus a branch in the generated
`PlayVideo` class.

## Converting an existing NMA notebook

Replace each `# @title Video …` cell with an `{nma-video}`, copying the ids
from its `video_ids = [...]` line. Replace the `# @title Tutorial slides`
cell with `{nma-slides}`, using its `link_id`. Keep the "Submit your
feedback" cells as code cells.
