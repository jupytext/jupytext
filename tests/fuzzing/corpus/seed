"""Escape Jupyter magics when converting to other formats"""

import re

from .languages import _COMMENT, _SCRIPT_EXTENSIONS, usual_language_name
from .stringparser import StringParser


def get_comment(ext):
    return re.escape(_SCRIPT_EXTENSIONS[ext]["comment"])


# A magic expression is a line or cell or metakernel magic (#94, #61) escaped zero, or multiple times
_MAGIC_RE = {
    _SCRIPT_EXTENSIONS[ext]["language"]: re.compile(
        r"^\s*({0} |{0})*(%|%%|%%%)[a-zA-Z]".format(get_comment(ext))
    )
    for ext in _SCRIPT_EXTENSIONS
}
_MAGIC_FORCE_ESC_RE = {
    _SCRIPT_EXTENSIONS[ext]["language"]: re.compile(
        r"^\s*({0} |{0})*(%|%%|%%%)[a-zA-Z](.*){0}\s*escape".format(get_comment(ext))
    )
    for ext in _SCRIPT_EXTENSIONS
}
_MAGIC_NOT_ESC_RE = {
    _SCRIPT_EXTENSIONS[ext]["language"]: re.compile(
        r"^\s*({0} |{0})*(%|%%|%%%)[a-zA-Z](.*){0}\s*noescape".format(get_comment(ext))
    )
    for ext in _SCRIPT_EXTENSIONS
}
_LINE_CONTINUATION_RE = re.compile(r".*\\\s*$")

# Rust magics start with single ':' #351
_MAGIC_RE["rust"] = re.compile(r"^(// |//)*:[a-zA-Z]")
_MAGIC_FORCE_ESC_RE["rust"] = re.compile(r"^(// |//)*:[a-zA-Z](.*)//\s*escape")
_MAGIC_FORCE_ESC_RE["rust"] = re.compile(r"^(// |//)*:[a-zA-Z](.*)//\s*noescape")

# C# magics start with '#!'
_MAGIC_RE["csharp"] = re.compile(r"^(// |//)*#![a-zA-Z]")
_MAGIC_FORCE_ESC_RE["csharp"] = re.compile(r"^(// |//)*#![a-zA-Z](.*)//\s*escape")
_MAGIC_FORCE_ESC_RE["csharp"] = re.compile(r"^(// |//)*#![a-zA-Z](.*)//\s*noescape")

# Go magics might start with % or ! or !*
# (in addition, Go NB might use %% or %% -, see "_GO_DOUBLE_PERCENT_COMMAND")
_MAGIC_RE["go"] = re.compile(r"^(// |//)*(!|!\*|%|%%|%%%)[a-zA-Z]")

# Commands starting with a question or exclamation mark have to be escaped
_PYTHON_HELP_OR_BASH_CMD = re.compile(r"^\s*(# |#)*\s*(\?|!)\s*[A-Za-z\.\~\$\\\/\{\}]")

# A bash command not followed by an equal sign or a parenthesis is a magic command
_PYTHON_MAGIC_CMD = re.compile(
    r"^(# |#)*({})($|\s$|\s[^=,])".format(
        "|".join(
            # posix
            ["cat", "cd", "cp", "mv", "rm", "rmdir", "mkdir"]
            +  # noqa: W504
            # windows
            ["copy", "ddir", "echo", "ls", "ldir", "mkdir", "ren", "rmdir"]
        )
    )
)
# Python help commands end with ?
_IPYTHON_MAGIC_HELP = re.compile(r"^\s*(# )*[^\s]*\?\s*$")

_PYTHON_MAGIC_ASSIGN = re.compile(
    r"^(# |#)*\s*([a-zA-Z_][a-zA-Z_$0-9]*)\s*=\s*(%|%%|%%%|!)[a-zA-Z](.*)"
)

_SCRIPT_LANGUAGES = [_SCRIPT_EXTENSIONS[ext]["language"] for ext in _SCRIPT_EXTENSIONS]


