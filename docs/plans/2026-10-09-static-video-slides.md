# Static Video and Slide Embeds Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Render NMA videos and slides on the published site as static HTML,
with no Pyodide needed, while generated notebooks keep the NMA `# @title Video`
code cells.

**Architecture:** Authors write `{nma-video}` / `{nma-slides}` directives in
the `.md` source. A MyST JavaScript plugin (`plugins/nma.mjs`) turns them into
iframes and tab sets when the site is built. A Python module
(`scripts/nma_media.py`) validates the directives and, after jupytext converts
a page, swaps each one for a hidden NMA-style code cell in the generated
`.ipynb`.

**Tech Stack:** mystmd 1.11 (JS plugin API: `DirectiveSpec`, AST nodes
`tabSet`/`tabItem`/`iframe`/`div`), Python 3, jupytext, pytest, GitHub Actions.

Design: `docs/plans/2026-10-09-static-video-slides-design.md`

**Local environment notes**
- MyST needs Node >= 20. Before any `myst` command, run:
  `export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh" && nvm use 22`
- Run Python through uv: `uv run python ...`, `uv run pytest ...`
- `notebooks/` and `_build/` are gitignored. Never commit them.

---

### Task 0: Commit the design and plan docs

**Step 1: Commit**

```bash
git add docs/plans/2026-10-09-static-video-slides-design.md docs/plans/2026-10-09-static-video-slides.md
git commit -m "docs: add design and plan for static video/slide embeds"
```

---

### Task 1: Test scaffolding

**Files:**
- Modify: `requirements.txt` (add `pytest` at the end)
- Create: `tests/conftest.py`

**Step 1: Add pytest to requirements.txt**

Append this line:

```
pytest
```

**Step 2: Create `tests/conftest.py`**

`scripts/` is not a package. This puts it on `sys.path` so tests can
`import nma_media`, the same way `convert_to_notebooks.py` does when it runs as
a script.

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
```

**Step 3: Install and check**

Run: `uv pip install -r requirements.txt && uv run pytest -q`
Expected: `no tests ran` (exit code 5). That's fine at this point.

**Step 4: Commit**

```bash
git add requirements.txt tests/conftest.py
git commit -m "test: add pytest scaffolding"
```

---

### Task 2: Directive parser (`find_directives`)

**Files:**
- Create: `scripts/nma_media.py`
- Create: `tests/test_nma_media.py`

**Step 1: Write failing tests**

`tests/test_nma_media.py`:

```python
import re

from nma_media import find_directives

VIDEO_MD = """Intro text

:::{nma-video} Video 1: Linear Dynamical Systems
:youtube: 87z6OR7-DBI
:bilibili: BV1up4y1S7wj
:::

Outro text
"""


def test_find_video_directive():
    [d] = find_directives(VIDEO_MD)
    assert d.kind == "nma-video"
    assert d.arg == "Video 1: Linear Dynamical Systems"
    assert d.options == {"youtube": "87z6OR7-DBI", "bilibili": "BV1up4y1S7wj"}
    assert (d.start, d.end) == (2, 5)
    assert d.body == []


def test_find_backtick_slides_directive():
    [d] = find_directives("```{nma-slides} snv4m\n:title: Day slides\n```\n")
    assert d.kind == "nma-slides"
    assert d.arg == "snv4m"
    assert d.options == {"title": "Day slides"}


def test_ignores_directive_inside_example_fence():
    text = "````markdown\n:::{nma-video} T\n:youtube: x\n:::\n````\n"
    assert find_directives(text) == []


def test_ignores_directive_nested_in_other_directive():
    text = ":::{note}\n:::{nma-video} T\n:youtube: x\n:::\n:::\n"
    # Only top-level media directives are supported (see validate_content docs)
    assert find_directives(text) == []


def test_unclosed_directive_has_end_minus_one():
    [d] = find_directives(":::{nma-video} T\n:youtube: x\n")
    assert d.end == -1


def test_body_lines_are_captured():
    [d] = find_directives(":::{nma-video} T\n:youtube: x\nstray text\n:::\n")
    assert d.body == ["stray text"]
```

**Step 2: Run them and confirm they fail**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nma_media'`

**Step 3: Implement**

`scripts/nma_media.py`:

