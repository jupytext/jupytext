"""Export notebook cells as text"""

import re
import warnings
from copy import copy

from .cell_metadata import (
    _IGNORE_CELL_METADATA,
    is_active,
    metadata_to_double_percent_options,
    metadata_to_rmd_options,
    metadata_to_text,
)
from .cell_reader import LightScriptCellReader, MarkdownCellReader, RMarkdownCellReader
from .doxygen import markdown_to_doxygen
from .languages import _SCRIPT_EXTENSIONS, cell_language, comment_lines, same_language, _NEED_TRAILING_WHITESPACE_LANGUAGES
from .magics import comment_magic, escape_code_start, need_explicit_marker
from .metadata_filter import filter_metadata
from .pep8 import pep8_lines_between_cells


def cell_source(cell):
    """Return the source of the current cell, as an array of lines"""
    source = cell.source
    if source == "":
        return [""]
    if source.endswith("\n"):
        return source.splitlines() + [""]
    return source.splitlines()


def three_backticks_or_more(lines):
    """Return a string with enough backticks to encapsulate the given code cell in Markdown
    cf. https://github.com/mwouts/jupytext/issues/712"""
    code_cell_delimiter = "```"
    for line in lines:
        if not line.startswith(code_cell_delimiter):
            continue
        for char in line[len(code_cell_delimiter) :]:
            if char != "`":
                break
            code_cell_delimiter += "`"
        code_cell_delimiter += "`"

    return code_cell_delimiter


