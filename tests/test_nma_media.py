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
