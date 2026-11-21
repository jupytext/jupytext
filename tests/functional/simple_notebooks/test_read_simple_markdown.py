from nbformat.v4.nbbase import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_raw_cell,
)

import jupytext
from jupytext.combine import combine_inputs_with_outputs
from jupytext.compare import compare, compare_cells, compare_notebooks


def test_read_mostly_py_markdown_file(
    markdown="""---
title: Simple file
---

```python
import numpy as np
x = np.arange(0, 2*math.pi, eps)
```

```python
x = np.arange(0,1,eps)
y = np.abs(x)-.5
```

This is
a Markdown cell

```
# followed by a code cell with no language info
```

```
# another code cell


# with two blank lines
```

And the same markdown cell continues

<!-- #raw -->
this is a raw cell
<!-- #endraw -->

```R
ls()
```

```R
cat(stringi::stri_rand_lipsum(3), sep='\n\n')
```
""",
):
    nb = jupytext.reads(markdown, "md")
    assert nb.metadata["jupytext"]["main_language"] == "python"
    compare_cells(
        nb.cells,
        [
            new_raw_cell("---\ntitle: Simple file\n---"),
            new_code_cell("import numpy as np\nx = np.arange(0, 2*math.pi, eps)"),
            new_code_cell("x = np.arange(0,1,eps)\ny = np.abs(x)-.5"),
            new_markdown_cell(
                """This is
a Markdown cell

```
# followed by a code cell with no language info
```

```
# another code cell


# with two blank lines
```

And the same markdown cell continues"""
            ),
            new_raw_cell("this is a raw cell"),
            new_code_cell("%%R\nls()"),
            new_code_cell("%%R\ncat(stringi::stri_rand_lipsum(3), sep='\n\n')"),
        ],
        compare_ids=False,
    )

    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_read_md_and_markdown_regions(
    markdown="""Some text

<!-- #md -->
A


long
cell
<!-- #endmd -->

<!-- #markdown -->
Another


long
cell
<!-- #endmarkdown -->
""",
):
    nb = jupytext.reads(markdown, "md")
    assert nb.metadata["jupytext"]["main_language"] == "python"
    compare_cells(
        nb.cells,
        [
            new_markdown_cell("Some text"),
            new_markdown_cell(
                """A


long
cell""",
                metadata={"region_name": "md"},
            ),
            new_markdown_cell(
                """Another


long
cell""",
                metadata={"region_name": "markdown"},
            ),
        ],
        compare_ids=False,
    )

    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_read_mostly_R_markdown_file(
    markdown="""```R
ls()
```

```R
cat(stringi::stri_rand_lipsum(3), sep='\n\n')
```
""",
):
    nb = jupytext.reads(markdown, "md")
    assert nb.metadata["jupytext"]["main_language"] == "R"
    compare_cells(
        nb.cells,
        [
            new_code_cell("ls()"),
            new_code_cell("cat(stringi::stri_rand_lipsum(3), sep='\n\n')"),
        ],
        compare_ids=False,
    )

    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_read_markdown_file_no_language(
    markdown="""```
ls
```

```
echo 'Hello World'
```
""",
):
    nb = jupytext.reads(markdown, "md")
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_read_julia_notebook(
    markdown="""```julia
1 + 1
```
""",
):
    nb = jupytext.reads(markdown, "md")
    assert nb.metadata["jupytext"]["main_language"] == "julia"
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_split_on_header(
    markdown="""A paragraph

# H1 Header

## H2 Header

Another paragraph
""",
):
    fmt = {"extension": ".md", "split_at_heading": True}
    nb = jupytext.reads(markdown, fmt)
    assert nb.cells[0].source == "A paragraph"
    assert nb.cells[1].source == "# H1 Header"
    assert nb.cells[2].source == "## H2 Header\n\nAnother paragraph"
    assert len(nb.cells) == 3
    markdown2 = jupytext.writes(nb, fmt)
    compare(markdown2, markdown)


def test_split_on_header_after_two_blank_lines(
    markdown="""A paragraph


# H1 Header
""",
):
    fmt = {"extension": ".Rmd", "split_at_heading": True}
    nb = jupytext.reads(markdown, fmt)
    markdown2 = jupytext.writes(nb, fmt)
    compare(markdown2, markdown)


def test_split_at_heading_in_metadata(
    markdown="""---
jupyter:
  jupytext:
    split_at_heading: true
---

A paragraph

# H1 Header
""",
    nb_expected=new_notebook(cells=[new_markdown_cell("A paragraph"), new_markdown_cell("# H1 Header")]),
):
    nb = jupytext.reads(markdown, ".md")
    compare_notebooks(nb, nb_expected)


