import pytest

from jupytext.languages import comment_lines


@pytest.mark.parametrize(
    "prefix,suffix,no_empty_comment,expected",
    [
        ("#", "", False, ["# First", "#", "# Second"]),
        ("/", "", False, ["/ First", "/", "/ Second"]),
        ("/", "", True, ["/ First", "", "/ Second"]),
        ("(*", "*)", False, ["(* First *)", "(* *)", "(* Second *)"]),
        ("(*", "*)", True, ["(* First *)", "(* *)", "(* Second *)"]),
        ("", "", True, ["First", "", "Second"]),
    ],
)
def test_comment_lines(prefix, suffix, no_empty_comment, expected):
    assert comment_lines(["First", "", "Second"], prefix, suffix, no_empty_comment) == expected


@pytest.mark.parametrize("no_empty_comment", [False, True])
def test_comment_lines_empty_input(no_empty_comment):
    assert comment_lines([], "/", no_empty_comment=no_empty_comment) == []


def test_comment_lines_without_prefix_preserves_input():
    lines = ["First", "", "Second"]
    assert comment_lines(lines, "", no_empty_comment=True) is lines