```python
"""
Parse {nma-video} / {nma-slides} directives in MyST Markdown and expand them
into NMA-style code cells for generated notebooks.

The website renders the same directives with plugins/nma.mjs. The URL
templates here and in that file must stay in sync.

Syntax (top level of a page only, not nested inside other directives/fences):

    :::{nma-video} Video 1: Title
    :youtube: <id>
    :bilibili: <BV id>
    :osf: <id>
    :::

    :::{nma-slides} <osf id>
    :title: Tutorial slides
    :::
"""

import re
from dataclasses import dataclass, field

ANY_FENCE_RE = re.compile(r"^(`{3,}|~{3,}|:{3,})(.*)$")
DIRECTIVE_RE = re.compile(r"^\{(nma-video|nma-slides)\}\s*(.*?)\s*$")
OPTION_RE = re.compile(r"^:([A-Za-z][\w-]*):\s*(.*?)\s*$")


@dataclass
class MediaDirective:
    kind: str                 # "nma-video" or "nma-slides"
    arg: str                  # video title, or OSF id for slides
    options: dict             # option name -> value
    start: int                # 0-based line index of the opening fence
    end: int = -1             # 0-based line index of the closing fence; -1 if unclosed
    body: list = field(default_factory=list)  # unexpected non-option lines


def find_directives(text: str) -> list[MediaDirective]:
    """
    Return the top-level media directives in `text`, in order.

    Anything inside another fence (```, ~~~ or :::) is skipped. That keeps
    syntax examples on documentation pages from being treated as real
    directives.
    """
    found = []
    open_fence = None   # (char, length) of a non-media fence we're inside
    current = None      # directive being read
    current_fence = None

    for i, line in enumerate(text.splitlines()):
        match = ANY_FENCE_RE.match(line)

        if current is not None:
            if (match and match.group(1)[0] == current_fence[0]
                    and len(match.group(1)) >= current_fence[1]
                    and not match.group(2).strip()):
                current.end = i
                found.append(current)
                current = None
                continue
            option = OPTION_RE.match(line)
            if option and not current.body:
                current.options[option.group(1)] = option.group(2)
            elif line.strip():
                current.body.append(line)
            continue

        if not match:
            continue
        marker, info = match.group(1), match.group(2).strip()
        if open_fence is None:
            directive = DIRECTIVE_RE.match(info)
            if directive:
                current = MediaDirective(directive.group(1), directive.group(2), {}, i)
                current_fence = (marker[0], len(marker))
            else:
                open_fence = (marker[0], len(marker))
        elif marker[0] == open_fence[0] and len(marker) >= open_fence[1] and not info:
            open_fence = None

    if current is not None:
        found.append(current)  # unclosed; validate_directive reports it
    return found
```

**Step 4: Run tests and confirm they pass**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: 6 passed

**Step 5: Commit**

```bash
git add scripts/nma_media.py tests/test_nma_media.py
git commit -m "feat: parse nma-video/nma-slides directives"
```

---

### Task 3: Directive validation

**Files:**
- Modify: `scripts/nma_media.py`
- Modify: `tests/test_nma_media.py`

**Step 1: Write failing tests** (append; add `validate_directive` to the import)

```python
from nma_media import validate_directive


def _errors(text):
    [d] = find_directives(text)
    return validate_directive(d)


def test_valid_video_has_no_errors():
    assert _errors(VIDEO_MD) == []


def test_valid_slides_has_no_errors():
    assert _errors(":::{nma-slides} snv4m\n:::\n") == []


def test_video_without_source_is_error():
    [err] = _errors(":::{nma-video} T\n:::\n")
    assert "at least one of :youtube:, :bilibili:, :osf:" in err
    assert err.startswith("line 1: ")


def test_video_without_title_is_error():
    [err] = _errors(":::{nma-video}\n:youtube: x\n:::\n")
    assert "needs a title" in err


def test_unknown_option_is_error():
    [err] = _errors(":::{nma-video} T\n:youtube: x\n:vimeo: y\n:::\n")
    assert "unknown option :vimeo:" in err


def test_slides_without_id_is_error():
    [err] = _errors(":::{nma-slides}\n:::\n")
    assert "needs an OSF id" in err


def test_unclosed_is_error():
    [err] = _errors(":::{nma-slides} x\n")
    assert "never closed" in err


def test_body_is_error():
    [err] = _errors(":::{nma-video} T\n:youtube: x\nhello\n:::\n")
    assert "takes no body" in err
```

**Step 2: Run them and confirm they fail**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: FAIL with `ImportError: cannot import name 'validate_directive'`

**Step 3: Implement** (append to `scripts/nma_media.py`)

```python
# (option name, label used in NMA's video_ids, order on the page)
VIDEO_SOURCES = [("youtube", "Youtube"), ("bilibili", "Bilibili"), ("osf", "Osf")]
ALLOWED_OPTIONS = {
    "nma-video": {name for name, _ in VIDEO_SOURCES},
    "nma-slides": {"title"},
}
DEFAULT_SLIDES_TITLE = "Tutorial slides"


