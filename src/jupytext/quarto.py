"""Jupyter notebook to Quarto Markdown and back, using 'quarto convert'"""

import json
import shutil
import subprocess
import sys
import tempfile

# Copy nbformat reads and writes to avoid them being patched in the contents manager!!
from nbformat import reads as ipynb_reads
from nbformat import writes as ipynb_writes
from packaging.version import parse
import yaml

QUARTO_MIN_VERSION = "0.2.134"


class QuartoError(OSError):
    """An error related to Quarto"""


def quarto(args, filein=None):
    """Execute quarto with the given arguments"""
    executable = shutil.which("quarto")
    if not executable and sys.platform.startswith("win"):
        # On Windows, try quarto.cmd, see #1406
        executable = shutil.which("quarto.cmd")
    if not executable:
        raise QuartoError("Could not find 'quarto' executable")

    cmd = [executable] + args.split()

    if filein:
        cmd.append(filein)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode:
        raise QuartoError(f"{' '.join(cmd)} exited with return code {proc.returncode}\n{err.decode('utf-8')}")

    return out.decode("utf-8")


def is_quarto_available(min_version=QUARTO_MIN_VERSION):
    """Is Quarto available?"""
    try:
        raise_if_quarto_is_not_available(min_version=min_version)
        return True
    except QuartoError:
        return False


def raise_if_quarto_is_not_available(min_version=QUARTO_MIN_VERSION):
    """Raise with an informative error message if quarto is not available"""
    version = quarto_version()
    if version == "N/A":
        raise QuartoError(f"The Quarto Markdown format requires 'quarto>={min_version}', but quarto was not found")

    if parse(version) < parse(min_version):
        raise QuartoError(
            f"The Quarto Markdown format requires 'quarto>={min_version}', but quarto version {version} was found"
        )

    return version


def quarto_version():
    """Quarto's version number"""
    try:
        return quarto("--version").strip()
    except OSError:
        return "N/A"


def qmd_to_notebook(text):
    """Convert a Quarto Markdown notebook to a Jupyter notebook"""
    raise_if_quarto_is_not_available()
    # Quarto derives the name of the file it writes from the name of the file it reads,
    # so we give it a directory of its own rather than let it create that output file
    # in the shared temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_qmd_file = tempfile.NamedTemporaryFile(delete=False, suffix=".qmd", dir=tmp_dir)
        tmp_qmd_file.write(text.encode("utf-8"))
        tmp_qmd_file.close()

        quarto("convert --log-level warning", tmp_qmd_file.name)

        tmp_ipynb_file_name = tmp_qmd_file.name[:-4] + ".ipynb"

        with open(tmp_ipynb_file_name, encoding="utf-8") as ipynb_file:
            notebook = ipynb_reads(ipynb_file.read(), as_version=4)

    # Recent version of Quarto duplicate the notebook metadata in a YAML header
    # If we find such a header, we remove it if it is identical to the notebook metadata
    if not notebook.cells or notebook.cells[0].cell_type != "markdown":
        return notebook

    cell_source = notebook.cells[0].source.strip()
    if cell_source.startswith("---") and cell_source.endswith("---"):
        try:
            metadata_from_top_cell = yaml.safe_load(cell_source[3:-3])
        except yaml.YAMLError:
            pass
        else:
            if "jupyter" not in metadata_from_top_cell:
                return notebook
            if metadata_from_top_cell == {"jupyter": "python3"}:
                # Quarto sometimes writes "jupyter: python3" instead of the full metadata
                # We can safely remove this cell
                del notebook.cells[0]
                return notebook

            jupyter_metadata = json.dumps(metadata_from_top_cell["jupyter"], sort_keys=True)
            notebook_metadata = json.dumps(notebook.metadata, sort_keys=True)
            if jupyter_metadata == notebook_metadata:
                if set(metadata_from_top_cell.keys()) == {"jupyter"}:
                    # The metadata are identical, we can remove the duplicated cell
                    del notebook.cells[0]
                    return notebook
                else:
                    # The jupyter metadata are identical, but there are other keys in the YAML header
                    # We keep the cell, but remove the jupyter key
                    lines = cell_source.splitlines()
                    non_jupyter_lines = []
                    in_jupyter_section = False
                    for line in lines:
                        if not (line.startswith("  ") or line.startswith("\t")):
                            in_jupyter_section = False
                        if line.rstrip() == "jupyter:":
                            in_jupyter_section = True
                        if not in_jupyter_section:
                            non_jupyter_lines.append(line)
                    notebook.cells[0].source = "\n".join(non_jupyter_lines)
            else:
                # The metadata are different, we keep the cell but issue a warning
                print(
                    "Warning: the Quarto Markdown file contains a YAML header that does not match the notebook metadata:\n"
                    f"Header metadata:\n{metadata_from_top_cell}\n"
                    f"Notebook metadata:\n{notebook_metadata}",
                    file=sys.stderr,
                )

    return notebook


def notebook_to_qmd(notebook):
    """Convert a Jupyter notebook to its Quarto Markdown representation"""
    raise_if_quarto_is_not_available()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_ipynb_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ipynb", dir=tmp_dir)
        tmp_ipynb_file.write(ipynb_writes(notebook).encode("utf-8"))
        tmp_ipynb_file.close()

        quarto("convert --log-level warning", tmp_ipynb_file.name)

        tmp_qmd_file_name = tmp_ipynb_file.name[:-6] + ".qmd"

        with open(tmp_qmd_file_name, encoding="utf-8") as qmd_file:
            text = qmd_file.read()

    return "\n".join(text.splitlines())
