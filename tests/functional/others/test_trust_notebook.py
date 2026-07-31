"""
A notebook is trusted when all its outputs are trusted. Hence, a trusted notebook that is
updated using Jupytext should remain trusted, as no new outputs are added.
"""

import os
import shutil

import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_notebook, new_output
from jupytext.cli import jupytext as jupytext_cli
from jupytext.compare import compare_notebooks

pytestmark = pytest.mark.asyncio


async def test_py_notebooks_are_trusted(python_file, cm):
    """Text notebooks don't have outputs, so they are trusted"""
    root, file = os.path.split(python_file)
    cm.root_dir = root
    nb = await ensure_async(cm.get(file))
    for cell in nb["content"].cells:
        assert cell.metadata.get("trusted", True)


async def test_rmd_notebooks_are_trusted(rmd_file, cm):
    """Text notebooks don't have outputs, so they are trusted"""
    root, file = os.path.split(rmd_file)
    cm.root_dir = root
    nb = await ensure_async(cm.get(file))
    for cell in nb["content"].cells:
        assert cell.metadata.get("trusted", True)


def cell_just_has_safe_outputs(cell):
    if cell.cell_type != "code":
        return True
    for output in cell.get("outputs", []):
        if output.output_type == "stream":
            continue
        if output.output_type == "error":
            continue
        if output.output_type == "display_data":
            return False
        if output.output_type == "execute_result":
            return False
        return False
    return True


async def test_ipynb_notebooks_can_be_trusted(ipynb_py_file, tmpdir, no_jupytext_version_number, cm):
    if "hash sign" in ipynb_py_file:
        pytest.skip()
    root, file = os.path.split(ipynb_py_file)
    tmp_ipynb = str(tmpdir.join(file))
    py_file = file.replace(".ipynb", ".py")
    tmp_py = str(tmpdir.join(py_file))
    shutil.copy(ipynb_py_file, tmp_ipynb)

    cm.formats = "ipynb,py"
    cm.root_dir = str(tmpdir)
    model = await ensure_async(cm.get(file))
    await ensure_async(cm.save(model, py_file))

    # Make sure notebook is NOT trusted to start with
    model = await ensure_async(cm.get(file))
    for cell in model["content"].cells:
        if cell_just_has_safe_outputs(cell):
            continue
        assert "trusted" not in cell.metadata or not cell.metadata["trusted"]

    # Trust and reload
    await ensure_async(cm.trust_notebook(py_file))

    model = await ensure_async(cm.get(file))
    for cell in model["content"].cells:
        assert cell.metadata.get("trusted", True)

    # Remove py file, content should be the same
    os.remove(tmp_py)
    nb2 = await ensure_async(cm.get(file))
    for cell in nb2["content"].cells:
        assert cell.metadata.get("trusted", True)

    compare_notebooks(nb2["content"], model["content"])

    # Just for coverage
    await ensure_async(cm.trust_notebook(file))


async def test_ipynb_notebooks_can_be_trusted_even_with_metadata_filter(ipynb_py_file, tmpdir, no_jupytext_version_number, cm):
    if "hash sign" in ipynb_py_file:
        pytest.skip()
    root, file = os.path.split(ipynb_py_file)
    tmp_ipynb = str(tmpdir.join(file))
    py_file = file.replace(".ipynb", ".py")
    tmp_py = str(tmpdir.join(py_file))
    shutil.copy(ipynb_py_file, tmp_ipynb)

    cm.formats = "ipynb,py"
    cm.notebook_metadata_filter = "all"
    cm.cell_metadata_filter = "-all"
    cm.root_dir = str(tmpdir)
    model = await ensure_async(cm.get(file))
    await ensure_async(cm.save(model, py_file))

    # Make sure notebook is NOT trusted to start with
    model = await ensure_async(cm.get(file))
    for cell in model["content"].cells:
        if cell_just_has_safe_outputs(cell):
            continue
        assert "trusted" not in cell.metadata or not cell.metadata["trusted"]

    # Trust and reload
    await ensure_async(cm.trust_notebook(py_file))

    model = await ensure_async(cm.get(file))
    for cell in model["content"].cells:
        assert cell.metadata.get("trusted", True)

    # Remove py file, content should be the same
    os.remove(tmp_py)
    nb2 = await ensure_async(cm.get(file))
    for cell in nb2["content"].cells:
        assert cell.metadata.get("trusted", True)

    compare_notebooks(nb2["content"], model["content"])