def validate_directive(d: MediaDirective) -> list[str]:
    """Return human-readable errors for one directive, each prefixed with its line."""
    where = f"line {d.start + 1}: {{{d.kind}}}"
    errors = []
    if d.end == -1:
        errors.append(f"{where} is never closed")
    for name in sorted(set(d.options) - ALLOWED_OPTIONS[d.kind]):
        allowed = ", ".join(f":{o}:" for o in sorted(ALLOWED_OPTIONS[d.kind]))
        errors.append(f"{where} has unknown option :{name}: (allowed: {allowed})")
    if d.body:
        errors.append(f"{where} takes no body content, only options")
    if d.kind == "nma-video":
        if not d.arg:
            errors.append(f"{where} needs a title argument, e.g. {{nma-video}} Video 1: Intro")
        if not any(d.options.get(name) for name, _ in VIDEO_SOURCES):
            errors.append(f"{where} needs at least one of :youtube:, :bilibili:, :osf:")
    elif not d.arg:
        errors.append(f"{where} needs an OSF id argument, e.g. {{nma-slides}} snv4m")
    return errors
```

**Step 4: Run tests and confirm they pass**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: 14 passed

**Step 5: Commit**

```bash
git add scripts/nma_media.py tests/test_nma_media.py
git commit -m "feat: validate nma media directives"
```

---

### Task 4: Code-cell source generation

**Files:**
- Modify: `scripts/nma_media.py`
- Modify: `tests/test_nma_media.py`

**Step 1: Write failing tests** (append; import `video_cell_source`, `slides_cell_source`)

```python
from nma_media import slides_cell_source, video_cell_source


def test_video_cell_source():
    [d] = find_directives(VIDEO_MD)
    src = video_cell_source(d)
    assert src.startswith("# @title Video 1: Linear Dynamical Systems\n")
    assert "video_ids = [('Youtube', '87z6OR7-DBI'), ('Bilibili', 'BV1up4y1S7wj')]" in src
    assert "tabs = widgets.Tab()" in src
    compile(src, "<cell>", "exec")


def test_video_sources_use_fixed_order():
    [d] = find_directives(":::{nma-video} T\n:osf: o1\n:youtube: y1\n:::\n")
    assert "video_ids = [('Youtube', 'y1'), ('Osf', 'o1')]" in video_cell_source(d)


def test_slides_cell_source_default_title():
    [d] = find_directives(":::{nma-slides} snv4m\n:::\n")
    src = slides_cell_source(d)
    assert src.startswith("# @title Tutorial slides\n")
    assert 'link_id = "snv4m"' in src
    compile(src, "<cell>", "exec")


def test_slides_cell_source_custom_title():
    [d] = find_directives(":::{nma-slides} snv4m\n:title: Day 3 slides\n:::\n")
    assert slides_cell_source(d).startswith("# @title Day 3 slides\n")
```

**Step 2: Run them and confirm they fail**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: FAIL with an ImportError

**Step 3: Implement** (append to `scripts/nma_media.py`; add `from string import Template` to the imports)

The template reproduces the current NMA video cell exactly
(`tutorials/W2D1_Examples/W2D1_Tutorial1.md:271-318`). It uses
`string.Template` (`$name`) so the f-string braces in the cell don't need
escaping.

```python
VIDEO_TEMPLATE = Template('''\
# @title $title
from ipywidgets import widgets
from IPython.display import YouTubeVideo
from IPython.display import IFrame
from IPython.display import display


class PlayVideo(IFrame):
  def __init__(self, id, source, page=1, width=400, height=300, **kwargs):
    self.id = id
    if source == 'Bilibili':
      src = f'https://player.bilibili.com/player.html?bvid={id}&page={page}'
    elif source == 'Osf':
      src = f'https://mfr.ca-1.osf.io/render?url=https://osf.io/download/{id}/?direct%26mode=render'
    super(PlayVideo, self).__init__(src, width, height, **kwargs)


def display_videos(video_ids, W=400, H=300, fs=1):
  tab_contents = []
  for i, video_id in enumerate(video_ids):
    out = widgets.Output()
    with out:
      if video_ids[i][0] == 'Youtube':
        video = YouTubeVideo(id=video_ids[i][1], width=W,
                             height=H, fs=fs, rel=0)
        print(f'Video available at https://youtube.com/watch?v={video.id}')
      else:
        video = PlayVideo(id=video_ids[i][1], source=video_ids[i][0], width=W,
                          height=H, fs=fs, autoplay=False)
        if video_ids[i][0] == 'Bilibili':
          print(f'Video available at https://www.bilibili.com/video/{video.id}')
        elif video_ids[i][0] == 'Osf':
          print(f'Video available at https://osf.io/{video.id}')
      display(video)
    tab_contents.append(out)
  return tab_contents


video_ids = $video_ids
tab_contents = display_videos(video_ids, W=854, H=480)
tabs = widgets.Tab()
tabs.children = tab_contents
for i in range(len(tab_contents)):
  tabs.set_title(i, video_ids[i][0])
display(tabs)''')

