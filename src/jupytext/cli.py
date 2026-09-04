"""`jupytext` as a command line tool"""

import argparse
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import warnings
from copy import copy
from tempfile import NamedTemporaryFile
from typing import Optional

from nbformat.sign import NotebookNotary

from .combine import combine_inputs_with_outputs
from .compare import NotebookDifference, compare, test_round_trip_conversion
from .config import load_jupytext_config, notebook_formats
from .formats import (
    _BINARY_FORMAT_OPTIONS,
    _VALID_FORMAT_OPTIONS,
    JUPYTEXT_FORMATS,
    NOTEBOOK_EXTENSIONS,
    check_auto_ext,
    check_file_version,
    long_form_multiple_formats,
    long_form_one_format,
    short_form_one_format,
)
from .header import recursive_update
from .jupytext import (
    create_prefix_dir,
    get_formats_from_notebook_path,
    read,
    reads,
    write,
    writes,
)
from .kernels import find_kernel_specs, get_kernel_spec, kernelspec_from_language
from .languages import _SCRIPT_EXTENSIONS
from .paired_paths import (
    InconsistentPath,
    base_path,
    find_base_path_and_format,
    full_path,
    paired_paths,
)
from .pairs import latest_inputs_and_outputs
from .sync_pairs import read_pair, write_pair
from .version import __version__


def system(*args, **kwargs):
    """Execute the given bash command"""
    kwargs.setdefault("stdout", subprocess.PIPE)
    proc = subprocess.Popen(args, **kwargs)
    out, _ = proc.communicate()
    if proc.returncode:
        raise SystemExit(proc.returncode)
    return out.decode("utf-8")


def tool_version(tool):
    try:
        args = tool.split(" ")
        args.append("--version")
        return system(*args)
    except (OSError, SystemExit):  # pragma: no cover
        return None


def str2bool(value):
    """Parse Yes/No/Default string
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse"""
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if value.lower() in ("no", "false", "f", "n", "0"):
        return False
    if value.lower() in ("d", "default", ""):
        return None
    raise argparse.ArgumentTypeError("Expected: (Y)es/(T)rue/(N)o/(F)alse/(D)efault")