async def test_text_notebooks_can_be_trusted(percent_file, tmpdir, no_jupytext_version_number, cm):
    root, file = os.path.split(percent_file)
    py_file = str(tmpdir.join(file))
    shutil.copy(percent_file, py_file)

    cm.root_dir = str(tmpdir)
    model = await ensure_async(cm.get(file))
    model["type"] == "notebook"
    await ensure_async(cm.save(model, file))

    # Unsign notebook
    nb = model["content"]
    for cell in nb.cells:
        cell.metadata.pop("trusted", True)

    cm.notary.unsign(nb)

    # Trust and reload
    await ensure_async(cm.trust_notebook(file))

    model = await ensure_async(cm.get(file))
    for cell in model["content"].cells:
        assert cell.metadata.get("trusted", True)


async def test_simple_notebook_is_trusted(tmpdir, python_notebook, cm):
    cm.root_dir = str(tmpdir)

    nb = python_notebook
    cm.notary.unsign(nb)

    # All cells are trusted in this notebook
    assert cm.notary.check_cells(nb)
    # Yet the notebook is not in the database of trusted notebooks
    assert not cm.notary.check_signature(nb)

    # Save the notebook using the CM
    await ensure_async(cm.save(dict(type="notebook", content=nb), "test.ipynb"))

    # The notebook is safe so it should have been trusted before getting saved to disk
    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    assert cm.notary.check_signature(nb)


@pytest.mark.requires_myst
async def test_myst_notebook_is_trusted_941(
    tmp_path,
    cm,
    myst="""---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
kernelspec:
  display_name: itables
  language: python
  name: itables
---

# Downsampling

```{code-cell} ipython3
from itables import init_notebook_mode, show

init_notebook_mode(all_interactive=True)
```
""",
):
    cm.root_dir = str(tmp_path)

    test_md = tmp_path / "test.md"
    test_md.write_text(myst)

    nb = (await ensure_async(cm.get("test.md")))["content"]

    # All cells are trusted in this notebook
    assert cm.notary.check_cells(nb)


