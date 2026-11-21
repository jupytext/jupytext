"""
This module contains round-trip conversion between
myst formatted text documents and notebooks.
"""

import json
import re
import warnings
from textwrap import dedent

import nbformat as nbf
import yaml
from yaml.representer import SafeRepresenter

from .cell_to_text import three_backticks_or_more
from .metadata_filter import _JUPYTER_METADATA_NAMESPACE

try:
    from markdown_it import MarkdownIt
    from mdit_py_plugins.front_matter import front_matter_plugin
    from mdit_py_plugins.myst_blocks import myst_block_plugin
    from mdit_py_plugins.myst_role import myst_role_plugin
except ImportError:
    MarkdownIt = None

MYST_FORMAT_NAME = "myst"
CODE_DIRECTIVE = "{code-cell}"
RAW_DIRECTIVE = "{raw-cell}"
_DEFAULT_ROOT_LEVEL_METADATA = "all"

SafeRepresenter.add_representer(nbf.NotebookNode, SafeRepresenter.represent_dict)


def is_myst_available():
    """Whether the markdown-it-py package is available."""
    return MarkdownIt is not None


def raise_if_myst_is_not_available():
    if not is_myst_available():
        raise ImportError("The MyST Markdown format requires python >= 3.6 and markdown-it-py~=1.0")


def myst_version():
    """The version of myst."""
    return 0.13


def myst_extensions(no_md=False):
    """The allowed extensions for the myst format."""
    if no_md:
        return [".myst", ".mystnb", ".mnb"]
    return [".md", ".myst", ".mystnb", ".mnb"]


def get_parser():
    """Return the markdown-it parser to use."""
    parser = (
        MarkdownIt("commonmark")
        .enable("table")
        .use(front_matter_plugin)
        .use(myst_block_plugin)
        .use(myst_role_plugin)
        # we only need to parse block level components (for efficiency)
        .disable("inline", True)
    )
    return parser


def matches_mystnb(
    text,
    ext=None,
    requires_meta=True,
    code_directive=CODE_DIRECTIVE,
    raw_directive=RAW_DIRECTIVE,
):
    """Attempt to distinguish a file as myst, only given its extension and content.

    :param ext: the extension of the file
    :param requires_meta: requires the file to contain top matter metadata
    :param code_directive: the name of the directive to search for containing code cells
    :param raw_directive: the name of the directive to search for containing raw cells
    """
    # is the extension uniquely associated with myst (i.e. not just .md)
    if ext and "." + ("." + ext).rsplit(".", 1)[1] in myst_extensions(no_md=True):
        return True

    # might the text contain metadata front matter
    if requires_meta and not text.startswith("---"):
        return False

    try:
        tokens = get_parser().parse(text + "\n")
    except (TypeError, ValueError) as err:
        warnings.warn(f"myst-parser failed unexpectedly: {err}")  # pragma: no cover
        return False

    # Is the format information available in the jupytext text representation?
    if tokens and tokens[0].type == "front_matter":
        try:
            metadata = yaml.safe_load(tokens[0].content)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError):
            pass
        else:
            try:
                format_name = (
                    metadata.get(_JUPYTER_METADATA_NAMESPACE, metadata)
                    .get("jupytext", {})
                    .get("text_representation", {})
                    .get("format_name")
                )
            except AttributeError:
                pass
            else:
                if format_name == MYST_FORMAT_NAME:
                    return True

    # is there at least on fenced code block with a code/raw directive language
    for token in tokens:
        if token.type == "fence" and (token.info.startswith(code_directive) or token.info.startswith(raw_directive)):
            return True

    return False


class CompactDumper(yaml.SafeDumper):
    """This YAML dumper creates a more compact style for lists"""


def represent_list(self, data):
    """Compact lists"""
    flow_style = not any(isinstance(i, dict) for i in data)
    return self.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow_style)


def represent_dict(self, data):
    """Compact dicts"""
    return self.represent_mapping("tag:yaml.org,2002:map", data, flow_style=False)


CompactDumper.add_representer(list, represent_list)
CompactDumper.add_representer(dict, represent_dict)


def dump_yaml_blocks(data, compact=True):
    """Where possible, we try to use a more compact metadata style.

    For blocks with no nested dicts, the block is denoted by starting colons::

        :other: true
        :tags: [hide-output, show-input]

    For blocks with nesting the block is enlosed by ``---``::

        ---
        other:
            more: true
        tags: [hide-output, show-input]
        ---
    """
    # Allow unicode characters for taking accents into account
    string = yaml.dump(data, Dumper=CompactDumper, sort_keys=False, allow_unicode=True)
    lines = string.splitlines()
    if compact and all(line and line[0].isalpha() for line in lines):
        return "\n".join([f":{line}" for line in lines]) + "\n\n"
    return f"---\n{string}---\n"


