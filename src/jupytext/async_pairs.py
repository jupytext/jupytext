from .combine import combine_inputs_with_outputs
from .formats import check_file_version, long_form_multiple_formats
from .paired_paths import find_base_path_and_format, full_path
from .pairs import check_paired_files_match


async def read_pair(inputs, outputs, read_one_file, must_match=False):
    """Read a notebook given its inputs and outputs path and formats"""
    if not outputs.path or outputs.path == inputs.path:
        return await read_one_file(inputs.path, inputs.fmt)

    notebook = await read_one_file(inputs.path, inputs.fmt)
    check_file_version(notebook, inputs.path, outputs.path)

    notebook_with_outputs = await read_one_file(outputs.path, outputs.fmt)

    if must_match:
        check_paired_files_match(inputs, outputs, notebook, notebook_with_outputs)

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