def parse_jupytext_args(args=None):
    """Command line parser for jupytext"""

    parser = argparse.ArgumentParser(
        description="Jupyter Notebooks as Markdown Documents, Julia, Python or R Scripts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input
    parser.add_argument(
        "notebooks",
        help="One or more notebook(s). Notebook is read from stdin when this argument is empty.",
        nargs="*",
    )
    parser.add_argument(
        "--from",
        dest="input_format",
        help="Jupytext format for the input(s). Inferred from the file extension and content when missing.",
    )
    # Destination format & act on metadata

    selected_file_extensions = ["md", "Rmd", "jl", "py", "R"]
    parser.add_argument(
        "--to",
        dest="output_format",
        help=(
            "The destination format: 'ipynb', 'markdown' or 'script', or a file extension: "
            "'{}', ... or 'auto' (script extension matching the notebook language), "
            "or a combination of an extension and a format name, e.g. {} ".format(
                "', '".join(selected_file_extensions),
                ", ".join({f"md:{fmt.format_name}" for fmt in JUPYTEXT_FORMATS if fmt.extension == ".md"}),
            )
            + " or {}. ".format(", ".join({f"py:{fmt.format_name}" for fmt in JUPYTEXT_FORMATS if fmt.extension == ".py"}))
            + "The default format for scripts is the 'percent' format, "
            "which uses '# %%%%' as cell markers and is compatible with VS Code and PyCharm. "
            "Alternatively, you can also use the 'light' format, which uses fewer cell markers. "
            "The main formats (MyST Markdown, Markdown, percent, light) preserve "
            "notebooks and text documents in a roundtrip. Use the "
            "--test and and --test-strict commands to test the roundtrip on your files. "
            "Read more about the available formats at "
            "https://jupytext.org/formats/scripts/ "
            "NB: in addition to the extensions listed above, you can also use these: '{}'".format(
                "', '".join(
                    sorted(
                        {ext.removeprefix(".") for ext in NOTEBOOK_EXTENSIONS}
                        - set(selected_file_extensions + ["auto", "ipynb"])
                    )
                )
            )
        ),
    )

    # Destination file
    parser.add_argument(
        "-o",
        "--output",
        help="Destination file. Defaults to the original file, "
        "with prefix/suffix/extension changed according to "
        "the destination format. "
        "Use '-' to print the notebook on stdout.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Preserve the output cells when the destination notebook is an .ipynb file that already exists",
    )

    parser.add_argument(
        "--set-formats",
        type=str,
        help="Turn the notebook or text document to one or more alternative representations "
        "with e.g. '--set-formats ipynb,py:light'. "
        "The --set-formats option also triggers the creation/update of all paired files",
    )

    # Action: convert(default)/version/list paired paths/sync/apply/test
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--sync",
        "-s",
        help="Synchronize the content of the paired representations of "
        "the given notebook. Input cells are taken from the file that "
        "was last modified, and outputs are read from the ipynb file, "
        "if present.",
        action="store_true",
    )
    action.add_argument(
        "--paired-paths",
        "-p",
        help="List the locations of the alternative representations for this notebook.",
        action="store_true",
    )
    parser.add_argument(
        "--format-options",
        "--opt",
        action="append",
        help="Set format options with e.g. '--opt comment_magics=true' or '--opt notebook_metadata_filter=-kernelspec'.",
    )
    parser.add_argument(
        "--update-metadata",
        default={},
        type=json.loads,
        help="Update the notebook metadata with the desired dictionary. "
        "Argument must be given in JSON format. For instance, if you "
        "want to activate a pairing in the generated file, use e.g. "
        """--update-metadata '{"jupytext":{"formats":"ipynb,py:light"}}' """
        "See also the --opt and --set-formats options for other ways "
        "to operate on the Jupytext metadata.",
    )
    parser.add_argument(
        "--use-source-timestamp",
        help="Set the modification timestamp of the output file(s) equal"
        "to that of the source file, and keep the source file and "
        "its timestamp unchanged.",
        action="store_true",
    )
    parser.add_argument(
        "--check-source-is-newer",
        help="Check that the file given as argument is the most recent of all paired files, and "
        "if applicable, checks that it is newer than the destination file.",
        action="store_true",
    )
    parser.add_argument(
        "--warn-only",
        "-w",
        action="store_true",
        help="Only issue a warning and continue processing other notebooks when the conversion of a given notebook fails",
    )
    action.add_argument(
        "--test",
        action="store_true",
        help="Test that the notebook is stable under a round trip conversion, up to the expected changes",
    )
    action.add_argument(
        "--test-strict",
        action="store_true",
        help="Test that the notebook is strictly stable under a round trip conversion",
    )
    parser.add_argument(
        "--stop",
        "-x",
        dest="stop_on_first_error",
        action="store_true",
        help="In --test mode, stop on first round trip conversion error, and report stack traceback",
    )

    # Pipe notebook inputs into other commands
    parser.add_argument(
        "--pipe",
        action="append",
        help="Pipe the text representation (in format --pipe-fmt) of the notebook into "
        "another program, and read the notebook back. For instance, reformat "
        "your notebook with: "
        "'jupytext notebook.ipynb --pipe black' "
        "If you want to reformat it and sync the paired representation, execute: "
        "'jupytext notebook.ipynb --sync --pipe black' "
        "In case the program that you want to execute does not accept pipes, use {} "
        "as a placeholder for a temporary file name into which jupytext will "
        "write the text representation of the notebook, e.g.: "
        "jupytext notebook.ipynb --pipe 'black {}'",
    )
    parser.add_argument(
        "--diff",
        "-d",
        action="store_true",
        help="Show the differences between (the inputs) of two notebooks",
    )
    parser.add_argument(
        "--diff-format",
        help="The text format used to show differences in --diff",
    )
    parser.add_argument(
        "--check",
        action="append",
        help="Pipe the text representation (in format --pipe-fmt) of the notebook into "
        "another program, and test that the returned value is non zero. For "
        "instance, test that your notebook is pep8 compliant with: "
        "'jupytext notebook.ipynb --check flake8' "
        "or run pytest on your notebook with: "
        "'jupytext notebook.ipynb --check pytest' "
        "In case the program that you want to execute does not accept pipes, use {} "
        "as a placeholder for a temporary file name into which jupytext will "
        "write the text representation of the notebook, e.g.: "
        "jupytext notebook.ipynb --check 'pytest {}'",
    )
    parser.add_argument(
        "--pipe-fmt",
        default="auto:percent",
        help="The format in which the notebook should be piped to other programs, "
        "when using the --pipe and/or --check commands.",
    )

    # Execute the notebook
    parser.add_argument(
        "--set-kernel",
        "-k",
        type=str,
        help="Set the kernel with the given name on the notebook. "
        "Use '--set-kernel -' to set a kernel matching the current "
        "environment on Python notebooks, and matching the notebook "
        "language otherwise (get the list of available kernels with "
        "'jupyter kernelspec list')",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the notebook with the given kernel. In the "
        "--pre-commit-mode, the notebook is executed only if a code "
        "cell changed, or if some execution outputs are missing "
        "or not ordered.",
    )
    parser.add_argument(
        "--run-path",
        type=str,
        help="Execute the notebook at the given path (defaults to the notebook parent directory)",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode: do not comment about files being updated or created",
    )
    parser.add_argument(
        "--show-changes",
        action="store_true",
        help="Display the diff for each output file",
    )

    action.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show jupytext's version number and exit",
    )

    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help="Ignore the notebook argument, and instead apply Jupytext "
        "on the notebooks found in the git index, which have an "
        "extension that matches the (optional) --from argument.",
    )
    parser.add_argument(
        "--pre-commit-mode",
        action="store_true",
        help="This is a mode that is compatible with the pre-commit framework. "
        "In this mode, --sync won't use timestamp but instead will "
        "determines the source notebook as the element of the pair "
        "that is added to the git index. An alert is raised if multiple inconsistent representations are "
        "in the index. It also raises an alert after updating the paired files or outputs if those "
        "files need to be added to the index. Finally, filepaths that aren't in the source format "
        "you are trying to convert from are ignored.",
    )

    return parser.parse_args(args)


