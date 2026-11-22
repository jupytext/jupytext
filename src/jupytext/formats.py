"""
In this file the various text notebooks formats are defined. Please contribute
new formats here!
"""

import os
import re
import warnings

import nbformat
import yaml

from .cell_reader import (
    DoublePercentScriptCellReader,
    HydrogenCellReader,
    LightScriptCellReader,
    MarkdownCellReader,
    RMarkdownCellReader,
    RScriptCellReader,
    SphinxGalleryScriptCellReader,
)
from .cell_to_text import (
    BareScriptCellExporter,
    DoublePercentCellExporter,
    HydrogenCellExporter,
    LightScriptCellExporter,
    MarkdownCellExporter,
    RMarkdownCellExporter,
    RScriptCellExporter,
    SphinxGalleryCellExporter,
)
from .header import header_to_metadata_and_cell, insert_or_test_version_number
from .languages import _COMMENT_CHARS, _SCRIPT_EXTENSIONS, same_language
from .magics import is_magic
from .metadata_filter import metadata_filter_as_string
from .myst import (
    MYST_FORMAT_NAME,
    is_myst_available,
    matches_mystnb,
    myst_extensions,
    myst_version,
)
from .pandoc import is_pandoc_available, pandoc_version
from .stringparser import StringParser
from .version import __version__


class JupytextFormatError(ValueError):
    """Error in the specification of the format for the text notebook"""


class NotebookFormatDescription:
    """Description of a notebook format"""

    def __init__(
        self,
        format_name,
        extension,
        header_prefix,
        cell_reader_class,
        cell_exporter_class,
        current_version_number,
        header_suffix="",
        min_readable_version_number=None,
    ):
        self.format_name = format_name
        self.extension = extension
        self.header_prefix = header_prefix
        self.header_suffix = header_suffix
        self.cell_reader_class = cell_reader_class
        self.cell_exporter_class = cell_exporter_class
        self.current_version_number = current_version_number
        self.min_readable_version_number = min_readable_version_number


