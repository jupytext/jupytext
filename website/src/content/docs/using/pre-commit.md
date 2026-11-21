---
title: "Pre-commit hook"
description: "Keep paired notebooks in sync automatically with pre-commit hooks."
sidebar:
  order: 3
---

Jupytext includes a hook for the [pre-commit](https://pre-commit.com/) framework.

## Do I need to use this hook?

You don't need Jupytext's pre-commit hook if you commit only the `.py` (or `.md`) representation of notebooks in your Git repository.

In that case, a possible pre-commit `.pre-commit-config.yaml` configuration that works well with `.py:percent` notebooks (and does not include a `jupytext` pre-commit hook!) is the following:

```yaml
repos:
- repo: https://github.com/pycqa/isort
    rev: 5.11.2
    hooks:
    - id: isort
      args: [--treat-comment-as-code, "# %%", --float-to-top]

- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.0.275
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]

- repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    - id: black
      language_version: python3
```

## What is the point of having a `jupytext` pre-commit hook?

Jupyter keeps paired `.py` and `.ipynb` files in sync, but the synchronization happens only when you _save_ the notebook in Jupyter. If you edit the `.py` file manually, then the `.ipynb` file will be outdated until you reload and save the notebook in Jupyter, or execute `jupytext --sync`.

Jupytext's pre-commit hook can enforce this synchronization on commits:
```yaml
repos:
-   repo: https://github.com/jupytext/jupytext
    rev: v1.14.7  # CURRENT_TAG/COMMIT_HASH
    hooks:
    - id: jupytext
      args: [--sync]
```

If you combine Jupytext with other pre-commit hooks, you must ensure that all hooks will pass on any files you generate. For example, if you have a hook for using `black` to format all your python code, then you should use Jupytext's `--pipe` option to also format newly generated Python scripts before writing them:

```yaml
repos:
-   repo: https://github.com/jupytext/jupytext
    rev: v1.14.7  # CURRENT_TAG/COMMIT_HASH
    hooks:
    - id: jupytext
      args: [--sync, --pipe, black]
      additional_dependencies:
        - black==23.3.0 # Matches hook

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    - id: black
      language_version: python3
```

Tested examples of how to use the pre-commit hook are available in our [tests](https://github.com/jupytext/jupytext/tree/main/tests/external/pre_commit) -
see for instance [test_pre_commit_1_sync_with_config.py](https://github.com/jupytext/jupytext/blob/main/tests/external/pre_commit/test_pre_commit_1_sync_with_config.py).
