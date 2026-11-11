import logging
from datetime import datetime

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook

import jupytext
from jupytext.compare import compare_cells, notebook_model


@pytest.fixture(params=["sync", "async"])
def cm_from_fs_meta_manager(tmp_path, request):
    pytest.importorskip("jupyterfs")
    pytest.importorskip("fsspec")
    from jupyterfs.metamanager import MetaManager, SyncMetaManager

    if request.param == "sync":
        cm_class = jupytext.build_sync_jupytext_contents_manager_class(SyncMetaManager)
    else:
        cm_class = jupytext.build_async_jupytext_contents_manager_class(MetaManager)

    logger = logging.getLogger("jupyter-fs")
    cm = cm_class(parent=None, log=logger)
    cm.initResource(
        {
            "url": tmp_path.as_uri(),
            "type": "fsspec",
            "auth": "none",
        }
    )

    managers = [h for h in getattr(cm, "_managers", {}) if h != ""]
    assert len(managers) == 1, cm.resources
    assert cm.resources[0]["init"], cm.resources

    return cm


@pytest.mark.asyncio
async def test_jupytext_jupyter_fs_metamanager(cm_from_fs_meta_manager):
    """Test the basic get/save functions of Jupytext with a fs manager
    https://github.com/mwouts/jupytext/issues/618"""
    cm = cm_from_fs_meta_manager
    # the drive identifier for the fsspec resource
    drive = [h for h in cm._managers if h != ""][0]

    # save a few files
    text = "some text\n"
    await ensure_async(cm.save(dict(type="file", content=text, format="text"), path=drive + ":text.md"))
    nb = new_notebook(cells=[new_markdown_cell("A markdown cell"), new_code_cell("1 + 1")])
    await ensure_async(cm.save(notebook_model(nb), drive + ":notebook.ipynb"))
    await ensure_async(cm.save(notebook_model(nb), drive + ":text_notebook.md"))

    # list the directory
    directory = await ensure_async(cm.get(drive + ":/"))
    assert {file["name"] for file in directory["content"]} == {
        "text.md",
        "text_notebook.md",
        "notebook.ipynb",
    }

    # get the files
    model = await ensure_async(cm.get(drive + ":/text.md", type="file"))
    assert model["type"] == "file"
    assert model["content"] == text

    model = await ensure_async(cm.get(drive + ":text.md", type="notebook"))
    assert model["type"] == "notebook"
    # We only compare the cells, as kernelspecs are added to the notebook metadata
    compare_cells(model["content"].cells, [new_markdown_cell(text.strip())], compare_ids=False)

    for nb_file in ["notebook.ipynb", "text_notebook.md"]:
        model = await ensure_async(cm.get(drive + ":" + nb_file))
        assert model["type"] == "notebook"
        assert isinstance(model["last_modified"], datetime)
        actual_cells = model["content"].cells

        # saving adds 'trusted=True' to the code cell metadata
        for cell in actual_cells:
            cell.metadata = {}
        compare_cells(actual_cells, nb.cells, compare_ids=False)


@pytest.mark.asyncio
async def test_config_jupytext_jupyter_fs_meta_manager(tmp_path, cm_from_fs_meta_manager):
    """Test the configuration of Jupytext with a fs manager"""
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,py"', encoding="utf-8")
    cm = cm_from_fs_meta_manager
    # the drive identifier for the fsspec resource
    drive = [h for h in cm._managers if h != ""][0]

    # save a few files
    nb = new_notebook()
    await ensure_async(cm.save(dict(type="file", content="text", format="text"), path=drive + ":text.md"))
    await ensure_async(cm.save(notebook_model(nb), drive + ":script.py"))
    await ensure_async(cm.save(notebook_model(nb), drive + ":text_notebook.md"))
    await ensure_async(cm.save(notebook_model(nb), drive + ":notebook.ipynb"))

    # list the directory
    directory = await ensure_async(cm.get(drive + ":/"))
    assert {file["name"] for file in directory["content"]} == {
        "jupytext.toml",
        "text.md",
        "text_notebook.md",
        "notebook.ipynb",
        "notebook.py",
        "script.py",
        "script.ipynb",
    }

    for notebook_path in ["script.py", "script.ipynb", "notebook.py", "notebook.ipynb"]:
        model = await ensure_async(cm.get(drive + ":" + notebook_path))
        assert model["type"] == "notebook"
        assert model["content"].cells == []
        assert isinstance(model["last_modified"], datetime)
