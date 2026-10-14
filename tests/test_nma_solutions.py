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


# --- Task 2: validation -----------------------------------------------------

from nma_solutions import validate


def test_valid_page_has_no_errors():
    assert validate(PAGE) == []


def test_page_without_exercises_is_valid():
    assert validate("# Hi\n\n```{code-cell} python\nx = 1\n```\n") == []


def test_to_remove_marker_is_error():
    text = "```{code-cell} python\n:tags: [hide-input]\n# to_remove solution\nx = 1\n```\n"
    [err] = validate(text)
    assert err.startswith("line 1:") and "# to_remove" in err


def test_to_remove_inside_example_fence_is_fine():
    text = "````markdown\n```{code-cell} python\n# to_remove solution\n```\n````\n"
    assert validate(text) == []


def test_nested_solution_is_error():
    text = f"{EXERCISE}\n\n{SOLUTION}\n\n:::::{{note}}\n{SOLUTION}\n:::::\n"
    errors = validate(text)
    assert len(errors) == 1 and "top level" in errors[0]


def test_unclosed_is_error():
    errors = validate(":::{nma-explanation}\ntext\n")
    assert any("never closed" in e for e in errors)


def test_argument_and_options_are_errors():
    errors = validate(":::{nma-explanation} extra\n:label: x\nText\n:::\n")
    assert any("argument" in e for e in errors)
    assert any(":label:" in e for e in errors)


def test_solution_body_must_be_one_python_fence():
    bad_bodies = [
        "x = 1",                          # no fence
        "```\nx = 1\n```",                # no language
        "```r\nx <- 1\n```",              # wrong language
        "```python\n```",                 # empty code
        "```python\nx = 1\n```\nmore",    # stray text
    ]
    for body in bad_bodies:
        text = f"{EXERCISE}\n\n::::{{nma-solution}}\n{body}\n::::\n"
        errors = validate(text)
        assert any("single ```python fence" in e for e in errors), body


def test_empty_explanation_is_error():
    errors = validate(":::{nma-explanation}\n\n:::\n")
    assert any("empty" in e for e in errors)


def test_solution_without_exercise_is_error():
    errors = validate(f"Prose\n\n{SOLUTION}\n")
    assert any("directly after an exercise" in e for e in errors)


def test_prose_between_exercise_and_solution_is_error():
    errors = validate(f"{EXERCISE}\n\nProse\n\n{SOLUTION}\n")
    assert any("directly after an exercise" in e for e in errors)
    assert any("no {nma-solution}" in e for e in errors)


def test_exercise_without_solution_is_error():
    [err] = validate(f"{EXERCISE}\n\nProse\n")
    assert err.startswith("line 1:") and "no {nma-solution}" in err
