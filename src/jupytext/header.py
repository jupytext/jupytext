"""Parse header of text notebooks"""

import logging
import re

import nbformat
import yaml
from nbformat.v4.nbbase import NotebookNode, new_raw_cell
from yaml.representer import SafeRepresenter

from .languages import (
    _SCRIPT_EXTENSIONS,
    comment_lines,
    default_language_from_metadata_and_ext,
)
from .metadata_filter import (
    _DEFAULT_NOTEBOOK_METADATA,
    _DEFAULT_ROOT_LEVEL_METADATA,
    _JUPYTER_METADATA_NAMESPACE,
    filter_metadata,
)
from .myst import MYST_FORMAT_NAME
from .pep8 import pep8_lines_between_cells
from .version import __version__

SafeRepresenter.add_representer(nbformat.NotebookNode, SafeRepresenter.represent_dict)

_HEADER_RE = re.compile(r"^---\s*$")
_BLANK_RE = re.compile(r"^\s*$")
_JUPYTER_RE = re.compile(r"^jupyter\s*:\s*$")
_LEFTSPACE_RE = re.compile(r"^\s")
_UTF8_HEADER = " -*- coding: utf-8 -*-"

# Change this to False in tests
INSERT_AND_CHECK_VERSION_NUMBER = True


class FrontMatterCell(NotebookNode):
    """A raw cell synthesized from front matter, which stores no cell metadata."""


def _new_frontmatter_cell(source, **kwargs):
    # Keep the origin in memory without adding a field to the serialized cell.
    return FrontMatterCell(new_raw_cell(source, **kwargs))


def insert_or_test_version_number():
    """Should the format name and version number be inserted in text
    representations (not in tests!)"""
    return INSERT_AND_CHECK_VERSION_NUMBER


def uncomment_line(line, prefix, suffix=""):
    """Remove prefix (and space) from line"""
    if prefix:
        if line.startswith(prefix + " "):
            line = line[len(prefix) + 1 :]
        elif line.startswith(prefix):
            line = line[len(prefix) :]
    if suffix:
        if line.endswith(suffix + " "):
            line = line[: -(1 + len(suffix))]
        elif line.endswith(suffix):
            line = line[: -len(suffix)]
    return line


def encoding_and_executable(notebook, metadata, ext):
    """Return encoding and executable lines for a notebook, if applicable"""
    lines = []
    comment = _SCRIPT_EXTENSIONS.get(ext, {}).get("comment")
    jupytext_metadata = metadata.get("jupytext", {})

    if comment is not None and "executable" in jupytext_metadata:
        lines.append("#!" + jupytext_metadata.pop("executable"))

    if comment is not None:
        if "encoding" in jupytext_metadata:
            lines.append(jupytext_metadata.pop("encoding"))
        elif default_language_from_metadata_and_ext(metadata, ext) != "python":
            for cell in notebook.cells:
                try:
                    cell.source.encode("ascii")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    lines.append(comment + _UTF8_HEADER)
                    break

    return lines


def insert_jupytext_info_and_filter_metadata(metadata, fmt, text_format, unsupported_keys):
    """Update the notebook metadata to include Jupytext information, and filter
    the notebook metadata according to the default or user filter"""
    if insert_or_test_version_number():
        metadata.setdefault("jupytext", {})["text_representation"] = {
            "extension": fmt["extension"],
            "format_name": text_format.format_name,
            "format_version": text_format.current_version_number,
            "jupytext_version": __version__,
        }

    if "jupytext" in metadata and not metadata["jupytext"]:
        del metadata["jupytext"]

    notebook_metadata_filter = fmt.get("notebook_metadata_filter")
    return filter_metadata(
        metadata,
        notebook_metadata_filter,
        _DEFAULT_NOTEBOOK_METADATA,
        unsupported_keys=unsupported_keys,
    )