def jupytext(args=None, *, notary=None):
    """Entry point for the jupytext script"""
    args = parse_jupytext_args(args)

    def log(text):
        if not args.quiet:
            sys.stdout.write(text + "\n")

    if args.version:
        log(__version__)
        return 0

    if args.pre_commit:
        warnings.warn(
            "The --pre-commit argument is deprecated. "
            "Please consider switching to the pre-commit.com framework "
            "(let us know at https://github.com/jupytext/jupytext/issues "
            "if that is an issue for you)",
            DeprecationWarning,
        )
        if args.notebooks:
            raise ValueError("--pre-commit takes notebooks from the git index. Do not pass any notebook here.")
        args.notebooks = notebooks_in_git_index(args.input_format)
        log("[jupytext] Notebooks in git index are:")
        for nb_file in args.notebooks:
            log(nb_file)

    # Read notebook from stdin
    if not args.notebooks:
        if not args.pre_commit:
            args.notebooks = ["-"]

    if args.set_formats is not None:
        # Replace empty string with None
        args.update_metadata = recursive_update(args.update_metadata, {"jupytext": {"formats": args.set_formats or None}})
        args.sync = True

    if args.paired_paths:
        if len(args.notebooks) != 1:
            raise ValueError("--paired-paths applies to a single notebook")
        print_paired_paths(args.notebooks[0], args.input_format)
        return 1

    if args.run_path:
        args.execute = True

    if (args.test or args.test_strict) and not args.output_format and not args.output and not args.sync:
        raise ValueError("Please provide one of --to, --output or --sync")

    if (
        not args.output_format
        and not args.output
        and not args.sync
        and not args.pipe
        and not args.diff
        and not args.check
        and not args.update_metadata
        and not args.format_options
        and not args.set_kernel
        and not args.execute
    ):
        raise ValueError(
            "Please provide one of --to, --output, --set-formats, --sync, --pipe, --diff, "
            "--check, --update-metadata, --format-options, --set-kernel or --execute"
        )

    if args.diff:
        if (
            len(args.notebooks) != 2
            or args.output_format
            or args.output
            or args.sync
            or args.pipe
            or args.check
            or args.update_metadata
            or args.format_options
            or args.set_kernel
            or args.execute
        ):
            raise ValueError(
                "Please provide two notebooks after 'jupytext --diff'.\n"
                "NB: Use --show-changes if you wish to see the changes in "
                "a notebook being updated by Jupytext."
            )

        nb_file1, nb_file2 = args.notebooks
        nb1 = read(nb_file1)
        nb2 = read(nb_file2)

        def fmt_if_not_ipynb(nb):
            fmt = nb.metadata["jupytext"]["text_representation"]
            if fmt["extension"] == ".ipynb":
                return None
            return short_form_one_format(fmt)

        diff_fmt = args.diff_format or fmt_if_not_ipynb(nb1) or fmt_if_not_ipynb(nb2) or "md"

        diff = compare(
            writes(nb2, diff_fmt),
            writes(nb1, diff_fmt),
            nb_file2,
            nb_file1,
            return_diff=True,
        )
        sys.stdout.write(diff)

        return

    if args.output and len(args.notebooks) != 1:
        raise ValueError("Please input a single notebook when using --output")

    # Warn if '--to' is used in place of '--output'
    if (
        not args.output
        and args.output_format
        and "." in args.output_format
        # a suffix is expected to start with one of these characters #901
        and not args.output_format.startswith((".", "-", "_"))
        and "//" not in args.output_format
    ):

        def single_line(msg, *args, **kwargs):
            return f"[warning] {msg}\n"

        warnings.formatwarning = single_line
        warnings.warn(
            "You might have passed a file name to the '--to' option, "
            "when a format description was expected. Maybe you want to use the '-o' option instead?"
        )

    if args.input_format:
        args.input_format = long_form_one_format(args.input_format)

    if args.output_format:
        args.output_format = long_form_one_format(args.output_format)
        set_format_options(args.output_format, args.format_options)

    # Wildcard extension on Windows #202
    notebooks = []
    for pattern in args.notebooks:
        if "*" in pattern or "?" in pattern:
            # Exclude the .jupytext.py configuration file
            notebooks.extend(glob.glob(pattern, recursive=True))
        else:
            notebooks.append(pattern)

    if os.sep == "\\":
        notebooks = [path.replace("\\", "/") for path in notebooks]

    # Count how many files have round-trip issues when testing
    exit_code = 0

    notary_to_close = None
    if notary is None:
        notary = notary_to_close = NotebookNotary()

    try:
        for nb_file in notebooks:
            if not args.warn_only:
                exit_code += jupytext_single_file(nb_file, args, log, notary=notary)
            else:
                try:
                    exit_code += jupytext_single_file(nb_file, args, log, notary=notary)
                except Exception as err:
                    sys.stderr.write(f"[jupytext] Error: {str(err)}\n")

        return exit_code
    finally:
        if notary_to_close:
            notary_to_close.store.close()


