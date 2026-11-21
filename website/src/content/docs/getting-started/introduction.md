---
title: "Introduction"
description: "Jupytext lets you save Jupyter notebooks as plain text files — easy to edit, version control and refactor with AI."
sidebar:
  order: 1
---

Have you always wished Jupyter notebooks were plain text documents? Wished you could edit them in
your favorite IDE? And get clear, meaningful diffs when doing version control? Then **Jupytext** may
well be the tool you're looking for!

Jupytext can save Jupyter notebooks as text files — for instance with a `.py` or `.md` extension —
and open them again as notebooks. A text notebook contains only your inputs (and selected metadata),
so it is:

- **easy to version control** — clean, line-by-line diffs instead of unreadable JSON;
- **easy to edit** — open and refactor it in VS Code, PyCharm, Spyder, vim, or any editor;
- **easy to share and reuse** — a Python text notebook is also an importable module or a script;
- **easy for AI assistants** — tools like Claude, GitHub Copilot and Cursor read and edit plain text
  directly, so they can refactor your notebooks with no JSON wrangling.

## How it works

You have two complementary ways to use Jupytext.

### Text notebooks

A [text notebook](/getting-started/text-notebooks/) is a script or Markdown document that you open
and run as a notebook. It contains the inputs only — no outputs — which makes it perfect for version
control. This is the lightest setup: a single text file is your notebook.

### Paired notebooks

A [paired notebook](/using/paired-notebooks/) is a pair of files — a classic `.ipynb` (which keeps
your rich outputs) plus a text file like `.py` or `.md` (which is clean and reviewable). Jupytext
keeps the two in sync every time you save. You commit the text file, and your outputs stay safe in
the `.ipynb`.

## A 60-second tour

Install Jupytext:

```bash
pip install jupytext
```
and **restart** your Jupyter server.

Convert a notebook to a text file (and back):

```bash
jupytext --to py:percent notebook.ipynb      # notebook.ipynb -> notebook.py
jupytext --to notebook notebook.py           # notebook.py    -> notebook.ipynb
jupytext --to notebook notebook.py --update  # preserve existing outputs
```

Pair one notebook so both representations stay in sync on every save:

```bash
jupytext --set-formats ipynb,py:percent notebook.ipynb
```

Or pair every notebook in your project by adding a [`jupytext.toml`](/using/config/) file:

```toml
formats = "ipynb,py:percent"
```

## When does synchronization happen?

Synchronization is triggered in three situations:

1. **Jupyter** — inputs are loaded from the text notebook and combined (in memory) with outputs from the `.ipynb` notebook. Both files are updated on save.
2. **`jupytext --sync`** — both files are updated using inputs from the most recently modified file (outputs always come from the `.ipynb` notebook).
3. **VS Code** with the [Jupytext Sync](https://marketplace.visualstudio.com/items?itemName=caenrigen.jupytext-sync) extension — both files are updated on every save.


## Where to next

- [Install Jupytext](/getting-started/install/) and learn about the tools it ships with.
- Understand [text notebooks](/getting-started/text-notebooks/) and [paired notebooks](/using/paired-notebooks/).
- Choose a format: [scripts](/formats/scripts/) (percent / light) or [Markdown](/formats/markdown/) (MyST, Quarto, Pandoc).
- Drive everything from the [command line](/using/cli/) or a [pre-commit hook](/using/pre-commit/).
- See the [FAQ](/reference/faq/) for common questions.