JUPYTEXT_FORMATS = (
    [
        NotebookFormatDescription(
            format_name="markdown",
            extension=".md",
            header_prefix="",
            cell_reader_class=MarkdownCellReader,
            cell_exporter_class=MarkdownCellExporter,
            # Version 1.0 on 2018-08-31 - jupytext v0.6.0 : Initial version
            # Version 1.1 on 2019-03-24 - jupytext v1.1.0 : Markdown regions and cell metadata
            # Version 1.2 on 2019-09-21 - jupytext v1.3.0 : Raw regions are now encoded with HTML comments (#321)
            # and by default, cell metadata use the key=value representation (#347)
            # Version 1.3 on 2021-01-24 - jupytext v1.10.0 : Code cells may start with more than three backticks (#712)
            current_version_number="1.3",
            min_readable_version_number="1.0",
        ),
        NotebookFormatDescription(
            format_name="markdown",
            extension=".markdown",
            header_prefix="",
            cell_reader_class=MarkdownCellReader,
            cell_exporter_class=MarkdownCellExporter,
            current_version_number="1.2",
            min_readable_version_number="1.0",
        ),
        NotebookFormatDescription(
            format_name="rmarkdown",
            extension=".Rmd",
            header_prefix="",
            cell_reader_class=RMarkdownCellReader,
            cell_exporter_class=RMarkdownCellExporter,
            # Version 1.0 on 2018-08-22 - jupytext v0.5.2 : Initial version
            # Version 1.1 on 2019-03-24 - jupytext v1.1.0 : Markdown regions and cell metadata
            # Version 1.2 on 2019-09-21 - jupytext v1.3.0 : Raw regions are now encoded with HTML comments (#321)
            # and by default, cell metadata use the key=value representation in raw and markdown cells (#347)
            current_version_number="1.2",
            min_readable_version_number="1.0",
        ),
    ]
    + [
        NotebookFormatDescription(
            format_name="light",
            extension=ext,
            header_prefix=_SCRIPT_EXTENSIONS[ext]["comment"],
            header_suffix=_SCRIPT_EXTENSIONS[ext].get("comment_suffix", ""),
            cell_reader_class=LightScriptCellReader,
            cell_exporter_class=LightScriptCellExporter,
            # Version 1.5 on 2019-10-19 - jupytext v1.3.0 - Cell metadata represented as key=value by default
            # Version 1.4 on 2019-03-30 - jupytext v1.1.0 - custom cell markers allowed
            # Version 1.3 on 2018-09-22 - jupytext v0.7.0rc0 : Metadata are
            # allowed for all cell types (and then include 'cell_type')
            # Version 1.2 on 2018-09-05 - jupytext v0.6.3 : Metadata bracket
            # can be omitted when empty, if previous line is empty #57
            # Version 1.1 on 2018-08-25 - jupytext v0.6.0 : Cells separated
            # with one blank line #38
            # Version 1.0 on 2018-08-22 - jupytext v0.5.2 : Initial version
            current_version_number="1.5",
            min_readable_version_number="1.1",
        )
        for ext in _SCRIPT_EXTENSIONS
    ]
    + [
        NotebookFormatDescription(
            format_name="nomarker",
            extension=ext,
            header_prefix=_SCRIPT_EXTENSIONS[ext]["comment"],
            header_suffix=_SCRIPT_EXTENSIONS[ext].get("comment_suffix", ""),
            cell_reader_class=LightScriptCellReader,
            cell_exporter_class=BareScriptCellExporter,
            current_version_number="1.0",
            min_readable_version_number="1.0",
        )
        for ext in _SCRIPT_EXTENSIONS
    ]
    + [
        NotebookFormatDescription(
            format_name="percent",
            extension=ext,
            header_prefix=_SCRIPT_EXTENSIONS[ext]["comment"],
            header_suffix=_SCRIPT_EXTENSIONS[ext].get("comment_suffix", ""),
            cell_reader_class=DoublePercentScriptCellReader,
            cell_exporter_class=DoublePercentCellExporter,
            # Version 1.3 on 2019-09-21 - jupytext v1.3.0: Markdown cells can be quoted using triple quotes #305
            # and cell metadata are represented as key=value by default
            # Version 1.2 on 2018-11-18 - jupytext v0.8.6: Jupyter magics are commented by default #126, #132
            # Version 1.1 on 2018-09-23 - jupytext v0.7.0rc1 : [markdown] and
            # [raw] for markdown and raw cells.
            # Version 1.0 on 2018-09-22 - jupytext v0.7.0rc0 : Initial version
            current_version_number="1.3",
            min_readable_version_number="1.1",
        )
        for ext in _SCRIPT_EXTENSIONS
    ]
    + [
        NotebookFormatDescription(
            format_name="hydrogen",
            extension=ext,
            header_prefix=_SCRIPT_EXTENSIONS[ext]["comment"],
            header_suffix=_SCRIPT_EXTENSIONS[ext].get("comment_suffix", ""),
            cell_reader_class=HydrogenCellReader,
            cell_exporter_class=HydrogenCellExporter,
            # Version 1.2 on 2018-12-14 - jupytext v0.9.0: same as percent - only magics are not commented by default
            current_version_number="1.3",
            min_readable_version_number="1.1",
        )
        for ext in _SCRIPT_EXTENSIONS
    ]
    + [
        NotebookFormatDescription(
            format_name="spin",
            extension=ext,
            header_prefix="#'",
            cell_reader_class=RScriptCellReader,
            cell_exporter_class=RScriptCellExporter,
            # Version 1.0 on 2018-08-22 - jupytext v0.5.2 : Initial version
            current_version_number="1.0",
        )
        for ext in [".r", ".R"]
    ]
    + [
        NotebookFormatDescription(
            format_name="sphinx",
            extension=".py",
            header_prefix="#",
            cell_reader_class=SphinxGalleryScriptCellReader,
            cell_exporter_class=SphinxGalleryCellExporter,
            # Version 1.0 on 2018-09-22 - jupytext v0.7.0rc0 : Initial version
            current_version_number="1.1",
        ),
        NotebookFormatDescription(
            format_name="pandoc",
            extension=".md",
            header_prefix="",
            cell_reader_class=None,
            cell_exporter_class=None,
            current_version_number=pandoc_version(),
        ),
        NotebookFormatDescription(
            format_name="quarto",
            extension=".qmd",
            header_prefix="",
            cell_reader_class=None,
            cell_exporter_class=None,
            # Version 1.0 on 2021-09-07 = quarto --version >= 0.2.134,
            # cf. https://github.com/mwouts/jupytext/issues/837
            current_version_number="1.0",
        ),
        NotebookFormatDescription(
            format_name="marimo",
            extension=".py",
            header_prefix="",
            cell_reader_class=None,
            cell_exporter_class=None,
            # Version 1.0 on 2025-09-07
            current_version_number="1.0",
        ),
    ]
    + [
        NotebookFormatDescription(
            format_name=MYST_FORMAT_NAME,
            extension=ext,
            header_prefix="",
            cell_reader_class=None,
            cell_exporter_class=None,
            current_version_number=myst_version(),
        )
        for ext in myst_extensions()
    ]
)

