"""Notebook and cell metadata filtering"""

from copy import copy

from .cell_metadata import _JUPYTEXT_CELL_METADATA, is_valid_metadata_key

_DEFAULT_NOTEBOOK_METADATA = ",".join(
    [
        # Preserve Jupytext section
        "jupytext",
        # Preserve kernel specs
        "kernelspec",
        # Org Babel header arguments
        "org_babel",
        # Kernel_info found in Nteract notebooks
        "kernel_info",
        # Used in MyST notebooks
        "orphan",
        "tocdepth",
    ]
)
_JUPYTER_METADATA_NAMESPACE = "jupyter"
_DEFAULT_ROOT_LEVEL_METADATA = "-all"


def metadata_filter_as_dict(metadata_config):
    """Return the metadata filter represented as either None (no filter),
    or a dictionary with at most two keys: 'additional' and 'excluded',
    which contain either a list of metadata names, or the string 'all'"""

    if metadata_config is None:
        return {}

    if metadata_config is True:
        return {"additional": "all"}

    if metadata_config is False:
        return {"excluded": "all"}

    if isinstance(metadata_config, dict):
        assert set(metadata_config) <= {"additional", "excluded"}
        return metadata_config

    metadata_keys = metadata_config.split(",")

    metadata_config = {}

    for key in metadata_keys:
        key = key.strip()
        if key.startswith("-"):
            metadata_config.setdefault("excluded", []).append(key[1:].strip())
        elif key.startswith("+"):
            metadata_config.setdefault("additional", []).append(key[1:].strip())
        else:
            metadata_config.setdefault("additional", []).append(key)

    for section in metadata_config:
        if "all" in metadata_config[section]:
            metadata_config[section] = "all"
        else:
            metadata_config[section] = [k for k in metadata_config[section] if k]

    return metadata_config


def metadata_filter_as_string(metadata_filter):
    """Convert a filter, represented as a dictionary with 'additional' and 'excluded' entries, to a string"""
    if not isinstance(metadata_filter, dict):
        return metadata_filter

    additional = metadata_filter.get("additional", [])
    if additional == "all":
        entries = ["all"]
    else:
        entries = [key for key in additional if key not in _JUPYTEXT_CELL_METADATA]

    excluded = metadata_filter.get("excluded", [])
    if excluded == "all":
        entries.append("-all")
    else:
        entries.extend(["-" + e for e in excluded])

    return ",".join(entries)


def update_metadata_filters(metadata, jupyter_md, cell_metadata):
    """Update or set the notebook and cell metadata filters"""

    if not jupyter_md:
        # Set a metadata filter equal to the current metadata in script
        metadata.setdefault("jupytext", {})["notebook_metadata_filter"] = "-all"
        metadata["jupytext"].setdefault(
            "cell_metadata_filter",
            metadata_filter_as_string({"additional": cell_metadata, "excluded": "all"}),
        )
    elif "cell_metadata_filter" in metadata.get("jupytext", {}):
        # Update the existing metadata filter
        metadata_filter = metadata_filter_as_dict(metadata.get("jupytext", {})["cell_metadata_filter"])
        if isinstance(metadata_filter.get("excluded"), list):
            metadata_filter["excluded"] = [key for key in metadata_filter["excluded"] if key not in cell_metadata]
        metadata_filter.setdefault("additional", [])
        if isinstance(metadata_filter.get("additional"), list):
            for key in cell_metadata:
                if key not in metadata_filter["additional"]:
                    metadata_filter["additional"].append(key)
        metadata.setdefault("jupytext", {})["cell_metadata_filter"] = metadata_filter_as_string(metadata_filter)
    else:
        # Update the notebook metadata filter to include existing entries 376
        nb_md_filter = metadata.get("jupytext", {}).get("notebook_metadata_filter", "").split(",")
        nb_md_filter = [key for key in nb_md_filter if key]
        if "all" in nb_md_filter or "-all" in nb_md_filter:
            return
        for key in metadata:
            if key in _DEFAULT_NOTEBOOK_METADATA.split(",") or key in nb_md_filter or ("-" + key) in nb_md_filter:
                continue
            nb_md_filter.append(key)
        if nb_md_filter:
            metadata.setdefault("jupytext", {})["notebook_metadata_filter"] = ",".join(nb_md_filter)


