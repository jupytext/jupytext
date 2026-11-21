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
    ##################################################################
    This is a notebook that contains many hash signs.
    Hopefully its python representation is not recognized as a Sphinx Gallery script...
    ##################################################################
    """)
    return


@app.cell
def _():
    some = 1
    code = 2
    some+code

    ##################################################################
    # A comment
    ##################################################################
    # Another comment
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##################################################################
    This is a notebook that contains many hash signs.
    Hopefully its python representation is not recognized as a Sphinx Gallery script...
    ##################################################################
    """)
    return


if __name__ == "__main__":
    app.run()