def jupytext_single_file(nb_file, args, log, notary):
    """Apply the jupytext command, with given arguments, to a single file"""
    if nb_file == "-" and args.sync:
        msg = "Missing notebook path."
        if args.set_formats is not None and os.path.isfile(args.set_formats):
            msg += f" Did you mean 'jupytext --sync {args.set_formats}' ?"
        raise ValueError(msg)

    nb_dest = None
    if args.output:
        nb_dest = args.output
    elif nb_file == "-":
        nb_dest = "-"
    else:
        try:
            bp = base_path(nb_file, args.input_format)
        except InconsistentPath:
            if args.pre_commit_mode:
                log(
                    "[jupytext] Ignoring unmatched input path {}{}".format(
                        nb_file,
                        f" for format {args.input_format}" if args.input_format else "",
                    )
                )
                return 0
            raise
        if args.output_format:
            nb_dest = full_path(bp, args.output_format)

    config = load_jupytext_config(os.path.abspath(nb_file))

    def _read(path, fmt=None):
        """Read a notebook; mark cells trusted when the signature is valid."""
        nb = read(path, fmt=fmt, config=config)
        if notary.check_signature(nb):
            notary.mark_cells(nb, True)
        return nb

    def _writes(nb, fmt):
        """Serialize a notebook; sign the result when every cell is trusted."""
        content = writes(nb, fmt=fmt, config=config)
        if notary.check_cells(nb):
            notary.sign(reads(content, fmt=fmt, config=config))
        else:
            log("[jupytext] Warning: Notebook is not trusted")
        return content

    # Just acting on metadata / pipe => save in place
    save_in_place = not nb_dest and not args.sync
    if save_in_place:
        nb_dest = nb_file

    if nb_dest == "-":
        args.quiet = True

    # I. ### Read the notebook ###
    fmt = copy(args.input_format) or {}
    if not fmt:
        ext = os.path.splitext(nb_file)[1]
        if ext:
            fmt = {"extension": ext}
    if fmt:
        set_format_options(fmt, args.format_options)
    log(
        "[jupytext] Reading {}{}".format(
            nb_file if nb_file != "-" else "stdin",
            f" in format {short_form_one_format(fmt)}" if "extension" in fmt else "",
        )
    )

    timestamp_checker = TimestampChecker(pre_commit_mode=args.pre_commit_mode)
    timestamp_checker.get_and_check_timestamp(nb_file)
    notebook = _read(nb_file, fmt=fmt)

    if "extension" in fmt and "format_name" not in fmt:
        text_representation = notebook.metadata.get("jupytext", {}).get("text_representation", {})
        if text_representation.get("extension") == fmt["extension"]:
            fmt["format_name"] = text_representation["format_name"]

    # Compute actual extension when using script/auto, and update nb_dest if necessary
    dest_fmt = args.output_format
    if dest_fmt and dest_fmt["extension"] == ".auto":
        dest_fmt = check_auto_ext(dest_fmt, notebook.metadata, "--to")
        if not args.output and nb_file != "-":
            nb_dest = full_path(base_path(nb_file, args.input_format), dest_fmt)

    # Set the kernel
    set_kernel = args.set_kernel
    if (not set_kernel) and args.execute and notebook.metadata.get("kernelspec", {}).get("name") is None:
        set_kernel = "-"

    if set_kernel:
        if set_kernel == "-":
            language = (
                notebook.metadata.get("jupytext", {}).get("main_language") or notebook.metadata["kernelspec"]["language"]
            )

            if not language:
                raise ValueError("Cannot infer a kernel as notebook language is not defined")

            kernelspec = kernelspec_from_language(language)
        else:
            try:
                kernelspec = get_kernel_spec(set_kernel)
            except KeyError as err:
                raise KeyError(f"Please choose a kernel name among {find_kernel_specs().keys()}") from err

            kernelspec = {
                "name": args.set_kernel,
                "language": kernelspec.language,
                "display_name": kernelspec.display_name,
            }

        log("[jupytext] Setting kernel {}".format(kernelspec.get("name")))
        args.update_metadata["kernelspec"] = kernelspec

    # Read paired notebooks
    nb_files = [nb_file, nb_dest]
    outputs_nb_file = None
    if args.sync:
        # If we are also setting the formats, we take the information
        # from the --set-formats option
        if args.set_formats is not None:
            formats = long_form_multiple_formats(args.set_formats)
        else:
            formats = notebook_formats(notebook, config, nb_file, fallback_on_current_fmt=False)
        set_prefix_and_suffix(fmt, formats, nb_file)

        try:
            notebook, inputs_nb_file, outputs_nb_file = load_paired_notebook(
                notebook,
                fmt,
                config,
                formats,
                nb_file,
                log,
                args.pre_commit_mode,
                timestamp_checker,
                read_func=_read,
            )
            nb_files = [inputs_nb_file, outputs_nb_file]
        except NotAPairedNotebook as err:
            sys.stderr.write("[jupytext] Warning: " + str(err) + "\n")
            return 0
        except InconsistentVersions as err:
            sys.stderr.write("[jupytext] Error: " + str(err) + "\n")
            return 1

    # Are we updating a text file that has a metadata filter? #212
    if args.update_metadata or args.format_options:
        if notebook.metadata.get("jupytext", {}).get("notebook_metadata_filter") == "-all":
            notebook.metadata.get("jupytext", {}).pop("notebook_metadata_filter")

    # Update the metadata
    if args.update_metadata:
        log(f"[jupytext] Updating notebook metadata with '{json.dumps(args.update_metadata)}'")

        if "kernelspec" in args.update_metadata and "main_language" in notebook.metadata.get("jupytext", {}):
            notebook.metadata["jupytext"].pop("main_language")

        recursive_update(notebook.metadata, args.update_metadata)

    # II. ### Apply commands onto the notebook ###
    # Pipe the notebook into the desired commands
    if nb_file == "-":
        prefix = None
        directory = None
    else:
        prefix = os.path.splitext(os.path.basename(nb_file))[0]
        directory = os.path.dirname(nb_file)
    for cmd in args.pipe or []:
        notebook = pipe_notebook(
            notebook,
            cmd,
            args.pipe_fmt,
            quiet=args.quiet,
            prefix=prefix,
            directory=directory,
            warn_only=args.warn_only,
        )

    # and/or test the desired commands onto the notebook
    for cmd in args.check or []:
        pipe_notebook(
            notebook,
            cmd,
            args.pipe_fmt,
            update=False,
            quiet=args.quiet,
            prefix=prefix,
            directory=directory,
            warn_only=args.warn_only,
        )

    if (
        args.execute
        and args.pre_commit_mode
        and execution_counts_are_in_order(notebook)
        and not code_cells_have_changed(notebook, nb_files)
    ):
        log(f"[jupytext] Execution of {shlex.quote(nb_file)} skipped as code cells have not changed and outputs are present.")
        args.execute = False

    # Execute the notebook
    if args.execute:
        kernel_name = notebook.metadata.get("kernelspec", {}).get("name")
        log(f"[jupytext] Executing notebook with kernel {kernel_name}")

        if nb_dest is not None and nb_dest != "-":
            nb_path = os.path.dirname(nb_dest)
        elif nb_file != "-":
            nb_path = os.path.dirname(nb_file)
        else:
            nb_path = None

        run_path = args.run_path or nb_path
        if args.run_path and not os.path.isdir(run_path):
            # is this a relative directory?
            for base_dir in [nb_path, os.getcwd()]:
                try_path = os.path.join(base_dir, run_path)
                if os.path.isdir(try_path):
                    run_path = try_path
                    break
            if not os.path.isdir(run_path):
                raise ValueError(f"--run-path={args.run_path} is not a valid path")

        if run_path:
            resources = {"metadata": {"path": run_path}}
        else:
            resources = {}

        try:
            from nbconvert.preprocessors import ExecutePreprocessor

            exec_proc = ExecutePreprocessor(timeout=None, kernel_name=kernel_name)
            exec_proc.preprocess(notebook, resources=resources)
        except (ImportError, RuntimeError) as err:
            if args.pre_commit_mode:
                raise RuntimeError(
                    "An error occurred while executing the notebook. Please "
                    "make sure that you have listed 'nbconvert' and 'ipykernel' "
                    "under 'additional_dependencies' in the jupytext hook."
                ) from err
            raise RuntimeError(
                "An error occurred while executing the notebook. Please "
                "make sure that 'nbconvert' and 'ipykernel' are installed."
            ) from err

    # III. ### Possible actions ###
    # a. Test round trip conversion
    if args.test or args.test_strict:
        try:
            # Round trip from an ipynb document
            if fmt["extension"] == ".ipynb":
                test_round_trip_conversion(
                    notebook,
                    dest_fmt,
                    update=args.update,
                    allow_expected_differences=not args.test_strict,
                    stop_on_first_error=args.stop_on_first_error,
                )

            # Round trip from a text file
            else:
                # We read the original text from disk a second time
                with open(nb_file, encoding="utf-8") as fp:
                    org_text = fp.read()

                # We also make sure that the text file
                # has not changed since we first read it!
                timestamp_checker.check_timestamp(nb_file)

                # If the destination is not ipynb, we convert to/back that format
                if dest_fmt["extension"] != ".ipynb":
                    dest_text = writes(notebook, fmt=dest_fmt)
                    notebook = reads(dest_text, fmt=dest_fmt)

                text = writes(notebook, fmt=fmt, config=config)

                if args.test_strict:
                    compare(text, org_text)
                else:
                    # we ignore the YAML header in the comparison #414
                    comment = _SCRIPT_EXTENSIONS.get(fmt["extension"], {}).get("comment", "")
                    # white spaces between the comment char and the YAML delimiters are allowed
                    if comment:
                        comment = comment + r"\s*"
                    yaml_header = re.compile(
                        r"^{comment}---\s*\n.*\n{comment}---\s*\n".format(comment=comment),
                        re.MULTILINE | re.DOTALL,
                    )
                    compare(re.sub(yaml_header, "", text), re.sub(yaml_header, "", org_text))

        except (NotebookDifference, AssertionError) as err:
            sys.stdout.write(f"{nb_file}: {str(err)}")
            return 1
        return 0

    # b. Output to the desired file or format
    untracked_files = 0

    def lazy_write(
        path,
        fmt=None,
        action=None,
        update_timestamp_only=False,
        force_update_timestamp=False,
    ):
        """Write the notebook only if it has changed"""
        # Used in tests only
        if _callback_on_lazy_write is not None:
            _callback_on_lazy_write(path)
        if path == "-":
            timestamp_checker.check_all_timestamps()
            write(notebook, "-", fmt=fmt)
            return

        nonlocal untracked_files
        if update_timestamp_only:
            modified = False
        else:
            _, ext = os.path.splitext(path)
            fmt = copy(fmt or {})
            fmt = long_form_one_format(fmt, update={"extension": ext})
            new_content = _writes(notebook, fmt=fmt)
            diff = None
            if not new_content.endswith("\n"):
                new_content += "\n"
            if not os.path.isfile(path):
                modified = True
                diff = "(file did not exist)"
            else:
                # We load the current file from disk
                # NB: in the --to mode, it might be the first
                # time we actually read this file
                timestamp_checker.get_and_check_timestamp(path)
                with open(path, encoding="utf-8") as fp:
                    current_content = fp.read()

                timestamp_checker.check_timestamp(path)

                modified = new_content != current_content
                if modified and args.show_changes:
                    diff = compare(
                        new_content,
                        current_content,
                        "",
                        "",
                        return_diff=True,
                    )

        tmp_path = path
        if modified:
            # The text representation of the notebook has changed, we write it on disk
            create_prefix_dir(path, fmt, log)
            # Create a temporary file in the same directory as path. Later on we will move
            # that temporary file back to path (os.replace is atomic on most OS)
            name, ext = os.path.splitext(path)
            tmp_path = name + f"_tmp_jupytext_{os.getpid()}" + ext
            with open(tmp_path, "w", encoding="utf-8") as fp:
                fp.write(new_content)

        # We check that none of the input files changed while we were
        # doing our processing. If they did, we abort as we would
        # otherwise overwrite the modifications.
        try:
            timestamp_checker.check_all_timestamps()
        except SynchronousModificationError:
            if modified:
                os.remove(tmp_path)
            raise

        # When the content is unchanged, we still need to update the timestamp of
        # the text file to make sure they remain more recent than the ipynb file, for compatibility with the
        # Jupytext contents manager for Jupyter
        if args.use_source_timestamp:
            if tmp_path != nb_file:
                log(f"[jupytext] Setting the timestamp of {shlex.quote(path)} equal to that of {shlex.quote(nb_file)}")
                os.utime(tmp_path, (os.stat(nb_file).st_atime, os.stat(nb_file).st_mtime))
        elif not modified:
            if path.endswith(".ipynb"):
                # No need to update the timestamp of ipynb files
                log(f"[jupytext] Unchanged {shlex.quote(path)}")
            elif args.sync and not force_update_timestamp:
                # if the content is unchanged (and matches ipynb), we don't need
                # to update the timestamp as the contents manager will not throw in
                # that case (see the try/catch on read_pair(... must_match=True))
                log(f"[jupytext] Unchanged {shlex.quote(path)}")
            else:
                log(f"[jupytext] Updating the timestamp of {shlex.quote(path)}")
                os.utime(path, None)

        if modified:
            if action is None:
                message = f"[jupytext] Updating {shlex.quote(path)}"
            else:
                message = "[jupytext] Writing {path}{format}{action}".format(
                    path=shlex.quote(path),
                    format=(" in format " + short_form_one_format(fmt) if fmt and "format_name" in fmt else ""),
                    action=action,
                )
            if args.show_changes:
                message += " with this change:\n" + diff

            log(message)
            os.replace(tmp_path, path)

        # If we changed the file timestamp, we update our checker accordingly
        if modified or args.use_source_timestamp or force_update_timestamp:
            timestamp_checker.update_timestamp(path)

        if args.pre_commit:
            system("git", "add", path)

        if args.pre_commit_mode and is_untracked(path):
            log(
                f"[jupytext] Error: the git index is outdated.\n"
                f"Please add the paired notebook with:\n"
                f"    git add {shlex.quote(path)}"
            )
            untracked_files += 1

        return {"modified": modified}

    if nb_dest:
        if args.check_source_is_newer:
            ts_src = timestamp_checker.check_file_is_newest(nb_file)
            ts_dest = timestamp_checker.get_and_check_timestamp(nb_dest)
            if ts_dest is not None and ts_dest > ts_src:
                raise ValueError(f"Source {nb_file} is older than destination {nb_dest}")

        if nb_dest == nb_file and not dest_fmt:
            dest_fmt = fmt

        # Test consistency between dest name and output format
        if dest_fmt and nb_dest != "-":
            base_path(nb_dest, dest_fmt)

        # Describe what jupytext is doing
        if save_in_place:
            action = ""
        elif os.path.isfile(nb_dest) and args.update:
            if not nb_dest.endswith(".ipynb"):
                raise ValueError("--update is only for ipynb files")
            action = " (destination file updated)"
            check_file_version(notebook, nb_file, nb_dest)
            notebook = combine_inputs_with_outputs(notebook, read(nb_dest), fmt=fmt)
        elif os.path.isfile(nb_dest):
            suggest_update = " [use --update to preserve cell outputs and ids]" if nb_dest.endswith(".ipynb") else ""
            action = f" (destination file replaced{suggest_update})"
        else:
            action = ""

        formats = notebook.metadata.get("jupytext", {}).get("formats")
        formats = long_form_multiple_formats(formats)
        if formats:
            try:
                base_path_out, _ = find_base_path_and_format(nb_dest, formats)
            except InconsistentPath:
                # Drop 'formats' if the destination is not part of the paired notebooks
                formats = {}
                notebook.metadata.get("jupytext", {}).pop("formats")

        lazy_write(nb_dest, fmt=dest_fmt, action=action)

        nb_dest_in_pair = formats and any(
            os.path.exists(alt_path) and os.path.samefile(nb_dest, alt_path)
            for alt_path, _ in paired_paths(nb_file, fmt, formats)
        )

        if (
            nb_dest_in_pair
            and os.path.isfile(nb_file)
            and not nb_file.endswith(".ipynb")
            and os.path.isfile(nb_dest)
            and nb_dest.endswith(".ipynb")
        ):
            # If the destination is an ipynb file and is in the pair, then we
            # update the original text file timestamp, as required by our Content Manager
            # Otherwise Jupyter will refuse to open the paired notebook #335
            # NB: An alternative is --use-source-timestamp
            lazy_write(nb_file, update_timestamp_only=True)

    # c. Synchronize paired notebooks
    elif args.sync:
        if args.check_source_is_newer:
            timestamp_checker.check_file_is_newest(nb_file)
        write_pair(nb_file, formats, lazy_write)

    return untracked_files