def metadata_and_cell_to_header(notebook, metadata, text_format, fmt, unsupported_keys=None):
    """
    Return the text header corresponding to a notebook, and remove the
    first cell of the notebook if it contained the header
    """

    header = []

    lines_to_next_cell = None
    root_level_metadata = {}
    root_level_metadata_as_raw_cell = fmt.get("root_level_metadata_as_raw_cell", True)

    if not root_level_metadata_as_raw_cell:
        root_level_metadata = metadata.get("jupytext", {}).pop("root_level_metadata", {})
    elif notebook.cells:
        cell = notebook.cells[0]
        if cell.cell_type == "raw":
            lines = cell.source.strip("\n\t ").splitlines()
            if len(lines) >= 2 and _HEADER_RE.match(lines[0]) and _HEADER_RE.match(lines[-1]):
                header = lines[1:-1]
                lines_to_next_cell = cell.metadata.get("lines_to_next_cell")
                notebook.cells = notebook.cells[1:]

    metadata = insert_jupytext_info_and_filter_metadata(metadata, fmt, text_format, unsupported_keys)

    if metadata:
        root_level_metadata["jupyter"] = metadata

    if root_level_metadata:
        header.extend(yaml.safe_dump(root_level_metadata, default_flow_style=False).splitlines())

    if header:
        header = ["---"] + header + ["---"]

        if fmt.get("hide_notebook_metadata", False) and text_format.format_name == "markdown":
            header = ["<!--", ""] + header + ["", "-->"]

    return (
        comment_lines(header, text_format.header_prefix, text_format.header_suffix),
        lines_to_next_cell,
    )


