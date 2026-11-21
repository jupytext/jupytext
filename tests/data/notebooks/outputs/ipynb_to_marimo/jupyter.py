import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Jupyter notebook

    This notebook is a simple jupyter notebook. It only has markdown and code cells. And it does not contain consecutive markdown cells. We start with an addition:
    """)
    return


@app.cell
def _():
    a = 1
    b = 2
    a + b
    return a, b


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we return a few tuples
    """)
    return


@app.cell
def _(a, b):
    a, b
    return


@app.cell
def _(a, b):
    a, b, a+b
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And this is already the end of the notebook
    """)
    return


if __name__ == "__main__":
    app.run()
