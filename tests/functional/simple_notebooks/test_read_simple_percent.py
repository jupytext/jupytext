import os

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_raw_cell,
)

import jupytext
from jupytext.compare import compare, compare_notebooks, notebook_model


def test_read_simple_file(
    script="""# ---
# title: Simple file
# ---

# %% [markdown]
# This is a markdown cell

# %% [md]
# This is also a markdown cell

# %% [raw]
# This is a raw cell

# %%% sub-cell title
# This is a sub-cell

# %%%% sub-sub-cell title
# This is a sub-sub-cell

# %% And now a code cell
1 + 2 + 3 + 4
5
6
# %%magic # this is a commented magic, not a cell

7
""",
):
    nb = jupytext.reads(script, "py:percent")
    compare_notebooks(
        new_notebook(
            cells=[
                new_raw_cell("---\ntitle: Simple file\n---"),
                new_markdown_cell("This is a markdown cell"),
                new_markdown_cell("This is also a markdown cell", metadata={"region_name": "md"}),
                new_raw_cell("This is a raw cell"),
                new_code_cell(
                    "# This is a sub-cell",
                    metadata={"title": "sub-cell title", "cell_depth": 1},
                ),
                new_code_cell(
                    "# This is a sub-sub-cell",
                    metadata={"title": "sub-sub-cell title", "cell_depth": 2},
                ),
                new_code_cell(
                    """1 + 2 + 3 + 4
5
6
%%magic # this is a commented magic, not a cell

7""",
                    metadata={"title": "And now a code cell"},
                ),
            ]
        ),
        nb,
    )

    script2 = jupytext.writes(nb, "py:percent")
    compare(script2, script)


def test_read_cell_with_metadata(
    script="""# %% a code cell with parameters {"tags": ["parameters"]}
a = 3
""",
):
    nb = jupytext.reads(script, "py:percent")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"
    assert nb.cells[0].source == "a = 3"
    assert nb.cells[0].metadata == {
        "title": "a code cell with parameters",
        "tags": ["parameters"],
    }

    script2 = jupytext.writes(nb, "py:percent")
    compare(script2, script)


def test_read_nbconvert_script(
    script="""
# coding: utf-8

# A markdown cell

# In[1]:


import pandas as pd

pd.options.display.max_rows = 6
pd.options.display.max_columns = 20


# Another markdown cell

# In[2]:


1 + 1


# Again, a markdown cell

# In[33]:


2 + 2


# <codecell>


3 + 3
""",
):
    assert jupytext.formats.guess_format(script, ".py")[0] == "percent"
    nb = jupytext.reads(script, ".py")
    assert len(nb.cells) == 5


def test_read_remove_blank_lines(
    script="""# %%
import pandas as pd

# %% Display a data frame
df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]},
                  index=pd.Index(['x0', 'x1'], name='x'))
df

# %% Pandas plot {"tags": ["parameters"]}
df.plot(kind='bar')


# %% sample class
class MyClass:
    pass


# %% a function
def f(x):
    return 42 * x

""",
):
    nb = jupytext.reads(script, "py")
    assert len(nb.cells) == 5
    for i in range(5):
        assert nb.cells[i].cell_type == "code"
        assert not nb.cells[i].source.startswith("\n")
        assert not nb.cells[i].source.endswith("\n")

    script2 = jupytext.writes(nb, "py:percent")
    compare(script2, script)


def test_no_crash_on_square_bracket(
    script="""# %% In [2]
print('Hello')
""",
):
    nb = jupytext.reads(script, "py")
    script2 = jupytext.writes(nb, "py:percent")
    compare(script2, script)


def test_nbconvert_cell(
    script="""# In[2]:
print('Hello')
""",
):
    nb = jupytext.reads(script, "py")
    script2 = jupytext.writes(nb, "py:percent")
    expected = """# %%
print('Hello')
"""
    compare(script2, expected)


def test_nbformat_v3_nbpy_cell(
    script="""# <codecell>
print('Hello')
""",
):
    nb = jupytext.reads(script, "py")
    script2 = jupytext.writes(nb, "py:percent")
    expected = """# %%
print('Hello')
"""
    compare(script2, expected)


def test_multiple_empty_cells():
    nb = new_notebook(
        cells=[new_code_cell(), new_code_cell(), new_code_cell()],
        metadata={"jupytext": {"notebook_metadata_filter": "-all"}},
    )
    text = jupytext.writes(nb, "py:percent")
    expected = """# %%

# %%

# %%
"""
    compare(text, expected)
    nb2 = jupytext.reads(text, "py:percent")
    nb2.metadata = nb.metadata
    compare_notebooks(nb2, nb)


