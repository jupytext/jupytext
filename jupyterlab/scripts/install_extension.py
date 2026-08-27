# This script does the "same" job as `jupyter labextension develop --overwrite .`
#
# Seems like we cannot use the upstream script on our repo organization.
# If we want to use the upstream script we need to have a setup.py or pyproject.toml
# in jupyterlab/jupyterlab-jupytext folder with the name of the package.
#
# We are only interested in making a symlink to the
# sys.prefix/share/jupyter/labextensions folder for development. We should be able
# to do it in simple script
#

import os

import jupyterlab_jupytext
from jupyter_builder.federated_extensions import build_labextension, develop_labextension


def main():
    """Create symlink in sys.prefix based on name of extension"""

    labexts = jupyterlab_jupytext._jupyter_labextension_paths()
    base_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "jupyterlab_jupytext",
    )

    for labext in labexts:
        src = os.path.join(base_path, labext["src"])
        dest = labext["dest"]
        print(f"Installing {src} -> {dest}")

        if not os.path.exists(src):
            build_labextension(base_path)

        full_dest = develop_labextension(
            src,
            overwrite=True,
            symlink=True,
            user=False,
            sys_prefix=True,
            labextensions_dir="",
            destination=dest,
        )
        print(f"Creating symlink at {full_dest}")


if __name__ == "__main__":
    main()
