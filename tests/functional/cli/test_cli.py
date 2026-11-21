import os
import sys
import time
import unittest.mock as mock
import warnings
from argparse import ArgumentTypeError
from io import StringIO
from shutil import copyfile
from subprocess import check_call

import nbformat
import pytest
from jupyter_client.kernelspec import find_kernel_specs, get_kernel_spec
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook

from jupytext import __version__, read, reads, write, writes
from jupytext.cli import jupytext, parse_jupytext_args, str2bool, system
from jupytext.compare import compare, compare_notebooks
from jupytext.formats import JupytextFormatError, long_form_one_format
from jupytext.myst import is_myst_available
from jupytext.paired_paths import InconsistentPath, paired_paths
from jupytext.pandoc import is_pandoc_available


def test_str2bool():
    assert str2bool("d") is None
    assert str2bool("TRUE") is True
    assert str2bool("0") is False
    with pytest.raises(ArgumentTypeError):
        str2bool("UNEXPECTED")


def test_cli_single_file(ipynb_py_R_jl_file):
    assert parse_jupytext_args([ipynb_py_R_jl_file] + ["--to", "py"]).notebooks == [ipynb_py_R_jl_file]


def test_cli_multiple_files(ipynb_py_R_jl_files):
    assert parse_jupytext_args(ipynb_py_R_jl_files + ["--to", "py"]).notebooks == ipynb_py_R_jl_files


def test_convert_single_file_in_place(ipynb_py_file, tmpdir):
    nb_org = str(tmpdir.join(os.path.basename(ipynb_py_file)))
    copyfile(ipynb_py_file, nb_org)

    base, ext = os.path.splitext(nb_org)
    nb_other = base + ".py"

    jupytext([nb_org, "--to", "py"])

    nb1 = read(nb_org)
    nb2 = read(nb_other)

    compare_notebooks(nb2, nb1)


def test_convert_single_file_in_place_m(ipynb_py_file, tmpdir):
    nb_org = str(tmpdir.join(os.path.basename(ipynb_py_file)))
    copyfile(ipynb_py_file, nb_org)

    base, ext = os.path.splitext(nb_org)

    for fmt_ext in ("py", "Rmd"):
        nb_other = base + "." + fmt_ext

        check_call([sys.executable, "-m", "jupytext", nb_org, "--to", fmt_ext])

        nb1 = read(nb_org)
        nb2 = read(nb_other)

        compare_notebooks(nb2, nb1)


def test_convert_single_file(ipynb_or_rmd_file, tmpdir, capsys):
    nb_org = str(tmpdir.join(os.path.basename(ipynb_or_rmd_file)))
    copyfile(ipynb_or_rmd_file, nb_org)

    nb1 = read(ipynb_or_rmd_file)
    pynb = writes(nb1, "py")
    jupytext([nb_org, "--to", "py", "-o", "-"])

    out, err = capsys.readouterr()
    assert err == ""
    compare(out, pynb)


def test_jupytext_version(capsys):
    jupytext(["--version"])

    out, err = capsys.readouterr()
    assert err == ""
    compare(out, __version__ + "\n")


def test_wildcard(tmpdir):
    nb1_ipynb = str(tmpdir.join("nb1.ipynb"))
    nb2_ipynb = str(tmpdir.join("nb2.ipynb"))

    nb1_py = str(tmpdir.join("nb1.py"))
    nb2_py = str(tmpdir.join("nb2.py"))

    write(new_notebook(metadata={"notebook": 1}), nb1_ipynb)
    write(new_notebook(metadata={"notebook": 2}), nb2_ipynb)

    os.chdir(str(tmpdir))
    jupytext(["nb*.ipynb", "--to", "py"])

    assert os.path.isfile(nb1_py)
    assert os.path.isfile(nb2_py)

    with pytest.raises(IOError):
        jupytext(["nb3.ipynb", "--to", "py"])


def test_to_cpluplus(ipynb_cpp_file, tmpdir, capsys):
    nb_org = str(tmpdir.join(os.path.basename(ipynb_cpp_file)))
    copyfile(ipynb_cpp_file, nb_org)
    nb1 = read(nb_org)

    text_cpp = writes(nb1, "cpp")
    jupytext([nb_org, "--to", "c++", "--output", "-"])

    out, err = capsys.readouterr()
    assert err == ""
    compare(out, text_cpp)


def test_convert_multiple_file(ipynb_py_files, tmpdir):
    nb_orgs = []
    nb_others = []

    for nb_file in ipynb_py_files:
        nb_org = str(tmpdir.join(os.path.basename(nb_file)))
        base, ext = os.path.splitext(nb_org)
        nb_other = base + ".py"
        copyfile(nb_file, nb_org)
        nb_orgs.append(nb_org)
        nb_others.append(nb_other)

    jupytext(nb_orgs + ["--to", "py"])

    for nb_org, nb_other in zip(nb_orgs, nb_others):
        nb1 = read(nb_org)
        nb2 = read(nb_other)
        compare_notebooks(nb2, nb1)


def test_error_not_notebook_ext_input(tmpdir, capsys):
    tmp_file = str(tmpdir.join("notebook.ext"))
    with open(tmp_file, "w") as fp:
        fp.write("\n")

    with pytest.raises(InconsistentPath, match="is not a notebook. Supported extensions are"):
        jupytext([tmp_file, "--to", "py"])


@pytest.fixture
def tmp_ipynb(tmpdir):
    tmp_file = str(tmpdir.join("notebook.ipynb"))
    write(new_notebook(), tmp_file)
    return tmp_file


@pytest.fixture
def tmp_py(tmpdir):
    tmp_file = str(tmpdir.join("notebook.py"))
    with open(tmp_file, "w") as fp:
        fp.write("\n")
    return tmp_file


def test_error_not_notebook_ext_to(tmp_ipynb):
    with pytest.raises(JupytextFormatError, match="'ext' is not a notebook extension"):
        jupytext([tmp_ipynb, "--to", "ext"])


def test_error_not_notebook_ext_output(tmp_ipynb, tmpdir):
    with pytest.raises(
        JupytextFormatError,
        match="Extension '.ext' is not a notebook extension. Please use one of",
    ):
        jupytext([tmp_ipynb, "-o", str(tmpdir.join("not.ext"))])


def test_error_not_same_ext(tmp_ipynb, tmpdir):
    with pytest.raises(InconsistentPath):
        jupytext([tmp_ipynb, "--to", "py", "-o", str(tmpdir.join("not.md"))])


def test_error_no_action(tmp_ipynb):
    with pytest.raises(ValueError, match="Please provide one of"):
        jupytext([tmp_ipynb])


def test_error_update_not_ipynb(tmp_py):
    with pytest.raises(ValueError, match="--update is only for ipynb files"):
        jupytext([tmp_py, "--to", "py", "--update"])


