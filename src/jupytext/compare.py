"""Compare two Jupyter notebooks"""

import difflib
import json
import os
import re

from jupytext.marimo import marimo_version
from jupytext.paired_paths import full_path

from .cell_metadata import _IGNORE_CELL_METADATA
from .combine import combine_inputs_with_outputs
from .formats import check_auto_ext, long_form_one_format
from .header import _DEFAULT_NOTEBOOK_METADATA
from .jupytext import read, reads, write, writes
from .metadata_filter import filter_metadata

_BLANK_LINE = re.compile(r"^\s*$")


def _multilines(obj):
    try:
        lines = obj.splitlines()
        return lines + [""] if obj.endswith("\n") else lines
    except AttributeError:
        # Remove the final blank space on Python 2.7
        # return json.dumps(obj, indent=True, sort_keys=True).splitlines()
        return [line.rstrip() for line in json.dumps(obj, indent=True, sort_keys=True).splitlines()]


def compare(actual, expected, actual_name="actual", expected_name="expected", return_diff=False):
    """Compare two strings, lists or dict-like objects"""
    if actual != expected:
        diff = difflib.unified_diff(
            _multilines(expected),
            _multilines(actual),
            expected_name,
            actual_name,
            lineterm="",
        )
        if expected_name == "" and actual_name == "":
            diff = list(diff)[2:]
        diff = "\n".join(diff)
        if return_diff:
            return diff
        raise AssertionError("\n" + diff)
    return "" if return_diff else None


def filtered_cell(cell, preserve_outputs, cell_metadata_filter):
    """Cell type, metadata and source from given cell"""
    filtered = {
        "cell_type": cell.cell_type,
        "source": cell.source,
        "metadata": filter_metadata(cell.metadata, cell_metadata_filter, _IGNORE_CELL_METADATA),
    }

    if preserve_outputs:
        for key in ["execution_count", "outputs"]:
            if key in cell:
                filtered[key] = cell[key]

    return filtered


def filtered_notebook_metadata(notebook, ignore_kernelspec=False):
    """Notebook metadata, filtered for metadata added by Jupytext itself"""
    metadata = filter_metadata(
        notebook.metadata,
        notebook.metadata.get("jupytext", {}).get("notebook_metadata_filter"),
        _DEFAULT_NOTEBOOK_METADATA,
    )

    # Quarto round-trips may change the kernelspec
    if ignore_kernelspec:
        metadata.pop("kernelspec", None)

    if "jupytext" in metadata:
        del metadata["jupytext"]
    return metadata


class NotebookDifference(Exception):
    """Report notebook differences"""


def same_content(ref_source, test_source, allow_removed_final_blank_line):
    """Is the content of two cells the same, except for an optional final blank line?"""
    if ref_source == test_source:
        return True

    if not allow_removed_final_blank_line:
        return False

    # Is ref identical to test, plus one blank line?
    ref_source = ref_source.splitlines()
    test_source = test_source.splitlines()

    if not ref_source:
        return False

    if ref_source[:-1] != test_source:
        return False

    return _BLANK_LINE.match(ref_source[-1])


def compare_notebooks(
    notebook_actual,
    notebook_expected,
    fmt=None,
    allow_expected_differences=True,
    raise_on_first_difference=True,
    compare_outputs=False,
    compare_ids=None,
):
    """Compare the two notebooks, and raise with a meaningful message
    that explains the differences, if any"""
    fmt = long_form_one_format(fmt)
    format_name = fmt.get("format_name")

    if format_name == "sphinx" and notebook_actual.cells and notebook_actual.cells[0].source == "%matplotlib inline":
        notebook_actual.cells = notebook_actual.cells[1:]

    if compare_ids is None:
        compare_ids = compare_outputs

    modified_cells, modified_cell_metadata = compare_cells(
        notebook_actual.cells,
        notebook_expected.cells,
        raise_on_first_difference,
        compare_outputs=compare_outputs,
        compare_ids=compare_ids,
        cell_metadata_filter="-all"
        if format_name == "marimo"
        else notebook_actual.get("jupytext", {}).get("cell_metadata_filter"),
        allow_missing_code_cell_metadata=(allow_expected_differences and format_name in ["sphinx", "marimo"]),
        allow_missing_markdown_cell_metadata=(allow_expected_differences and format_name in ["sphinx", "spin", "marimo"]),
        allow_filtered_cell_metadata=allow_expected_differences,
        allow_removed_final_blank_line=allow_expected_differences,
    )

    # Compare notebook metadata
    modified_metadata = False
    if fmt.get("format_name") != "marimo":
        try:
            ignore_kernelspec = fmt.get("extension") == ".qmd" and allow_expected_differences
            compare(
                filtered_notebook_metadata(notebook_actual, ignore_kernelspec),
                filtered_notebook_metadata(notebook_expected, ignore_kernelspec),
            )
        except AssertionError as error:
            if raise_on_first_difference:
                raise NotebookDifference(f"Notebook metadata differ: {str(error)}")
            modified_metadata = True

    error = []
    if modified_cells:
        error.append(
            "Cells {} differ ({}/{})".format(
                ",".join([str(i) for i in modified_cells]),
                len(modified_cells),
                len(notebook_expected.cells),
            )
        )
    if modified_cell_metadata:
        error.append("Cell metadata '{}' differ".format("', '".join([str(i) for i in modified_cell_metadata])))
    if modified_metadata:
        error.append("Notebook metadata differ")

    if error:
        raise NotebookDifference(" | ".join(error))


