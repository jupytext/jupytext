"""
This module exposes the AsyncTextFileContentsManager that allows to open
text files as notebooks
"""

import inspect
import itertools
import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from collections import namedtuple
from datetime import timedelta

import nbformat
from tornado.web import HTTPError

from .async_pairs import read_pair, write_pair
from .config import (
    JUPYTEXT_CONFIG_FILES,
    PYPROJECT_FILE,
    JupytextConfiguration,
    JupytextConfigurationError,
    find_global_jupytext_configuration_file,
    load_jupytext_configuration_file,
    notebook_formats,
    preferred_format,
)
from .formats import (
    long_form_multiple_formats,
    short_form_multiple_formats,
    short_form_one_format,
)
from .jupytext import drop_text_representation_metadata, reads, writes
from .kernels import set_kernelspec_from_language
from .paired_paths import (
    InconsistentPath,
    base_path,
    base_path_and_adjusted_fmt,
    find_base_path_and_format,
    full_path,
    paired_paths,
)
from .pairs import PairedFilesDiffer, latest_inputs_and_outputs


def build_async_jupytext_contents_manager_class(base_contents_manager_class):
    """
    Derives an asynchronous TextFileContentsManager class from the given base class,
    which is supposed to be asynchronous too.
    """

    class AsyncJupytextContentsManager(base_contents_manager_class, JupytextConfiguration):
        """
        A FileContentsManager Class that reads and stores notebooks to classical
        Jupyter notebooks (.ipynb), R Markdown notebooks (.Rmd), Julia (.jl),
        Python (.py) or R scripts (.R)
        """

        def __init__(self, *args, **kwargs):
            # Dictionary: notebook path => (fmt, formats) where
            # fmt is the current format, and formats the paired formats.
            self.paired_notebooks = dict()

            # Configuration cache, useful when notebooks are listed in a given directory
            self.cached_config = namedtuple("cached_config", "path config_file config")
            self.super = super()
            self.super.__init__(*args, **kwargs)

        def all_nb_extensions(self, config):
            """All extensions that should be classified as notebooks"""
            return [ext if ext.startswith(".") else "." + ext for ext in config.notebook_extensions]

        def drop_paired_notebook(self, path):
            """Remove the current notebook from the list of paired notebooks"""
            if path not in self.paired_notebooks:
                return

            fmt, formats = self.paired_notebooks.pop(path)
            prev_paired_paths = paired_paths(path, fmt, formats)
            for alt_path, _ in prev_paired_paths:
                if alt_path in self.paired_notebooks:
                    self.drop_paired_notebook(alt_path)

        def update_paired_notebooks(self, path, formats):
            """Update the list of paired notebooks to include/update the current pair"""
            if not formats:
                self.drop_paired_notebook(path)
                return

            formats = long_form_multiple_formats(formats)
            _, fmt = find_base_path_and_format(path, formats)
            new_paired_paths = paired_paths(path, fmt, formats)
            for alt_path, _ in new_paired_paths:
                self.drop_paired_notebook(alt_path)

            if len(formats) == 1 and set(formats[0]) <= {"extension"}:
                return

            short_formats = short_form_multiple_formats(formats)
            for alt_path, alt_fmt in new_paired_paths:
                self.paired_notebooks[alt_path] = (
                    short_form_one_format(alt_fmt),
                    short_formats,
                )

        async def create_prefix_dir(self, path, fmt):
            """Create the prefix dir, if missing"""
            if "prefix" in fmt and "/" in path:
                parent_dir = self.get_parent_dir(path)
                if not await self.dir_exists(parent_dir):
                    await self.create_prefix_dir(parent_dir, fmt)
                    self.log.info("Creating directory %s", parent_dir)
                    await self.super.save(dict(type="directory"), parent_dir)

        async def save(self, model, path=""):
            """Save the file model and return the model with no content."""
            if model["type"] != "notebook":
                return await self.super.save(model, path)

            path = path.strip("/")
            nbk = model["content"]
            try:
                config = await self.get_config(path)
                jupytext_formats = notebook_formats(nbk, config, path)
                _, jupytext_formats = self._drop_formats_if_they_dont_match_path(path, None, jupytext_formats)
                self.update_paired_notebooks(path, jupytext_formats)

                async def save_one_file(path, fmt):
                    if "format_name" in fmt and fmt["extension"] not in [
                        ".md",
                        ".markdown",
                        ".Rmd",
                    ]:
                        self.log.info(
                            "Saving %s in format %s:%s",
                            os.path.basename(path),
                            fmt["extension"][1:],
                            fmt["format_name"],
                        )
                    else:
                        self.log.info("Saving %s", os.path.basename(path))

                    await self.create_prefix_dir(path, fmt)
                    if fmt["extension"] == ".ipynb":
                        return await self.super.save(
                            dict(
                                type="notebook",
                                content=drop_text_representation_metadata(model["content"]),
                            ),
                            path,
                        )

                    if model["content"]["metadata"].get("jupytext", {}).get("notebook_metadata_filter") == "-all":
                        self.log.warning(
                            "Stripping metadata from {} as 'Include Metadata' is off "
                            "(toggle 'Include Metadata' in the Jupytext Menu or Commands if desired)".format(path)
                        )

                    text_model = dict(
                        type="file",
                        format="text",
                        content=writes(nbformat.from_dict(model["content"]), fmt=fmt, config=config),
                    )

                    return await self.super.save(text_model, path)

                return await write_pair(path, jupytext_formats, save_one_file)

            except Exception as e:
                self.log.error("Error while saving file: %s %s", path, e, exc_info=True)
                raise HTTPError(500, f"Unexpected error while saving file: {path} {e}")

        async def _get_with_no_require_hash_argument(
            self,
            path,
            content=True,
            type=None,
            format=None,
            load_alternative_format=True,
        ):
            return await self._get_with_require_hash_argument(
                path,
                content=content,
                type=type,
                format=format,
                require_hash=False,
                load_alternative_format=load_alternative_format,
            )

        async def _get_with_require_hash_argument(
            self,
            path,
            content=True,
            type=None,
            format=None,
            require_hash=False,
            load_alternative_format=True,
        ):
            """Takes a path for an entity and returns its model"""
            path = path.strip("/")
            ext = os.path.splitext(path)[1]

            super_kwargs = {"content": content, "type": type, "format": format}
            if require_hash:
                super_kwargs["require_hash"] = require_hash

            # Not a notebook?
            if not await self.file_exists(path) or await self.dir_exists(path) or (type is not None and type != "notebook"):
                return await self.super.get(path, **super_kwargs)

            config = await self.get_config(path, use_cache=content is False)
            if ext not in self.all_nb_extensions(config):
                return await self.super.get(path, **super_kwargs)

            fmt = preferred_format(ext, config.preferred_jupytext_formats_read)
            if ext == ".ipynb":
                super_kwargs["type"] = "notebook"
                model = await self.super.get(path, **super_kwargs)
            else:
                super_kwargs["type"] = "file"
                super_kwargs["format"] = "text"
                model = await self.super.get(path, **super_kwargs)
                model["type"] = "notebook"
                if content:
                    # We may need to update these keys, inherited from text files formats
                    # Cf. https://github.com/mwouts/jupytext/issues/659
                    model["format"] = "json"
                    model["mimetype"] = None
                    try:
                        model["content"] = reads(model["content"], fmt=fmt, config=config)
                    except Exception as err:
                        self.log.error("Error while reading file: %s %s", path, err, exc_info=True)
                        raise HTTPError(500, str(err))

            if not load_alternative_format:
                return model

            # We will now read a second file if this is a paired notebooks.
            if content:
                nbk = model["content"]
                formats = nbk.metadata.get("jupytext", {}).get("formats") or config.default_formats(path)
                formats = long_form_multiple_formats(formats, nbk.metadata, auto_ext_requires_language_info=False)
            else:
                if path not in self.paired_notebooks:
                    return model

                _, formats = self.paired_notebooks.get(path)
                formats = long_form_multiple_formats(formats)

            # Compute paired notebooks from formats
            alt_paths = [(path, fmt)]
            fmt, formats = self._drop_formats_if_they_dont_match_path(path, fmt, formats)
            if formats:
                try:
                    _, fmt = find_base_path_and_format(path, formats)
                    alt_paths = paired_paths(path, fmt, formats)
                    self.update_paired_notebooks(path, formats)
                except InconsistentPath as err:
                    self.log.error(
                        "Unable to read paired notebook: %s %s",
                        path,
                        err,
                        exc_info=True,
                    )
                    raise HTTPError(500, f"Unable to read paired notebook: {path} {err}")
            else:
                if path in self.paired_notebooks:
                    fmt, formats = self.paired_notebooks.get(path)
                    alt_paths = paired_paths(path, fmt, formats)
                    formats = long_form_multiple_formats(formats)

            if content and len(alt_paths) > 1 and ext == ".ipynb":
                # Apply default options (like saving and reloading would do)
                jupytext_metadata = model["content"]["metadata"].get("jupytext", {})
                config.set_default_format_options(jupytext_metadata, read=True)
                if jupytext_metadata:
                    model["content"]["metadata"]["jupytext"] = jupytext_metadata

            async def get_timestamp(alt_path):
                # self.exists is not async for AsyncLargeManager,
                # but MetaManager from fs_manager has an async version
                exists = self.exists(alt_path)
                if inspect.isawaitable(exists):
                    exists = await exists
                if not exists:
                    return None
                if alt_path == path:
                    return model["last_modified"]
                return (await self.super.get(alt_path, content=False))["last_modified"]

            async def read_one_file(alt_path, alt_fmt):
                if alt_path == path:
                    return model["content"]
                if alt_path.endswith(".ipynb"):
                    self.log.info(f"Reading OUTPUTS from {alt_path}")
                    return (await self.super.get(alt_path, content=True, type="notebook", format=format))["content"]

                self.log.info(f"Reading SOURCE from {alt_path}")
                text = (
                    await self.super.get(
                        alt_path,
                        content=True,
                        type="file",
                        # Don't use the parent format, see https://github.com/mwouts/jupytext/issues/1124
                        format=None,
                    )
                )["content"]
                return reads(text, fmt=alt_fmt, config=config)

            timestamps = {alt_path: await get_timestamp(alt_path) for alt_path, alt_fmt in paired_paths(path, fmt, formats)}

            inputs, outputs = latest_inputs_and_outputs(
                path,
                fmt,
                formats,
                lambda alt_path: timestamps[alt_path],
                contents_manager_mode=True,
            )

            # Modification time of a paired notebook is the timestamp of inputs #118 #978
            model["last_modified"] = inputs.timestamp

            if require_hash:
                if inputs.path is not None and outputs.path is not None and inputs.path != outputs.path:
                    model_other = await self.super.get(
                        inputs.path if path == outputs.path else outputs.path,
                        content=False,
                        require_hash=True,
                    )
                    # The hash of a paired file is the concatenation of
                    # the hashes of the input and output files
                    if path == outputs.path:
                        model["hash"] = model_other["hash"] + model["hash"]
                    else:
                        model["hash"] = model["hash"] + model_other["hash"]

            if not content:
                return model

            # Before we combine the two files, we make sure we're not overwriting ipynb cells
            # with an outdated text file
            content = None
            try:
                if outputs.timestamp and outputs.timestamp > inputs.timestamp + timedelta(
                    seconds=config.outdated_text_notebook_margin
                ):
                    ts_mismatch = (
                        "{out} (last modified {out_last}) is more recent than {src} (last modified {src_last})".format(
                            src=inputs.path,
                            src_last=inputs.timestamp,
                            out=outputs.path,
                            out_last=outputs.timestamp,
                        )
                    )
                    self.log.warning(ts_mismatch)

                    try:
                        content = await read_pair(inputs, outputs, read_one_file, must_match=True)
                        self.log.warning(
                            "The inputs in {src} and {out} are identical, so the mismatch in timestamps was ignored".format(
                                src=inputs.path, out=outputs.path
                            )
                        )
                    except HTTPError:
                        raise
                    except PairedFilesDiffer as diff:
                        raise HTTPError(
                            400,
                            """{ts_mismatch}

Differences (jupytext --diff {src} {out}) are:
{diff}
Please either:
- open {src} in a text editor, make sure it is up to date, and save it,
- or delete {src} if not up to date,
- or increase check margin by adding, say,
outdated_text_notebook_margin = 5  # default is 1 (second)
to your jupytext.toml file
                        """.format(
                                ts_mismatch=ts_mismatch,
                                src=inputs.path,
                                out=outputs.path,
                                diff=diff,
                            ),
                        )
            except OverflowError:
                pass

            if content is not None:
                model["content"] = content
            else:
                try:
                    model["content"] = await read_pair(inputs, outputs, read_one_file)
                except HTTPError:
                    raise
                except Exception as err:
                    self.log.error("Error while reading file: %s %s", path, err, exc_info=True)
                    raise HTTPError(500, str(err))

            if not outputs.timestamp:
                set_kernelspec_from_language(model["content"])

            return model

        async def new_untitled(self, path="", type="", ext=""):
            """Create a new untitled file or directory in path

            We override the base function because that one does not take the 'ext' argument
            into account when type=="notebook". See https://github.com/mwouts/jupytext/issues/443
            """
            if type != "notebook" and ext != ".ipynb":
                return await self.super.new_untitled(path, type, ext)

            ext = ext or ".ipynb"
            if ":" in ext:
                ext, format_name = ext.split(":", 1)
            else:
                format_name = ""

            path = path.strip("/")
            if not await self.dir_exists(path):
                raise HTTPError(404, "No such directory: %s" % path)

            untitled = self.untitled_notebook
            config = await self.get_config(path)
            name = self.increment_notebook_filename(config, untitled + ext, path)
            path = f"{path}/{name}"

            model = {"type": "notebook"}
            if format_name:
                model["format"] = "json"
                model["content"] = nbformat.v4.nbbase.new_notebook(metadata={"jupytext": {"formats": ext + ":" + format_name}})

            return await self.new(model, path)

        def increment_notebook_filename(self, config, filename, path=""):
            """Increment a notebook filename until it is unique, regardless of extension"""
            # Extract the full suffix from the filename (e.g. .tar.gz)
            path = path.strip("/")
            basename, dot, ext = filename.partition(".")
            ext = dot + ext

            for i in itertools.count():
                if i:
                    insert_i = f"{i}"
                else:
                    insert_i = ""
                basename_i = basename + insert_i
                name = basename_i + ext
                if not any(self.exists(f"{path}/{basename_i}{nb_ext}") for nb_ext in config.notebook_extensions):
                    break
            return name

        async def trust_notebook(self, path):
            """Trust the current notebook"""
            if path.endswith(".ipynb") or path not in self.paired_notebooks:
                await self.super.trust_notebook(path)
                return

            fmt, formats = self.paired_notebooks[path]
            for alt_path, alt_fmt in paired_paths(path, fmt, formats):
                if alt_fmt["extension"] == ".ipynb":
                    await self.super.trust_notebook(alt_path)

        async def rename_file(self, old_path, new_path):
            """
            Rename the current file. If the file is a notebook,
            we rename the paired files as well
            """

            # If the file is not a notebook, we call the parent rename_file method
            ext = os.path.splitext(old_path)[1]
            config = await self.get_config(old_path, use_cache=True)
            if ext not in self.all_nb_extensions(config):
                await self.super.rename_file(old_path, new_path)
                return

            if old_path not in self.paired_notebooks:
                try:
                    # we do not know yet if this is a paired notebook (#190)
                    # -> to get this information we open the notebook
                    self.log.info("Opening %s to check if it is a paired notebook", old_path)
                    await self.get(old_path, content=True)
                except Exception:
                    pass

            if old_path not in self.paired_notebooks:
                await self.super.rename_file(old_path, new_path)
                return

            fmt, formats = self.paired_notebooks.get(old_path)
            fmt, formats = self._drop_formats_if_they_dont_match_path(new_path, fmt, formats)
            old_alt_paths = paired_paths(old_path, fmt, formats)

            # Is the new file name consistent with suffix?
            try:
                new_base = base_path(new_path, fmt)
            except HTTPError:
                raise
            except Exception as err:
                self.log.error(
                    "Error while renaming file from %s to %s: %s",
                    old_path,
                    new_path,
                    err,
                    exc_info=True,
                )
                raise HTTPError(500, str(err))

            for old_alt_path, alt_fmt in old_alt_paths:
                new_alt_path = full_path(new_base, alt_fmt)
                if self.exists(old_alt_path):
                    await self.create_prefix_dir(new_alt_path, alt_fmt)
                    await self.super.rename_file(old_alt_path, new_alt_path)

            self.drop_paired_notebook(old_path)
            self.update_paired_notebooks(new_path, formats)

        def get_parent_dir(self, path):
            """The parent directory"""
            if "/" in path:
                return path.rsplit("/", 1)[0]
            # jupyter-fs
            if ":" in path and hasattr(self, "_managers"):
                if path.endswith(":"):
                    return ""
                return path.rsplit(":", 1)[0] + ":"
            return ""

        async def get_config_file(self, directory):
            """Return the jupytext configuration file, if any"""
            for jupytext_config_file in JUPYTEXT_CONFIG_FILES:
                path = directory + "/" + jupytext_config_file
                if await self.file_exists(path):
                    if not self.allow_hidden and jupytext_config_file.startswith("."):
                        self.log.warning(f"Ignoring config file {path} (see Jupytext issue #964)")
                        continue
                    return path

            pyproject_path = directory + "/" + PYPROJECT_FILE
            if await self.file_exists(pyproject_path):
                model = await self.get(pyproject_path, type="file")
                try:
                    doc = tomllib.loads(model["content"])
                except tomllib.TOMLDecodeError as e:
                    self.log.warning(f"Cannot load {pyproject_path}: {e}")
                else:
                    if doc.get("tool", {}).get("jupytext") is not None:
                        return pyproject_path

            if not directory:
                return None

            parent_dir = self.get_parent_dir(directory)
            return await self.get_config_file(parent_dir)

        async def load_config_file(self, config_file, *, prev_config_file, prev_config, is_os_path=False):
            """Load the configuration file"""
            if config_file is None:
                return None
            if config_file.endswith(".py") and not is_os_path:
                config_file = self._get_os_path(config_file)
                is_os_path = True

            config_content = None
            if not is_os_path:
                try:
                    model = await self.super.get(config_file, content=True, type="file")
                    config_content = model["content"]
                except HTTPError:
                    pass

            config = load_jupytext_configuration_file(config_file, config_content)
            if config is None:
                return config

            log_level = config.cm_config_log_level
            if log_level == "info_if_changed":
                if config_file != prev_config_file or config != prev_config:
                    log_level = "info"
                else:
                    log_level = "none"
            if log_level != "none":
                getattr(self.log, log_level)("Loaded Jupytext configuration file at %s", config_file)
            return config

        async def get_config(self, path, use_cache=False):
            """Return the Jupytext configuration for the given path"""
            parent_dir = self.get_parent_dir(path)

            # When listing the notebooks for the tree view, we use a cache for the configuration file
            # The cache will be refreshed when a notebook is opened or saved, or when we go
            # to a different directory.
            if not use_cache or parent_dir != self.cached_config.path:
                try:
                    config_file = await self.get_config_file(parent_dir)
                    if config_file:
                        self.cached_config.config = await self.load_config_file(
                            config_file,
                            prev_config_file=self.cached_config.config_file,
                            prev_config=self.cached_config.config,
                        )
                    else:
                        config_file = find_global_jupytext_configuration_file()
                        self.cached_config.config = await self.load_config_file(
                            config_file,
                            prev_config_file=self.cached_config.config_file,
                            prev_config=self.cached_config.config,
                            is_os_path=True,
                        )
                    self.cached_config.config_file = config_file
                    self.cached_config.path = parent_dir
                except JupytextConfigurationError as err:
                    self.log.error(
                        "Error while reading config file: %s %s",
                        config_file,
                        err,
                        exc_info=True,
                    )
                    raise HTTPError(500, f"{err}")

            if self.cached_config.config is not None:
                return self.cached_config.config
            if isinstance(self.notebook_extensions, str):
                self.notebook_extensions = self.notebook_extensions.split(",")
            return self

        def _drop_formats_if_they_dont_match_path(self, path, fmt, formats):
            if formats is None:
                return fmt, formats
            list_of_formats = long_form_multiple_formats(formats)
            try:
                _, _ = find_base_path_and_format(path, list_of_formats)
            except InconsistentPath:
                for fmt in list_of_formats:
                    try:
                        _, adjusted_format = base_path_and_adjusted_fmt(path, fmt)
                    except InconsistentPath:
                        continue
                    else:
                        self.log.warning(
                            "Notebook %s matches none of the expected formats. "
                            'Ignoring formats="%s" and using formats="%s" instead.',
                            path,
                            short_form_multiple_formats(formats),
                            short_form_one_format(adjusted_format),
                        )
                        new_formats = [adjusted_format]
                        if isinstance(formats, list):
                            return adjusted_format, new_formats
                        return short_form_one_format(adjusted_format), short_form_multiple_formats(new_formats)
            return fmt, formats

    if "require_hash" in inspect.signature(base_contents_manager_class.get).parameters:
        AsyncJupytextContentsManager.get = AsyncJupytextContentsManager._get_with_require_hash_argument
    else:
        AsyncJupytextContentsManager.get = AsyncJupytextContentsManager._get_with_no_require_hash_argument

    return AsyncJupytextContentsManager


try:
    # The AsyncLargeFileManager is taken by default from jupyter_server if available
    from jupyter_server.services.contents.largefilemanager import AsyncLargeFileManager

    AsyncTextFileContentsManager = build_async_jupytext_contents_manager_class(AsyncLargeFileManager)
except ImportError:
    # If we can't find jupyter_server then we take the file manager from notebook
    # import notebook.transutils needs to happen before notebook.services.contents.filemanager, see #75
    try:
        import notebook.transutils  # noqa
    except ImportError:
        pass

    try:
        from notebook.services.contents.largefilemanager import AsyncLargeFileManager

        AsyncTextFileContentsManager = build_async_jupytext_contents_manager_class(AsyncLargeFileManager)
    except ImportError:
        # Older versions of notebook do not have the LargeFileManager #217
        from notebook.services.contents.filemanager import FileContentsManager

        AsyncTextFileContentsManager = build_async_jupytext_contents_manager_class(FileContentsManager)
