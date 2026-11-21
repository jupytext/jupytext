import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    # This is an unfrozen cell. Works as usual.
    print("I'm a regular cell so I run and print!")
    return


@app.cell
def _():
    # This is an frozen cell
    print("I'm frozen so Im not executed :(")
    return


if __name__ == "__main__":
    app.run()