NOTEBOOK_EXTENSIONS = list(dict.fromkeys([".ipynb"] + [fmt.extension for fmt in JUPYTEXT_FORMATS]))
EXTENSION_PREFIXES = [".lgt", ".spx", ".pct", ".hyd", ".nb"]
FORMATS_WITH_NO_CELL_METADATA = {"sphinx", "nomarker", "spin", "quarto", "marimo"}


def get_format_implementation(ext, format_name=None):
    """Return the implementation for the desired format"""
    # remove pre-extension if any
    ext = "." + ext.split(".")[-1]

    formats_for_extension = []
    for fmt in JUPYTEXT_FORMATS:
        if fmt.extension == ext:
            if fmt.format_name == format_name or not format_name:
                return fmt
            formats_for_extension.append(fmt.format_name)

    if formats_for_extension:
        raise JupytextFormatError(
            "Format '{}' is not associated to extension '{}'. Please choose one of: {}.".format(
                format_name, ext, ", ".join(formats_for_extension)
            )
        )
    raise JupytextFormatError(f"No format associated to extension '{ext}'")


def read_metadata(text, ext):
    """Return the header metadata"""
    ext = "." + ext.split(".")[-1]
    lines = text.splitlines()

    if ext in [".md", ".markdown", ".Rmd"]:
        comment = comment_suffix = ""
    else:
        comment = _SCRIPT_EXTENSIONS.get(ext, {}).get("comment", "#")
        comment_suffix = _SCRIPT_EXTENSIONS.get(ext, {}).get("comment_suffix", "")

    metadata, _, _, _ = header_to_metadata_and_cell(lines, comment, comment_suffix, ext)
    if ext in [".r", ".R"] and not metadata:
        metadata, _, _, _ = header_to_metadata_and_cell(lines, "#'", "", ext)

    # metadata in MyST format may be at root level (i.e. not caught above)
    if not metadata and ext in myst_extensions() and text.startswith("---"):
        for header in yaml.safe_load_all(text):
            if not isinstance(header, dict):
                continue
            if header.get("jupytext", {}).get("text_representation", {}).get("format_name") == MYST_FORMAT_NAME:
                return header
            return metadata

    return metadata


def read_format_from_metadata(text, ext):
    """Return the format of the file, when that information is available from the metadata"""
    metadata = read_metadata(text, ext)
    rearrange_jupytext_metadata(metadata)
    return format_name_for_ext(metadata, ext, explicit_default=False)