class BaseCellExporter:
    """A class that represent a notebook cell as text"""

    default_comment_magics = None
    parse_cell_language = True

    def __init__(self, cell, default_language, fmt=None, unsupported_keys=None):
        self.fmt = fmt or {}
        self.ext = self.fmt.get("extension")
        self.cell_type = cell.cell_type
        self.source = cell_source(cell)
        self.unfiltered_metadata = cell.metadata
        self.metadata = filter_metadata(
            cell.metadata,
            self.fmt.get("cell_metadata_filter"),
            _IGNORE_CELL_METADATA,
            unsupported_keys=unsupported_keys,
        )
        if self.parse_cell_language:
            custom_cell_magics = self.fmt.get("custom_cell_magics", "").split(",")
            custom_language_magics = self.fmt.get("custom_language_magics", "").split(",")
            self.language, magic_args = cell_language(
                self.source, default_language, custom_cell_magics + custom_language_magics
            )

            if magic_args:
                self.metadata["magic_args"] = magic_args
        else:
            self.language = None

        if self.language and not self.ext.endswith(".Rmd"):
            self.metadata["language"] = self.language

        self.language = self.language or cell.metadata.get("language", default_language)
        self.default_language = default_language
        self.comment = _SCRIPT_EXTENSIONS.get(self.ext, {}).get("comment", "#")
        self.comment_suffix = _SCRIPT_EXTENSIONS.get(self.ext, {}).get("comment_suffix", "")
        self.empty_line_whitespace = " " if self.language in _NEED_TRAILING_WHITESPACE_LANGUAGES else ""
        self.comment_magics = self.fmt.get("comment_magics", self.default_comment_magics)
        self.cell_metadata_json = self.fmt.get("cell_metadata_json", False)
        self.use_runtools = self.fmt.get("use_runtools", False)
        self.doxygen_equation_markers = self.fmt.get("doxygen_equation_markers", False)

        # how many blank lines before next cell
        self.lines_to_next_cell = cell.metadata.get("lines_to_next_cell")
        self.lines_to_end_of_cell_marker = cell.metadata.get("lines_to_end_of_cell_marker")

        if (
            cell.cell_type == "raw"
            and "active" not in self.metadata
            and not any(tag.startswith("active-") for tag in self.metadata.get("tags", []))
        ):
            self.metadata["active"] = ""

    def is_code(self):
        """Is this cell a code cell?"""
        if self.cell_type == "code":
            return True
        if (
            self.cell_type == "raw"
            and "active" in self.metadata
            or any(tag.startswith("active-") for tag in self.metadata.get("tags", []))
        ):
            return True
        return False

    def use_triple_quotes(self):
        """Should this markdown cell use triple quote?"""
        if "cell_marker" not in self.unfiltered_metadata:
            return False
        cell_marker = self.unfiltered_metadata["cell_marker"]
        if cell_marker in ['"""', "'''"]:
            return True
        if "," not in cell_marker:
            return False
        left, right = cell_marker.split(",")
        return left[:3] == right[-3:] and left[:3] in ['"""', "'''"]

    def cell_to_text(self):
        """Return the text representation for the cell"""
        # Trigger cell marker in case we are using multiline quotes
        if self.cell_type != "code" and not self.metadata and self.use_triple_quotes():
            self.metadata["cell_type"] = self.cell_type

        # Go notebooks have '%%' or '%% -' magic commands that need to be escaped
        if self.default_language == "go" and self.language == "go":
            self.source = [re.sub(r"^(//\s*)*(%%\s*$|%%\s+-.*$)", r"\1//gonb:\2", line) for line in self.source]

        if self.is_code():
            return self.code_to_text()

        source = copy(self.source)
        if not self.comment:
            escape_code_start(source, self.ext, None)
        return self.markdown_to_text(source)

    def markdown_to_text(self, source):
        """Escape the given source, for a markdown cell"""
        cell_markers = self.unfiltered_metadata.get("cell_marker", self.fmt.get("cell_markers"))
        if cell_markers:
            if "," in cell_markers:
                left, right = cell_markers.split(",", 1)
            else:
                left = cell_markers + "\n"
                if cell_markers.startswith(("r", "R")):
                    cell_markers = cell_markers[1:]
                right = "\n" + cell_markers

            if (left[:3] == right[-3:] or (left[:1] in ["r", "R"] and left[1:4] == right[-3:])) and right[-3:] in [
                '"""',
                "'''",
            ]:
                # Markdown cells that contain a backslash should be encoded as raw strings
                if left[:1] not in ["r", "R"] and "\\" in "\n".join(source) and self.fmt.get("format_name") == "percent":
                    left = "r" + left

                source = copy(source)
                source[0] = left + source[0]
                source[-1] = source[-1] + right
                return source

        if (
            self.comment
            and self.comment != "#'"
            and is_active(self.ext, self.metadata)
            and self.fmt.get("format_name") not in ["percent", "hydrogen"]
        ):
            source = copy(source)
            comment_magic(
                source,
                self.language,
                self.comment_magics,
                explicitly_code=self.cell_type == "code",
            )

        return comment_lines(source, self.comment, self.comment_suffix, self.empty_line_whitespace)

    def code_to_text(self):
        """Return the text representation of this cell as a code cell"""
        raise NotImplementedError("This method must be implemented in a sub-class")

    def remove_eoc_marker(self, text, next_text):
        """Remove end-of-cell marker when possible"""
        # pylint: disable=W0613,R0201
        return text