def test_first_cell_markdown_191():
    text = """# %% [markdown]
# Docstring

# %%
from math import pi

# %% [markdown]
# Another markdown cell
"""

    nb = jupytext.reads(text, "py")
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[2].cell_type == "markdown"


def test_multiline_comments_in_markdown_1():
    text = """# %% [markdown]
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
    text = '''# %% [markdown]
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


def test_multiline_comments_format_option():
    text = '''# %% [markdown]
"""
a
long
cell
"""
'''
    nb = new_notebook(
        cells=[new_markdown_cell("a\nlong\ncell")],
        metadata={"jupytext": {"cell_markers": '"""', "notebook_metadata_filter": "-all"}},
    )
    py = jupytext.writes(nb, "py:percent")
    compare(py, text)


def test_multiline_comments_in_raw_cell():
    text = '''# %% [raw]
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
    text = '''# %% [markdown]
"""a
long
cell"""
'''
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "a\nlong\ncell"


def test_multiline_comments_in_markdown_cell_is_robust_to_additional_cell_marker():
    text = '''# %% [markdown]
"""
some text, and a fake cell marker
# %% [raw]
"""
'''
    nb = jupytext.reads(text, "py")
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "some text, and a fake cell marker\n# %% [raw]"
    py = jupytext.writes(nb, "py")
    compare(py, text)


@pytest.mark.asyncio
async def test_cell_markers_option_in_contents_manager(tmpdir, cm):
    tmp_ipynb = tmpdir / "notebook.ipynb"
    tmp_py = tmpdir / "notebook.py"

    cm.root_dir = str(tmpdir)

    nb = new_notebook(
        cells=[new_code_cell("1 + 1"), new_markdown_cell("a\nlong\ncell")],
        metadata={
            "jupytext": {
                "formats": "ipynb,py:percent",
                "notebook_metadata_filter": "-all",
                "cell_markers": "'''",
            }
        },
    )
    await ensure_async(cm.save(model=notebook_model(nb), path="notebook.ipynb"))

    assert os.path.isfile(tmp_ipynb)
    assert os.path.isfile(tmp_py)

    with open(tmp_py) as fp:
        text = fp.read()

    compare(
        text,
        """# %%
1 + 1

# %% [markdown]
'''
a
long
cell
'''
""",
    )

    nb2 = jupytext.read(tmp_py)
    compare_notebooks(nb, nb2)


@pytest.mark.asyncio
async def test_cell_markers_in_config(tmpdir, python_notebook, cm):
    (tmpdir / "jupytext.toml").write('''cell_markers = '"""'\n''')

    cm.root_dir = str(tmpdir)
    nb = python_notebook
    nb.metadata["jupytext"] = {"formats": "ipynb,py:percent"}

    await ensure_async(cm.save(model=notebook_model(nb), path="notebook.ipynb"))

    text = (tmpdir / "notebook.py").read()
    assert (
        '''# %% [markdown]
"""
A short notebook
"""
'''
        in text
    )

    nb2 = jupytext.read(tmpdir / "notebook.py")
    compare_notebooks(nb, nb2)


@pytest.mark.asyncio
async def test_cell_markers_in_contents_manager(tmpdir, cm):
    tmp_ipynb = tmpdir / "notebook.ipynb"
    tmp_py = tmpdir / "notebook.py"

    cm.root_dir = str(tmpdir)
    cm.cell_markers = "'''"

    nb = new_notebook(
        cells=[new_code_cell("1 + 1"), new_markdown_cell("a\nlong\ncell")],
        metadata={
            "jupytext": {
                "formats": "ipynb,py:percent",
                "notebook_metadata_filter": "-all",
            }
        },
    )
    await ensure_async(cm.save(model=notebook_model(nb), path="notebook.ipynb"))

    assert os.path.isfile(tmp_ipynb)
    assert os.path.isfile(tmp_py)

    with open(tmp_py) as fp:
        text = fp.read()

    compare(
        text,
        """# %%
1 + 1

# %% [markdown]
'''
a
long
cell
'''
""",
    )

    nb2 = jupytext.read(tmp_py)
    compare_notebooks(nb, nb2)