def notebooks_in_git_index(fmt):
    """Return the list of modified and deleted ipynb files in the git index that match the given format"""
    git_status = system("git", "status", "--porcelain")
    re_modified = re.compile(r"^[AM]+\s+(?P<name>.*)", re.MULTILINE)
    modified_files_in_git_index = re_modified.findall(git_status)
    files = []
    for nb_file in modified_files_in_git_index:
        if nb_file.startswith('"') and nb_file.endswith('"'):
            nb_file = nb_file[1:-1]
        try:
            base_path(nb_file, fmt)
            files.append(nb_file)
        except InconsistentPath:
            continue
    return files


def is_untracked(filepath):
    """Check whether a file was created or modified and needs to be added to the git index"""
    if not filepath:
        return False

    output = system("git", "ls-files", filepath).strip()
    if output == "":
        return True

    output = system("git", "diff", filepath).strip()
    if output != "":
        return True

    return False


def print_paired_paths(nb_file, fmt):
    """Display the paired paths for this notebook"""
    formats = get_formats_from_notebook_path(nb_file, fmt)
    if formats:
        for path, _ in paired_paths(nb_file, fmt, formats):
            if path != nb_file:
                sys.stdout.write(path + "\n")


def set_format_options(fmt, format_options):
    """Apply the desired format options to the format description fmt"""
    if not format_options:
        return

    for opt in format_options:
        try:
            key, value = opt.split("=")
        except ValueError as err:
            raise ValueError(f"Format options are expected to be of the form key=value, not '{opt}'") from err

        if key not in _VALID_FORMAT_OPTIONS:
            raise ValueError(
                "'{}' is not a valid format option. Expected one of '{}'".format(key, "', '".join(_VALID_FORMAT_OPTIONS))
            )

        if key in _BINARY_FORMAT_OPTIONS:
            value = str2bool(value)

        fmt[key] = value


