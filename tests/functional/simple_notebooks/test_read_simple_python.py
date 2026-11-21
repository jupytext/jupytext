import pytest
from nbformat.v4.nbbase import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_raw_cell,
)

import jupytext
from jupytext.compare import compare, compare_notebooks


def test_read_simple_file(
    pynb="""# ---
# title: Simple file
# ---

# Here we have some text
# And below we have some python code

def f(x):
    return x+1


def h(y):
    return y-1
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 4
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].source == "---\ntitle: Simple file\n---"
    assert nb.cells[1].cell_type == "markdown"
    assert nb.cells[1].source == "Here we have some text\nAnd below we have some python code"
    assert nb.cells[2].cell_type == "code"
    compare(
        nb.cells[2].source,
        """def f(x):
    return x+1""",
    )
    assert nb.cells[3].cell_type == "code"
    compare(
        nb.cells[3].source,
        """def h(y):
    return y-1""",
    )

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_less_simple_file(
    pynb="""# ---
# title: Less simple file
# ---

# Here we have some text
# And below we have some python code

# This is a comment about function f
def f(x):
    return x+1


# And a comment on h
def h(y):
    return y-1
""",
):
    nb = jupytext.reads(pynb, "py")

    assert len(nb.cells) == 4
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].source == "---\ntitle: Less simple file\n---"
    assert nb.cells[1].cell_type == "markdown"
    assert nb.cells[1].source == "Here we have some text\nAnd below we have some python code"
    assert nb.cells[2].cell_type == "code"
    compare(
        nb.cells[2].source,
        "# This is a comment about function f\ndef f(x):\n    return x+1",
    )
    assert nb.cells[3].cell_type == "code"
    compare(nb.cells[3].source, """# And a comment on h\ndef h(y):\n    return y-1""")

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_indented_comment(
    text="""def f():
    return 1

    # f returns 1


def g():
    return 2


# h returns 3
def h():
    return 3
""",
    ref=new_notebook(
        cells=[
            new_code_cell(
                """def f():
    return 1

    # f returns 1"""
            ),
            new_code_cell("def g():\n    return 2"),
            new_code_cell("# h returns 3\ndef h():\n    return 3"),
        ]
    ),
):
    nb = jupytext.reads(text, "py")
    compare_notebooks(nb, ref)
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_non_pep8(
    text="""def f():
    return 1
def g():
    return 2

def h():
    return 3
""",
    ref=new_notebook(
        cells=[
            new_code_cell(
                "def f():\n    return 1\ndef g():\n    return 2",
                metadata={"lines_to_next_cell": 1},
            ),
            new_code_cell("def h():\n    return 3"),
        ]
    ),
):
    nb = jupytext.reads(text, "py")
    compare_notebooks(nb, ref)
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_read_non_pep8_file(
    pynb="""# ---
# title: Non-pep8 file
# ---

# This file is non-pep8 as the function below has
# two consecutive blank lines in its body

def f(x):


    return x+1
""",
):
    nb = jupytext.reads(pynb, "py")

    assert len(nb.cells) == 3
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].source == "---\ntitle: Non-pep8 file\n---"
    assert nb.cells[1].cell_type == "markdown"
    assert nb.cells[1].source == "This file is non-pep8 as the function below has\ntwo consecutive blank lines in its body"
    assert nb.cells[2].cell_type == "code"
    compare(nb.cells[2].source, "def f(x):\n\n\n    return x+1")

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_cell_two_blank_lines(
    pynb="""# ---
# title: cell with two consecutive blank lines
# ---

# +
a = 1


a + 2
""",
):
    nb = jupytext.reads(pynb, "py")

    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].source == "---\ntitle: cell with two consecutive blank lines\n---"
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "a = 1\n\n\na + 2"

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_cell_explicit_start(
    pynb="""
import pandas as pd
# +
def data():
    return pd.DataFrame({'A': [0, 1]})


data()
""",
):
    nb = jupytext.reads(pynb, "py")
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_complex_cells(
    pynb="""import pandas as pd

# +
def data():
    return pd.DataFrame({'A': [0, 1]})


data()

# +
def data2():
    return pd.DataFrame({'B': [0, 1]})


data2()

# +
# Finally we have a cell with only comments
# This cell should remain a code cell and not get converted
# to markdown

# + {"endofcell": "--"}
# This cell has an enumeration in it that should not
# match the endofcell marker!
# - item 1
# - item 2
# -
# --
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 5
    assert nb.cells[0].cell_type == "code"
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[2].cell_type == "code"
    assert nb.cells[3].cell_type == "code"
    assert nb.cells[4].cell_type == "code"
    assert (
        nb.cells[3].source
        == """# Finally we have a cell with only comments
# This cell should remain a code cell and not get converted
# to markdown"""
    )
    assert (
        nb.cells[4].source
        == """# This cell has an enumeration in it that should not
# match the endofcell marker!
# - item 1
# - item 2
# -"""
    )

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_prev_function(
    pynb="""def test_read_cell_explicit_start_end(pynb='''
import pandas as pd
# +
def data():
    return pd.DataFrame({'A': [0, 1]})


data()
'''):
    nb = jupytext.reads(pynb, 'py')
    pynb2 = jupytext.writes(nb, 'py')
    compare(pynb2, pynb)
""",
):
    nb = jupytext.reads(pynb, "py")
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_cell_with_one_blank_line_end(
    pynb="""import pandas

""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 1
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_code_cell_fully_commented(
    pynb="""# +
# This is a code cell that
# only contains comments
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"
    assert (
        nb.cells[0].source
        == """# This is a code cell that
# only contains comments"""
    )
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_file_with_two_blank_line_end(
    pynb="""import pandas


""",
):
    nb = jupytext.reads(pynb, "py")
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_one_blank_lines_after_endofcell(
    pynb="""# +
# This is a code cell with explicit end of cell
1 + 1

2 + 2
# -

# This cell is a cell with implicit start
1 + 1
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "code"
    assert (
        nb.cells[0].source
        == """# This is a code cell with explicit end of cell
1 + 1

2 + 2"""
    )
    assert nb.cells[1].cell_type == "code"
    assert (
        nb.cells[1].source
        == """# This cell is a cell with implicit start
1 + 1"""
    )
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_two_cells_with_explicit_start(
    pynb="""# +
# Cell one
1 + 1

1 + 1

# +
# Cell two
2 + 2

2 + 2
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "code"
    assert (
        nb.cells[0].source
        == """# Cell one
1 + 1

1 + 1"""
    )
    assert nb.cells[1].cell_type == "code"
    assert (
        nb.cells[1].source
        == """# Cell two
2 + 2

2 + 2"""
    )
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_escape_start_pattern(
    pynb="""# The code start pattern '# +' can
# appear in code and markdown cells.

# In markdown cells it is escaped like here:
# # + {"sample_metadata": "value"}

# In code cells like this one, it is also escaped
# # + {"sample_metadata": "value"}
1 + 1
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 3
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[1].cell_type == "markdown"
    assert nb.cells[2].cell_type == "code"
    assert (
        nb.cells[1].source
        == """In markdown cells it is escaped like here:
# + {"sample_metadata": "value"}"""
    )
    assert (
        nb.cells[2].source
        == """# In code cells like this one, it is also escaped
# + {"sample_metadata": "value"}
1 + 1"""
    )
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_dictionary_with_blank_lines_not_broken(
    pynb="""# This is a markdown cell, and below
# we have a long dictionary with blank lines
# inside it

dictionary = {
    'a': 'A',
    'b': 'B',

    # and the end
    'z': 'Z'}
""",
):
    nb = jupytext.reads(pynb, "py")
    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[1].cell_type == "code"
    assert (
        nb.cells[0].source
        == """This is a markdown cell, and below
we have a long dictionary with blank lines
inside it"""
    )
    assert (
        nb.cells[1].source
        == """dictionary = {
    'a': 'A',
    'b': 'B',

    # and the end
    'z': 'Z'}"""
    )
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_isolated_cell_with_magic(
    pynb="""# ---
# title: cell with isolated jupyter magic
# ---

# A magic command included in a markdown
# paragraph is code
#
# %matplotlib inline

# a code block may start with
# a magic command, like this one:

# %matplotlib inline

# or that one

# %matplotlib inline
1 + 1
""",
):
    nb = jupytext.reads(pynb, "py")

    assert len(nb.cells) == 6
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].source == "---\ntitle: cell with isolated jupyter magic\n---"
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[2].cell_type == "markdown"
    assert nb.cells[3].cell_type == "code"
    assert nb.cells[3].source == "%matplotlib inline"
    assert nb.cells[4].cell_type == "markdown"
    assert nb.cells[5].cell_type == "code"
    assert nb.cells[5].source == "%matplotlib inline\n1 + 1"

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_ipython_help_are_commented_297(
    text="""# This is a markdown cell
# that ends with a question: float?

# The next cell is also a markdown cell,
# because it has no code marker:

# float?

# +
# float?

# +
# float??

# +
# Finally a question in a code
# # cell?
""",
    nb=new_notebook(
        cells=[
            new_markdown_cell("This is a markdown cell\nthat ends with a question: float?"),
            new_markdown_cell("The next cell is also a markdown cell,\nbecause it has no code marker:"),
            new_markdown_cell("float?"),
            new_code_cell("float?"),
            new_code_cell("float??"),
            new_code_cell("# Finally a question in a code\n# cell?"),
        ]
    ),
):
    nb2 = jupytext.reads(text, "py")
    compare_notebooks(nb2, nb)

    text2 = jupytext.writes(nb2, "py")
    compare(text2, text)


def test_questions_in_unmarked_cells_are_not_uncommented_297(
    text="""# This cell has no explicit marker
# question?
1 + 2
""",
    nb=new_notebook(
        cells=[
            new_code_cell(
                "# This cell has no explicit marker\n# question?\n1 + 2",
                metadata={"comment_questions": False},
            )
        ]
    ),
):
    nb2 = jupytext.reads(text, "py")
    compare_notebooks(nb2, nb)

    text2 = jupytext.writes(nb2, "py")
    compare(text2, text)


def test_read_multiline_comment(
    pynb="""'''This is a multiline
comment with "quotes", 'single quotes'
# and comments
and line breaks


and it ends here'''


1 + 1
""",
):
    nb = jupytext.reads(pynb, "py")

    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "code"
    assert (
        nb.cells[0].source
        == """'''This is a multiline
comment with "quotes", 'single quotes'
# and comments
and line breaks


and it ends here'''"""
    )
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "1 + 1"

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_no_space_after_code(
    pynb="""# -*- coding: utf-8 -*-
# Markdown cell

def f(x):
    return x+1

# And a new cell, and non ascii contênt
""",
):
    nb = jupytext.reads(pynb, "py")

    assert len(nb.cells) == 3
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "Markdown cell"
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "def f(x):\n    return x+1"
    assert nb.cells[2].cell_type == "markdown"
    assert nb.cells[2].source == "And a new cell, and non ascii contênt"

    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_write_script(
    pynb="""#!/usr/bin/env python
# coding=utf-8
print('Hello world')
""",
):
    nb = jupytext.reads(pynb, "py")
    pynb2 = jupytext.writes(nb, "py")
    compare(pynb2, pynb)


def test_read_write_script_with_metadata_241(
    no_jupytext_version_number,
    pynb="""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

a = 2

a + 1
""",
):
    nb = jupytext.reads(pynb, "py")
    assert "executable" in nb.metadata["jupytext"]
    assert "encoding" in nb.metadata["jupytext"]
    pynb2 = jupytext.writes(nb, "py")

    compare(pynb2, pynb)


def test_notebook_blank_lines(
    script="""# +
# This is a comment
# followed by two variables
a = 3

b = 4
# -

# New cell is a variable
c = 5


# +
# Now we have two functions
def f(x):
    return x + x


def g(x):
    return x + x + x


# -


# A commented block that is two lines away
# from previous cell

# A function again
def h(x):
    return x + 1


# variable
d = 6
""",
):
    notebook = jupytext.reads(script, "py")
    assert len(notebook.cells) >= 6
    for cell in notebook.cells:
        lines = cell.source.splitlines()
        if len(lines) != 1:
            assert lines[0], cell.source
            assert lines[-1], cell.source

    script2 = jupytext.writes(notebook, "py")

    compare(script2, script)


def test_notebook_two_blank_lines_before_next_cell(
    script="""# +
# This is cell with a function

def f(x):
    return 4


# +
# Another cell
c = 5


def g(x):
    return 6


# +
# Final cell

1 + 1
""",
):
    notebook = jupytext.reads(script, "py")
    assert len(notebook.cells) == 3
    for cell in notebook.cells:
        lines = cell.source.splitlines()
        if len(lines) != 1:
            assert lines[0]
            assert lines[-1]

    script2 = jupytext.writes(notebook, "py")

    compare(script2, script)


def test_notebook_one_blank_line_between_cells(
    script="""# +
1 + 1

2 + 2

# +
3 + 3

4 + 4

# +
5 + 5


def g(x):
    return 6


# +
7 + 7


def h(x):
    return 8


# +
def i(x):
    return 9


10 + 10


# +
def j(x):
    return 11


12 + 12
""",
):
    notebook = jupytext.reads(script, "py")
    for cell in notebook.cells:
        lines = cell.source.splitlines()
        assert lines[0]
        assert lines[-1]
        assert not cell.metadata, cell.source

    script2 = jupytext.writes(notebook, "py")

    compare(script2, script)


def test_notebook_with_magic_and_bash_cells(
    script="""# This is a test for issue #181

# %load_ext line_profiler

# !head -4 data/president_heights.csv
""",
):
    notebook = jupytext.reads(script, "py")
    for cell in notebook.cells:
        lines = cell.source.splitlines()
        assert lines[0]
        assert lines[-1]
        assert not cell.metadata, cell.source

    script2 = jupytext.writes(notebook, "py")

    compare(script2, script)


def test_notebook_no_line_to_next_cell(
    nb=new_notebook(
        cells=[
            new_markdown_cell("Markdown cell #1"),
            new_code_cell("%load_ext line_profiler"),
            new_markdown_cell("Markdown cell #2"),
            new_code_cell("%lprun -f ..."),
            new_markdown_cell("Markdown cell #3"),
            new_code_cell("# And a function!\ndef f(x):\n    return 5"),
        ]
    ),
):
    script = jupytext.writes(nb, "py")
    nb2 = jupytext.reads(script, "py")
    nb2.metadata.pop("jupytext")

    compare_notebooks(nb2, nb)


def test_notebook_one_blank_line_before_first_markdown_cell(
    script="""
# This is a markdown cell

1 + 1
""",
):
    notebook = jupytext.reads(script, "py")
    script2 = jupytext.writes(notebook, "py")
    compare(script2, script)

    assert len(notebook.cells) == 3
    for cell in notebook.cells:
        lines = cell.source.splitlines()
        if len(lines):
            assert lines[0]
            assert lines[-1]


def test_read_markdown_cell_with_triple_quote_307(
    script="""# This script test that commented triple quotes '''
# do not impede the correct identification of Markdown cells

# Here is Markdown cell number 2 '''
""",
):
    notebook = jupytext.reads(script, "py")
    assert len(notebook.cells) == 2
    assert notebook.cells[0].cell_type == "markdown"
    assert (
        notebook.cells[0].source
        == """This script test that commented triple quotes '''
do not impede the correct identification of Markdown cells"""
    )
    assert notebook.cells[1].cell_type == "markdown"
    assert notebook.cells[1].source == "Here is Markdown cell number 2 '''"

    script2 = jupytext.writes(notebook, "py")
    compare(script2, script)


def test_read_explicit_markdown_cell_with_triple_quote_307(
    script="""# {{{ [md] {"special": "metadata"}
# some text '''
# }}}

print('hello world')

# {{{ [md] {"special": "metadata"}
# more text '''
# }}}
""",
):
    notebook = jupytext.reads(script, "py")
    assert len(notebook.cells) == 3
    assert notebook.cells[0].cell_type == "markdown"
    assert notebook.cells[0].source == "some text '''"
    assert notebook.cells[1].cell_type == "code"
    assert notebook.cells[1].source == "print('hello world')"
    assert notebook.cells[2].cell_type == "markdown"
    assert notebook.cells[2].source == "more text '''"

    script2 = jupytext.writes(notebook, "py")
    compare(script2, script)


def test_round_trip_markdown_cell_with_magic():
    notebook = new_notebook(
        cells=[new_markdown_cell("IPython has magic commands like\n%quickref")],
        metadata={"jupytext": {"main_language": "python"}},
    )
    text = jupytext.writes(notebook, "py")
    notebook2 = jupytext.reads(text, "py")
    compare_notebooks(notebook2, notebook)


def test_round_trip_python_with_js_cell():
    notebook = new_notebook(
        cells=[
            new_code_cell(
                """import notebook.nbextensions
notebook.nbextensions.install_nbextension('index.js', user=True)"""
            ),
            new_code_cell(
                """%%javascript
Jupyter.utils.load_extensions('jupytext')"""
            ),
        ]
    )
    text = jupytext.writes(notebook, "py")
    notebook2 = jupytext.reads(text, "py")
    compare_notebooks(notebook2, notebook)


def test_round_trip_python_with_js_cell_no_cell_metadata():
    notebook = new_notebook(
        cells=[
            new_code_cell(
                """import notebook.nbextensions
notebook.nbextensions.install_nbextension('index.js', user=True)"""
            ),
            new_code_cell(
                """%%javascript
Jupyter.utils.load_extensions('jupytext')"""
            ),
        ],
        metadata={
            "jupytext": {
                "notebook_metadata_filter": "-all",
                "cell_metadata_filter": "-all",
            }
        },
    )
    text = jupytext.writes(notebook, "py")
    notebook2 = jupytext.reads(text, "py")
    compare_notebooks(notebook2, notebook)


def test_raw_with_metadata(
    text="""# + key="value" active=""
# Raw cell
# # Commented line
""",
    notebook=new_notebook(cells=[new_raw_cell("Raw cell\n# Commented line", metadata={"key": "value"})]),
):
    nb2 = jupytext.reads(text, "py")
    compare_notebooks(nb2, notebook)
    text2 = jupytext.writes(nb2, "py")
    compare(text2, text)


def test_raw_with_metadata_2(
    no_jupytext_version_number,
    text="""# + [raw] key="value"
# Raw cell
# # Commented line
""",
    notebook=new_notebook(cells=[new_raw_cell("Raw cell\n# Commented line", metadata={"key": "value"})]),
):
    nb2 = jupytext.reads(text, "py")
    compare_notebooks(nb2, notebook)


def test_markdown_with_metadata(
    text="""# + [markdown] key="value"
# Markdown cell
""",
    notebook=new_notebook(cells=[new_markdown_cell("Markdown cell", metadata={"key": "value"})]),
):
    nb2 = jupytext.reads(text, "py")
    compare_notebooks(nb2, notebook)
    text2 = jupytext.writes(nb2, "py")
    compare(text2, text)


def test_multiline_comments_in_markdown_1():
    text = """# + [markdown]
'''
a
long
cell
'''
"""
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "a\nlong\ncell"
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_multiline_comments_in_markdown_2():
    text = '''# + [markdown]
"""
a
long
cell
"""
'''
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "a\nlong\ncell"
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_multiline_comments_in_raw_cell():
    text = '''# + active=""
"""
some
text
"""
'''
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].source == "some\ntext"
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_multiline_comments_in_markdown_cell_no_line_return():
    text = '''# + [md]
"""a
long
cell"""
'''
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "a\nlong\ncell"


