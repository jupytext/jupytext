"""Combine source and outputs from two notebooks"""

import re

from nbformat import NotebookNode

from .cell_metadata import _IGNORE_CELL_METADATA
from .formats import long_form_one_format
from .header import _DEFAULT_NOTEBOOK_METADATA, FrontMatterCell
from .metadata_filter import restore_filtered_metadata

_BLANK_LINE = re.compile(r"^\s*$")


def black_invariant(text, chars=None):
    """Remove characters that may be changed when reformatting the text with black"""
    if chars is None:
        chars = [" ", "\t", "\n", ",", "'", '"', "(", ")", "\\"]

    for char in chars:
        text = text.replace(char, "")
    return text


def same_content(ref, test, endswith=False):
    """Is the content of two cells the same, up to reformatting by black"""
    ref = black_invariant(ref)
    test = black_invariant(test)

    if endswith and test:
        return ref.endswith(test)
    return ref == test


def combine_inputs_with_outputs(nb_source, nb_outputs, fmt=None):
    """Return a notebook that combines the text and metadata from the first notebook,
    with the outputs and metadata of the second notebook."""
    # nbformat version number taken from the notebook with outputs
    assert nb_outputs.nbformat == nb_source.nbformat, (
        "The notebook with outputs is in format {}.{}, please upgrade it to {}.x".format(
            nb_outputs.nbformat, nb_outputs.nbformat_minor, nb_source.nbformat
        )
    )
    source_ids = vars(nb_source).get("_cell_ids_from_text", ())
    nbformat_minor = max(nb_outputs.nbformat_minor, 5) if source_ids else nb_outputs.nbformat_minor
    nb_source.nbformat_minor = nbformat_minor

    fmt = long_form_one_format(fmt)
    text_repr = nb_source.metadata.get("jupytext", {}).get("text_representation", {})
    ext = fmt.get("extension") or text_repr.get("extension")
    format_name = fmt.get("format_name") or text_repr.get("format_name")

    notebook_metadata_filter = nb_source.metadata.get("jupytext", {}).get("notebook_metadata_filter")
    if ext == ".org":
        nb_metadata = restore_filtered_metadata(nb_source.metadata, nb_outputs.metadata, None, "kernelspec,org_babel")
    elif notebook_metadata_filter == "-all":
        nb_metadata = nb_outputs.metadata

    else:
        nb_metadata = restore_filtered_metadata(
            nb_source.metadata,
            nb_outputs.metadata,
            notebook_metadata_filter,
            _DEFAULT_NOTEBOOK_METADATA,
        )

    source_is_md_version_one = ext in [".md", ".markdown", ".Rmd"] and text_repr.get("format_version") == "1.0"
    if nb_metadata.get("jupytext", {}).get("formats") or ext in [
        ".md",
        ".markdown",
        ".Rmd",
    ]:
        nb_metadata.get("jupytext", {}).pop("text_representation", None)

    if not nb_metadata.get("jupytext", {}):
        nb_metadata.pop("jupytext", {})

    if format_name in ["nomarker", "sphinx", "marimo"] or source_is_md_version_one:
        cell_metadata_filter = "-all"
    else:
        cell_metadata_filter = nb_metadata.get("jupytext", {}).get("cell_metadata_filter")

    outputs_map = map_outputs_to_inputs(nb_source.cells, nb_outputs.cells, source_ids)

    cells = []
    for source_cell, j in zip(nb_source.cells, outputs_map):
        if j is None:
            cells.append(source_cell)
            continue

        output_cell = nb_outputs.cells[j]

        # Keep the stored outputs and attributes, and use the source cell's origin.
        is_frontmatter_cell = isinstance(source_cell, FrontMatterCell)
        cell_cls = FrontMatterCell if is_frontmatter_cell else NotebookNode
        cell = cell_cls(output_cell)

        # Cell text is taken from the source notebook
        cell.source = source_cell.source
        if source_ids and (source_cell.id in source_ids or "id" not in output_cell or output_cell.id in source_ids):
            cell.id = source_cell.id

        # We also restore the cell metadata that has been filtered
        if is_frontmatter_cell:
            source_cell_metadata_filter = "-all"
        elif format_name == "spin" and source_cell.cell_type != "code":
            # The 'spin' format does not allow metadata on non-code cells
            source_cell_metadata_filter = "-all"
        else:
            source_cell_metadata_filter = cell_metadata_filter
        cell.metadata = restore_filtered_metadata(
            source_cell.metadata,
            output_cell.metadata,
            source_cell_metadata_filter,
            _IGNORE_CELL_METADATA,
        )

        cells.append(cell)

    # We call NotebookNode rather than new_notebook as we don't want to validate
    # the notebook (some of the notebook in the collection of test notebooks
    # do have some invalid properties - probably inherited from an older version
    # of the notebook format).
    return NotebookNode(
        cells=cells,
        metadata=nb_metadata,
        nbformat=nb_outputs.nbformat,
        nbformat_minor=nbformat_minor,
    )


def map_outputs_to_inputs(cells_inputs, cells_outputs, source_ids=()):
    """Returns a map i->(j or None) that maps the cells with outputs to the input cells"""
    n_in = len(cells_inputs)
    n_out = len(cells_outputs)
    outputs_map = [None] * n_in
    used_outputs = set()

    if source_ids:
        outputs_by_id = {(cell.get("id"), cell.cell_type): j for j, cell in enumerate(cells_outputs)}
        for i, cell in enumerate(cells_inputs):
            if cell.id in source_ids:
                j = outputs_by_id.get((cell.id, cell.cell_type))
                if j is not None:
                    outputs_map[i] = j
                    used_outputs.add(j)

    # First rule: match based on cell type, content, in increasing order, for each cell type
    first_unmatched_output_per_cell_type = {}
    for i in range(n_in):
        if outputs_map[i] is not None:
            continue
        cell_input = cells_inputs[i]
        for j in range(first_unmatched_output_per_cell_type.get(cell_input.cell_type, 0), n_out):
            if j in used_outputs:
                continue
            cell_output = cells_outputs[j]
            if cell_input.cell_type == cell_output.cell_type and same_content(cell_input.source, cell_output.source):
                outputs_map[i] = j
                first_unmatched_output_per_cell_type[cell_input.cell_type] = j + 1
                break

    # Second rule: match unused outputs based on cell type and content
    # Third rule: is the new cell the final part of a previous cell with outputs?
    unused_outputs = set(range(n_out)).difference(outputs_map)
    for endswith in [False, True]:
        if not unused_outputs:
            return outputs_map

        for i in range(n_in):
            if outputs_map[i] is not None:
                continue
            cell_input = cells_inputs[i]
            for j in unused_outputs:
                cell_output = cells_outputs[j]
                if cell_input.cell_type == cell_output.cell_type and same_content(
                    cell_output.source, cell_input.source, endswith
                ):
                    outputs_map[i] = j
                    unused_outputs.remove(j)
                    break

    # Fourth rule: match based on increasing index (and cell type) for non-empty cells
    if not unused_outputs:
        return outputs_map

    prev_j = -1
    for i in range(n_in):
        if outputs_map[i] is not None:
            prev_j = outputs_map[i]
            continue

        j = prev_j + 1
        if j not in unused_outputs:
            continue

        cell_input = cells_inputs[i]
        cell_output = cells_outputs[j]
        if cell_input.cell_type == cell_output.cell_type and cell_input.source.strip() != "":
            outputs_map[i] = j
            unused_outputs.remove(j)
            prev_j = j

    return outputs_map