def test_code_cell_with_metadata(
    markdown="""```python tags=["parameters"]
a = 1
b = 2
```
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [new_code_cell(source="a = 1\nb = 2", metadata={"tags": ["parameters"]})],
        compare_ids=False,
    )
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_raw_cell_with_metadata_json(
    markdown="""<!-- #raw {"key": "value"} -->
raw content
<!-- #endraw -->
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [new_raw_cell(source="raw content", metadata={"key": "value"})],
        compare_ids=False,
    )
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_raw_cell_with_metadata(
    markdown="""<!-- #raw key="value" -->
raw content
<!-- #endraw -->
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [new_raw_cell(source="raw content", metadata={"key": "value"})],
        compare_ids=False,
    )
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_read_raw_cell_markdown_version_1_1(
    markdown="""---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.1.0
---

```key="value"
raw content
```
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [new_raw_cell(source="raw content", metadata={"key": "value"})],
        compare_ids=False,
    )
    md2 = jupytext.writes(nb, "md")
    assert "format_version: '1.1'" not in md2


def test_read_raw_cell_markdown_version_1_1_with_mimetype(
    header="""---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.1.0-rc0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---
""",
    markdown_11="""```raw_mimetype="text/restructuredtext"
.. meta::
   :description: Topic: Integrated Development Environments, Difficulty: Easy, Category: Tools
   :keywords: python, introduction, IDE, PyCharm, VSCode, Jupyter, recommendation, tools
```
""",
    markdown_12="""<!-- #raw raw_mimetype="text/restructuredtext" -->
.. meta::
   :description: Topic: Integrated Development Environments, Difficulty: Easy, Category: Tools
   :keywords: python, introduction, IDE, PyCharm, VSCode, Jupyter, recommendation, tools
<!-- #endraw -->
""",
):
    nb = jupytext.reads(header + "\n" + markdown_11, "md")
    compare_cells(
        nb.cells,
        [
            new_raw_cell(
                source=""".. meta::
   :description: Topic: Integrated Development Environments, Difficulty: Easy, Category: Tools
   :keywords: python, introduction, IDE, PyCharm, VSCode, Jupyter, recommendation, tools""",
                metadata={"raw_mimetype": "text/restructuredtext"},
            )
        ],
        compare_ids=False,
    )
    md2 = jupytext.writes(nb, "md")
    assert "format_version: '1.1'" not in md2
    nb.metadata["jupytext"]["notebook_metadata_filter"] = "-all"
    md2 = jupytext.writes(nb, "md")
    compare(md2, markdown_12)


def test_markdown_cell_with_metadata_json(
    markdown="""<!-- #region {"key": "value"} -->
A long


markdown cell
<!-- #endregion -->
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [new_markdown_cell(source="A long\n\n\nmarkdown cell", metadata={"key": "value"})],
        compare_ids=False,
    )
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_markdown_cell_with_metadata(
    markdown="""<!-- #region key="value" -->
A long


markdown cell
<!-- #endregion -->
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [new_markdown_cell(source="A long\n\n\nmarkdown cell", metadata={"key": "value"})],
        compare_ids=False,
    )
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_two_markdown_cells(
    markdown="""# A header

<!-- #region -->
A long


markdown cell
<!-- #endregion -->
""",
):
    nb = jupytext.reads(markdown, "md")
    compare_cells(
        nb.cells,
        [
            new_markdown_cell(source="# A header"),
            new_markdown_cell(source="A long\n\n\nmarkdown cell"),
        ],
        compare_ids=False,
    )
    markdown2 = jupytext.writes(nb, "md")
    compare(markdown2, markdown)


def test_combine_md_version_one():
    markdown = """---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.0'
      jupytext_version: 1.0.0
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

A short markdown cell

```
a raw cell
```

```python
1 + 1
```
"""
    # notebook read from markdown file in version 1.0
    nb_source = jupytext.reads(markdown, "md")

    # actual notebook has metadata
    nb_meta = jupytext.reads(markdown, "md")
    for cell in nb_meta.cells:
        cell.metadata = {"key": "value"}

    nb_source = combine_inputs_with_outputs(nb_source, nb_meta)
    for cell in nb_source.cells:
        assert cell.metadata == {"key": "value"}, cell.source


def test_jupyter_cell_is_not_split():
    text = """Here we have a markdown
file with a jupyter code cell

```python
1 + 1


2 + 2
```

the code cell should become a Jupyter cell.
"""
    nb = jupytext.reads(text, "md")
    assert nb.cells[0].cell_type == "markdown"
    compare(
        nb.cells[0].source,
        """Here we have a markdown
file with a jupyter code cell""",
    )

    assert nb.cells[1].cell_type == "code"
    compare(
        nb.cells[1].source,
        """1 + 1


2 + 2""",
    )

    assert nb.cells[2].cell_type == "markdown"
    compare(nb.cells[2].source, "the code cell should become a Jupyter cell.")
    assert len(nb.cells) == 3


