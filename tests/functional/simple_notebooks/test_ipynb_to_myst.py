import json
import unittest.mock as mock
import warnings
from textwrap import dedent

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_notebook
from tornado.web import HTTPError

import jupytext
from jupytext.cli import jupytext as jupytext_cli
from jupytext.compare import compare
from jupytext.formats import (
    JupytextFormatError,
    get_format_implementation,
    guess_format,
)
from jupytext.myst import (
    CODE_DIRECTIVE,
    MystMetadataParsingError,
    matches_mystnb,
    myst_extensions,
    myst_to_notebook,
)


@pytest.mark.requires_myst
def test_bad_notebook_metadata():
    """Test exception raised if notebook metadata cannot be parsed."""
    with pytest.raises(MystMetadataParsingError):
        myst_to_notebook(
            dedent(
                """\
            ---
            {{a
            ---
            """
            )
        )


@pytest.mark.requires_myst
def test_bad_code_metadata():
    """Test exception raised if cell metadata cannot be parsed."""
    with pytest.raises(MystMetadataParsingError):
        myst_to_notebook(
            dedent(
                """\
            ```{0}
            ---
            {{a
            ---
            ```
            """
            ).format(CODE_DIRECTIVE)
        )


@pytest.mark.requires_myst
def test_bad_markdown_metadata():
    """Test exception raised if markdown metadata cannot be parsed."""
    with pytest.raises(MystMetadataParsingError):
        myst_to_notebook(
            dedent(
                """\
            +++ {{a
            """
            )
        )


@pytest.mark.requires_myst
def test_bad_markdown_metadata2():
    """Test exception raised if markdown metadata is not a dict."""
    with pytest.raises(MystMetadataParsingError):
        myst_to_notebook(
            dedent(
                """\
            +++ [1, 2]
            """
            )
        )


@pytest.mark.requires_myst
def test_matches_mystnb():
    assert matches_mystnb("") is False
    assert matches_mystnb("```{code-cell}\n```") is False
    assert matches_mystnb("---\njupytext: true\n---") is False
    for ext in myst_extensions(no_md=True):
        assert matches_mystnb("", ext=ext) is True
    text = dedent(
        """\
        ---
        {{a
        ---
        ```{code-cell}
        :b: {{c
        ```
        """
    )
    assert matches_mystnb(text) is True
    text = dedent(
        """\
        ---
        jupyter:
            jupytext:
                text_representation:
                    format_name: myst
                    extension: .md
        ---
        """
    )
    assert matches_mystnb(text) is True
    text = dedent(
        """\
        ---
        jupytext:
            text_representation:
                format_name: myst
                extension: .md
        ---
        """
    )
    assert matches_mystnb(text) is True
    text = dedent(
        """\
        ---
        a: 1
        ---
        > ```{code-cell}
          ```
        """
    )
    assert matches_mystnb(text) is True
    assert guess_format(text, ".md") == ("myst", {})


def test_not_installed():
    with mock.patch("jupytext.formats.JUPYTEXT_FORMATS", return_value=[]):
        with pytest.raises(JupytextFormatError):
            get_format_implementation(".myst")


@pytest.mark.requires_myst
def test_add_source_map():
    notebook = myst_to_notebook(
        dedent(
            """\
            ---
            a: 1
            ---
            abc
            +++
            def
            ```{0}
            ---
            b: 2
            ---
            c = 3
            ```
            xyz
            """
        ).format(CODE_DIRECTIVE),
        add_source_map=True,
    )
    assert notebook.metadata.source_map == [3, 5, 7, 12]


PLEASE_INSTALL_MYST = "The MyST Markdown format requires .*"


@pytest.mark.requires_no_myst
def test_meaningfull_error_write_myst_missing(tmpdir):
    nb_file = tmpdir.join("notebook.ipynb")
    jupytext.write(new_notebook(), str(nb_file))

    with pytest.raises(ImportError, match=PLEASE_INSTALL_MYST):
        jupytext_cli([str(nb_file), "--to", "md:myst"])


