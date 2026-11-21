import contextlib
import itertools
import os.path
import re
import sys
import unittest.mock as mock
from pathlib import Path

import pytest
from jupyter_client.kernelspec import find_kernel_specs, get_kernel_spec
import nbformat
from nbformat import reads as nb_reads, validate
from nbformat.v4 import nbbase
from nbformat.v4.nbbase import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_output,
)
from nbformat.sign import NotebookNotary


import jupytext
from jupytext.cell_reader import rst2md
from jupytext.cli import system, tool_version
from jupytext.formats import formats_with_support_for_cell_metadata
from jupytext.myst import is_myst_available
from jupytext.pandoc import is_pandoc_available
from jupytext.quarto import is_quarto_available
from jupytext.marimo import is_marimo_available

# Pytest's tmpdir is in /tmp (at least for me), so this helps to avoid interferences between
# global configuration on HOME and the test collection
jupytext.config.JUPYTEXT_CEILING_DIRECTORIES = ["/tmp/"]

SAMPLE_NOTEBOOK_PATH = Path(__file__).parent / "data" / "notebooks" / "inputs"
ROOT_PATH = Path(__file__).parent.parent


def nbformat_reads(s, as_version, capture_validation_error=None, **kwargs):
    """Wrapper around nbformat.reads that forces validation"""
    nb = nb_reads(s, as_version, capture_validation_error=capture_validation_error, **kwargs)
    validate(nb)
    return nb


@pytest.fixture(autouse=True)
def force_validate_nbformat(monkeypatch):
    """Force validation of nbformat in all tests"""
    monkeypatch.setattr(nbformat, "reads", nbformat_reads)


@pytest.fixture
def fresh_notary(tmp_path):
    notary = NotebookNotary(
        db_file=":memory:",
        secret=b"test-secret",
    )
    yield notary
    # Close the SQLite database connection to avoid ResourceWarnings on Python 3.13+
    notary.store.close()


@pytest.fixture(params=["sync", "async"])
def cm(request, fresh_notary):
    if request.param == "sync":
        cm = jupytext.TextFileContentsManager()
    else:
        cm = jupytext.AsyncTextFileContentsManager()

    # We use a fresh notary for each test,
    # to make sure that the trust status of
    # notebooks is not shared between tests
    cm.notary = fresh_notary

    yield cm
    # Clean up any resources in the contents manager
    with contextlib.suppress(Exception):
        if hasattr(cm, "close"):
            cm.close()


@pytest.fixture
def no_jupytext_version_number():
    with mock.patch("jupytext.header.INSERT_AND_CHECK_VERSION_NUMBER", False):
        yield


@pytest.fixture
def cwd_tmpdir(tmpdir):
    # Run the whole test from inside tmpdir
    with tmpdir.as_cwd():
        yield tmpdir


@pytest.fixture()
def cwd_tmp_path(tmp_path):
    # Run the whole test from inside tmp_path
    if sys.version_info < (3, 11):
        with tmp_path.cwd():
            yield tmp_path
    else:
        # https://github.com/mwouts/jupytext/issues/1242
        with contextlib.chdir(tmp_path):
            yield tmp_path


@pytest.fixture
def jupytext_repo_root():
    """The local path of this repo, to use in .pre-commit-config.yaml in tests"""
    return str(Path(__file__).parent.parent.resolve())


@pytest.fixture
def jupytext_repo_rev(jupytext_repo_root):
    """The local revision of this repo, to use in .pre-commit-config.yaml in tests"""
    return system("git", "rev-parse", "HEAD", cwd=jupytext_repo_root).strip()


@pytest.fixture()
def python_notebook():
    return new_notebook(
        cells=[new_markdown_cell("A short notebook")],
        # We need a Python kernel here otherwise Jupytext is going to add
        # the information that this is a Python notebook when we sync the
        # .py and .ipynb files
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python_kernel",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.6.4",
            },
        },
    )


@pytest.fixture()
def notebook_with_outputs():
    return new_notebook(
        cells=[
            new_code_cell(
                "1+1",
                execution_count=1,
                outputs=[
                    new_output(
                        data={"text/plain": "2"},
                        execution_count=1,
                        output_type="execute_result",
                    )
                ],
            )
        ],
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python_kernel",
            }
        },
    )


@pytest.fixture(params=list(formats_with_support_for_cell_metadata()))
def fmt_with_cell_metadata(request):
    return request.param


