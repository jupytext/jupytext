import nbformat
from nbformat.v4.nbbase import new_code_cell, new_notebook

import jupytext
from jupytext.cli import jupytext as jupytext_cli
from jupytext.compare import compare_notebooks


def test_custom_language_magics_md_to_ipynb():
    """Code blocks in custom language magics should be converted to code cells"""

    md = """\
```python
print("hello")
```

```custom
hello
```
"""
    nb = jupytext.reads(md, fmt={"extension": ".md", "custom_language_magics": "custom"})
    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "code"
    assert nb.cells[0].source == 'print("hello")'
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "%%custom\nhello"


def test_custom_language_magics_ipynb_to_md():
    """Code cells with custom language magics are converted to code blocks in those languages"""

    nb = new_notebook(
        cells=[
            new_code_cell('print("hello")'),
            new_code_cell("%%custom\nhello"),
        ]
    )

    md = jupytext.writes(nb, fmt={"extension": ".md", "custom_language_magics": "custom"})
    assert "custom_language_magics:" in md
    assert "```custom\n" in md


def test_custom_language_magics_roundtrip():
    """Round-trip: md with custom language magic -> ipynb -> md should preserve the code cell"""

    nb = new_notebook(
        cells=[
            new_code_cell('print("hello")'),
            new_code_cell("%%custom\nhello"),
        ]
    )

    # ipynb -> md
    md = jupytext.writes(nb, fmt={"extension": ".md", "custom_language_magics": "custom"})
    assert "```custom\n" in md

    # md -> ipynb
    nb2 = jupytext.reads(md, fmt={"extension": ".md", "custom_language_magics": "custom"})
    assert len(nb2.cells) == 2
    assert nb2.cells[1].cell_type == "code"
    assert nb2.cells[1].source == "%%custom\nhello"

    compare_notebooks(nb2, nb)


def test_custom_language_magics_config_file(tmpdir):
    """custom_language_magics from jupytext.toml should allow md -> ipynb conversion"""

    cfg_file = tmpdir.join("jupytext.toml")
    cfg_file.write('custom_language_magics = "custom"')

    md_file = tmpdir.join("notebook.md")
    nb_file = tmpdir.join("notebook.ipynb")

    md_file.write(
        """\
```python
print("hello")
```

```custom
hello
```
"""
    )

    jupytext_cli([str(md_file), "--to", "notebook"])
    nb = nbformat.read(str(nb_file), as_version=4)

    assert len(nb.cells) == 2
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "%%custom\nhello"


def test_custom_language_magics_not_markdown_cell():
    """Without custom_language_magics, custom code blocks should remain as markdown cells"""

    md = """\
```custom
hello
```
"""
    nb = jupytext.reads(md, fmt="md")
    # Without custom_language_magics, this should be a markdown cell
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "markdown"
