import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_code_cell, new_notebook

import jupytext
from jupytext.compare import compare, compare_notebooks, notebook_model
from jupytext.magics import (
    _PYTHON_MAGIC_ASSIGN,
    comment_magic,
    is_magic,
    uncomment_magic,
    unesc,
)


def test_unesc():
    assert unesc("# comment", "python") == "comment"
    assert unesc("#comment", "python") == "comment"
    assert unesc("comment", "python") == "comment"


@pytest.mark.parametrize(
    "line",
    [
        "%matplotlib inline",
        "#%matplotlib inline",
        "##%matplotlib inline",
        "%%HTML",
        "%autoreload",
        "%store",
    ],
)
def test_escape(line):
    assert comment_magic([line]) == ["# " + line]
    assert uncomment_magic(comment_magic([line])) == [line]


@pytest.mark.parametrize("line", ["@pytest.fixture"])
def test_escape_magic_only(line):
    assert comment_magic([line]) == [line]


@pytest.mark.parametrize("line", ["%matplotlib inline #noescape"])
def test_force_noescape(line):
    assert comment_magic([line]) == [line]


@pytest.mark.parametrize("line", ["%matplotlib inline #noescape"])
def test_force_noescape_with_gbl_esc_flag(line):
    assert comment_magic([line], global_escape_flag=True) == [line]


@pytest.mark.parametrize("line", ["%matplotlib inline #escape"])
def test_force_escape_with_gbl_esc_flag(line):
    assert comment_magic([line], global_escape_flag=False) == ["# " + line]


@pytest.mark.parametrize(
    "fmt,commented",
    zip(
        [
            "md",
            "Rmd",
            "py:light",
            "py:percent",
            "py:sphinx",
            "R",
            "ss:light",
            "ss:percent",
        ],
        [False, True, True, True, True, True, True, True],
    ),
)
def test_magics_commented_default(fmt, commented):
    nb = new_notebook(cells=[new_code_cell("%pylab inline")])

    text = jupytext.writes(nb, fmt)
    assert ("%pylab inline" in text.splitlines()) != commented
    nb2 = jupytext.reads(text, fmt)

    if "sphinx" in fmt:
        nb2.cells = nb2.cells[1:]

    compare_notebooks(nb2, nb)


@pytest.mark.parametrize("fmt", ["jenner:light", "jenner:percent", "Rmd"])
def test_jenner_macro_statements_preserved(fmt):
    source = """/* %put This statement is commented out; */
%let name = Jupytext;
%macro greet;
    %put &name;
%mend;
%greet;"""
    nb = new_notebook(
        cells=[new_code_cell(source)],
        metadata={"jupytext": {"main_language": "jenner"}},
    )

    text = jupytext.writes(nb, fmt)
    assert source in text
    compare_notebooks(jupytext.reads(text, fmt), nb)


def test_read_jenner_commented_macro_preserved():
    source = "/* %put This statement is commented out; */\n%put Hello;"
    nb = jupytext.reads("/* %% */\n" + source + "\n", "jenner:percent")

    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"
    assert nb.cells[0].source == source


@pytest.mark.parametrize(
    "fmt",
    ["md", "Rmd", "py:light", "py:percent", "py:sphinx", "R", "ss:light", "ss:percent"],
)
def test_magics_are_commented(fmt):
    nb = new_notebook(
        cells=[new_code_cell("%pylab inline")],
        metadata={
            "jupytext": {
                "comment_magics": True,
                "main_language": ("R" if fmt == "R" else "scheme" if fmt.startswith("ss") else "python"),
            }
        },
    )

    text = jupytext.writes(nb, fmt)
    assert "%pylab inline" not in text.splitlines()
    nb2 = jupytext.reads(text, fmt)

    if "sphinx" in fmt:
        nb2.cells = nb2.cells[1:]

    compare_notebooks(nb2, nb)


@pytest.mark.parametrize(
    "fmt",
    ["md", "Rmd", "py:light", "py:percent", "py:sphinx", "R", "ss:light", "ss:percent"],
)
def test_magics_are_not_commented(fmt):
    nb = new_notebook(
        cells=[new_code_cell("%pylab inline")],
        metadata={
            "jupytext": {
                "comment_magics": False,
                "main_language": ("R" if fmt == "R" else "scheme" if fmt.startswith("ss") else "python"),
            }
        },
    )

    text = jupytext.writes(nb, fmt)
    assert "%pylab inline" in text.splitlines()
    nb2 = jupytext.reads(text, fmt)

    if "sphinx" in fmt:
        nb2.cells = nb2.cells[1:]

    compare_notebooks(nb2, nb)


@pytest.mark.asyncio
async def test_force_comment_using_contents_manager(tmpdir, cm):
    tmp_py = "notebook.py"

    cm.preferred_jupytext_formats_save = "py:percent"
    cm.root_dir = str(tmpdir)

    nb = new_notebook(cells=[new_code_cell("%pylab inline")])

    await ensure_async(cm.save(model=notebook_model(nb), path=tmp_py))
    with open(str(tmpdir.join(tmp_py))) as stream:
        assert "# %pylab inline" in stream.read().splitlines()

    cm.comment_magics = False
    await ensure_async(cm.save(model=notebook_model(nb), path=tmp_py))
    with open(str(tmpdir.join(tmp_py))) as stream:
        assert "%pylab inline" in stream.read().splitlines()