def test_multiline_comments_in_markdown_cell_is_robust_to_additional_cell_marker():
    text = '''# + [md]
"""
some text, and a fake cell marker
# + [raw]
"""
'''
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "some text, and a fake cell marker\n# + [raw]"
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_active_tag(
    text="""# + tags=["active-py"]
interpreter = 'python'

# + tags=["active-ipynb"]
# interpreter = 'ipython'
""",
    ref=new_notebook(
        cells=[
            new_raw_cell("interpreter = 'python'", metadata={"tags": ["active-py"]}),
            new_code_cell("interpreter = 'ipython'", metadata={"tags": ["active-ipynb"]}),
        ]
    ),
):
    nb = jupytext.reads(text, "py")
    compare_notebooks(nb, ref)
    py = jupytext.writes(nb, "py")
    compare(py, text)


def test_indented_bash_command(
    no_jupytext_version_number,
    nb=new_notebook(
        cells=[
            new_code_cell(
                """try:
    !echo jo
    pass
except:
    pass"""
            )
        ]
    ),
    text="""try:
    # !echo jo
    pass
except:
    pass
""",
):
    """Reproduces https://github.com/mwouts/jupytext/issues/437"""
    py = jupytext.writes(nb, "py:light")
    compare(py, text)
    nb2 = jupytext.reads(py, "py")
    compare_notebooks(nb2, nb)


