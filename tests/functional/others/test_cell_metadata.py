import pytest
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell

import jupytext
from jupytext.cell_metadata import (
    _IGNORE_CELL_METADATA,
    RMarkdownOptionParsingError,
    is_valid_metadata_key,
    metadata_to_rmd_options,
    metadata_to_text,
    parse_key_equal_value,
    parse_rmd_options,
    rmd_options_to_metadata,
    text_to_metadata,
    try_eval_metadata,
)
from jupytext.combine import combine_inputs_with_outputs
from jupytext.compare import compare, compare_notebooks
from jupytext.metadata_filter import filter_metadata


def r_options_language_metadata():
    yield from [
        ("r", "R", {}),
        (
            'r plot_1, dpi=72, fig.path="fig_path/"',
            "R",
            {"name": "plot_1", "dpi": 72, "fig.path": "fig_path/"},
        ),
        (
            'r plot_1, bool=TRUE, fig.path="fig_path/"',
            "R",
            {"name": "plot_1", "bool": True, "fig.path": "fig_path/"},
        ),
        ("r echo=FALSE", "R", {"tags": ["remove_input"]}),
        ("r plot_1, echo=TRUE", "R", {"name": "plot_1", "echo": True}),
        (
            "python echo=if a==5 then TRUE else FALSE",
            "python",
            {"echo": "#R_CODE#if a==5 then TRUE else FALSE"},
        ),
        (
            'python noname, tags=c("a", "b", "c"), echo={sum(a+c(1,2))>1}',
            "python",
            {
                "name": "noname",
                "tags": ["a", "b", "c"],
                "echo": "#R_CODE#{sum(a+c(1,2))>1}",
            },
        ),
        ('python active="ipynb,py"', "python", {"active": "ipynb,py"}),
        (
            'python include=FALSE, active="Rmd"',
            "python",
            {"active": "Rmd", "tags": ["remove_cell"]},
        ),
        (
            'r chunk_name, include=FALSE, active="Rmd"',
            "R",
            {"name": "chunk_name", "active": "Rmd", "tags": ["remove_cell"]},
        ),
        ('python tags=c("parameters")', "python", {"tags": ["parameters"]}),
    ]


@pytest.mark.parametrize("options,language, metadata", r_options_language_metadata())
def test_parse_rmd_options(options, language, metadata):
    compare(rmd_options_to_metadata(options), (language, metadata))


@pytest.mark.parametrize("options,language, metadata", r_options_language_metadata())
def test_build_options(options, language, metadata):
    compare(metadata_to_rmd_options(*(language, metadata)), options)


@pytest.mark.parametrize("options,language, metadata", r_options_language_metadata())
def test_build_options_random_order(options, language, metadata):
    # Older python has no respect for order...
    # assert to_chunk_options(metadata) == options

    def split_and_strip(opt):
        {o.strip() for o in opt.split(",")}

    assert split_and_strip(metadata_to_rmd_options(*(language, metadata))) == split_and_strip(options)


@pytest.mark.parametrize("options", ["a={)", "name, name2", "a=}", "b=]", "c=["])
def test_parsing_error(options):
    with pytest.raises(RMarkdownOptionParsingError):
        parse_rmd_options(options)


def test_ignore_metadata():
    metadata = {"trusted": True, "tags": ["remove_input"]}
    metadata = filter_metadata(metadata, None, _IGNORE_CELL_METADATA)
    assert metadata_to_rmd_options("R", metadata) == "r echo=FALSE"


def test_filter_metadata():
    assert filter_metadata({"scrolled": True}, None, _IGNORE_CELL_METADATA) == {}


def test_try_eval_metadata():
    metadata = {"list": 'list("a",5)', "c": "c(1,2,3)"}
    try_eval_metadata(metadata, "list")
    try_eval_metadata(metadata, "c")
    assert metadata == {"list": ["a", 5], "c": [1, 2, 3]}


def test_language_no_metadata(text="python", value=("python", {})):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == text.strip()


def test_only_metadata(text='key="value"', value=("", {"key": "value"})):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == text


def test_only_metadata_2(text='key="value"', value=("", {"key": "value"})):
    compare(text_to_metadata(text, allow_title=True), value)
    assert metadata_to_text(*value) == text


def test_no_language(text=".class", value=("", {".class": None})):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == text


def test_language_metadata_no_space(text='python{"a":1}', value=("python", {"a": 1})):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == "python a=1"


def test_title_no_metadata(text="title", value=("title", {})):
    compare(text_to_metadata(text, allow_title=True), value)
    assert metadata_to_text(*value) == text.strip()


def test_simple_metadata(
    text='python string="value" number=1.0 array=["a", "b"]',
    value=("python", {"string": "value", "number": 1.0, "array": ["a", "b"]}),
):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == text


def test_simple_metadata_with_spaces(
    text='python string = "value" number = 1.0 array = ["a",  "b"]',
    value=("python", {"string": "value", "number": 1.0, "array": ["a", "b"]}),
):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == 'python string="value" number=1.0 array=["a", "b"]'


def test_title_and_relax_json(
    text="cell title string='value' number=1.0 array=['a', \"b\"]",
    value=("cell title", {"string": "value", "number": 1.0, "array": ["a", "b"]}),
):
    compare(text_to_metadata(text, allow_title=True), value)
    assert metadata_to_text(*value) == 'cell title string="value" number=1.0 array=["a", "b"]'


def test_title_and_json_dict(
    text='cell title {"string": "value", "number": 1.0, "array": ["a", "b"]}',
    value=("cell title", {"string": "value", "number": 1.0, "array": ["a", "b"]}),
):
    compare(text_to_metadata(text, allow_title=True), value)
    assert metadata_to_text(*value) == 'cell title string="value" number=1.0 array=["a", "b"]'


