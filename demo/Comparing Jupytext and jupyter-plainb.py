# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5.dev0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Comparing Jupytext and jupyter-plainb
#
# [jupyter-plainb](https://github.com/notebook-link/jupyter-plainb) is a JupyterLab/JupyterLite
# extension that converts plain text files to notebooks, using the parsers from the
# [`plainb`](https://github.com/notebook-link/plainb) npm package. It supports a subset of the
# formats that Jupytext supports: the percent format, Sphinx-Gallery scripts, classic Markdown,
# and MyST Markdown.
#
# This notebook checks how closely `plainb`'s parsers agree with Jupytext's own parsers, using
# Jupytext's *mirror files* as the reference corpus: `tests/data/notebooks/outputs/` contains,
# for every test notebook, the text representation that Jupytext itself produces in each format.
# Since `plainb` has no Python bindings, we drive it from a small Node.js CLI
# (`demo/plainb_compare/convert.mjs`) and compare its output, cell by cell, to what
# `jupytext.read()` produces for the same file.
#
# Run `npm install` in `demo/plainb_compare/` once before running this notebook (the cell below
# does this automatically if needed). A `nodejs` environment is provided by this repo's pixi
# environment.

# %%
import json
import subprocess
from pathlib import Path

import jupytext

REPO_ROOT = Path(jupytext.__file__).resolve().parents[2]
BRIDGE_DIR = REPO_ROOT / "demo" / "plainb_compare"
CONVERT_JS = BRIDGE_DIR / "convert.mjs"
MIRRORS_ROOT = REPO_ROOT / "tests" / "data" / "notebooks" / "outputs"

# mirror directory -> (jupytext format used to write it, matching plainb parser)
FORMAT_MAP = {
    "ipynb_to_percent": ("auto:percent", "parsePy"),
    "ipynb_to_sphinx": ("py:sphinx", "parseSphinxGallery"),
    "ipynb_to_myst": ("md:myst", "parseMystMd"),
    "ipynb_to_md": ("md", "parseClassicMd"),
}

if not (BRIDGE_DIR / "node_modules").exists():
    subprocess.run(["npm", "install"], cwd=BRIDGE_DIR, check=True)

# %% [markdown]
# ## Helpers
#
# `run_plainb` shells out to Node for a single file. `cell_source` normalizes a cell's source to
# a plain string, since `plainb` stores it as a list of lines (nbformat's on-disk convention)
# while `jupytext.read()` returns a single string per cell.


