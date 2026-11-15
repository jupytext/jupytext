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

### Concurrent edits to paired files

Opening both members of a pair (for example, `demo.ipynb` as a notebook and
`demo.py` in a text editor) creates separate live documents. Saving either member
can rewrite the other file. With Jupyter Collaboration, that disk change can
replace unsaved edits in the other live document without a warning
([#1648](https://github.com/jupytext/jupytext/issues/1648)). Avoid editing both
members of a pair at the same time. Keep a copy of unsaved work before reloading.

Jupytext's contents manager checks the modification times of paired files before
saving. If an existing twin has changed on disk since the notebook was last loaded or
successfully saved through that contents manager, the save is refused with HTTP
409 before any member of the pair is written. This also covers a script saved by
an external editor or an AI assistant. Save a separate copy of your unsaved edits,
reload the notebook, then reconcile the two versions before saving again.

This is a limited safeguard, not a solution for real-time collaboration between
paired files. It cannot see edits that exist only in another live document, and
it does not merge changes. It relies on modification times and an earlier load or
save in the same contents manager; it cannot detect changes that preserve those
times, changes made during the save, or edits predating that earlier load or save.
The baseline is shared per notebook path in the contents manager: a full reload
of that path, including by another client, refreshes it. Metadata-only polling
does not reset the check. Deleted twins can still be recreated on save. The
command-line interface is unaffected.