@pytest.mark.asyncio
async def test_cell_markers_in_contents_manager_does_not_impact_light_format(tmpdir, cm):
    tmp_ipynb = tmpdir / "notebook.ipynb"
    tmp_py = tmpdir / "notebook.py"

    cm.root_dir = str(tmpdir)
    cm.cell_markers = "'''"

    nb = new_notebook(
        cells=[new_code_cell("1 + 1"), new_markdown_cell("a\nlong\ncell")],
        metadata={
            "jupytext": {
                "formats": "ipynb,py:light",
                "notebook_metadata_filter": "-all",
            }
        },
    )
    with pytest.warns(UserWarning, match="Ignored cell markers"):
        await ensure_async(cm.save(model=notebook_model(nb), path="notebook.ipynb"))

    assert os.path.isfile(tmp_ipynb)
    assert os.path.isfile(tmp_py)

    with open(tmp_py) as fp:
        text = fp.read()

    compare(
        text,
        """1 + 1

# a
# long
# cell
""",
    )

    nb2 = jupytext.read(tmp_py)
    compare_notebooks(nb, nb2)


def test_single_triple_quote_works(
    no_jupytext_version_number,
    text='''# ---
# jupyter:
#   jupytext:
#     cell_markers: '"""'
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %%
print("hello")
''',
    notebook=new_notebook(cells=[new_code_cell('print("hello")')]),
):
    compare_notebooks(jupytext.reads(text, "py"), notebook)


def test_docstring_with_quadruple_quote(
    nb=new_notebook(
        cells=[
            new_code_cell(
                '''def fun_1(df):
  """"
  docstring starting with 4 double quotes and ending with 3
  """
  return df'''
            ),
            new_code_cell(
                '''def fun_2(df):
  """
  docstring
  """
  return df'''
            ),
        ]
    ),
):
    """Reproduces https://github.com/mwouts/jupytext/issues/460"""
    py = jupytext.writes(nb, "py:percent")
    nb2 = jupytext.reads(py, "py")
    compare_notebooks(nb2, nb)


def test_cell_marker_has_same_indentation_as_code(
    text="""# %%
if __name__ == '__main__':
    print(1)

    # %%
    # INDENTED COMMENT
    print(2)
""",
    nb_expected=new_notebook(
        cells=[
            new_code_cell(
                """if __name__ == '__main__':
    print(1)"""
            ),
            new_code_cell(
                """    # INDENTED COMMENT
    print(2)"""
            ),
        ]
    ),
):
    """The cell marker should have the same indentation as the first code line. See issue #562"""
    nb_actual = jupytext.reads(text, fmt="py:percent")
    compare_notebooks(nb_actual, nb_expected)
    text_actual = jupytext.writes(nb_actual, fmt="py:percent")
    compare(text_actual, text)


@pytest.mark.parametrize("space_in_gonb", [False, True])
def test_read_simple_gonb_cell_with_double_percent(
    space_in_gonb,
    go_percent="""// ---
// jupyter:
//   kernelspec:
//     display_name: Go (gonb)
//     language: go
//     name: gonb
// ---

// %%
//gonb:%%
fmt.Printf("Hello World!")
""",
):
    """The cell marker should have the same indentation as the first code line. See issue #562"""
    if space_in_gonb:
        go_percent = go_percent.replace("//gonb:%%", "// gonb:%%")
    nb = jupytext.reads(go_percent, fmt="go:percent")
    assert len(nb.cells) == 1
    (cell,) = nb.cells
    assert cell.cell_type == "code", cell.cell_type
    assert (
        cell.source
        == """%%
fmt.Printf("Hello World!")"""
    )


def test_write_simple_gonb_cell_with_double_percent(
    no_jupytext_version_number,
    go_percent="""// ---
// jupyter:
//   kernelspec:
//     display_name: Go (gonb)
//     language: go
//     name: gonb
// ---

// %%
//gonb:%%
fmt.Printf("Hello World!")
""",
):
    """The cell marker should have the same indentation as the first code line. See issue #562"""
    nb = jupytext.reads(go_percent, fmt="go:percent")
    go = jupytext.writes(nb, fmt="go:percent")
    compare(go, go_percent)


def test_trailing_whitespace_only_line_is_preserved():
    """A trailing line made of spaces belongs to the cell (#1599)"""
    source = 'print("hello")\n# the following line has 4 white spaces.\n    '
    nb = jupytext.reads("# %%\n" + source + "\n", fmt="py:percent")
    assert len(nb.cells) == 1
    compare(nb.cells[0].source, source)
