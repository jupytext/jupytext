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
    This cell uses no particular cell marker

    $$
    \begin{align}
    \dot{x} & = \sigma(y-x)\\
    \dot{y} & = \rho x - y - xz \\
    \dot{z} & = -\beta z + xy
    \end{align}
    $$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This cell uses no particular cell marker, and a single slash in the $\LaTeX$ equation

    $$
    \begin{align}
    \dot{x} & = \sigma(y-x) \
    \dot{y} & = \rho x - y - xz \
    \dot{z} & = -\beta z + xy
    \end{align}
    $$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This cell uses the triple quote cell markers introduced at https://github.com/mwouts/jupytext/issues/305

    $$
    \begin{align}
    \dot{x} & = \sigma(y-x)\\
    \dot{y} & = \rho x - y - xz \\
    \dot{z} & = -\beta z + xy
    \end{align}
    $$
    """)
    return


if __name__ == "__main__":
    app.run()
