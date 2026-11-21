"""Read and write Jupyter notebooks as text files"""

import logging
import os
import sys
import warnings
from copy import copy, deepcopy

import nbformat
from nbformat.v4.nbbase import NotebookNode, new_code_cell, new_notebook
from nbformat.v4.rwbase import NotebookReader, NotebookWriter

from .cell_metadata import _IGNORE_CELL_METADATA
from .config import get_formats_from_notebook_and_config, load_jupytext_config
from .formats import (
    _VALID_FORMAT_OPTIONS,
    divine_format,
    format_name_for_ext,
    get_format_implementation,
    guess_format,
    long_form_one_format,
    read_format_from_metadata,
    rearrange_jupytext_metadata,
    update_jupytext_formats_metadata,
)
from .header import (
    _JUPYTER_METADATA_NAMESPACE,
    encoding_and_executable,
    header_to_metadata_and_cell,
    insert_jupytext_info_and_filter_metadata,
    insert_or_test_version_number,
    metadata_and_cell_to_header,
    metadata_and_cell_to_metadata,
    metadata_to_metadata_and_cell,
)
from .languages import (
    _SCRIPT_EXTENSIONS,
    default_language_from_metadata_and_ext,
    set_main_and_cell_language,
)
from .metadata_filter import filter_metadata, update_metadata_filters
from .myst import MYST_FORMAT_NAME, myst_extensions, myst_to_notebook, notebook_to_myst
from .pandoc import md_to_notebook, notebook_to_md
from .pep8 import pep8_lines_between_cells
from .quarto import notebook_to_qmd, qmd_to_notebook
from .marimo import notebook_to_marimo_py, marimo_py_to_notebook
from .version import __version__


class NotSupportedNBFormatVersion(NotImplementedError):
    """An error issued when the current notebook format is not supported by this version of Jupytext"""


