# Testing a Jupyter notebook with pytest

Use this example to run the same checks in a notebook and from the command
line. Install `pytest` alongside Jupytext for the command-line part.

## Write and check a function

The function below returns evenly spaced integers using a configurable step.

```python
def sequence(start, length=5, step=1):
    return [start + index * step for index in range(length)]
```

Run an assertion in the notebook to check the result as you work.

```python
assert sequence(5) == [5, 6, 7, 8, 9]
```

A passing assertion displays no output. To see what a failure looks like,
temporarily remove `7` from the expected list and run the assertion in Jupyter.
The traceback points to the line that failed.

```text
----> 1 assert sequence(5) == [5, 6, 8, 9]

AssertionError
```

Restore the expected list before continuing.

## Name tests for pytest

Pytest discovers functions whose names begin with `test_`. Here we check the
defaults and two edge cases. To run the same checks from Jupyter, call the
functions in a cell.

```python
def test_default_step():
    assert sequence(5) == [5, 6, 7, 8, 9]


def test_negative_step():
    assert sequence(5, length=3, step=-2) == [5, 3, 1]


def test_empty_sequence():
    assert sequence(5, length=0) == []
```

## Run the checks from a terminal

From this directory, run:

```text
jupytext --check "pytest {}" "Tests in a notebook.md"
```

Jupytext exports the notebook to a temporary Python script. The `{}`
placeholder gives pytest that file. Pytest collects the three `test_`
functions and reports `3 passed` when they all succeed.

To compare the output with Jupyter's traceback, remove `7` from the expected
list inside `test_default_step` and run the terminal command again. Pytest
reports `1 failed, 2 passed`. Its assertion rewriting shows the actual and
expected lists and points to the first index where they differ.

```text
______________________________ test_default_step _______________________________

    def test_default_step():
>       assert sequence(5) == [5, 6, 8, 9]
E       assert [5, 6, 7, 8, 9] == [5, 6, 8, 9]
E         At index 2 diff: 7 != 8
```

## Going further

- [nbval](https://github.com/computationalmodelling/nbval) runs an `.ipynb`
  notebook and compares its new outputs with the saved ones. Run
  `pytest --nbval notebook.ipynb`.
- [ipytest](https://github.com/chmp/ipytest) lets you run pytest from Jupyter.
  Call `ipytest.autoconfig()` after importing it, then use the `%%ipytest`
  cell magic or call `ipytest.run()`.