class MystMetadataParsingError(Exception):
    """Error when parsing metadata from myst formatted text"""


def strip_blank_lines(text):
    """Remove initial blank lines"""
    text = text.rstrip()
    while text and text.startswith("\n"):
        text = text[1:]
    return text


def read_fenced_cell(token, cell_index, cell_type):
    """Parse (and validate) the full directive text."""
    content = token.content
    error_msg = f"{cell_type} cell {cell_index} at line {token.map[0] + 1} could not be read: "

    body_lines, options = parse_directive_options(content, error_msg)

    # remove first line of body if blank
    # this is to allow space between the options and the content
    if body_lines and not body_lines[0].strip():
        body_lines = body_lines[1:]

    return options, body_lines


def parse_directive_options(content, error_msg):
    """Parse (and validate) the directive option section."""
    options = {}
    if content.startswith("---"):
        content = "\n".join(content.splitlines()[1:])
        match = re.search(r"^-{3,}", content, re.MULTILINE)
        if match:
            yaml_block = content[: match.start()]
            content = content[match.end() + 1 :]
        else:
            yaml_block = content
            content = ""
        yaml_block = dedent(yaml_block)
        try:
            options = yaml.safe_load(yaml_block) or {}
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as error:
            raise MystMetadataParsingError(error_msg + "Invalid YAML; " + str(error))
    elif content.lstrip().startswith(":"):
        content_lines = content.splitlines()  # type: list
        yaml_lines = []
        while content_lines:
            if not content_lines[0].lstrip().startswith(":"):
                break
            yaml_lines.append(content_lines.pop(0).lstrip()[1:])
        yaml_block = "\n".join(yaml_lines)
        content = "\n".join(content_lines)
        try:
            options = yaml.safe_load(yaml_block) or {}
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as error:
            raise MystMetadataParsingError(error_msg + "Invalid YAML; " + str(error))

    return content.splitlines(), options


def read_cell_metadata(token, cell_index):
    """Return cell metadata"""
    metadata = {}
    if token.content:
        try:
            metadata = json.loads(token.content.strip())
        except Exception as err:
            raise MystMetadataParsingError(f"Markdown cell {cell_index} at line {token.map[0] + 1} could not be read: {err}")
        if not isinstance(metadata, dict):
            raise MystMetadataParsingError(f"Markdown cell {cell_index} at line {token.map[0] + 1} is not a dict")

    return metadata