@pytest.mark.parametrize("nb_was_originally_trusted", [True, False])
async def test_notebook_remains_trusted_after_jupytext_sync(tmp_path, cm, nb_was_originally_trusted):
    """
    A trusted notebook should remain trusted after a jupytext --sync edit,
    e.g. through the jupytext-sync extension in VS Code (#1505)
    """
    # Write a jupytext.toml that pairs every ipynb to py:percent (global config, no per-notebook metadata needed)
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,py:percent"\n')

    cm.root_dir = str(tmp_path)

    # Build an ipynb with a code cell that has a rich output that is not
    # automatically considered safe by Jupyter's trust model.
    nb = new_notebook(
        cells=[
            new_code_cell(
                source="HTML('<b>hello</b>')",
                outputs=[
                    new_output(
                        output_type="display_data",
                        data={"text/html": "<b>hello</b>"},
                        metadata={},
                    )
                ],
            )
        ],
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
    )

    # Sign the notebook
    nb.cells[0].metadata["trusted"] = nb_was_originally_trusted

    # Save via the CM – this also creates the paired .py file
    await ensure_async(cm.save(dict(type="notebook", content=nb), "test.ipynb"))

    # Check that the notebook is indeed trusted at this stage
    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    for cell in nb.cells:
        assert cell.metadata.get("trusted", True) is nb_was_originally_trusted, (
            f"Cell should have trusted={nb_was_originally_trusted} after initial save"
        )

    # Simulate an LLM editing the paired .py file directly on disk
    py_file = tmp_path / "test.py"
    original_text = py_file.read_text()
    modified_text = original_text.replace("HTML('<b>hello</b>')", "HTML('<b>hello, world!</b>')")
    py_file.write_text(modified_text)

    # Reload the ipynb: the py file is now newer, so its content is used.
    # The .ipynb still holds the original trusted outputs, so the combined
    # notebook should remain trusted.
    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    assert nb.cells[0].metadata["trusted"] is nb_was_originally_trusted, (
        f"Cell should keep trusted={nb_was_originally_trusted} after paired .py file is edited"
    )

    # We save the notebook with the CM
    await ensure_async(cm.save(dict(type="notebook", content=nb), "test.ipynb"))

    # We modify the notebook again
    modified_text = original_text.replace("HTML('<b>hello</b>')", "HTML('<b>hello again, world!</b>')")
    py_file.write_text(modified_text)

    # And this time we run 'jupytext --sync test.ipynb' to update the .ipynb
    ipynb_file = tmp_path / "test.ipynb"
    jupytext_cli(["--sync", str(ipynb_file)], notary=cm.notary)

    # And check that the updated notebook is still trusted
    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    assert nb.cells[0].metadata["trusted"] is nb_was_originally_trusted, (
        f"Cell should keep trusted={nb_was_originally_trusted} after jupytext sync"
    )

    # We add a new cell to the notebook
    modified_text = modified_text + "\n\n# %%\n# New cell\nprint('This is a new cell')"
    py_file.write_text(modified_text)

    # We run 'jupytext --sync test.ipynb' again
    ipynb_file = tmp_path / "test.ipynb"
    jupytext_cli(["--sync", str(ipynb_file)], notary=cm.notary)

    # And check that the updated notebook is still trusted
    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    for cell in nb.cells:
        assert cell.metadata["trusted"] is nb_was_originally_trusted, (
            f"All cells should keep trusted={nb_was_originally_trusted} after jupytext sync with new cell"
        )


async def test_paired_text_file_cannot_make_a_notebook_trusted(tmp_path, cm):
    """
    A 'trusted' cell option in a text notebook comes from the text file itself, so it is
    not evidence that the paired ipynb, and the outputs it holds, can be trusted
    """
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,py:percent"\n')

    cm.root_dir = str(tmp_path)

    nb = new_notebook(
        cells=[
            new_code_cell(
                source="HTML('<b>hello</b>')",
                outputs=[
                    new_output(
                        output_type="display_data",
                        data={"text/html": "<b>hello</b>"},
                        metadata={},
                    )
                ],
            )
        ],
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
    )
    nb.cells[0].metadata["trusted"] = False

    # Save via the CM - this also creates the paired .py file
    await ensure_async(cm.save(dict(type="notebook", content=nb), "test.ipynb"))

    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    assert nb.cells[0].metadata["trusted"] is False

    # The paired .py file is edited on disk, and it says that the cell is trusted
    py_file = tmp_path / "test.py"
    py_file.write_text(py_file.read_text().replace("# %%\n", "# %% trusted=true\n"))

    jupytext_cli(["--sync", str(tmp_path / "test.ipynb")], notary=cm.notary)

    nb = (await ensure_async(cm.get("test.ipynb")))["content"]
    assert nb.cells[0].metadata["trusted"] is False, "The .py file should not have made the notebook trusted"


@pytest.mark.requires_myst
async def test_paired_notebook_with_outputs_is_not_trusted_941(tmp_path, python_notebook, cm):
    cm.root_dir = str(tmp_path)

    nb = python_notebook
    nb.cells.append(new_code_cell(source="1+1", outputs=[new_output("execute_result")]))
    nb.metadata["jupytext"] = {"formats": "ipynb,md:myst"}
    cm.notary.unsign(nb)
    await ensure_async(cm.save(model=dict(type="notebook", content=nb), path="test.ipynb"))

    nb = (await ensure_async(cm.get("test.md")))["content"]
    assert not cm.notary.check_cells(nb)
    assert not cm.notary.check_signature(nb)
