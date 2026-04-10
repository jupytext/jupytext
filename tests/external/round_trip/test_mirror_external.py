import pytest

from jupytext.compare import assert_conversion_same_as_mirror

"""---------------------------------------------------------------------------------

Part I: ipynb -> fmt -> ipynb

---------------------------------------------------------------------------------"""


@pytest.mark.requires_pandoc
def test_ipynb_to_pandoc(ipynb_to_pandoc, no_jupytext_version_number):
    assert_conversion_same_as_mirror(ipynb_to_pandoc, "md:pandoc", "ipynb_to_pandoc")


@pytest.mark.requires_pandoc
# @pytest.mark.xfail(
#     reason="Strict Org round-trip still differs on cell structure/content for some notebooks",
#     strict=True,
# )
def test_ipynb_to_org(ipynb_to_org, no_jupytext_version_number):
    assert_conversion_same_as_mirror(ipynb_to_org, "org", "ipynb_to_org")


@pytest.mark.requires_quarto
def test_ipynb_to_quarto(
    ipynb_to_quarto,
    no_jupytext_version_number,
):
    assert_conversion_same_as_mirror(ipynb_to_quarto, "qmd", "ipynb_to_quarto")


@pytest.mark.requires_sphinx_gallery
def test_ipynb_to_python_sphinx(ipynb_to_sphinx, no_jupytext_version_number):
    assert_conversion_same_as_mirror(ipynb_to_sphinx, "py:sphinx", "ipynb_to_sphinx")


"""---------------------------------------------------------------------------------

Part II: text -> ipynb -> text

---------------------------------------------------------------------------------"""


def test_Rmd_to_ipynb(rmd_file, no_jupytext_version_number):
    assert_conversion_same_as_mirror(rmd_file, "ipynb", "Rmd_to_ipynb")


@pytest.mark.requires_sphinx_gallery
def test_sphinx_to_ipynb(sphinx_file, no_jupytext_version_number):
    assert_conversion_same_as_mirror(sphinx_file, "ipynb:sphinx", "sphinx_to_ipynb")


@pytest.mark.requires_sphinx_gallery
def test_sphinx_md_to_ipynb(sphinx_file, no_jupytext_version_number):
    assert_conversion_same_as_mirror(
        sphinx_file,
        {"extension": ".ipynb", "format_name": "sphinx", "rst2md": True},
        "sphinx-rst2md_to_ipynb",
        compare_notebook=True,
    )
