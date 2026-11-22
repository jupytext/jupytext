# Testing a Jupyter notebook with pytest

Use this example to run the same checks in a notebook and from the command
line. Install `pytest` alongside Jupytext for the command-line part.

## Write and check a function

The function below returns consecutive integers using a configurable step.

```python
def sequence(start, length=5, step=1):
    return [start + index * step for index in range(length)]
```

Run an assertion in the notebook to check the result as you work.

```python
assert sequence(5) == [5, 6, 7, 8, 9]
```

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
placeholder gives pytest that file. Pytest runs the three tests and returns a
failure status if any assertion fails. Try changing the expected result in
`test_negative_step` to see pytest show the differing values.
