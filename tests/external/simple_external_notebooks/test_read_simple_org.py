import os

import pytest
from nbformat import reads as ipynb_reads
from nbformat.v4.nbbase import new_code_cell, new_markdown_cell, new_notebook, new_raw_cell

import jupytext
from jupytext.cli import jupytext as jupytext_cli
from jupytext.compare import compare_notebooks
from jupytext.pandoc import PandocError, pandoc


@pytest.mark.requires_pandoc(min_version="3.4")
def test_notebook_to_org_and_back(
    notebook=new_notebook(
        cells=[
            new_markdown_cell("# Hello\n\nThis is a markdown cell."),
            new_code_cell("print('hello')"),
            new_markdown_cell("Another markdown cell."),
        ]
    ),
):
    org = jupytext.writes(notebook, "org")
    assert "#+begin_src" in org.lower()
    nb2 = jupytext.reads(org, "org")
    assert [cell.cell_type for cell in nb2.cells] == [cell.cell_type for cell in notebook.cells]
    assert nb2.cells[0].source.endswith(notebook.cells[0].source)
    assert nb2.cells[1].source.rstrip("\n") == notebook.cells[1].source
    assert nb2.cells[2].source.endswith(notebook.cells[2].source)


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_round_trip_preserves_code():
    notebook = new_notebook(
        cells=[
            new_code_cell("a = 1\nb = 2\na + b"),
        ]
    )
    org = jupytext.writes(notebook, "org")
    nb2 = jupytext.reads(org, "org")
    assert any("a = 1" in cell.source for cell in nb2.cells if cell.cell_type == "code")


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_kernel_header_arg():
    """Kernel metadata should appear in Org header-args properties."""
    notebook = new_notebook(
        metadata={"kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"}},
        cells=[
            new_code_cell("x = 1"),
        ],
    )
    org = jupytext.writes(notebook, "org")
    assert "#+JUPYTER_KERNEL_DISPLAY_NAME: Python 3" in org
    assert "#+PROPERTY: header-args:jupyter-python :kernel python3" in org
    assert "header-args:jupyter-python+ :session" not in org


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_header_args_are_read_as_kernel_metadata():
    org = """#+JUPYTER_KERNEL_DISPLAY_NAME: Python 3
#+PROPERTY: header-args:jupyter-python :kernel python3
#+PROPERTY: header-args:jupyter-python+ :session python3

#+begin_src jupyter-python
print("hello")
#+end_src
"""
    nb = jupytext.reads(org, "org")
    assert nb.metadata["kernelspec"]["name"] == "python3"
    assert nb.metadata["kernelspec"]["language"] == "python"
    assert nb.metadata["kernelspec"]["display_name"] == "Python 3"
    assert nb.metadata["org_babel"]["header_args"]["jupyter-python"]["session"] == "python3"
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_babel_metadata_is_written_to_header_args():
    notebook = new_notebook(
        metadata={
            "kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"},
            "org_babel": {"header_args": {"jupyter-python": {"session": "verification-games-fluxes"}}},
        },
        cells=[new_code_cell("x = 1")],
    )
    org = jupytext.writes(notebook, "org")
    assert "#+JUPYTER_KERNEL_DISPLAY_NAME: Python 3" in org
    assert "#+PROPERTY: header-args:jupyter-python :kernel python3" in org
    assert "#+PROPERTY: header-args:jupyter-python+ :session verification-games-fluxes" in org


@pytest.mark.requires_pandoc(min_version="3.4")
def test_header_args_without_kernel_do_not_set_kernelspec():
    org = """#+PROPERTY: header-args:jupyter-python+ :session verification-games-fluxes

#+begin_src jupyter-python
print("hello")
#+end_src
"""
    nb = jupytext.reads(org, "org")
    assert "kernelspec" not in nb.metadata
    assert nb.metadata["org_babel"]["header_args"]["jupyter-python"]["session"] == "verification-games-fluxes"


