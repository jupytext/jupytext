import sys

import atheris

with atheris.instrument_imports():
    from jupytext.cell_reader import RMarkdownCellReader

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeString(len(data))
    lines = text.splitlines()
    _ = RMarkdownCellReader().read(lines)


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
