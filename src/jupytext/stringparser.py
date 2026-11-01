"""A simple file parser that can tell whether the first character of a line
is quoted or not"""

from .languages import _COMMENT


class StringParser:
    """A simple file parser that can tell whether the first character of a line
    is quoted or not"""

    single = None
    triple = None
    triple_start = None

    def __init__(self, language):
        self.ignore = language is None
        self.python = language != "R"
        self.comment = _COMMENT.get(language)

    def is_quoted(self):
        """Is the next line quoted?"""
        if self.ignore:
            return False
        return self.single or self.triple

    def read_line(self, line):
        """Read a new line"""
        if self.ignore:
            return

        # Do not search for quotes when the line is commented out (and not quoted)
        if not self.is_quoted() and self.comment is not None and line.lstrip().startswith(self.comment):
            return

        self.triple_start = -1

        # Skip lines without quotes, or lines inside a multiline string that
        # cannot contain its closing triple quote.
        if self.triple is not None:
            if 3 * self.triple not in line:
                return
        elif '"' not in line and "'" not in line:
            return

        for i, char in enumerate(line):
            if (
                self.single is None
                and self.triple is None
                and self.comment
                and self.comment.startswith(char)
                and line[i:].startswith(self.comment)
            ):
                break
            if char not in ['"', "'"]:
                continue
            # Is the char escaped?
            if line[i - 1 : i] == "\\":
                continue

            if self.single == char:
                self.single = None
                continue
            if self.single is not None:
                continue

            if not self.python:
                continue

            if line[i - 2 : i + 1] == 3 * char and i >= self.triple_start + 3:
                # End of a triple quote
                if self.triple == char:
                    self.triple = None
                    self.triple_start = i
                    continue

                # Are we looking for a different triple quote?
                if self.triple is not None:
                    continue

                # Triple quote starting
                self.triple = char
                self.triple_start = i
                continue

            # Inside a multiline quote
            if self.triple is not None:
                continue

            self.single = char

        # Line ended
        if self.python:
            self.single = None