def guess_format(text, ext):
    """Guess the format and format options of the file, given its extension and content"""
    metadata = read_metadata(text, ext)

    if "text_representation" in metadata.get("jupytext", {}):
        return format_name_for_ext(metadata, ext), {}

    if is_myst_available() and ext in myst_extensions() and matches_mystnb(text, ext, requires_meta=False):
        return MYST_FORMAT_NAME, {}

    lines = text.splitlines()

    # Is this a Hydrogen-like script?
    # Or a Sphinx-gallery script?
    if ext in _SCRIPT_EXTENSIONS:
        unescaped_comment = _SCRIPT_EXTENSIONS[ext]["comment"]
        comment = re.escape(unescaped_comment)
        language = _SCRIPT_EXTENSIONS[ext]["language"]
        twenty_hash_re = re.compile(r"^#( |)#{19,}\s*$")
        double_percent_re = re.compile(rf"^{comment}( %%|%%)$")
        double_percent_and_space_re = re.compile(rf"^{comment}( %%|%%)\s")
        nbconvert_script_re = re.compile(rf"^{comment}( <codecell>| In\[[0-9 ]*\]:?)")
        vim_folding_markers_re = re.compile(rf"^{comment}\s*" + "{{{")
        vscode_folding_markers_re = re.compile(rf"^{comment}\s*region")
        marimo_cell_re = re.compile(r"^@app.cell.*")

        twenty_hash_count = 0
        double_percent_count = 0
        magic_command_count = 0
        rspin_comment_count = 0
        vim_folding_markers_count = 0
        vscode_folding_markers_count = 0
        marimo_app_count = 0

        parser = StringParser(language="R" if ext in [".r", ".R"] else "python")
        for line in lines:
            parser.read_line(line)
            if parser.is_quoted():
                continue

            # Don't count escaped Jupyter magics (no space between %% and command) as cells
            if double_percent_re.match(line) or double_percent_and_space_re.match(line) or nbconvert_script_re.match(line):
                double_percent_count += 1

            if not line.startswith(unescaped_comment) and is_magic(line, language):
                magic_command_count += 1

            if twenty_hash_re.match(line) and ext == ".py":
                twenty_hash_count += 1

            if line.startswith("#'") and ext in [".R", ".r"]:
                rspin_comment_count += 1

            if vim_folding_markers_re.match(line):
                vim_folding_markers_count += 1

            if vscode_folding_markers_re.match(line):
                vscode_folding_markers_count += 1

            if ext == ".py" and (line in {"import marimo", "app = marimo.App()"} or marimo_cell_re.match(line)):
                marimo_app_count += 1

        if double_percent_count >= 1:
            if magic_command_count:
                return "hydrogen", {}
            return "percent", {}

        if marimo_app_count >= 2:
            return "marimo", {}

        if vim_folding_markers_count:
            return "light", {"cell_markers": "{{{,}}}"}

        if vscode_folding_markers_count:
            return "light", {"cell_markers": "region,endregion"}

        if twenty_hash_count >= 2:
            return "sphinx", {}

        if rspin_comment_count >= 1:
            return "spin", {}

    if ext in [".md", ".markdown"]:
        for line in lines:
            if line.startswith(":::"):  # Pandoc div
                return "pandoc", {}

    # Default format
    return get_format_implementation(ext).format_name, {}


def divine_format(text):
    """Guess the format of the notebook, based on its content #148"""
    try:
        nbformat.reads(text, as_version=4)
        return "ipynb"
    except (AttributeError, nbformat.reader.NotJSONError):
        pass

    lines = text.splitlines()
    for comment in ["", "#"] + _COMMENT_CHARS:
        metadata, _, _, _ = header_to_metadata_and_cell(lines, comment, "")
        ext = metadata.get("jupytext", {}).get("text_representation", {}).get("extension")
        if ext:
            return ext[1:] + ":" + guess_format(text, ext)[0]

    # No metadata, but ``` on at least one line => markdown
    for line in lines:
        if line == "```":
            return "md"

    return "py:" + guess_format(text, ".py")[0]


def check_file_version(notebook, source_path, outputs_path):
    """Raise if file version in source file would override outputs"""
    if not insert_or_test_version_number():
        return

    if source_path == "-":
        # https://github.com/mwouts/jupytext/issues/1282
        ext = notebook.metadata["jupytext"]["text_representation"]["extension"]
    else:
        _, ext = os.path.splitext(source_path)
        assert not ext.endswith(".ipynb"), f"source_path={source_path} should be a text file"

    version = notebook.metadata.get("jupytext", {}).get("text_representation", {}).get("format_version")
    format_name = format_name_for_ext(notebook.metadata, ext)

    fmt = get_format_implementation(ext, format_name)
    current = fmt.current_version_number

    # Missing version, still generated by jupytext?
    if notebook.metadata and not version:
        version = current

    # Same version? OK
    if version == fmt.current_version_number:
        return

    # Version larger than minimum readable version
    if (fmt.min_readable_version_number or current) <= version <= current:
        return

    jupytext_version_in_file = (
        notebook.metadata.get("jupytext", {}).get("text_representation", {}).get("jupytext_version", "N/A")
    )

    raise JupytextFormatError(
        "The file {source_path} was generated with jupytext version {jupytext_version_in_file} "
        "but you have {jupytext_version} installed. Please upgrade jupytext to version "
        "{jupytext_version_in_file}, or remove either {source_path} or {output_path}. "
        "This error occurs because {source_path} is in the {format_name} format in version {format_version}, "
        "while jupytext version {jupytext_version} installed at {jupytext_path} can only read the "
        "{format_name} format in versions {min_format_version} to {current_format_version}.".format(
            source_path=os.path.basename(source_path),
            output_path=os.path.basename(outputs_path),
            format_name=format_name,
            format_version=version,
            jupytext_version_in_file=jupytext_version_in_file,
            jupytext_version=__version__,
            jupytext_path=os.path.dirname(os.path.dirname(__file__)),
            min_format_version=fmt.min_readable_version_number or current,
            current_format_version=current,
        )
    )


