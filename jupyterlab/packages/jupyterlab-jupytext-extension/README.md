# A JupyterLab extension for Jupytext

This extension adds a few [Jupytext](https://github.com/jupytext/jupytext) commands to the command palette. Use these to select the desired ipynb/text pairing for your notebook.

The latest version for this extension is [![npm version](https://badge.fury.io/js/jupyterlab-jupytext.svg)](https://badge.fury.io/js/jupyterlab-jupytext).

Most users do not need to install this extension, since it is already included in the latest [jupytext](https://github.com/jupytext/jupytext/), both on [![Pypi](https://img.shields.io/pypi/v/jupytext.svg)](https://pypi.python.org/pypi/jupytext) and
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/jupytext.svg)](https://anaconda.org/conda-forge/jupytext).

![](https://raw.githubusercontent.com/jupytext/jupytext/main/packages/labextension/jupytext_commands.png)

## Installation

Please install [Jupytext](https://github.com/jupytext/jupytext/blob/main/README.md#Install) first. As mentioned above, both the `pip` and `conda` packages do include the latest version of the JupyterLab extension, so in most cases you don't need to specifically install this `npm` package.

In case you're not using JupyterLab 4.x, you will have to install an older version of the extension that is compatible with your version. Please first install `jupytext` using `pip` or `conda`, and then downgrade the extension to a version compatible with your version of JupyterLab with:

```bash
jupyter labextension install jupyterlab-jupytext@1.3.11  # for JupyterLab 3.x
jupyter labextension install jupyterlab-jupytext@1.2.2  # for JupyterLab 2.x
jupyter labextension install jupyterlab-jupytext@1.1.1  # for JupyterLab 1.x
```

# How to develop this extension

For fine-grained access to the `jlpm` command and various build steps:

```bash
pip install -e '.[dev]'
cd jupyterlab/packages/jupyterlab-jupytext-extension
jlpm
jlpm install:extension     # Symlink into `{sys.prefix}/share/jupyter/labextensions`
```

(see also the instructions at [developing.md](../../../docs/developing.md) on how to create a Python environment with a recent version of `nodejs`)

Watch the source directory and automatically rebuild the `lib` folder:

```bash
cd jupyterlab/packages/jupyterlab-jupytext-extension
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

While running `jlpm watch`, every saved change to a `.ts` file will immediately be
built locally and available in your running Jupyter client. "Hard" refresh JupyterLab or Notebook
with <kbd>CTRL-F5</kbd> or <kbd>⌘-F5</kbd> to load the change in your browser
(you may need to wait several seconds for the extension to be fully rebuilt).

Read more on this on the [JupyterLab documentation](https://jupyterlab.readthedocs.io/en/latest/extension/extension_dev.html#developing-a-prebuilt-extension).

# How to publish a new version of the extension on npm

Please note that the main purpose of updating the extension on [npm](https://www.npmjs.com) is to keep the npm documentation up-to-date, since the extension is made available within the Python package itself.

Make sure you have `nodejs>=18` installed, bump the version in `package.json`, and then:

```bash
cd jupyterlab/packages/jupyterlab-jupytext-extension

# Package the extension
npm pack

# Test the extension locally
jupyter labextension install jupyterlab-jupytext-xxx.tgz

# Publish the package on npm with
npm publish --access=public
```
