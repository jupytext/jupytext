import os
import unittest.mock as mock

import pytest

import jupytext
from jupytext.cli import jupytext as jupytext_cli
from jupytext.compare import compare
from jupytext.formats import (
    long_form_multiple_formats,
    long_form_one_format,
    short_form_multiple_formats,
)
from jupytext.paired_paths import (
    InconsistentPath,
    base_path,
    base_path_and_adjusted_fmt,
    full_path,
    paired_paths,
)


def test_simple_pair():
    formats = long_form_multiple_formats("ipynb,py")
    expected_paths = ["notebook.ipynb", "notebook.py"]
    compare(
        paired_paths("notebook.ipynb", "ipynb", formats),
        list(zip(expected_paths, formats)),
    )
    compare(paired_paths("notebook.py", "py", formats), list(zip(expected_paths, formats)))


def test_base_path():
    fmt = long_form_one_format("dir/prefix_/ipynb")
    assert base_path("dir/prefix_NAME.ipynb", fmt) == "NAME"
    with pytest.raises(InconsistentPath):
        base_path("dir/incorrect_prefix_NAME.ipynb", fmt)


def test_base_path_dotdot():
    fmt = long_form_one_format("../scripts//py")
    assert base_path("scripts/test.py", fmt=fmt) == "scripts/test"


def test_full_path_dotdot():
    fmt = long_form_one_format("../scripts//py")
    assert full_path("scripts/test", fmt=fmt) == "scripts/test.py"


@pytest.mark.parametrize(
    "formats",
    [
        "notebooks///ipynb,../../../../../../tmp/escape///py:light",
        "notebooks///ipynb,/tmp/escape///py:light",
    ],
)
def test_paired_path_cannot_escape_notebook_tree(formats):
    nb_file = "notebooks/nb.ipynb"
    with pytest.raises(InconsistentPath, match="escapes the directory"):
        paired_paths(nb_file, "notebooks///ipynb", formats)


def test_base_path_in_tree_from_root():
    fmt = long_form_one_format("scripts///py")
    assert base_path("scripts/subfolder/test.py", fmt=fmt) == "//subfolder/test"
    assert base_path("/scripts/subfolder/test.py", fmt=fmt) == "///subfolder/test"


def test_base_path_in_tree_from_non_root():
    fmt = long_form_one_format("scripts///py")
    assert base_path("/parent_folder/scripts/subfolder/test.py", fmt=fmt) == "/parent_folder///subfolder/test"


def test_base_path_in_tree_from_non_root_no_subfolder():
    nb_file = "/parent/notebooks/wrap_markdown.ipynb"
    formats = "notebooks///ipynb,scripts///py:percent"
    fmt = "notebooks///ipynb"
    assert base_path(nb_file, fmt) == "/parent///wrap_markdown"
    paired_paths(nb_file, fmt, formats)


def test_full_path_in_tree_from_root():
    fmt = long_form_one_format("notebooks///ipynb")
    assert full_path("//subfolder/test", fmt=fmt) == "notebooks/subfolder/test.ipynb"
    assert full_path("///subfolder/test", fmt=fmt) == "/notebooks/subfolder/test.ipynb"


def test_full_path_in_tree_from_root_no_subfolder():
    fmt = long_form_one_format("notebooks///ipynb")
    assert full_path("//test", fmt=fmt) == "notebooks/test.ipynb"
    assert full_path("///test", fmt=fmt) == "/notebooks/test.ipynb"


def test_full_path_in_tree_from_non_root():
    fmt = long_form_one_format("notebooks///ipynb")
    assert full_path("/parent_folder///subfolder/test", fmt=fmt) == "/parent_folder/notebooks/subfolder/test.ipynb"


def test_paired_paths_windows():
    nb_file = "C:\\Users\\notebooks\\notebooks\\subfolder\\nb.ipynb"
    formats = "notebooks///ipynb,scripts///py"
    with mock.patch("os.path.sep", "\\"):
        assert base_path(nb_file, "notebooks///ipynb") == "C:\\Users\\notebooks\\//subfolder\\nb"
        paired_paths(nb_file, "notebooks///ipynb", formats)


def test_paired_paths_windows_no_subfolder():
    nb_file = "C:\\Users\\notebooks\\notebooks\\nb.ipynb"
    formats = "notebooks///ipynb,scripts///py"
    with mock.patch("os.path.sep", "\\"):
        assert base_path(nb_file, "notebooks///ipynb") == "C:\\Users\\notebooks\\//nb"
        paired_paths(nb_file, "notebooks///ipynb", formats)


