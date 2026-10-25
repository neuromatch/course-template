# Neuromatch Course Guide

The manual and showcase for building a course with [MyST](https://mystmd.org)
(JupyterBook 2) and the [Neuromatch course kit](https://github.com/neuromatch/course-kit).

**Live book:** https://neuromatch.github.io/course-template/

## Starting a course

**Don't fork or copy this repository.** A course never merges back into it, and
its content will diverge. Generate a fresh repository with the kit instead:

```bash
uv venv && uv pip install neuromatch-course-kit
uv run nma-kit init --title "My Course" --author "Your Name" \
    --github https://github.com/<org>/<repo>
```

The result is a small starter (`myst.yml`, the CI workflow, one example day, a
setup checklist) with no history and no link to this repo. The CI logic, the
MyST plugin and the `nma-kit` CLI all come from the kit, so your course gets
fixes through the version in `course.yml` (`@v0.1`) and `extend:` in `myst.yml`.
See ["Starting a new course"](https://neuromatch.github.io/course-template/tutorials/new_course)
for the full walkthrough.

## What this repository is

A book that teaches course authors the kit, written with the kit, so each page
is also a working example:

| Part | What it shows |
|---|---|
| `tutorials/intro.md`, `tutorials/new_course.md` | Orientation and how to start a course |
| `W1D1` Getting Started | MyST writing, TOC, rich outputs, page types |
| `W1D2` Interactive Content | In-browser Python, widgets, videos, exercises, scrollytelling |
| `W1D3` Publishing and CI | The workflow, notebooks and badges, branding |
| `W2D1` Examples | A real NMA tutorial, as a normal page and as a scrolly page |
| `projects/` | Project booklet pages: guidance, a NeuroAI project, a dataset guide |

Copy snippets and pages from here into your course. Changes to the kit itself
belong in the kit repository.

## Working on this repository

Requires **Node.js >= 20** (`nvm use`) and Python 3.10+.

```bash
uv venv
uv pip install -r requirements.txt neuromatch-course-kit
uv run nma-kit check
uv run nma-kit sync-assets      # branding files (_nma/), re-run after kit upgrades
uv run myst start               # http://localhost:3000
```

For scrollytelling pages, run `uv run nma-kit render-scrolly` first so their
panels show real outputs. Pushes to `main` publish the site; pull requests are
checked and, with the Cloudflare settings in place, previewed.

Agents and contributors: see `AGENTS.md` for the authoring conventions.