def test_two_raw_cells_are_preserved(nb=new_notebook(cells=[new_raw_cell("---\nX\n---"), new_raw_cell("Y")])):
    """Test the pattern described at https://github.com/mwouts/jupytext/issues/466"""
    py = jupytext.writes(nb, "py")
    nb2 = jupytext.reads(py, "py")
    compare_notebooks(nb2, nb)


def test_no_metadata_on_multiline_decorator(
    text="""import pytest


@pytest.mark.parametrize(
    "arg",
    [
        'a',
        'b',
        'c'
    ],
)
def test_arg(arg):
    assert isinstance(arg, str)
""",
):
    """Applying black on the code of jupytext 1.4.2 turns some pytest parameters into multi-lines ones, and
    causes a few failures in test_pep8.py:test_no_metadata_when_py_is_pep8"""
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 2
    for cell in nb.cells:
        assert cell.cell_type == "code"
    assert nb.cells[0].source == "import pytest"
    assert nb.cells[0].metadata == {}


@pytest.mark.parametrize(
    "script,cell",
    [
        (
            """if True:
    # # !rm file 1
    # !rm file 2
""",
            """if True:
    # !rm file 1
    !rm file 2""",
        ),
        (
            """# +
if True:
    # help?
    # ?help
    # # ?help
    # # help?
""",
            """if True:
    help?
    ?help
    # ?help
    # help?""",
        ),
    ],
)
def test_indented_magic_commands(script, cell):
    nb = jupytext.reads(script, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"
    compare(nb.cells[0].source, cell)
    assert nb.cells[0].metadata == {}
    compare(jupytext.writes(nb, "py"), script)


@pytest.mark.parametrize("source", ["%%bash\n%pwd", "%%bash\necho 1\n%cat file"])
def test_magic_in_other_language_cell_round_trips_in_light_format(source):
    """Magic-like lines in a cell with another language (%%bash) must not be escaped twice"""
    nb = new_notebook(
        cells=[new_code_cell(source)],
        metadata={"kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"}},
    )
    text = jupytext.writes(nb, "py:light")
    compare_notebooks(jupytext.reads(text, "py:light"), nb, "py:light")


@pytest.mark.parametrize("cell_markers", ["%,-", "+,%pwd"])
def test_magic_in_other_language_cell_keeps_custom_light_cell_boundaries(cell_markers):
    nb = new_notebook(
        cells=[new_code_cell("%%bash\n%pwd\necho done")],
        metadata={
            "kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"},
            "jupytext": {"cell_markers": cell_markers},
        },
    )
    script = jupytext.writes(nb, "py:light")
    restored = jupytext.reads(script, "py:light")
    assert [cell.source for cell in restored.cells] == ["%%bash\n# %pwd\necho done"]
