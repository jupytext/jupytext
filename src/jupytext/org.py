"""Jupyter notebook to Emacs Org-mode and back, using Pandoc"""

import os
import re
import tempfile
from typing import Any

# Copy nbformat reads and writes to avoid them being patched in the contents manager!!
from nbformat import reads as ipynb_reads
from nbformat import writes as ipynb_writes

from .pandoc import PandocError, pandoc, raise_if_pandoc_is_not_available

# Matches valid Org keyword lines such as #+TITLE:, #+AUTHOR:, #+PROPERTY:, etc.
# Org keywords are case-insensitive; Pandoc may generate lowercase variants.
_ORG_KEYWORD_RE = re.compile(r"^#\+[A-Za-z_]+:", re.IGNORECASE)
_ORG_BLOCK_START_RE = re.compile(r"^[ \t]*#\+BEGIN_(\w+)\b", re.IGNORECASE)
_ORG_CPP_SOURCE_RE = re.compile(r"^([ \t]*#\+BEGIN_SRC[ \t]+)jupyter-c\+\+(?=\s|$)", re.IGNORECASE)
_ORG_JUPYTER_SOURCE_RE = re.compile(r"^[ \t]*#\+BEGIN_SRC[ \t]+jupyter-\S+", re.IGNORECASE)
_ORG_HEADER_ARGS_RE = re.compile(r"^#\+PROPERTY:[ \t]+header-args(?::(\S+)|\+)?[ \t]+(.*)$", re.IGNORECASE)
_ORG_HEADER_ARG_RE = re.compile(r'(?:^|[ \t]+):([A-Za-z0-9_-]+)(?=[ \t]|$)|"(?:\\.|[^"\\])*"')
_ORG_KERNEL_DISPLAY_NAME_RE = re.compile(r"^#\+JUPYTER_KERNEL_DISPLAY_NAME:[ \t]*(.*?)\s*$", re.IGNORECASE)
_ORG_ARGUMENT_KEY_RE = re.compile(r"[A-Za-z0-9_-]+")
_ORG_TIMEOUT_SECONDS = 30


def org_to_notebook(text):
    """Convert an Org-mode text to a Jupyter notebook, using Pandoc"""
    _raise_if_pandoc_is_not_available_for_org()
    text, metadata = _extract_org_metadata(_preserve_source_tabs(text))
    tmp_in = tempfile.NamedTemporaryFile(suffix=".org", delete=False)
    tmp_in.write(text.encode("utf-8"))
    tmp_in.close()
    out_file = tmp_in.name + ".ipynb"

    try:
        pandoc(
            "--from org --to ipynb -s --wrap=preserve --preserve-tabs",
            tmp_in.name,
            out_file,
            timeout=_ORG_TIMEOUT_SECONDS,
        )
        with open(out_file, encoding="utf-8") as f:
            notebook = ipynb_reads(f.read(), as_version=4)
    finally:
        os.unlink(tmp_in.name)
        if os.path.exists(out_file):
            os.unlink(out_file)

    _trim_trailing_newline_from_code_cells(notebook)
    notebook.metadata.update(metadata)

    return notebook


def notebook_to_org(notebook):
    """Convert a notebook to its Org-mode representation, using Pandoc"""
    _raise_if_pandoc_is_not_available_for_org()
    if any(cell.get("attachments") for cell in notebook.cells):
        raise ValueError("Org export cannot preserve notebook attachments")
    tmp_in = tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False)
    tmp_in.write(ipynb_writes(notebook).encode("utf-8"))
    tmp_in.close()
    out_file = tmp_in.name + ".org"

    try:
        pandoc(
            "--from ipynb --to org -s --wrap=preserve --preserve-tabs",
            tmp_in.name,
            out_file,
            timeout=_ORG_TIMEOUT_SECONDS,
        )
        with open(out_file, encoding="utf-8") as f:
            text = f.read()
    finally:
        os.unlink(tmp_in.name)
        if os.path.exists(out_file):
            os.unlink(out_file)

    kernelspec = notebook.metadata.get("kernelspec", {})
    header_args = notebook.metadata.get("org_babel", {}).get("header_args", {})
    text = _inject_header_args(text, kernelspec, header_args)

    return "\n".join(_preserve_source_tabs(text).splitlines())


def _inject_header_args(text: str, kernelspec: dict, header_args: dict) -> str:
    """Insert document-wide Babel properties and Jupyter kernel metadata."""
    kernel_name = kernelspec.get("name")
    kernel_language = kernelspec.get("language")
    block_language = f"jupyter-{kernel_language}" if kernel_name and kernel_language else None
    header_args_lines = []
    if block_language:
        display_name = " ".join(str(kernelspec.get("display_name") or "").split())
        if display_name:
            header_args_lines.append(f"#+JUPYTER_KERNEL_DISPLAY_NAME: {display_name}\n")
        header_args_lines.append(_format_header_args_line(block_language, {"kernel": kernel_name}))

    for language, args in header_args.items():
        args = {key: value for key, value in args.items() if language != block_language or key != "kernel"}
        if language == block_language == "jupyter-c++" and args:
            header_args_lines[-1] = _format_header_args_line(language, {"kernel": kernel_name, **args})
        elif args:
            property_language = language + "+" if language == block_language else language
            header_args_lines.append(_format_header_args_line(property_language, args))

    lines = text.splitlines(keepends=True)
    last_header_line = -1
    for i, line in enumerate(lines):
        if _ORG_KEYWORD_RE.match(line):
            last_header_line = i
        elif line.strip():
            break

    insert_pos = last_header_line + 1
    lines[insert_pos:insert_pos] = header_args_lines
    return "".join(lines)


