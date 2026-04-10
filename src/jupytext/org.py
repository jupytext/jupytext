"""Jupyter notebook to Emacs Org-mode and back, using Pandoc"""

import os
import tempfile

# Copy nbformat reads and writes to avoid them being patched in the contents manager!!
from nbformat import reads as ipynb_reads
from nbformat import writes as ipynb_writes

from .pandoc import PandocError, is_pandoc_available, pandoc, pandoc_version, raise_if_pandoc_is_not_available


def org_to_notebook(text):
    """Convert an Org-mode text to a Jupyter notebook, using Pandoc"""
    raise_if_pandoc_is_not_available()
    tmp_file = tempfile.NamedTemporaryFile(suffix=".org", delete=False)
    tmp_file.write(text.encode("utf-8"))
    tmp_file.close()

    out_file = tmp_file.name + ".ipynb"
    pandoc(
        "--from org --to ipynb -s --wrap=preserve --preserve-tabs",
        tmp_file.name,
        out_file,
    )

    with open(out_file, encoding="utf-8") as f:
        notebook = ipynb_reads(f.read(), as_version=4)

    os.unlink(tmp_file.name)
    os.unlink(out_file)

    return notebook


def notebook_to_org(notebook):
    """Convert a notebook to its Org-mode representation, using Pandoc"""
    raise_if_pandoc_is_not_available()
    tmp_file = tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False)
    tmp_file.write(ipynb_writes(notebook).encode("utf-8"))
    tmp_file.close()

    out_file = tmp_file.name + ".org"
    pandoc(
        "--from ipynb --to org -s --wrap=preserve --preserve-tabs",
        tmp_file.name,
        out_file,
    )

    with open(out_file, encoding="utf-8") as f:
        text = f.read()

    os.unlink(tmp_file.name)
    os.unlink(out_file)

    # Inject kernel name as an Org header-args property if available
    kernelspec = notebook.metadata.get("kernelspec", {})
    kernel_name = kernelspec.get("language") or kernelspec.get("name")
    if kernel_name:
        text = _inject_kernel_header_args(text, kernel_name)

    return "\n".join(text.splitlines())


def _inject_kernel_header_args(text, kernel_name):
    """Insert a top-level #+PROPERTY: header-args line for the kernel language"""
    header_args_line = f"#+PROPERTY: header-args:{kernel_name} :session *{kernel_name}*\n"
    lines = text.splitlines(keepends=True)
    # Insert after any existing #+TITLE / #+... lines at the top
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith("#+"):
            insert_pos = i + 1
        elif line.strip() == "":
            # skip blank lines at the very top
            if insert_pos == 0:
                continue
            break
        else:
            break
    lines.insert(insert_pos, header_args_line)
    return "".join(lines)
