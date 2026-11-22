import inspect
import os

import pytest
from jupyter_core.utils import ensure_async
from nbformat import validate
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output, new_raw_cell
from tornado.web import HTTPError

from jupytext import read, reads, write, writes
from jupytext.cli import jupytext
from jupytext.combine import combine_inputs_with_outputs
from jupytext.config import JupytextConfiguration


@pytest.mark.parametrize(("fmt", "marker"), [("light", "# +"), ("percent", "# %%"), ("hydrogen", "# %%")])
@pytest.mark.parametrize("filter_metadata", [False, True])
def test_cell_id_to_title_round_trip(fmt, marker, filter_metadata):
    config = JupytextConfiguration(cell_id_to_title=True)
    if filter_metadata:
        config.notebook_metadata_filter = "-all"
        config.cell_metadata_filter = "-all"
    notebook = new_notebook(
        cells=[
            new_raw_cell("---\ntitle: Example\n---", id="frontmatter"),
            new_markdown_cell("# Heading", id="intro-1", metadata={"title": "Read me"}),
            new_code_cell("1 + 1", id="calculate_2"),
            new_raw_cell("Unformatted", id="raw-3"),
        ]
    )
    text = writes(notebook, f"py:{fmt}", config=config)
    assert text.startswith("# ---\n# title: Example\n")
    assert "#     raw_header_cell_id: frontmatter\n" in text
    assert f"{marker} intro-1 [markdown]" in text
    assert f"{marker} calculate_2" in text
    assert f"{marker} raw-3" in text
    assert ('title="Read me"' in text) is not filter_metadata

    recreated = reads(text, f"py:{fmt}", config=config)
    validate(recreated)
    assert "_cell_ids_from_text" not in recreated
    assert "raw_header_cell_id" not in recreated.metadata.get("jupytext", {})
    assert [(cell.id, cell.cell_type, cell.source) for cell in recreated.cells] == [
        (cell.id, cell.cell_type, cell.source) for cell in notebook.cells
    ]
    assert recreated.cells[1].metadata.get("title") == (None if filter_metadata else "Read me")
    assert notebook.cells[1].metadata.title == "Read me"


@pytest.mark.parametrize("title", ["A title!", "é", "a" * 65])
def test_invalid_cell_id_remains_a_title(title):
    config = JupytextConfiguration(cell_id_to_title=True)
    notebook = reads(f"# %% {title}\n1 + 1\n", "py:percent", config=config)
    assert notebook.cells[0].metadata.title == title
    validate(notebook)


def test_cell_id_to_title_is_opt_in():
    text = "# %% A title\n1 + 1\n"
    assert reads(text, "py:percent").cells[0].metadata.title == "A title"
    config = JupytextConfiguration(cell_id_to_title=True)
    assert reads(text, "py:percent", config=config).cells[0].id == "A_title"
    # An explicit title attribute remains cell metadata.
    text = '# %% title="A title"\n1 + 1\n'
    assert reads(text, "py:percent", config=config).cells[0].metadata.title == "A title"


@pytest.mark.parametrize("config", [None, JupytextConfiguration(cell_id_to_title=False)])
def test_script_header_cannot_enable_cell_id_to_title(config):
    text = """# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       cell_id_to_title: true
# ---

# %% A title
1 + 1

# %% A title
2 + 2
"""
    notebook = reads(text, "py:percent", config=config)
    assert [cell.metadata.title for cell in notebook.cells] == ["A title", "A title"]
    assert writes(notebook, "py:percent", config=config).count("# %% A title\n") == 2


def test_empty_yaml_raw_cell_keeps_its_id():
    config = JupytextConfiguration(cell_id_to_title=True, notebook_metadata_filter="-all")
    notebook = new_notebook(cells=[new_raw_cell("---\n---", id="frontmatter")])
    text = writes(notebook, "py:light", config=config)
    recreated = reads(text, "py:light", config=config)
    assert [(cell.id, cell.cell_type, cell.source) for cell in recreated.cells] == [("frontmatter", "raw", "---\n---")]
    assert recreated.metadata.jupytext.notebook_metadata_filter == "-all"


def test_duplicate_cell_ids_are_reported():
    config = JupytextConfiguration(cell_id_to_title=True)
    text = "# %% A title\n1 + 1\n\n# %% A_title\n2 + 2\n"
    with pytest.raises(ValueError, match="Duplicate cell ID 'A_title'"):
        reads(text, "py:percent", config=config)


def test_notebook_fields_do_not_supply_ids_for_pairing():
    source = new_notebook(cells=[new_code_cell("1 + 1", id="source")])
    source["_cell_ids_from_text"] = ["source"]
    outputs = new_notebook(cells=[new_code_cell("1 + 1", id="existing")])

    assert combine_inputs_with_outputs(source, outputs).cells[0].id == "existing"


