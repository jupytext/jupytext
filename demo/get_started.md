---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.20.1.dev0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

# Getting started with Jupytext

Jupytext lets you open a Markdown file or a script as a notebook. It can also
pair a notebook with a text file so you can review edits in Git and keep rich
outputs in the notebook.

Binder opens this example as a notebook. In a local JupyterLab installation,
follow the [installation guide](https://jupytext.org/getting-started/install/)
and open `get_started.md` with **Open With → Jupytext Notebook** to try the text
view. To start with a notebook, convert a copy of the Markdown file with
`jupytext --to ipynb --update-metadata '{"jupytext":null}' get_started.md`,
then open `get_started.ipynb`.

## Pair a notebook with a Python script

1. Open `get_started.ipynb` in JupyterLab.
2. Choose **File → Jupytext → Pair Notebook → Pair Notebook with Percent Format**.
3. Save the notebook. Jupytext writes `get_started.py` alongside it.
4. Open the script in the text editor and find the `# %%` cell boundaries. Edit
   a cell, save the script, and use **Reload Notebook from Disk** in JupyterLab
   to see the change.

## Inspect the pairing

The notebook metadata records the paired formats. This cell shows the pairing
stored in `get_started.ipynb` after you save it.

```python
from pathlib import Path

import nbformat

path = Path("get_started.ipynb")
if path.exists():
    notebook = nbformat.read(path, as_version=4)
    print(notebook.metadata.get("jupytext", {}).get("formats", "No pairing saved yet."))
else:
    print(f"Open and save {path.name} to inspect its pairing.")
```

## Try an output

Run this cell and save the notebook again. The plot stays in the `.ipynb` file
and the Python script contains the code that produced it. Install `matplotlib`
if you are running this example locally.

```python
import matplotlib.pyplot as plt

days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
commits = [3, 5, 2, 6, 4]
fig, ax = plt.subplots(figsize=(5, 2.6))
ax.bar(days, commits)
ax.set(title="A week of commits", ylabel="Commits")
plt.show()
```

## Explore the other examples

- [World Population](World%20population.ipynb) uses the same notebook to show seven text formats.
- [Benchmarking Jupytext](Benchmarking%20Jupytext.py) measures conversion size and timing.
- [Tests in a notebook](Tests%20in%20a%20notebook.md) uses pytest to check notebook code.
- [Jupytext's word cloud](Jupytext%27s%20word%20cloud.py) displays an image from a script.
- [Pairing in VS Code](vscode/notebook.ipynb) shows the same notebook in two editors.
- [Stable cell IDs](cell_ids/notebook.py) builds matching notebooks from a shared script.
