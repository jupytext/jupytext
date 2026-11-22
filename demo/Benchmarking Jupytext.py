# %% [markdown]
# # Benchmarking Jupytext formats
#
# This notebook measures how long it takes to write and read the same
# [World Population notebook](World%20population.ipynb) in different formats.
# It also reports the size of each serialized file in UTF-8 bytes. Run it from
# the demo directory to see results for your environment.

# %%
from copy import deepcopy
from shutil import which
from statistics import median
from time import perf_counter

import jupytext
import nbformat
from IPython.display import Markdown, display

notebook = jupytext.read("World population.ipynb")
without_outputs = deepcopy(notebook)
for cell in without_outputs.cells:
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

# %% [markdown]
# ## Measure each format
#
# Each result is the median of five conversions. The nbformat row provides a
# baseline for reading and writing an ordinary Jupyter notebook. Pandoc is
# included when its executable is available.

# %%
formats = ["nbformat", "ipynb", "py:percent", "py:light", "py:sphinx", "md", "md:myst", "Rmd"]
if which("pandoc"):
    formats.append("md:pandoc")


def measure(notebook, fmt, repeats=5):
    write_times = []
    read_times = []
    for _ in range(repeats):
        started = perf_counter()
        if fmt == "nbformat":
            text = nbformat.writes(notebook)
        else:
            text = jupytext.writes(notebook, fmt)
        written = perf_counter()
        if fmt == "nbformat":
            nbformat.reads(text, as_version=4)
        else:
            jupytext.reads(text, fmt)
        read_times.append(perf_counter() - written)
        write_times.append(written - started)
    return len(text.encode("utf-8")), 1000 * median(write_times), 1000 * median(read_times)

# %% [markdown]
# ## See what outputs cost
#
# Compare the two tables. An `.ipynb` file can store rich cell outputs such as
# the population charts. Text formats typically store the inputs.

# %%
for label, example in [("With outputs", notebook), ("Without outputs", without_outputs)]:
    rows = [
        f"### {label}",
        "",
        "| Format | Bytes | Write (ms) | Read (ms) |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for fmt in formats:
        size, write_ms, read_ms = measure(example, fmt)
        rows.append(f"| `{fmt}` | {size:,} | {write_ms:.2f} | {read_ms:.2f} |")
    display(Markdown("\n".join(rows)))
