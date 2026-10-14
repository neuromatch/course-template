from nma_solutions import find_blocks

EXERCISE = '''```{code-cell} python
def f(x):
  raise NotImplementedError("Student exercise: implement f")
  return ...
```'''

SOLUTION = '''::::{nma-solution}
```python
def f(x):
  return 2 * x
```
::::'''

EXPLANATION = ''':::{nma-explanation}
For $a<0$ the solution **decays**.
:::'''

PAGE = f"""# Title

{EXERCISE}

{SOLUTION}

Some prose.

```{{code-cell}} python
:tags: [hide-input]
plot()
```

{EXPLANATION}
"""


def kinds(text):
    return [b.kind for b in find_blocks(text)]


# --- Task 1: scanning -------------------------------------------------------

def test_finds_blocks_in_order():
    assert kinds(PAGE) == ["exercise", "nma-solution", "code-cell", "nma-explanation"]


def test_block_positions_and_body():
    ex, sol, cell, expl = find_blocks(PAGE)
    assert (ex.start, ex.end) == (2, 6)
    assert (sol.start, sol.end) == (8, 13)
    assert sol.body_lines == ["```python", "def f(x):", "  return 2 * x", "```"]
    assert expl.body_lines == ["For $a<0$ the solution **decays**."]
    assert cell.options == {"tags": "[hide-input]"}
    assert cell.body_lines == ["plot()"]
    assert not any(b.nested for b in (ex, sol, cell, expl))


def test_ignores_blocks_inside_literal_example_fence():
    text = f"`````markdown\n{EXERCISE}\n\n{SOLUTION}\n`````\n"
    assert kinds(text) == []


def test_flags_blocks_nested_in_directive():
    text = f":::::{{note}}\n{SOLUTION}\n:::::\n"
    [sol] = find_blocks(text)
    assert sol.kind == "nma-solution" and sol.nested


def test_same_length_colon_nesting_is_detected():
    text = ":::{dropdown} Answer\n:::{nma-explanation}\nText\n:::\n:::\n"
    [expl] = find_blocks(text)
    assert expl.nested
    assert expl.body_lines == ["Text"]


def test_backtick_directive_form():
    text = "````{nma-solution}\n```python\nx = 1\n```\n````\n"
    [sol] = find_blocks(text)
    assert sol.kind == "nma-solution"
    assert sol.body_lines == ["```python", "x = 1", "```"]


def test_unclosed_block_has_end_minus_one():
    [sol] = find_blocks(":::{nma-explanation}\ntext\n")
    assert sol.end == -1


def test_arg_and_options_are_parsed():
    [expl] = find_blocks(":::{nma-explanation} extra\n:label: x\nText\n:::\n")
    assert expl.arg == "extra"
    assert expl.options == {"label": "x"}
    assert expl.body_lines == ["Text"]


def test_code_cell_inside_code_cell_body_is_not_a_block():
    text = "```{code-cell} python\ns = '''\n:::{nma-solution}\n'''\n```\n"
    assert kinds(text) == ["code-cell"]