# %%
def run_plainb(parser: str, path: Path) -> tuple[dict | None, str | None]:
    proc = subprocess.run(
        ["node", str(CONVERT_JS), parser, str(path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None, proc.stderr.strip()
    return json.loads(proc.stdout), None


def cell_source(source) -> str:
    return "".join(source) if isinstance(source, list) else source


def compare_file(mirror_dir: str, filename: str, jupytext_fmt: str, plainb_parser: str) -> dict:
    path = MIRRORS_ROOT / mirror_dir / filename
    row = dict(mirror_dir=mirror_dir, file=filename)

    try:
        jt_nb = jupytext.read(path, fmt=jupytext_fmt)
    except Exception as exc:  # jupytext itself fails to read its own mirror: report, don't crash
        return {**row, "error": f"jupytext: {exc}"}

    pb_nb, error = run_plainb(plainb_parser, path)
    if error:
        return {**row, "error": f"plainb: {error}"}

    jt_cells = [(c.cell_type, c.source) for c in jt_nb.cells]
    pb_cells = [(c["cell_type"], cell_source(c["source"])) for c in pb_nb["cells"]]

    same_length = len(jt_cells) == len(pb_cells)
    type_match = same_length and all(a[0] == b[0] for a, b in zip(jt_cells, pb_cells))
    source_match = same_length and all(a[1] == b[1] for a, b in zip(jt_cells, pb_cells))

    first_diff = None
    if same_length and not source_match:
        first_diff = next(i for i, (a, b) in enumerate(zip(jt_cells, pb_cells)) if a != b)

    return {
        **row,
        "error": None,
        "jt_cells": len(jt_cells),
        "pb_cells": len(pb_cells),
        "same_length": same_length,
        "type_match": type_match,
        "source_match": source_match,
        "first_diff_cell": first_diff,
    }


# %% [markdown]
# ## Run the comparison over every mirror file

# %%
results = [
    compare_file(mirror_dir, path.name, jupytext_fmt, plainb_parser)
    for mirror_dir, (jupytext_fmt, plainb_parser) in FORMAT_MAP.items()
    for path in sorted((MIRRORS_ROOT / mirror_dir).iterdir())
]
len(results)

# %% [markdown]
# ## Agreement rate by format
#
# `source_match` requires the two implementations to agree on cell count, cell type, and cell
# source, in order, for every cell in the file. It is a strict, cell-exact agreement measure.

# %%
by_dir: dict[str, list[dict]] = {}
for row in results:
    by_dir.setdefault(row["mirror_dir"], []).append(row)

header = f"{'mirror_dir':<20} {'n_files':>8} {'errors':>7} {'same_len':>9} {'type_match':>11} {'source_match':>13} {'agreement':>10}"
print(header)
print("-" * len(header))
for mirror_dir, rows in by_dir.items():
    n = len(rows)
    errors = sum(r["error"] is not None for r in rows)
    same_length = sum(r.get("same_length", False) for r in rows)
    type_match = sum(r.get("type_match", False) for r in rows)
    source_match = sum(r.get("source_match", False) for r in rows)
    print(
        f"{mirror_dir:<20} {n:>8} {errors:>7} {same_length:>9} {type_match:>11} "
        f"{source_match:>13} {source_match / n:>10.1%}"
    )

# %% [markdown]
# ## Where do they disagree?
#
# For files where cell count/type match but sources differ, show the first mismatching cell from
# each side. For files with a different cell count (or a hard error), just report as such.

# %%
mismatches = [r for r in results if r["error"] is not None or not r.get("source_match", False)]
print(f"{len(mismatches)} / {len(results)} files disagree")

for row in mismatches:
    print(f"\n=== {row['mirror_dir']}/{row['file']} ===")
    if row["error"]:
        print(f"  error: {row['error']}")
        continue
    if not row["same_length"]:
        print(f"  cell count differs: jupytext={row['jt_cells']} plainb={row['pb_cells']}")
        continue
    if not row["type_match"]:
        print("  cell types differ (see first_diff_cell)")
    jupytext_fmt, plainb_parser = FORMAT_MAP[row["mirror_dir"]]
    path = MIRRORS_ROOT / row["mirror_dir"] / row["file"]
    jt_nb = jupytext.read(path, fmt=jupytext_fmt)
    pb_nb, _ = run_plainb(plainb_parser, path)
    i = row["first_diff_cell"]
    jt_cell, pb_cell = jt_nb.cells[i], pb_nb["cells"][i]
    print(f"  first differing cell: #{i}")
    print(f"  jupytext [{jt_cell.cell_type}]: {jt_cell.source[:200]!r}")
    print(f"  plainb   [{pb_cell['cell_type']}]: {cell_source(pb_cell['source'])[:200]!r}")

# %% [markdown]
# ## Caveats
#
# - Only the four formats `plainb` supports are compared: percent `.py`, Sphinx-Gallery `.py`,
#   classic Markdown `.md`, and MyST Markdown `.md`. Jupytext supports many more (R Markdown,
#   light format, `.jl`/`.R`/other-language scripts, marimo, ...).
# - `plainb`'s parsers never populate `outputs` or `execution_count` (they parse text only, no
#   execution), so this notebook does not compare outputs — only the cell structure and source.
# - Notebook/cell *metadata* (beyond `cell_type`/`source`) is not compared either: the two
#   projects use different metadata schemas (e.g. cell ids, kernelspec placement), so a
#   metadata-level diff would mostly measure schema differences rather than parsing agreement.