SLIDES_TEMPLATE = Template('''\
# @title $title
from IPython.display import IFrame
link_id = "$link_id"
print(f"If you want to download the slides: https://osf.io/download/{link_id}/")
IFrame(src=f"https://mfr.ca-1.osf.io/render?url=https://osf.io/{link_id}/?direct%26mode=render%26action=download%26mode=render", width=854, height=480)''')


def video_cell_source(d: MediaDirective) -> str:
    video_ids = [(label, d.options[name]) for name, label in VIDEO_SOURCES if d.options.get(name)]
    return VIDEO_TEMPLATE.substitute(title=d.arg, video_ids=repr(video_ids))


def slides_cell_source(d: MediaDirective) -> str:
    title = d.options.get("title") or DEFAULT_SLIDES_TITLE
    return SLIDES_TEMPLATE.substitute(title=title, link_id=d.arg)
```

**Step 4: Run tests and confirm they pass**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: 18 passed

**Step 5: Commit**

```bash
git add scripts/nma_media.py tests/test_nma_media.py
git commit -m "feat: generate NMA video/slides code cells"
```

---

### Task 5: Notebook expansion (`expand_notebook`)

**Files:**
- Modify: `scripts/nma_media.py`
- Modify: `tests/test_nma_media.py`

**Step 1: Write failing tests** (append; import `expand_notebook`)

```python
from nma_media import expand_notebook

CELL_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _md_cell(text, cell_id="abc123"):
    return {"cell_type": "markdown", "id": cell_id, "metadata": {},
            "source": text.splitlines(keepends=True)}


def test_expand_splits_markdown_cell():
    nb = {"cells": [_md_cell(VIDEO_MD)]}
    assert expand_notebook(nb) == 1
    cells = nb["cells"]
    assert [c["cell_type"] for c in cells] == ["markdown", "code", "markdown"]
    assert "".join(cells[0]["source"]) == "Intro text"
    assert "".join(cells[2]["source"]) == "Outro text"
    code = cells[1]
    assert code["metadata"] == {"cellView": "form", "tags": ["hide-input"]}
    assert code["outputs"] == [] and code["execution_count"] is None
    assert "".join(code["source"]).startswith("# @title Video 1")
    ids = [c["id"] for c in cells]
    assert len(set(ids)) == 3 and all(CELL_ID_RE.match(i) for i in ids)


def test_expand_drops_empty_markdown_fragments():
    nb = {"cells": [_md_cell(":::{nma-slides} snv4m\n:::\n")]}
    expand_notebook(nb)
    assert [c["cell_type"] for c in nb["cells"]] == ["code"]


def test_expand_handles_two_directives_in_one_cell():
    text = ":::{nma-slides} s1\n:::\n\nmiddle\n\n:::{nma-video} V\n:youtube: y\n:::\n"
    nb = {"cells": [_md_cell(text)]}
    assert expand_notebook(nb) == 2
    assert [c["cell_type"] for c in nb["cells"]] == ["code", "markdown", "code"]


def test_expand_leaves_other_cells_alone_and_is_idempotent():
    code = {"cell_type": "code", "id": "c1", "metadata": {}, "outputs": [],
            "execution_count": None, "source": ["x = 1"]}
    plain = _md_cell("just text", "m1")
    nb = {"cells": [code, plain]}
    assert expand_notebook(nb) == 0
    assert nb["cells"] == [code, plain]
```

**Step 2: Run them and confirm they fail**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: FAIL with an ImportError

**Step 3: Implement** (append to `scripts/nma_media.py`)

```python
def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def make_code_cell(d: MediaDirective, cell_id: str) -> dict:
    source = video_cell_source(d) if d.kind == "nma-video" else slides_cell_source(d)
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {"cellView": "form", "tags": ["hide-input"]},
        "outputs": [],
        "source": _lines(source),
    }


def _markdown_fragment(lines: list[str], cell_id: str) -> list[dict]:
    text = "".join(lines).strip("\n")
    if not text.strip():
        return []
    return [{"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": _lines(text)}]