def _format_header_args_line(language: str, args: dict[str, Any]) -> str:
    if any(char.isspace() for char in language):
        raise ValueError(f"Invalid Org Babel language {language!r}")
    tokens = []
    for key, value in args.items():
        if not _ORG_ARGUMENT_KEY_RE.fullmatch(key):
            raise ValueError(f"Invalid Org Babel header argument {key!r}")
        values = value if key == "var" and isinstance(value, list) else [value]
        for item in values:
            item = str(item)
            if len(item.splitlines()) > 1 or "\n" in item or "\r" in item:
                raise ValueError(f"Invalid Org Babel header argument {key!r}")
            tokens.append(f":{key} {item}".rstrip())
    suffix = f":{language}" if language else ""
    return f"#+PROPERTY: header-args{suffix} {' '.join(tokens)}\n"


def _update_header_args(args: dict[str, str | list[str]], text: str) -> None:
    # Quoted strings are matched as a unit, so a colon inside one cannot start another argument.
    keys = [match for match in _ORG_HEADER_ARG_RE.finditer(text) if match.group(1)]
    for index, match in enumerate(keys):
        key = match.group(1)
        end = keys[index + 1].start() if index + 1 < len(keys) else len(text)
        value = text[match.end() : end].strip()

        # Babel allows multiple :var assignments in one property or across additive properties.
        if key == "var" and key in args:
            previous = args[key]
            if isinstance(previous, list):
                previous.append(value)
            else:
                args[key] = [previous, value]
        else:
            args[key] = value


def _preserve_source_tabs(text: str) -> str:
    """Mark Jupyter source blocks with tabs so Pandoc reads the tabs literally."""
    lines = text.splitlines(keepends=True)
    block_end = None
    source_header = None
    for index, line in enumerate(lines):
        if block_end:
            if line.strip().upper() == block_end:
                block_end = None
                source_header = None
            elif source_header is not None and "\t" in line:
                # Pandoc honors --preserve-tabs in Org source blocks with the -i switch.
                header_index, language_end = source_header
                header = lines[header_index]
                if not re.match(r"[ \t]+-i(?:\s|$)", header[language_end:]):
                    lines[header_index] = header[:language_end] + " -i" + header[language_end:]
                source_header = None
        elif block := _ORG_BLOCK_START_RE.match(line):
            block_end = f"#+END_{block.group(1).upper()}"
            if source := _ORG_JUPYTER_SOURCE_RE.match(line):
                source_header = index, source.end()
    return "".join(lines)


def _extract_org_metadata(text: str) -> tuple[str, dict[str, Any]]:
    """Remove document-level properties and prepare source block languages for Pandoc."""
    body = []
    header_args: dict[str, dict[str, str | list[str]]] = {}
    display_name = ""
    block_end = None
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if block_end:
            body.append(line)
            if content.strip().upper() == block_end:
                block_end = None
            continue

        block = _ORG_BLOCK_START_RE.match(content)
        if block:
            block_end = f"#+END_{block.group(1).upper()}"
            # Pandoc's Org reader does not recognize '+' in a source block language.
            line = _ORG_CPP_SOURCE_RE.sub(r"\g<1>jupyter-cpp", line)
        elif match := _ORG_HEADER_ARGS_RE.fullmatch(content):
            language = match.group(1) or ""
            if language.endswith("+") and language.lower() != "jupyter-c++":
                language = language[:-1]
            _update_header_args(header_args.setdefault(language, {}), match.group(2))
            continue
        elif match := _ORG_KERNEL_DISPLAY_NAME_RE.fullmatch(content):
            display_name = match.group(1)
            continue
        body.append(line)

    metadata: dict[str, Any] = {}
    for language, args in header_args.items():
        if language.lower().startswith("jupyter-") and args.get("kernel"):
            kernel = args.pop("kernel")
            metadata["kernelspec"] = {
                "name": kernel,
                "language": language[len("jupyter-") :],
                "display_name": display_name or kernel,
            }
            break

    if extra_args := {language: args for language, args in header_args.items() if args}:
        metadata["org_babel"] = {"header_args": extra_args}

    return "".join(body), metadata


def _raise_if_pandoc_is_not_available_for_org() -> None:
    """Raise with an Org-specific error when Pandoc is unavailable."""
    try:
        raise_if_pandoc_is_not_available(min_version="3.4")
    except PandocError as exc:
        raise PandocError(str(exc).replace("Pandoc Markdown format", "Pandoc Org format")) from exc


def _trim_trailing_newline_from_code_cells(notebook) -> None:
    """Trim one trailing newline from each code cell produced by Pandoc."""
    for cell in notebook.cells:
        if cell.cell_type == "code" and cell.source.endswith("\n"):
            cell.source = cell.source[:-1]