def test_paired_paths_windows_relative():
    """Test Windows pairing with relative paths and backslash as path separator, issue #1028"""
    nb_file = "C:\\notebooks\\example.ipynb"
    formats = "notebooks///ipynb,scripts///py:percent"
    with mock.patch("os.path.sep", "\\"):
        # Should not raise InconsistentPath
        paths = paired_paths(nb_file, "notebooks///ipynb", formats)
        # Verify the notebook path is in the paired paths
        path_list = [p[0] for p in paths]
        assert nb_file in path_list, f"Expected {nb_file} to be in paired paths {path_list}"
        # Verify both paths use backslashes on Windows
        assert paths[0][0] == "C:\\notebooks\\example.ipynb"
        assert paths[1][0] == "C:\\scripts\\example.py"


@pytest.mark.parametrize("os_path_sep", ["\\", "/"])
def test_paired_path_dotdot_564(os_path_sep):
    main_path = os_path_sep.join(["examples", "tutorials", "colabs", "rigid_object_tutorial.ipynb"])
    formats = "../nb_python//py:percent,../colabs//ipynb"
    with mock.patch("os.path.sep", os_path_sep):
        assert base_path(main_path, None, long_form_multiple_formats(formats)) == os_path_sep.join(
            ["examples", "tutorials", "colabs", "rigid_object_tutorial"]
        )
        paired_paths(main_path, "ipynb", formats)


def test_path_in_tree_limited_to_config_dir(tmpdir):
    root_nb_dir = tmpdir.mkdir("notebooks")
    nb_dir = root_nb_dir.mkdir("notebooks")
    src_dir = root_nb_dir.mkdir("scripts")
    other_dir = root_nb_dir.mkdir("other")

    formats = "notebooks///ipynb,scripts///py"
    fmt = long_form_multiple_formats(formats)[0]

    # Notebook in nested 'notebook' dir is paired
    notebook_in_nb_dir = nb_dir.join("subfolder").join("nb.ipynb")

    assert {path for (path, _) in paired_paths(str(notebook_in_nb_dir), fmt, formats)} == {
        str(notebook_in_nb_dir),
        str(src_dir.join("subfolder").join("nb.py")),
    }

    # Notebook in base 'notebook' dir is paired if no config file is found
    notebook_in_other_dir = other_dir.mkdir("subfolder").join("nb.ipynb")
    assert {path for (path, _) in paired_paths(str(notebook_in_other_dir), fmt, formats)} == {
        str(notebook_in_other_dir),
        str(tmpdir.join("scripts").join("other").join("subfolder").join("nb.py")),
    }

    # When a config file exists
    root_nb_dir.join("jupytext.toml").write("\n")

    # Notebook in nested 'notebook' dir is still paired
    assert {path for (path, _) in paired_paths(str(notebook_in_nb_dir), fmt, formats)} == {
        str(notebook_in_nb_dir),
        str(src_dir.join("subfolder").join("nb.py")),
    }

    # But the notebook in base 'notebook' dir is not paired any more
    alert = (
        "Notebook directory '/other/subfolder' does not match prefix root 'notebooks'"
        if os.path.sep == "/"
        # we escape twice the backslash because pytest.raises matches it as a regular expression
        else "Notebook directory '\\\\other\\\\subfolder' does not match prefix root 'notebooks'"
    )
    with pytest.raises(InconsistentPath, match=alert):
        paired_paths(str(notebook_in_other_dir), fmt, formats)


def test_many_and_suffix():
    formats = long_form_multiple_formats("ipynb,.pct.py,_lgt.py")
    expected_paths = ["notebook.ipynb", "notebook.pct.py", "notebook_lgt.py"]
    for fmt, path in zip(formats, expected_paths):
        compare(paired_paths(path, fmt, formats), list(zip(expected_paths, formats)))

    with pytest.raises(InconsistentPath):
        paired_paths("wrong_suffix.py", "py", formats)


def test_prefix_and_suffix():
    short_formats = (
        "notebook_folder/notebook_prefix_/_notebook_suffix.ipynb,"
        "script_folder//_in_percent_format.py:percent,"
        "script_folder//_in_light_format.py"
    )

    formats = long_form_multiple_formats(short_formats)
    assert short_form_multiple_formats(formats) == short_formats

    expected_paths = [
        "parent/notebook_folder/notebook_prefix_NOTEBOOK_NAME_notebook_suffix.ipynb",
        "parent/script_folder/NOTEBOOK_NAME_in_percent_format.py",
        "parent/script_folder/NOTEBOOK_NAME_in_light_format.py",
    ]
    for fmt, path in zip(formats, expected_paths):
        compare(paired_paths(path, fmt, formats), list(zip(expected_paths, formats)))

    # without the parent folder
    expected_paths = [path[7:] for path in expected_paths]
    for fmt, path in zip(formats, expected_paths):
        compare(paired_paths(path, fmt, formats), list(zip(expected_paths, formats)))

    # Not the expected parent folder
    with pytest.raises(InconsistentPath):
        paired_paths(
            "script_folder_incorrect/NOTEBOOK_NAME_in_percent_format.py",
            formats[1],
            formats,
        )

    # Not the expected suffix
    with pytest.raises(InconsistentPath):
        paired_paths("parent/script_folder/NOTEBOOK_NAME_in_LIGHT_format.py", formats[2], formats)

    # Not the expected extension
    with pytest.raises(InconsistentPath):
        paired_paths(
            "notebook_folder/notebook_prefix_NOTEBOOK_NAME_notebook_suffix.py",
            formats[0],
            formats,
        )