def test_legacy_notebook_without_cell_ids():
    config = JupytextConfiguration(cell_id_to_title=True)
    notebook = new_notebook(cells=[new_code_cell("1 + 1", metadata={"title": "A title"})])
    notebook.nbformat_minor = 4
    notebook.cells[0].pop("id")
    text = writes(notebook, "py:light", config=config)
    assert '# + title="A title"' in text
    assert reads(text, "py:light", config=config).cells[0].metadata.title == "A title"


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("action", [["--sync"], ["--to", "ipynb", "--update"]])
def test_cli_keeps_explicit_and_existing_cell_ids(tmp_path, legacy, action):
    script = tmp_path / "example.py"
    ipynb = script.with_suffix(".ipynb")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.jupytext]\nformats = "ipynb,py:percent"\ncell_id_to_title = true\n', encoding="utf-8"
    )
    notebook = new_notebook(
        cells=[
            new_code_cell("1 + 1", id="first", outputs=[new_output("stream", name="stdout", text="first")]),
            new_code_cell("2 + 2", id="second", outputs=[new_output("stream", name="stdout", text="second")]),
        ]
    )
    if legacy:
        notebook.nbformat_minor = 4
        for cell in notebook.cells:
            cell.pop("id")
    write(notebook, ipynb)
    script.write_text("# %% renamed\n1 + 1\n\n# %%\n2 + 2\n", encoding="utf-8")
    os.utime(ipynb, (100, 100))
    os.utime(script, (200, 200))

    assert jupytext([*action, str(script)]) == 0
    converted = read(ipynb)
    validate(converted)
    assert converted.cells[0].id == "renamed"
    assert converted.cells[1].id
    if not legacy:
        assert converted.cells[1].id == "second"
    assert [cell.outputs[0].text for cell in converted.cells] == ["first", "second"]


def test_outputs_follow_explicit_ids_when_identical_cells_are_reordered(tmp_path):
    (tmp_path / "jupytext.toml").write_text("cell_id_to_title = true\n", encoding="utf-8")
    notebook = new_notebook(
        cells=[
            new_code_cell("print(x)", id=cell_id, outputs=[new_output("stream", name="stdout", text=cell_id)])
            for cell_id in ("first", "second")
        ]
    )
    script = tmp_path / "example.py"
    ipynb = script.with_suffix(".ipynb")
    write(notebook, ipynb)
    script.write_text("# %% second\nprint(x)\n\n# %% first\nprint(x)\n", encoding="utf-8")

    assert jupytext(["--to", "ipynb", "--update", str(script)]) == 0
    converted = read(ipynb)
    assert [(cell.id, cell.outputs[0].text) for cell in converted.cells] == [("second", "second"), ("first", "first")]


@pytest.mark.asyncio
@pytest.mark.parametrize("id_to_change", ["frontmatter", "intro"])
async def test_contents_manager_opens_pair_with_cell_ids(tmp_path, cm, id_to_change):
    cm.root_dir = str(tmp_path)
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,py:light"\ncell_id_to_title = true\n', encoding="utf-8")
    script = tmp_path / "example.py"
    ipynb = script.with_suffix(".ipynb")
    notebook = new_notebook(
        cells=[
            new_raw_cell("---\ntitle: Example\n---", id="frontmatter"),
            new_markdown_cell("Heading", id="intro"),
            new_code_cell("1 + 1", id="code"),
        ]
    )
    config = JupytextConfiguration(cell_id_to_title=True)
    text = writes(notebook, "py:light", config=config).replace("# + code\n", "# +\n")
    script.write_text(text, encoding="utf-8")
    write(notebook, ipynb)
    os.utime(script, (100, 100))
    os.utime(ipynb, (200, 200))

    model = await ensure_async(cm.get(ipynb.name))
    assert [cell.id for cell in model["content"].cells] == ["frontmatter", "intro", "code"]

    script.write_text(text.replace(id_to_change, "older"), encoding="utf-8")
    os.utime(script, (100, 100))
    with pytest.raises(HTTPError, match="is more recent"):
        await ensure_async(cm.get(ipynb.name))


@pytest.mark.asyncio
async def test_contents_manager_opens_pair_created_by_sync(tmp_path, cm):
    cm.root_dir = str(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.jupytext]\ncell_id_to_title = true\nformats = "ipynb,py"\n', encoding="utf-8"
    )
    script = tmp_path / "example.py"
    ipynb = script.with_suffix(".ipynb")
    script.write_text("# + intro [markdown]\n# Heading\n", encoding="utf-8")

    assert jupytext(["--sync", str(script)]) == 0
    os.utime(script, (100, 100))
    os.utime(ipynb, (200, 200))

    supports_hash = "require_hash" in inspect.signature(cm.super.get).parameters
    kwargs = {"require_hash": True} if supports_hash else {}
    model = await ensure_async(cm.get(ipynb.name, **kwargs))
    assert model["content"].cells[0].id == "intro"
    if supports_hash:
        assert model["hash"]
