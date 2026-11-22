# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.20.1.dev0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Edit a paired notebook in VS Code
#
# Open both `notebook.ipynb` and `notebook.py`. With the
# [Jupytext Sync extension](https://marketplace.visualstudio.com/items?itemName=caenrigen.jupytext-sync)
# active, save changes in either file to update its pair. Save an edit before
# switching editors to avoid conflicting unsaved changes.
#
# To try the same workflow from the terminal, run
# `jupytext --sync notebook.py` from this directory after editing the script.

# %%
import plotly.express as px

iris = px.data.iris()
px.scatter(
    iris,
    x="sepal_width",
    y="sepal_length",
    color="species",
    labels={"sepal_width": "Sepal width (cm)", "sepal_length": "Sepal length (cm)"},
    title="Iris sepal measurements",
)

# %% [markdown]
# Try changing the chart title in the script. Sync, run the cell in the
# notebook, and save to keep the refreshed output in the `.ipynb` file.
