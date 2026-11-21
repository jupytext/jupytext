import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    1 + 1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A markdown cell
    And below, the cell for function f has non trivial cell metadata. And the next cell as well.
    """)
    return


@app.function
def f(x):
    return x


@app.cell
def _():
    f(5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    More text
    """)
    return


@app.cell
def _():
    2 + 2
    return


if __name__ == "__main__":
    app.run()
