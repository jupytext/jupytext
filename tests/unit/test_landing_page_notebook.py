"""
Tests for the landing page "Quarterly Sales" example notebook.
Verifies that:
  1. The notebook executes without errors.
  2. Conversion to each text format matches the snapshot files in data/landing_page/.

To update snapshots after a format change, run:
  UPDATE_SNAPSHOTS=1 pytest tests/unit/test_landing_page_notebook.py

The landing page (website/src/pages/index.astro) imports all snapshot files directly,
so rebuilding the site is all that is needed after updating snapshots.
"""

import os
import re
from pathlib import Path

import nbclient
import pytest
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook

import jupytext

_MARIMO_VERSION_RE = re.compile(r'^__generated_with = ".*"$', re.MULTILINE)


def _normalize(text: str) -> str:
    """Strip the marimo __generated_with version line so tests don't break on upgrades."""
    return _MARIMO_VERSION_RE.sub('__generated_with = "<version>"', text)


DATA_DIR = Path(__file__).parent / "data" / "landing_page"

FORMATS = {
    "notebook": DATA_DIR / "notebook.ipynb",
    "py:percent": DATA_DIR / "notebook_percent.py",
    "py:light": DATA_DIR / "notebook_light.py",
    "py:marimo": DATA_DIR / "notebook_marimo.py",
    "md": DATA_DIR / "notebook.md",
    "md:myst": DATA_DIR / "notebook.myst.md",
    "qmd": DATA_DIR / "notebook.qmd",
}


@pytest.fixture
def update_snapshots():
    return os.environ.get("UPDATE_SNAPSHOTS") == "1"


def make_notebook():
    nb = new_notebook()
    nb.metadata = {
        "jupytext": {
            "notebook_metadata_filter": "-all",
            "cell_metadata_filter": "-all",
        }
    }
    nb.cells = [
        new_markdown_cell("# Quarterly Sales\nA look at Q4 revenue by region.", id="cell-0001"),
        new_code_cell('import pandas as pd\ndf = pd.read_csv("sales.csv")', id="cell-0002"),
        new_code_cell('df.groupby("region")["revenue"].sum().plot.bar()', id="cell-0003"),
    ]
    return nb


def test_notebook_runs(tmp_path):
    """The example notebook executes without errors given a minimal sales.csv."""
    pytest.importorskip("matplotlib")
    pytest.importorskip("pandas")

    sales_csv = tmp_path / "sales.csv"
    sales_csv.write_text("region,revenue\nNorth,100\nSouth,150\nEast,80\nWest,120\n")

    nb = make_notebook()
    nb.cells.insert(0, new_code_cell("import matplotlib\nmatplotlib.use('Agg')"))

    client = nbclient.NotebookClient(nb, timeout=60, kernel_name="python3", resources={"metadata": {"path": str(tmp_path)}})
    client.execute()

    errors = [
        output
        for cell in nb.cells
        if cell.cell_type == "code"
        for output in cell.get("outputs", [])
        if output.output_type == "error"
    ]
    assert errors == [], f"Notebook raised errors: {errors}"


@pytest.mark.parametrize("fmt,snapshot", list(FORMATS.items()))
def test_conversion(fmt, snapshot, update_snapshots):
    """Conversion to each landing page format matches the snapshot file."""
    from jupytext.marimo import is_marimo_available
    from jupytext.myst import is_myst_available
    from jupytext.quarto import is_quarto_available

    if fmt == "qmd" and not is_quarto_available():
        pytest.skip("quarto not available")
    if fmt == "md:myst" and not is_myst_available():
        pytest.skip("myst-parser not available")
    if fmt == "py:marimo" and not is_marimo_available():
        pytest.skip("marimo not available")

    nb = make_notebook()
    text = jupytext.writes(nb, fmt=fmt)

    if update_snapshots:
        snapshot.write_text(text)
        return

    assert snapshot.exists(), f"Snapshot {snapshot} does not exist — run with --update-snapshots to create it"
    expected = snapshot.read_text()
    assert _normalize(text) == _normalize(expected), (
        f"Format {fmt!r} output does not match snapshot {snapshot.name}.\n\n"
        f"Run UPDATE_SNAPSHOTS=1 pytest to regenerate the snapshot, then review the diff.\n"
        f"All snapshots are imported directly by the landing page and will update on rebuild."
    )
