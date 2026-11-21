import pytest
from jupyter_server.utils import ensure_async
from nbformat.v4.nbbase import new_notebook

import jupytext
from jupytext.compare import compare
from jupytext.formats import (
    JupytextFormatError,
    divine_format,
    get_format_implementation,
    guess_format,
    long_form_multiple_formats,
    read_format_from_metadata,
    rearrange_jupytext_metadata,
    short_form_multiple_formats,
    update_jupytext_formats_metadata,
    validate_one_format,
)


def test_guess_format_light(python_file):
    with open(python_file) as stream:
        assert guess_format(stream.read(), ext=".py")[0] == "light"


def test_guess_format_percent(percent_file):
    with open(percent_file) as stream:
        assert guess_format(stream.read(), ext=".py")[0] == "percent"


def test_guess_format_simple_percent(
    nb="""# %%
print("hello world!")
""",
):
    assert guess_format(nb, ext=".py")[0] == "percent"


def test_guess_format_simple_percent_with_magic(
    nb="""# %%
# %time
print("hello world!")
""",
):
    assert guess_format(nb, ext=".py")[0] == "percent"


def test_guess_format_simple_hydrogen_with_magic(
    nb="""# %%
%time
print("hello world!")
""",
):
    assert guess_format(nb, ext=".py")[0] == "hydrogen"


def test_guess_format_sphinx(sphinx_file):
    with open(sphinx_file) as stream:
        assert guess_format(stream.read(), ext=".py")[0] == "sphinx"


def test_guess_format_hydrogen():
    text = """# %%
cat hello.txt
"""
    assert guess_format(text, ext=".py")[0] == "hydrogen"


def test_divine_format():
    assert divine_format('{"cells":[]}') == "ipynb"
    assert (
        divine_format(
            """def f(x):
    x + 1"""
        )
        == "py:light"
    )
    assert (
        divine_format(
            """# %%
def f(x):
    x + 1

# %%
def g(x):
    x + 2
"""
        )
        == "py:percent"
    )
    assert (
        divine_format(
            """This is a markdown file
with one code block

```
1 + 1
```
"""
        )
        == "md"
    )
    assert (
        divine_format(
            """;; ---
;; jupyter:
;;   jupytext:
;;     text_representation:
;;       extension: .ss
;;       format_name: percent
;; ---"""
        )
        == "ss:percent"
    )


def test_get_format_implementation():
    assert get_format_implementation(".py").format_name == "light"
    assert get_format_implementation(".py", "percent").format_name == "percent"
    with pytest.raises(JupytextFormatError):
        get_format_implementation(".py", "wrong_format")


def test_script_with_magics_not_percent(
    script="""# %%time
1 + 2""",
):
    assert guess_format(script, ".py")[0] == "light"


def test_script_with_spyder_cell_is_percent(
    script="""#%%
1 + 2""",
):
    assert guess_format(script, ".py")[0] == "percent"


def test_script_with_percent_cell_and_magic_is_hydrogen(
    script="""#%%
%matplotlib inline
""",
):
    assert guess_format(script, ".py")[0] == "hydrogen"


def test_script_with_percent_cell_and_kernelspec(
    script="""# ---
# jupyter:
#   kernelspec:
#     display_name: Python3
#     language: python
#     name: python3
# ---

# %%
a = 1
""",
):
    assert guess_format(script, ".py")[0] == "percent"


def test_script_with_spyder_cell_with_name_is_percent(
    script="""#%% cell name
1 + 2""",
):
    assert guess_format(script, ".py")[0] == "percent"


def test_read_format_from_metadata(
    script="""---
jupyter:
  jupytext:
    formats: ipynb,pct.py:percent,lgt.py:light,spx.py:sphinx,md,Rmd
    text_representation:
      extension: .pct.py
      format_name: percent
      format_version: '1.1'
      jupytext_version: 0.8.0
---""",
):
    assert read_format_from_metadata(script, ".Rmd") is None


