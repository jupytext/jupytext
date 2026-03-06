"""Determine notebook or cell language"""

import re

# Jupyter magic commands that are also languages
_JUPYTER_LANGUAGES = [
    "R",
    "bash",
    "sh",
    "python",
    "python2",
    "python3",
    "coconut",
    "javascript",
    "js",
    "perl",
    "html",
    "latex",
    "markdown",
    "pypy",
    "ruby",
    "script",
    "svg",
    "matlab",
    "octave",
    "idl",
    "robotframework",
    "sas",
    "spark",
    "sql",
    "cython",
    "haskell",
    "tcl",
    "gnuplot",
    "wolfram language",
]

# Supported file extensions (and languages)
# Please add more languages here (and add a few tests) - see contributing.md
_SCRIPT_EXTENSIONS = {
    ".py": {"language": "python", "comment": "#"},
    ".coco": {"language": "coconut", "comment": "#"},
    ".R": {"language": "R", "comment": "#"},
    ".r": {"language": "R", "comment": "#"},
    ".jl": {"language": "julia", "comment": "#"},
    ".cpp": {"language": "c++", "comment": "//"},
    ".ss": {"language": "scheme", "comment": ";;"},
    ".clj": {"language": "clojure", "comment": ";;"},
    ".scm": {"language": "scheme", "comment": ";;"},
    ".sh": {"language": "bash", "comment": "#"},
    ".ps1": {"language": "powershell", "comment": "#"},
    ".q": {"language": "q", "comment": "/"},
    ".m": {"language": "matlab", "comment": "%"},
    # Unfortunately, Wolfram Mathematica also uses the .m extension which
    # conflicts with Matlab. To work around this problem we arbitrarily use a
    # made-up .wolfram extension.
    ".wolfram": {
        "language": "wolfram language",
        "comment": "(*",
        "comment_suffix": "*)",
    },
    ".pro": {"language": "idl", "comment": ";"},
    ".js": {"language": "javascript", "comment": "//"},
    ".ts": {"language": "typescript", "comment": "//"},
    ".scala": {"language": "scala", "comment": "//"},
    ".rs": {"language": "rust", "comment": "//"},
    ".robot": {"language": "robotframework", "comment": "#"},
    ".resource": {"language": "robotframework", "comment": "#"},
    ".cs": {"language": "csharp", "comment": "//"},
    ".fsx": {"language": "fsharp", "comment": "//"},
    ".fs": {"language": "fsharp", "comment": "//"},
    ".sos": {"language": "sos", "comment": "#"},
    ".java": {"language": "java", "comment": "//"},
    ".groovy": {"language": "groovy", "comment": "//"},
    ".sage": {"language": "sage", "comment": "#"},
    ".ml": {
        "language": "ocaml",
        "comment": "(*",
        "comment_suffix": "*)",
    },  # OCaml only has block comments
    ".hs": {"language": "haskell", "comment": "--"},
    ".tcl": {"language": "tcl", "comment": "#"},
    ".mac": {
        "language": "maxima",
        "comment": "/*",
        "comment_suffix": "*/",
    },  # Maxima only has block comments
    ".gp": {"language": "gnuplot", "comment": "#"},
    ".do": {"language": "stata", "comment": "//"},
    ".sas": {
        "language": "sas",
        "comment": "/*",
        "comment_suffix": "*/",
    },
    ".jenner": {
        "language": "jenner",
        "comment": "/*",
        "comment_suffix": "*/",
    },
    ".xsh": {"language": "xonsh", "comment": "#"},
    ".lgt": {"language": "logtalk", "comment": "%"},
    ".logtalk": {"language": "logtalk", "comment": "%"},
    ".lua": {"language": "lua", "comment": "--"},
    ".go": {"language": "go", "comment": "//"},
}

_COMMENT_CHARS = [
    _SCRIPT_EXTENSIONS[ext]["comment"] for ext in _SCRIPT_EXTENSIONS if _SCRIPT_EXTENSIONS[ext]["comment"] != "#"
]

