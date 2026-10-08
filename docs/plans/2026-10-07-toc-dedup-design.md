# TOC De-duplication Design

## Problem

The left sidebar shows each day twice, with an extra nesting level:

```
Day 1: Getting Started          (title-only group, not clickable)
└─ Day 1: Getting Started       (chapter_intro.md)
   ├─ Tutorial 1
   └─ ...
```

Cause: `myst.yml` wraps each day in a `title:` group whose only child is
`chapter_intro.md`. The intro page has the same frontmatter title, and the
tutorials hang off the intro as its children.

## Decision

Drop the `title:` wrapper. Make `chapter_intro.md` the day's top-level entry
with the tutorials as its direct children:

```yaml
- file: tutorials/W1D1_GettingStarted/chapter_intro.md
  children:
    - file: tutorials/W1D1_GettingStarted/W1D1_Tutorial1.md
    - ...
```

Result: one clickable "Day 1" entry (opens the intro page) and one level of
nesting. No page content changes.

Alternatives rejected:
- Rename intros to "Overview" inside the group: generic entries, extra edits.
- Drop intros from the TOC: learning objectives and schedule become unreachable.

## Scope

- `myst.yml`: restructure all 4 day entries.
- Update docs that teach the old pattern:
  - `tutorials/W1D1_GettingStarted/W1D1_Tutorial2.md` (TOC example, lines 14-22)
  - `tutorials/W1D3_PublishingAndCI/W1D3_Bonus.md` (TOC example, lines 22-30)
  - `AGENTS.md` ("Adding a new day": state the pattern explicitly)
- Out of scope: historical files in `docs/plans/`.

## Verification

1. `python3 -c "import yaml; yaml.safe_load(open('myst.yml'))"`
2. `uv run myst build --html`: no `⛔` errors.
3. `uv run myst start`: each day appears once in the sidebar, the tutorials are
   its direct children, and clicking the day opens the intro.