@pytest.mark.asyncio
@pytest.mark.requires_no_myst
async def test_meaningfull_error_open_myst_missing(tmpdir, cm):
    md_file = tmpdir.join("notebook.md")
    md_file.write(
        """---
jupytext:
  text_representation:
    extension: '.md'
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

1 + 1
"""
    )

    with pytest.raises(ImportError, match=PLEASE_INSTALL_MYST):
        jupytext_cli([str(md_file), "--to", "ipynb"])

    cm.root_dir = str(tmpdir)

    with pytest.raises(HTTPError, match=PLEASE_INSTALL_MYST):
        await ensure_async(cm.get("notebook.md"))


@pytest.mark.asyncio
@pytest.mark.requires_myst
@pytest.mark.parametrize("language_info", ["none", "std", "no_pygments_lexer"])
async def test_myst_representation_same_cli_or_contents_manager(tmpdir, cwd_tmpdir, cm, notebook_with_outputs, language_info):
    """This test gives some information on #759. As of Jupytext 1.11.1, in the MyST Markdown format,
    the code cells have an ipython3 lexer when the notebook "language_info" metadata has "ipython3"
    as the pygments_lexer. This information comes from the kernel and ATM it is not clear how the user
    can choose to include it or not in the md file."""

    nb = notebook_with_outputs
    if language_info != "none":
        nb["metadata"]["language_info"] = {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.7.3",
        }
    if language_info == "no_pygments_lexer":
        del nb["metadata"]["language_info"]["pygments_lexer"]

    # Writing the notebook with the Python API
    text_api = jupytext.writes(nb, fmt="md:myst")

    # How do code cells look like?
    code_cells = {line for line in text_api.splitlines() if line.startswith("```{code-cell")}

    if language_info == "std":
        assert code_cells == {"```{code-cell} ipython3"}
    else:
        assert code_cells == {"```{code-cell}"}

    # We get the same file with the command line jupytext
    tmpdir.mkdir("cli").join("notebook.ipynb").write(json.dumps(nb))
    jupytext_cli(["--to", "md:myst", "cli/notebook.ipynb"])
    text_cli = tmpdir.join("cli").join("notebook.md").read()

    compare(text_cli, text_api)

    # Or with the contents manager
    cm.formats = "ipynb,md:myst"
    cm.root_dir = str(tmpdir.mkdir("contents_manager"))

    await ensure_async(cm.save(model=dict(content=nb, type="notebook"), path="notebook.ipynb"))
    text_cm = tmpdir.join("contents_manager").join("notebook.md").read()

    compare(text_cm, text_api)


@pytest.mark.requires_myst
@pytest.mark.parametrize("magic_first", [True, False])
def test_language_magic_keeps_its_myst_lexer(magic_first):
    cells = [new_code_cell("%%bash -e\necho hello"), new_code_cell("x = 1")]
    if not magic_first:
        cells.reverse()
    notebook = new_notebook(
        cells=cells,
        metadata={"language_info": {"name": "python", "pygments_lexer": "ipython3"}},
    )

    text = jupytext.writes(notebook, fmt="md:myst")

    assert "```{code-cell} bash\n%%bash -e\necho hello" in text
    assert "```{code-cell} ipython3\nx = 1" in text
    with warnings.catch_warnings(record=True) as caught:
        restored = jupytext.reads(text, fmt="md:myst")
    assert not caught
    assert [cell.source for cell in restored.cells] == [cell.source for cell in cells]
    assert restored.metadata.jupytext.default_lexer == "ipython3"


@pytest.mark.requires_myst
def test_myst_different_lexer_without_magic_still_warns():
    text = "```{code-cell} python\nx = 1\n```\n\n```{code-cell} r\nx <- 1\n```\n"
    with pytest.warns(UserWarning, match="All code cells.*same language"):
        myst_to_notebook(text)


@pytest.mark.requires_myst
def test_myst_csharp_directive_keeps_existing_lexer():
    notebook = new_notebook(
        cells=[new_code_cell("#!python\nx = 1"), new_code_cell("var x = 1;")],
        metadata={"language_info": {"name": "csharp", "pygments_lexer": "csharp"}},
    )

    text = jupytext.writes(notebook, fmt="md:myst")

    assert text.count("```{code-cell} csharp\n") == 2
    with warnings.catch_warnings(record=True) as caught:
        restored = jupytext.reads(text, fmt="md:myst")
    assert not caught
    assert [cell.source for cell in restored.cells] == [cell.source for cell in notebook.cells]