@pytest.mark.requires_pandoc(min_version="3.4")
def test_raw_cells_are_not_preserved():
    notebook = new_notebook(
        cells=[
            new_markdown_cell("before"),
            new_raw_cell("RAW CONTENT"),
            new_markdown_cell("after"),
        ]
    )
    nb2 = jupytext.reads(jupytext.writes(notebook, "org"), "org")
    assert all(cell.cell_type != "raw" for cell in nb2.cells)
    assert len(nb2.cells) == 1
    assert nb2.cells[0].cell_type == "markdown"
    assert "before" in nb2.cells[0].source
    assert "after" in nb2.cells[0].source
    assert "RAW CONTENT" not in nb2.cells[0].source


@pytest.mark.requires_pandoc(min_version="3.4")
def test_consecutive_markdown_cells_are_concatenated():
    notebook = new_notebook(
        cells=[
            new_markdown_cell("First markdown cell."),
            new_markdown_cell("Second markdown cell."),
        ]
    )
    nb2 = jupytext.reads(jupytext.writes(notebook, "org"), "org")
    assert len(nb2.cells) == 1
    assert nb2.cells[0].cell_type == "markdown"
    assert "First markdown cell." in nb2.cells[0].source
    assert "Second markdown cell." in nb2.cells[0].source


@pytest.mark.requires_pandoc(min_version="3.4")
@pytest.mark.xfail(
    reason="Org prose has no native cell-boundary markers; consecutive markdown cells are concatenated",
    strict=True,
)
def test_strict_round_trip_does_not_preserve_consecutive_markdown_cells():
    notebook = new_notebook(
        cells=[
            new_markdown_cell("First markdown cell."),
            new_markdown_cell("Second markdown cell."),
        ]
    )
    compare_notebooks(jupytext.reads(jupytext.writes(notebook, "org"), "org"), notebook, "org")


@pytest.mark.requires_pandoc(min_version="3.4")
@pytest.mark.xfail(
    reason="Pandoc Org conversion does not preserve raw cells",
    strict=True,
)
def test_strict_round_trip_does_not_preserve_raw_cells():
    notebook = new_notebook(
        cells=[
            new_markdown_cell("before"),
            new_raw_cell("RAW CONTENT"),
            new_markdown_cell("after"),
        ]
    )
    compare_notebooks(jupytext.reads(jupytext.writes(notebook, "org"), "org"), notebook, "org")


@pytest.mark.requires_pandoc(min_version="3.4")
@pytest.mark.xfail(
    reason="Org format does not preserve cell metadata",
    strict=True,
)
def test_strict_round_trip_does_not_preserve_cell_metadata():
    notebook = new_notebook(
        cells=[
            new_markdown_cell(
                "A markdown cell",
                metadata={"slideshow": {"slide_type": "slide"}},
            )
        ]
    )
    compare_notebooks(jupytext.reads(jupytext.writes(notebook, "org"), "org"), notebook, "org")


@pytest.mark.requires_pandoc(min_version="3.4")
def test_strict_round_trip_preserves_code_indentation():
    notebook = new_notebook(
        cells=[
            new_code_cell('fish = {"x"=>x,\n\t"type"=>"scatter"}'),
        ]
    )
    compare_notebooks(jupytext.reads(jupytext.writes(notebook, "org"), "org"), notebook, "org")


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_utf8():
    """Org format should handle unicode correctly"""
    notebook = new_notebook(
        cells=[
            new_markdown_cell("Greek letter π and emoji 🎉"),
        ]
    )
    org = jupytext.writes(notebook, "org")
    nb2 = jupytext.reads(org, "org")
    assert any("π" in cell.source for cell in nb2.cells)