class TextNotebookConverter(NotebookReader, NotebookWriter):
    """A class that can read or write a Jupyter notebook as text"""

    def __init__(self, fmt, config):
        self.fmt = copy(long_form_one_format(fmt))
        self.config = config
        self.ext = self.fmt["extension"]
        self.implementation = get_format_implementation(self.ext, self.fmt.get("format_name"))

    def update_fmt_with_notebook_options(self, metadata, read=False):
        """Update format options with the values in the notebook metadata, and record those
        options in the notebook metadata"""
        # The settings in the Jupytext configuration file have precedence over the metadata in the notebook
        # when the notebook is saved. This is because the metadata in the notebook might not be visible
        # in the text representation when e.g. notebook_metadata_filter="-all", which makes them hard to edit.
        if not read and self.config is not None:
            self.config.set_default_format_options(self.fmt, read)

        # Use format options from the notebook if not already set by the config
        for opt in _VALID_FORMAT_OPTIONS:
            if opt in metadata.get("jupytext", {}):
                self.fmt.setdefault(opt, metadata["jupytext"][opt])

        # When we read the notebook we use the values of the config as defaults, as again the text representation
        # of the notebook might not store the format options when notebook_metadata_filter="-all"
        if read and self.config is not None:
            self.config.set_default_format_options(self.fmt, read=read)

        # We save the format options in the notebook metadata
        for opt in _VALID_FORMAT_OPTIONS:
            if opt in self.fmt:
                metadata.setdefault("jupytext", {})[opt] = self.fmt[opt]

        # Is this format the same as that documented in the YAML header? If so, we want to know the format version
        file_fmt = metadata.get("jupytext", {}).get("text_representation", {})
        if self.fmt.get("extension") == file_fmt.get("extension") and self.fmt.get("format_name") == file_fmt.get(
            "format_name"
        ):
            self.fmt.update(file_fmt)

        # rST to md conversion should happen only once
        if metadata.get("jupytext", {}).get("rst2md") is True:
            metadata["jupytext"]["rst2md"] = False

    def reads(self, s, **_):
        """Read a notebook represented as text"""
        if self.fmt.get("format_name") == "pandoc":
            return md_to_notebook(s)

        if self.fmt.get("format_name") == "quarto":
            return qmd_to_notebook(s)

        if self.fmt.get("format_name") == "marimo":
            return marimo_py_to_notebook(s)

        if self.fmt.get("format_name") == MYST_FORMAT_NAME:
            nb = myst_to_notebook(s)
            return self.split_frontmatter(nb)

        lines = s.splitlines()

        cells = []
        metadata, jupyter_md, header_cell, pos = header_to_metadata_and_cell(
            lines,
            self.implementation.header_prefix,
            self.implementation.header_suffix,
            self.implementation.extension,
            self.fmt.get(
                "root_level_metadata_as_raw_cell",
                (self.config.root_level_metadata_as_raw_cell if self.config is not None else True),
            ),
        )
        default_language = default_language_from_metadata_and_ext(metadata, self.implementation.extension)
        self.update_fmt_with_notebook_options(metadata, read=True)

        if header_cell:
            cells.append(header_cell)

        lines = lines[pos:]

        if self.implementation.format_name and self.implementation.format_name.startswith("sphinx"):
            cells.append(new_code_cell(source="%matplotlib inline"))

        cell_metadata_json = False

        while lines:
            reader = self.implementation.cell_reader_class(self.fmt, default_language)
            cell, pos = reader.read(lines)
            cells.append(cell)
            cell_metadata_json = cell_metadata_json or reader.cell_metadata_json
            if pos <= 0:
                raise Exception("Blocked at lines " + "\n".join(lines[:6]))  # pragma: no cover
            lines = lines[pos:]

        custom_cell_magics = self.fmt.get("custom_cell_magics", "").split(",")
        custom_language_magics = self.fmt.get("custom_language_magics", "").split(",")
        set_main_and_cell_language(metadata, cells, self.implementation.extension, custom_cell_magics + custom_language_magics)
        cell_metadata = set()
        for cell in cells:
            cell_metadata.update(cell.metadata.keys())
        update_metadata_filters(metadata, jupyter_md, cell_metadata)

        if cell_metadata_json:
            metadata.setdefault("jupytext", {}).setdefault("cell_metadata_json", True)

        if self.implementation.format_name and self.implementation.format_name.startswith("sphinx"):
            filtered_cells = []
            for i, cell in enumerate(cells):
                if (
                    cell.source == ""
                    and i > 0
                    and i + 1 < len(cells)
                    and cells[i - 1].cell_type != "markdown"
                    and cells[i + 1].cell_type != "markdown"
                ):
                    continue
                filtered_cells.append(cell)
            cells = filtered_cells

        return new_notebook(cells=cells, metadata=metadata)

    def filter_notebook(self, nb, metadata, preserve_cell_ids=True):
        self.update_fmt_with_notebook_options(nb.metadata)
        unsupported_keys = set()
        metadata = insert_jupytext_info_and_filter_metadata(
            metadata, self.fmt, self.implementation, unsupported_keys=unsupported_keys
        )
        # We sort the notebook metadata for consistency with v1.16
        metadata = dict(sorted(metadata.items()))

        cells = []
        for cell in nb.cells:
            cell_kwargs = dict(cell)
            cell_kwargs["metadata"] = filter_metadata(
                cell.metadata,
                self.fmt.get("cell_metadata_filter"),
                _IGNORE_CELL_METADATA,
                unsupported_keys=unsupported_keys,
            )
            if not preserve_cell_ids:
                cell_kwargs.pop("id", None)
            elif hasattr(cell, "id"):
                cell_kwargs["id"] = cell.id
            if cell.cell_type == "code":
                # Drop outputs and execution count
                cell_kwargs["outputs"] = []
                cell_kwargs["execution_count"] = None

            cells.append(NotebookNode(**cell_kwargs))

        _warn_on_unsupported_keys(unsupported_keys)

        return NotebookNode(
            nbformat=nb.nbformat,
            nbformat_minor=nb.nbformat_minor,
            metadata=metadata,
            cells=cells,
        )

    def writes(self, nb, metadata=None, **kwargs):
        """Return the text representation of the notebook"""
        if self.fmt.get("format_name") == "pandoc":
            return notebook_to_md(self.filter_notebook(nb, metadata))
        if self.fmt.get("format_name") == "quarto" or self.ext == ".qmd":
            return notebook_to_qmd(self.filter_notebook(nb, metadata))
        if self.fmt.get("format_name") == "marimo":
            return notebook_to_marimo_py(self.filter_notebook(nb, metadata))
        if self.fmt.get("format_name") == MYST_FORMAT_NAME or self.ext in myst_extensions(no_md=True):
            default_lexer_from_language_info = metadata.get("language_info", {}).get("pygments_lexer", None)
            default_lexer_from_jupytext_metadata = metadata.get("jupytext", {}).pop("default_lexer", None)
            default_lexer = default_lexer_from_language_info or default_lexer_from_jupytext_metadata
            nb = self.filter_notebook(nb, metadata)
            nb = self.merge_frontmatter(nb)
            return notebook_to_myst(nb, default_lexer=default_lexer)

        # Copy the notebook, in order to be sure we do not modify the original notebook
        nb = NotebookNode(
            nbformat=nb.nbformat,
            nbformat_minor=nb.nbformat_minor,
            metadata=deepcopy(metadata or nb.metadata),
            cells=nb.cells,
        )

        metadata = nb.metadata
        default_language = default_language_from_metadata_and_ext(metadata, self.implementation.extension, True) or "python"
        self.update_fmt_with_notebook_options(nb.metadata)
        if "use_runtools" not in self.fmt:
            for cell in nb.cells:
                if cell.metadata.get("hide_input", False) or cell.metadata.get("hide_output", False):
                    self.fmt["use_runtools"] = True
                    break

        header = encoding_and_executable(nb, metadata, self.ext)
        unsupported_keys = set()
        header_content, header_lines_to_next_cell = metadata_and_cell_to_header(
            nb,
            metadata,
            self.implementation,
            self.fmt,
            unsupported_keys=unsupported_keys,
        )
        header.extend(header_content)

        cell_exporters = []
        looking_for_first_markdown_cell = self.implementation.format_name and self.implementation.format_name.startswith(
            "sphinx"
        )
        split_at_heading = self.fmt.get("split_at_heading", False)

        for cell in nb.cells:
            if looking_for_first_markdown_cell and cell.cell_type == "markdown":
                cell.metadata.setdefault("cell_marker", '"""')
                looking_for_first_markdown_cell = False

            cell_exporters.append(
                self.implementation.cell_exporter_class(cell, default_language, self.fmt, unsupported_keys=unsupported_keys)
            )

        _warn_on_unsupported_keys(unsupported_keys)

        texts = [cell.cell_to_text() for cell in cell_exporters]
        lines = []

        # concatenate cells in reverse order to determine how many blank lines (pep8)
        for i, cell in reversed(list(enumerate(cell_exporters))):
            text = cell.remove_eoc_marker(texts[i], lines)

            if (
                i == 0
                and self.implementation.format_name
                and self.implementation.format_name.startswith("sphinx")
                and (text in [["%matplotlib inline"], ["# %matplotlib inline"]])
            ):
                continue

            lines_to_next_cell = cell.lines_to_next_cell
            if lines_to_next_cell is None:
                lines_to_next_cell = pep8_lines_between_cells(text, lines, self.implementation.extension)

            text.extend([""] * lines_to_next_cell)

            # two blank lines between markdown cells in Rmd when those do not have explicit region markers
            if self.ext in [".md", ".markdown", ".Rmd"] and not cell.is_code():
                if (
                    i + 1 < len(cell_exporters)
                    and not cell_exporters[i + 1].is_code()
                    and not texts[i][0].startswith("<!-- #")
                    and not texts[i + 1][0].startswith("<!-- #")
                    and (not split_at_heading or not (texts[i + 1] and texts[i + 1][0].startswith("#")))
                ):
                    text.append("")

            # "" between two consecutive code cells in sphinx
            if self.implementation.format_name.startswith("sphinx") and cell.is_code():
                if i + 1 < len(cell_exporters) and cell_exporters[i + 1].is_code():
                    text.append('""')

            lines = text + lines

        if header_lines_to_next_cell is None:
            header_lines_to_next_cell = pep8_lines_between_cells(header_content, lines, self.implementation.extension)

        header.extend([""] * header_lines_to_next_cell)

        return "\n".join(header + lines)

    def split_frontmatter(self, nb):
        """Use during self.reads to separate notebook metadata from other frontmatter."""
        unsupported_keys = set()
        metadata = nb.metadata.pop(_JUPYTER_METADATA_NAMESPACE, {})
        self.update_fmt_with_notebook_options(
            {
                "jupytext": {
                    **metadata.get("jupytext", {}),
                    **nb.metadata.get("jupytext", {}),
                },
            },
            read=True,
        )
        nb = metadata_to_metadata_and_cell(nb, metadata, self.fmt, unsupported_keys)
        _warn_on_unsupported_keys(unsupported_keys)
        return nb

    def merge_frontmatter(self, nb):
        """Use during self.writes to rewrite notebook metadata as frontmatter content."""
        unsupported_keys = set()
        nb = metadata_and_cell_to_metadata(nb, self.fmt, unsupported_keys)
        _warn_on_unsupported_keys(unsupported_keys)
        return nb