def set_prefix_and_suffix(fmt, formats, nb_file):
    """Add prefix and suffix information from jupytext.formats if format and path matches"""
    for alt_fmt in long_form_multiple_formats(formats):
        if alt_fmt["extension"] == fmt["extension"] and fmt.get("format_name") == alt_fmt.get("format_name"):
            try:
                base_path(nb_file, alt_fmt)
                fmt.update(alt_fmt)
                return
            except InconsistentPath:
                continue


class NotAPairedNotebook(ValueError):
    """An error raised when a notebook is not a paired notebook"""


class InconsistentVersions(ValueError):
    """An error raised when two paired files in the git index contain inconsistent representations"""


def file_in_git_index(path):
    if not os.path.isfile(path):
        return False
    return system("git", "status", "--porcelain", path).strip().startswith(("M", "A"))


def git_timestamp(path):
    if not os.path.isfile(path):
        return None

    # Files that are in the git index are considered most recent
    if file_in_git_index(path):
        return float("inf")

    # Return the commit timestamp
    try:
        git_ts_str = system("git", "log", "-1", "--pretty=%ct", "--no-show-signature", path).strip()
    except SystemExit as err:
        if err.code == 128:
            # git not initialized
            git_ts_str = ""
        else:
            raise

    if git_ts_str:
        return float(git_ts_str)

    # The file is not in the git index
    return get_timestamp(path)