def compare_cells(
    actual_cells,
    expected_cells,
    raise_on_first_difference=True,
    compare_outputs=True,
    compare_ids=True,
    cell_metadata_filter=None,
    allow_missing_code_cell_metadata=False,
    allow_missing_markdown_cell_metadata=False,
    allow_filtered_cell_metadata=False,
    allow_removed_final_blank_line=False,
):
    """Compare two collection of notebook cells"""
    test_cell_iter = iter(actual_cells)
    modified_cells = set()
    modified_cell_metadata = set()

    for i, ref_cell in enumerate(expected_cells, 1):
        try:
            test_cell = next(test_cell_iter)
        except StopIteration:
            if raise_on_first_difference:
                raise NotebookDifference(f"No cell corresponding to {ref_cell.cell_type} cell #{i}:\n{ref_cell.source}")
            modified_cells.update(range(i, len(expected_cells) + 1))
            break

        ref_lines = [line for line in ref_cell.source.splitlines() if not _BLANK_LINE.match(line)]
        test_lines = []

        # 1. test cell type
        if ref_cell.cell_type != test_cell.cell_type:
            if raise_on_first_difference:
                raise NotebookDifference(
                    f"When comparing cell #{i}: "
                    f"expecting a {ref_cell.cell_type} cell, but got a {test_cell.cell_type} cell.\n"
                    f"Expected content:\n{ref_cell.source}\nActual content:\n{test_cell.source}"
                )
            modified_cells.add(i)

        # Compare cell ids (introduced in nbformat 5.1.0)
        if compare_ids and test_cell.get("id") != ref_cell.get("id"):
            if raise_on_first_difference:
                raise NotebookDifference(
                    f"Cell ids differ on {test_cell['cell_type']} cell #{i}: '{test_cell.get('id')}' != '{ref_cell.get('id')}'"
                )
            modified_cells.add(i)

        # 2. test cell metadata
        if (ref_cell.cell_type == "code" and not allow_missing_code_cell_metadata) or (
            ref_cell.cell_type != "code" and not allow_missing_markdown_cell_metadata
        ):
            ref_metadata = ref_cell.metadata
            test_metadata = test_cell.metadata
            if allow_filtered_cell_metadata:
                ref_metadata = {key: ref_metadata[key] for key in ref_metadata if key not in _IGNORE_CELL_METADATA}
                test_metadata = {key: test_metadata[key] for key in test_metadata if key not in _IGNORE_CELL_METADATA}

            if ref_metadata != test_metadata:
                if raise_on_first_difference:
                    try:
                        compare(test_metadata, ref_metadata)
                    except AssertionError as error:
                        raise NotebookDifference(
                            "Metadata differ on {} cell #{}: {}\nCell content:\n{}".format(
                                test_cell.cell_type, i, str(error), ref_cell.source
                            )
                        )
                else:
                    modified_cell_metadata.update(set(test_metadata).difference(ref_metadata))
                    modified_cell_metadata.update(set(ref_metadata).difference(test_metadata))
                    for key in set(ref_metadata).intersection(test_metadata):
                        if ref_metadata[key] != test_metadata[key]:
                            modified_cell_metadata.add(key)

        test_lines.extend([line for line in test_cell.source.splitlines() if not _BLANK_LINE.match(line)])

        # 3. test cell content
        if ref_lines != test_lines:
            if raise_on_first_difference:
                try:
                    compare("\n".join(test_lines), "\n".join(ref_lines))
                except AssertionError as error:
                    raise NotebookDifference(f"Cell content differ on {test_cell.cell_type} cell #{i}: {str(error)}")
            else:
                modified_cells.add(i)

        # 3. bis test entire cell content
        if not same_content(ref_cell.source, test_cell.source, allow_removed_final_blank_line):
            if ref_cell.source != test_cell.source:
                if raise_on_first_difference:
                    diff = compare(test_cell.source, ref_cell.source, return_diff=True)
                    raise NotebookDifference(f"Cell content differ on {test_cell.cell_type} cell #{i}: {diff}")
                modified_cells.add(i)

        if not compare_outputs:
            continue

        if ref_cell.cell_type != "code":
            continue

        ref_cell = filtered_cell(
            ref_cell,
            preserve_outputs=compare_outputs,
            cell_metadata_filter=cell_metadata_filter,
        )
        test_cell = filtered_cell(
            test_cell,
            preserve_outputs=compare_outputs,
            cell_metadata_filter=cell_metadata_filter,
        )

        try:
            compare(test_cell, ref_cell)
        except AssertionError as error:
            if raise_on_first_difference:
                raise NotebookDifference(
                    "Cell outputs differ on {} cell #{}: {}".format(test_cell["cell_type"], i, str(error))
                )
            modified_cells.add(i)

    # More cells in the actual notebook?
    remaining_cell_count = 0
    while True:
        try:
            test_cell = next(test_cell_iter)
            if raise_on_first_difference:
                raise NotebookDifference(f"Additional {test_cell.cell_type} cell: {test_cell.source}")
            remaining_cell_count += 1
        except StopIteration:
            break

    if remaining_cell_count and not raise_on_first_difference:
        modified_cells.update(
            range(
                len(expected_cells) + 1,
                len(expected_cells) + 1 + remaining_cell_count,
            )
        )

    return modified_cells, modified_cell_metadata


