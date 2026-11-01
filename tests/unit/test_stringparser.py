import pytest

from jupytext.stringparser import StringParser


def test_long_string(
    text="""'''This is a multiline
comment with "quotes", 'single quotes'
# and comments
and line breaks


and it ends here'''


1 + 1
""",
):
    quoted = []
    sp = StringParser("python")
    for i, line in enumerate(text.splitlines()):
        if sp.is_quoted():
            quoted.append(i)
        sp.read_line(line)

    assert quoted == [1, 2, 3, 4, 5, 6]


def test_single_chars(
    text="""'This is a single line comment'''
'and another one'
# and comments
"and line breaks"


"and it ends here'''"


1 + 1
""",
):
    sp = StringParser("python")
    for line in text.splitlines():
        assert not sp.is_quoted()
        sp.read_line(line)


def test_long_string_with_four_quotes(
    text="""''''This is a multiline
comment that starts with four quotes
'''

1 + 1
""",
):
    quoted = []
    sp = StringParser("python")
    for i, line in enumerate(text.splitlines()):
        if sp.is_quoted():
            quoted.append(i)
        sp.read_line(line)

    assert quoted == [1, 2]


def test_long_string_ends_with_four_quotes(
    text="""'''This is a multiline
comment that ends with four quotes
''''

1 + 1
""",
):
    quoted = []
    sp = StringParser("python")
    for i, line in enumerate(text.splitlines()):
        if sp.is_quoted():
            quoted.append(i)
        sp.read_line(line)

    assert quoted == [1, 2]


@pytest.mark.parametrize("quote", ['"""', "'''"])
def test_multiline_string_with_quotes_and_cell_markers(quote):
    other_quote = "'''" if quote == '"""' else '"""'
    parser = StringParser("python")
    parser.read_line("text = " + quote)
    for line in ["plain text", "'single' and \"double\" quotes", "# %%", "", other_quote]:
        parser.read_line(line)
        assert parser.is_quoted() == quote[0]

    # Closing one string and opening another on the same line must still be parsed.
    parser.read_line(quote + "; other = " + other_quote)
    assert parser.is_quoted() == other_quote[0]
    parser.read_line("more text")
    parser.read_line(other_quote)
    assert not parser.is_quoted()
    parser.read_line("value = 1")
    assert not parser.is_quoted()
