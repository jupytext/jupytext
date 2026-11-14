from copy import deepcopy

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook, new_raw_cell

import jupytext
from jupytext.combine import combine_inputs_with_outputs
from jupytext.compare import compare, compare_notebooks


def test_combine():
    nb_source = new_notebook(
        cells=[
            new_markdown_cell("Markdown text"),
            new_code_cell("a=3"),
            new_code_cell("a+1"),
            new_code_cell("a+1"),
            new_markdown_cell("Markdown text"),
            new_code_cell("a+2"),
        ]
    )

    nb_outputs = new_notebook(
        cells=[
            new_markdown_cell("Markdown text"),
            new_code_cell("a=3"),
            new_code_cell("a+1"),
            new_code_cell("a+2"),
            new_markdown_cell("Markdown text"),
        ]
    )

    nb_outputs.cells[2].outputs = ["4"]
    nb_outputs.cells[3].outputs = ["5"]

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs)

    assert nb_source.cells[2].outputs == ["4"]
    assert nb_source.cells[3].outputs == []
    assert nb_source.cells[5].outputs == ["5"]


@pytest.mark.asyncio
async def test_read_text_and_combine_with_outputs(tmpdir, cm):
    tmp_ipynb = "notebook.ipynb"
    tmp_script = "notebook.py"

    with open(str(tmpdir.join(tmp_script)), "w") as fp:
        fp.write(
            """# ---
# jupyter:
#   jupytext_formats: ipynb,py:light
# ---

1+1

2+2

3+3
"""
        )

    with open(str(tmpdir.join(tmp_ipynb)), "w") as fp:
        fp.write(
            """{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "2"
      ]
     },
     "execution_count": 1,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "1+1"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "6"
      ]
     },
     "execution_count": 3,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "3+3"
   ]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 2
}
"""
        )

    # create contents manager
    cm.root_dir = str(tmpdir)

    # load notebook from script
    model = await ensure_async(cm.get(tmp_script))
    nb = model["content"]

    assert nb.cells[0]["source"] == "1+1"
    assert nb.cells[1]["source"] == "2+2"
    assert nb.cells[2]["source"] == "3+3"

    # No output for the second cell, which is not in the ipynb
    assert nb.cells[0]["outputs"]
    assert not nb.cells[1]["outputs"]
    assert nb.cells[2]["outputs"]

    assert len(nb.cells) == 3


def test_combine_stable(ipynb_file):
    nb_org = jupytext.read(ipynb_file)
    nb_source = deepcopy(nb_org)
    nb_outputs = deepcopy(nb_org)

    for cell in nb_source.cells:
        cell.outputs = []

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs)
    compare_notebooks(nb_source, nb_org)


def test_combine_reorder():
    nb_source = new_notebook(
        cells=[
            new_markdown_cell("Markdown text"),
            new_code_cell("1+1"),
            new_code_cell("2+2"),
            new_code_cell("3+3"),
            new_markdown_cell("Markdown text"),
            new_code_cell("4+4"),
        ]
    )

    nb_outputs = new_notebook(
        cells=[
            new_markdown_cell("Markdown text"),
            new_code_cell("2+2"),
            new_code_cell("4+4"),
            new_code_cell("1+1"),
            new_code_cell("3+3"),
            new_markdown_cell("Markdown text"),
        ]
    )

    nb_outputs.cells[1].outputs = ["4"]
    nb_outputs.cells[2].outputs = ["8"]
    nb_outputs.cells[3].outputs = ["2"]
    nb_outputs.cells[4].outputs = ["6"]

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs)

    assert nb_source.cells[1].outputs == ["2"]
    assert nb_source.cells[2].outputs == ["4"]
    assert nb_source.cells[3].outputs == ["6"]
    assert nb_source.cells[5].outputs == ["8"]


def test_combine_split():
    nb_source = new_notebook(cells=[new_code_cell("1+1"), new_code_cell("2+2")])

    nb_outputs = new_notebook(cells=[new_code_cell("1+1\n2+2")])

    nb_outputs.cells[0].outputs = ["4"]

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs)

    assert nb_source.cells[0].outputs == []
    assert nb_source.cells[1].outputs == ["4"]


def test_combine_refactor():
    nb_source = new_notebook(cells=[new_code_cell("a=1"), new_code_cell("a+1"), new_code_cell("a+2")])

    nb_outputs = new_notebook(cells=[new_code_cell("b=1"), new_code_cell("b+1"), new_code_cell("b+2")])

    nb_outputs.cells[1].outputs = ["2"]
    nb_outputs.cells[2].outputs = ["3"]

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs)

    assert nb_source.cells[0].outputs == []
    assert nb_source.cells[1].outputs == ["2"]
    assert nb_source.cells[2].outputs == ["3"]


def test_combine_attachments():
    nb_source = new_notebook(cells=[new_markdown_cell("![image.png](attachment:image.png)")])

    nb_outputs = new_notebook(
        cells=[
            new_markdown_cell(
                "![image.png](attachment:image.png)",
                attachments={"image.png": {"image/png": "SOME_LONG_IMAGE_CODE...=="}},
            )
        ]
    )

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs)
    compare(nb_source, nb_outputs)


@pytest.mark.parametrize("fmt", ["py:percent", "py:light", "md", "md:myst"])
def test_combine_keeps_metadata_of_yaml_header_cell(fmt):
    """The text formats write a leading YAML raw cell as the file header, without its metadata (#1687)"""
    nb = new_notebook(
        cells=[
            new_raw_cell(
                "---\ntitle: Minimal\n---",
                metadata={"raw_mimetype": "text/markdown", "tags": ["remove-cell"]},
            ),
            new_markdown_cell("Some text"),
            new_code_cell("1 + 1"),
        ]
    )

    text = jupytext.writes(nb, fmt)
    nb_source = jupytext.reads(text, fmt)
    assert nb_source.cells[0].metadata == {}

    nb_source = combine_inputs_with_outputs(nb_source, nb, fmt=fmt)

    assert nb_source.cells[0].metadata == {"raw_mimetype": "text/markdown", "tags": ["remove-cell"]}


def test_combine_does_not_restore_metadata_of_other_raw_cells():
    nb_source = new_notebook(cells=[new_raw_cell("---\nnot: a header\n---")])
    nb_outputs = new_notebook(cells=[new_raw_cell("---\nnot: a header\n---", metadata={"tags": ["removed"]})])

    nb_source = combine_inputs_with_outputs(nb_source, nb_outputs, fmt="ipynb")

    assert nb_source.cells[0].metadata == {}
