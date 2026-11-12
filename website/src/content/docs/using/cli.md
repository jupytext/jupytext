---
title: "Jupytext CLI"
description: "Convert, pair, sync and pipe notebooks from the command line."
sidebar:
  order: 2
---

## Command line conversion

Jupytext provides command line interface for converting notebooks between the different formats.

```bash
jupytext --to py notebook.ipynb                 # convert notebook.ipynb to a .py file
jupytext --to py:percent notebook.ipynb         # convert notebook.ipynb to a .py file in the double percent format
jupytext --to py:percent --opt comment_magics=false notebook.ipynb   # same as above + do not comment magic commands
jupytext --to markdown notebook.ipynb           # convert notebook.ipynb to a .md file
jupytext --output script.py notebook.ipynb      # convert notebook.ipynb to a script.py file

jupytext --to notebook notebook.py              # convert notebook.py to an .ipynb file with no outputs
jupytext --update --to notebook notebook.py     # update the input cells in the .ipynb file and preserve outputs and metadata

jupytext --to md --test notebook.ipynb          # Test round trip conversion

jupytext --to md --output - notebook.ipynb      # display the markdown version on screen
jupytext --from ipynb --to py:percent           # read ipynb from stdin and write double percent script on stdout
```

Jupytext has a `--sync` mode that updates all the paired representations of a notebook based on timestamps:
```bash
jupytext --set-formats ipynb,py notebook.ipynb  # Turn notebook.ipynb into a paired ipynb/py notebook
jupytext --sync notebook.ipynb                  # Update whichever of notebook.ipynb/notebook.py is outdated
```

You may also find useful to `--pipe` the text representation of a notebook into tools like `black`:
```bash
jupytext --sync --pipe black notebook.ipynb    # read most recent version of notebook, reformat with black, save
```

To reorder the imports in your notebook, use
```bash
jupytext --pipe 'isort - --treat-comment-as-code "# %%" --float-to-top' notebook.ipynb
```
(remove the `--float-to-top` argument if you prefer to run `isort` per cell).

For programs that don't accept pipes, use `{}` as a placeholder for the name of a temporary file that will contain the text representation of the notebook. For instance, run `pytest` on your notebook with:
```bash
jupytext --check 'pytest {}' notebook.ipynb    # export the notebook in format py:percent in a temp file, run pytest
```
Read more about running `pytest` on notebooks in our example [`Tests in a notebook.md`](https://github.com/jupytext/jupytext/blob/main/demo/Tests%20in%20a%20notebook.md#).
Note also that on Windows you need to use double quotes instead of single quotes and type e.g. `jupytext --check "pytest {}" notebook.ipynb`.

Execute `jupytext --help` to access the full documentation.

### Execute notebook cells

For convenience, when creating a notebook from text you can execute it:

```bash
jupytext --set-kernel - notebook.md             # create a YAML header with kernel metadata matching the current python executable
jupytext --set-formats md:myst notebook.md      # create a YAML header with an explicit jupytext format
jupytext --to notebook --execute notebook.md    # convert notebook.md to an .ipynb file and run it
```

If you wanted to convert a collection of Markdown files to paired notebooks, and execute them in the current Python environment, you could run:
```bash
jupytext --set-formats ipynb,md --execute *.md
```

By default the cell outputs are only saved in the notebook. To follow the progress of a long-running notebook, add `--show-output`: the stdout and stderr outputs of each cell are then printed to stderr while the cell runs (they are still saved in the notebook, and they do not mix with a notebook written to stdout with `-o -`):
```bash
jupytext --to notebook --execute --show-output notebook.md
```

#### Advanced usage: error tolerance

If any notebook cell errors, execution will terminate and `jupytext` will not save the notebook. This can cause headaches as the details of any error would be encoded in the notebook, which would not have been saved. But there's an error-tolerant way to execute a notebook: `jupyter nbconvert` has a mode which will still save a notebook if a cell errors, producing something akin to what would happen if you ran all cells manually in Jupyter's notebook UI.

```bash
# First, convert script (py/sh/R/jl etc) -> notebook. May need additional args to define input format etc as above.
jupytext --to ipynb script.py
# Then, execute notebook in place and allowing cells to produce errors
jupyter nbconvert --to ipynb --inplace --execute --allow-errors script.ipynb
# One can also combine these to a single command using jupytext --pipe
jupytext --to ipynb --pipe-fmt ipynb \
  --pipe 'jupyter nbconvert --to ipynb --execute --allow-errors --stdin --stdout' \
  script.py
```

In each of the above, `jupyter nbconvert` could be replaced with any alternative tool to execute a jupyter notebook non-interactively, including [papermill](https://github.com/nteract/papermill) which would allow notebook parameterisation (see [@mwouts' post on the topic here](https://github.com/CFMTech/jupytext_papermill_post/blob/master/README.md)).

## Testing the round-trip conversion

Representing Jupyter notebooks as scripts requires a solid round trip conversion. You don't want your notebooks (nor your scripts) to change because you are converting them to the other form. Our test suite includes a few hundred tests to ensure that round trip conversion is safe.

You can test yourself that the round trip conversion preserves your Jupyter notebooks and scripts. Run for instance:
```bash
# Test the ipynb -> py:percent -> ipynb round trip conversion
jupytext --test notebook.ipynb --to py:percent

# Test the ipynb -> (py:percent + ipynb) -> ipynb (à la paired notebook) conversion
jupytext --test --update notebook.ipynb --to py:percent
```

Note that `jupytext --test` compares the resulting notebooks according to its expectations. If you wish to proceed to a strict comparison of the two notebooks, use `jupytext --test-strict`, and use the flag `-x` to report with more details on the first difference, if any.

## Cell and notebook metadata

When a scripts is converted to an `.ipynb` notebook, Jupytext will set empty notebook and cell [metadata filters](/reference/advanced-options/) to avoid having notebook or cell metadata added back to the script. Remove these filters if you want to store Jupytext's settings, or the kernel information, in the text file.

Cell metadata are available in the `light` and `percent` formats, as well as in the MyST Markdown, R Markdown and Jupytext Markdown formats. R scripts in `spin` format support cell metadata for code cells only. Sphinx Gallery scripts in `sphinx` format do not support cell metadata.

A few cell metadata are not included in the text representation of the notebook, and only the most standard notebook metadata are exported - see the section on [metadata filters](/reference/advanced-options/).
