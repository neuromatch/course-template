import json
from pathlib import Path

import pytest

import nma_scrolly
from nma_scrolly import cell_key, find_markers, is_scrolly, parse_params, validate

FIXTURES = Path(__file__).parent / "fixtures" / "scrolly"

FRONT = "---\ntitle: T\nlayout: scrolly\nkernelspec:\n  name: python3\n  display_name: Python 3\n---\n"
PLAIN_FRONT = "---\ntitle: T\nkernelspec:\n  name: python3\n  display_name: Python 3\n---\n"

PAGE = FRONT + """
Intro before the first step.

:::{step} hero
:kicker: neuromatch academy
:::
# Title

:::{step}
:section: One
:kicker: Exercise 1
:::
### Heading

:::{stage}
:style: list
1. one
2. two
:::

```{code-cell} python
a = 1  # @param [1, 2]
print(a)
```

:::{step}
:::
More prose.
"""


# --- fixtures shared with tests/js/scrolly.test.mjs -------------------------

@pytest.mark.parametrize("case", json.loads((FIXTURES / "cell_keys.json").read_text()),
                         ids=lambda c: c["name"])
def test_cell_key_fixture(case):
    assert nma_scrolly.canonical_code(case["code"]) == case["canonical"]
    assert cell_key(case["code"]) == case["key"]


@pytest.mark.parametrize("case", json.loads((FIXTURES / "params.json").read_text()),
                         ids=lambda c: c["name"])
def test_parse_params_fixture(case):
    if "error" in case:
        with pytest.raises(ValueError, match=case["error"]):
            parse_params(case["code"])
    else:
        assert parse_params(case["code"]) == case["params"]


def test_int_values_stay_ints():
    (p,) = parse_params('n = 3  # @param {type:"slider", min:1, max:10}')
    assert all(isinstance(p[k], int) for k in ("value", "min", "max", "step"))


# --- detection ----------------------------------------------------------------

def test_is_scrolly():
    assert is_scrolly(FRONT)
    assert is_scrolly("---\nlayout: 'scrolly'  # comment\n---\n")
    assert not is_scrolly(PLAIN_FRONT)
    assert not is_scrolly("layout: scrolly\n")          # not in frontmatter
    assert not is_scrolly("---\nsite:\n  layout: scrolly\n---\n")  # nested key


def test_find_markers():
    markers = find_markers(PAGE)
    assert [(m.kind, m.arg) for m in markers] == [("step", "hero"), ("step", ""), ("stage", ""), ("step", "")]
    assert markers[0].options == {"kicker": "neuromatch academy"}
    assert markers[2].body_lines == ["1. one", "2. two"]


def test_markers_in_example_fences_are_text():
    text = FRONT + "\n:::{step}\n:::\n\n````markdown\n:::{step} nonsense\n:bad: 1\n:::\n````\n"
    assert [m.kind for m in find_markers(text)] == ["step"]
    assert validate(text) == []


# --- validation ---------------------------------------------------------------

def test_valid_page():
    assert validate(PAGE) == []


def test_non_scrolly_page_without_markers_is_ignored():
    assert validate(PLAIN_FRONT + "\n```{code-cell} python\na = 1  # @param {bad}\n```\n") == []


def test_markers_need_layout_scrolly():
    errors = validate(PLAIN_FRONT + "\n:::{step}\n:::\n")
    assert len(errors) == 1 and "layout: scrolly" in errors[0] and errors[0].startswith("line 8:")


def test_scrolly_page_needs_a_step():
    errors = validate(FRONT + "\nJust prose.\n")
    assert len(errors) == 1 and "no {step}" in errors[0]


def test_step_rules():
    errors = validate(FRONT + "\n:::{step} big\n:color: red\nbody text\n:::\n")
    assert any("hero" in e for e in errors)
    assert any(":color:" in e for e in errors)
    assert any("no body" in e for e in errors)


def test_marker_must_be_top_level():
    errors = validate(FRONT + "\n:::{step}\n:::\n\n::::{note}\n:::{step}\n:::\n::::\n")
    assert len(errors) == 1 and "top level" in errors[0]


def test_unclosed_marker():
    errors = validate(FRONT + "\n:::{step}\n:::\n\n:::{stage}\ntext\n")
    assert any("never closed" in e for e in errors)


def test_stage_rules():
    before = validate(FRONT + "\n:::{stage}\nx\n:::\n\n:::{step}\n:::\n")
    assert any("before the first {step}" in e for e in before)
    twice = validate(FRONT + "\n:::{step}\n:::\n:::{stage}\nx\n:::\n:::{stage}\ny\n:::\n")
    assert len(twice) == 1 and "more than one {stage}" in twice[0]
    opts = validate(FRONT + "\n:::{step}\n:::\n:::{stage} arg\n:style: grid\n:size: 2\nx\n:::\n")
    assert any("takes no argument" in e for e in opts)
    assert any(":style:" in e for e in opts)
    assert any(":size:" in e for e in opts)


def test_bad_param_reported_with_page_line():
    text = FRONT + "\n:::{step}\n:::\n\n```{code-cell} python\nx = 1\na = 1  # @param {type:\"string\"}\n```\n"
    errors = validate(text)
    assert len(errors) == 1
    assert errors[0].startswith("line 14:") and "# @param" in errors[0]


def test_param_errors_inside_exercise_cells_too():
    text = FRONT + "\n:::{step}\n:::\n\n```{code-cell} python\na = 1  # @param [3]\nraise NotImplementedError\n```\n"
    assert any("# @param" in e for e in validate(text))
