# Agent instructions for Jupytext

## Working preferences

- Make changes in a dedicated Git worktree on a task-specific branch. Reuse the
  worktree for the current task rather than editing the user's original checkout.
- Check Git status before starting and preserve existing changes. Report the
  worktree and branch, what changed, the checks run, and any validation limits.
- Keep this file updated with explicitly agreed preferences and established
  project conventions. Current user instructions take precedence; update stale
  guidance when requirements change.

## Development workflow

- Use the Pixi environments defined in `pyproject.toml`. Initialize them with
  `pixi install --locked`, and run tools through `pixi run` or `pixi shell`.
- When intentionally changing dependencies, run `pixi install` and include the
  resulting `pixi.lock` changes. Routine setup and CI should use the lockfile.
- Preserve compatibility with the Python versions declared in `pyproject.toml`.
- Python code lives in `src/`, tests in `tests/`, the JupyterLab extension in
  `jupyterlab/`, and the current documentation in `website/src/content/docs/`.
  Follow [developing](website/src/content/docs/reference/developing.md) and
  [contributing](website/src/content/docs/reference/contributing.md) for details.
- Preserve the text representations of notebook fixtures and examples. Respect
  the exclusions in `.pre-commit-config.yaml`, including generated synchronous
  modules; make changes to their source rather than hand-editing generated code.

## Validation

- Run tests relevant to the change through Pixi, for example
  `pixi run pytest tests/unit` or a specific test file or test case. Broaden the
  checks when the change affects multiple areas.
- Tests that execute notebooks require the current environment's Jupyter kernel:
  `pixi run python -m ipykernel install --name python_kernel --user`.
  Check for unexpected skips when validating notebook execution.
- Use the existing Ruff and pre-commit configuration. Run hooks on changed files
  with `pixi run pre-commit run --files <paths>`. The JupyterLab lint hook needs
  Node and `jlpm` from Pixi; run Git commits through Pixi when hooks are installed.
- Build the JupyterLab extension with
  `pixi run -e build build-labextension` when that part of the project changes.
- Follow the existing CI workflow structure and pin GitHub Actions to full commit
  SHAs. Keep required jobs included in the final `pass` job's dependencies.
- Describe checks that actually ran. When a container engine is unavailable,
  distinguish local setup and smoke checks from a complete container build.

## Dev container conventions

- Keep `.devcontainer/devcontainer.json` valid strict JSON, without comments, so
  it passes the repository's `check-json` hook.
- Use Linux AMD64 for both builds and runs. Native ARM containers are currently
  outside the supported scope; ARM hosts require AMD64 emulation.
- Install dependencies automatically with `pixi install --locked`, register
  `python_kernel`, and keep `.pixi` in a dedicated container volume.
- Configure Python, Pyright, pytest discovery, and Ruff around the Pixi default
  interpreter. Use Pyright as the language server and Ruff for linting/formatting.
- Maintain a CI smoke check that builds the configured container and verifies
  the editable package, kernel registration, and notebook execution.
