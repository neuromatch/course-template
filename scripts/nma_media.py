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
from string import Template

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


# (option name, label used in NMA's video_ids), in display order
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
