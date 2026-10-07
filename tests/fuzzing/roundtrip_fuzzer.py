import sys

import atheris
from fuzz_helpers import EnhancedFuzzedDataProvider

with atheris.instrument_imports(include=["jupytext"]):
    import jupytext
    from jupytext.compare import compare


def TestOneInput(data: bytes):
    fdp = EnhancedFuzzedDataProvider(data)

    py = fdp.ConsumeRemainingString()
    nb = jupytext.reads(py, "py")
    py2 = jupytext.writes(nb, "py")

    compare(py, py2)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