_COMMENT = {_SCRIPT_EXTENSIONS[ext]["language"]: _SCRIPT_EXTENSIONS[ext]["comment"] for ext in _SCRIPT_EXTENSIONS}
_JUPYTER_LANGUAGES = set(_JUPYTER_LANGUAGES).union(_COMMENT.keys()).union(["c#", "f#", "cs", "fs"])
_JUPYTER_LANGUAGES_LOWER_AND_UPPER = _JUPYTER_LANGUAGES.union({str.upper(lang) for lang in _JUPYTER_LANGUAGES})
_GO_DOUBLE_PERCENT_COMMAND = re.compile(r"^(%%\s*|%%\s+-.*)$")


def default_language_from_metadata_and_ext(metadata, ext, pop_main_language=False):
    """Return the default language given the notebook metadata, and a file extension"""
    default_from_ext = _SCRIPT_EXTENSIONS.get(ext, {}).get("language")

    main_language = metadata.get("jupytext", {}).get("main_language")
    default_language = metadata.get("kernelspec", {}).get("language") or default_from_ext
    language = main_language or default_language

    if main_language is not None and main_language == default_language and pop_main_language:
        metadata["jupytext"].pop("main_language")

    if language is None or language in ["R", "sas"]:
        return language

    if language.startswith("C++"):
        return "c++"

    return language.lower().replace("#", "sharp")


def usual_language_name(language):
    """Return the usual language name (one that may be found in _SCRIPT_EXTENSIONS above)"""
    language = language.lower()
    if language == "r":
        return "R"
    if language.startswith("c++"):
        return "c++"
    if language == "octave":
        return "matlab"
    if language in ["cs", "c#"]:
        return "csharp"
    if language in ["fs", "f#"]:
        return "fsharp"
    if language == "sas":
        return "SAS"
    return language


def same_language(kernel_language, language):
    """Are those the same language?"""
    return usual_language_name(kernel_language) == usual_language_name(language)


def set_main_and_cell_language(metadata, cells, ext, custom_cell_magics):
    """Set main language for the given collection of cells, and
    use magics for cells that use other languages"""
    main_language = default_language_from_metadata_and_ext(metadata, ext)

    if main_language is None:
        languages = {"python": 0.5}
        for cell in cells:
            if "language" in cell["metadata"]:
                language = usual_language_name(cell["metadata"]["language"])
                languages[language] = languages.get(language, 0.0) + 1

        main_language = max(languages, key=languages.get)

    # save main language when no kernel is set
    if "language" not in metadata.get("kernelspec", {}) and cells:
        metadata.setdefault("jupytext", {})["main_language"] = main_language

    # Remove 'language' meta data and add a magic if not main language
    for cell in cells:
        if "language" in cell["metadata"]:
            language = cell["metadata"]["language"]
            if language == main_language:
                cell["metadata"].pop("language")
                continue

            if usual_language_name(language) == main_language:
                continue

            if language in _JUPYTER_LANGUAGES or language in custom_cell_magics:
                cell["metadata"].pop("language")
                magic = "%%" if main_language != "csharp" else "#!"
                if "magic_args" in cell["metadata"]:
                    magic_args = cell["metadata"].pop("magic_args")
                    cell["source"] = f"{magic}{language} {magic_args}\n" + cell["source"]
                else:
                    cell["source"] = f"{magic}{language}\n" + cell["source"]


def cell_language(source, default_language, custom_cell_magics):
    """Return cell language and language options, if any"""
    if source:
        line = source[0]
        if default_language == "go" and _GO_DOUBLE_PERCENT_COMMAND.match(line):
            return None, None
        if default_language == "csharp":
            if line.startswith("#!"):
                lang = line[2:].strip()
                if lang in _JUPYTER_LANGUAGES:
                    source.pop(0)
                    return lang, ""
        elif line.startswith("%%"):
            magic = line[2:]
            if " " in magic:
                lang, magic_args = magic.split(" ", 1)
            else:
                lang = magic
                magic_args = ""

            if lang in _JUPYTER_LANGUAGES or lang in custom_cell_magics:
                source.pop(0)
                return lang, magic_args

    return None, None


def comment_lines(lines, prefix, suffix=""):
    """Return commented lines"""
    if not prefix:
        return lines
    if not suffix:
        return [prefix + " " + line if line else prefix for line in lines]
    return [prefix + " " + line + " " + suffix if line else prefix + " " + suffix for line in lines]