@pytest.mark.requires_no_pandoc
def test_meaningful_error_when_pandoc_is_missing(tmpdir):
    nb_file = tmpdir.join("notebook.ipynb")
    jupytext.write(new_notebook(), str(nb_file))

    with pytest.raises(PandocError):
        jupytext_cli([str(nb_file), "--to", "org"])


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_round_trip_preserves_literal_source_lines():
    source = """cat <<'EOF'
<<tag>>
#+PROPERTY: header-args:bash :results silent
#+JUPYTER_KERNEL_DISPLAY_NAME: literal text
EOF"""
    org = f"#+begin_src jupyter-bash\n{source}\n#+end_src\n"
    notebook = jupytext.reads(org, "org")
    assert notebook.cells[0].source == source
    assert "org_babel" not in notebook.metadata

    restored = jupytext.reads(jupytext.writes(notebook, "org"), "org")
    assert restored.cells[0].source == source


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_round_trip_preserves_document_babel_args_without_a_kernel():
    org = """#+PROPERTY: header-args :exports both
#+PROPERTY: header-args:python :results output replace :file output/report.csv
#+PROPERTY: header-args:python+ :var label="a :b c" :dir /tmp/results
#+PROPERTY: header-args:R :session analysis

#+begin_src python
print("hello")
#+end_src
"""
    notebook = jupytext.reads(org, "org")
    expected = {
        "": {"exports": "both"},
        "python": {
            "results": "output replace",
            "file": "output/report.csv",
            "var": 'label="a :b c"',
            "dir": "/tmp/results",
        },
        "R": {"session": "analysis"},
    }
    assert notebook.metadata.org_babel.header_args == expected
    assert "kernelspec" not in notebook.metadata

    restored = jupytext.reads(jupytext.writes(notebook, "org"), "org")
    assert restored.metadata.org_babel.header_args == expected
    assert restored.cells[0].cell_type == "markdown"
    assert restored.cells[0].source.endswith(notebook.cells[0].source)


@pytest.mark.requires_pandoc(min_version="3.4")
@pytest.mark.parametrize("language", ["", "jupyter-python"])
def test_org_round_trip_preserves_repeated_babel_vars(language):
    suffix = f":{language}" if language else ""
    org = f"""#+PROPERTY: header-args{suffix} :var x=1 :var label="a :b c"
#+PROPERTY: header-args{suffix}+ :var y=2

#+begin_src jupyter-python
print(x + y, label)
#+end_src
"""
    notebook = jupytext.reads(org, "org")
    expected = {"var": ["x=1", 'label="a :b c"', "y=2"]}
    assert notebook.metadata.org_babel.header_args[language] == expected

    ipynb = jupytext.writes(notebook, "ipynb")
    restored = jupytext.writes(jupytext.reads(ipynb, "ipynb"), "org")
    assert f'#+PROPERTY: header-args{suffix} :var x=1 :var label="a :b c" :var y=2' in restored
    assert jupytext.reads(restored, "org").metadata.org_babel == notebook.metadata.org_babel


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_round_trip_preserves_cpp_kernel():
    kernel = {"name": "xcpp17", "language": "c++", "display_name": "C++17"}
    notebook = new_notebook(
        metadata={"kernelspec": kernel, "org_babel": {"header_args": {"jupyter-c++": {"session": "cpp"}}}},
        cells=[new_code_cell("int x = 42;")],
    )
    restored = jupytext.reads(jupytext.writes(notebook, "org"), "org")
    assert restored.metadata.kernelspec == kernel
    assert restored.metadata.org_babel == notebook.metadata.org_babel
    assert restored.cells[0].cell_type == "code"
    assert restored.cells[0].source == notebook.cells[0].source


