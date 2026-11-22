from copy import deepcopy

import pytest
from nbformat.v4 import new_notebook

from jupytext import read, write, writes
from jupytext.compare import compare
from jupytext.formats import long_form_one_format
from jupytext.jupytext import NotSupportedNBFormatVersion


@pytest.mark.parametrize(
    "fmt",
    ["auto:light", "auto:percent", "md", ".Rmd", ".ipynb"],
)
def test_write_notebook_does_not_change_it(ipynb_py_R_jl_file, fmt, tmpdir):
    nb_org = read(ipynb_py_R_jl_file)
    nb_org_copied = deepcopy(nb_org)
    ext = long_form_one_format(fmt, nb_org.metadata)["extension"]

    writes(nb_org, fmt)
    compare(nb_org, nb_org_copied)

    tmp_dest = str(tmpdir.join("notebook" + ext))
    write(nb_org, tmp_dest, fmt=fmt)
    compare(nb_org, nb_org_copied)


def test_serialization_failure_leaves_existing_file_intact(tmp_path):
    path = tmp_path / "notebook.py"
    original = b"# Keep this file\n"
    path.write_bytes(original)

    notebook = new_notebook()
    notebook.nbformat = 3
    with pytest.raises(NotSupportedNBFormatVersion):
        write(notebook, path, fmt="py:percent")

    assert path.read_bytes() == original