def test_round_trip_conversion(notebook, fmt, update, allow_expected_differences=True, stop_on_first_error=True):
    """Test round trip conversion for a Jupyter notebook"""
    text = writes(notebook, fmt)
    round_trip = reads(text, fmt)

    if update:
        round_trip = combine_inputs_with_outputs(round_trip, notebook, fmt)

    compare_notebooks(
        round_trip,
        notebook,
        fmt,
        allow_expected_differences,
        raise_on_first_difference=stop_on_first_error,
    )


# The functions below are used in the Jupytext text collection
def create_mirror_file_if_missing(mirror_file, notebook, fmt):
    if not os.path.isfile(mirror_file):
        write(notebook, mirror_file, fmt=fmt)


def assert_conversion_same_as_mirror(nb_file, fmt, mirror_name, compare_notebook=False):
    """This function is used in the tests"""
    dirname, basename = os.path.split(nb_file)
    file_name, org_ext = os.path.splitext(basename)
    fmt = long_form_one_format(fmt)
    notebook = read(nb_file, fmt=fmt)
    fmt = check_auto_ext(fmt, notebook.metadata, "")
    ext = fmt["extension"]
    mirror_file = os.path.join(dirname, "..", "..", "outputs", mirror_name, full_path(file_name, fmt))

    # it's better not to have Jupytext metadata in test notebooks:
    if fmt == "ipynb" and "jupytext" in notebook.metadata:  # pragma: no cover
        notebook.metadata.pop("jupytext")
        write(nb_file, fmt=fmt)

    create_mirror_file_if_missing(mirror_file, notebook, fmt)

    # Compare the text representation of the two notebooks
    if compare_notebook:
        # Read and convert the mirror file to the latest nbformat version if necessary
        nb_mirror = read(mirror_file, as_version=notebook.nbformat)
        nb_mirror.nbformat_minor = notebook.nbformat_minor
        compare_notebooks(nb_mirror, notebook)
        return
    elif ext == ".ipynb":
        notebook = read(mirror_file)
        fmt.update({"extension": org_ext})
        actual = writes(notebook, fmt)
        with open(nb_file, encoding="utf-8") as fp:
            expected = fp.read()
    else:
        actual = writes(notebook, fmt)
        with open(mirror_file, encoding="utf-8") as fp:
            expected = fp.read()

    if not actual.endswith("\n"):
        actual = actual + "\n"

    if fmt.get("format_name") == "marimo":
        lines = expected.splitlines()
        lines = [
            # mirror files were generated with marimo 0.25.2
            f'__generated_with = "{marimo_version()}"' if line == '__generated_with = "0.25.2"' else line
            for line in lines
        ]
        expected = "\n".join(lines) + "\n"

    compare(actual, expected)

    # Compare the two notebooks
    if ext != ".ipynb":
        notebook = read(nb_file)
        nb_mirror = read(mirror_file, fmt=fmt)

        if fmt.get("format_name") == "sphinx":
            nb_mirror.cells = nb_mirror.cells[1:]
            for cell in notebook.cells:
                cell.metadata = {}
            for cell in nb_mirror.cells:
                cell.metadata = {}

        compare_notebooks(nb_mirror, notebook, fmt)

        nb_mirror = combine_inputs_with_outputs(nb_mirror, notebook)
        compare_notebooks(nb_mirror, notebook, fmt, compare_outputs=True)


def notebook_model(nb):
    """Return a notebook model, with content a
    dictionary rather than a notebook object.
    To be used in tests only."""
    return dict(type="notebook", content=json.loads(json.dumps(nb)))
