---
title: "Advanced options"
description: "Metadata filtering, custom cell markers and other advanced settings."
sidebar:
  order: 1
---

## Metadata filtering

The metadata that is included in the text notebooks is governed by the two options `notebook_metadata_filter` and `cell_metadata_filter`. The default value for these options are
- `notebook_metadata_filter="kernelspec,jupytext"`, i.e. by default, only the Jupytext and the kernel metadata are included:
- `cell_metadata_filter=all,-autoscroll,-collapsed,-scrolled,-trusted,-ExecuteTime`, i.e. by default all the cell metadata are included, except those listed with a negative sign.

Suppose you want to keep all the notebook metadata but `widgets` and `varInspector` in the YAML header, and that for cell metadata, you want to allow `ExecuteTime` and `autoscroll`, but not `hide_output`. Then, you could either add
```python
notebook_metadata_filter="all,-widgets,-varInspector"
cell_metadata_filter="ExecuteTime,autoscroll,-hide_output"
```
to your [`jupytext.toml`](/using/config/) file, or set these options for one notebook using the [Jupytext CLI](/using/cli/) with
```
jupytext --opt notebook_metadata_filter=all,-widgets,-varInspector --opt cell_metadata_filter=ExecuteTime,autoscroll,-hide_output notebook.py
```

If you wanted no notebook or cell metadata at all in the text notebooks, you could add this to your [`jupytext.toml`](/using/config/) file:
```python
notebook_metadata_filter="-all"
cell_metadata_filter="-all"
```

It is possible to filter nested metadata - use a dot to represent the nested fields. For example, if you wanted to include the Jupytext metadata, but not the Jupytext version number, you can use:
```python
notebook_metadata_filter="-jupytext.text_representation.jupytext_version"
```

Finally, note that you can _hide_ the notebook metadata in an HTML comment in `.md` files - just set `hide_notebook_metadata=true` either at the command line or in the `jupytext.toml` file.

## Magic commands

In the `percent` and `light` script formats, magic commands (Jupyter commands prefixed by `%` or `%%`) are commented out in scripts. You can change this by using the `comment_magics` option, either in the `jupytext.toml` file or at the command line with `jupytext --opt`.

## Custom language magics

In Markdown and R Markdown notebooks, code blocks in languages with built-in Jupyter magic support (e.g. `javascript`, `bash`, `sql`) are automatically converted to code cells using the corresponding `%%language` magic. However, code blocks in languages not covered by built-in magics remain as Markdown cells by default.

If you have written custom Jupyter magics for additional languages, you can tell Jupytext about them using the `custom_language_magics` option. For example, if you have custom `%%jsx` and `%%tsx` magics, add the following to your [`jupytext.toml`](config.md) file:

```toml
custom_language_magics = "jsx,tsx"
```

With this option set, Markdown code blocks like:

````markdown
```jsx
const Hello = () => (<b>Hello</b>);
```
````

will be converted to code cells with the `%%jsx` magic:

```
%%jsx
const Hello = () => (<b>Hello</b>);
```

## Active and inactive cells

You might want to make some cell active only when the notebook is run in Jupyter, or active only when the `.py` file is interpreted by Python. To do so, add an `active-ipynb` tag to the cells that should only be executed in the `.ipynb` file, and an `active-py` tag to the cells that should be executed only in the Python script.

## More options

There are a couple more options available - please have a look at the `JupytextConfiguration` class in [config.py](https://github.com/jupytext/jupytext/blob/main/src/jupytext/config.py).
