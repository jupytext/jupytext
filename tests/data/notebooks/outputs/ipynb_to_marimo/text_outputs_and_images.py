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
    This notebook contains outputs of many different types: text, HTML, plots and errors.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Text outputs

    Using `print`, `sys.stdout` and `sys.stderr`
    """)
    return


@app.cell
def _():
    import sys
    print('using print')
    sys.stdout.write('using sys.stdout.write')
    sys.stderr.write('using sys.stderr.write')
    return


@app.cell
def _():
    import logging
    logging.debug('Debug')
    logging.info('Info')
    logging.warning('Warning')
    logging.error('Error')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # HTML outputs

    Using `pandas`. Here we find two representations: both text and HTML.
    """)
    return


@app.cell
def _():
    import pandas as pd
    pd.DataFrame([4])
    return (pd,)


@app.cell
def _(pd):
    from IPython.display import display
    display(pd.DataFrame([5]))
    display(pd.DataFrame([6]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Images
    """)
    return


@app.cell
def _():
    # '%matplotlib inline' command supported automatically in marimo
    return


@app.cell
def _():
    # First plot
    from matplotlib import pyplot as plt
    import numpy as np
    w, h = 3, 3
    data = np.zeros((h, w, 3), dtype=np.uint8)
    data[0,:] = [0,255,0]
    data[1,:] = [0,0,255]
    data[2,:] = [0,255,0]
    data[1:3,1:3] = [255, 0, 0]
    plt.imshow(data)
    plt.axis('off')
    plt.show()
    # Second plot
    data[1:3,1:3] = [255, 255, 0]
    plt.imshow(data)
    plt.axis('off')
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Errors
    """)
    return


@app.cell
def _(undefined_variable):
    undefined_variable
    return


if __name__ == "__main__":
    app.run()