def test_indented_code_is_not_split():
    text = """Here we have a markdown
file with an indented code cell

    1 + 1


    2 + 2

the code cell should not become a Jupyter cell,
nor be split into two pieces."""
    nb = jupytext.reads(text, "md")
    compare(nb.cells[0].source, text)
    assert nb.cells[0].cell_type == "markdown"
    assert len(nb.cells) == 1


def test_non_jupyter_code_is_not_split():
    text = """Here we have a markdown
file with a non-jupyter code cell

```{.python}
1 + 1


2 + 2
```

the code cell should not become a Jupyter cell,
nor be split into two pieces."""
    nb = jupytext.reads(text, "md")
    compare(nb.cells[0].source, text)
    assert nb.cells[0].cell_type == "markdown"
    assert len(nb.cells) == 1


def test_read_markdown_idl(
    no_jupytext_version_number,
    text="""---
jupyter:
  kernelspec:
    display_name: IDL [conda env:gdl] *
    language: IDL
    name: conda-env-gdl-idl
---

# A sample IDL Markdown notebook

```idl
a = 1
```
""",
):
    nb = jupytext.reads(text, "md")
    assert len(nb.cells) == 2
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "a = 1"

    text2 = jupytext.writes(nb, "md")
    compare(text2, text)


def test_read_markdown_IDL(
    no_jupytext_version_number,
    text="""---
jupyter:
  kernelspec:
    display_name: IDL [conda env:gdl] *
    language: IDL
    name: conda-env-gdl-idl
---

# A sample IDL Markdown notebook

```IDL
a = 1
```
""",
):
    nb = jupytext.reads(text, "md")
    assert len(nb.cells) == 2
    assert nb.cells[1].cell_type == "code"
    assert nb.cells[1].source == "a = 1"

    text2 = jupytext.writes(nb, "md")
    compare(text2, text)


def test_inactive_cell(
    text="""```python active="md"
# This becomes a raw cell in Jupyter
```
""",
    expected=new_notebook(cells=[new_raw_cell("# This becomes a raw cell in Jupyter", metadata={"active": "md"})]),
):
    nb = jupytext.reads(text, "md")
    compare_notebooks(nb, expected)
    text2 = jupytext.writes(nb, "md")
    compare(text2, text)


def test_inactive_cell_using_tag(
    text="""```python tags=["active-md"]
# This becomes a raw cell in Jupyter
```
""",
    expected=new_notebook(cells=[new_raw_cell("# This becomes a raw cell in Jupyter", metadata={"tags": ["active-md"]})]),
):
    nb = jupytext.reads(text, "md")
    compare_notebooks(nb, expected)
    text2 = jupytext.writes(nb, "md")
    compare(text2, text)


def test_inactive_cell_using_noeval(
    text="""This is text

```python .noeval
# This is python code.
# It should not become a code cell
```
""",
):
    expected = new_notebook(cells=[new_markdown_cell(text[:-1])])
    nb = jupytext.reads(text, "md")
    compare_notebooks(nb, expected)
    text2 = jupytext.writes(nb, "md")
    compare(text2, text)


def test_noeval_followed_by_code_works(
    text="""```python .noeval
# Not a code cell in Jupyter
```

```python
1 + 1
```
""",
    expected=new_notebook(
        cells=[
            new_markdown_cell(
                """```python .noeval
# Not a code cell in Jupyter
```"""
            ),
            new_code_cell("1 + 1"),
        ]
    ),
):
    nb = jupytext.reads(text, "md")
    compare_notebooks(nb, expected)
    text2 = jupytext.writes(nb, "md")
    compare(text2, text)


def test_markdown_cell_with_code_works(
    nb=new_notebook(
        cells=[
            new_markdown_cell(
                """```python
1 + 1
```"""
            )
        ]
    ),
):
    text = jupytext.writes(nb, "md")
    nb2 = jupytext.reads(text, "md")
    compare_notebooks(nb2, nb)


def test_markdown_cell_with_noeval_code_works(
    nb=new_notebook(
        cells=[
            new_markdown_cell(
                """```python .noeval
1 + 1
```"""
            )
        ]
    ),
):
    text = jupytext.writes(nb, "md")
    nb2 = jupytext.reads(text, "md")
    compare_notebooks(nb2, nb)


