"""Jupyter notebook to Markdown and back, using Pandoc"""

import os
import subprocess
import tempfile

# Copy nbformat reads and writes to avoid them being patched in the contents manager!!
from nbformat import reads as ipynb_reads
from nbformat import writes as ipynb_writes
from packaging.version import parse


class PandocError(OSError):
    """An error related to Pandoc"""


def pandoc(args, filein=None, fileout=None, *, timeout=None, input_text=None):
    """Execute pandoc with the given arguments"""
    cmd = ["pandoc"]

    if filein:
        cmd.append(filein)

    if fileout:
        cmd.append("-o")
        cmd.append(fileout)

    cmd.extend(args.split())

    try:
        proc = subprocess.run(
            cmd,
            input=input_text.encode("utf-8") if input_text is not None else None,
            stdout=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise PandocError(f"Pandoc conversion timed out after {timeout} seconds") from exc
    if proc.returncode:
        raise PandocError(f"pandoc exited with return code {proc.returncode}")
    return proc.stdout.decode("utf-8")


def is_pandoc_available(min_version="2.7.2", max_version=None):
    """Is Pandoc>=2.7.2 available?"""
    try:
        raise_if_pandoc_is_not_available(min_version=min_version, max_version=max_version)
        return True
    except PandocError:
        return False


def raise_if_pandoc_is_not_available(min_version="2.7.2", max_version=None):
    """Raise with an informative error message if pandoc is not available"""
    version = pandoc_version()
    if version == "N/A":
        raise PandocError(f"The Pandoc Markdown format requires 'pandoc>={min_version}', but pandoc was not found")

    if parse(version) < parse(min_version):
        raise PandocError(
            f"The Pandoc Markdown format requires 'pandoc>={min_version}', but pandoc version {version} was found"
        )

    if max_version and parse(version) > parse(max_version):
        raise PandocError(
            f"The Pandoc Markdown format requires 'pandoc<={max_version}', but pandoc version {version} was found"
        )

    return version


def pandoc_version():
    """Pandoc's version number"""
    try:
        return pandoc("--version").splitlines()[0].split()[1]
    except OSError:
        return "N/A"


def md_to_notebook(text):
    """Convert a Markdown text to a Jupyter notebook, using Pandoc"""
    raise_if_pandoc_is_not_available()
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(text.encode("utf-8"))
    tmp_file.close()

    if parse(pandoc_version()) < parse("2.11.2"):
        pandoc_args = "--from markdown --to ipynb -s --atx-headers --wrap=preserve --preserve-tabs"
    else:
        pandoc_args = "--from markdown --to ipynb -s --markdown-headings=atx --wrap=preserve --preserve-tabs"
    pandoc(
        pandoc_args,
        tmp_file.name,
        tmp_file.name,
    )

    with open(tmp_file.name, encoding="utf-8") as opened_file:
        notebook = ipynb_reads(opened_file.read(), as_version=4)
    os.unlink(tmp_file.name)

    return notebook


def notebook_to_md(notebook):
    """Convert a notebook to its Markdown representation, using Pandoc"""
    raise_if_pandoc_is_not_available()
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(ipynb_writes(notebook).encode("utf-8"))
    tmp_file.close()

    if parse(pandoc_version()) < parse("2.11.2"):
        pandoc_args = "--from ipynb --to markdown -s --atx-headers --wrap=preserve --preserve-tabs"
    else:
        pandoc_args = "--from ipynb --to markdown -s --markdown-headings=atx --wrap=preserve --preserve-tabs"
    pandoc(
        pandoc_args,
        tmp_file.name,
        tmp_file.name,
    )

    with open(tmp_file.name, encoding="utf-8") as opened_file:
        text = opened_file.read()

    os.unlink(tmp_file.name)
    return "\n".join(text.splitlines())
