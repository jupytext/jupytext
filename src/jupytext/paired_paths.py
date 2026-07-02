"""List all the paths associated to a given notebook"""

import os

from .config import find_jupytext_configuration_file
from .formats import (
    NOTEBOOK_EXTENSIONS,
    long_form_multiple_formats,
    long_form_one_format,
    short_form_multiple_formats,
    short_form_one_format,
)


class InconsistentPath(ValueError):
    """An exception raised when the path of a notebook is not consistent with the jupytext.format
    information it contains"""


class InconsistentSuffix(InconsistentPath):
    """An exception raised when the suffix of a notebook is not consistent with the suffix specification
    of a Jupytext format"""


class InconsistentPrefix(InconsistentPath):
    """An exception raised when the prefix of a notebook is not consistent with the prefix specification
    of a Jupytext format"""


class InconsistentPrefixDirectory(InconsistentPath):
    """An exception raised when the directory prefix of a notebook is not consistent with the directory prefix specification
    of a Jupytext format"""


class InconsistentPrefixRoot(InconsistentPath):
    """An exception raised when the root prefix of a notebook is not consistent with the root prefix specification
    of a Jupytext format"""


class NonNotebookExtension(InconsistentPath):
    """An exception raised when a notebook path does not have a notebook extension"""


class InconsistentExtension(InconsistentPath):
    """An exception raised when the extension of a notebook is not consistent with the extension specification
    of a Jupytext format"""


def split(path, sep):
    if sep not in path:
        return "", path

    return path.rsplit(sep, 1)


def join(left, right, sep):
    if left:
        return left + sep + right
    return right


def separator(path):
    """Return the local path separator (always / in the contents manager)"""
    if os.path.sep == "\\" and "\\" in path:
        return "\\"
    return "/"


def _path_reach(path, sep):
    """Describe how far a resolved path reaches outside its starting directory.

    Return an ``(anchor, climb)`` pair where ``anchor`` is the leading root the path
    is tied to (empty for a path relative to the current directory, the separator for
    an absolute path, or a Windows drive) and ``climb`` is the number of leading '..'
    segments that survive after resolving '.' and normal segments, i.e. how many
    levels the path escapes above that anchor.
    """
    if path.startswith(sep):
        anchor = sep
    elif len(path) >= 2 and path[1] == ":":
        anchor = path[:2]
    else:
        anchor = ""

    climb = 0
    depth = 0
    for part in path.split(sep):
        if part in ("", "."):
            continue
        if part == "..":
            if depth > 0:
                depth -= 1
            else:
                climb += 1
        else:
            depth += 1
    return anchor, climb


def get_prefix_root_prefix_dir_prefix_file_name(prefix: str) -> tuple[str, str, str]:
    if "//" in prefix:
        prefix_root, prefix = prefix.rsplit("//", 1)
    else:
        prefix_root = ""
    prefix_dir, prefix_file_name = split(prefix, "/")
    return prefix_root, prefix_dir, prefix_file_name


def get_prefix(prefix_root: str, prefix_dir: str, prefix_file_name: str) -> str:
    if prefix_root:
        return f"{prefix_root}//{prefix_dir}/{prefix_file_name}"
    if not prefix_dir and not prefix_file_name:
        return ""
    return f"{prefix_dir}/{prefix_file_name}"