class MarkdownCellExporter(BaseCellExporter):
    """A class that represent a notebook cell as Markdown"""

    default_comment_magics = False
    cell_reader = MarkdownCellReader

    def __init__(self, *args, **kwargs):
        BaseCellExporter.__init__(self, *args, **kwargs)
        self.comment = ""

    def html_comment(self, metadata, code="region"):
        """Protect a Markdown or Raw cell with HTML comments"""
        if metadata:
            region_start = [
                "<!-- #" + code,
                metadata_to_text(metadata, plain_json=self.cell_metadata_json),
                "-->",
            ]
            region_start = " ".join(region_start)
        else:
            region_start = f"<!-- #{code} -->"

        return [region_start] + self.source + [f"<!-- #end{code} -->"]

    def cell_to_text(self):
        """Return the text representation of a cell"""
        if self.cell_type == "markdown":
            if self.doxygen_equation_markers and self.cell_type == "markdown":
                self.source = markdown_to_doxygen("\n".join(self.source)).splitlines()

            # Is an explicit region required?
            if self.metadata:
                protect = True
            else:
                # Would the text be parsed to a shorter cell/a cell with a different type?
                cell, pos = self.cell_reader(self.fmt).read(self.source)
                protect = pos < len(self.source) or cell.cell_type != self.cell_type
            if protect:
                return self.html_comment(self.metadata, self.metadata.pop("region_name", "region"))
            return self.source

        return self.code_to_text()

    def code_to_text(self):
        """Return the text representation of a code cell"""
        source = copy(self.source)
        comment_magic(source, self.language, self.comment_magics)

        if self.metadata.get("active") == "":
            self.metadata.pop("active")

        self.language = self.metadata.pop("language", self.language)
        if self.cell_type == "raw" and not is_active(self.ext, self.metadata, False):
            return self.html_comment(self.metadata, "raw")

        options = metadata_to_text(self.language, self.metadata)
        code_cell_delimiter = three_backticks_or_more(self.source)
        return [code_cell_delimiter + options] + source + [code_cell_delimiter]


class RMarkdownCellExporter(MarkdownCellExporter):
    """A class that represent a notebook cell as R Markdown"""

    default_comment_magics = True
    cell_reader = RMarkdownCellReader

    def __init__(self, *args, **kwargs):
        MarkdownCellExporter.__init__(self, *args, **kwargs)
        self.ext = ".Rmd"
        self.comment = ""

    def code_to_text(self):
        """Return the text representation of a code cell"""
        active = is_active(self.ext, self.metadata)
        source = copy(self.source)

        if active:
            comment_magic(source, self.language, self.comment_magics)

        lines = []
        if not is_active(self.ext, self.metadata):
            self.metadata["eval"] = False
        options = metadata_to_rmd_options(self.language, self.metadata, self.use_runtools)
        lines.append(f"```{{{options}}}")
        lines.extend(source)
        lines.append("```")
        return lines


def endofcell_marker(source, comment):
    """Issues #31 #38:  does the cell contain a blank line? In that case
    we add an end-of-cell marker"""
    endofcell = "-"
    while True:
        endofcell_re = re.compile(rf"^{re.escape(comment)}( )" + endofcell + r"\s*$")
        if list(filter(endofcell_re.match, source)):
            endofcell = endofcell + "-"
        else:
            return endofcell