@pytest.mark.requires_pandoc(min_version="3.4")
@pytest.mark.parametrize("test_flag", ["--test", "--test-strict"])
def test_org_cli_test_reports_loss_without_writing_notebook(tmp_path, test_flag, capsys):
    path = tmp_path / "notebook.ipynb"
    notebook = new_notebook(cells=[new_code_cell("1 + 1"), new_raw_cell("Keep this raw text")])
    jupytext.write(notebook, path)
    notebook_before = path.read_bytes()

    assert jupytext_cli([test_flag, "--to", "org", str(path)]) == 1

    assert "Cells 2 differ" in capsys.readouterr().out
    assert path.read_bytes() == notebook_before
    assert not path.with_suffix(".org").exists()


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_cli_test_reports_comment_loss_without_writing_org(tmp_path, capsys):
    org_path = tmp_path / "notebook.org"
    org_path.write_text(
        """# A comment to keep

#+begin_src jupyter-python
1 + 2
#+end_src
""",
        encoding="utf-8",
    )
    org_before = org_path.read_bytes()

    assert jupytext_cli(["--test", "--to", "ipynb", str(org_path)]) == 1

    assert "-# A comment to keep" in capsys.readouterr().out
    assert org_path.read_bytes() == org_before
    assert not org_path.with_suffix(".ipynb").exists()


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_cli_sync_propagates_edit_in_a_supported_pair(tmp_path):
    path = tmp_path / "notebook.ipynb"
    org_path = path.with_suffix(".org")
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,org"\n', encoding="utf-8")
    jupytext.write(
        new_notebook(
            cells=[new_code_cell("1 + 1")],
            metadata={
                "custom": "keep this in the notebook",
                "kernelspec": {"name": "python3", "language": "python", "display_name": "Python 3"},
            },
        ),
        path,
    )
    assert jupytext_cli(["--set-formats", "ipynb,org", str(path)]) == 0
    new_text = org_path.read_text(encoding="utf-8").replace("1 + 1", "1 + 2")
    org_path.write_text(new_text, encoding="utf-8")
    os.utime(path, (org_path.stat().st_mtime - 2,) * 2)

    assert jupytext_cli(["--sync", "--check-source-is-newer", str(org_path)]) == 0

    restored = jupytext.read(path)
    assert [cell.source for cell in restored.cells] == ["1 + 2"]
    assert restored.metadata.custom == "keep this in the notebook"
    assert restored.metadata.jupytext.formats == "ipynb,org"
    assert jupytext.read(org_path).cells[-1].source == "1 + 2"


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_round_trip_preserves_literal_tab_in_code():
    source = 'text = """first\n\tsecond\n"""'
    notebook = new_notebook(cells=[new_code_cell(source), new_code_cell("pass")])
    org = jupytext.writes(notebook, "org")
    assert [line for line in org.splitlines() if line.startswith("#+begin_src")] == [
        "#+begin_src jupyter-python -i",
        "#+begin_src jupyter-python",
    ]

    converted = pandoc("--from org --to ipynb --standalone --preserve-tabs", input_text=org, timeout=30)
    assert ipynb_reads(converted, as_version=4).cells[0].source.removesuffix("\n") == source

    # Jupytext also preserves tabs when importing an Org block without the switch.
    old_org = org.replace("#+begin_src jupyter-python -i", "#+begin_src jupyter-python", 1)
    restored = jupytext.reads(old_org, "org")
    assert restored.cells[0].source == source


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_export_rejects_notebook_attachments():
    png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/ak33iUAAAAASUVORK5CYII="
    cell = new_markdown_cell(
        "![Diagram](attachment:diagram.png)",
        attachments={"diagram.png": {"image/png": png}},
    )
    with pytest.raises(ValueError, match="Org.*attachment"):
        jupytext.writes(new_notebook(cells=[cell]), "org")


@pytest.mark.requires_pandoc(min_version="3.4")
def test_org_reports_pandoc_timeout(monkeypatch):
    from subprocess import TimeoutExpired

    from jupytext import org, pandoc

    original_run = pandoc.subprocess.run

    def time_out_conversion(cmd, **kwargs):
        if "--from" in cmd:
            assert kwargs["timeout"] == org._ORG_TIMEOUT_SECONDS
            raise TimeoutExpired(cmd, kwargs["timeout"])
        return original_run(cmd, **kwargs)

    monkeypatch.setattr(pandoc.subprocess, "run", time_out_conversion)
    with pytest.raises(PandocError, match="Pandoc conversion timed out"):
        jupytext.reads("#+begin_src python\npass\n#+end_src\n", "org")
