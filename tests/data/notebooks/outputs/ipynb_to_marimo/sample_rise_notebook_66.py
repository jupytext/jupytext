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
    A markdown cell
    """)
    return


@app.cell
def _():
    1+1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Markdown cell two
    """)
    return


if __name__ == "__main__":
    app.run()