def base_path(main_path, fmt, formats=None):
    """Given a path and options for a format (ext, suffix, prefix), return the corresponding base path"""
    fmt = long_form_one_format(fmt)

    base, ext = os.path.splitext(main_path)
    if "extension" not in fmt:
        fmt["extension"] = ext
        if ext not in NOTEBOOK_EXTENSIONS:
            raise NonNotebookExtension(
                "'{}' is not a notebook. Supported extensions are '{}'.".format(main_path, "', '".join(NOTEBOOK_EXTENSIONS))
            )

    if ext != fmt["extension"]:
        raise InconsistentExtension(
            "Notebook path '{}' was expected to have extension '{}'".format(main_path, fmt["extension"])
        )

    # Is there a format that matches the main path?
    if formats is None:
        formats = [fmt]

    for f in formats:
        if f["extension"] != fmt["extension"]:
            continue
        if "format_name" in fmt and "format_name" in f and f["format_name"] != fmt["format_name"]:
            continue
        # extend 'fmt' with the format information (prefix, suffix) from f
        fmt = {key: fmt.get(key, value) for key, value in f.items()}
        break

    suffix = fmt.get("suffix")
    prefix = fmt.get("prefix")

    if suffix:
        if not base.endswith(suffix):
            raise InconsistentSuffix(f"Notebook name '{base}' was expected to end with suffix '{suffix}'")
        base = base[: -len(suffix)]

    if not prefix:
        return base

    (
        prefix_root,
        prefix_dir,
        prefix_file_name,
    ) = get_prefix_root_prefix_dir_prefix_file_name(prefix)
    sep = separator(base)
    notebook_dir, notebook_file_name = split(base, sep)

    base_dir = None
    config_file = find_jupytext_configuration_file(notebook_dir)
    if config_file:
        config_file_dir = os.path.dirname(config_file)
        if notebook_dir.startswith(config_file_dir):
            base_dir = config_file_dir
            notebook_dir = notebook_dir[len(config_file_dir) :]

    if prefix_file_name:
        if not notebook_file_name.startswith(prefix_file_name):
            raise InconsistentPrefix(
                f"Notebook name '{notebook_file_name}' was expected to start with prefix '{prefix_file_name}'"
            )
        notebook_file_name = notebook_file_name[len(prefix_file_name) :]

    if prefix_dir:
        parent_notebook_dir = notebook_dir
        parent_prefix_dir = prefix_dir
        actual_folders = list()
        while parent_prefix_dir:
            parent_prefix_dir, expected_folder = split(parent_prefix_dir, "/")
            if expected_folder == "..":
                if not actual_folders:
                    raise InconsistentPrefixDirectory(
                        f"Notebook directory '{notebook_dir}' does not match prefix '{prefix_dir}'"
                    )
                parent_notebook_dir = join(parent_notebook_dir, actual_folders.pop(), sep)
            else:
                parent_notebook_dir, actual_folder = split(parent_notebook_dir, sep)
                actual_folders.append(actual_folder)

                if actual_folder != expected_folder:
                    raise InconsistentPrefixDirectory(
                        f"Notebook directory '{notebook_dir}' does not match prefix '{prefix_dir}'"
                    )
        notebook_dir = parent_notebook_dir

    if prefix_root:
        long_prefix_root = sep + prefix_root.replace("/", sep) + sep
        long_notebook_dir = sep + notebook_dir + sep
        if long_prefix_root not in long_notebook_dir:
            raise InconsistentPrefixRoot(f"Notebook directory '{notebook_dir}' does not match prefix root '{prefix_root}'")
        left, right = long_notebook_dir.rsplit(long_prefix_root, 1)
        notebook_dir = left + sep + "//" + right

        # We are going to remove the last char, but we need to insert it back in the end...
        if not right:
            sep = notebook_dir[-1]
        notebook_dir = notebook_dir[len(sep) : -len(sep)]

    if base_dir:
        notebook_dir = base_dir + notebook_dir

    if not notebook_dir:
        return notebook_file_name

    return notebook_dir + sep + notebook_file_name


def base_path_and_adjusted_fmt(path: str, fmt: dict[str, str]) -> tuple[str, dict[str, str]]:
    """Return the base path and possibly adjusted Jupytext format
    that matches the current path"""
    assert isinstance(fmt, dict), "fmt must be a dictionary"
    fmt = dict(fmt)  # make a copy
    prefix = fmt.get("prefix", "")
    (
        prefix_root,
        prefix_dir,
        prefix_file_name,
    ) = get_prefix_root_prefix_dir_prefix_file_name(prefix)

    try:
        return base_path(path, fmt), fmt
    except InconsistentSuffix:
        del fmt["suffix"]
        return base_path(path, fmt), fmt
    except InconsistentPrefixRoot:
        if not prefix_root:
            raise
        fmt["prefix"] = get_prefix("", prefix_dir, prefix_file_name)
        if not fmt["prefix"]:
            del fmt["prefix"]
        return base_path(path, fmt), fmt
    except InconsistentPrefix:
        if not prefix_file_name:
            raise
        fmt["prefix"] = get_prefix(prefix_root, prefix_dir, "")
        if not fmt["prefix"]:
            del fmt["prefix"]
        return base_path(path, fmt), fmt
    except InconsistentPrefixDirectory:
        if not prefix_dir:
            raise
        fmt["prefix"] = get_prefix(prefix_root, "", prefix_file_name)
        if not fmt["prefix"]:
            del fmt["prefix"]
        return base_path(path, fmt), fmt


