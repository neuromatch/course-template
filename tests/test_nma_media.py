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