def myst_to_notebook(
    text,
    code_directive=CODE_DIRECTIVE,
    raw_directive=RAW_DIRECTIVE,
    add_source_map=False,
):
    """Convert text written in the myst format to a notebook.

    :param text: the file text
    :param code_directive: the name of the directive to search for containing code cells
    :param raw_directive: the name of the directive to search for containing raw cells
    :param add_source_map: add a `source_map` key to the notebook metadata,
        which is a list of the starting source line number for each cell.

    :raises MystMetadataParsingError if the metadata block is not valid JSON/YAML

    NOTE: we assume here that all of these directives are at the top-level,
    i.e. not nested in other directives.
    """
    raise_if_myst_is_not_available()

    tokens = get_parser().parse(text + "\n")
    lines = text.splitlines()
    md_start_line = 0
    default_lexer = None

    # get the document metadata
    metadata_nb = {}
    if tokens and tokens[0].type == "front_matter":
        metadata = tokens.pop(0)
        md_start_line = metadata.map[1]
        try:
            metadata_nb = yaml.safe_load(metadata.content)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as error:
            raise MystMetadataParsingError(f"Notebook metadata: {error}")

    # create an empty notebook
    nbf_version = nbf.v4
    kwargs = {"metadata": nbf.from_dict(metadata_nb)}
    notebook = nbf_version.new_notebook(**kwargs)
    source_map = []  # this is a list of the starting line number for each cell

    def _flush_markdown(start_line, token, md_metadata):
        """When we find a cell we check if there is preceding text.o"""
        endline = token.map[0] if token else len(lines)
        md_source = strip_blank_lines("\n".join(lines[start_line:endline]))
        meta = nbf.from_dict(md_metadata)
        if md_source:
            source_map.append(start_line)
            notebook.cells.append(nbf_version.new_markdown_cell(source=md_source, metadata=meta))

    # iterate through the tokens to identify notebook cells
    nesting_level = 0
    md_metadata = {}

    for token in tokens:
        nesting_level += token.nesting

        if nesting_level != 0:
            # we ignore fenced block that are nested, e.g. as part of lists, etc
            continue

        if token.type == "fence" and token.info.startswith(code_directive):
            _flush_markdown(md_start_line, token, md_metadata)
            options, body_lines = read_fenced_cell(token, len(notebook.cells), "Code")
            assert token.info.startswith(code_directive)
            lexer = token.info[len(code_directive) :].strip()
            if lexer:
                if not default_lexer:
                    default_lexer = lexer
                elif lexer != default_lexer:
                    warnings.warn(f"All code cells in a MyST notebook must have the same language: {lexer}!={default_lexer}")

            meta = nbf.from_dict(options)
            source_map.append(token.map[0] + 1)
            notebook.cells.append(nbf_version.new_code_cell(source="\n".join(body_lines), metadata=meta))
            md_metadata = {}
            md_start_line = token.map[1]

        elif token.type == "fence" and token.info.startswith(raw_directive):
            _flush_markdown(md_start_line, token, md_metadata)
            options, body_lines = read_fenced_cell(token, len(notebook.cells), "Raw")
            meta = nbf.from_dict(options)
            source_map.append(token.map[0] + 1)
            notebook.cells.append(nbf_version.new_raw_cell(source="\n".join(body_lines), metadata=meta))
            md_metadata = {}
            md_start_line = token.map[1]

        elif token.type == "myst_block_break":
            _flush_markdown(md_start_line, token, md_metadata)
            md_metadata = read_cell_metadata(token, len(notebook.cells))
            md_start_line = token.map[1]

    _flush_markdown(md_start_line, None, md_metadata)

    if add_source_map:
        notebook.metadata["source_map"] = source_map

    if "language_info" not in notebook.metadata and default_lexer:
        has_metadata = bool(notebook.metadata)
        jupyter_metadata = notebook.metadata.setdefault(_JUPYTER_METADATA_NAMESPACE, {})
        jupytext_metadata = jupyter_metadata.setdefault("jupytext", {})
        jupytext_metadata["default_lexer"] = default_lexer
        if not has_metadata:
            jupytext_metadata["notebook_metadata_filter"] = "-all"

    return notebook


def notebook_to_myst(
    nb,
    code_directive=CODE_DIRECTIVE,
    raw_directive=RAW_DIRECTIVE,
    default_lexer=None,
):
    """Parse a notebook to a MyST formatted text document.

    :param nb: the notebook to parse
    :param code_directive: the name of the directive to use for code cells
    :param raw_directive: the name of the directive to use for raw cells
    :param default_lexer: a lexer name to use for annotating code cells
        (if ``nb.metadata.language_info.pygments_lexer`` is not available)
    """
    raise_if_myst_is_not_available()
    string = ""

    nb_metadata = nb.metadata

    # we add the pygments lexer as a directive argument, for use by syntax highlighters
    pygments_lexer = nb_metadata.get("language_info", {}).get("pygments_lexer", None)
    if pygments_lexer is None:
        pygments_lexer = default_lexer

    if nb_metadata:
        string += dump_yaml_blocks(nb_metadata, compact=False)

    last_cell_md = False
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "markdown":
            metadata = cell.metadata
            if metadata or last_cell_md:
                if metadata:
                    string += f"\n+++ {json.dumps(metadata)}\n"
                else:
                    string += "\n+++\n"
            string += "\n" + cell.source
            if not cell.source.endswith("\n"):
                string += "\n"
            last_cell_md = True

        elif cell.cell_type in ["code", "raw"]:
            cell_delimiter = three_backticks_or_more(cell.source.splitlines())
            string += "\n{}{}".format(
                cell_delimiter,
                code_directive if cell.cell_type == "code" else raw_directive,
            )
            if pygments_lexer and cell.cell_type == "code":
                string += f" {pygments_lexer}"
            string += "\n"
            metadata = cell.metadata
            if metadata:
                string += dump_yaml_blocks(metadata)
            elif cell.source.startswith("---") or cell.source.startswith(":"):
                string += "\n"
            string += cell.source
            if not cell.source.endswith("\n"):
                string += "\n"
            string += cell_delimiter + "\n"
            last_cell_md = False

        else:
            raise NotImplementedError(f"cell {i}, type: {cell.cell_type}")

    if not nb_metadata:
        # remove initial blank line
        assert string.startswith("\n")
        string = string[1:]

    return string.rstrip() + "\n"
