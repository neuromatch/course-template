"""
Scrollytelling pages: `layout: scrolly`, {step} and {stage}.

A scrolly page is an ordinary tutorial page with `layout: scrolly` in its
frontmatter. `{step}` markers split it into steps, and an optional `{stage}`
block holds markdown that only appears on the pinned stage:

    :::{step} hero
    :kicker: neuromatch academy
    :::
    # Title

    :::{step}
    :section: One dimension
    :kicker: Coding Exercise 1
    :::
    Card text. Code cells after the marker go on the stage.

    :::{stage}
    :style: list
    1. An objective
    :::

Interactive demos use Colab form syntax, one assignment per line:

    a = -0.5   # @param {type:"slider", min:-2.5, max:1.5, step:0.25}
    option = 1 # @param [1, 2, 3, 4]

The website side is plugins/scrolly/scrolly.mjs. These rules must match it:
  - is_scrolly()     <-> isScrolly()
  - cell_key()       <-> cellKey()       (fixture tests/fixtures/scrolly/cell_keys.json)
  - parse_params()   <-> parseParams()   (fixture tests/fixtures/scrolly/params.json)
  - render file path _build/scrolly/<relDir>/<stem>.json
"""

import hashlib
import re

from nma_solutions import Block, find_blocks

STEP = "step"
STAGE = "stage"
KINDS = (STEP, STAGE)
STEP_OPTIONS = {"section", "kicker"}
STAGE_OPTIONS = {"style", "class"}
STAGE_STYLES = {"list"}

LAYOUT_RE = re.compile(r"""^layout:\s*(['"]?)scrolly\1\s*(#.*)?$""", re.M)