def expand_markdown_cell(cell: dict) -> list[dict]:
    """Split a markdown cell around its media directives. Returns replacement cells."""
    source = cell["source"]
    text = "".join(source) if isinstance(source, list) else source
    directives = find_directives(text)
    if not directives:
        return [cell]

    lines = text.splitlines(keepends=True)
    base = cell.get("id", "cell")[:50]
    out, cursor = [], 0
    for n, d in enumerate(directives):
        out += _markdown_fragment(lines[cursor:d.start], f"{base}-md{n}")
        out.append(make_code_cell(d, f"{base}-{d.kind}{n}"))
        cursor = d.end + 1
    out += _markdown_fragment(lines[cursor:], f"{base}-md{len(directives)}")
    return out


def expand_notebook(nb: dict) -> int:
    """Replace media directives in markdown cells with code cells, in place.

    Returns the number of directives expanded. Assumes validate_directive
    passed, so every directive is closed.
    """
    new_cells, count = [], 0
    for cell in nb["cells"]:
        if cell.get("cell_type") != "markdown":
            new_cells.append(cell)
            continue
        expanded = expand_markdown_cell(cell)
        count += sum(1 for c in expanded if c["cell_type"] == "code")
        new_cells += expanded
    nb["cells"] = new_cells
    return count
```

**Step 4: Run tests and confirm they pass**

Run: `uv run pytest tests/test_nma_media.py -v`
Expected: 22 passed

**Step 5: Commit**

```bash
git add scripts/nma_media.py tests/test_nma_media.py
git commit -m "feat: expand media directives into notebook code cells"
```

---

### Task 6: Wire into `convert_to_notebooks.py`

**Files:**
- Modify: `scripts/convert_to_notebooks.py`

**Step 1: Import** (after `import yaml`, line 37):

```python
from nma_media import expand_notebook, find_directives, validate_directive
```

**Step 2: Validation.** In `validate_content()` (line 122 loop), add after the
kernelspec check, inside the same `for path in ...rglob("*.md")` loop:

```python
        text = path.read_text(encoding="utf-8")
        for directive in find_directives(text):
            for problem in validate_directive(directive):
                errors.append(f"{path}: {problem}")
```

**Step 3: Expansion step.** Add this function after `convert_md_to_notebook`:

```python
def expand_media(notebook_path: Path, dry_run: bool) -> None:
    """Replace {nma-video}/{nma-slides} directives with NMA code cells."""
    if dry_run:
        return
    with notebook_path.open(encoding="utf-8") as fh:
        nb = json.load(fh)
    count = expand_notebook(nb)
    if count:
        print(f"  Expanded {count} video/slides directive(s): {notebook_path}")
        with notebook_path.open("w", encoding="utf-8") as fh:
            json.dump(nb, fh, indent=1, ensure_ascii=False)
```

In `process_tutorials`, call it between conversion and badge injection:

```python
            convert_md_to_notebook(source_file, out_path, dry_run)
            expand_media(out_path, dry_run)
            inject_badges(out_path, github_repo, dry_run)
```

**Step 4: Update the module docstring.** Add step "2. Replace
{nma-video}/{nma-slides} directives with NMA code cells (scripts/nma_media.py)"
to the default-mode list and renumber. Add "Media directives must be valid"
to the validation list.

**Step 5: Check that validation fails on a bad directive**

```bash
printf ':::{nma-video} Bad\n:::\n' > tutorials/W2D1_Examples/_tmp_bad.md
uv run python scripts/convert_to_notebooks.py --dry-run; echo "exit=$?"
rm tutorials/W2D1_Examples/_tmp_bad.md
```
Expected: `_tmp_bad.md: line 1: {nma-video} needs at least one of ...` and `exit=1`

**Step 6: Check that the current tree still passes**

Run: `uv run python scripts/convert_to_notebooks.py && uv run pytest -q`
Expected: `Done. Processed N file(s).` and all tests pass. No directives
exist yet, so there are no "Expanded" lines.

**Step 7: Commit**

```bash
git add scripts/convert_to_notebooks.py
git commit -m "feat: validate and expand media directives during notebook generation"
```

---

### Task 7: MyST plugin for site rendering

**Files:**
- Create: `plugins/nma.mjs`
- Modify: `myst.yml` (under `project:`, after `jupyter:`)

**Step 1: Create `plugins/nma.mjs`**

AST shapes were checked against mystmd 1.11 (`myst.cjs`):
`{type:'tabSet', children:[{type:'tabItem', title, children}]}` and
`{type:'iframe', src, width, title}`. Errors use `vfile.message` + `fatal`,
which is how `fileError` in myst-common works, so there are no imports.

```javascript
// Renders {nma-video} and {nma-slides} as static embeds on the website.
// scripts/nma_media.py builds the matching notebook code cells.
// Keep the URL templates in both files in sync.