class LightScriptCellExporter(BaseCellExporter):
    """A class that represent a notebook cell as a Python or Julia script"""

    default_comment_magics = True
    use_cell_markers = True
    cell_marker_start = None
    cell_marker_end = None

    def __init__(self, *args, **kwargs):
        BaseCellExporter.__init__(self, *args, **kwargs)
        if "cell_markers" in self.fmt:
            if "," not in self.fmt["cell_markers"]:
                warnings.warn(
                    "Ignored cell markers '{}' as it does not match the expected 'start,end' pattern".format(
                        self.fmt.pop("cell_markers")
                    )
                )
            elif self.fmt["cell_markers"] != "+,-":
                self.cell_marker_start, self.cell_marker_end = self.fmt["cell_markers"].split(",", 1)
        for key in ["endofcell"]:
            if key in self.unfiltered_metadata:
                self.metadata[key] = self.unfiltered_metadata[key]

    def is_code(self):
        # Treat markdown cells with metadata as code cells (#66)
        if (self.cell_type == "markdown" and self.metadata) or self.use_triple_quotes():
            if is_active(self.ext, self.metadata):
                self.metadata["cell_type"] = self.cell_type
                self.source = self.markdown_to_text(self.source)
                self.cell_type = "code"
                self.unfiltered_metadata = copy(self.unfiltered_metadata)
                self.unfiltered_metadata.pop("cell_marker", "")
            return True
        return super().is_code()

    def code_to_text(self):
        """Return the text representation of a code cell"""
        active = is_active(self.ext, self.metadata, same_language(self.language, self.default_language))
        source = copy(self.source)
        escape_code_start(source, self.ext, self.language)
        comment_questions = self.metadata.pop("comment_questions", True)

        if active:
            comment_magic(source, self.language, self.comment_magics, comment_questions)
        else:
            source = self.markdown_to_text(source)

        if (
            active and comment_questions and need_explicit_marker(self.source, self.language, self.comment_magics)
        ) or self.explicit_start_marker(source):
            self.metadata["endofcell"] = self.cell_marker_end or endofcell_marker(source, self.comment)

        if not self.metadata or not self.use_cell_markers:
            return source

        lines = []
        endofcell = self.metadata["endofcell"]
        if endofcell == "-" or self.cell_marker_end:
            del self.metadata["endofcell"]

        cell_start = [self.comment, self.cell_marker_start or "+"]
        options = metadata_to_double_percent_options(self.metadata, self.cell_metadata_json)
        if options:
            cell_start.append(options)
        lines.append(" ".join(cell_start))
        lines.extend(source)
        lines.append(self.comment + f" {endofcell}")
        return lines

    def explicit_start_marker(self, source):
        """Does the python representation of this cell requires an explicit
        start of cell marker?"""
        if not self.use_cell_markers:
            return False
        if self.metadata:
            return True
        if self.cell_marker_start:
            start_code_re = re.compile("^" + self.comment + r"\s*" + self.cell_marker_start + r"\s*(.*)$")
            end_code_re = re.compile("^" + self.comment + r"\s*" + self.cell_marker_end + r"\s*$")
            if start_code_re.match(source[0]) or end_code_re.match(source[0]):
                return False

        if all([line.startswith(self.comment) for line in self.source]):
            return True
        if LightScriptCellReader(self.fmt).read(source)[1] < len(source):
            return True

        return False

    def remove_eoc_marker(self, text, next_text):
        """Remove end of cell marker when next cell has an explicit start marker"""
        if self.cell_marker_start:
            return text

        if self.is_code() and text[-1] == self.comment + " -":
            # remove end of cell marker when redundant with next explicit marker
            if not next_text or next_text[0].startswith(self.comment + " +"):
                text = text[:-1]
                # When we do not need the end of cell marker, number of blank lines is the max
                # between that required at the end of the cell, and that required before the next cell.
                if self.lines_to_end_of_cell_marker and (
                    self.lines_to_next_cell is None or self.lines_to_end_of_cell_marker > self.lines_to_next_cell
                ):
                    self.lines_to_next_cell = self.lines_to_end_of_cell_marker
            else:
                # Insert blank lines at the end of the cell
                blank_lines = self.lines_to_end_of_cell_marker
                if blank_lines is None:
                    # two blank lines when required by pep8
                    blank_lines = pep8_lines_between_cells(text[:-1], next_text, self.ext)
                    blank_lines = 0 if blank_lines < 2 else 2
                text = text[:-1] + [""] * blank_lines + text[-1:]

        return text


class BareScriptCellExporter(LightScriptCellExporter):
    """A class that writes notebook cells as scripts with no cell markers"""

    use_cell_markers = False


class RScriptCellExporter(BaseCellExporter):
    """A class that can represent a notebook cell as a R script"""

    default_comment_magics = True

    def __init__(self, *args, **kwargs):
        BaseCellExporter.__init__(self, *args, **kwargs)
        self.comment = "#'"

    def code_to_text(self):
        """Return the text representation of a code cell"""
        active = is_active(self.ext, self.metadata)
        source = copy(self.source)
        escape_code_start(source, self.ext, self.language)

        if active:
            comment_magic(source, self.language, self.comment_magics)

        if not active:
            source = ["# " + line if line else "#" for line in source]

        lines = []
        if not is_active(self.ext, self.metadata):
            self.metadata["eval"] = False
        options = metadata_to_rmd_options(None, self.metadata, self.use_runtools)
        if options:
            lines.append(f"#+ {options}")
        lines.extend(source)
        return lines


