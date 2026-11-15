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

The container uses Linux AMD64. Native ARM containers are not supported; ARM hosts need a container engine configured for AMD64 emulation.

The container automatically installs the dependencies from `pixi.lock` with `pixi install --locked` and registers the `python_kernel` Jupyter kernel used by the tests. The Pixi environment is stored in a dedicated container volume, separate from any environment on your host. If you change the dependencies, run `pixi install` to update the lockfile.

VS Code uses the Pixi Python interpreter and enables pytest discovery in the Test Explorer. The container installs the Python, Pyright, Ruff, and OpenAI Codex extensions. Pyright provides the Python language server, and Ruff provides linting and formatting.

### Codex history and container rebuilds

The container installs the OpenAI Codex extension and excludes `anthropic.claude-code` from automatic extension installation. Codex stores its local state in `/home/vscode/.codex`, backed by a dedicated container volume. Rebuilding the same container preserves this volume; deleting its volumes deletes that history.

Before migrating an existing container to this configuration, close Codex and back up its state from a terminal in the old container:

```bash
umask 077
tar -czf "$(git rev-parse --git-common-dir)/jupytext-codex-history.tar.gz" -C "$HOME/.codex" .
```

This private archive can include credentials. Keep it out of version control and do not share it. On creation, the container restores this archive only if the Codex volume is empty. Existing volume contents are never overwritten. Keep the backup until you have verified your conversations after the rebuild.

A container volume is local to its container host. To access the same local Codex conversations from another computer, reconnect to that host and container (for example, using VS Code Remote SSH), with the same workspace path and account. A fresh container on a different host does not synchronize local Codex history merely by signing in. To move hosts, stop Codex, transfer the private backup securely, and restore it into an empty Codex volume before opening Codex. Do not synchronize a live SQLite database between computers.

### GitHub CLI authentication

The container includes `gh` and forwards the host's `GH_TOKEN` environment variable to VS Code and its subprocesses.
Retrieve the token from your host's credential store before starting VS Code. For example, if `gh` on the host is
already authenticated using a secure system keyring, run this in a host terminal:

```bash
GH_TOKEN="$(gh auth token --hostname github.com)" code .
```

Fully quit existing VS Code instances first so the new process inherits the variable. Rebuild the container after
changing its configuration. In a new container terminal, `gh auth status` should report authentication via `GH_TOKEN`.
You do not need to run `gh auth login` in the container. The token is available to processes in that VS Code session;
do not print it or put it in project files, shell startup files, or the container image.

If you previously logged in inside the container and `gh` fell back to plaintext storage, remove that saved login
with `gh auth logout --hostname github.com` before relying on injection. If `GH_TOKEN` is already set, run
`env -u GH_TOKEN -u GITHUB_TOKEN gh auth logout --hostname github.com` to remove the stored login. This removes the
local credential without revoking the token on GitHub. Verify injection works before discarding your only copy.

### Startup warnings

The container excludes `.pixi` and `node_modules` from VS Code file watching and uses the configured Pixi interpreter without the separate Python Environments discovery extension. If VS Code still reports `ENOSPC` or “System limit for number of file watchers reached”, increase the inotify limits on the Linux container host (or the Linux VM running your container engine):

```bash
sudo tee /etc/sysctl.d/99-jupytext-inotify.conf <<'EOF'
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=1024
EOF
sudo sysctl --system
```

Then reload VS Code. These are host kernel limits; changing the container image does not reliably change them.

Run commands with `pixi run <command>`, or activate the environment with `pixi shell`. To launch JupyterLab, run `pixi run jupyter lab`; its port `8888` is forwarded to your host. The website development server's port `4321` is also forwarded.

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
