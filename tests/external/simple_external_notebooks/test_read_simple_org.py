import pytest
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook

import jupytext
from jupytext.cli import jupytext as jupytext_cli
from jupytext.compare import compare_notebooks
from jupytext.pandoc import PandocError


@pytest.mark.requires_pandoc
def test_notebook_to_org_and_back(
    notebook=new_notebook(
        cells=[
            new_markdown_cell("# Hello\n\nThis is a markdown cell."),
            new_code_cell("print('hello')"),
            new_markdown_cell("Another markdown cell."),
        ]
    ),
):
    org = jupytext.writes(notebook, "org")
    assert "#+begin_src" in org.lower() or "#+BEGIN_SRC" in org
    nb2 = jupytext.reads(org, "org")
    compare_notebooks(nb2, notebook, "org")


@pytest.mark.requires_pandoc
def test_org_round_trip_preserves_code():
    notebook = new_notebook(
        cells=[
            new_code_cell("a = 1\nb = 2\na + b"),
        ]
    )
    org = jupytext.writes(notebook, "org")
    nb2 = jupytext.reads(org, "org")
    assert any(
        "a = 1" in cell.source for cell in nb2.cells if cell.cell_type == "code"
    )


@pytest.mark.requires_pandoc
def test_org_kernel_header_arg():
    """Kernel language should appear as a header-args property in the Org output"""
    notebook = new_notebook(
        metadata={"kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"}},
        cells=[
            new_code_cell("x = 1"),
        ],
    )
    org = jupytext.writes(notebook, "org")
    assert "header-args:python" in org


@pytest.mark.requires_pandoc
def test_org_utf8():
    """Org format should handle unicode correctly"""
    notebook = new_notebook(
        cells=[
            new_markdown_cell("Greek letter π and emoji 🎉"),
        ]
    )
    org = jupytext.writes(notebook, "org")
    nb2 = jupytext.reads(org, "org")
    assert any("π" in cell.source for cell in nb2.cells)


@pytest.mark.requires_no_pandoc
def test_meaningful_error_when_pandoc_is_missing(tmpdir):
    nb_file = tmpdir.join("notebook.ipynb")
    jupytext.write(new_notebook(), str(nb_file))

    with pytest.raises(PandocError):
        jupytext_cli([str(nb_file), "--to", "org"])
