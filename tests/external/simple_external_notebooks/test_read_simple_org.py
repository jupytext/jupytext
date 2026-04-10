import pytest
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook

import jupytext
from jupytext.cli import jupytext as jupytext_cli
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
    assert [cell.cell_type for cell in nb2.cells] == [cell.cell_type for cell in notebook.cells]
    assert nb2.cells[0].source == notebook.cells[0].source
    assert nb2.cells[1].source.rstrip("\n") == notebook.cells[1].source
    assert nb2.cells[2].source == notebook.cells[2].source


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
    """Kernel metadata should appear in Org header-args properties."""
    notebook = new_notebook(
        metadata={"kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"}},
        cells=[
            new_code_cell("x = 1"),
        ],
    )
    org = jupytext.writes(notebook, "org")
    assert "#+PROPERTY: header-args:jupyter-python :kernel python3" in org
    assert "#+PROPERTY: header-args:jupyter-python+ :session python3" in org


@pytest.mark.requires_pandoc
def test_org_header_args_are_read_as_kernel_metadata():
    org = """#+PROPERTY: header-args:jupyter-python :kernel python3
#+PROPERTY: header-args:jupyter-python+ :session python3

#+begin_src jupyter-python
print("hello")
#+end_src
"""
    nb = jupytext.reads(org, "org")
    assert nb.metadata["kernelspec"]["name"] == "python3"
    assert nb.metadata["kernelspec"]["language"] == "python"
    assert nb.metadata["org_babel"]["header_args"]["jupyter-python"]["session"] == "python3"
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"


@pytest.mark.requires_pandoc
def test_org_babel_metadata_is_written_to_header_args():
    notebook = new_notebook(
        metadata={
            "kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"},
            "org_babel": {"header_args": {"jupyter-python": {"session": "verification-games-fluxes"}}},
        },
        cells=[new_code_cell("x = 1")],
    )
    org = jupytext.writes(notebook, "org")
    assert "#+PROPERTY: header-args:jupyter-python :kernel python3" in org
    assert "#+PROPERTY: header-args:jupyter-python+ :session verification-games-fluxes" in org


@pytest.mark.requires_pandoc
def test_consecutive_markdown_cells_are_concatenated():
    notebook = new_notebook(
        cells=[
            new_markdown_cell("First markdown cell."),
            new_markdown_cell("Second markdown cell."),
        ]
    )
    nb2 = jupytext.reads(jupytext.writes(notebook, "org"), "org")
    assert len(nb2.cells) == 1
    assert nb2.cells[0].cell_type == "markdown"
    assert nb2.cells[0].source == "First markdown cell.\n\nSecond markdown cell."


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
