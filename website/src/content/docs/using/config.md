---
title: "Jupytext's configuration file"
description: "Configure Jupytext for a whole project with jupytext.toml."
sidebar:
  order: 4
---

Jupytext can use either `jupytext.toml` or `pyproject.toml` as its configuration file.

## Global pairing

To [pair](/using/paired-notebooks/) all the notebooks in the current folder and subfolders, all you need to do is to create a `jupytext.toml` file with this content:

```
# Pair ipynb notebooks to py:percent text notebooks
formats = "ipynb,py:percent"
```

With the above configuration, saving `notebook.ipynb` (or `notebook.py`) in Jupyter will have the effect to update both `notebook.ipynb` and `notebook.py` on disk.

You can use other text formats like `md`, `md:myst`, `Rmd` or `qmd`. The percent format is available for many languages. Use `auto:percent` to infer the file extension from the programmation language used in the notebook.

You can also configure Jupytext in a `pyproject.toml` config file rather than `jupytext.toml`. In that case, a sample configuration would be:
```
[tool.jupytext]
formats = "ipynb,py:percent"
```

## Pairing in subfolders

If you want to store your `.ipynb` notebooks in a `notebooks` folder, and their `.py` representation in a `scripts` folder, you can use this `jupytext.toml` configuration:
```
[formats]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
```

or this `pyproject.toml` configuration:
```
[tool.jupytext.formats]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
```

The `notebook/` prefix above is matched with the top-most parent folder of the matching name, not above the Jupytext configuration file.

## Pairing with multiple format specifications

You can define different pairing configurations for specific subsets of notebooks by using a list of format dictionaries. This is useful when you want to apply different pairing rules to notebooks in different locations, such as generating documentation markdown files only for tutorial notebooks.

Since Jupytext v1.18.0, the `formats` option can be a list of format dictionaries, where the first matching format is used for each notebook.

Here's an example that pairs tutorial notebooks to markdown documentation files, and all other notebooks to Python scripts:

```toml
# jupytext.toml

# Tutorial notebooks get paired to markdown docs
[[formats]]
"notebooks/tutorials/" = "ipynb"
"docs/tutorials/" = "md"
"scripts/tutorials/" = "py:percent"

# Default pairing: all other notebooks are paired with Python scripts
[[formats]]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
```

With this configuration:
- Tutorial notebooks like `notebooks/tutorials/getting_started.ipynb` are paired with:
  - `docs/tutorials/getting_started.md`
  - `scripts/tutorials/getting_started.py`
- Regular notebooks like `notebooks/hello.ipynb` are paired with `scripts/hello.py`

You can define multiple format specifications for different subsets:

```toml
# Tutorial notebooks
[[formats]]
"notebooks/tutorials/" = "ipynb"
"docs/tutorials/" = "md"

# Example notebooks with MyST format
[[formats]]
"notebooks/examples/" = "ipynb"
"docs/examples/" = "md:myst"

# Default for all other notebooks
[[formats]]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
```

The first format specification that matches the notebook path is used. It's recommended to put more specific paths first and the default/catch-all formats last.

### Alternative syntaxes

You can also use a semicolon-separated string for a more compact notation:

```toml
# jupytext.toml
formats = "notebooks///ipynb,scripts///py:percent;ipynb,py:percent"
```

Or a TOML list with string format specifications:

```toml
# jupytext.toml
formats = [
    "notebooks///ipynb,scripts///py:percent",
    "ipynb,py:percent"
]
```

In `pyproject.toml`, the configuration would be:
```toml
[[tool.jupytext.formats]]
"notebooks/tutorials/" = "ipynb"
"docs/tutorials/" = "md"

[[tool.jupytext.formats]]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
```


## Global pairing vs individual pairing

Alternatively, notebooks can be paired individually using either the Jupytext commands in JupyterLab, or the command line interface:

```bash
jupytext --set-formats ipynb,py:percent notebook.ipynb
```

The individual pairing takes precedence over the global pairing. You can disable the global pairing for an individual notebook by setting formats to a single format:
```bash
jupytext --set-formats ipynb notebook.ipynb
```

Please note that, while Jupytext is Jupyter acts accordingly to both local or global Jupytext configuration files, the Jupyter commands in JupyterLab and the Jupytext menu in Jupyter only display the pairing information set in the notebooks itself and are not aware of the global configuration ([#177](https://github.com/jupytext/jupytext/issues/177)).

## Possible locations for the Jupytext configuration files

The Jupytext configuration file(s) should be either in the local or a parent directory, or in any directory listed in
```python
from jupytext.config import global_jupytext_configuration_directories
list(global_jupytext_configuration_directories())
```
which include `XDG_CONFIG_HOME` (defaults to `$HOME/.config`) and `XDG_CONFIG_DIR`.

The name for the configuration file can be any of `jupytext.config.JUPYTEXT_CONFIG_FILES`, i.e. `.jupytext` (in TOML),
`jupytext.toml`, `jupytext.yml`, `jupytext.yaml`, `jupytext.json` or `jupytext.py` (dot-files
like `.jupytext.toml` are accepted by the CLI version of Jupytext, but are not effective in Jupyter).

As mentionned above, you can also use your Python project's `pyproject.toml` file.

If you want to know, for a given directory, which configuration file is used by Jupytext, run this in a Python shell:
```python
from jupytext.config import find_jupytext_configuration_file
find_jupytext_configuration_file('.')
```

If you want to limit the search for a configuration file to a given parent directory, you can create an empty `.jupytext` configuration file in that directory. Alternatively, you can set the search boundaries with an environment variable `JUPYTEXT_CEILING_DIRECTORIES` - a colon-separated list of absolute paths.

If `JUPYTEXT_CEILING_DIRECTORIES` is defined, Jupytext will stop searching for configuration files when it meets one of these path. This can be helpful to avoid searching for configuration files on slow filesystems. It can also be useful if you don't want to use a global configuration - for instance, when running `pytest` on Jupytext, we use `JUPYTEXT_CEILING_DIRECTORIES="/tmp"`.
