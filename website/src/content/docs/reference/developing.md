---
title: "Developing Jupytext"
description: "Set up a development environment for Jupytext."
sidebar:
  order: 5
---

## How to test development versions from GitHub

If you want to test a feature that has been integrated in `main` but not delivered yet to `pip` or `conda`, use
```
HATCH_BUILD_HOOKS_ENABLE=true pip install git+https://github.com/jupytext/jupytext.git
```

The above requires `node`. You can install it with e.g.
```
conda install 'nodejs>=20' -c conda-forge
```

Alternatively you can build only Jupytext core (e.g. skip the JupyterLab extension). To do so, remove `HATCH_BUILD_HOOKS_ENABLE=true` in the above.

Finally, if you want to test a development branch, use
```
HATCH_BUILD_HOOKS_ENABLE=true pip install git+https://github.com/jupytext/jupytext.git@branch
```
where `branch` is the name of the branch you want to test.

## Using our VS Code development container

Our development container is a convenient alternative to installing Pixi on your host machine. You need [VS Code](https://code.visualstudio.com/), the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), and a container engine, either `podman` or `docker`. Pixi runs inside the container, so you do not need to install it on your host.

You can open a local clone by opening the Jupytext repository in VS Code and running **Dev Containers: Reopen in Container** from the Command Palette. For a fresh clone, run **Dev Containers: Clone Repository in Container Volume...** and enter `jupytext/jupytext`. VS Code clones the repository and builds its development container. The first build may take a few minutes.

Once the container is ready, initialize the Pixi environment with `pixi install`. Run commands with `pixi run <command>`, or activate the environment with `pixi shell`. The container also installs the Pyright and OpenAI Codex VS Code extensions.

## Installing and developing Jupytext locally with Pixi

Most of Jupytext's code is written in Python. To develop the Python part of Jupytext, you should clone Jupytext, then create a dedicated Python environment with [Pixi](https://pixi.sh):
```
pixi shell
```

Install the `jupytext` package in development mode with
```
HATCH_BUILD_HOOKS_ENABLE=true pip install -e '.[dev]'
```

We use the [pre-commit](https://pre-commit.com) package to run pre-commit scripts like `black` and `ruff` on the code.
Install it with
```
pre-commit install
```

Tests are executed with `pytest`. You can run them in parallel with for instance
```
pytest -n 5
```

Some tests require a Jupyter kernel pointing to the current environment:
```
python -m ipykernel install --name python_kernel --user
```

## Jupytext's extension for JupyterLab

Our extension for JupyterLab adds a series of Jupytext commands to JupyterLab. The code is in `packages/labextension`. See the `README.md` there for instructions on how to develop that extension.

## Jupytext's website

You can start a local dev server with:
```bash
pixi shell
cd website
npm install
npm run dev
```
