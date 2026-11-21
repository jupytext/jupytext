---
title: "Installation"
description: "Install Jupytext with pip or conda and discover the tools it ships with."
sidebar:
  order: 2
---

Installing Jupytext is as simple as
```bash
pip install jupytext
```
or
```bash
conda install jupytext -c conda-forge
```

You should run either one of these commands in the Python environment from which you launch JupyterLab. Once you have installed Jupytext, you need to restart Jupyter to be able to use Jupytext within Jupyter.

If the Python environment where the Jupyter server runs is read-only, for instance if your server is started using JupyterHub, you can still install Jupytext in user mode with:
```
/path_to_your_jupyter_environment/python -m pip install jupytext --user
```

Jupytext comes with a series of tools and plugin, which we will now briefly describe.

## Jupytext's contents manager

Jupytext provides a contents manager that let Jupyter open and save notebooks as text files.

Jupytext's contents manager is activated automatically by Jupytext's server extension. When you start either `jupyter lab` or `jupyter notebook`, you should see a line that looks like:
```bash
[I 10:28:31.646 LabApp] [Jupytext Server Extension] Changing NotebookApp.contents_manager_class from LargeFileManager to jupytext.TextFileContentsManager
```

If you don't see the message above after a fresh restart of your Jupyter server, please enable our server extension explicitly with
```
jupyter serverextension enable jupytext
```

When [`jupyter-fs>=1.0.0`](https://github.com/jpmorganchase/jupyter-fs) is being used along with `jupytext`, use `SyncMetaManager` as the contents manager for `jupyter-fs` as `jupytext` do not support async contents manager which is used in default `MetaManager` of `jupyter-fs`. The `jupyter-fs` config must be as follows:

```json
{
  "ServerApp": {
    "contents_manager_class": "jupyterfs.metamanager.SyncMetaManager",
  }
}
```
so that `jupytext` will create its own contents manager derived from `SyncMetaManager`.

## Jupytext commands in JupyterLab

Jupytext comes with a frontend extension for JupyterLab which provides pairing commands (accessible with View / Activate Command Palette, or Ctrl+Shift+C):

![](/images/pair_commands.png)

The Jupytext extension for JupyterLab is bundled with Jupytext. It should be installed and enabled automatically. You can `enable` or `disable` it manually with either
```
jupyter labextension enable jupyterlab-jupytext
jupyter labextension disable jupyterlab-jupytext
```

From Jupytext 1.16.0 on, the version of the extension is compatible with JupyterLab 4.x only. If you wish to use Jupytext with JupyterLab 3.x or older, please
- install the `jupytext` package using `pip` or `conda`
- and then, install the last version of the `jupyterlab-jupytext` extension that is compatible with your version of JupyterLab, i.e.
```
jupyter labextension install jupyterlab-jupytext@1.3.11  # for JupyterLab 3.x
jupyter labextension install jupyterlab-jupytext@1.2.2  # for JupyterLab 2.x
jupyter labextension install jupyterlab-jupytext@1.1.1  # for JupyterLab 1.x
```

## Jupytext menu in Jupyter Notebook

In Jupyter Notebook 7 you can use the same pairing commands as in JupyterLab (see above).

In Jupyter Notebook **classic**, i.e. Jupyter Notebook 6.x and below, Jupytext used to provided an extension that added a Jupytext section in the File menu.

![](/images/jupytext_menu.png)

That extension is available only for `jupytext<1.16`, and is automatically installed. If need be, you can install and activate it manually with
```
jupyter nbextension install --py jupytext [--user]
jupyter nbextension enable --py jupytext [--user]
```

See also [Issue #1095](https://github.com/jupytext/jupytext/issues/1095) where we discuss how to
add a Jupytext menu to JupyterLab and Notebook 7.x.

## Jupytext's command line interface

Jupytext provides a `jupytext` command in the terminal that you can use to pair, synchronize or convert notebooks in different formats.

The CLI is documented [here](/using/cli/).

Run `jupytext --version` to check which version of Jupytext is installed.

## Jupytext as a Python library

Jupytext is also available as a Python library. The `jupytext` package exposes the same `read`, `write`, `reads` and `writes` functions than `nbformat`, meaning that you can read and write notebooks within Python like this:

```
import jupytext

# read a notebook from a file
nb = jupytext.read("notebook.py")

# or from a string
nb = jupytext.reads(text, fmt="md:myst")

# write a notebook to a file in the 'py:percent' format
jupytext.write(nb, "notebook.py", fmt="py:percent")
```

In the above, `nb` is an instance of an `nbformat` `NotebookNode`. The notebook format is documented in the [nbformat documentation](https://nbformat.readthedocs.io).