def is_magic(line, language, global_escape_flag=True, explicitly_code=False):
    """Is the current line a (possibly escaped) Jupyter magic, and should it be commented?"""
    language = usual_language_name(language)
    if (
        language in ["octave", "matlab", "sas", "logtalk"]
        or language not in _SCRIPT_LANGUAGES
    ):
        return False
    if _MAGIC_FORCE_ESC_RE[language].match(line):
        return True
    if not global_escape_flag or _MAGIC_NOT_ESC_RE[language].match(line):
        return False
    if _MAGIC_RE[language].match(line):
        return True
    if language != "python":
        return False
    if _PYTHON_HELP_OR_BASH_CMD.match(line):
        return True
    if _PYTHON_MAGIC_ASSIGN.match(line):
        return True
    if explicitly_code and _IPYTHON_MAGIC_HELP.match(line):
        return True
    return _PYTHON_MAGIC_CMD.match(line)


def need_explicit_marker(
    source, language="python", global_escape_flag=True, explicitly_code=True
):
    """Does this code needs an explicit cell marker?"""
    if language != "python" or not global_escape_flag or not explicitly_code:
        return False

    parser = StringParser(language)
    for line in source:
        if not parser.is_quoted() and is_magic(
            line, language, global_escape_flag, explicitly_code
        ):
            if not is_magic(line, language, global_escape_flag, False):
                return True
        parser.read_line(line)
    return False


def comment_magic(
    source, language="python", global_escape_flag=True, explicitly_code=True
):
    """Escape Jupyter magics with '# '"""
    parser = StringParser(language)
    next_is_magic = False
    for pos, line in enumerate(source):
        if not parser.is_quoted() and (
            next_is_magic
            or is_magic(line, language, global_escape_flag, explicitly_code)
        ):
            if next_is_magic:
                # this is the continuation line of a magic command on the previous line,
                # so we don't want to indent the comment
                unindented = line
                indent = ""
            else:
                unindented = line.lstrip()
                indent = line[: len(line) - len(unindented)]
            source[pos] = indent + _COMMENT[language] + " " + unindented
            next_is_magic = language == "python" and _LINE_CONTINUATION_RE.match(line)
        parser.read_line(line)
    return source


def unesc(line, language):
    """Uncomment once a commented line"""
    comment = _COMMENT[language]
    unindented = line.lstrip()
    indent = line[: len(line) - len(unindented)]
    if unindented.startswith(comment + " "):
        return indent + unindented[len(comment) + 1 :]
    if unindented.startswith(comment):
        return indent + unindented[len(comment) :]
    return line


def uncomment_magic(
    source, language="python", global_escape_flag=True, explicitly_code=True
):
    """Unescape Jupyter magics"""
    parser = StringParser(language)
    next_is_magic = False
    for pos, line in enumerate(source):
        if not parser.is_quoted() and (
            next_is_magic
            or is_magic(line, language, global_escape_flag, explicitly_code)
        ):
            source[pos] = unesc(line, language)
            next_is_magic = language == "python" and _LINE_CONTINUATION_RE.match(line)
        parser.read_line(line)
    return source


_ESCAPED_CODE_START = {
    ".Rmd": re.compile(r"^(# |#)*```{.*}"),
    ".md": re.compile(r"^(# |#)*```"),
    ".markdown": re.compile(r"^(# |#)*```"),
}
_ESCAPED_CODE_START.update(
    {
        ext: re.compile(r"^({0} |{0})*({0}|{0} )\+".format(get_comment(ext)))
        for ext in _SCRIPT_EXTENSIONS
    }
)


def is_escaped_code_start(line, ext):
    """Is the current line a possibly commented code start marker?"""
    return _ESCAPED_CODE_START[ext].match(line)


def escape_code_start(source, ext, language="python"):
    """Escape code start with '# '"""
    parser = StringParser(language)
    for pos, line in enumerate(source):
        if not parser.is_quoted() and is_escaped_code_start(line, ext):
            source[pos] = (
                _SCRIPT_EXTENSIONS.get(ext, {}).get("comment", "#") + " " + line
            )
        parser.read_line(line)
    return source


def unescape_code_start(source, ext, language="python"):
    """Unescape code start"""
    parser = StringParser(language)
    for pos, line in enumerate(source):
        if not parser.is_quoted() and is_escaped_code_start(line, ext):
            unescaped = unesc(line, language)
            # don't remove comment char if we break the code start...
            if is_escaped_code_start(unescaped, ext):
                source[pos] = unescaped
        parser.read_line(line)
    return source
