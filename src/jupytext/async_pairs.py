from copy import copy

import jupytext

from .combine import combine_inputs_with_outputs
from .compare import compare
from .config import JupytextConfiguration
from .formats import check_file_version, long_form_multiple_formats
from .paired_paths import find_base_path_and_format, full_path
from .pairs import PairedFilesDiffer


async def read_pair(inputs, outputs, read_one_file, must_match=False):
    """Read a notebook given its inputs and outputs path and formats"""
    if not outputs.path or outputs.path == inputs.path:
        return await read_one_file(inputs.path, inputs.fmt)

    notebook = await read_one_file(inputs.path, inputs.fmt)
    check_file_version(notebook, inputs.path, outputs.path)

    notebook_with_outputs = await read_one_file(outputs.path, outputs.fmt)

    if must_match:
        comparison_source = notebook
        fmt = inputs.fmt
        config = None
        source_ids = getattr(notebook, "_cell_ids_from_titles", ())
        if source_ids:
            config = JupytextConfiguration(cell_id_to_title=True)
            # A pairing such as "ipynb,py" leaves the source script format to be detected on read.
            text_repr = notebook.metadata.get("jupytext", {}).get("text_representation", {})
            if "format_name" in text_repr:
                fmt = {**fmt, "format_name": text_repr["format_name"]}
            # Untitled cells carry temporary IDs. Compare only the IDs specified in the script.
            comparison_source = copy(notebook)
            comparison_source.cells = list(notebook.cells)
            for i, (cell, output_cell) in enumerate(zip(notebook.cells, notebook_with_outputs.cells)):
                if cell.id not in source_ids:
                    cell = copy(cell)
                    cell.pop("id")
                    if "id" in output_cell:
                        cell.id = output_cell.id
                    comparison_source.cells[i] = cell
        in_text = jupytext.writes(comparison_source, fmt, config=config)
        out_text = jupytext.writes(notebook_with_outputs, fmt, config=config)
        diff = compare(out_text, in_text, outputs.path, inputs.path, return_diff=True)
        if diff:
            raise PairedFilesDiffer(diff)

    notebook = combine_inputs_with_outputs(notebook, notebook_with_outputs, fmt=inputs.fmt)

    return notebook


async def write_pair(path, formats, write_one_file):
    """
    Call the function 'write_one_file' on each of the paired path/formats
    """
    formats = long_form_multiple_formats(formats)
    base, _ = find_base_path_and_format(path, formats)

    # Save as ipynb first
    return_value = None
    value = None
    ipynb_changed = False
    for fmt in formats[::-1]:
        if fmt["extension"] != ".ipynb":
            continue

        alt_path = full_path(base, fmt)
        value = await write_one_file(alt_path, fmt)
        ipynb_changed = ipynb_changed or value.get("modified", False)
        if alt_path == path:
            return_value = value

    # And then to the other formats, in reverse order so that
    # the first format is the most recent
    for fmt in formats[::-1]:
        if fmt["extension"] == ".ipynb":
            continue

        alt_path = full_path(base, fmt)
        if ipynb_changed:
            value = await write_one_file(alt_path, fmt, force_update_timestamp=True)
        else:
            # in the contents manager the write_one_file always writes anyway
            value = await write_one_file(alt_path, fmt)
        if alt_path == path:
            return_value = value

    # Update modified timestamp to match that of the pair #207
    if isinstance(return_value, dict) and "last_modified" in return_value:
        return_value["last_modified"] = value["last_modified"]

    return return_value