def format_name_for_ext(metadata, ext, cm_default_formats=None, explicit_default=True):
    """Return the format name for that extension"""
    # Is the format information available in the text representation?
    text_repr = metadata.get("jupytext", {}).get("text_representation", {})
    if text_repr.get("extension", "").endswith(ext) and text_repr.get("format_name"):
        return text_repr.get("format_name")

    # Format from jupytext.formats
    formats = metadata.get("jupytext", {}).get("formats", "") or cm_default_formats
    formats = long_form_multiple_formats(formats)
    for fmt in formats:
        if fmt["extension"] == ext:
            if (not explicit_default) or fmt.get("format_name"):
                return fmt.get("format_name")

    if (not explicit_default) or ext in [".md", ".markdown", ".Rmd"]:
        return None

    return get_format_implementation(ext).format_name


def identical_format_path(fmt1, fmt2):
    """Do the two (long representation) of formats target the same file?"""
    for key in ["extension", "prefix", "suffix"]:
        if fmt1.get(key) != fmt2.get(key):
            return False
    return True


def update_jupytext_formats_metadata(metadata, new_format):
    """Update the jupytext_format metadata in the Jupyter notebook"""
    new_format = long_form_one_format(new_format)
    formats = long_form_multiple_formats(metadata.get("jupytext", {}).get("formats", ""))
    if not formats:
        return

    for fmt in formats:
        if identical_format_path(fmt, new_format):
            fmt["format_name"] = new_format.get("format_name")
            break

    metadata.setdefault("jupytext", {})["formats"] = short_form_multiple_formats(formats)


def rearrange_jupytext_metadata(metadata):
    """Convert the jupytext_formats metadata entry to jupytext/formats, etc. See #91"""

    # Backward compatibility with nbrmd
    for key in ["nbrmd_formats", "nbrmd_format_version"]:
        if key in metadata:
            metadata[key.replace("nbrmd", "jupytext")] = metadata.pop(key)

    jupytext_metadata = metadata.get("jupytext", {})

    if "jupytext_formats" in metadata:
        jupytext_metadata["formats"] = metadata.pop("jupytext_formats")
    if "jupytext_format_version" in metadata:
        jupytext_metadata["text_representation"] = {"format_version": metadata.pop("jupytext_format_version")}
    if "main_language" in metadata:
        jupytext_metadata["main_language"] = metadata.pop("main_language")
    for entry in ["encoding", "executable"]:
        if entry in metadata:
            jupytext_metadata[entry] = metadata.pop(entry)

    filters = jupytext_metadata.pop("metadata_filter", {})
    if "notebook" in filters:
        jupytext_metadata["notebook_metadata_filter"] = filters["notebook"]
    if "cells" in filters:
        jupytext_metadata["cell_metadata_filter"] = filters["cells"]

    for filter_level in ["notebook_metadata_filter", "cell_metadata_filter"]:
        if filter_level in jupytext_metadata:
            jupytext_metadata[filter_level] = metadata_filter_as_string(jupytext_metadata[filter_level])

    if jupytext_metadata.get("text_representation", {}).get("jupytext_version", "").startswith("0."):
        formats = jupytext_metadata.get("formats")
        if formats:
            jupytext_metadata["formats"] = ",".join(["." + fmt if fmt.rfind(".") > 0 else fmt for fmt in formats.split(",")])

    # auto to actual extension
    formats = jupytext_metadata.get("formats")
    if formats:
        jupytext_metadata["formats"] = short_form_multiple_formats(long_form_multiple_formats(formats, metadata))

    if jupytext_metadata:
        metadata["jupytext"] = jupytext_metadata


