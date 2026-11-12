import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_raw_cell

import jupytext


@pytest.mark.parametrize("fmt", ["q:light", "q:percent", "q:hydrogen"])
@pytest.mark.parametrize(
    "source",
    ["", "\n", "\n\n", "First\n\nSecond", "\nFirst", "First\n", "First\n\n", "-\n--\n", "/\n", "\\\n"],
)
@pytest.mark.parametrize("new_cell", [new_markdown_cell, new_raw_cell], ids=["markdown", "raw"])
@pytest.mark.parametrize("has_next_cell", [False, True], ids=["last", "middle"])
def test_q_blank_lines_round_trip(fmt, source, new_cell, has_next_cell):
    cells = [new_cell(source)]
    if has_next_cell:
        cells.append(new_code_cell("show 42;"))
    notebook = new_notebook(cells=cells)

    script = jupytext.writes(notebook, fmt)
    assert "/" not in script.splitlines()
    restored = jupytext.reads(script, fmt)
    assert [(cell.cell_type, cell.source) for cell in restored.cells] == [
        (cell.cell_type, cell.source) for cell in notebook.cells
    ]

    # Repeated conversions must not keep adding blank cell separators.
    script2 = jupytext.writes(restored, fmt)
    assert jupytext.writes(jupytext.reads(script2, fmt), fmt) == script2


@pytest.mark.parametrize("fmt", ["q:percent", "q:hydrogen"])
@pytest.mark.parametrize("plain_json", [False, True])
@pytest.mark.parametrize("blank_lines", [0, 1, 3])
def test_q_trailing_blank_line_with_metadata_and_custom_spacing(fmt, plain_json, blank_lines):
    notebook = new_notebook(
        cells=[
            new_markdown_cell("-\n--\n", metadata={"tags": ["example"], "lines_to_next_cell": blank_lines}),
            new_code_cell("show 42;"),
        ]
    )
    script = jupytext.writes(notebook, fmt, cell_metadata_json=plain_json)
    restored = jupytext.reads(script, fmt)
    assert len(restored.cells) == 2
    assert restored.cells[0].source == "-\n--\n"
    assert restored.cells[0].metadata["tags"] == ["example"]
    assert restored.cells[0].metadata.get("lines_to_next_cell", 1) == blank_lines
    assert "endofcell" not in restored.cells[0].metadata
    assert jupytext.writes(restored, fmt) == script


@pytest.mark.parametrize("fmt", ["q:light", "q:percent"])
@pytest.mark.parametrize("source", ["%%python\nprint(1)\n\nprint(2)", "%%python\nprint(1)\n"])
def test_q_comments_foreign_code_cells(fmt, source):
    notebook = new_notebook(cells=[new_code_cell(source), new_code_cell("show 42;")])
    script = jupytext.writes(notebook, fmt)
    assert "/" not in script.splitlines()
    restored = jupytext.reads(script, fmt)
    assert [cell.source for cell in restored.cells] == [cell.source for cell in notebook.cells]


@pytest.mark.parametrize("fmt", ["py:light", "py:percent", "R:percent"])
@pytest.mark.parametrize("source", ["First\n\nSecond", "First\n", ""])
def test_export_q_notebook_to_other_language(fmt, source):
    notebook = new_notebook(
        cells=[new_markdown_cell(source)],
        metadata={"jupytext": {"main_language": "q"}},
    )
    restored = jupytext.reads(jupytext.writes(notebook, fmt), fmt)
    assert len(restored.cells) == 1
    assert restored.cells[0].cell_type == "markdown"
    assert restored.cells[0].source == source


@pytest.mark.parametrize("fmt", ["q:light", "q:percent"])
def test_q_comments_follow_target_language_with_python_kernel(fmt):
    notebook = new_notebook(
        cells=[new_markdown_cell("First\n\nSecond")],
        metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
    )
    script = jupytext.writes(notebook, fmt)
    assert "/" not in script.splitlines()
    assert jupytext.reads(script, fmt).cells[0].source == notebook.cells[0].source


def test_q_percent_reads_existing_empty_comments():
    script = "/ %% [markdown]\n/ First\n/\n/ Second\n/\n\n/ %%\nshow 42;\n"
    notebook = jupytext.reads(script, "q:percent")
    assert [(cell.cell_type, cell.source) for cell in notebook.cells] == [
        ("markdown", "First\n\nSecond\n"),
        ("code", "show 42;"),
    ]


def test_q_light_reads_existing_markdown_without_closing_marker():
    script = '/ + [markdown] tags=["md"]\n/ First\n\n/ + tags=["code"]\nshow 42;\n'
    notebook = jupytext.reads(script, "q:light")
    assert [(cell.cell_type, cell.source) for cell in notebook.cells] == [
        ("markdown", "First"),
        ("code", "show 42;"),
    ]
    assert notebook.cells[0].metadata["tags"] == ["md"]


@pytest.mark.parametrize("source", ["+\n", "/ +\n"])
@pytest.mark.parametrize("has_next_cell", [False, True])
def test_q_light_preserves_literal_start_markers_in_markdown(source, has_next_cell):
    cells = [new_markdown_cell(source)]
    if has_next_cell:
        cells.append(new_code_cell("show 42;", metadata={"tags": ["example"]}))
    notebook = new_notebook(cells=cells)
    script = jupytext.writes(notebook, "q:light")
    restored = jupytext.reads(script, "q:light")
    assert [(cell.cell_type, cell.source) for cell in restored.cells] == [
        (cell.cell_type, cell.source) for cell in notebook.cells
    ]
    assert "endofcell" not in restored.cells[0].metadata
    assert jupytext.writes(restored, "q:light") == script


@pytest.mark.parametrize("plain_json", [False, True])
@pytest.mark.parametrize("markers", ["+,-", "region,endregion"])
def test_q_light_blank_lines_with_metadata_and_custom_markers(plain_json, markers):
    notebook = new_notebook(cells=[new_markdown_cell("First\n\nSecond\n", metadata={"tags": ["example"]})])
    script = jupytext.writes(notebook, "q:light", cell_metadata_json=plain_json, cell_markers=markers)
    restored = jupytext.reads(script, "q:light")
    assert len(restored.cells) == 1
    assert restored.cells[0].source == notebook.cells[0].source
    assert restored.cells[0].metadata["tags"] == ["example"]
    assert "endofcell" not in restored.cells[0].metadata
    assert jupytext.writes(restored, "q:light") == script