def test_two_markdown_cell_with_code_works(
    nb=new_notebook(
        cells=[
            new_markdown_cell(
                """```python
1 + 1
```"""
            ),
            new_markdown_cell(
                """```python
2 + 2
```"""
            ),
        ]
    ),
):
    text = jupytext.writes(nb, "md")
    nb2 = jupytext.reads(text, "md")
    compare_notebooks(nb2, nb)


def test_two_markdown_cell_with_no_language_code_works(
    nb=new_notebook(
        cells=[
            new_markdown_cell(
                """```
1 + 1
```"""
            ),
            new_markdown_cell(
                """```
2 + 2
```"""
            ),
        ]
    ),
):
    text = jupytext.writes(nb, "md")
    nb2 = jupytext.reads(text, "md")
    compare_notebooks(nb2, nb)


def test_markdown_cell_with_code_inside_multiline_string_419(
    text='''```python
readme = """
above

```python
x = 2
```

below
"""
```
''',
):
    """A code cell containing triple backticks is converted to a code cell encapsulated with four backticks"""
    nb = jupytext.reads(text, "md")
    compare(jupytext.writes(nb, "md"), "`" + text[:-1] + "`\n")
    assert len(nb.cells) == 1


def test_notebook_with_python3_magic(
    no_jupytext_version_number,
    nb=new_notebook(
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        cells=[
            new_code_cell("%%python2\na = 1\nprint a"),
            new_code_cell("%%python3\nb = 2\nprint(b)"),
        ],
    ),
    text="""---
jupyter:
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python2
a = 1
print a
```

```python3
b = 2
print(b)
```
""",
):
    md = jupytext.writes(nb, "md")
    compare(md, text)

    nb2 = jupytext.reads(md, "md")
    compare_notebooks(nb2, nb)


def test_update_metadata_filter(
    no_jupytext_version_number,
    org="""---
jupyter:
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  extra:
    key: value
---
""",
    target="""---
jupyter:
  extra:
    key: value
  jupytext:
    notebook_metadata_filter: extra
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---
""",
):
    nb = jupytext.reads(org, "md")
    text = jupytext.writes(nb, "md")
    compare(text, target)


def test_update_metadata_filter_2(
    no_jupytext_version_number,
    org="""---
jupyter:
  jupytext:
    notebook_metadata_filter: -extra
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  extra:
    key: value
---
""",
    target="""---
jupyter:
  jupytext:
    notebook_metadata_filter: -extra
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---
""",
):
    nb = jupytext.reads(org, "md")
    text = jupytext.writes(nb, "md")
    compare(text, target)


def test_custom_metadata(
    no_jupytext_version_number,
    nb=new_notebook(
        metadata={
            "author": "John Doe",
            "title": "Some serious math",
            "jupytext": {"notebook_metadata_filter": "title,author"},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
        }
    ),
    md="""---
jupyter:
  author: John Doe
  jupytext:
    notebook_metadata_filter: title,author
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  title: Some serious math
---
""",
):
    """Here we test the addition of custom metadata, cf. https://github.com/mwouts/jupytext/issues/469"""
    md2 = jupytext.writes(nb, "md")
    compare(md2, md)
    nb2 = jupytext.reads(md, "md")
    compare_notebooks(nb2, nb)


def test_org_babel_metadata(
    no_jupytext_version_number,
    nb=new_notebook(
        metadata={
            "org_babel": {"header_args": {"jupyter-python": {"session": "verification-games-fluxes"}}},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
        }
    ),
    md="""---
jupyter:
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  org_babel:
    header_args:
      jupyter-python:
        session: verification-games-fluxes
---
""",
):
    md2 = jupytext.writes(nb, "md")
    compare(md2, md)
    nb2 = jupytext.reads(md, "md")
    compare_notebooks(nb2, nb)


def test_hide_notebook_metadata(
    no_jupytext_version_number,
    nb=new_notebook(
        metadata={
            "jupytext": {"hide_notebook_metadata": True},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
        }
    ),
    md="""<!--

---
jupyter:
  jupytext:
    hide_notebook_metadata: true
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

-->
""",
):
    """Test the hide_notebook_metadata option"""
    md2 = jupytext.writes(nb, "md")
    compare(md2, md)
    nb2 = jupytext.reads(md, "md")
    compare_notebooks(nb2, nb)


def test_notebook_with_empty_header_1070(
    md="""---

---

This file has empty frontmatter.
""",
):
    nb = jupytext.reads(md, fmt="md:markdown")
    md2 = jupytext.writes(nb, "md")
    compare(md2, md)
    nb2 = jupytext.reads(md, "md")
    compare_notebooks(nb2, nb)
