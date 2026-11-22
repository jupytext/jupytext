---
title: "Notebooks as Markdown"
description: "The Markdown, MyST, Quarto and Pandoc notebook formats."
sidebar:
  order: 2
---

## MyST Markdown

[MyST (Markedly Structured Text)][myst-parser] is a markdown flavor that "implements the best parts of reStructuredText". It provides a way to call Sphinx directives and roles from within Markdown,
using a *slight* extension of CommonMark markdown.
[MyST-NB][myst-nb] and [Jupyter Book][jupyter-book] builds on this markdown flavor, to offer direct conversion of Jupyter Notebooks into Sphinx documents.

Similar to the jupytext Markdown format, MyST Markdown uses code blocks to contain code cells.
The difference though, is that the metadata is contained in a YAML block:

````md
```{code-cell} ipython3
---
other:
  more: true
tags: [hide-output, show-input]
---

print("Hallo!")
```
````

The `ipython3` here is purely optional, as an aide for syntax highlighting.
In the round-trip, it is copied from `notebook.metadata.language_info.pygments_lexer`.

Also, where possible the conversion will use the short-hand metadata format
(see the [MyST guide](https://myst-parser.readthedocs.io/en/latest/using/syntax.html#parameterizing-directives)):

````md
```{code-cell} ipython3
:tags: [hide-output, show-input]

print("Hallo!")
```
````

Raw cells are also represented in a similar fashion:

````md
```{raw-cell}
:raw_mimetype: text/html

<b>Bold text<b>
```
````

Markdown cells are not wrapped. If a markdown cell has metadata, or
directly proceeds another markdown cell, then a [block break] will be inserted
above it, with an (optional) single line JSON representation of the metadata:

```md
+++ {"slide": true}

This is a markdown cell with metadata

+++

This is a new markdown cell with no metadata
```

See for instance how our `World population.ipynb` notebook is [represented](https://github.com/jupytext/jupytext/blob/main/demo/World%20population.myst.md#) in the `myst` format.

**Note**: The `myst` format requires Python >= 3.6

**Tip**: You can use the [myst-highlight] VS Code extension to provide better syntax highlighting for this format.

[myst-parser]: https://myst-parser.readthedocs.io
[myst-nb]: https://myst-nb.readthedocs.io
[jupyter-book]: https://jupyterbook.org
[block break]: https://myst-parser.readthedocs.io/en/latest/using/syntax.html#block-breaks
[myst-highlight]: https://marketplace.visualstudio.com/items?itemName=ExecutableBookProject.myst-highlight

## Quarto

[Quarto](https://quarto.org/) is a scientific and technical publishing system built on Pandoc. If you have `quarto` installed, Jupytext lets you edit `.qmd` documents as notebooks in Jupyter, and pair `.ipynb` notebooks with `.qmd` notebooks.

The conversion from `.ipynb` to `.qmd` and back directly calls `quarto convert`, and consequently requires an installation of Quarto v0.2.134 or higher.

Note that the round trip of `.ipynb` to `.qmd` to `.ipynb` has the effect of concatenating consecutive Markdown cells and turning raw cells into Markdown cells (since `.qmd` files represent all content as either Markdown or code cells).

## R Markdown

[R Markdown](https://rmarkdown.rstudio.com/authoring_quick_tour.html) is [RStudio](https://www.rstudio.com/)'s format for notebooks, with support for R, Python, and many [other languages](https://bookdown.org/yihui/rmarkdown/language-engines.html).

Jupytext's implementation of R Markdown is very similar to that of the Markdown format. The major difference is on code cells, which use R Markdown's convention, i.e. the language and options are surrounded by curly brackets, and the cell metadata are encoded as R objects. For instance our cell with the `parameters` tags would be represented as:

    ```{python tags=c("parameters")}
    param = 5
    ```

Python and R notebooks represented in the R Markdown format can run both in Jupyter and RStudio. Note that you can change the default Python environment in RStudio with `RETICULATE_PYTHON` in a `.Renviron` file, see [here](https://github.com/jupytext/jupytext/issues/267#issuecomment-506994930).

See how our `World population.ipynb` notebook in the [demo folder](https://github.com/jupytext/jupytext/tree/main/demo) is represented in [R Markdown](https://github.com/jupytext/jupytext/blob/main/demo/World%20population.Rmd).

## Jupytext Markdown

Jupytext can save notebooks as [Markdown](https://daringfireball.net/projects/markdown/syntax) documents. This format is well adapted to tutorials, books, or more generally notebooks that contain more text than code. Notebooks represented in this form are well rendered by most Markdown editors or renderers, including GitHub.

Like all the Jupytext formats, Jupytext Markdown notebooks start with an (optional) YAML header. This header is used to store selected notebook metadata like the kernel information, together with Jupytext's format and version information.
```
---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.1.0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---
```

You can add custom notebook metadata like `author` or `title` under the `jupyter:` section, it will be synchronized with the notebook metadata.
And if you wish to export more metadata from the notebook, have a look at the paragraph on [metadata filtering](/reference/advanced-options/#metadata-filtering).

In the Markdown format, markdown cells are inserted verbatim and separated with two blank lines.

If you'd like that cell breaks also occurs on Markdown headers, add a `split_at_heading: true` entry in the `jupytext` section in the YAML header, or if you want that option to be the default for all Markdown documents in Jupyter, activate the option in the [`jupytext.toml` configuration file](/using/config/):

```
split_at_heading = true
```

Code cells are encoded using the classical triple backticks, followed by the notebook language. Cell metadata are appended after the language information, with a `key=value` syntax, where `value` is encoded in JSON format. For instance, in a Python notebook, a simple code cell with a `parameters` tag is represented as:

    ```python tags=["parameters"]
    param = 5
    ```

Code snippets are turned into code cells in Jupyter as soon as they have an explicit language, when that language is supported in Jupyter. Thus, you have a code snippet that you don't want to execute in Jupyter, you can either
- remove the language information,
- or, start the code snippet with a triple tilde, e.g. `~~~python`, instead of ` ```python`
- or, add an `active="md"` cell metadata, or a `.noeval` attribute after the language information, e.g. ` ```python .noeval `
- or, surround the code snippet with explicit Markdown cell markers (see below).

Raw cells are delimited with HTML comments, and accept cell metadata in the same key=value format:

    <!-- #raw -->
    raw text
    <!-- #endraw -->

    <!-- #raw key="value"-->
    raw cell with metadata
    <!-- #endraw -->

Markdown cells can also have explicit markers: use one of `<!-- #md -->` or `<!-- #markdown -->` or `<!-- #region -->` and the corresponding `<!-- #end... -->` counterpart. Note that the `<!-- #region -->` and `<!-- #endregion -->` cells markers are [foldable](https://code.visualstudio.com/docs/editor/codebasics#_folding) in VS Code, and that you can also insert a title there, e.g. `<!-- #region This is a title for my protected cell -->`. Cell metadata are accepted in the format `key="value"` (`"value"` being encoded in JSON) as for the other cell types.

For a concrete example, see how our `World population.ipynb` notebook in the [demo folder](https://github.com/jupytext/jupytext/tree/main/demo) is represented in [Markdown](https://github.com/jupytext/jupytext/blob/main/demo/World%20population.md#).

## Pandoc Markdown

Pandoc, the _Universal document converter_,  can read and write Jupyter notebooks - see [Pandoc's documentation](https://pandoc.org/MANUAL.html#creating-jupyter-notebooks-with-pandoc).

In Pandoc Markdown, all cells are marked with pandoc divs (`:::`). The format is therefore slightly more verbose than the Jupytext Markdown format.

See for instance how our `World population.ipynb` notebook is [represented](https://github.com/jupytext/jupytext/blob/main/demo/World%20population.pandoc.md#) in the `md:pandoc` format.

If you wish to use that format, please install `pandoc` in version 2.7.2 or above, with e.g. `conda install pandoc -c conda-forge`.

If you use Pandoc 3.10, upgrade to 3.10.1 or later. Pandoc 3.10 can truncate the format version in the Markdown metadata and prevent Jupytext from reopening paired notebooks. See [Jupytext issue #1545](https://github.com/jupytext/jupytext/issues/1545).

## Org Mode

**Org support is experimental.** Jupytext introduced Org format version `0.1` in version 1.20.1. Pairing with Org can lose content or metadata when saving or syncing. Check your files before pairing them, and keep a copy of the originals. See the list of [known Org issues](https://github.com/jupytext/jupytext/issues?q=state%3Aopen%20label%3A%22org-format%22).

[Org mode](https://orgmode.org/) is a major mode for Emacs widely used for note-taking and literate programming.
Jupytext can read and write Jupyter notebooks as Org-mode (`.org`) files using Pandoc as a conversion backend.
Keep the original file when converting a notebook or Org document and review the converted file before replacing the original.

Code cells are represented as `#+BEGIN_SRC jupyter-<language> ... #+END_SRC` blocks. Pandoc imports ordinary source blocks such as `#+BEGIN_SRC python` as fenced code in Markdown cells. The kernel metadata are recorded as top-level `#+PROPERTY: header-args` lines in the Org output, e.g.

```org
#+JUPYTER_KERNEL_DISPLAY_NAME: Python 3
#+PROPERTY: header-args:jupyter-python :kernel python3
#+PROPERTY: header-args:jupyter-python+ :session python3
```

Jupytext stores document-wide Babel properties in notebook metadata under `org_babel.header_args`. In Markdown-like formats this appears under `jupyter.org_babel`. Language-specific properties use the Org language name as the key, and a property that applies to all languages uses an empty key.
Repeated `:var` values are stored as a list in their original order.

```yaml
jupyter:
  org_babel:
    header_args:
      jupyter-python:
        session: python3
```

Current limitations

- Cell metadata is not preserved in the Org representation.
- Consecutive Markdown cells are concatenated on round-trip, since Org prose has no native cell-boundary markers.
- Pandoc can write Markdown cell IDs as Org targets, which come back as HTML anchors in Markdown.
- Raw cells are not preserved by the current Pandoc-based conversion path.
- Org headers store the kernelspec and document-wide Babel properties. Other notebook metadata is absent from the Org representation.
- Org comments and block- or subtree-level Babel settings can be lost on conversion.
- Embedded notebook attachments cannot be exported to Org.
- Org conversion stops with an error if Pandoc takes longer than 30 seconds.

Run a [round-trip test](/using/cli/#testing-the-round-trip-conversion) from the file you plan to pair.

```bash
jupytext --test --to org notebook.ipynb
jupytext --test --to ipynb notebook.org
```

These commands report differences without writing either file. Use `--test-strict` for a stricter comparison. For notebook inputs, the comparison covers cell content and metadata and ignores outputs and cell IDs.

To sync by passing the `.org` path, declare `formats = "ipynb,org"` in `jupytext.toml`.

Install Pandoc 3.4 or later to use the Org format.

```bash
jupytext --to org notebook.ipynb
jupytext --to ipynb notebook.org
```