class DoublePercentCellExporter(BaseCellExporter):  # pylint: disable=W0223
    """A class that can represent a notebook cell as a Spyder/VScode script (#59)"""

    default_comment_magics = True
    parse_cell_language = True

    def __init__(self, *args, **kwargs):
        BaseCellExporter.__init__(self, *args, **kwargs)
        self.cell_markers = self.fmt.get("cell_markers")

    def cell_to_text(self):
        """Return the text representation for the cell"""
        # Go notebooks have '%%' or '%% -' magic commands that need to be escaped
        if self.default_language == "go" and self.language == "go":
            self.source = [re.sub(r"^(//\s*)*(%%\s*$|%%\s+-.*$)", r"\1//gonb:\2", line) for line in self.source]

        active = is_active(self.ext, self.metadata, same_language(self.language, self.default_language))
        if self.cell_type == "raw" and "active" in self.metadata and self.metadata["active"] == "":
            del self.metadata["active"]

        if not self.is_code():
            self.metadata["cell_type"] = self.cell_type

        options = metadata_to_double_percent_options(self.metadata, self.cell_metadata_json)
        indent = ""
        if self.is_code() and active and self.source:
            first_line = self.source[0]
            if first_line.strip():
                left_space = re.compile(r"^(\s*)").match(first_line)
                if left_space:
                    indent = left_space.groups()[0]

        if options.startswith("%") or not options:
            lines = comment_lines(["%%" + options], indent + self.comment, self.comment_suffix, self.empty_line_whitespace)
        else:
            lines = comment_lines(["%% " + options], indent + self.comment, self.comment_suffix, self.empty_line_whitespace)

        if self.is_code() and active:
            source = copy(self.source)
            comment_magic(source, self.language, self.comment_magics)
            if source == [""]:
                return lines
            return lines + source

        return lines + self.markdown_to_text(self.source)


class HydrogenCellExporter(DoublePercentCellExporter):  # pylint: disable=W0223
    """A class that can represent a notebook cell as a Hydrogen script (#59)"""

    default_comment_magics = False
    parse_cell_language = False


class SphinxGalleryCellExporter(BaseCellExporter):  # pylint: disable=W0223
    """A class that can represent a notebook cell as a
    Sphinx Gallery script (#80)"""

    default_cell_marker = "#" * 79
    default_comment_magics = True

    def __init__(self, *args, **kwargs):
        BaseCellExporter.__init__(self, *args, **kwargs)
        self.comment = "#"

        for key in ["cell_marker"]:
            if key in self.unfiltered_metadata:
                self.metadata[key] = self.unfiltered_metadata[key]

        if self.fmt.get("rst2md"):
            raise ValueError(
                "The 'rst2md' option is a read only option. The reverse conversion is not "
                "implemented. Please either deactivate the option, or save to another format."
            )  # pragma: no cover

    def cell_to_text(self):
        """Return the text representation for the cell"""
        if self.cell_type == "code":
            source = copy(self.source)
            return comment_magic(source, self.language, self.comment_magics)

        if "cell_marker" in self.metadata:
            cell_marker = self.metadata.pop("cell_marker")
        else:
            cell_marker = self.default_cell_marker

        if self.source == [""]:
            return [cell_marker] if cell_marker in ['""', "''"] else ['""']

        if cell_marker in ['"""', "'''"]:
            return [cell_marker] + self.source + [cell_marker]

        return [(cell_marker if cell_marker.startswith("#" * 20) else self.default_cell_marker)] + comment_lines(
            self.source, self.comment, self.comment_suffix, self.empty_line_whitespace
        )