const VIDEO_SOURCES = [
  {
    option: 'youtube',
    label: 'YouTube',
    embed: (id) => `https://www.youtube.com/embed/${id}?rel=0`,
    page: (id) => `https://youtube.com/watch?v=${id}`,
  },
  {
    option: 'bilibili',
    label: 'Bilibili',
    embed: (id) => `https://player.bilibili.com/player.html?bvid=${id}&page=1&autoplay=0`,
    page: (id) => `https://www.bilibili.com/video/${id}`,
  },
  {
    option: 'osf',
    label: 'OSF',
    embed: (id) => `https://mfr.ca-1.osf.io/render?url=https://osf.io/download/${id}/?direct%26mode=render`,
    page: (id) => `https://osf.io/${id}`,
  },
];

const text = (value) => ({ type: 'text', value });
const link = (url, label) => ({ type: 'link', url, children: [text(label ?? url)] });
const iframe = (src, title) => ({ type: 'iframe', src, width: '100%', title });
const heading = (title) => ({ type: 'paragraph', children: [{ type: 'strong', children: [text(title)] }] });

function fail(vfile, node, message) {
  const msg = vfile.message(message, node, 'nma-plugin');
  msg.fatal = true;
  return [];
}

const nmaVideo = {
  name: 'nma-video',
  doc: 'Lecture video with one tab per host (YouTube, Bilibili, OSF).',
  arg: { type: String, required: true, doc: 'Video title, e.g. "Video 1: Intro".' },
  options: {
    youtube: { type: String, doc: 'YouTube video id.' },
    bilibili: { type: String, doc: 'Bilibili BV id.' },
    osf: { type: String, doc: 'OSF file id.' },
  },
  run(data, vfile) {
    const sources = VIDEO_SOURCES
      .filter((s) => data.options?.[s.option])
      .map((s) => ({ ...s, id: data.options[s.option] }));
    if (sources.length === 0) {
      return fail(vfile, data.node, 'nma-video needs at least one of :youtube:, :bilibili:, :osf:');
    }
    const player =
      sources.length === 1
        ? iframe(sources[0].embed(sources[0].id), data.arg)
        : {
            type: 'tabSet',
            children: sources.map((s) => ({
              type: 'tabItem',
              title: s.label,
              children: [iframe(s.embed(s.id), `${data.arg} (${s.label})`)],
            })),
          };
    const links = sources.map((s) => ({
      type: 'paragraph',
      children: [text('Video available at '), link(s.page(s.id))],
    }));
    return [{ type: 'div', class: 'nma-video', children: [heading(data.arg), player, ...links] }];
  },
};

const nmaSlides = {
  name: 'nma-slides',
  doc: 'Embedded OSF slide deck with a download link.',
  arg: { type: String, required: true, doc: 'OSF file id, e.g. snv4m.' },
  options: { title: { type: String, doc: 'Heading shown above the slides.' } },
  run(data) {
    const id = data.arg;
    const title = data.options?.title ?? 'Tutorial slides';
    const src = `https://mfr.ca-1.osf.io/render?url=https://osf.io/${id}/?direct%26mode=render%26action=download%26mode=render`;
    return [
      {
        type: 'div',
        class: 'nma-slides',
        children: [
          heading(title),
          iframe(src, title),
          { type: 'paragraph', children: [link(`https://osf.io/download/${id}/`, 'Download the slides')] },
        ],
      },
    ];
  },
};

export default { name: 'Neuromatch media', directives: [nmaVideo, nmaSlides] };
```

**Step 2: Register it in `myst.yml`** (inside `project:`, after the `jupyter:` block):

```yaml
  plugins:
    - plugins/nma.mjs
