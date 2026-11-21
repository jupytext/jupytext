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
    # Quarterly Sales
    A look at Q4 revenue by region.
    """)
    return


@app.cell
def _():
    import pandas as pd
    df = pd.read_csv("sales.csv")
    return (df,)


@app.cell
def _(df):
    df.groupby("region")["revenue"].sum().plot.bar()
    return


if __name__ == "__main__":
    app.run()