def long_form_one_format(jupytext_format, metadata=None, update=None, auto_ext_requires_language_info=True):
    """Parse 'sfx.py:percent' into {'suffix':'sfx', 'extension':'py', 'format_name':'percent'}"""
    if isinstance(jupytext_format, dict):
        if update:
            jupytext_format.update(update)
        return validate_one_format(jupytext_format)

    if not jupytext_format:
        return {}

    common_name_to_ext = {
        "notebook": "ipynb",
        "rmarkdown": "Rmd",
        "quarto": "qmd",
        "marimo": "py",
        "markdown": "md",
        "script": "auto",
        "c++": "cpp",
        "myst": "md:myst",
        "pandoc": "md:pandoc",
    }
    if jupytext_format.lower() in common_name_to_ext:
        jupytext_format = common_name_to_ext[jupytext_format.lower()]

    fmt = {}

    if jupytext_format.rfind("/") > 0:
        fmt["prefix"], jupytext_format = jupytext_format.rsplit("/", 1)

    if jupytext_format.rfind(":") >= 0:
        ext, fmt["format_name"] = jupytext_format.rsplit(":", 1)
        if fmt["format_name"] == "bare":
            warnings.warn(
                "The `bare` format has been renamed to `nomarker` - (see https://github.com/mwouts/jupytext/issues/397)",
                DeprecationWarning,
            )
            fmt["format_name"] = "nomarker"
    elif not jupytext_format or "." in jupytext_format or ("." + jupytext_format) in NOTEBOOK_EXTENSIONS + [".auto"]:
        ext = jupytext_format
    elif jupytext_format in _VALID_FORMAT_NAMES:
        fmt["format_name"] = jupytext_format
        ext = ""
    else:
        raise JupytextFormatError(
            "'{}' is not a notebook extension (one of {}), nor a notebook format (one of {})".format(
                jupytext_format,
                ", ".join(NOTEBOOK_EXTENSIONS),
                ", ".join(_VALID_FORMAT_NAMES),
            )
        )

    if ext.rfind(".") > 0:
        fmt["suffix"], ext = os.path.splitext(ext)

    if not ext.startswith("."):
        ext = "." + ext

    if ext == ".auto":
        ext = auto_ext_from_metadata(metadata) if metadata is not None else ".auto"
        if not ext:
            if auto_ext_requires_language_info:
                raise JupytextFormatError(
                    "No language information in this notebook. Please replace 'auto' with an actual script extension."
                )
            ext = ".auto"

    fmt["extension"] = ext
    if update:
        fmt.update(update)
    return validate_one_format(fmt)


def long_form_multiple_formats(
    jupytext_formats: str, metadata=None, auto_ext_requires_language_info=True
) -> list[dict[str, str]]:
    """Convert a concise encoding of jupytext.formats to a list of formats, encoded as dictionaries"""
    if not jupytext_formats:
        return []

    if not isinstance(jupytext_formats, list):
        jupytext_formats = [fmt for fmt in jupytext_formats.split(",") if fmt]

    jupytext_formats = [
        long_form_one_format(
            fmt,
            metadata,
            auto_ext_requires_language_info=auto_ext_requires_language_info,
        )
        for fmt in jupytext_formats
    ]

    if not auto_ext_requires_language_info:
        jupytext_formats = [fmt for fmt in jupytext_formats if fmt["extension"] != ".auto"]

    return jupytext_formats


def short_form_one_format(jupytext_format: dict[str, str]) -> str:
    """Represent one jupytext format as a string"""
    if not isinstance(jupytext_format, dict):
        return jupytext_format
    fmt = jupytext_format["extension"]
    if "suffix" in jupytext_format:
        fmt = jupytext_format["suffix"] + fmt
    elif fmt.startswith("."):
        fmt = fmt[1:]

    if "prefix" in jupytext_format:
        fmt = jupytext_format["prefix"] + "/" + fmt

    if jupytext_format.get("format_name"):
        if jupytext_format["extension"] not in [
            ".md",
            ".markdown",
            ".Rmd",
        ] or jupytext_format["format_name"] in ["pandoc", MYST_FORMAT_NAME]:
            fmt = fmt + ":" + jupytext_format["format_name"]

    return fmt


def short_form_multiple_formats(jupytext_formats: list[dict[str, str]]) -> str:
    """Convert jupytext formats, represented as a list of dictionaries, to a comma separated list"""
    if not isinstance(jupytext_formats, list):
        return jupytext_formats

    jupytext_formats = [short_form_one_format(fmt) for fmt in jupytext_formats]
    return ",".join(jupytext_formats)


_VALID_FORMAT_INFO = ["extension", "format_name", "suffix", "prefix"]
_BINARY_FORMAT_OPTIONS = [
    "comment_magics",
    "hide_notebook_metadata",
    "root_level_metadata_as_raw_cell",
    "split_at_heading",
    "rst2md",
    "cell_metadata_json",
    "use_runtools",
    "doxygen_equation_markers",
]
_VALID_FORMAT_OPTIONS = _BINARY_FORMAT_OPTIONS + [
    "notebook_metadata_filter",
    "root_level_metadata_filter",
    "cell_metadata_filter",
    "cell_markers",
    "custom_cell_magics",
    "custom_language_magics",
]
_VALID_FORMAT_NAMES = {fmt.format_name for fmt in JUPYTEXT_FORMATS}


