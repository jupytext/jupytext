#!/usr/bin/env bash
set -euo pipefail

sudo chown vscode:vscode .pixi /home/vscode/.codex
chmod 700 /home/vscode/.codex

# A backup from the old container can seed the new volume once. Never overwrite
# conversations already present in an existing volume.
backup="$(git rev-parse --git-common-dir)/jupytext-codex-history.tar.gz"
if [[ -f "$backup" ]] && [[ -z "$(find /home/vscode/.codex -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    tar -xzf "$backup" -C /home/vscode/.codex
fi

pixi install --locked
pixi run --locked python -m ipykernel install --name python_kernel --user
