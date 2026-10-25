import pytest
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook, new_raw_cell

import jupytext
from jupytext.cli import jupytext as jupytext_cli
from jupytext.config import JupytextConfiguration
from jupytext.formats import JupytextFormatError

PERCENT = {"extension": ".py", "format_name": "percent", "notebook_metadata_filter": "-all"}


@pytest.mark.parametrize("enabled", [None, False, True])
def test_markdown_blank_lines_1627(enabled):
    script = """# %% [markdown]
# ## Title

# Para one.

# Para two.

# %%
x = 1
"""
    nb = jupytext.reads(script, "py:percent")
    sources = [cell.source for cell in nb.cells]
    fmt = dict(PERCENT)
    if enabled is not None:
        fmt["markdown_blank_lines"] = enabled

    text = jupytext.writes(nb, fmt)
    expected = script if enabled else script.replace("\n\n# Para", "\n#\n# Para")
    assert text == expected
    assert [cell.source for cell in nb.cells] == sources
    restored = jupytext.reads(text, "py:percent")
    assert [cell.source for cell in restored.cells] == sources
    assert [cell.cell_type for cell in restored.cells] == ["markdown", "code"]


@pytest.mark.parametrize("source", ["\nfirst\n \n\nsecond\n", "\n\n", ""])
def test_markdown_blank_lines_preserve_cell_boundaries(source):
    nb = new_notebook(cells=[new_markdown_cell(source), new_code_cell("x = 1")])
    text = jupytext.writes(nb, {**PERCENT, "markdown_blank_lines": True})
    assert "\n#\n\n# %%\nx = 1" in text
    restored = jupytext.reads(text, "py:percent")
    assert [(cell.cell_type, cell.source) for cell in restored.cells] == [
        ("markdown", source),
        ("code", "x = 1"),
    ]


def test_markdown_blank_lines_leave_quoted_cells_unchanged():
    nb = new_notebook(cells=[new_markdown_cell("\nfirst\n\nsecond")])
    fmt = {**PERCENT, "cell_markers": '"""'}
    expected = jupytext.writes(nb, fmt)
    text = jupytext.writes(nb, {**fmt, "markdown_blank_lines": True})
    assert text == expected
    assert jupytext.reads(text, "py:percent").cells[0].source == nb.cells[0].source


def test_markdown_blank_lines_leave_raw_and_code_cells_unchanged():
    nb = new_notebook(
        cells=[
            new_raw_cell("first\n\nsecond"),
            new_code_cell("x = 1\n\nx += 1"),
            new_code_cell("1\n\n2", metadata={"active": "ipynb"}),
        ]
    )
    assert jupytext.writes(nb, {**PERCENT, "markdown_blank_lines": True}) == jupytext.writes(nb, PERCENT)


@pytest.mark.parametrize("extension, format_name", [(".py", "light"), (".py", "hydrogen"), (".R", "percent")])
def test_markdown_blank_lines_leave_other_formats_unchanged(extension, format_name):
    nb = new_notebook(cells=[new_markdown_cell("first\n\nsecond")])
    fmt = {**PERCENT, "extension": extension, "format_name": format_name}
    assert jupytext.writes(nb, {**fmt, "markdown_blank_lines": True}) == jupytext.writes(nb, fmt)


def test_markdown_blank_lines_config_and_metadata_precedence():
    nb = new_notebook(cells=[new_markdown_cell("first\n\nsecond")])
    expected = "# %% [markdown]\n# first\n\n# second\n"
    commented = expected.replace("\n\n", "\n#\n")
    assert jupytext.writes(nb, PERCENT, config=JupytextConfiguration()) == commented
    config = JupytextConfiguration(markdown_blank_lines=True)
    assert jupytext.writes(nb, PERCENT, config=config) == expected
    nb.metadata["jupytext"] = {"markdown_blank_lines": True}
    assert jupytext.writes(nb, PERCENT) == expected
    config.markdown_blank_lines = False
    assert jupytext.writes(nb, PERCENT, config=config) == commented
    assert jupytext.writes(nb, {**PERCENT, "markdown_blank_lines": True}, config=config) == expected


def test_markdown_blank_lines_metadata_round_trip():
    nb = new_notebook(cells=[new_markdown_cell("first\n\nsecond")])
    fmt = {"extension": ".py", "format_name": "percent", "markdown_blank_lines": True}
    text = jupytext.writes(nb, fmt)
    restored = jupytext.reads(text, "py:percent")
    assert restored.metadata["jupytext"]["markdown_blank_lines"] is True
    assert jupytext.writes(restored, "py:percent") == text


def test_markdown_blank_lines_cli(tmp_path):
    notebook_path = tmp_path / "notebook.ipynb"
    jupytext.write(new_notebook(cells=[new_markdown_cell("first\n\nsecond")]), notebook_path)
    assert (
        jupytext_cli(
            [
                "--to",
                "py:percent",
                "--opt",
                "markdown_blank_lines=true",
                "--opt",
                "notebook_metadata_filter=-all",
                str(notebook_path),
            ]
        )
        == 0
    )
    assert notebook_path.with_suffix(".py").read_text(encoding="utf-8") == "# %% [markdown]\n# first\n\n# second\n"


def test_markdown_blank_lines_requires_boolean_format_option():
    with pytest.raises(JupytextFormatError, match="Format option 'markdown_blank_lines' should be a bool"):
        jupytext.writes(new_notebook(), {**PERCENT, "markdown_blank_lines": "true"})
