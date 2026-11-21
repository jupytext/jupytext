import pytest
from nbformat.v4.nbbase import new_notebook, new_raw_cell

from jupytext import reads, writes
from jupytext.compare import compare, compare_notebooks
from jupytext.config import load_jupytext_configuration_file
from jupytext.header import _JUPYTER_METADATA_NAMESPACE
from jupytext.myst import dump_yaml_blocks


@pytest.mark.requires_myst
def test_myst_header_is_stable_1247_using_inline_filter(
    md="""---
jupytext:
  formats: md:myst
  notebook_metadata_filter: -jupytext.text_representation.jupytext_version,settings,mystnb
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
mystnb:
  execution_mode: 'off'
settings:
  output_matplotlib_strings: remove
---
""",
):
    nb = reads(md, fmt="md")
    md2 = writes(nb, fmt="md")

    compare(md2, md)


@pytest.mark.requires_myst
def test_myst_header_is_stable_1247_using_config(
    jupytext_toml_content="""notebook_metadata_filter = "-jupytext.text_representation.jupytext_version,settings,mystnb"
""",
    md="""---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
mystnb:
  execution_mode: 'off'
settings:
  output_matplotlib_strings: remove
---
""",
):
    config = load_jupytext_configuration_file("jupytext.toml", jupytext_toml_content)

    nb = reads(md, fmt="md", config=config)
    md2 = writes(nb, fmt="md", config=config)

    compare(md2, md)


@pytest.mark.requires_myst
def test_myst_frontmatter_metadata_combo(no_jupytext_version_number):
    # ---
    # foo: bar
    # jupyter: <- subkeys become notebook metadata
    #   lorem: ipsum
    # ---
    frontmatter = {"foo": "bar"}
    metadata = {"lorem": "ipsum"}
    md = dump_yaml_blocks(
        {**frontmatter, _JUPYTER_METADATA_NAMESPACE: metadata},
        compact=False,
    )
    config = load_jupytext_configuration_file(
        "jupytext.toml",
        "\n".join(
            (
                'notebook_metadata_filter = "all,-jupytext"',
                'root_level_metadata_filter = "-all"',
            )
        ),
    )
    actual_nb = reads(md, fmt="md:myst", config=config)
    expected_nb = new_notebook(
        metadata=metadata,
        cells=[
            new_raw_cell(dump_yaml_blocks(frontmatter, compact=False).strip()),
        ],
    )
    compare_notebooks(actual_nb, expected_nb)
    # {
    #   "cells": [
    #     {
    #        "cell_type": "raw",
    #        "source": "---\nfoo: bar\n---",  <- merge with metadata in frontmatter
    #        ...
    #     }
    #   ],
    #   "metadata": {"foo": "baz"},
    #   ...
    # }
    actual_md = writes(actual_nb, fmt="md:myst", config=config)
    expected_md = md
    compare(actual_md, expected_md)


@pytest.mark.requires_myst
def test_myst_metadata_support_unicode_characters(
    md="""---
jupytext:
  formats: md:myst
  notebook_metadata_filter: -jupytext.text_representation.jupytext_version,settings,mystnb
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: àèìòùÀÈÌÒÙáéíóúýÁÉÍÓÚÝâêîôûÂÊÎÔÛãñõÃÑÕäëïöüÿÄËÏÖÜŸőűŐŰçÇßØøÅåÆæœ
mystnb:
  execution_mode: 'off'
settings:
  output_matplotlib_strings: remove
---
""",
):
    nb = reads(md, fmt="md")
    md2 = writes(nb, fmt="md")

    compare(md2, md)