def reads(text, fmt=None, as_version=nbformat.NO_CONVERT, config=None, **kwargs):
    """
    Read a notebook from a string

    :param text: the text representation of the notebook
    :param fmt: (optional) the jupytext format like `md`, `py:percent`, ...
    :param as_version: see nbformat.reads
    :param config: (optional) a Jupytext configuration object
    :param kwargs: (not used) additional parameters for nbformat.reads
    :return: the notebook
    """
    fmt = copy(fmt) if fmt else divine_format(text)
    fmt = long_form_one_format(fmt)
    ext = fmt["extension"]

    if ext == ".ipynb":
        nb = nbformat.reads(text, as_version, **kwargs)
        (version, version_minor) = nbformat.reader.get_version(nb)
        if version != 4:
            warnings.warn(
                f"Notebooks in nbformat version {version}.{version_minor} are not supported by Jupytext. "
                f"Please consider converting them to nbformat version 4.x with "
                f"'jupyter nbconvert --to notebook --inplace'"
            )
        return nb

    format_name = read_format_from_metadata(text, ext) or fmt.get("format_name")

    if format_name:
        format_options = {}
    else:
        format_name, format_options = guess_format(text, ext)

    if format_name:
        fmt["format_name"] = format_name

    fmt.update(format_options)
    reader = TextNotebookConverter(fmt, config)
    notebook = reader.reads(text, **kwargs)
    rearrange_jupytext_metadata(notebook.metadata)

    if format_name and insert_or_test_version_number():
        notebook.metadata.setdefault("jupytext", {}).setdefault("text_representation", {}).update(
            {"extension": ext, "format_name": format_name}
        )

    return notebook