def test_error_multiple_input(tmp_ipynb):
    with pytest.raises(ValueError, match="Please input a single notebook when using --output"):
        jupytext([tmp_ipynb, tmp_ipynb, "--to", "py", "-o", "notebook.py"])


def test_error_opt_missing_equal(tmp_ipynb):
    with pytest.raises(ValueError, match="key=value"):
        jupytext([tmp_ipynb, "--to", "py", "--opt", "missing_equal"])


def test_error_unknown_opt(tmp_ipynb):
    with pytest.raises(ValueError, match="is not a valid format option"):
        jupytext([tmp_ipynb, "--to", "py", "--opt", "unknown=true"])


def test_combine_same_version_ok(tmpdir):
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))
    tmp_nbpy = str(tmpdir.join("notebook.py"))
    tmp_rmd = str(tmpdir.join("notebook.Rmd"))

    with open(tmp_nbpy, "w") as fp:
        fp.write(
            """# ---
# jupyter:
#   jupytext_formats: ipynb,py
#   jupytext_format_version: '1.2'
# ---

# New cell
"""
        )

    nb = new_notebook(metadata={"jupytext_formats": "ipynb,py"})
    write(nb, tmp_ipynb)

    # to jupyter notebook
    jupytext([tmp_nbpy, "--to", "ipynb", "--update"])
    # test round trip
    jupytext([tmp_nbpy, "--to", "notebook", "--test"])
    # test ipynb to rmd
    jupytext([tmp_ipynb, "--to", "rmarkdown"])

    nb = read(tmp_ipynb)
    cells = nb["cells"]
    assert len(cells) == 1
    assert cells[0].cell_type == "markdown"
    assert cells[0].source == "New cell"

    nb = read(tmp_rmd)
    cells = nb["cells"]
    assert len(cells) == 1
    assert cells[0].cell_type == "markdown"
    assert cells[0].source == "New cell"


def test_combine_lower_version_raises(tmpdir):
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))
    tmp_nbpy = str(tmpdir.join("notebook.py"))

    with open(tmp_nbpy, "w") as fp:
        fp.write(
            """# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '55.4'
#       jupytext_version: 42.1.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# New cell
"""
        )

    nb = new_notebook(metadata={"jupytext_formats": "ipynb,py"})
    write(nb, tmp_ipynb)

    with pytest.raises(
        ValueError,
        match="The file notebook.py was generated with jupytext version 42.1.1 but you have .* installed. "
        "Please upgrade jupytext to version 42.1.1, or remove either notebook.py or notebook.ipynb. "
        "This error occurs because notebook.py is in the light format in version 55.4, "
        "while jupytext version .* installed at .* can only read the light format in versions .*",
    ):
        jupytext([tmp_nbpy, "--to", "ipynb", "--update"])


def test_ipynb_to_py_then_update_test(ipynb_py_file, tmpdir):
    """Reproduce https://github.com/mwouts/jupytext/issues/83"""
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))
    tmp_nbpy = str(tmpdir.join("notebook.py"))

    copyfile(ipynb_py_file, tmp_ipynb)

    jupytext(["--to", "py", tmp_ipynb])
    jupytext(["--test", "--update", "--to", "ipynb", tmp_nbpy])


def test_test_to_ipynb_ignore_version_number_414(
    tmpdir,
    text="""# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.1.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# A short markdown cell

# Followed by a code cell
2 + 2
""",
):
    tmp_py = str(tmpdir.join("script.py"))
    with open(tmp_py, "w") as fp:
        fp.write(text)

    assert jupytext(["--test", "--to", "ipynb", tmp_py]) == 0


def test_convert_to_percent_format(ipynb_py_file, tmpdir):
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))
    tmp_nbpy = str(tmpdir.join("notebook.py"))

    copyfile(ipynb_py_file, tmp_ipynb)

    jupytext(["--to", "py:percent", tmp_ipynb])

    with open(tmp_nbpy) as stream:
        py_script = stream.read()
        assert "format_name: percent" in py_script

    nb1 = read(tmp_ipynb)
    nb2 = read(tmp_nbpy)

    compare_notebooks(nb2, nb1)


def test_convert_to_percent_format_and_keep_magics(ipynb_py_file, tmpdir):
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))
    tmp_nbpy = str(tmpdir.join("notebook.py"))

    copyfile(ipynb_py_file, tmp_ipynb)

    jupytext(["--to", "py:percent", "--opt", "comment_magics=False", tmp_ipynb])

    with open(tmp_nbpy) as stream:
        py_script = stream.read()
        assert "format_name: percent" in py_script
        assert "comment_magics: false" in py_script
        assert "# %%time" not in py_script

    nb1 = read(tmp_ipynb)
    nb2 = read(tmp_nbpy)

    compare_notebooks(nb2, nb1)


def test_set_formats(python_file, tmpdir):
    tmp_py = str(tmpdir.join("notebook.py"))
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))

    copyfile(python_file, tmp_py)

    jupytext([tmp_py, "--set-formats", "ipynb,py:light"])
    nb = read(tmp_ipynb)
    assert nb.metadata["jupytext"]["formats"] == "ipynb,py:light"


def test_update_metadata(python_file, tmpdir, capsys):
    tmp_py = str(tmpdir.join("notebook.py"))
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))

    copyfile(python_file, tmp_py)

    jupytext(
        [
            "--to",
            "ipynb",
            tmp_py,
            "--update-metadata",
            '{"jupytext":{"formats":"ipynb,py:light"}}',
        ]
    )

    nb = read(tmp_ipynb)
    assert nb.metadata["jupytext"]["formats"] == "ipynb,py:light"

    jupytext(["--to", "py", tmp_ipynb, "--update-metadata", '{"jupytext":{"formats":null}}'])

    nb = read(tmp_py)
    assert "formats" not in nb.metadata["jupytext"]

    with pytest.raises(SystemExit):
        jupytext(["--to", "ipynb", tmp_py, "--update-metadata", '{"incorrect": "JSON"'])

    out, err = capsys.readouterr()
    assert "invalid" in err


@pytest.mark.requires_user_kernel_python3
def test_set_kernel_inplace(python_file, tmpdir):
    tmp_py = str(tmpdir.join("notebook.py"))

    copyfile(python_file, tmp_py)

    jupytext([tmp_py, "--set-kernel", "-"])

    nb = read(tmp_py)
    kernel_name = nb.metadata["kernelspec"]["name"]
    cmd = get_kernel_spec(kernel_name).argv[0]
    assert cmd == "python" or os.path.samefile(cmd, sys.executable)


