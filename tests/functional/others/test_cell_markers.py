import time

from nbformat.v4.nbbase import new_code_cell, new_notebook, new_raw_cell

from jupytext import reads, writes
from jupytext.cli import jupytext


def test_set_cell_markers_cli(tmpdir, cwd_tmpdir):
    tmpdir.join("test.py").write("# %% [markdown]\n# A Markdown cell\n")
    jupytext(["--format-options", 'cell_markers="""', "test.py"])
    py = tmpdir.join("test.py").read()
    assert py.endswith('# %% [markdown]\n"""\nA Markdown cell\n"""\n')


def test_add_cell_to_script_with_cell_markers(
    no_jupytext_version_number,
    py='''# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     cell_markers: '"""'
# ---
''',
):
    nb = reads(py, fmt="py:percent")
    nb.cells = [new_raw_cell("A raw cell")]
    py2 = writes(nb, fmt="py:percent")
    assert py2.endswith(
        '''# %% [raw]
"""
A raw cell
"""
'''
    )


def test_endofcell_option_is_matched_literally():
    """The endofcell option is read from the text file, so '# aa' below is not an end of cell marker"""
    py = '# + endofcell="a+"\n1 + 1\n\n# aa\n\n2 + 2\n'

    nb = reads(py, fmt="py:light")

    assert len(nb.cells) == 1


def test_endofcell_option_does_not_backtrack():
    py = '# + endofcell="(a+)+b"\n1 + 1\n\n# ' + "a" * 28 + "X\n"

    start = time.perf_counter()
    reads(py, fmt="py:light")
    assert time.perf_counter() - start < 2


def test_cell_markers_are_matched_literally(
    no_jupytext_version_number,
    py="""# ---
# jupyter:
#   jupytext:
#     cell_markers: a+,b+
#     text_representation:
#       extension: .py
#       format_name: light
# ---

# aa
1 + 1
""",
):
    nb = reads(py, fmt="py")

    assert len(nb.cells) == 1
    assert nb.cells[0].source == "# aa\n1 + 1"


def test_cell_markers_do_not_backtrack_when_writing():
    nb = new_notebook(
        cells=[new_code_cell("#" + "a" * 28 + "X\n\npass")],
        metadata={"jupytext": {"cell_markers": "(a+)+b,(a+)+b", "main_language": "python"}},
    )

    start = time.perf_counter()
    writes(nb, fmt="py:light")
    assert time.perf_counter() - start < 2


def test_cell_markers_with_block_comment_language():
    """The OCaml comment '(*' is not a regular expression either"""
    nb = new_notebook(
        cells=[new_code_cell("(* a comment *)\n\nlet x = 1")],
        metadata={"jupytext": {"cell_markers": "region,endregion", "main_language": "ocaml"}},
    )

    assert "let x = 1" in writes(nb, fmt="ml:light")
