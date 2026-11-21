[![](https://github.com/jupytext/jupytext/blob/17aea37c612f33a4e27eeee4b81966f1506920fd/docs/images/logo_large.png?raw=true)](https://jupytext.org)

<!-- INDEX-START -->

[![CI](https://github.com/jupytext/jupytext/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jupytext/jupytext/actions)
[![codecov.io](https://codecov.io/github/jupytext/jupytext/coverage.svg?branch=main)](https://codecov.io/gh/jupytext/jupytext/branch/main)
[![MIT License](https://img.shields.io/github/license/jupytext/jupytext)](https://github.com/jupytext/jupytext/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub language count](https://img.shields.io/github/languages/count/jupytext/jupytext)](https://jupytext.org/formats/languages/)
[![Conda Version](https://anaconda.org/conda-forge/jupytext/badges/version.svg)](https://anaconda.org/conda-forge/jupytext/)
[![Pypi](https://img.shields.io/pypi/v/jupytext.svg)](https://pypi.python.org/pypi/jupytext)
[![pyversions](https://img.shields.io/pypi/pyversions/jupytext.svg)](https://pypi.python.org/pypi/jupytext)
[![Binder:lab](https://img.shields.io/badge/binder-jupyterlab-0172B2.svg)](https://mybinder.org/v2/gh/jupytext/jupytext/main?urlpath=lab/tree/demo/get_started.ipynb)
[![Binder:notebook](https://img.shields.io/badge/binder-notebook-0172B2.svg)](https://mybinder.org/v2/gh/jupytext/jupytext/main?filepath=demo)
[![launch - renku](https://renkulab.io/renku-badge.svg)](https://renkulab.io/projects/best-practices/jupytext/sessions/new?autostart=1)
[![Jupyter Con 2020](https://img.shields.io/badge/YouTube-JupyterCon%202020-red.svg)](https://www.youtube.com/watch?v=SDYdeVfMh48)

# Jupytext

Have you always wished Jupyter notebooks were plain text documents? Wished you could edit them in your favorite IDE? And get clear and meaningful diffs when doing version control? Then, Jupytext may well be the tool you're looking for!

## Text Notebooks

A Python notebook encoded in the `py:percent` [format](website/src/content/docs/formats/scripts.md#the-percent-format) has a `.py` extension and looks like this:

```
# %% [markdown]
# This is a markdown cell

# %%
def f(x):
  return 3*x+1
```

Only the notebook inputs (and optionally, the metadata) are included. Text notebooks are well suited for version control. You can also edit or refactor them in an IDE - the `.py` notebook above is a regular Python file.

We recommend the `percent` format for notebooks that mostly contain code. The `percent` format is available for Julia, Python, R and many other [languages](website/src/content/docs/formats/languages.md).

If your notebook is documentation-oriented, a [Markdown-based format](website/src/content/docs/formats/markdown.md) (text notebooks with a `.md` extension) might be more appropriate. Depending on what you plan to do with your notebook, you might prefer the Myst Markdown format, which interoperates very well with Jupyter Book, or Quarto Markdown, or even Pandoc Markdown.

## Installation

Install Jupytext in the Python environment that you use for Jupyter. Use either

    pip install jupytext

or

    conda install jupytext -c conda-forge

Then, restart your JupyterLab server, and make sure Jupytext is activated in Jupyter:  `.py` and `.md` files have a Notebook icon, and you can open them as Notebooks with a right click in JupyterLab.

![Notebook icon on text notebooks](https://github.com/jupytext/jupytext/blob/64b4be818508760116f91bf156342cb4cf724d93/docs/images/jupyterlab_right_click.png?raw=true)

## Paired Notebooks

Text notebooks with a `.py` or `.md` extension are well suited for version control. They can be edited or authored conveniently in an IDE. You can open and run them as notebooks in JupyterLab with a right click. However, the notebook outputs are lost when the notebook is closed, as only the notebook inputs are saved in text notebooks.

A convenient alternative to text notebooks are [paired notebooks](website/src/content/docs/using/paired-notebooks.md). These are a set of two files, say `.ipynb` and `.py`, that contain the same notebook, but in different formats.

You can edit the `.py` version of the paired notebook, and get the edits back in Jupyter by selecting _reload notebook from disk_. The outputs will be reloaded from the `.ipynb` file, if it exists. The `.ipynb` version will be updated or recreated the next time you save the notebook in Jupyter.

💡 **Tip:** You can automate the notebook reloading by installing the [Jupyter Collaboration](website/src/content/docs/integrations/jupyter-collaboration.md) extension.

To pair a notebook in JupyterLab, use the command `Pair Notebook with percent Script` from the Command Palette:

![](https://github.com/jupytext/jupytext/blob/64b4be818508760116f91bf156342cb4cf724d93/docs/images/pair_commands.png?raw=true)

To pair all the notebooks in a certain directory, create a [configuration file](website/src/content/docs/using/config.md) with this content:

```
# jupytext.toml at the root of your notebook directory
formats = "ipynb,py:percent"
```

## Command line

Jupytext is also available at the [command line](website/src/content/docs/using/cli.md). You can

- pair a notebook with `jupytext --set-formats ipynb,py:percent notebook.ipynb`
- synchronize the paired files with `jupytext --sync notebook.py` (the inputs are loaded from the most recent paired file)
- convert a notebook in one format to another with `jupytext --to ipynb notebook.py` (use `-o` if you want a specific output file)
- pipe a notebook to a linter with e.g. `jupytext --pipe black notebook.ipynb`

## Sample use cases

### Notebooks under version control

This is a quick how-to:
- Open your `.ipynb` notebook in Jupyter and [pair](website/src/content/docs/using/paired-notebooks.md) it to a `.py` notebook, using either the _pair_ command in JupyterLab, or a global [configuration file](website/src/content/docs/using/config.md)
- Save the notebook - this creates a `.py` notebook
- Add this `.py` notebook to version control

You might exclude `.ipynb` files from version control (unless you want to see the outputs versioned!). Jupytext will recreate the `.ipynb` files locally when the users open and save the `.py` notebooks.

### Collaborating on notebooks with Git

Collaborating on Jupyter notebooks through Git becomes as easy as collaborating on text files.

Assume that you have your `.py` notebooks under version control (see above). Then,
- Your collaborator pulls the `.py` notebook
- They open it _as a notebook_ in Jupyter (right-click in JupyterLab)
- At that stage the notebook has no outputs. They run the notebook and save it. Outputs are regenerated, and a local `.ipynb` file is created
- They edit the notebook, and push the updated `notebook.py` file. The diff is nothing else than a standard diff on a Python script.
- You pull the updated `notebook.py` script, and refresh your browser. The input cells are updated based on the new content of `notebook.py`. The outputs are reloaded from your local `.ipynb` file. Finally, the kernel variables are untouched, so you have the option to run only the modified cells to get the new outputs.

### Editing or refactoring a notebook in an IDE

Once your notebook is [paired](website/src/content/docs/using/paired-notebooks.md) with a `.py` file, you can easily edit or refactor the `.py` representation of the notebook in an IDE.

Once you are done editing the `.py` notebook, you will just have to _reload_ the notebook in Jupyter to get the latest edits there.

Note: It is simpler to close the `.ipynb` notebook in Jupyter when you edit the paired `.py` file. There is no obligation to do so; however, if you don't, you should be prepared to read carefully the pop-up messages. If Jupyter tries to save the notebook while the paired `.py` file has also been edited on disk since the last reload, a conflict will be detected and you will be asked to decide which version of the notebook (in memory or on disk) is the appropriate one. Alternatively, the [Jupyter Collaboration](website/src/content/docs/integrations/jupyter-collaboration.md) extension provides an autoreload feature which simplifies this.

## More resources

Read more about Jupytext in the [documentation](https://jupytext.org).

If you're new to Jupytext, you may want to start with the [FAQ](website/src/content/docs/reference/faq.md) or with the [Tutorials](website/src/content/docs/reference/tutorials.md).

There is also this short introduction to Jupytext: [![](https://img.shields.io/badge/YouTube-JupyterCon%202020-red.svg)](https://www.youtube.com/watch?v=SDYdeVfMh48).

## Community

Have a question, a bug report, or an idea? Join us on [Discord](https://discord.gg/VfdAsYyn) or open an issue or discussion on [GitHub](https://github.com/jupytext/jupytext).