def read(fp, as_version=nbformat.NO_CONVERT, fmt=None, config=None, **kwargs):
    """Read a notebook from a file name or a file object

    :param fp: a file name or a file object
    :param as_version: see nbformat.read
    :param fmt: (optional) the jupytext format like `md`, `py:percent`, ...
    :param config: (optional) a Jupytext configuration object
    :param kwargs: (not used) additional parameters for nbformat.read
    :return: the notebook
    """
    if as_version != nbformat.NO_CONVERT and not isinstance(as_version, int):
        raise TypeError("Second argument 'as_version' should be either nbformat.NO_CONVERT, or an integer.")

    if fp == "-":
        text = sys.stdin.read()
        # Update the input format by reference if missing
        if isinstance(fmt, dict) and not fmt:
            fmt.update(long_form_one_format(divine_format(text)))
        return reads(text, fmt)

    if not hasattr(fp, "read"):
        # Treat fp as a file name
        fp = str(fp)
        _, ext = os.path.splitext(fp)
        fmt = copy(fmt or {})
        if not isinstance(fmt, dict):
            fmt = long_form_one_format(fmt)
        fmt.update({"extension": ext})
        with open(fp, encoding="utf-8") as stream:
            return read(stream, as_version=as_version, fmt=fmt, config=config, **kwargs)

    if fmt is not None:
        fmt = long_form_one_format(fmt)
        if fmt["extension"] == ".ipynb":
            notebook = nbformat.read(fp, as_version, **kwargs)
            rearrange_jupytext_metadata(notebook.metadata)
            return notebook

    return reads(fp.read(), fmt, config=config, **kwargs)


def writes(notebook, fmt, version=nbformat.NO_CONVERT, config=None, **kwargs):
    """Return the text representation of the notebook

    :param notebook: the notebook
    :param fmt: the jupytext format like `md`, `py:percent`, ...
    :param version: see nbformat.writes
    :param config: (optional) a Jupytext configuration object
    :param kwargs: (not used) additional parameters for nbformat.writes
    :return: the text representation of the notebook
    """
    if version is not nbformat.NO_CONVERT:
        if not isinstance(version, int):
            raise TypeError("The argument 'version' should be either nbformat.NO_CONVERT, or an integer.")
        notebook = nbformat.convert(notebook, version)
    (version, version_minor) = nbformat.reader.get_version(notebook)
    if version < 4:
        raise NotSupportedNBFormatVersion(
            f"Notebooks in nbformat version {version}.{version_minor} are not supported by Jupytext. "
            f"Please convert your notebooks to nbformat version 4 with "
            f"'jupyter nbconvert --to notebook --inplace', or call this function with 'version=4'."
        )
    if version > 4 or (version == 4 and version_minor > 5):
        warnings.warn(
            f"Notebooks in nbformat version {version}.{version_minor} "
            f"have not been tested with Jupytext version {__version__}."
        )

    metadata = deepcopy(notebook.metadata)
    rearrange_jupytext_metadata(metadata)
    fmt = copy(fmt)
    fmt = long_form_one_format(fmt, metadata)
    ext = fmt["extension"]
    format_name = fmt.get("format_name")

    if ext == ".ipynb":
        return nbformat.writes(
            drop_text_representation_metadata(notebook, metadata),
            version,
            **kwargs,
        )

    if not format_name:
        format_name = format_name_for_ext(metadata, ext, explicit_default=False)

    # Since Jupytext==1.17, the default format for
    # writing a notebook to a script is the percent format
    if not format_name and "cell_markers" not in fmt and ext in _SCRIPT_EXTENSIONS:
        format_name = "percent"

    if format_name:
        fmt["format_name"] = format_name
        update_jupytext_formats_metadata(metadata, fmt)

    writer = TextNotebookConverter(fmt, config)
    return writer.writes(notebook, metadata)


