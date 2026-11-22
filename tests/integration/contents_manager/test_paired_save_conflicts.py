"""Protect disk edits without requiring Jupyter Collaboration to be installed."""

import os

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4 import new_code_cell, new_notebook
from tornado.web import HTTPError

import jupytext
from jupytext.compare import notebook_model

pytestmark = pytest.mark.asyncio


async def create_pair(cm, tmp_path):
    cm.root_dir = str(tmp_path)
    nb = new_notebook(
        metadata={"jupytext": {"formats": "ipynb,py:percent"}},
        cells=[new_code_cell("original = 1")],
    )
    await ensure_async(cm.save(notebook_model(nb), "demo.ipynb"))


def change_file(path, content):
    # Force a distinct mtime even on filesystems with coarse timestamp resolution.
    timestamp = path.stat().st_mtime
    path.write_text(content)
    os.utime(path, (timestamp + 2, timestamp + 2))


@pytest.mark.parametrize("opened_path", ["demo.ipynb", "demo.py"])
async def test_changed_twin_refuses_save_before_writing(cm, tmp_path, opened_path):
    await create_pair(cm, tmp_path)
    model = await ensure_async(cm.get(opened_path, type="notebook"))
    model["content"].cells[0].source = "unsaved = 2"
    twin = tmp_path / ("demo.py" if opened_path.endswith("ipynb") else "demo.ipynb")
    nb = jupytext.read(twin)
    nb.cells[0].source = "external = 3"
    change_file(twin, jupytext.writes(nb, fmt="py:percent" if twin.suffix == ".py" else "ipynb"))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}

    # Collaboration and Jupyter may poll metadata between editing and saving.
    await ensure_async(cm.get(opened_path, content=False))
    with pytest.raises(HTTPError, match="changed on disk") as error:
        await ensure_async(cm.save(model, opened_path))
    assert error.value.status_code == 409
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()} == before
    assert model["content"].cells[0].source == "unsaved = 2"


async def test_repeated_saves_and_reload_after_conflict(cm, tmp_path):
    await create_pair(cm, tmp_path)
    model = await ensure_async(cm.get("demo.ipynb"))
    for source in ["first = 1", "second = 2"]:
        model["content"].cells[0].source = source
        await ensure_async(cm.save(model, "demo.ipynb"))

    twin = tmp_path / "demo.py"
    change_file(twin, twin.read_text().replace("second = 2", "external = 3"))
    with pytest.raises(HTTPError) as error:
        await ensure_async(cm.save(model, "demo.ipynb"))
    assert error.value.status_code == 409

    reloaded = await ensure_async(cm.get("demo.ipynb"))
    assert reloaded["content"].cells[0].source == "external = 3"
    reloaded["content"].cells[0].source = "merged = 4"
    await ensure_async(cm.save(reloaded, "demo.ipynb"))
    assert jupytext.read(twin).cells[0].source == "merged = 4"


async def test_unpair_after_twin_changes(cm, tmp_path):
    await create_pair(cm, tmp_path)
    model = await ensure_async(cm.get("demo.ipynb"))
    twin = tmp_path / "demo.py"
    change_file(twin, twin.read_text().replace("original = 1", "external = 3"))
    del model["content"].metadata["jupytext"]["formats"]
    await ensure_async(cm.save(model, "demo.ipynb"))
    assert jupytext.read(twin).cells[0].source == "external = 3"


async def test_twin_created_after_loading_refuses_save(cm, tmp_path):
    await create_pair(cm, tmp_path)
    twin = tmp_path / "demo.py"
    text = twin.read_text()
    twin.unlink()
    model = await ensure_async(cm.get("demo.ipynb"))
    twin.write_text(text.replace("original = 1", "external = 3"))
    before = (tmp_path / "demo.ipynb").read_bytes()

    with pytest.raises(HTTPError) as error:
        await ensure_async(cm.save(model, "demo.ipynb"))
    assert error.value.status_code == 409
    assert (tmp_path / "demo.ipynb").read_bytes() == before
    assert jupytext.read(twin).cells[0].source == "external = 3"


async def test_conflict_in_third_file_prevents_all_writes(cm, tmp_path):
    await create_pair(cm, tmp_path)
    model = await ensure_async(cm.get("demo.ipynb"))
    model["content"].metadata["jupytext"]["formats"] = "ipynb,md,py:percent"
    await ensure_async(cm.save(model, "demo.ipynb"))
    twin = tmp_path / "demo.py"
    change_file(twin, twin.read_text().replace("original = 1", "external = 3"))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    model["content"].cells[0].source = "unsaved = 2"

    with pytest.raises(HTTPError) as error:
        await ensure_async(cm.save(model, "demo.ipynb"))
    assert error.value.status_code == 409
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()} == before
