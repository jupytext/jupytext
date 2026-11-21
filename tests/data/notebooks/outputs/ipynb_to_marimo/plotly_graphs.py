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
    This notebook contains complex outputs, including plotly javascript graphs.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Interactive plots
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We use Plotly's connected mode to make the notebook lighter - when connected, the notebook downloads the `plotly.js` library from the web.
    """)
    return


@app.cell
def _():
    import plotly.offline as offline
    offline.init_notebook_mode(connected=True)
    return


@app.cell
def _():
    import plotly.graph_objects as go
    fig = go.Figure(
        data=[go.Bar(y=[2, 3, 1])],
        layout=go.Layout(title="bar plot"))
    fig.show()
    fig.data[0].marker = dict(color='purple')
    fig
    return


if __name__ == "__main__":
    app.run()
