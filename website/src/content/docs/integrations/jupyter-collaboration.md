---
title: "Jupyter Collaboration"
description: "Use Jupytext with Jupyter's real-time collaboration."
sidebar:
  order: 2
---

[Jupyter Collaboration](https://github.com/jupyterlab/jupyter-collaboration) is an official Jupyter extension that enables real-time collaboration in JupyterLab.

## Autoreload Feature

Beyond its collaboration features, Jupyter Collaboration also provides automatic file reloading. When the extension is installed, JupyterLab auto-reloads any file that gets modified on disk. This way, you can edit your notebook and text files outside of Jupyter, and the changes appear in Jupyter automatically without having to manually reload the document.

Note that Jupyter Collaboration also comes with an auto-save feature. By [default](https://github.com/jupyterlab/jupyter-collaboration/blob/67453e04dad30978d42fdef07040ae94cabe2bf0/projects/jupyter-server-ydoc/jupyter_server_ydoc/app.py#L45-L84), notebooks and text documents are saved one second after your last change.

## Collaborating on text notebooks

Currently, the real-time collaboration feature can be used:
- in the notebook editor when opening `.ipynb` notebooks
- in the text editor when opening `.py` or `.md` files

However, it does not yet work on `.py` and `.md` files opened as notebooks. If you want to collaborate on text notebooks, we recommend that you collaborate on paired notebooks (see [#1432](https://github.com/jupytext/jupytext/issues/1432)).

## Known issues

While using Jupytext and Jupyter Collaboration together mostly works, we have noticed a few side effects. Please review the list of [known issues](https://github.com/jupytext/jupytext/issues?q=state%3Aopen%20label%3A%22jupyter-collaboration%22) and make sure that you are comfortable with these.
