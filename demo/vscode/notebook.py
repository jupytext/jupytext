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
# This paired notebook can be edited either as
# a Python script or as a Jupyter notebook in
# VS Code. Thanks to the Jupytext Sync
# extension, changes are automatically synced to
# the other paired file(s) when you save.
#
# 💡 Tip: don't forget to hit "Save" before
# switching to the other editor. If you don't save
# your changes, you will run into conflicting edits
# as VS Code does not autoreload files that have
# unsaved edits.

# %%
import plotly.express as px

# %%
px.scatter(
    px.data.iris(),
    x="sepal_width",
    y="sepal_length",
    color="species",
)

# %%