def list_notebooks(path="ipynb", skip=""):
    """All notebooks in the directory notebooks/path,
    or in the package itself"""
    if path == "ipynb":
        return (
            list_notebooks("ipynb_julia", skip=skip)
            + list_notebooks("ipynb_py", skip=skip)
            + list_notebooks("ipynb_R", skip=skip)
        )

    nb_path = SAMPLE_NOTEBOOK_PATH

    if path == "ipynb_all":
        return itertools.chain(
            *(list_notebooks(folder.name, skip=skip) for folder in nb_path.iterdir() if folder.name.startswith("ipynb_"))
        )

    if path == "all":
        return itertools.chain(*(list_notebooks(folder.name, skip=skip) for folder in nb_path.iterdir()))

    if path.startswith("."):
        nb_path = Path(__file__).parent / ".." / path
    else:
        nb_path = nb_path / path

    if skip:
        skip_re = re.compile(".*" + skip + ".*")
        return [str(nb_file) for nb_file in nb_path.iterdir() if nb_file.is_file() and not skip_re.match(nb_file.name)]

    return [str(nb_file) for nb_file in nb_path.iterdir() if nb_file.is_file()]


def notebook_id_func(nb_file):
    nb_file = Path(nb_file)
    if SAMPLE_NOTEBOOK_PATH in nb_file.parents:
        return str(nb_file.relative_to(SAMPLE_NOTEBOOK_PATH))
    return str(nb_file.relative_to(ROOT_PATH))


@pytest.fixture(params=list_notebooks("ipynb_all"), ids=notebook_id_func)
def ipynb_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("all"), ids=notebook_id_func)
def any_nb_file(request):
    return request.param


@pytest.fixture
def ipynb_py_R_jl_files():
    return list_notebooks()


@pytest.fixture(params=list_notebooks(), ids=notebook_id_func)
def ipynb_py_R_jl_file(request):
    return request.param


@pytest.fixture
def ipynb_py_R_jl_ext(ipynb_py_R_jl_file):
    for language in "py", "R", "julia":
        if f"{os.path.sep}ipynb_{language}{os.path.sep}" in ipynb_py_R_jl_file:
            return ".jl" if language == "julia" else "." + language

    raise RuntimeError(f"language not found for {ipynb_py_R_jl_file}")


@pytest.fixture(params=list_notebooks("ipynb") + list_notebooks("Rmd"), ids=notebook_id_func)
def ipynb_or_rmd_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_py") + list_notebooks("ipynb_R"), ids=notebook_id_func)
def ipynb_py_R_file(request):
    return request.param


@pytest.fixture
def ipynb_py_files():
    return list_notebooks("ipynb_py")


@pytest.fixture(params=list_notebooks("ipynb_py"), ids=notebook_id_func)
def ipynb_py_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_py", skip="(raw_cell|R_magic|metadata and long cells)"), ids=notebook_id_func)
def marimo_compatible_ipynb(request):
    nb = jupytext.read(SAMPLE_NOTEBOOK_PATH / request.param)
    marimo_text = jupytext.writes(nb, "auto:marimo")
    for line in marimo_text.splitlines():
        if "not supported in marimo" in line:
            pytest.skip(f"{request.param} contains features not supported in marimo: {line}")

    # We'd need to get this one fixed in Marimo
    if "flavors of raw cells" in request.param:
        pytest.skip(f"{request.param} contains $ signs in a raw cells, not supported in marimo")

    if "jupyter_again" in request.param:
        pytest.skip(f"{request.param} contains '?help', not supported in marimo")

    if "nteract_with_parameter" in request.param:
        pytest.skip(f"{request.param} contains both tags and metadata - only tags are supported")

    if "jupyterlab-slideshow_1441" in request.param:
        pytest.skip(f"{request.param} contains a line ending with spaces, which is trimmed by marimo")

    return request.param


@pytest.fixture(params=list_notebooks("ipynb_R"), ids=notebook_id_func)
def ipynb_R_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_julia"), ids=notebook_id_func)
def ipynb_julia_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_scheme"), ids=notebook_id_func)
def ipynb_scheme_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_cpp"), ids=notebook_id_func)
def ipynb_cpp_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_all", skip="many hash"), ids=notebook_id_func)
def ipynb_to_light(request):
    return request.param


@pytest.fixture(params=list_notebooks("ipynb_all"), ids=notebook_id_func)
def ipynb_to_myst(request):
    return request.param


@pytest.fixture(
    params=[
        py_file for py_file in list_notebooks("./src/jupytext") if py_file.endswith(".py") and "folding_markers" not in py_file
    ],
    ids=notebook_id_func,
)
def py_file(request):
    return request.param


@pytest.fixture(
    params=list_notebooks("julia") + list_notebooks("python") + list_notebooks("R") + list_notebooks("ps1"),
    ids=notebook_id_func,
)
def script_to_ipynb(request):
    return request.param