```

**Step 3: Validate the YAML and check that the plugin loads**

```bash
python3 -c "import yaml; yaml.safe_load(open('myst.yml'))"
export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh" && nvm use 22
uv run myst build --html 2>&1 | tee /tmp/opencode/myst-build.log | grep -i "nma\|⛔"
```
Expected: a line like `🔌 Neuromatch media (plugins/nma.mjs) loaded: 2 directives`,
and no `⛔`.

**Step 4: Commit**

```bash
git add plugins/nma.mjs myst.yml
git commit -m "feat: add MyST plugin rendering nma-video/nma-slides statically"
```

---

### Task 8: Migrate the real example

**Files:**
- Modify: `tutorials/W2D1_Examples/W2D1_Tutorial1.md`

Work **bottom-up** so the earlier line numbers stay valid.

**Step 1:** Replace the Video 3 code cell (lines 664-711, from
```` ```{code-cell} python ```` through the closing ```` ``` ````) with:

```markdown
:::{nma-video} Video 3: Multi-Dimensional Dynamics
:youtube: c_GdNS3YH_M
:bilibili: BV1pf4y1R7uy
:::
```

**Step 2:** Replace the Video 2 cell (lines 546-593) with:

```markdown
:::{nma-video} Video 2: Oscillatory Solutions
:youtube: vPYQPI4nKT8
:bilibili: BV1gZ4y1u7PK
:::
```

**Step 3:** Replace the Video 1 cell (lines 271-318) with:

```markdown
:::{nma-video} Video 1: Linear Dynamical Systems
:youtube: 87z6OR7-DBI
:bilibili: BV1up4y1S7wj
:::
```

**Step 4:** Replace the slides cell (lines 54-62) with:

```markdown
:::{nma-slides} snv4m
:::
```

Leave the "Submit your feedback" cells exactly as they are.

**Step 5: Check that no old video or slides code remains**

Run: `grep -n "PlayVideo\|display_videos\|link_id" tutorials/W2D1_Examples/W2D1_Tutorial1.md`
Expected: no output

**Step 6: Check notebook expansion end to end**

```bash
uv run python scripts/convert_to_notebooks.py | grep Expanded
uv run python - <<'EOF'
import json
nb = json.load(open("notebooks/W2D1_Examples/W2D1_Tutorial1.ipynb"))
src = ["".join(c["source"]) for c in nb["cells"]]
assert not any("{nma-" in s for s in src), "directive text left in notebook"
titles = [s.splitlines()[0] for s, c in zip(src, nb["cells"]) if c["cell_type"] == "code" and s.startswith("# @title")]
print(titles)
EOF
```
Expected: `Expanded 4 video/slides directive(s)`, and the titles list includes
`# @title Tutorial slides`, `# @title Video 1: …`, `Video 2`, `Video 3`.

**Step 7: Check the site build end to end**

```bash
uv run myst build --html 2>&1 | grep "⛔" ; echo "---"
grep -rl "youtube.com/embed/87z6OR7-DBI" _build/html | head -3
grep -rl "player.bilibili.com/player.html?bvid=BV1up4y1S7wj" _build/html | head -3
grep -rl "osf.io/download/snv4m" _build/html | head -3
```
Expected: nothing before `---`, and each grep finds at least one file.

**Step 8: Look at it in the browser**

Run `uv run myst start` and open the W2D1 Tutorial 1 page. Check that the
slides iframe is visible near the top, and that each video shows YouTube and
Bilibili tabs with players, all without pressing the JupyterLite power button.

**Step 9: Commit**

```bash
git add tutorials/W2D1_Examples/W2D1_Tutorial1.md
git commit -m "content: use nma-video/nma-slides directives in W2D1 example"
```

---

### Task 9: CI path triggers and test step

**Files:**
- Modify: `.github/workflows/publish-book.yml` (`on.push.paths`)
- Modify: `.github/workflows/generate-notebooks.yml` (`on.push.paths`, steps)

**Step 1:** In `publish-book.yml`, add `- "plugins/**"` to `on.push.paths`.

**Step 2:** In `generate-notebooks.yml`, replace
`- "scripts/convert_to_notebooks.py"` with `- "scripts/**"`, and add
`- "tests/**"`.

**Step 3:** In `generate-notebooks.yml`, add this step before "Convert
tutorials to notebooks":

```yaml
      - name: Test notebook conversion helpers
        run: uv run pytest -q tests
```

(This step is a small addition to the design. Without it, the tests never
run in CI.)

**Step 4: Validate the YAML**

```bash
python3 -c "import yaml; [yaml.safe_load(open(f'.github/workflows/{f}')) for f in ['publish-book.yml','generate-notebooks.yml']]"
```
Expected: no output

**Step 5: Commit**

```bash
git add .github/workflows/publish-book.yml .github/workflows/generate-notebooks.yml
git commit -m "ci: trigger on plugin/script changes and run conversion tests"
```

---

### Task 10: Meta-template docs, new tutorial page

**Files:**
- Create: `tutorials/W1D2_InteractiveContent/W1D2_Tutorial4.md`
- Modify: `myst.yml` (TOC: after `W1D2_Tutorial3.md`)
- Modify: `tutorials/W1D2_InteractiveContent/chapter_intro.md` (add an
  objective and a schedule row)