def test_update_jupytext_formats_metadata():
    nb = new_notebook(metadata={"jupytext": {"formats": "py"}})
    update_jupytext_formats_metadata(nb.metadata, "py:light")
    assert nb.metadata["jupytext"]["formats"] == "py:light"

    nb = new_notebook(metadata={"jupytext": {"formats": "ipynb,py"}})
    update_jupytext_formats_metadata(nb.metadata, "py:light")
    assert nb.metadata["jupytext"]["formats"] == "ipynb,py:light"


def test_decompress_formats():
    assert long_form_multiple_formats("ipynb") == [{"extension": ".ipynb"}]
    assert long_form_multiple_formats("ipynb,md") == [
        {"extension": ".ipynb"},
        {"extension": ".md"},
    ]
    assert long_form_multiple_formats("ipynb,py:light") == [
        {"extension": ".ipynb"},
        {"extension": ".py", "format_name": "light"},
    ]
    assert long_form_multiple_formats(["ipynb", ".py:light"]) == [
        {"extension": ".ipynb"},
        {"extension": ".py", "format_name": "light"},
    ]
    assert long_form_multiple_formats(".pct.py:percent") == [{"extension": ".py", "suffix": ".pct", "format_name": "percent"}]


def test_compress_formats():
    assert short_form_multiple_formats([{"extension": ".ipynb"}]) == "ipynb"
    assert short_form_multiple_formats("ipynb") == "ipynb"
    assert short_form_multiple_formats([{"extension": ".ipynb"}, {"extension": ".md"}]) == "ipynb,md"
    assert (
        short_form_multiple_formats([{"extension": ".ipynb"}, {"extension": ".py", "format_name": "light"}])
        == "ipynb,py:light"
    )
    assert (
        short_form_multiple_formats(
            [
                {"extension": ".ipynb"},
                {"extension": ".py", "format_name": "light"},
                {"extension": ".md", "comment_magics": True},
            ]
        )
        == "ipynb,py:light,md"
    )
    assert short_form_multiple_formats([{"extension": ".py", "suffix": ".pct", "format_name": "percent"}]) == ".pct.py:percent"


def test_rearrange_jupytext_metadata():
    metadata = {"nbrmd_formats": "ipynb,py"}
    rearrange_jupytext_metadata(metadata)
    compare(metadata, {"jupytext": {"formats": "ipynb,py"}})

    metadata = {"jupytext_formats": "ipynb,py"}
    rearrange_jupytext_metadata(metadata)
    compare(metadata, {"jupytext": {"formats": "ipynb,py"}})

    metadata = {"executable": "#!/bin/bash"}
    rearrange_jupytext_metadata(metadata)
    compare(metadata, {"jupytext": {"executable": "#!/bin/bash"}})


def test_rearrange_jupytext_metadata_metadata_filter():
    metadata = {
        "jupytext": {
            "metadata_filter": {
                "notebook": {"additional": ["one", "two"], "excluded": "all"},
                "cells": {"additional": "all", "excluded": ["three", "four"]},
            }
        }
    }
    rearrange_jupytext_metadata(metadata)
    compare(
        metadata,
        {
            "jupytext": {
                "notebook_metadata_filter": "one,two,-all",
                "cell_metadata_filter": "all,-three,-four",
            }
        },
    )


def test_rearrange_jupytext_metadata_add_dot_in_suffix():
    metadata = {
        "jupytext": {
            "text_representation": {"jupytext_version": "0.8.6"},
            "formats": "ipynb,pct.py,lgt.py",
        }
    }
    rearrange_jupytext_metadata(metadata)
    compare(
        metadata,
        {
            "jupytext": {
                "text_representation": {"jupytext_version": "0.8.6"},
                "formats": "ipynb,.pct.py,.lgt.py",
            }
        },
    )