@pytest.mark.parametrize(
    "magic_cmd",
    [
        "ls",
        "!ls",
        "ls -al",
        "!whoami",
        "# ls",
        "# mv a b",
        "! mkdir tmp",
        "!./script",
        "! ./script",
        "!./script args",
        "!./script.sh args",
        "! ./script.sh args",
        "!~/script.sh args",
        "! ~/script.sh args",
        "!../script.sh $ENV $USER",
        "! ../script.sh $ENV $USER",
        "!$HOME/script.sh $ENV $USER",
        "!/bin/sh $ENV $USER",
        "! /bin/sh $ENV $USER",
        r"! \bin\sh $ENV $USER",
        r"!\bin\sh $ENV $USER",
        "cat",
        "cat ",
        "cat hello.txt",
        "cat --option=value hello.txt",
        "!{x}",
    ],
)
def test_comment_bash_commands_in_python(magic_cmd):
    assert comment_magic([magic_cmd]) == ["# " + magic_cmd]
    assert uncomment_magic(["# " + magic_cmd]) == [magic_cmd]


@pytest.mark.parametrize(
    "not_magic_cmd",
    ["copy(a)", "copy.deepcopy", "cat = 3", "cat=5", "cat, other = 5,3", "cat(5)"],
)
def test_do_not_comment_python_cmds(not_magic_cmd):
    assert comment_magic([not_magic_cmd]) == [not_magic_cmd]
    assert uncomment_magic([not_magic_cmd]) == [not_magic_cmd]


@pytest.mark.parametrize("magic_cmd", ["ls", "!ls", "ls -al", "!whoami", "# ls", "# mv a b"])
def test_do_not_comment_bash_commands_in_R(magic_cmd):
    assert comment_magic([magic_cmd], language="R") == [magic_cmd]
    assert uncomment_magic([magic_cmd], language="R") == [magic_cmd]


def test_markdown_image_is_not_magic():
    assert is_magic("# !cmd", "python")
    assert not is_magic("# ![Image name](image.png", "python")


def test_question_is_not_magic():
    assert is_magic("float?", "python", explicitly_code=True)
    assert is_magic("# float?", "python", explicitly_code=True)
    assert not is_magic("# question: float?", "python", explicitly_code=True)


def test_whitespace_line_is_not_magic_and_is_fast():
    # A whitespace-only line is not a magic, and detecting that must not take
    # quadratic time (see the _PYTHON_HELP_OR_BASH_CMD regex)
    import time

    line = " \t" * 100_000
    start = time.perf_counter()
    assert not is_magic(line, "python")
    assert time.perf_counter() - start < 2


def test_multiline_python_magic(no_jupytext_version_number):
    nb = new_notebook(
        cells=[
            new_code_cell(
                """%load_ext watermark
%watermark -u -n -t -z \\
    -p jupytext -v

def g(x):
    return x+1"""
            )
        ]
    )

    text = jupytext.writes(nb, "py:light")
    compare(
        text,
        """# +
# %load_ext watermark
# %watermark -u -n -t -z \\
#     -p jupytext -v

def g(x):
    return x+1
""",
    )
    compare_notebooks(jupytext.reads(text, "py"), nb)


def test_configure_magic(no_jupytext_version_number):
    nb = new_notebook(
        cells=[
            new_code_cell(
                """%%configure -f \\
{"executorMemory": "3072M", "executorCores": 4, "numExecutors":10}"""
            )
        ]
    )

    text = jupytext.writes(nb, "py:light")
    compare(
        text,
        """# %%configure -f \\
# {"executorMemory": "3072M", "executorCores": 4, "numExecutors":10}
""",
    )
    compare_notebooks(jupytext.reads(text, "py"), nb)


def test_indented_magic():
    assert is_magic("    !rm file", "python")
    assert is_magic("    # !rm file", "python")
    assert is_magic("    %cd", "python")
    assert comment_magic(["    !rm file"]) == ["    # !rm file"]
    assert uncomment_magic(["    # !rm file"]) == ["    !rm file"]
    assert comment_magic(["    %cd"]) == ["    # %cd"]
    assert uncomment_magic(["    # %cd"]) == ["    %cd"]


def test_magic_assign_781():
    assert _PYTHON_MAGIC_ASSIGN.match("name = %magic")
    assert _PYTHON_MAGIC_ASSIGN.match("# name = %magic")
    assert not _PYTHON_MAGIC_ASSIGN.match("# not a name = %magic")
    assert not _PYTHON_MAGIC_ASSIGN.match("# 0name = %magic")
    assert is_magic("result = %sql SELECT * FROM quickdemo WHERE value > 25", "python")


def test_magic_assign_816():
    assert _PYTHON_MAGIC_ASSIGN.match("flake8_version = !flake8 --version")
    assert _PYTHON_MAGIC_ASSIGN.match("# flake8_version = !flake8 --version")
    assert _PYTHON_MAGIC_ASSIGN.match("name = %time 2+2")
    assert _PYTHON_MAGIC_ASSIGN.match("# name = %time 2+2")