def recursive_update(target, update, overwrite=True):
    """Update recursively a (nested) dictionary with the content of another.
    Inspired from https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    for key in update:
        value = update[key]
        if value is None:
            del target[key]
        elif isinstance(value, dict):
            target[key] = recursive_update(
                target.get(key, {}),
                value,
                overwrite=overwrite,
            )
        elif overwrite:
            target[key] = value
        else:
            target.setdefault(key, value)
    return target


def header_to_metadata_and_cell(lines, header_prefix, header_suffix, ext=None, root_level_metadata_as_raw_cell=True):
    """
    Return the metadata, a boolean to indicate if a jupyter section was found,
    the first cell of notebook if some metadata is found outside
    the jupyter section, and next loc in text
    """

    header = []
    jupyter = []
    in_jupyter = False
    in_html_div = False

    start = 0
    started = False
    ended = False
    metadata = {}
    i = -1

    comment = "#" if header_prefix == "#'" else header_prefix

    encoding_re = re.compile(rf"^[ \t\f]*{re.escape(comment)}.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")

    for i, line in enumerate(lines):
        if i == 0 and line.startswith("#!"):
            metadata.setdefault("jupytext", {})["executable"] = line[2:]
            start = i + 1
            continue
        if i == 0 or (i == 1 and not encoding_re.match(lines[0])):
            encoding = encoding_re.match(line)
            if encoding:
                if encoding.group(1) != "utf-8":
                    raise ValueError("Encodings other than utf-8 are not supported")
                metadata.setdefault("jupytext", {})["encoding"] = line
                start = i + 1
                continue
        if not line.startswith(header_prefix):
            break
        if not comment:
            if line.strip().startswith("<!--"):
                in_html_div = True
                continue

        if in_html_div:
            if ended:
                if "-->" in line:
                    break
            if not started and not line.strip():
                continue

        line = uncomment_line(line, header_prefix, header_suffix)
        if _HEADER_RE.match(line):
            if not started:
                started = True
                continue
            ended = True
            if in_html_div:
                continue
            break

        # Stop if there is something else than a YAML header
        if not started and line.strip():
            break

        if _JUPYTER_RE.match(line):
            in_jupyter = True
        elif line and not _LEFTSPACE_RE.match(line):
            in_jupyter = False

        if in_jupyter:
            jupyter.append(line)
        else:
            header.append(line)

    if ended:
        if jupyter:
            extra_metadata = metadata
            metadata = yaml.safe_load("\n".join(jupyter))["jupyter"]
            recursive_update(metadata, extra_metadata)

        lines_to_next_cell = 1
        if len(lines) > i + 1:
            line = uncomment_line(lines[i + 1], header_prefix)
            if not _BLANK_RE.match(line):
                lines_to_next_cell = 0
            else:
                i = i + 1
        else:
            lines_to_next_cell = 0

        if header:
            if root_level_metadata_as_raw_cell:
                cell = _new_frontmatter_cell(
                    source="\n".join(["---"] + header + ["---"]),
                    metadata=(
                        {}
                        if lines_to_next_cell == pep8_lines_between_cells(["---"], lines[i + 1 :], ext)
                        else {"lines_to_next_cell": lines_to_next_cell}
                    ),
                )
            else:
                cell = None
                root_level_metadata = yaml.safe_load("\n".join(header))
                metadata.setdefault("jupytext", {})["root_level_metadata"] = root_level_metadata
        else:
            cell = None

        return metadata, jupyter, cell, i + 1

    return metadata, False, None, start


def default_root_level_metadata_filter(fmt):
    """Return defaults for settings that promote or demote root level metadata."""
    if fmt and fmt.get("format_name") == MYST_FORMAT_NAME:
        from .myst import _DEFAULT_ROOT_LEVEL_METADATA as default_filter
    else:
        default_filter = _DEFAULT_ROOT_LEVEL_METADATA
    return default_filter


def metadata_to_metadata_and_cell(nb, metadata, fmt, unsupported_keys=None):
    # stash notebook metadata, including keys promoted to the root level
    metadata = recursive_update(
        metadata,
        filter_metadata(
            nb.metadata,
            fmt.get("root_level_metadata_filter", ""),
            default_root_level_metadata_filter(fmt),
            unsupported_keys=unsupported_keys,
            remove=True,
        ),
    )
    # move remaining metadata (i.e. frontmatter) to the first notebook cell
    if nb.metadata and fmt.get("root_level_metadata_as_raw_cell", True):
        frontmatter = yaml.safe_dump(nb.metadata, sort_keys=False)
        nb.cells.insert(0, _new_frontmatter_cell("---\n" + frontmatter + "---"))
    # attach the stashed metadata to notebook
    nb.metadata = metadata
    return nb


def metadata_and_cell_to_metadata(nb, fmt, unsupported_keys=None):
    # new metadata from filtered nb.metadata
    metadata = filter_metadata(
        nb.metadata,
        fmt.get("root_level_metadata_filter", ""),
        default_root_level_metadata_filter(fmt),
        unsupported_keys=unsupported_keys,
        remove=True,
    )
    # remaining nb.metadata moved under namespace key for jupyter metadata
    if nb.metadata:
        metadata[_JUPYTER_METADATA_NAMESPACE] = nb.metadata
    # move first cell frontmatter to the root level of nb.metadata (overwrites)
    if nb.cells and fmt.get("root_level_metadata_as_raw_cell", True):
        cell = nb.cells[0]
        if cell.cell_type == "raw":
            lines = cell.source.strip("\n\t ").splitlines()
            if len(lines) >= 2 and _HEADER_RE.match(lines[0]) and _HEADER_RE.match(lines[-1]):
                try:
                    frontmatter = next(yaml.safe_load_all(cell.source))
                except (yaml.parser.ParserError, yaml.scanner.ScannerError):
                    logging.warning("[jupytext] failed to parse YAML in raw cell")
                else:
                    if not isinstance(frontmatter, dict):
                        logging.warning("[jupytext] YAML header in raw cell is not a dictionary")
                    else:
                        nb.cells = nb.cells[1:]
                        if "root_level_metadata_filter" not in fmt and default_root_level_metadata_filter(fmt) == "all":
                            metadata.setdefault("jupytext", {})["root_level_metadata_filter"] = "-" + ",-".join(frontmatter)
                        metadata = recursive_update(frontmatter, metadata, overwrite=False)
    nb.metadata = metadata
    return nb