@pytest.mark.parametrize("allow_title", [True, False])
def test_attribute(allow_title):
    text = ".class"
    value = ("", {".class": None})
    compare(text_to_metadata(text, allow_title), value)
    assert metadata_to_text(*value) == text


def test_language_and_attribute(text="python .class", value=("python", {".class": None})):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == text


def test_title_and_attribute(text="This is my title. .class", value=("This is my title.", {".class": None})):
    compare(text_to_metadata(text, allow_title=True), value)
    assert metadata_to_text(*value) == text


@pytest.mark.parametrize("metadata", [".foo .bar", ".bar .foo", ".foo number=1 .bar"])
def test_attribute_metadata_order_round_trip(metadata):
    markdown = f"<!-- #region {metadata} -->\ntext\n<!-- #endregion -->\n"
    converted = markdown
    for _ in range(2):
        nb = jupytext.reads(converted, "md")
        assert nb.cells[0].metadata[".foo"] is None
        assert nb.cells[0].metadata[".bar"] is None
        converted = jupytext.writes(nb, "md")
        assert converted == markdown


def test_values_with_equal_signs_inside(text='python string="value=5"', value=("python", {"string": "value=5"})):
    compare(text_to_metadata(text), value)
    assert metadata_to_text(*value) == text


def test_incorrectly_encoded(text="this is an incorrect expression d={{4 b=3"):
    value = text_to_metadata(text, allow_title=True)
    assert metadata_to_text(*value) == text


def test_incorrectly_encoded_json(text='this is an incorrect expression {"d": "}'):
    value = text_to_metadata(text, allow_title=True)
    assert metadata_to_text(*value) == text


def test_parse_key_value():
    assert parse_key_equal_value("key='value' key2=5.0") == {
        "key": "value",
        "key2": 5.0,
    }


def test_parse_key_value_key():
    assert parse_key_equal_value("key='value' key2") == {
        "key": "value",
        "key2": None,
    }


@pytest.mark.parametrize(
    "text,metadata",
    [
        (".foo .bar", {".foo": None, ".bar": None}),
        (".bar .foo", {".bar": None, ".foo": None}),
        ("foo bar", {"foo": None, "bar": None}),
        (".foo number=1 .bar", {".foo": None, "number": 1, ".bar": None}),
        ("number=1 .foo .bar", {"number": 1, ".foo": None, ".bar": None}),
        (".foo .bar number=1", {".foo": None, ".bar": None, "number": 1}),
    ],
)
def test_attribute_metadata_order(text, metadata):
    parsed = parse_key_equal_value(text)
    assert list(parsed.items()) == list(metadata.items())
    assert metadata_to_text(parsed) == text


@pytest.mark.parametrize(
    "text,metadata",
    [
        ("foo=1 foo", {"foo": 1}),
        ("foo foo=1", {"foo": 1}),
        ("foo=1 foo=2 foo", {"foo": 2}),
        ("foo foo", {"foo": None}),
    ],
)
def test_duplicate_bare_metadata(text, metadata):
    assert parse_key_equal_value(text) == metadata


@pytest.mark.parametrize("key", ["ok", "also.ok", "all_right_55", "not,ok", "unexpected,key"])
def test_is_valid_metadata_key(key):
    assert is_valid_metadata_key(key) == ("," not in key)


@pytest.fixture()
def notebook_with_unsupported_key_in_metadata(python_notebook):
    nb = python_notebook
    nb.cells.append(new_markdown_cell("text", metadata={"unexpected,key": True}))
    return nb


def test_unsupported_key_in_metadata(notebook_with_unsupported_key_in_metadata, fmt_with_cell_metadata):
    """Notebook metadata that can't be parsed in text notebook cannot go to the text file,
    but it should still remain available in the ipynb file for paired notebooks."""
    with pytest.warns(
        UserWarning,
        match="The following metadata cannot be exported to the text notebook",
    ):
        text = jupytext.writes(notebook_with_unsupported_key_in_metadata, fmt_with_cell_metadata)
    assert "unexpected" not in text
    nb_text = jupytext.reads(text, fmt=fmt_with_cell_metadata)
    nb = combine_inputs_with_outputs(nb_text, notebook_with_unsupported_key_in_metadata, fmt=fmt_with_cell_metadata)
    assert nb.cells[-1].metadata == {"unexpected,key": True}


@pytest.fixture()
def notebook_with_collapsed_cell(python_notebook):
    nb = python_notebook
    nb.cells.append(new_markdown_cell("## Data", metadata={"jp-MarkdownHeadingCollapsed": True}))
    return nb


def test_notebook_with_collapsed_cell(notebook_with_collapsed_cell, fmt_with_cell_metadata):
    text = jupytext.writes(notebook_with_collapsed_cell, fmt_with_cell_metadata)
    assert "MarkdownHeadingCollapsed" in text
    nb = jupytext.reads(text, fmt=fmt_with_cell_metadata)
    compare_notebooks(nb, notebook_with_collapsed_cell, fmt=fmt_with_cell_metadata)


def test_empty_tags_are_not_saved_in_text_notebooks(no_jupytext_version_number, python_notebook, fmt="py:percent"):
    nb = python_notebook
    nb.cells.append(new_code_cell(metadata={"tags": []}))
    text = jupytext.writes(nb, fmt=fmt)
    assert "tags" not in text
    nb_text = jupytext.reads(text, fmt=fmt)
    nb2 = combine_inputs_with_outputs(nb_text, nb, fmt=fmt)
    assert nb2.cells[-1].metadata["tags"] == []
