# %% [markdown]
# # Jupytext's word cloud
#
# This Python script is also a notebook. In JupyterLab, right-click the file
# and choose **Open With → Jupytext Notebook**. Run the cells to display the
# word cloud. Install `wordcloud` to run the example locally.

# %%
from wordcloud import WordCloud

topics = [
    "Jupytext",
    "Jupyter Notebook",
    "JupyterLab",
    "Version control",
    "GitHub",
    "Text notebooks",
    "Python",
    "Markdown",
    "MyST",
    "Quarto",
    "R Markdown",
    "Julia",
    "Scripts",
    "Notebook pairing",
    "Cell IDs",
    "Metadata",
    "Outputs",
    "VS Code",
    "Binder",
    "Marimo",
    "Reproducible research",
    "Code review",
    "pytest",
    "Ruff",
    "Notebook",
    "Git",
    "Text",
    "Code",
    "Notebook Template",
    "Visual Studio Code",
    "PyCharm",
    "Atom",
    "Spyder",
    "Hydrogen",
    "RStudio",
    "Sphinx-Gallery",
    "Documentation",
    "black",
    "autopep8",
    "R",
    "Bash",
    "Powershell",
    "Scala",
    "Scheme",
    "Clojure",
    "Matlab",
    "Octave",
    "C++",
    "q/kdb+",
    "IDL",
    "TypeScript",
    "Javascript",
    "Rust",
    "Robot Framework",
]

# %% [markdown]
# Give the main topics more weight and fix the random seed to make the layout
# repeatable. The last expression displays the image in the notebook.

# %%
frequencies = dict.fromkeys(topics, 1)
frequencies.update({"Jupytext": 7, "Jupyter Notebook": 5, "Text notebooks": 4})
cloud = WordCloud(
    random_state=42,
    background_color="white",
    width=960,
    height=420,
).generate_from_frequencies(frequencies)

cloud.to_image()

# %% [markdown]
# To export the image to a file, run `cloud.to_file("jupytext_word_cloud.png")`.
