import os
import shlex

import pytest
from nbformat.v4.nbbase import new_code_cell, new_notebook

import jupytext
from jupytext.cli import jupytext as jupytext_cli

doc_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "website", "src", "content", "docs")


@pytest.mark.requires_user_kernel_python3
@pytest.mark.requires_black
@pytest.mark.requires_myst
@pytest.mark.skipif(not os.path.isdir(doc_path), reason="Documentation folder is missing")
def test_jupytext_commands_in_the_documentation_work(tmpdir):
    # Read the documentation as a bash notebook
    using_cli = os.path.join(doc_path, "using", "cli.md")
    assert os.path.isfile(using_cli)
    using_cli_nb = jupytext.read(using_cli)

    # Run the commands in tmpdir on a sample notebook
    jupytext.write(new_notebook(cells=[new_code_cell("1+1")]), str(tmpdir.join("notebook.ipynb")))
    os.chdir(str(tmpdir))

    cmd_tested = 0
    for cell in using_cli_nb.cells:
        if cell.cell_type != "code":
            continue
        if not cell.source.startswith("jupytext"):
            continue
        for cmd in cell.source.splitlines():
            if not cmd.startswith("jupytext"):
                continue

            # Do not test commands that involve reading a notebook from stdin
            if "read ipynb from stdin" in cmd:
                continue

            # We can't run pytest inside pytest
            if "pytest {}" in cmd:
                continue

            # We need to remove the comments that may follow the jupytext command
            if "#" in cmd:
                left, comment = cmd.rsplit("#", 1)
                if '"' not in comment:
                    cmd = left

            print(f"Testing: {cmd}")
            args = shlex.split(cmd)[1:]
            assert not jupytext_cli(args), cmd
            cmd_tested += 1

    assert cmd_tested >= 10