def drop_text_representation_metadata(notebook, metadata=None):
    """When the notebook is saved to an ipynb file, we drop the text_representation metadata"""
    if metadata is None:
        # Make a copy to avoid modification by reference
        metadata = deepcopy(notebook["metadata"])

    jupytext_metadata = metadata.get("jupytext", {})
    jupytext_metadata.pop("text_representation", {})

    # Remove the jupytext section if empty
    if not jupytext_metadata:
        metadata.pop("jupytext", {})

    return NotebookNode(
        nbformat=notebook["nbformat"],
        nbformat_minor=notebook["nbformat_minor"],
        metadata=metadata,
        cells=notebook["cells"],
    )


def write(nb, fp, version=nbformat.NO_CONVERT, fmt=None, config=None, **kwargs):
    """Write a notebook to a file name or a file object

    :param nb: the notebook
    :param fp: a file name or a file object
    :param version: see nbformat.write
    :param fmt: (optional if fp is a file name) the jupytext format like `md`, `py:percent`, ...
    :param config: (optional) a Jupytext configuration object
    :param kwargs: (not used) additional parameters for nbformat.write
    """
    if fp == "-":
        # Use sys.stdout.buffer when possible, and explicit utf-8 encoding, cf. #331
        content = writes(nb, version=version, fmt=fmt, config=config, **kwargs)
        try:
            # Python 3
            sys.stdout.buffer.write(content.encode("utf-8"))
        except AttributeError:
            sys.stdout.write(content.encode("utf-8"))
        return

    if not hasattr(fp, "write"):
        # Treat fp as a file name
        fp = str(fp)
        _, ext = os.path.splitext(fp)
        fmt = copy(fmt or {})
        fmt = long_form_one_format(fmt, update={"extension": ext})
        create_prefix_dir(fp, fmt, None)

        with open(fp, "w", encoding="utf-8") as stream:
            write(nb, stream, version=version, fmt=fmt, config=config, **kwargs)
            return
    else:
        assert fmt is not None, "'fmt' argument in jupytext.write is mandatory unless fp is a file name"

    content = writes(nb, version=version, fmt=fmt, config=config, **kwargs)
    if isinstance(content, bytes):
        content = content.decode("utf8")
    fp.write(content)
    if not content.endswith("\n"):
        fp.write("\n")


def create_prefix_dir(nb_file, fmt, log):
    """Create directory if fmt has a prefix"""
    if "prefix" in fmt:
        nb_dir = os.path.dirname(nb_file) + os.path.sep
        if not os.path.isdir(nb_dir):
            if log is not None:
                log(f"[jupytext] creating missing directory {nb_dir}")
            else:
                logging.log(logging.WARNING, "[jupytext] creating missing directory %s", nb_dir)
            os.makedirs(nb_dir)


def _warn_on_unsupported_keys(unsupported_keys):
    if unsupported_keys:
        warnings.warn(f"The following metadata cannot be exported to the text notebook: {sorted(unsupported_keys)}")


def get_formats_from_notebook_path(nb_file, fmt=None):
    """
    Return the paired formats for a given notebook in the extended form.

    Parameters
    ----------
    nb_file : str
        Path to the notebook file.
    fmt : dict or None, optional
        The Jupytext format specification (default is None).

    Returns
    -------
    list of dict
        The paired formats in the 'extended form', i.e., as a list of dictionaries
        where each dictionary fully specifies a format (including extension, format_name, etc.).
    """
    config = load_jupytext_config(nb_file)
    notebook = read(nb_file, fmt=fmt, config=config)
    return get_formats_from_notebook_and_config(notebook, config, nb_file)
