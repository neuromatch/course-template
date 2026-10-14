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