@pytest.mark.requires_user_kernel_python3
def test_set_kernel_auto(python_file, tmpdir):
    tmp_py = str(tmpdir.join("notebook.py"))
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))

    copyfile(python_file, tmp_py)

    jupytext(["--to", "ipynb", tmp_py, "--set-kernel", "-"])

    nb = read(tmp_ipynb)
    kernel_name = nb.metadata["kernelspec"]["name"]
    cmd = get_kernel_spec(kernel_name).argv[0]
    assert cmd == "python" or os.path.samefile(cmd, sys.executable)


@pytest.mark.requires_user_kernel_python3
def test_set_kernel_with_name(python_file, tmpdir):
    tmp_py = str(tmpdir.join("notebook.py"))
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))

    copyfile(python_file, tmp_py)

    for kernel in find_kernel_specs():
        jupytext(["--to", "ipynb", tmp_py, "--set-kernel", kernel])

        nb = read(tmp_ipynb)
        assert nb.metadata["kernelspec"]["name"] == kernel

    with pytest.raises(KeyError):
        jupytext(["--to", "ipynb", tmp_py, "--set-kernel", "non_existing_env"])


def test_paired_paths(ipynb_py_file, tmpdir, capsys):
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))
    nb = read(ipynb_py_file)
    nb.metadata.setdefault("jupytext", {})["formats"] = "ipynb,_light.py,_percent.py:percent"
    write(nb, tmp_ipynb)

    jupytext(["--paired-paths", tmp_ipynb])

    out, err = capsys.readouterr()
    assert not err

    formats = nb.metadata.get("jupytext", {}).get("formats")
    assert set(out.splitlines()).union([tmp_ipynb]) == {path for path, _ in paired_paths(tmp_ipynb, "ipynb", formats)}


def test_sync(ipynb_py_file, tmpdir, cwd_tmpdir, capsys):
    tmp_ipynb = "notebook.ipynb"
    tmp_py = "notebook.py"
    tmp_rmd = "notebook.Rmd"
    nb = read(ipynb_py_file)
    write(nb, tmp_ipynb)

    # Test that sync issues a warning when the notebook is not paired
    jupytext(["--sync", tmp_ipynb])
    _, err = capsys.readouterr()
    assert "is not a paired notebook" in err

    # Now with a pairing information
    nb.metadata.setdefault("jupytext", {})["formats"] = "py,Rmd,ipynb"
    write(nb, tmp_ipynb)

    # Test that missing files are created
    jupytext(["--sync", tmp_ipynb])

    assert os.path.isfile(tmp_py)
    compare_notebooks(read(tmp_py), nb)

    assert os.path.isfile(tmp_rmd)
    compare_notebooks(read(tmp_rmd), nb, "Rmd")

    write(nb, tmp_rmd, fmt="Rmd")
    jupytext(["--sync", tmp_ipynb])

    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb, "Rmd", compare_outputs=True)

    write(nb, tmp_py, fmt="py")
    jupytext(["--sync", tmp_ipynb])

    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb, compare_outputs=True)

    # Finally we recreate the ipynb
    os.remove(tmp_ipynb)

    time.sleep(0.1)
    jupytext(["--sync", tmp_py])

    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb)

    # ipynb must be older than py file, otherwise our Contents Manager will complain
    assert os.path.getmtime(tmp_ipynb) <= os.path.getmtime(tmp_py)


@pytest.mark.requires_pandoc
def test_sync_pandoc(ipynb_to_pandoc, tmpdir, cwd_tmpdir, capsys):
    tmp_ipynb = "notebook.ipynb"
    tmp_md = "notebook.md"
    nb = read(ipynb_to_pandoc)
    write(nb, tmp_ipynb)

    # Test that sync issues a warning when the notebook is not paired
    jupytext(["--sync", tmp_ipynb])
    _, err = capsys.readouterr()
    assert "is not a paired notebook" in err

    # Now with a pairing information
    nb.metadata.setdefault("jupytext", {})["formats"] = "ipynb,md:pandoc"
    write(nb, tmp_ipynb)

    # Test that missing files are created
    jupytext(["--sync", tmp_ipynb])

    assert os.path.isfile(tmp_md)
    compare_notebooks(read(tmp_md), nb, "md:pandoc")

    with open(tmp_md) as fp:
        assert "pandoc" in fp.read()


def test_cli_can_infer_jupytext_format(ipynb_py_R_jl_file, ipynb_py_R_jl_ext, tmpdir, cwd_tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_text = "notebook" + ipynb_py_R_jl_ext
    nb = read(ipynb_py_R_jl_file)

    # Light format to Jupyter notebook
    write(nb, tmp_text)
    jupytext(["--to", "notebook", tmp_text])
    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb)

    # Percent format to Jupyter notebook
    write(nb, tmp_text, fmt=ipynb_py_R_jl_ext + ":percent")
    jupytext(["--to", "notebook", tmp_text])
    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb)