def validate_one_format(jupytext_format: dict[str, str]) -> dict[str, str]:
    """Validate extension and options for the given format"""
    if not isinstance(jupytext_format, dict):
        raise JupytextFormatError("Jupytext format should be a dictionary")

    if "format_name" in jupytext_format and jupytext_format["format_name"] not in _VALID_FORMAT_NAMES:
        raise JupytextFormatError(
            "{} is not a valid format name. Please choose one of {}".format(
                jupytext_format.get("format_name"), ", ".join(_VALID_FORMAT_NAMES)
            )
        )

    for key in jupytext_format:
        if key not in _VALID_FORMAT_INFO + _VALID_FORMAT_OPTIONS:
            raise JupytextFormatError(
                "Unknown format option '{}' - should be one of '{}'".format(key, "', '".join(_VALID_FORMAT_OPTIONS))
            )
        value = jupytext_format[key]
        if key in _BINARY_FORMAT_OPTIONS:
            if not isinstance(value, bool):
                raise JupytextFormatError(f"Format option '{key}' should be a bool, not '{str(value)}'")

    if "extension" not in jupytext_format:
        raise JupytextFormatError("Missing format extension")
    ext = jupytext_format["extension"]
    if ext not in NOTEBOOK_EXTENSIONS + [".auto"]:
        raise JupytextFormatError(
            "Extension '{}' is not a notebook extension. Please use one of '{}'.".format(
                ext, "', '".join(NOTEBOOK_EXTENSIONS + [".auto"])
            )
        )

    return jupytext_format


def auto_ext_from_metadata(metadata):
    """Script extension from notebook metadata"""
    auto_ext = metadata.get("language_info", {}).get("file_extension")

    # Sage notebooks have ".py" as the associated extension in "language_info",
    # so we change it to ".sage" in that case, see #727
    if auto_ext == ".py" and metadata.get("kernelspec", {}).get("language") == "sage":
        auto_ext = ".sage"

    if auto_ext is None:
        language = metadata.get("kernelspec", {}).get("language") or metadata.get("jupytext", {}).get("main_language")
        if language:
            for ext in _SCRIPT_EXTENSIONS:
                if same_language(language, _SCRIPT_EXTENSIONS[ext]["language"]):
                    auto_ext = ext
                    break

    if auto_ext == ".r":
        return ".R"

    if auto_ext == ".fs":
        return ".fsx"

    if auto_ext == ".resource":
        return ".robot"

    # Handle ROOT C++ notebooks
    # https://tinyurl.com/root-cpp-notebook-doc
    if auto_ext == ".C":
        return ".cpp"

    return auto_ext


def check_auto_ext(fmt, metadata, option):
    """Replace the auto extension with the actual file extension, and raise a ValueError if it cannot be determined"""
    if fmt["extension"] != ".auto":
        return fmt

    auto_ext = auto_ext_from_metadata(metadata)
    if auto_ext:
        fmt = fmt.copy()
        fmt["extension"] = auto_ext
        return fmt

    raise ValueError(
        "The notebook does not have a 'language_info' metadata. "
        "Please replace 'auto' with the actual language extension in the {} option (currently {}).".format(
            option, short_form_one_format(fmt)
        )
    )


def formats_with_support_for_cell_metadata():
    for fmt in JUPYTEXT_FORMATS:
        if fmt.format_name == "myst" and not is_myst_available():
            continue
        if fmt.format_name == "pandoc" and not is_pandoc_available():
            continue
        if fmt.format_name in FORMATS_WITH_NO_CELL_METADATA:
            continue

        yield f"{fmt.extension[1:]}:{fmt.format_name}"


def get_formats_from_notebook_metadata(notebook):
    """
    Get the pairing information from the notebook metadata.

    Parameters
    ----------
    notebook : nbformat.NotebookNode
        The notebook object whose metadata will be inspected.

    Returns
    -------
    formats : None or str
        The value of the 'formats' field in the 'jupytext' metadata, which can be None or a string.
    """
    return notebook.metadata.get("jupytext", {}).get("formats")
