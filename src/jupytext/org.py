"""Jupyter notebook to Emacs Org-mode and back, using Pandoc"""

import os
import re
import tempfile

# Copy nbformat reads and writes to avoid them being patched in the contents manager!!
from nbformat import reads as ipynb_reads
from nbformat import writes as ipynb_writes

from .pandoc import pandoc, raise_if_pandoc_is_not_available

# Matches valid Org keyword lines such as #+TITLE:, #+AUTHOR:, #+PROPERTY:, etc.
# Org keywords are case-insensitive; Pandoc may generate lowercase variants.
_ORG_KEYWORD_RE = re.compile(r"^#\+[A-Za-z_]+:", re.IGNORECASE)


def org_to_notebook(text):
    """Convert an Org-mode text to a Jupyter notebook, using Pandoc"""
    raise_if_pandoc_is_not_available()
    tmp_in = tempfile.NamedTemporaryFile(suffix=".org", delete=False)
    tmp_in.write(text.encode("utf-8"))
    tmp_in.close()
    out_file = tmp_in.name + ".ipynb"

    try:
        pandoc(
            "--from org --to ipynb -s --wrap=preserve --preserve-tabs",
            tmp_in.name,
            out_file,
        )
        with open(out_file, encoding="utf-8") as f:
            notebook = ipynb_reads(f.read(), as_version=4)
    finally:
        os.unlink(tmp_in.name)
        if os.path.exists(out_file):
            os.unlink(out_file)

    return notebook


def notebook_to_org(notebook):
    """Convert a notebook to its Org-mode representation, using Pandoc"""
    raise_if_pandoc_is_not_available()
    tmp_in = tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False)
    tmp_in.write(ipynb_writes(notebook).encode("utf-8"))
    tmp_in.close()
    out_file = tmp_in.name + ".org"

    try:
        pandoc(
            "--from ipynb --to org -s --wrap=preserve --preserve-tabs",
            tmp_in.name,
            out_file,
        )
        with open(out_file, encoding="utf-8") as f:
            text = f.read()
    finally:
        os.unlink(tmp_in.name)
        if os.path.exists(out_file):
            os.unlink(out_file)

    # Inject kernel name as an Org header-args property if available.
    # Sanitize to only allow safe characters (letters, digits, hyphens, underscores, plus).
    kernelspec = notebook.metadata.get("kernelspec", {})
    kernel_name = kernelspec.get("language") or kernelspec.get("name")
    if kernel_name:
        kernel_name = re.sub(r"[^A-Za-z0-9_+\-]", "", kernel_name)
    if kernel_name:
        text = _inject_kernel_header_args(text, kernel_name)

    # Normalize line endings (consistent with pandoc.py behavior)
    return "\n".join(text.splitlines())


def _inject_kernel_header_args(text, kernel_name):
    """Insert a #+PROPERTY: header-args line after the leading Org keyword block"""
    header_args_line = f"#+PROPERTY: header-args:{kernel_name} :session *{kernel_name}*\n"
    lines = text.splitlines(keepends=True)
    # Find the last Org keyword (#+KEYWORD:) line in the leading header block.
    # Blank lines are skipped; the first non-blank, non-keyword line ends the search.
    last_header_line = -1
    for i, line in enumerate(lines):
        if _ORG_KEYWORD_RE.match(line):
            last_header_line = i
        elif line.strip():
            # First non-blank, non-keyword line ends the search
            break
    # insert_pos == 0 when no keyword lines were found; inserts at document start
    insert_pos = last_header_line + 1
    lines.insert(insert_pos, header_args_line)
    return "".join(lines)