def test_cli_to_script(ipynb_py_R_jl_file, ipynb_py_R_jl_ext, tmpdir, cwd_tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_text = "notebook" + ipynb_py_R_jl_ext
    nb = read(ipynb_py_R_jl_file)

    write(nb, tmp_ipynb)
    jupytext(["--to", "script", tmp_ipynb])
    nb2 = read(tmp_text)
    compare_notebooks(nb2, nb)


def test_cli_to_auto(ipynb_py_R_jl_file, ipynb_py_R_jl_ext, tmpdir, cwd_tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_text = "notebook" + ipynb_py_R_jl_ext
    nb = read(ipynb_py_R_jl_file)

    write(nb, tmp_ipynb)
    jupytext(["--to", "auto", tmp_ipynb])
    nb2 = read(tmp_text)
    compare_notebooks(nb2, nb)


def test_cli_can_infer_jupytext_format_from_stdin(ipynb_py_file, tmpdir, cwd_tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_py = "notebook.py"
    tmp_rmd = "notebook.Rmd"
    nb = read(ipynb_py_file)

    # read ipynb notebook on stdin, write to python
    with open(ipynb_py_file) as fp, mock.patch("sys.stdin", fp):
        jupytext(["--to", "py:percent", "-o", tmp_py])
    nb2 = read(tmp_py)
    compare_notebooks(nb2, nb)

    # read python notebook on stdin, write to ipynb
    with open(tmp_py) as fp, mock.patch("sys.stdin", fp):
        jupytext(["-o", tmp_ipynb])
    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb)

    # read ipynb notebook on stdin, write to R markdown
    with open(ipynb_py_file) as fp, mock.patch("sys.stdin", fp):
        jupytext(["-o", tmp_rmd])
    nb2 = read(tmp_rmd)
    compare_notebooks(nb2, nb, "Rmd")

    # read markdown notebook on stdin, write to ipynb
    with open(tmp_rmd) as fp, mock.patch("sys.stdin", fp):
        jupytext(["-o", tmp_ipynb])
    nb2 = read(tmp_ipynb)
    compare_notebooks(nb2, nb, "Rmd")


@pytest.mark.requires_user_kernel_python3
def test_set_kernel_works_with_pipes_326(capsys):
    md = """```python
1 + 1
```"""

    with mock.patch("sys.stdin", StringIO(md)):
        jupytext(["--to", "ipynb", "--set-kernel", "-", "-"])

    out, err = capsys.readouterr()
    assert err == ""
    nb = reads(out, "ipynb")
    assert "kernelspec" in nb.metadata


@pytest.mark.filterwarnings("ignore:The --pre-commit argument is deprecated")
def test_cli_expect_errors(tmp_ipynb):
    with pytest.raises(ValueError):
        jupytext([])
    with pytest.raises(ValueError):
        jupytext(["--sync"])
    with pytest.raises(ValueError):
        jupytext([tmp_ipynb, tmp_ipynb, "--paired-paths"])
    with pytest.raises(ValueError):
        jupytext(["--pre-commit", "notebook.ipynb"])
    with pytest.raises(ValueError):
        jupytext(["notebook.ipynb", "--from", "py:percent", "--to", "md"])
    with pytest.raises(ValueError):
        jupytext([])
    with pytest.raises((SystemExit, TypeError)):  # SystemExit on Windows, TypeError on Linux
        system("jupytext", ["notebook.ipynb", "--from", "py:percent", "--to", "md"])


@pytest.mark.filterwarnings(
    "error",
    "ignore:You might have passed a file name to the '--to' option, "
    "when a format description was expected. "
    "Maybe you want to use the '-o' option instead?",
)
def test_format_prefix_suffix(tmpdir, cwd_tmpdir):
    os.makedirs("notebooks")
    tmp_ipynb = "notebooks/notebook_name.ipynb"
    tmp_py = "scripts/notebook_name.py"
    write(new_notebook(), tmp_ipynb)

    jupytext([tmp_ipynb, "--to", "../scripts//py"])
    assert os.path.isfile(tmp_py)
    os.remove(tmp_py)

    jupytext([tmp_ipynb, "--to", "scripts//py", "--from", "notebooks//ipynb"])
    assert os.path.isfile(tmp_py)
    os.remove(tmp_py)

    tmp_ipynb = "notebooks/nb_prefix_notebook_name.ipynb"
    tmp_py = "scripts/script_prefix_notebook_name.py"
    write(new_notebook(), tmp_ipynb)

    jupytext(
        [
            tmp_ipynb,
            "--to",
            "scripts/script_prefix_/py",
            "--from",
            "notebooks/nb_prefix_/ipynb",
        ]
    )
    assert os.path.isfile(tmp_py)
    os.remove(tmp_py)

    tmp_ipynb = "notebooks/nb_prefix_notebook_name_nb_suffix.ipynb"
    tmp_py = "scripts/script_prefix_notebook_name_script_suffix.py"
    write(new_notebook(), tmp_ipynb)

    jupytext(
        [
            tmp_ipynb,
            "--to",
            "scripts/script_prefix_/_script_suffix.py",
            "--from",
            "notebooks/nb_prefix_/_nb_suffix.ipynb",
        ]
    )
    assert os.path.isfile(tmp_py)
    os.remove(tmp_py)


def test_cli_sync_file_with_suffix(tmpdir, cwd_tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_pct_py = "notebook.pct.py"
    tmp_lgt_py = "notebook.lgt.py"
    tmp_rmd = "notebook.Rmd"
    nb = new_notebook(
        cells=[new_code_cell(source="1+1")],
        metadata={"jupytext": {"formats": "ipynb,.pct.py:percent,.lgt.py:light,Rmd"}},
    )

    write(nb, tmp_pct_py, fmt=".pct.py:percent")
    jupytext(["--sync", tmp_pct_py])
    assert os.path.isfile(tmp_lgt_py)
    assert os.path.isfile(tmp_rmd)
    assert os.path.isfile(tmp_ipynb)

    jupytext(["--sync", tmp_lgt_py])
    jupytext(["--sync", tmp_ipynb])

    with open(tmp_lgt_py) as fp:
        assert fp.read().splitlines()[-2:] == ["", "1+1"]
    with open(tmp_pct_py) as fp:
        fp.read().splitlines()[-3:] == ["", "# %%", "1+1"]
    with open(tmp_rmd) as fp:
        fp.read().splitlines()[-4:] == ["", "```{python}", "1+1", "```"]


def test_cli_sync_file_with_prefix_974(tmp_path, python_notebook):
    """Only the files that are in the example directory and that start with 'example' should be paired"""
    (tmp_path / "pyproject.toml").write_text(
        """[tool.jupytext]
formats = "examples//example/ipynb,examples//example/py:percent"
"""
    )

    write(python_notebook, tmp_path / "example_notebook.ipynb")
    (tmp_path / "examples" / "folder1").mkdir(parents=True)
    write(python_notebook, tmp_path / "examples/folder1/utils.py")
    write(python_notebook, tmp_path / "examples/folder1/example_paired.ipynb")

    jupytext(
        [
            "--sync",
            str(tmp_path / "example_notebook.ipynb"),
            str(tmp_path / "examples/folder1/utils.py"),
            str(tmp_path / "examples/folder1/example_paired.ipynb"),
        ]
    )

    assert not (tmp_path / "example_notebook.py").exists(), "Not in the 'examples' directory"
    assert not (tmp_path / "examples/folder1/utils_not_paired.ipynb").exists(), "Not with the 'example' prefix"
    assert (tmp_path / "examples/folder1/example_paired.py").exists(), "Paired"


def test_remove_jupytext_metadata(tmpdir, cwd_tmpdir):
    tmp_ipynb = "notebook.ipynb"
    nb = new_notebook(
        metadata={
            "jupytext": {
                "main_language": "python",
                "text_representation": {
                    "extension": ".md",
                    "format_name": "markdown",
                    "format_version": "1.0",
                    "jupytext_version": "0.8.6",
                },
            }
        }
    )

    nbformat.write(nb, tmp_ipynb, version=nbformat.NO_CONVERT)
    # Jupytext removes the 'text_representation' information from the notebook
    jupytext([tmp_ipynb, "--update-metadata", '{"jupytext":{"main_language":null}}'])
    nb2 = read(tmp_ipynb)
    assert not nb2.metadata

    nbformat.write(nb, tmp_ipynb, version=nbformat.NO_CONVERT)
    jupytext([tmp_ipynb, "--set-formats", "ipynb,py:light"])

    nb2 = read(tmp_ipynb)
    assert nb2.metadata == {"jupytext": {"formats": "ipynb,py:light", "main_language": "python"}}


@pytest.mark.parametrize("fmt", ["py:light", "py:percent", "md"])
def test_convert_and_update_preserves_notebook(ipynb_py_file, fmt, tmpdir, cwd_tmpdir):
    # cannot encode magic parameters in markdown yet
    if ("magic" in ipynb_py_file or "LateX" in ipynb_py_file) and fmt == "md":
        return

    tmp_ipynb = "notebook.ipynb"
    copyfile(ipynb_py_file, tmp_ipynb)
    ext = long_form_one_format(fmt)["extension"]
    tmp_text = "notebook" + ext

    jupytext(["--to", fmt, tmp_ipynb])
    jupytext(["--to", "ipynb", "--update", tmp_text])

    nb_org = read(ipynb_py_file)
    nb_now = read(tmp_ipynb)

    # The cell marker changes from """ to r""" on the LateX notebook #836
    if "LateX" in ipynb_py_file and fmt == "py:percent":
        last_cell = nb_now.cells[-1]
        last_cell.metadata["cell_marker"] = last_cell.metadata["cell_marker"][1:]

    compare(nb_now, nb_org)


def test_incorrect_notebook_causes_early_exit(tmpdir, cwd_tmpdir):
    incorrect_ipynb = "incorrect.ipynb"
    incorrect_md = "incorrect.md"
    with open(incorrect_ipynb, "w") as fp:
        fp.write('{"nbformat": 4, "nbformat_minor": 2, "metadata": {INCORRECT}, "cells": []}')

    correct_ipynb = "correct.ipynb"
    correct_md = "correct.md"
    with open(correct_ipynb, "w") as fp:
        fp.write('{"nbformat": 4, "nbformat_minor": 2, "metadata": {}, "cells": []}')

    with pytest.raises(nbformat.reader.NotJSONError, match="Notebook does not appear to be JSON"):
        jupytext([incorrect_ipynb, correct_ipynb, "--to", "md"])

    assert not os.path.exists(incorrect_md)
    assert not os.path.exists(correct_md)


def test_warn_only_skips_incorrect_notebook(tmpdir, cwd_tmpdir, capsys):
    incorrect_ipynb = "incorrect.ipynb"
    incorrect_md = "incorrect.md"
    with open(incorrect_ipynb, "w") as fp:
        fp.write('{"nbformat": 4, "nbformat_minor": 2, "metadata": {INCORRECT}, "cells": []}')

    correct_ipynb = "correct.ipynb"
    correct_md = "correct.md"
    with open(correct_ipynb, "w") as fp:
        fp.write('{"nbformat": 4, "nbformat_minor": 2, "metadata": {}, "cells": []}')

    jupytext([incorrect_ipynb, correct_ipynb, "--to", "md", "--warn-only"])

    _, err = capsys.readouterr()
    assert "Notebook does not appear to be JSON" in str(err)

    assert not os.path.exists(incorrect_md)
    assert os.path.exists(correct_md)


@pytest.mark.parametrize("fmt", ["md", "Rmd", "py", "py:percent", "py:hydrogen"])
def test_339_ipynb(tmpdir, cwd_tmpdir, fmt):
    tmp_ipynb = "test.ipynb"
    nb = new_notebook(cells=[new_code_cell("cat = 42")])
    nbformat.write(nb, tmp_ipynb)

    assert jupytext([tmp_ipynb, "--to", fmt, "--test-strict"]) == 0


def test_339_py(tmpdir, cwd_tmpdir):
    """Test that an incorrect round trip conversion on the text file is detected"""
    tmp_py = "test.py"
    with open(tmp_py, "w") as fp:
        fp.write(
            """# %%
cat = 42
"""
        )

    def erroneous_is_magic(line, language, comment_magics, explicitly_code):
        return "cat" in line

    with mock.patch("jupytext.magics.is_magic", erroneous_is_magic):
        assert jupytext([tmp_py, "--to", "ipynb", "--test-strict"]) != 0


def test_339_require_to(tmpdir, cwd_tmpdir):
    """Test that the `--to` argument is asked for when a `--test` command is provided"""
    with pytest.raises(ValueError, match="--to"):
        jupytext(["test.py", "--test-strict"])


def test_399_to_script_then_set_formats(tmpdir, cwd_tmpdir):
    nb = new_notebook(cells=[new_code_cell("1 + 1")])
    tmp_py = "notebook_first.py"
    tmp_ipynb = "notebook_first.ipynb"
    nbformat.write(nb, tmp_ipynb)

    jupytext(["--to", "py:percent", tmp_ipynb])
    assert os.path.isfile(tmp_py)

    jupytext(["--set-formats", "ipynb,py:percent", tmp_ipynb])


def test_set_format_with_subfolder(tmpdir, cwd_tmpdir):
    """Here we reproduce issue #450"""
    py = """# %% [markdown]
# A short notebook
"""

    tmpdir.mkdir("python_scripts").join("01_tabular_data_exploration.py").write(py)

    jupytext(
        [
            "--set-formats",
            "python_scripts//py:percent,notebooks//ipynb",
            "python_scripts/01_tabular_data_exploration.py",
        ]
    )


def skip_if_format_missing(format_name):
    """Check whether MyST or Pandoc are available and skip if not"""
    if format_name == "md:myst" and not is_myst_available():
        pytest.skip("MyST markdown is not available")
    elif format_name == "md:pandoc" and not is_pandoc_available():
        pytest.skip("Pandoc is not available")


@pytest.mark.parametrize("format_name", ["md", "md:myst", "md:pandoc"])
def test_create_header_with_set_formats(format_name, cwd_tmpdir, tmpdir):
    """Test jupytext --set-formats <format_name> #485"""

    skip_if_format_missing(format_name)

    tmpdir.join("notebook.md").write("\n")

    jupytext(["--set-formats", format_name, "notebook.md"])

    nb = read("notebook.md")
    assert nb["metadata"]["jupytext"]["formats"] == format_name


@pytest.mark.requires_user_kernel_python3
@pytest.mark.parametrize("format_name", ["md", "md:myst", "md:pandoc", "py:light", "py:percent"])
def test_create_header_with_set_formats_and_set_kernel(format_name, tmpdir, cwd_tmpdir):
    """Test jupytext --set-formats <format_name> --set-kernel - #485"""

    skip_if_format_missing(format_name)

    ext = format_name.split(":")[0]
    tmp_nb = "notebook." + ext
    tmpdir.join(tmp_nb).write("\n")

    jupytext(["--set-formats", format_name, "--set-kernel", "-", tmp_nb])

    nb = read(tmp_nb)
    assert nb["metadata"]["jupytext"]["formats"] == format_name
    assert "kernelspec" in nb["metadata"]


def test_set_option_split_at_heading(tmpdir, cwd_tmpdir):
    tmp_rmd = tmpdir.join("notebook.Rmd")
    tmp_rmd.write(
        """A paragraph

# H1 Header
"""
    )

    jupytext(["notebook.Rmd", "--opt", "split_at_heading=true"])
    assert "split_at_heading: true" in tmp_rmd.read()
    nb = read("notebook.Rmd")

    nb_expected = new_notebook(cells=[new_markdown_cell("A paragraph"), new_markdown_cell("# H1 Header")])
    compare_notebooks(nb, nb_expected)


def test_pair_in_tree(tmpdir):
    nb_file = tmpdir.mkdir("notebooks").mkdir("subfolder").join("example.ipynb")
    py_file = tmpdir.mkdir("scripts").mkdir("subfolder").join("example.py")

    write(new_notebook(cells=[new_markdown_cell("A markdown cell")]), str(nb_file))

    jupytext(["--set-formats", "notebooks///ipynb,scripts///py:percent", str(nb_file)])

    assert py_file.exists()
    assert "A markdown cell" in py_file.read()


def test_pair_in_tree_and_parent(tmpdir):
    nb_file = tmpdir.mkdir("notebooks").mkdir("subfolder").mkdir("a").mkdir("b").join("example.ipynb")
    py_file = tmpdir.mkdir("scripts").mkdir("subfolder").mkdir("c").join("example.py")

    write(new_notebook(cells=[new_markdown_cell("A markdown cell")]), str(nb_file))

    jupytext(["--set-formats", "notebooks//a/b//ipynb,scripts//c//py:percent", str(nb_file)])

    assert py_file.exists()
    assert "A markdown cell" in py_file.read()


@pytest.mark.requires_pandoc
def test_sync_pipe_config(tmpdir):
    """Sync a notebook to a script paired in a tree, and reformat the markdown cells using pandoc"""

    tmpdir.join("jupytext.toml").write(
        """# By default, the notebooks in this repository are in the notebooks subfolder
# and they are paired to scripts in the script subfolder.
formats = "notebooks///ipynb,scripts///py:percent"
"""
    )

    nb_file = tmpdir.mkdir("notebooks").join("wrap_markdown.ipynb")
    long_text = "This is a " + ("very " * 24) + "long sentence."
    assert len(long_text) > 100
    nb = new_notebook(cells=[new_markdown_cell(long_text)])
    write(nb, str(nb_file))

    jupytext(
        [
            "--sync",
            "--pipe-fmt",
            "ipynb",
            "--pipe",
            "pandoc --from ipynb --to ipynb --markdown-headings=atx",
            str(nb_file),
        ]
    )

    py_text = tmpdir.join("scripts").join("wrap_markdown.py").read()
    assert "This is a very very" in py_text
    for line in py_text.splitlines():
        assert len(line) <= 79

    nb = read(nb_file, as_version=4)
    text = nb.cells[0].source
    assert len(text.splitlines()) == 3
    assert text != long_text


def test_sync_script_dotdot_folder_564(tmpdir):
    """Reproduce the setting of issue #564"""
    nb_file = tmpdir.mkdir("colabs").mkdir("colabs").join("rigid_object_tutorial.ipynb")
    py_file = tmpdir.join("colabs").mkdir("nb_python").join("rigid_object_tutorial.py")
    py_file.write("1 + 1\n")

    jupytext(["--set-formats", "../nb_python//py:percent,../colabs//ipynb", str(py_file)])

    assert nb_file.exists()

    jupytext(["--sync", str(py_file)])
    jupytext(["--sync", str(nb_file)])


def test_jupytext_to_file_emits_a_warning(tmpdir):
    """The user may type
        jupytext notebook.ipynb --to script.py
    meaning
        jupytext notebook.ipynb -o script.py
    """
    os.chdir(str(tmpdir))

    nb_file = tmpdir.join("notebook.ipynb")
    write(new_notebook(), str(nb_file))

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        jupytext(["notebook.ipynb", "-o", "script.py"])

    with pytest.warns(UserWarning, match="Maybe you want to use the '-o' option"):
        jupytext(["notebook.ipynb", "--to", "script.py"])


def test_jupytext_set_formats_file_gives_an_informative_error(tmpdir, cwd_tmpdir):
    """The user may type
        jupytext --set-formats notebook.md
    meaning
        jupytext --sync notebook.md
    """
    cfg_file = tmpdir.join("jupytext.toml")
    cfg_file.write('formats = "md,ipynb,py:percent"')

    md_file = tmpdir.join("notebook.md")
    py_file = tmpdir.join("notebook.py")
    nb_file = tmpdir.join("notebook.ipynb")
    md_file.write("Some text")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        jupytext(["--sync", "notebook.md"])

    assert py_file.exists()
    assert nb_file.exists()

    with pytest.raises(ValueError, match="jupytext --sync notebook.md"):
        jupytext(["--set-formats", "notebook.md"])

    # Remove the config file, otherwise test_jupytext_jupyter_fs_metamanager fails later on!
    cfg_file.remove()


def test_diff(tmpdir, cwd_tmpdir, capsys):
    write(new_notebook(cells=[new_code_cell("1 + 1")]), "test.ipynb")
    write(new_notebook(cells=[new_code_cell("2 + 2")]), "test.py", fmt="py:percent")

    jupytext(["--diff", "test.py", "test.ipynb"])
    captured = capsys.readouterr()
    assert "-2 + 2\n+1 + 1" in captured.out


def test_show_changes(tmpdir, cwd_tmpdir, capsys):
    write(new_notebook(cells=[new_code_cell("1 + 1")]), "test.ipynb")
    write(new_notebook(cells=[new_code_cell("2 + 2")]), "test.py", fmt="py:percent")

    jupytext(["--to", "py:percent", "test.ipynb", "--show-changes"])
    captured = capsys.readouterr()
    assert "-2 + 2\n+1 + 1" in captured.out


def test_glob_recursive(tmpdir, cwd_tmpdir):
    tmpdir.mkdir("subfolder").join("test.py").write("1 + 1\n")
    tmpdir.join("test.py").write("2 + 2\n")
    jupytext(["--to", "ipynb", "**/*.py"])

    assert tmpdir.join("test.ipynb").isfile()
    assert tmpdir.join("subfolder").join("test.ipynb").isfile()


def test_jupytext_sync_preserves_cell_ids(tmpdir, cwd_tmpdir, notebook_with_outputs):
    write(notebook_with_outputs, "test.ipynb")

    # Sync with a py file, this should not change the cell id
    jupytext(["--set-formats", "ipynb,py:percent", "test.ipynb"])
    nb = read("test.ipynb")
    assert nb.cells[0].source == "1+1"
    assert nb.cells[0].id == notebook_with_outputs.cells[0].id

    # Change the py file and sync. This should not change the cell id neither
    py_nb = tmpdir.join("test.py")
    py = py_nb.read()
    py_nb.write(py.replace("1+1", "2+2"))

    jupytext(["--sync", "test.ipynb"])
    nb = read("test.ipynb")
    assert nb.cells[0].source == "2+2"
    assert nb.cells[0].id == notebook_with_outputs.cells[0].id


def test_jupytext_update_preserves_cell_ids(tmpdir, cwd_tmpdir, notebook_with_outputs):
    write(notebook_with_outputs, "test.ipynb")

    # Sync with a py file, this should not change the cell id
    jupytext(["--to", "py:percent", "test.ipynb"])
    nb = read("test.ipynb")
    assert nb.cells[0].source == "1+1"
    assert nb.cells[0].id == notebook_with_outputs.cells[0].id

    # Change the py file and update the ipynb file.
    # This should not change the cell id neither
    py_nb = tmpdir.join("test.py")
    py = py_nb.read()
    py_nb.write(py.replace("1+1", "2+2"))

    jupytext(["--to", "notebook", "--update", "test.py"])
    nb = read("test.ipynb")
    assert nb.cells[0].source == "2+2"
    assert nb.cells[0].id == notebook_with_outputs.cells[0].id


def test_jupytext_to_ipynb_suggests_update(tmpdir, cwd_tmpdir, capsys):
    tmpdir.join("test.py").write("1 + 1\n")
    jupytext(["--to", "ipynb", "test.py"])
    capture = capsys.readouterr()
    assert "update" not in capture.out

    jupytext(["--to", "ipynb", "test.py"])
    capture = capsys.readouterr()
    assert "update" in capture.out


@pytest.mark.parametrize("formats", ["", "py:percent", "py", "py:percent,ipynb"])
def test_jupytext_to_ipynb_does_not_update_timestamp_if_output_not_in_pair(
    tmpdir, cwd_tmpdir, python_notebook, capsys, formats
):
    # Write a text notebook
    nb = python_notebook
    if formats:
        nb.metadata["jupytext"] = {"formats": formats}

    test_py = tmpdir.join("test.py")
    write(nb, str(test_py))

    # make it read-only
    test_py.chmod(0o444)

    # py -> ipynb
    if "ipynb" not in formats:
        jupytext(["--to", "ipynb", "test.py"])
    else:
        jupytext(["--to", "ipynb", "test.py", "-o", "another.ipynb"])

    capture = capsys.readouterr()
    assert "Updating the timestamp" not in capture.out


@pytest.mark.parametrize("formats", ["py:percent", "py", None])
def test_jupytext_to_ipynb_does_not_update_timestamp_if_not_paired(tmpdir, cwd_tmpdir, python_notebook, capsys, formats):
    # Write a text notebook
    nb = python_notebook
    if formats:
        nb.metadata["jupytext"] = {"formats": formats}

    test_py = tmpdir.join("test.py")
    write(nb, str(test_py))

    # make it read-only
    test_py.chmod(0o444)

    # py -> ipynb
    jupytext(["--to", "ipynb", "test.py"])

    capture = capsys.readouterr()
    assert "Updating the timestamp" not in capture.out


@pytest.mark.asyncio
@pytest.mark.parametrize("formats", ["ipynb,py", "py:percent", "py:light", None])
async def test_use_source_timestamp(tmpdir, cwd_tmpdir, python_notebook, capsys, formats, cm):
    # Write a text notebook
    nb = python_notebook
    if formats:
        nb.metadata["jupytext"] = {"formats": formats}

    test_py = tmpdir.join("test.py")
    test_ipynb = tmpdir.join("test.ipynb")
    write(nb, str(test_py))
    src_timestamp = test_py.stat().mtime

    # Wait...
    time.sleep(0.1)

    # py -> ipynb
    jupytext(["--to", "ipynb", "test.py", "--use-source-timestamp"])

    capture = capsys.readouterr()
    assert "Updating the timestamp" not in capture.out

    dest_timestamp = test_ipynb.stat().mtime
    # on Mac OS the dest_timestamp is truncated at the microsecond (#790)
    assert src_timestamp - 1e-6 <= dest_timestamp <= src_timestamp

    # Make sure that we can open the file in Jupyter

    cm.outdated_text_notebook_margin = 0.001
    cm.root_dir = str(tmpdir)

    # No error here
    await ensure_async(cm.get("test.ipynb"))

    # But now if we don't use --use-source-timestamp
    jupytext(["--to", "ipynb", "test.py"])
    os.utime(test_py, (src_timestamp, src_timestamp))

    # Then we can't open paired notebooks
    if formats == "ipynb,py:percent":
        from tornado.web import HTTPError

        with pytest.raises(HTTPError, match="is more recent than test.py"):
            await ensure_async(cm.get("test.ipynb"))
    else:
        await ensure_async(cm.get("test.ipynb"))


def test_round_trip_with_null_metadata_792(tmpdir, cwd_tmpdir, python_notebook):
    nb = python_notebook
    nb.metadata.kernelspec = {
        "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Python 3",
        "env": None,
        "interrupt_mode": "signal",
        "language": "python",
        "metadata": None,
        "name": "python3",
    }
    write(nb, "test.ipynb")
    jupytext(["--to", "py:percent", "test.ipynb"])
    jupytext(["--to", "ipynb", "test.py"])
    nb = read("test.ipynb")
    assert nb.metadata.kernelspec.env is None


def test_set_shebang_with_update_metadata(tmp_path, python_notebook):
    tmp_py = tmp_path / "nb.py"
    write(python_notebook, tmp_py, fmt="py:percent")

    jupytext(
        [
            str(tmp_py),
            "--update-metadata",
            '{"jupytext":{"executable":"/usr/bin/python"}}',
        ]
    )

    assert tmp_py.read_text().startswith("#!/usr/bin/python")


@pytest.mark.parametrize("compare_ids", [False, True])
@pytest.mark.parametrize("compare_outputs", [False, True])
def test_set_formats_does_not_override_existing_ipynb(tmp_path, notebook_with_outputs, compare_ids, compare_outputs):
    tmp_py = tmp_path / "nb.py"
    tmp_ipynb = tmp_path / "nb.ipynb"
    write(notebook_with_outputs, tmp_ipynb)

    jupytext([str(tmp_ipynb), "--set-formats", "ipynb,py:percent"])
    jupytext([str(tmp_py), "--set-formats", "ipynb,py:percent"])

    nb = read(tmp_ipynb)
    compare_notebooks(
        nb,
        notebook_with_outputs,
        compare_ids=compare_ids,
        compare_outputs=compare_outputs,
    )


@pytest.mark.requires_myst
@pytest.mark.parametrize(
    "header",
    [
        "",
        """---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: ipython3
  language: python
  name: ipython3
---

""",
    ],
)
def test_lexer_is_preserved_in_round_trips(
    tmp_path,
    no_jupytext_version_number,
    header,
    text="""```{code-cell} ipython3
1 + 1
```
""",
):
    text = header + text
    tmp_md = tmp_path / "notebook.md"
    tmp_md.write_text(text)

    jupytext(["--to", "myst", str(tmp_md)])

    assert tmp_md.read_text() == text


@pytest.mark.requires_black
def test_pipe_with_quiet_does_not_print(tmp_path, capsys):
    tmp_py = tmp_path / "nb.py"
    tmp_py.write_text("# %%\n1+1\n")

    jupytext(["--quiet", "--pipe", "black", str(tmp_py)])
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert tmp_py.read_text() == "# %%\n1 + 1\n"


def test_quiet_does_not_print_when_creating_missing_directory(tmp_path, monkeypatch, capsys):
    """In quiet mode, jupytext should not print a warning when creating a missing directory (#1285)"""
    monkeypatch.chdir(tmp_path)
    tmp_py = tmp_path / "script.py"
    tmp_py.write_text("# %%\n1+1\n")

    output_dir = tmp_path / "jupyter_execute"
    assert not output_dir.exists()

    # The double slash in './jupyter_execute//ipynb' is the jupytext syntax for a prefix directory
    jupytext(["--quiet", "script.py", "--to", "./jupyter_execute//ipynb"])
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert output_dir.exists()
    assert (output_dir / "script.ipynb").exists()


def test_update_formats_1386(python_notebook, tmp_path, capsys):
    """
    Test that we can change the formats in an already paired notebook
    """
    tmp_py = tmp_path / "notebook.py"
    tmp_md = tmp_path / "notebook.md"
    tmp_ipynb = tmp_path / "notebook.ipynb"
    write(python_notebook, tmp_py, fmt="py:percent")

    formats = "py:percent,md"
    jupytext([str(tmp_py), "--set-formats", formats])

    # We need to update all the files, not only their timestamps
    capture = capsys.readouterr()
    assert "Updating the timestamp" not in capture.out

    # Each paired file should have the new formats
    assert read(tmp_py)["metadata"]["jupytext"]["formats"] == formats
    assert read(tmp_md)["metadata"]["jupytext"]["formats"] == formats

    # The issue occurred when the py file was older than the md file
    current_time = time.time()
    os.utime(tmp_py, (current_time - 1, current_time - 1))
    os.utime(tmp_md, (current_time, current_time))

    formats = "ipynb,py:percent,md"
    jupytext([str(tmp_py), "--set-formats", formats])

    # We need to update all the files, not only their timestamps
    capture = capsys.readouterr()
    assert "Updating the timestamp" not in capture.out

    # And each paired file should have the new formats
    assert read(tmp_py)["metadata"]["jupytext"]["formats"] == formats
    assert read(tmp_md)["metadata"]["jupytext"]["formats"] == formats
    assert read(tmp_ipynb)["metadata"]["jupytext"]["formats"] == formats


def test_paired_paths_from_notebook_metadata(tmp_path, python_notebook, capsys):
    ipynb_notebook_path = tmp_path / "notebook.ipynb"
    python_notebook.metadata["jupytext"] = {"formats": "ipynb,py:percent,md"}
    write(python_notebook, ipynb_notebook_path)

    jupytext([str(ipynb_notebook_path), "--paired-paths"])

    capture = capsys.readouterr()

    paired_paths = capture.out.strip().split("\n")

    assert paired_paths == [
        str(tmp_path / "notebook.py"),
        str(tmp_path / "notebook.md"),
    ], paired_paths


def test_paired_paths_from_config(tmp_path, python_notebook, capsys):
    ipynb_notebook_path = tmp_path / "notebook.ipynb"
    write(python_notebook, ipynb_notebook_path)
    (tmp_path / "jupytext.toml").write_text('''formats="ipynb,py:percent,md"''')

    jupytext([str(ipynb_notebook_path), "--paired-paths"])

    capture = capsys.readouterr()

    paired_paths = capture.out.strip().split("\n")

    assert paired_paths == [
        str(tmp_path / "notebook.py"),
        str(tmp_path / "notebook.md"),
    ], paired_paths


@pytest.mark.parametrize("with_config", [False, True])
def test_sync_keeps_simple_python_file_unchanged(tmp_path, with_config: bool):
    """Test that jupytext --sync on a simple Python file leaves it unchanged,
    even if a Jupytext configuration has formats=ipynb,py:percent
    """
    # Create a simple Python file without jupytext metadata
    if with_config:
        config_file = tmp_path / "jupytext.toml"
        config_file.write_text('formats = "ipynb,py:percent"')

    py_file = tmp_path / "simple.py"
    py_content = '''#!/usr/bin/env python3
"""A simple Python script"""

def hello():
    print("Hello, world!")

if __name__ == "__main__":
    hello()
'''
    py_file.write_text(py_content)

    # Record original timestamp and content
    original_mtime = py_file.stat().st_mtime
    original_content = py_file.read_text()

    # Wait a bit to ensure timestamp would change if file was modified
    time.sleep(0.1)

    # Run jupytext --sync on the file
    jupytext(["--sync", str(py_file)])

    # Verify file is unchanged
    final_mtime = py_file.stat().st_mtime
    final_content = py_file.read_text()

    assert final_mtime == original_mtime, "File timestamp should be unchanged"
    assert final_content == original_content, "File content should be unchanged"

    # Verify no additional files were created
    files_in_dir = list(tmp_path.iterdir())
    if with_config:
        assert len(files_in_dir) == 2, f"Expected only 2 files, found: {[f.name for f in files_in_dir]}"
        assert set(files_in_dir) == {py_file, config_file}
    else:
        assert len(files_in_dir) == 1, f"Expected only 1 file, found: {[f.name for f in files_in_dir]}"
        assert files_in_dir[0] == py_file


def test_set_formats_pairing_in_subfolders(tmp_path, python_notebook):
    """Test that jupytext --set-formats works with subfolders, including on Windows (#1028)"""

    ipynb_notebook_dir = tmp_path / "notebooks" / "subfolder"
    ipynb_notebook_dir.mkdir(parents=True)
    ipynb_notebook_path = ipynb_notebook_dir / "notebook.ipynb"

    write(python_notebook, ipynb_notebook_path)

    jupytext([str(ipynb_notebook_path), "--set-formats", "notebooks///ipynb,scripts///py:percent"])

    assert (tmp_path / "scripts" / "subfolder" / "notebook.py").exists()


def test_sync_in_subfolders(tmp_path, python_notebook):
    """Test that jupytext --sync works with subfolders, including on Windows (#1028)"""
    ipynb_notebook_dir = tmp_path / "notebooks" / "subfolder"
    ipynb_notebook_dir.mkdir(parents=True)
    ipynb_notebook_path = ipynb_notebook_dir / "notebook.ipynb"
    write(python_notebook, ipynb_notebook_path)

    (tmp_path / "jupytext.toml").write_text("""[formats]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
""")

    jupytext([str(ipynb_notebook_path), "--sync"])

    assert (tmp_path / "scripts" / "subfolder" / "notebook.py").exists()