def test_prefix_on_root_174():
    short_formats = "ipynb,python//py:percent"

    formats = long_form_multiple_formats(short_formats)
    assert short_form_multiple_formats(formats) == short_formats

    expected_paths = ["Untitled.ipynb", "python/Untitled.py"]
    for fmt, path in zip(formats, expected_paths):
        compare(paired_paths(path, fmt, formats), list(zip(expected_paths, formats)))


def test_duplicated_paths():
    formats = long_form_multiple_formats("ipynb,py:percent,py:light")
    with pytest.raises(InconsistentPath):
        paired_paths("notebook.ipynb", "ipynb", formats)


@pytest.mark.asyncio
async def test_cm_paired_paths(cm):
    cm.paired_notebooks = dict()

    three = "ipynb,py,md"
    cm.update_paired_notebooks("nb.ipynb", three)
    assert cm.paired_notebooks == {"nb." + fmt: (fmt, three) for fmt in three.split(",")}

    two = "ipynb,Rmd"
    cm.update_paired_notebooks("nb.ipynb", two)
    assert cm.paired_notebooks == {"nb." + fmt: (fmt, two) for fmt in two.split(",")}

    one = "ipynb"
    cm.update_paired_notebooks("nb.ipynb", one)
    assert cm.paired_notebooks == {}

    zero = ""
    cm.update_paired_notebooks("nb.ipynb", zero)
    assert cm.paired_notebooks == {}


def test_paired_path_with_prefix(
    nb_file="scripts/test.py",
    fmt={"extension": ".py", "format_name": "percent"},
    formats=[
        {"extension": ".ipynb"},
        {"prefix": "scripts/", "format_name": "percent", "extension": ".py"},
    ],
):
    assert paired_paths(nb_file, fmt, formats) == [
        ("test.ipynb", {"extension": ".ipynb"}),
        (
            "scripts/test.py",
            {"prefix": "scripts/", "format_name": "percent", "extension": ".py"},
        ),
    ]


def test_paired_notebook_ipynb_root_scripts_in_folder_806(tmpdir, cwd_tmpdir, python_notebook):
    """In this test we pair a notebook with a script in a subfolder, and then do some
    natural operations like delete/recreate one of the paired files"""
    # Save sample notebook
    test_ipynb = tmpdir / "test.ipynb"
    jupytext.write(python_notebook, str(test_ipynb))

    # Pair the notebook to a script in a subfolder
    jupytext_cli(["--set-formats", "ipynb,scripts//py:percent", "test.ipynb"])
    assert (tmpdir / "scripts" / "test.py").exists()

    # Delete and then recreate the ipynb notebook using --to notebook
    test_ipynb.remove()
    jupytext_cli(
        [
            "--to",
            "notebook",
            "--output",
            "test.ipynb",
            "scripts/test.py",
        ]
    )
    assert test_ipynb.exists()

    # Delete and then recreate the ipynb notebook using --sync
    test_ipynb.remove()
    jupytext_cli(
        [
            "--sync",
            "scripts/test.py",
        ]
    )
    assert test_ipynb.exists()


@pytest.mark.parametrize(
    "path, input_fmt, adjusted_fmt",
    [
        (
            "scripts/test.py",
            {"extension": ".py", "format_name": "percent", "prefix": "scripts//"},
            {"extension": ".py", "format_name": "percent", "prefix": "scripts//"},
        ),
        (
            "test.py",
            {"extension": ".py", "format_name": "percent", "prefix": "scripts//"},
            {
                "extension": ".py",
                "format_name": "percent",
            },
        ),
        (
            "test.py",
            {"extension": ".py", "format_name": "percent", "prefix": "prefix_"},
            {"extension": ".py", "format_name": "percent"},
        ),
    ],
)
def test_paired_paths_and_adjusted_fmt(path, input_fmt, adjusted_fmt):
    base_path, actual_adjusted_fmt = base_path_and_adjusted_fmt(path, input_fmt)
    assert actual_adjusted_fmt == adjusted_fmt


@pytest.mark.parametrize("os_sep", ["\\", "/"])
def test_base_path_os_sep(os_sep):
    fmt = "notebooks/tutorials///ipynb"
    root = ("" if os_sep == "/" else "C:") + os_sep
    path = root + os_sep.join(["notebooks", "tutorials", "subfolder", "notebook.ipynb"])
    with mock.patch("os.path.sep", os_sep):
        assert base_path(path, fmt) == root + os_sep.join(["//subfolder", "notebook"])
