import stat
import tempfile
import unittest.mock as mock
from pathlib import Path

import pytest
from nbformat import writes as ipynb_writes
from nbformat.v4.nbbase import new_notebook

from jupytext.quarto import notebook_to_qmd, qmd_to_notebook


@pytest.fixture()
def quarto_conversion_dirs():
    """Patch 'quarto convert' with a stub that records where it is asked to work"""
    dirs = []

    def fake_quarto(args, filein=None):
        if filein is None:
            return "1.4.550\n"
        directory = Path(filein).parent
        dirs.append((directory, stat.S_IMODE(directory.stat().st_mode)))
        # 'quarto convert' writes its output next to its input
        if filein.endswith(".qmd"):
            Path(filein[:-4] + ".ipynb").write_text(ipynb_writes(new_notebook()), encoding="utf-8")
        else:
            Path(filein[:-6] + ".qmd").write_text("1 + 1\n", encoding="utf-8")
        return ""

    with mock.patch("jupytext.quarto.quarto", fake_quarto):
        yield dirs


@pytest.mark.skip_on_windows
@pytest.mark.parametrize("convert", [lambda: qmd_to_notebook("1 + 1\n"), lambda: notebook_to_qmd(new_notebook())])
def test_quarto_does_not_convert_in_the_shared_temp_dir(convert, quarto_conversion_dirs):
    """Quarto names its output after its input, so both must sit in a directory
    that other users cannot write to"""
    convert()

    assert quarto_conversion_dirs
    for directory, mode in quarto_conversion_dirs:
        assert directory != Path(tempfile.gettempdir())
        assert not mode & 0o077
