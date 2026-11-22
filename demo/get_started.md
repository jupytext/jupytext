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

This small notebook shows you how to activate Jupytext in the JupyterLab
environment. We'll show you a few things that you can do with Jupytext and
a bit of what happens under the hood.

**Note: to run this notebook locally, you need to first follow the Jupytext
installation instructions and activate the JupyterLab plugin. If you're on
Binder, it should already work.**


## Enabling Jupytext in a new notebook

This notebook is brand new - it hasn't had any special extra metadata added
to it.

If we want Jupytext to save files in multiple formats automatically,
we can use the JupyterLab **command palette** to do so.

* In the _View_ menu, click on _Activate Command Palette_
* Then type **`Jupytext`**. You should see a number of commands come up. Each
  one tells Jupytext to save the notebook in a different
  file format automatically.
* Select **Pair notebook with MyST Markdown**

That's it! If you have Jupytext installed, it will now save your notebook in
markdown format automatically when you save this `.ipynb` file
**in addition to** saving the `.ipynb` file itself.

After you've done this, save the notebook. You should now see a new file called
**`get_started.md`** in the same directory as this notebook.


## How does Jupytext know to do this?

Jupytext uses notebook-level metadata to keep track of what formats are paired
with a notebook. Below we'll print the metadata of this notebook so you can see
what the Jupytext metadata looks like.

```python
import nbformat as nbf
from IPython.display import JSON
notebook = nbf.read('./get_started.ipynb', nbf.NO_CONVERT)
JSON(notebook['metadata'])
```

As you select different formats from the command palette (following the instructions
above) and save the notebook, you'll see this metadata change.


## That's it!

Play around with different kinds of code and outputs to see how each is
converted into its corresponding text format. Here's a little Python code
to get you started:

```python
import numpy as np
import matplotlib.pyplot as plt

plt.scatter(*np.random.randn(2, 100), c=np.random.randn(100), s=np.random.rand(100)*100)
```

# Experiment with the demo notebook!

In the *`demo/`* folder for `jupytext` there is a notebook called **`World population.ipynb`**.
By default, saving the demo notebook will also create *many* possible Jupytext
outputs so you can see what each looks like and which you prefer.
