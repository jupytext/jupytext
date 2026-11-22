# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.20.1.dev0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% introduction [markdown]
# # Stable cell IDs in a text notebook
#
# With Jupytext 1.20.1 or later, the `jupytext.toml` in this directory enables
# `cell_id_to_title`. Jupytext writes the cell ID as the title of the cell
# marker. For example, `# %% introduction [markdown]` gives this cell the ID
# `introduction`. A separate `title="..."` attribute is still available for
# cell metadata, as the `results` cell shows.
#
# Open `notebook.py` with **Open With → Jupytext Notebook** in JupyterLab,
# or run `jupytext --sync notebook.py` in this directory and open the generated
# `notebook.ipynb`. The script and configuration are enough to rebuild it.

# %% rebuild
import subprocess
import sys
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

import nbformat


def rebuild(folder):
    folder.mkdir()
    for name in ("notebook.py", "jupytext.toml"):
        copyfile(name, folder / name)

    subprocess.run(
        [sys.executable, "-m", "jupytext", "--sync", "notebook.py"],
        cwd=folder,
        stdout=subprocess.DEVNULL,
        check=True,
    )
    return nbformat.read(folder / "notebook.ipynb", as_version=4)


with TemporaryDirectory() as temporary_directory:
    directory = Path(temporary_directory)
    first = rebuild(directory / "first-checkout")
    second = rebuild(directory / "second-checkout")

# %% results [markdown] title="Stable references"
# ## Compare the rebuilt notebooks
#
# The previous cell copied only the script and its configuration into two
# directories, then generated a notebook in each. Run the next cell to check
# that the IDs match.

# %% compare
cell_ids = [cell.id for cell in first.cells]
assert cell_ids == [cell.id for cell in second.cells]
assert cell_ids == ["introduction", "rebuild", "results", "compare"]
assert first.cells[2].metadata.title == "Stable references"
print(", ".join(cell_ids))