def test_fix_139():
    text = """# ---
# jupyter:
#   jupytext:
#     metadata_filter:
#       cells:
#         additional:
#           - "lines_to_next_cell"
#         excluded:
#           - "all"
# ---

# + {"lines_to_next_cell": 2}
1 + 1
# -


1 + 1
"""

    nb = jupytext.reads(text, "py:light")
    text2 = jupytext.writes(nb, "py:light")
    assert "cell_metadata_filter: -all" in text2
    assert "lines_to_next_cell" not in text2


def test_validate_one_format():
    with pytest.raises(JupytextFormatError):
        validate_one_format("py:percent")

    with pytest.raises(JupytextFormatError):
        validate_one_format({"extension": "py", "format_name": "invalid"})

    with pytest.raises(JupytextFormatError):
        validate_one_format({})

    with pytest.raises(JupytextFormatError):
        validate_one_format({"extension": ".py", "unknown_option": True})

    with pytest.raises(JupytextFormatError):
        validate_one_format({"extension": ".py", "comment_magics": "TRUE"})


def test_set_auto_ext():
    with pytest.raises(ValueError):
        long_form_multiple_formats("ipynb,auto:percent", {})


@pytest.mark.requires_pandoc
def test_pandoc_format_is_preserved():
    formats_org = "ipynb,md,.pandoc.md:pandoc,py:light"
    long = long_form_multiple_formats(formats_org)
    formats_new = short_form_multiple_formats(long)

    compare(formats_new, formats_org)


@pytest.mark.requires_myst
def test_write_as_myst(tmpdir):
    """Inspired by https://github.com/mwouts/jupytext/issues/462"""
    nb = new_notebook()
    tmp_md = str(tmpdir.join("notebook.md"))

    jupytext.write(nb, tmp_md, fmt="myst")

    with open(tmp_md) as fp:
        md = fp.read()

    assert "myst" in md


def test_write_raises_when_fmt_does_not_exists(tmpdir):
    """Inspired by https://github.com/mwouts/jupytext/issues/462"""
    nb = new_notebook()
    tmp_md = str(tmpdir.join("notebook.md"))

    with pytest.raises(JupytextFormatError):
        jupytext.write(nb, tmp_md, fmt="unknown_format")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config_file,config_contents",
    [
        (
            "jupytext.toml",
            """# Always pair ipynb notebooks to md files
formats = "ipynb,md"
""",
        ),
        (
            "jupytext.toml",
            """# Always pair ipynb notebooks to py:percent files
formats = "ipynb,py:percent"
""",
        ),
        (
            "pyproject.toml",
            """[tool.jupytext]
formats = "ipynb,py:percent"
""",
        ),
        (
            "jupytext.toml",
            """# Pair notebooks in subfolders of 'notebooks' to scripts in subfolders of 'scripts'
formats = "notebooks///ipynb,scripts///py:percent"
""",
        ),
        (
            "jupytext.toml",
            """[formats]
"notebooks/" = "ipynb"
"scripts/" = "py:percent"
""",
        ),
    ],
)
async def test_configuration_examples_from_documentation(config_file, config_contents, python_notebook, tmp_path, cm):
    """Here we make sure that the config examples from
    https://jupytext.org/using/config/#global-pairing
    just work
    """
    (tmp_path / config_file).write_text(config_contents)
    cm.root_dir = str(tmp_path)

    # Save the notebook
    (tmp_path / "notebooks").mkdir()
    await ensure_async(cm.save(dict(type="notebook", content=python_notebook), "notebooks/nb.ipynb"))

    # Make sure that ipynb and text version are created
    assert (tmp_path / "notebooks" / "nb.ipynb").is_file()
    assert (
        (tmp_path / "notebooks" / "nb.py").is_file()
        or (tmp_path / "notebooks" / "nb.md").is_file()
        or (tmp_path / "scripts" / "nb.py").is_file()
    )
