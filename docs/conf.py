# Minimal Sphinx configuration — serves HTTP redirects from jupytext.readthedocs.io
# to the new jupytext.org site via sphinx-reredirects.
# The actual documentation now lives in website/ (Astro + Starlight).

project = "Jupytext"

extensions = ["myst_parser", "sphinx_reredirects"]
source_suffix = {".md": "markdown"}
root_doc = "index"

redirects = {
    "index": "https://jupytext.org/",
    "install": "https://jupytext.org/getting-started/install/",
    "text-notebooks": "https://jupytext.org/getting-started/text-notebooks/",
    "formats-scripts": "https://jupytext.org/formats/scripts/",
    "formats-markdown": "https://jupytext.org/formats/markdown/",
    "languages": "https://jupytext.org/formats/languages/",
    "paired-notebooks": "https://jupytext.org/using/paired-notebooks/",
    "using-cli": "https://jupytext.org/using/cli/",
    "using-pre-commit": "https://jupytext.org/using/pre-commit/",
    "config": "https://jupytext.org/using/config/",
    "jupyterlab-extension": "https://jupytext.org/integrations/jupyterlab/",
    "jupyter-collaboration": "https://jupytext.org/integrations/jupyter-collaboration/",
    "vs-code": "https://jupytext.org/integrations/vs-code/",
    "advanced-options": "https://jupytext.org/reference/advanced-options/",
    "tutorials": "https://jupytext.org/reference/tutorials/",
    "faq": "https://jupytext.org/reference/faq/",
    "contributing": "https://jupytext.org/reference/contributing/",
    "developing": "https://jupytext.org/reference/developing/",
    "changelog": "https://github.com/jupytext/jupytext/blob/main/CHANGELOG.md",
}