def full_path(base, fmt):
    """Return the full path for the notebook, given the base path"""
    ext = fmt["extension"]
    suffix = fmt.get("suffix")
    prefix = fmt.get("prefix")

    full = base

    if prefix:
        if "//" in prefix:
            prefix_root, prefix = prefix.rsplit("//", 1)
        else:
            prefix_root = ""
        prefix_dir, prefix_file_name = split(prefix, "/")

        # Local path separator (\\ on windows)
        sep = separator(base)
        prefix_dir = prefix_dir.replace("/", sep)

        if (prefix_root != "") != ("//" in base):
            raise InconsistentPath(
                "Notebook base name '{}' is not compatible with fmt={}. Make sure you use prefix roots "
                "in either none, or all of the paired formats".format(base, short_form_one_format(fmt))
            )
        if prefix_root:
            left, right = base.rsplit("//", 1)
            right_dir, notebook_file_name = split(right, sep)
            notebook_dir = left + prefix_root + sep + right_dir
        else:
            notebook_dir, notebook_file_name = split(base, sep)

        if prefix_file_name:
            notebook_file_name = prefix_file_name + notebook_file_name

        if prefix_dir:
            dotdot = ".." + sep
            while prefix_dir.startswith(dotdot):
                prefix_dir = prefix_dir[len(dotdot) :]
                notebook_dir = split(notebook_dir, sep)[0]

            # Do not add a path separator when notebook_dir is '/'
            if notebook_dir and not notebook_dir.endswith(sep):
                notebook_dir = notebook_dir + sep

            notebook_dir = notebook_dir + prefix_dir

        if notebook_dir and not notebook_dir.endswith(sep):
            notebook_dir = notebook_dir + sep

        full = notebook_dir + notebook_file_name

    if suffix:
        full = full + suffix

    return full + ext


def find_base_path_and_format(main_path, formats: list[dict[str, str]]) -> tuple[str, dict[str, str]]:
    """Return the base path and the format corresponding to the given path"""
    for fmt in formats:
        try:
            return base_path(main_path, fmt), fmt
        except InconsistentPath:
            continue

    ext = os.path.splitext(main_path)[1][1:]
    raise InconsistentPath(
        f"Path '{main_path}' matches none of the export formats: {formats}. "
        f"Please make sure that jupytext.formats covers the current file "
        f"(e.g. add '{ext}' to the export formats)."
    )


def paired_paths(main_path, fmt, formats):
    """Return the list of paired notebooks, given main path, and the list of formats"""
    if not formats:
        return [(main_path, {"extension": os.path.splitext(main_path)[1]})]

    formats = long_form_multiple_formats(formats)

    # Is there a format that matches the main path?
    base = base_path(main_path, fmt, formats)
    paths = [full_path(base, f) for f in formats]

    if main_path not in paths:
        raise InconsistentPath(
            "Paired paths '{}' do not include the current notebook path '{}'. "
            "Current format is '{}', and paired formats are '{}'.".format(
                "','".join(paths),
                main_path,
                short_form_one_format(fmt),
                short_form_multiple_formats(formats),
            )
        )

    if len(paths) > len(set(paths)):
        raise InconsistentPath("Duplicate paired paths for this notebook. Please fix jupytext.formats.")

    # A paired file must stay within the notebook's own directory tree. Reject any
    # format whose prefix (e.g. '../../../' or an absolute path) makes a paired path
    # reach further up, or to a different root, than the notebook itself - otherwise
    # untrusted 'formats' metadata could drive writes outside the working tree.
    sep = separator(main_path)
    main_anchor, main_climb = _path_reach(main_path, sep)
    for alt_path in paths:
        anchor, climb = _path_reach(alt_path, sep)
        if anchor != main_anchor or climb > main_climb:
            raise InconsistentPath(
                f"Paired path '{alt_path}' escapes the directory of the notebook '{main_path}'. "
                "A prefix like '../' or an absolute path in 'formats' must stay within the "
                "notebook's directory tree."
            )

    return list(zip(paths, formats))