**Step 1: Create the page.** It is static (no `kernelspec`) and has no code
cells.

`````markdown
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
| Website | `plugins/nma.mjs` (registered in `myst.yml` → `project.plugins`) | Turns directives into iframes and tabs during `myst build` |
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
`````

**Step 2: TOC.** In `myst.yml`, after
`- file: tutorials/W1D2_InteractiveContent/W1D2_Tutorial3.md`, add:

```yaml
        - file: tutorials/W1D2_InteractiveContent/W1D2_Tutorial4.md
```

**Step 3: chapter_intro.** Add the objective
`- Embed lecture videos and slides that render without a kernel`, and add
`| Tutorial 4 | Videos and slides | 15 min |` before the Bonus row.

**Step 4: Check**

```bash
python3 -c "import yaml; yaml.safe_load(open('myst.yml'))"
uv run python scripts/convert_to_notebooks.py --dry-run
uv run myst build --html 2>&1 | grep "⛔"; echo "exit-grep=$?"
```
Expected: the dry run passes, which shows the examples inside the
````` ````markdown ````` fences are ignored and the live ones are valid.
`exit-grep=1` means no `⛔` lines.

**Step 5: Commit**

```bash
git add tutorials/W1D2_InteractiveContent/ myst.yml
git commit -m "docs: add Videos and Slides tutorial to the meta-template"
```

---

### Task 11: AGENTS.md and the CI tutorial

**Files:**
- Modify: `AGENTS.md`
- Modify: `tutorials/W1D3_PublishingAndCI/W1D3_Tutorial1.md`

**Step 1: AGENTS.md edits**

1. **Architecture tree:** add
   `plugins/nma.mjs  # MyST plugin: {nma-video}/{nma-slides} -> static embeds`,
   `scripts/nma_media.py  # Validates media directives, expands them into notebook cells`,
   and `tests/  # pytest for scripts/`.
2. **Key files:** add a bullet for each of the two new files, and note that
   they share URL templates that must stay in sync.
3. **Key Conventions:** add a new subsection, `### Videos and slides`, with the
   two syntax blocks from Tutorial 4. Explain that they render statically on
   the site and become hidden code cells in notebooks, that they must be at
   the top level with no body, and that they never go in `{code-cell}`s.
4. **Content rules:** add a third bullet, "Media directives must be valid",
   covering missing ids, unknown options and unclosed blocks.
5. **CI pipelines:** generate-notebooks also triggers on `scripts/**` and
   `tests/**` and runs `pytest` first. publish-book also triggers on
   `plugins/**`.
6. **Cell mapping table:** add the rows
   `| Video cell (`# @title Video …`, `video_ids = [...]`) | `{nma-video}` directive |`
   and `| Slides cell (`# @title Tutorial slides`, `link_id = …`) | `{nma-slides}` directive |`.
7. **Checklist for conversion:** after step 4, insert "Replace video and
   slides cells with `{nma-video}`/`{nma-slides}`" and renumber.
8. **Local preview:** add `uv run pytest -q` under the notebook conversion
   commands.

**Step 2: W1D3_Tutorial1.** In the "Workflow 1" list, add a step after
"Converts…": "Replaces `{nma-video}`/`{nma-slides}` directives with NMA video
and slides code cells." Under "Workflow 2", add the sentence: "Videos and
slides need no extra step. The `plugins/nma.mjs` MyST plugin renders them
during `myst build`, and a change under `plugins/` triggers a rebuild."

**Step 3: Check**

Run: `uv run myst build --html 2>&1 | grep "⛔"; echo "exit-grep=$?"`
Expected: `exit-grep=1`

**Step 4: Commit**

```bash
git add AGENTS.md tutorials/W1D3_PublishingAndCI/W1D3_Tutorial1.md
git commit -m "docs: document media directives in AGENTS.md and CI tutorial"
```

---

### Task 12: Final verification

Use @superpowers:verification-before-completion.

```bash
uv run pytest -q
uv run python scripts/convert_to_notebooks.py
uv run python scripts/convert_to_notebooks.py --inject-md-badges && git diff --stat tutorials/ && git checkout -- tutorials/
uv run myst build --html 2>&1 | grep -c "⛔"
git status --short
```
Expected:
- all tests pass
- conversion reports `Expanded 4` for W2D1
- the badge injection diff touches only the frontmatter-adjacent lines, and
  the checkout reverts it
- the `⛔` count is `0`
- `git status` shows a clean tree, with nothing from `notebooks/` or `_build/`
