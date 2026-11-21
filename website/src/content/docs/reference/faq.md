---
title: "FAQ"
description: "Frequently asked questions about Jupytext."
sidebar:
  order: 3
---

## What is Jupytext?

Jupytext is a Python package that provides _two-way_ conversion between Jupyter notebooks and several other text-based formats like Markdown documents or scripts.

## Why would I want to convert my notebooks to text?

The text representation only contains the part of the notebook that you wrote (not the outputs). You get a cleaner diff history. Thanks to the _two-way_ conversion, you can also act on the text file and then propagate the changes to the original `.ipynb` file. Refactor your code or merge multiple contributions easily!

## How do I use Jupytext?

Open the notebook that you want to version control. _Pair_ the notebook to a script or a Markdown file using the [Jupytext Commands](/getting-started/install/#jupytext-commands-in-jupyterlab) in JupyterLab.

Save the notebook, and you get two copies of the notebook: the original `*.ipynb` file, together with its paired text representation.

## Which Jupytext format do you recommend?

Notebooks that contain more text than code are best represented as Markdown documents. These are conveniently edited in IDEs and are also well rendered on GitHub.

Saving notebooks as scripts is an appropriate choice when you want to act on the code (refactor the code, import it in another script or notebook, etc). Use the `percent` format if you prefer to get explicit cell markers (compatible with VScode, PyCharm, Spyder, Hydrogen...). And if you prefer to get the minimal amount of cell markers, go for the `light` format.

## Can I see a sample of each format?

Go to [our demo folder](https://github.com/jupytext/jupytext/tree/main/demo) and see how our sample `World population` notebook is represented in each format.

## Can I edit the paired text file?

Yes! When you're done, reload the notebook in Jupyter. There, you will see the updated input cells combined with the matching output cells from the `.ipynb` file.

## Do I need to close my notebook in Jupyter?

Closing the notebook in Jupyter while you refactor it in another editor will help you avoid the message _Untitled.ipynb has changed on disk_. However, you don't really need to close the notebook.

You can simply use _Reload Notebook from disk_ to load the latest edits once you're done with the other editor. When you reload the notebook, the kernel variables are preserved (and the outputs too if the notebook is paired to an `.ipynb` file), so you can continue your work where you left it.

💡 **Tip:** You can automate the notebook reloading by installing the [Jupyter Collaboration](/integrations/jupyter-collaboration/) extension.

## How do paired notebooks work?

The `.ipynb` file contains the full notebook. The paired text file only contains the input cells and selected metadata. When the notebook is loaded by Jupyter, input cells are loaded from the text file, while the output cells and the filtered metadata are restored using the `.ipynb` file. When the notebook is saved in Jupyter, the two files are updated to match the current content of the notebook.

## Can I create a notebook from a text file?

Certainly. Open your pre-existing scripts or Markdown files as notebooks with the _Open as Notebook_ menu in JupyterLab.

Output cells appear in the browser when you execute the notebook, but they are not written to the disk when you save the notebook.

The output cells are lost when you reload the notebook - if you want to avoid this, just _pair_ the text file to an `.ipynb` file.

If you want to convert text formats to notebooks programmatically, use one of
```shell
jupytext --to ipynb *.md                        # convert all .md files to notebooks with no outputs
jupytext --to ipynb --execute *.md              # convert all .md files to notebooks and execute them
jupytext --set-formats ipynb,md --execute *.md  # convert all .md files to paired notebooks and execute them
```

Conversions the other way use a similar format
```shell
jupytext --to md *.ipynb                         # convert all .ipynb files to .md files
```

## I want a specific cell to be commented out in the paired script

That's possible! See how to [activate or deactivate cells](/reference/advanced-options/#active-and-inactive-cells).

## Which files should I version control?

Unless you want to version the outputs, you should version *only the text representation*. The paired `.ipynb` file can safely be deleted. It will be recreated locally the next time you open the notebook (from the text file) and save it.

Note that if you version both the `.md` and `.ipynb` files, you can configure `git diff` to [ignore the diffs on the `.ipynb` files](https://github.com/jupytext/jupytext/issues/251).

## I have modified a text file, but git reports no diff for the paired `.ipynb` file

The synchronization between the two files happens when you reload and *save* the notebook in Jupyter, or when you explicitly run `jupytext --sync`. If you want to force the synchronization on every commit, you could use `jupytext` as a [pre-commit hook](/using/pre-commit/).

## Jupyter warns me that the file has changed on disk

By default, Jupyter tries to save your notebooks every 2 minutes. If you have edited the text representation in another editor, it will detect that and ask you if you want to either overwrite, or _reload_ the notebook from disk.

You should simply click on _Reload_.

Note you can deactivate Jupyter's autosave function with the _Autosave Document_ setting in JupyterLab (search for _autosave_ in the _advanced settings editor_).

## When I reload, Jupyter warns me that my notebook has unsaved changes

That happens if you have edited both the notebook and the paired text file at the same time... If you know which version you want to keep, save it and reload the other. If you want to compare and merge both versions, backup the text file (with e.g. `git stash`), save the notebook, and merge the updated paired file with the backup (with e.g. `git stash pop`). Then, refresh the notebook in Jupyter.

## Jupyter complains that the `.ipynb` file is more recent than the text representation

This happens if you have edited the `.ipynb` file outside of Jupyter. This is a safeguard to avoid overwriting the notebook with an outdated text file.

In this case, a manual action is requested. Remove the paired `.md` or `.py` file if it is outdated, otherwise, edit and save it to update the file timestamp.

## Can I use Jupytext with JupyterHub, Binder, Nteract, Colab, Saturn or Azure?

Jupytext is compatible with JupyterHub (execute `pip install jupytext --user` to install it in user mode) and with Binder (add `jupytext` to the project requirements).

If you use another editor than JupyterLab, you probably can't get Jupytext there. However, you can still use Jupytext at the command line to manually sync the two representations of the notebook:
```shell
jupytext --set-formats ipynb,py:light notebook.ipynb   # Pair a notebook to a light script
jupytext --sync notebook.ipynb                         # Sync the two representations
```

## Can I re-write my git history to use text files instead of notebooks?

Indeed, you could substitute every `.ipynb` file in the project history with its Jupytext Markdown representation.

Technically this is available in just one command, which results in a complete rewrite of the history. Please experiment that in a branch, and think twice before pushing the result...
```shell
git filter-branch --tree-filter 'jupytext --to md */*.ipynb && rm -f */*.ipynb' HEAD
```

See the result and the cleaner diff history in the case of the [Python Data Science Handbook](https://github.com/mwouts/PythonDataScienceHandbook/tree/jupytext_no_ipynb).
