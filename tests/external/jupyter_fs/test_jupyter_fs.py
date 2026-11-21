import logging
import sys

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook

import jupytext
from jupytext.compare import compare_cells, notebook_model

pytestmark = pytest.mark.skipif(sys.version_info >= (3, 12), reason="https://github.com/mwouts/jupytext/issues/1509")


@pytest.fixture(params=["sync", "async"])
def cm_from_fs_meta_manager(tmpdir, request):
    try:
        from jupyterfs.metamanager import MetaManager, SyncMetaManager
    except ImportError:
        pytest.skip("jupyterfs is not available")

    if request.param == "sync":
        cm_class = jupytext.build_sync_jupytext_contents_manager_class(SyncMetaManager)
    else:
        cm_class = jupytext.build_async_jupytext_contents_manager_class(MetaManager)

    logger = logging.getLogger("jupyter-fs")
    cm = cm_class(parent=None, log=logger)
    cm.initResource(
        {
            "url": f"osfs://{tmpdir}",
        }
    )

    managers = [h for h in getattr(cm, "_managers", {}) if h != ""]
    if not managers:
        pytest.skip("jupyterfs osfs resource could not be initialized; optional dependency may be missing")

    return cm


@pytest.mark.asyncio
async def test_jupytext_jupyter_fs_metamanager(cm_from_fs_meta_manager):
    """Test the basic get/save functions of Jupytext with a fs manager
    https://github.com/mwouts/jupytext/issues/618"""
    cm = cm_from_fs_meta_manager
    # the hash that corresponds to the osfs
    osfs = [h for h in cm._managers if h != ""][0]

    # save a few files
    text = "some text\n"
    await ensure_async(cm.save(dict(type="file", content=text, format="text"), path=osfs + ":text.md"))
    nb = new_notebook(cells=[new_markdown_cell("A markdown cell"), new_code_cell("1 + 1")])
    await ensure_async(cm.save(notebook_model(nb), osfs + ":notebook.ipynb"))
    await ensure_async(cm.save(notebook_model(nb), osfs + ":text_notebook.md"))

    # list the directory
    directory = await ensure_async(cm.get(osfs + ":/"))
    assert {file["name"] for file in directory["content"]} == {
        "text.md",
        "text_notebook.md",
        "notebook.ipynb",
    }

    # get the files
    model = await ensure_async(cm.get(osfs + ":/text.md", type="file"))
    assert model["type"] == "file"
    assert model["content"] == text

    model = await ensure_async(cm.get(osfs + ":text.md", type="notebook"))
    assert model["type"] == "notebook"
    # We only compare the cells, as kernelspecs are added to the notebook metadata
    compare_cells(model["content"].cells, [new_markdown_cell(text.strip())], compare_ids=False)

    for nb_file in ["notebook.ipynb", "text_notebook.md"]:
        model = await ensure_async(cm.get(osfs + ":" + nb_file))
        assert model["type"] == "notebook"
        actual_cells = model["content"].cells

        # saving adds 'trusted=True' to the code cell metadata
        for cell in actual_cells:
            cell.metadata = {}
        compare_cells(actual_cells, nb.cells, compare_ids=False)


@pytest.mark.asyncio
async def test_config_jupytext_jupyter_fs_meta_manager(tmpdir, cm_from_fs_meta_manager):
    """Test the configuration of Jupytext with a fs manager"""
    tmpdir.join("jupytext.toml").write('formats = "ipynb,py"')
    cm = cm_from_fs_meta_manager
    # the hash that corresponds to the osfs
    osfs = [h for h in cm._managers if h != ""][0]

    # save a few files
    nb = new_notebook()
    await ensure_async(cm.save(dict(type="file", content="text", format="text"), path=osfs + ":text.md"))
    await ensure_async(cm.save(notebook_model(nb), osfs + ":script.py"))
    await ensure_async(cm.save(notebook_model(nb), osfs + ":text_notebook.md"))
    await ensure_async(cm.save(notebook_model(nb), osfs + ":notebook.ipynb"))

    # list the directory
    directory = await ensure_async(cm.get(osfs + ":/"))
    assert {file["name"] for file in directory["content"]} == {
        "jupytext.toml",
        "text.md",
        "text_notebook.md",
        "notebook.ipynb",
        "notebook.py",
        "script.py",
        "script.ipynb",
    }