def get_timestamp(path: str) -> Optional[float]:
    if not os.path.isfile(path):
        return None
    return os.stat(path).st_mtime


class SynchronousModificationError(OSError):
    """An error raised when a file was modified while Jupytext was running"""


class TimestampChecker:
    """
    This class keeps track of the timestamps of files that have been used by Jupytext
    when loading a paired notebook. Either the timestamp of each file was consulted to
    identify the most recent input file, or its content was read.
    """

    def __init__(self, pre_commit_mode: bool = False):
        self.pre_commit_mode = pre_commit_mode
        self._timestamps: dict[str, Optional[float]] = {}

    def get_and_check_timestamp(self, path: str) -> Optional[float]:
        if path in self._timestamps:
            ts = self.check_timestamp(path)
        else:
            ts = get_timestamp(path)
            self._timestamps[path] = ts

        if self.pre_commit_mode:
            return git_timestamp(path)

        return ts

    def check_timestamp(self, path: str) -> Optional[float]:
        if path not in self._timestamps:
            raise ValueError(
                f"The timestamp of {shlex.quote(path)} was not previously recorded. So far Jupytext has only recorded timestamps for {', '.join(shlex.quote(p) for p in self._timestamps)}"
            )

        ts = get_timestamp(path)
        old_ts = self._timestamps[path]
        if old_ts is None and ts is not None:
            raise SynchronousModificationError(f"The file {shlex.quote(path)} was created while Jupytext was running")
        if old_ts is not None and ts is None:
            raise SynchronousModificationError(f"The file {shlex.quote(path)} was deleted while Jupytext was running")
        if ts != old_ts:
            raise SynchronousModificationError(f"The file {shlex.quote(path)} was modified while Jupytext was running")

        return ts

    def update_timestamp(self, path: str):
        ts = get_timestamp(path)
        if ts is None:
            raise FileNotFoundError(f"The file {shlex.quote(path)} does not exist")
        self._timestamps[path] = ts

    def check_all_timestamps(self):
        for path in self._timestamps:
            self.check_timestamp(path)

    def check_file_is_newest(self, path: str) -> Optional[float]:
        """Check that the given file is the most recent among all files whose timestamp
        was recorded by this TimestampChecker. Return its timestamp."""
        ts = self._timestamps[path]
        assert ts is not None, f"The timestamp of {shlex.quote(path)} was not previously recorded"
        for p, p_ts in self._timestamps.items():
            if p == path or p_ts is None:
                continue
            if p_ts > ts:
                raise ValueError(f"Source {shlex.quote(path)} is older than paired file {shlex.quote(p)}")
        return ts


# If not none, this function is called with the path of each file
# that Jupytext CLI considers to write back (to be used in tests)
_callback_on_lazy_write = None