@pytest.fixture(params=list_notebooks("python"), ids=notebook_id_func)
def python_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("percent"), ids=notebook_id_func)
def percent_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("hydrogen"), ids=notebook_id_func)
def hydrogen_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("R"), ids=notebook_id_func)
def r_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("R_spin"), ids=notebook_id_func)
def r_spin_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("marimo"), ids=notebook_id_func)
def marimo_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("md"), ids=notebook_id_func)
def md_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("myst"), ids=notebook_id_func)
def myst_file(request):
    return request.param


@pytest.fixture(
    params=list_notebooks("ipynb", skip="(functional|Notebook with|flavors|invalid|305|jupyterlab-slideshow)"),
    ids=notebook_id_func,
)
def ipynb_to_pandoc(request):
    return request.param


@pytest.fixture(
    params=list_notebooks(
        "ipynb",
        skip="(functional|Notebook with|plotly_graphs|flavors|complex_metadata|"
        "update83|raw_cell|_66|nteract|LaTeX|invalid|305|text_outputs|ir_notebook|jupyter|with_R_magic)",
    ),
    ids=notebook_id_func,
)
def ipynb_to_quarto(request):
    return request.param


@pytest.fixture(
    params=list_notebooks("ipynb_py", skip="(raw|hash|frozen|magic|html|164|long)"),
    ids=notebook_id_func,
)
def ipynb_to_sphinx(request):
    return request.param


@pytest.fixture(params=list_notebooks("Rmd"), ids=notebook_id_func)
def rmd_file(request):
    return request.param


@pytest.fixture(params=list_notebooks("sphinx"), ids=notebook_id_func)
def sphinx_file(request):
    return request.param


def pytest_runtest_setup(item):
    for mark in item.iter_markers():
        for tool in [
            "jupytext",
            "black",
            "isort",
            "flake8",
            "autopep8",
            "jupyter nbconvert",
        ]:
            if mark.name == f"requires_{tool.replace(' ', '_')}":
                if not tool_version(tool):
                    pytest.skip(f"{tool} is not installed")
        if mark.name == "requires_sphinx_gallery":
            if not rst2md:
                pytest.skip("sphinx_gallery is not available")
        if mark.name == "requires_pandoc":
            # The mirror files changed slightly when Pandoc 2.11 was introduced
            # https://github.com/mwouts/jupytext/commit/c07d919702999056ce47f92b74f63a15c8361c5d
            # The mirror files changed again when Pandoc 2.16 was introduced
            # https://github.com/mwouts/jupytext/pull/919/commits/1fa1451ecdaa6ad8d803bcb6fb0c0cf09e5371bf
            if not is_pandoc_available(min_version="3.0"):
                pytest.skip("pandoc>=3.0 is not available")
        if mark.name == "requires_quarto":
            if not is_quarto_available(min_version="0.2.0"):
                pytest.skip("quarto>=0.2 is not available")
        if mark.name == "requires_marimo":
            if not is_marimo_available():
                pytest.skip("marimo is not available")
        if mark.name == "requires_no_pandoc":
            if is_pandoc_available():
                pytest.skip("Pandoc is installed")
        if mark.name == "requires_ir_kernel":
            if not any(get_kernel_spec(name).language == "R" for name in find_kernel_specs()):
                pytest.skip("irkernel is not installed")
        if mark.name == "requires_user_kernel_python3":
            if "python_kernel" not in find_kernel_specs():
                pytest.skip("Please run 'python -m ipykernel install --name python_kernel --user'")
        if mark.name == "requires_myst":
            if not is_myst_available():
                pytest.skip("myst_parser not found")
        if mark.name == "requires_no_myst":
            if is_myst_available():
                pytest.skip("myst is available")
        if mark.name == "skip_on_windows":
            if sys.platform.startswith("win"):
                pytest.skip("Issue 489")
        if mark.name == "pre_commit":
            if sys.platform.startswith("win"):
                pytest.skip("OSError: [WinError 193] %1 is not a valid Win32 application")
            if not (Path(__file__).parent.parent / ".git").is_dir():
                pytest.skip("Jupytext folder is not a git repository #814")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if (config.rootdir / "tests" / "external" / "pre_commit") in item.path.parents:
            item.add_marker(pytest.mark.pre_commit)


@pytest.fixture(autouse=True)
def cell_id():
    """To make sure that cell ids are distinct we use a global counter.
    This solves https://github.com/mwouts/jupytext/issues/747"""
    local_cell_count = 0

    def enumerate_cell_ids():
        nonlocal local_cell_count
        local_cell_count += 1
        return f"cell-{local_cell_count}"

    nbbase.random_cell_id = enumerate_cell_ids