def _frontmatter_text(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def is_scrolly(text: str) -> bool:
    """True if the frontmatter has a plain top-level `layout: scrolly` line."""
    return bool(LAYOUT_RE.search(_frontmatter_text(text)))


def find_markers(text: str) -> list[Block]:
    """The {step} and {stage} directives in `text`, in order (code cells excluded)."""
    return [b for b in find_blocks(text, KINDS) if b.kind in KINDS]


# --- cell keys ----------------------------------------------------------------

def canonical_code(code: str) -> str:
    """CRLF -> LF, trailing spaces/tabs removed per line, outer blank lines removed."""
    lines = [line.rstrip(" \t") for line in code.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n")


def cell_key(code: str) -> str:
    """Identifies a code cell between the page, the render file and the plugin."""
    return hashlib.sha256(canonical_code(code).encode("utf-8")).hexdigest()[:16]


# --- # @param -----------------------------------------------------------------

PARAM_MARK_RE = re.compile(r"(?:^|\s)#\s*@param\b")
PARAM_LINE_RE = re.compile(r"^([A-Za-z_]\w*)\s*=\s*(.+?)\s*#\s*@param\s*(.*?)\s*$")
NUMBER_RE = re.compile(r"^-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$")
SLIDER_KEYS = {"type", "min", "max", "step"}
CONSTANTS = {"True": True, "False": False, "None": None}


def _number(raw: str):
    raw = raw.strip()
    if not NUMBER_RE.match(raw):
        raise ValueError(f"{raw!r} is not a number")
    return int(raw) if re.match(r"^-?\d+$", raw) else float(raw)


def _split_top(raw: str) -> list[str]:
    """Split on commas that aren't inside quotes."""
    parts, current, quote = [], "", None
    for ch in raw:
        if quote:
            current += ch
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            current += ch
        elif ch == ",":
            parts.append(current)
            current = ""
        else:
            current += ch
    if quote:
        raise ValueError("unclosed quote")
    parts.append(current)
    return [p.strip() for p in parts]


def _literal(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] in "'\"" and raw[-1] == raw[0]:
        return raw[1:-1]
    if raw in CONSTANTS:
        return CONSTANTS[raw]
    return _number(raw)


def _parse_slider(name: str, value_raw: str, spec: str) -> dict:
    fields = {}
    for part in _split_top(spec[1:-1]):
        if not part:
            continue
        key, sep, raw = part.partition(":")
        key = key.strip().strip("'\"")
        if not sep:
            raise ValueError(f"expected key:value, got {part!r}")
        fields[key] = raw.strip()
    kind = fields.get("type", "").strip("'\"")
    if kind != "slider":
        raise ValueError(f'only type:"slider" is supported (got {kind or "no type"})')
    unknown = sorted(set(fields) - SLIDER_KEYS)
    if unknown:
        raise ValueError(f"unknown slider key(s): {', '.join(unknown)}")
    for key in ("min", "max"):
        if key not in fields:
            raise ValueError(f"slider needs {key}")
    return {
        "name": name, "kind": "slider", "value": _number(value_raw),
        "min": _number(fields["min"]), "max": _number(fields["max"]),
        "step": _number(fields["step"]) if "step" in fields else 1,
        "options": None,
    }


def _parse_dropdown(name: str, value_raw: str, spec: str) -> dict:
    inner = spec[1:-1].strip()
    if not inner:
        raise ValueError("dropdown needs at least one option")
    options = [_literal(p) for p in _split_top(inner)]
    value = _literal(value_raw)
    # Same as JS `===`: 1 matches 1.0, but True doesn't match 1.
    if not any(value == o and isinstance(value, bool) == isinstance(o, bool) for o in options):
        raise ValueError(f"default {value_raw} is not one of the options")
    return {"name": name, "kind": "dropdown", "value": value,
            "min": None, "max": None, "step": None, "options": options}


def parse_param_line(line: str) -> dict:
    """Parse one `name = value  # @param ...` line. Raises ValueError."""
    if line[:1].isspace():
        raise ValueError("must not be indented (it has to be a top-level assignment)")
    match = PARAM_LINE_RE.match(line)
    if not match:
        raise ValueError("must be an assignment: `name = value  # @param ...`")
    name, value_raw, spec = match.groups()
    if spec.startswith("{") and spec.endswith("}"):
        return _parse_slider(name, value_raw, spec)
    if spec.startswith("[") and spec.endswith("]"):
        return _parse_dropdown(name, value_raw, spec)
    raise ValueError('expected {type:"slider", min:..., max:..., step:...} or [option, ...]')


def is_param_line(line: str) -> bool:
    return bool(PARAM_MARK_RE.search(line))


def parse_params(code: str) -> list[dict]:
    """
    The `# @param` controls in a code cell, in order. Raises ValueError naming
    the (1-based) line within the cell for the first malformed one.
    """
    params = []
    for number, line in enumerate(code.replace("\r\n", "\n").split("\n"), start=1):
        if not is_param_line(line):
            continue
        try:
            params.append(parse_param_line(line))
        except ValueError as exc:
            raise ValueError(f"line {number}: # @param {exc}") from None
    return params


# --- validation -----------------------------------------------------------------

def _code_offset(lines: list[str], block: Block) -> int:
    """0-based page line of the first code line of a code cell (after options)."""
    stop = block.end if block.end != -1 else len(lines)
    body = lines[block.start + 1:stop]
    return block.start + 1 + len(body) - len(block.body_lines)


def validate(text: str) -> list[str]:
    """Human-readable errors for the page, each prefixed with its line."""
    scrolly = is_scrolly(text)
    lines = text.splitlines()
    blocks = find_blocks(text, KINDS)
    markers = [b for b in blocks if b.kind in KINDS]
    errors = []

    if not scrolly:
        for m in markers:
            errors.append(
                f"line {m.start + 1}: {{{m.kind}}} only works on pages with `layout: scrolly` "
                f"in the frontmatter"
            )
        return errors

    steps_seen = 0
    stage_in_step = False
    for b in markers:
        where = f"line {b.start + 1}:"
        name = f"{{{b.kind}}}"
        if b.nested:
            errors.append(f"{where} {name} must be at the top level of the page, not inside another directive")
            continue
        if b.end == -1:
            errors.append(f"{where} {name} is never closed")
            continue
        if b.kind == STEP:
            steps_seen += 1
            stage_in_step = False
            if b.arg not in ("", "hero"):
                errors.append(f"{where} {name} takes no argument or `hero` (got {b.arg!r})")
            for option in sorted(set(b.options) - STEP_OPTIONS):
                errors.append(f"{where} {name} has unknown option :{option}: (allowed: :section:, :kicker:)")
            if any(line.strip() for line in b.body_lines):
                errors.append(f"{where} {name} has no body. Put the step's content after the closing fence")
        else:
            if steps_seen == 0:
                errors.append(f"{where} {name} comes before the first {{step}}")
            elif stage_in_step:
                errors.append(f"{where} step has more than one {{stage}}")
            stage_in_step = True
            if b.arg:
                errors.append(f"{where} {name} takes no argument (got {b.arg!r})")
            for option in sorted(set(b.options) - STAGE_OPTIONS):
                errors.append(f"{where} {name} has unknown option :{option}: (allowed: :style:, :class:)")
            style = b.options.get("style")
            if style is not None and style not in STAGE_STYLES:
                errors.append(f"{where} {name} :style: must be `list` (got {style!r})")

    if steps_seen == 0 and not any(b.nested for b in markers):
        errors.append("line 1: page has `layout: scrolly` but no {step} markers")

    for b in blocks:
        if b.kind not in ("code-cell", "exercise") or b.nested:
            continue
        offset = _code_offset(lines, b)
        for number, line in enumerate(b.body_lines):
            if not is_param_line(line):
                continue
            try:
                parse_param_line(line)
            except ValueError as exc:
                errors.append(f"line {offset + number + 1}: # @param {exc}")
    return errors
