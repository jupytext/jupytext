"""Functions to read or write paired notebooks"""

from collections import namedtuple
from copy import copy

from .compare import compare
from .config import JupytextConfiguration
from .formats import long_form_multiple_formats, long_form_one_format
from .jupytext import writes
from .paired_paths import paired_paths

NotebookFile = namedtuple("notebook_file", "path fmt timestamp")


class PairedFilesDiffer(ValueError):
    """An error when the two representations of a paired notebook differ"""


def check_paired_files_match(inputs, outputs, notebook, notebook_with_outputs):
    """Raise PairedFilesDiffer if the two notebooks differ in the input text format."""
    comparison_source = notebook
    fmt = inputs.fmt
    config = None
    source_ids = vars(notebook).get("_cell_ids_from_text", ())
    if source_ids:
        config = JupytextConfiguration(cell_id_to_title=True)
        # A pairing such as "ipynb,py" leaves the source script format to be detected on read.
        text_repr = notebook.metadata.get("jupytext", {}).get("text_representation", {})
        if "format_name" in text_repr:
            fmt = {**fmt, "format_name": text_repr["format_name"]}
        # Cells without explicit IDs carry temporary IDs. Compare only the IDs specified in the script.
        comparison_source = copy(notebook)
        comparison_source.cells = list(notebook.cells)
        for i, (cell, output_cell) in enumerate(zip(notebook.cells, notebook_with_outputs.cells)):
            if cell.id not in source_ids:
                cell = copy(cell)
                cell.pop("id")
                if "id" in output_cell:
                    cell.id = output_cell.id
                comparison_source.cells[i] = cell

    in_text = writes(comparison_source, fmt, config=config)
    out_text = writes(notebook_with_outputs, fmt, config=config)
    diff = compare(out_text, in_text, outputs.path, inputs.path, return_diff=True)
    if diff:
        raise PairedFilesDiffer(diff)


def latest_inputs_and_outputs(path, fmt, formats, get_timestamp, contents_manager_mode=False):
    """Given a notebook path, its format and paired formats, and a function that
    returns the timestamp for each (or None if the file does not exist), return
    the most recent notebook for the inputs and outputs, respectively"""

    timestamp_inputs = None
    timestamp_outputs = None
    inputs_path = None
    outputs_path = None
    input_fmt = None
    output_fmt = None

    fmt = long_form_one_format(fmt)
    formats = long_form_multiple_formats(formats)

    for alt_path, alt_fmt in paired_paths(path, fmt, formats):
        # In the contents manager, we don't read another text file if the current notebook is in already in text mode
        if contents_manager_mode and alt_fmt["extension"] != ".ipynb" and fmt["extension"] != ".ipynb":
            if any(alt_fmt.get(key) != fmt.get(key) for key in ["extension", "suffix", "prefix"]):
                continue

        timestamp = get_timestamp(alt_path)
        if timestamp is None:
            continue

        if alt_fmt["extension"] == ".ipynb":
            if timestamp_outputs is None or timestamp > timestamp_outputs:
                timestamp_outputs = timestamp
                outputs_path, output_fmt = alt_path, alt_fmt
        elif timestamp_inputs is None or timestamp > timestamp_inputs:
            timestamp_inputs = timestamp
            inputs_path, input_fmt = alt_path, alt_fmt

    if timestamp_inputs is None or (not contents_manager_mode and timestamp_outputs and timestamp_outputs > timestamp_inputs):
        timestamp_inputs = timestamp_outputs
        inputs_path, input_fmt = outputs_path, output_fmt

    return (
        NotebookFile(inputs_path, input_fmt, timestamp_inputs),
        NotebookFile(outputs_path, output_fmt, timestamp_outputs),
    )