def load_paired_notebook(
    notebook,
    fmt,
    config,
    formats,
    nb_file,
    log,
    pre_commit_mode: bool,
    timestamp_checker: TimestampChecker,
    read_func,
):
    """Update the notebook with the inputs and outputs of the most recent paired files"""
    if not formats:
        raise NotAPairedNotebook(f"{shlex.quote(nb_file)} is not a paired notebook")

    formats = long_form_multiple_formats(formats)
    _, fmt_with_prefix_suffix = find_base_path_and_format(nb_file, formats)
    fmt.update(fmt_with_prefix_suffix)

    def read_one_file(path, fmt):
        if path == nb_file:
            return notebook

        log(f"[jupytext] Loading {shlex.quote(path)}")
        timestamp_checker.get_and_check_timestamp(path)
        return read_func(path, fmt=fmt)

    if pre_commit_mode and file_in_git_index(nb_file):
        # We raise an error if two representations of this notebook in the git index are inconsistent
        nb_files_in_git_index = sorted(
            ((alt_path, alt_fmt) for alt_path, alt_fmt in paired_paths(nb_file, fmt, formats) if file_in_git_index(alt_path)),
            key=lambda x: 0 if x[1]["extension"] != ".ipynb" else 1,
        )

        if len(nb_files_in_git_index) > 1:
            path0, fmt0 = nb_files_in_git_index[0]
            timestamp_checker.get_and_check_timestamp(path0)
            with open(path0, encoding="utf-8") as fp:
                text0 = fp.read()
            for alt_path, alt_fmt in nb_files_in_git_index[1:]:
                timestamp_checker.get_and_check_timestamp(alt_path)
                nb = read(alt_path, fmt=alt_fmt, config=config)
                alt_text = writes(nb, fmt=fmt0, config=config)
                if alt_text != text0:
                    diff = compare(alt_text, text0, alt_path, path0, return_diff=True)
                    raise InconsistentVersions(
                        f"{shlex.quote(alt_path)} and {shlex.quote(path0)} are inconsistent.\n"
                        + diff
                        + f"\nPlease revert JUST ONE of the files with EITHER\n"
                        f"    git reset {shlex.quote(alt_path)} && git checkout -- {shlex.quote(alt_path)}\nOR\n"
                        f"    git reset {shlex.quote(path0)} && git checkout -- {shlex.quote(path0)}\n"
                    )

    inputs, outputs = latest_inputs_and_outputs(nb_file, fmt, formats, timestamp_checker.get_and_check_timestamp)
    notebook = read_pair(inputs, outputs, read_one_file)

    return notebook, inputs.path, outputs.path


def exec_command(command, input=None, capture=False, warn_only=False, quiet=False):
    """Execute the desired command, and pipe the given input into it"""
    assert isinstance(command, list)
    if not quiet:
        sys.stdout.write("[jupytext] Executing {}\n".format(" ".join(command)))
    process = subprocess.Popen(
        command,
        **(dict(stdout=subprocess.PIPE, stdin=subprocess.PIPE) if input is not None else {}),
    )
    out, err = process.communicate(input=input)
    if out and not capture and not quiet:
        sys.stdout.write(out.decode("utf-8"))
    if err:
        sys.stderr.write(err.decode("utf-8"))

    if process.returncode:
        msg = f"The command '{' '.join(command)}' exited with code {process.returncode}"
        hint = "" if warn_only else " (use --warn-only to turn this error into a warning)"
        sys.stderr.write(f"[jupytext] {'Warning' if warn_only else 'Error'}: {msg}{hint}\n")
        if not warn_only:
            raise SystemExit(process.returncode)

    return out


def pipe_notebook(
    notebook,
    command,
    fmt="py:percent",
    update=True,
    quiet=False,
    prefix=None,
    directory=None,
    warn_only=False,
):
    """Pipe the notebook, in the desired representation, to the given command. Update the notebook
    with the returned content if desired."""
    if command in ["black", "flake8", "autopep8"]:
        command = command + " -"
    elif command in ["pytest", "unittest"]:
        command = command + " {}"

    fmt = long_form_one_format(fmt, notebook.metadata, auto_ext_requires_language_info=False)
    fmt = check_auto_ext(fmt, notebook.metadata, "--pipe-fmt")
    text = writes(notebook, fmt)

    command = shlex.split(command)
    if "{}" in command:
        if prefix is not None:
            prefix = prefix + "-"
        tmp_file_args = dict(
            mode="w+",
            encoding="utf8",
            prefix=prefix,
            suffix=fmt["extension"],
            dir=directory,
            delete=False,
        )
        try:
            tmp = NamedTemporaryFile(**tmp_file_args)
        except TypeError:
            # NamedTemporaryFile does not have an 'encoding' argument on pypy
            tmp_file_args.pop("encoding")
            tmp = NamedTemporaryFile(**tmp_file_args)
        try:
            tmp.write(text)
            tmp.close()

            exec_command(
                [cmd if cmd != "{}" else tmp.name for cmd in command],
                capture=update,
                quiet=quiet,
                warn_only=warn_only,
            )

            if not update:
                return notebook

            piped_notebook = read(tmp.name, fmt=fmt)
        finally:
            os.remove(tmp.name)
    else:
        cmd_output = exec_command(
            command,
            text.encode("utf-8"),
            capture=update,
            warn_only=warn_only,
            quiet=quiet,
        )

        if not update:
            return notebook

        if not cmd_output:
            sys.stderr.write(
                "[jupytext] The command '{}' had no output. As a result, the notebook is empty. "
                "Is this expected? If not, use --check rather than --pipe for this command.".format(command)
            )

        piped_notebook = reads(cmd_output.decode("utf-8"), fmt)

    if fmt["extension"] != ".ipynb":
        piped_notebook = combine_inputs_with_outputs(piped_notebook, notebook, fmt)

    # Remove jupytext / text_representation entry
    if "jupytext" in notebook.metadata:
        piped_notebook.metadata["jupytext"] = notebook.metadata["jupytext"]
    else:
        piped_notebook.metadata.pop("jupytext", None)

    return piped_notebook


def execution_counts_are_in_order(notebook):
    """Returns True if all the code cells have an execution count, ordered from 1 to N with no missing number"""
    expected_execution_count = 1
    for cell in notebook.cells:
        if cell.cell_type == "code":
            if cell.execution_count != expected_execution_count:
                return False
            expected_execution_count += 1
    return True


def code_cells_have_changed(notebook, nb_files):
    """The source for the code cells has not changed"""
    for nb_file in nb_files:
        if not os.path.exists(nb_file):
            return True

        nb_ref = read(nb_file)

        # Are the new code cells equals to those in the file?
        ref = [cell.source for cell in nb_ref.cells if cell.cell_type == "code"]
        new = [cell.source for cell in notebook.cells if cell.cell_type == "code"]

        if ref != new:
            return True

    return False