def filter_metadata(metadata, user_filter, default_filter="", unsupported_keys=None, **kwargs):
    """Filter the cell or notebook metadata, according to the user preference"""
    default_filter = metadata_filter_as_dict(default_filter) or {}
    user_filter = metadata_filter_as_dict(user_filter) or {}

    default_exclude = default_filter.get("excluded", [])
    default_include = default_filter.get("additional", [])

    assert not (default_exclude == "all" and default_include == "all")
    if isinstance(default_include, list) and default_include and default_exclude == []:
        default_exclude = "all"

    user_exclude = user_filter.get("excluded", [])
    user_include = user_filter.get("additional", [])

    # notebook default filter = include only few metadata
    if default_exclude == "all":
        if user_include == "all":
            return subset_metadata(
                metadata,
                exclude=user_exclude,
                unsupported_keys=unsupported_keys,
                **kwargs,
            )
        if user_exclude == "all":
            return subset_metadata(
                metadata,
                keep_only=user_include,
                unsupported_keys=unsupported_keys,
                **kwargs,
            )
        return subset_metadata(
            metadata,
            keep_only=set(user_include).union(default_include),
            exclude=user_exclude,
            unsupported_keys=unsupported_keys,
            **kwargs,
        )

    # cell default filter = all metadata but removed ones
    if user_include == "all":
        return subset_metadata(
            metadata,
            exclude=user_exclude,
            unsupported_keys=unsupported_keys,
            **kwargs,
        )
    if user_exclude == "all":
        return subset_metadata(
            metadata,
            keep_only=user_include,
            unsupported_keys=unsupported_keys,
            **kwargs,
        )
    # Do not serialize empty tags
    if "tags" in metadata and not metadata["tags"]:
        metadata = metadata.copy()
        metadata.pop("tags")
    return subset_metadata(
        metadata,
        exclude=set(user_exclude).union(set(default_exclude).difference(user_include)),
        unsupported_keys=unsupported_keys,
        **kwargs,
    )


def second_level(keys):
    """Return a dictionary with the nested keys, e.g. returns {'I':['a', 'b']} when keys=['I.a', 'I.b']"""
    sub_keys = {}
    for key in keys:
        if "." in key:
            left, right = key.split(".", 1)
            sub_keys.setdefault(left, []).append(right)

    return sub_keys


def suppress_unsupported_keys(metadata, unsupported_keys=None):
    # assert isinstance(unsupported_keys, set)
    if isinstance(unsupported_keys, set):
        for key in metadata:
            if not is_valid_metadata_key(key):
                unsupported_keys.add(key)
    return [key for key in metadata if is_valid_metadata_key(key)]


def subset_metadata(metadata, keep_only=None, exclude=None, unsupported_keys=None, remove=False):
    """Filter the metadata"""
    supported_keys = suppress_unsupported_keys(metadata, unsupported_keys=unsupported_keys)
    if keep_only is not None:
        include = [key for key in supported_keys if key in keep_only]
        filtered_metadata = {key: metadata[key] for key in include}
        sub_keep_only = second_level(keep_only)
        keys = [key for key in supported_keys if key in sub_keep_only]
        for key in keys:
            filtered_metadata[key] = subset_metadata(
                metadata[key],
                keep_only=sub_keep_only[key],
                unsupported_keys=unsupported_keys,
                remove=remove,
            )
    else:
        include = supported_keys
        filtered_metadata = {key: metadata[key] for key in supported_keys}

    if exclude is not None:
        for key in exclude:
            if key in filtered_metadata:
                filtered_metadata.pop(key)
        sub_exclude = second_level(exclude)
        for key in sub_exclude:
            if key in filtered_metadata:
                filtered_metadata[key] = subset_metadata(
                    filtered_metadata[key],
                    exclude=sub_exclude[key],
                    unsupported_keys=unsupported_keys,
                    remove=remove,
                )

    if remove:
        for key in set(include).difference(exclude or {}):
            metadata.pop(key, None)

    return filtered_metadata


def restore_filtered_metadata(filtered_metadata, unfiltered_metadata, user_filter, default_filter):
    """Update the filtered metadata with the part of the unfiltered one that matches the filter"""
    filtered_unfiltered_metadata = filter_metadata(unfiltered_metadata, user_filter, default_filter)

    metadata = copy(filtered_metadata)
    for key in unfiltered_metadata:
        if key not in filtered_unfiltered_metadata:
            # We don't want to restore the line_to_next_cell metadata from the ipynb file, see #761
            if key not in _JUPYTEXT_CELL_METADATA:
                metadata[key] = unfiltered_metadata[key]

    return metadata
