"""
Exercise solutions and explanations: {nma-solution} / {nma-explanation}.

Syntax (top level of a page only):

    ```{code-cell} python
    def f(x):
      raise NotImplementedError("Student exercise: ...")
    ```

    ::::{nma-solution}
    ```python
    def f(x):
      return 2 * x
    ```
    ::::

    :::{nma-explanation}
    Markdown text, math allowed.
    :::

An {nma-solution} belongs to the exercise code cell directly above it.

One source becomes:
  - student notebook: "Click for solution/explanation" link cells
  - instructor notebook: the solution as a code cell, the explanation as markdown
  - solution files, written to notebooks/<day>/solutions/ on notebooks-branch
  - a hidden setup cell for the site that runs the reference solution when
    an unfinished exercise is executed, so "Run all" doesn't stop

The website renders the directives with plugins/nma.mjs. The file naming and
URL rules here and in that file must stay in sync.
"""

import re
from dataclasses import dataclass, field

FENCE_RE = re.compile(r"^(`{3,}|~{3,}|:{3,})(.*)$")
DIRECTIVE_RE = re.compile(r"^\{([\w-]+)\}\s*(.*?)\s*$")
OPTION_RE = re.compile(r"^:([A-Za-z][\w-]*):\s*(.*?)\s*$")

SOLUTION = "nma-solution"
EXPLANATION = "nma-explanation"
KINDS = (SOLUTION, EXPLANATION)

# Directives whose body is code, not Markdown, so fences inside them are text.
LITERAL_DIRECTIVES = {"code-cell", "code", "code-block"}

EXERCISE_MARKER = "raise NotImplementedError"
TO_REMOVE_RE = re.compile(r"^\s*#\s*to_remove\b")


@dataclass
class Block:
    kind: str           # "nma-solution", "nma-explanation", "exercise" or "code-cell"
    start: int          # 0-based line of the opening fence
    end: int = -1       # 0-based line of the closing fence; -1 if unclosed
    nested: bool = False
    arg: str = ""
    options: dict = field(default_factory=dict)
    body_lines: list = field(default_factory=list)


def _split_options(lines: list[str]) -> tuple[dict, list[str]]:
    """Split leading `:key: value` lines (or a `---` YAML block) off a body."""
    options, i = {}, 0
    if lines and lines[0].strip() == "---":
        close = next((j for j in range(1, len(lines)) if lines[j].strip() == "---"), None)
        if close is not None:
            return {}, lines[close + 1:]
    while i < len(lines):
        match = OPTION_RE.match(lines[i])
        if not match:
            break
        options[match.group(1)] = match.group(2)
        i += 1
    return options, lines[i:]


def find_blocks(text: str) -> list[Block]:
    """
    Return the solution/explanation directives and the code cells in `text`.

    The scanner keeps a stack of open fences. Fences whose content is code
    (plain ``` blocks, {code-cell}) are opaque. Anything inside them is text,
    so syntax examples on documentation pages are ignored. Directive fences are
    containers, so blocks inside them are found and marked `nested`.
    """
    lines = text.splitlines()
    blocks, stack = [], []   # stack items: [char, length, literal, block|None]

    def close_block(block, end):
        block.end = end
        stop = end if end != -1 else len(lines)
        body = lines[block.start + 1:stop]
        block.options, block.body_lines = _split_options(body)
        if block.kind == "code-cell" and any(EXERCISE_MARKER in l for l in block.body_lines):
            block.kind = "exercise"

    for i, line in enumerate(lines):
        match = FENCE_RE.match(line)
        if not match:
            continue
        marker, info = match.group(1), match.group(2).strip()
        char, length = marker[0], len(marker)
        top = stack[-1] if stack else None

        if top and not info and char == top[0] and length >= top[1]:
            stack.pop()
            if top[3] is not None:
                close_block(top[3], i)
            continue
        if top and top[2]:
            continue  # inside a code fence: just text

        directive = DIRECTIVE_RE.match(info) if char == ":" or info.startswith("{") else None
        name = directive.group(1) if directive else None
        literal = char != ":" and (name is None or name in LITERAL_DIRECTIVES)
        block = None
        if name in KINDS or name == "code-cell":
            block = Block("code-cell" if name == "code-cell" else name, i,
                          nested=bool(stack), arg=directive.group(2))
            blocks.append(block)
        stack.append([char, length, literal, block])

    for item in stack:
        if item[3] is not None:
            close_block(item[3], -1)
    return blocks


def _previous_content_line(lines: list[str], index: int) -> int:
    """Index of the last non-blank line before `index`, or -1."""
    i = index - 1
    while i >= 0 and not lines[i].strip():
        i -= 1
    return i


def _next_content_line(lines: list[str], index: int) -> int:
    """Index of the first non-blank line after `index`, or -1."""
    i = index + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i if i < len(lines) else -1


def solution_code(block: Block) -> str | None:
    """The code inside a solution's single ```python fence, or None if malformed."""
    body = list(block.body_lines)
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if len(body) < 2:
        return None
    opening, closing = FENCE_RE.match(body[0]), FENCE_RE.match(body[-1])
    if not (opening and closing) or opening.group(1)[0] == ":":
        return None
    if opening.group(2).strip() != "python" or closing.group(2).strip():
        return None
    if closing.group(1)[0] != opening.group(1)[0] or len(closing.group(1)) < len(opening.group(1)):
        return None
    code = "\n".join(body[1:-1]).strip("\n")
    return code if code.strip() else None


def explanation_text(block: Block) -> str:
    return "\n".join(block.body_lines).strip("\n")


def validate(text: str) -> list[str]:
    """Return human-readable errors for the page, each prefixed with its line."""
    lines = text.splitlines()
    blocks = find_blocks(text)
    errors = []
    exercise_ends = {b.end: b for b in blocks if b.kind == "exercise" and not b.nested and b.end != -1}
    solution_starts = {b.start for b in blocks if b.kind == SOLUTION and not b.nested}

    for b in blocks:
        where = f"line {b.start + 1}:"
        if b.kind in ("code-cell", "exercise"):
            if any(TO_REMOVE_RE.match(l) for l in b.body_lines):
                errors.append(
                    f"{where} code cell has a `# to_remove` marker. Move the solution into "
                    f"an {{nma-solution}} or the explanation into an {{nma-explanation}} directive"
                )
            if b.kind == "exercise" and not b.nested and b.end != -1:
                if _next_content_line(lines, b.end) not in solution_starts:
                    errors.append(
                        f"{where} exercise code cell (raises NotImplementedError) has no "
                        f"{{nma-solution}} directly after it"
                    )
            continue

        name = f"{{{b.kind}}}"
        if b.nested:
            errors.append(f"{where} {name} must be at the top level of the page, not inside another directive")
            continue
        if b.end == -1:
            errors.append(f"{where} {name} is never closed")
            continue
        if b.arg:
            errors.append(f"{where} {name} takes no argument (got {b.arg!r})")
        for option in sorted(b.options):
            errors.append(f"{where} {name} has unknown option :{option}: (it takes none)")
        if b.kind == SOLUTION:
            if solution_code(b) is None:
                errors.append(f"{where} {name} body must be a single ```python fence with the solution code")
            if _previous_content_line(lines, b.start) not in exercise_ends:
                errors.append(
                    f"{where} {name} must come directly after an exercise code cell "
                    f"(one that raises NotImplementedError)"
                )
        elif not explanation_text(b).strip():
            errors.append(f"{where} {name} is empty")
    return errors
