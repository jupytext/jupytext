from jupytext.marimo import marimo_py_to_notebook, notebook_to_marimo_py, marimo_version
import pytest
from nbformat.v4.nbbase import new_notebook, new_code_cell
from jupytext.compare import compare, compare_notebooks
from jupytext.formats import guess_format


@pytest.fixture
def py_marimo() -> str:
    return f"""import marimo

__generated_with = "{marimo_version()}"
app = marimo.App()


@app.cell
def _():
    x = 1
    return


if __name__ == "__main__":
    app.run()"""


@pytest.fixture
def notebook():
    return new_notebook(cells=[new_code_cell("x = 1")])


def test_guess_format(py_marimo):
    assert guess_format(py_marimo, ".py") == ("marimo", {})


@pytest.mark.requires_marimo
def test_notebook_to_py_marimo(py_marimo, notebook):
    actual = notebook_to_marimo_py(notebook)
    compare(actual, py_marimo)


@pytest.mark.requires_marimo
def test_marimo_py_to_notebook(py_marimo, notebook):
    actual = marimo_py_to_notebook(py_marimo)
    compare_notebooks(actual, notebook)


@pytest.mark.requires_marimo
@pytest.mark.parametrize("text", ["café", "안녕하세요", "✅"], ids=["latin", "korean", "emoji"])
def test_marimo_round_trip_with_non_ascii_text(text):
    notebook = new_notebook(cells=[new_code_cell(f'x = "{text}"')])

    py_marimo = notebook_to_marimo_py(notebook)
    assert f'x = "{text}"' in py_marimo

    actual = marimo_py_to_notebook(py_marimo)
    compare_notebooks(actual, notebook)
